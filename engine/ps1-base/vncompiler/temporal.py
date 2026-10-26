"""Adaptador de cronologias neutrales del kit a las tablas ANIM existentes."""
import math


def transition_from_spec(spec, fps=60):
    if type(fps) is not int or not 1 <= fps <= 240:
        raise ValueError("frecuencia de muestreo invalida")
    kind = spec.get("kind")
    if kind == "cut":
        return {"op": "ps1_transition", "type": 0}
    if kind == "dissolve" and spec.get("curve", "linear") == "linear":
        values = [spec["duration"]]
        transition_type = 1
    elif kind == "fade" and spec.get("color", "#000").lower() in ("#000", "#000000", "#fff", "#ffffff"):
        values = [spec["out"], spec["hold"], spec["in"]]
        transition_type = 2 if spec.get("color", "#000").lower() in ("#000", "#000000") else 6
    else:
        raise ValueError("transicion no representable en PS1")
    if any(type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 65535 / fps
           for value in values):
        raise ValueError("duracion de transicion fuera de rango")
    return {"op": "ps1_transition", "type": transition_type,
            **{key: round(value * fps) for key, value in zip(("a", "b", "c"), values)}}


# Kit timeline properties ANIM reproduces (xzoom/yzoom/zpos are checked apart). transform_anchor only moves the
# rotation pivot; zzoom and crop_relative change nothing while depth and crop stay rejected.
DRAWN = {"xpos", "ypos", "xanchor", "yanchor", "xoffset", "yoffset", "zoom", "alpha",
         "rotate", "xzoom", "yzoom", "zpos", "transform_anchor", "zzoom", "crop_relative"}
NEUTRAL = {"blur": 0, "xrotate": 0, "yrotate": 0, "zrotate": 0, "xpan": 0, "ypan": 0,
           **{prefix + axis: 0 for prefix in ("matrixoffset_", "matrixrotate_") for axis in "xyz"}}


def parse_color(text):
    digits = text[1:] if text.startswith("#") else text
    if len(digits) in (3, 4):
        digits = "".join(character * 2 for character in digits)
    if len(digits) not in (6, 8):
        raise ValueError(f"color invalido: {text}")
    values = [int(digits[index:index + 2], 16) for index in range(0, len(digits), 2)]
    return values + [255] * (4 - len(values))


def color_factors(operations):
    """(r, g, b, alpha) multipliers of kit matrixcolor operations, or ValueError when the GPU cannot multiply it."""
    factors = [1.0, 1.0, 1.0, 1.0]
    for name, args in operations:
        if name == "tint":
            if len(args) == 1 and isinstance(args[0], str):
                *rgb, alpha = parse_color(args[0])
                scale = [1 - (1 - value / 255) * alpha / 255 for value in rgb]
            elif len(args) == 1 and isinstance(args[0], (list, tuple)) and len(args[0]) == 3:
                scale = [float(value) for value in args[0]]
            else:
                scale = [float(value) for value in args[:3]]
            factors = [factor * value for factor, value in zip(factors, scale)] + factors[3:]
        elif name == "colorize" and parse_color(args[0])[:3] == [0, 0, 0]:
            # From black to a color: a plain multiply by that color.
            factors = [factor * value / 255 for factor, value in zip(factors, parse_color(args[1])[:3])] + factors[3:]
        elif name == "opacity":
            factors[3] *= float(args[0])
        elif name in ("brightness", "hue", "saturation", "contrast") and len(args) == 1 \
                and float(args[0]) == (0.0 if name in ("brightness", "hue") else 1.0):
            continue
        elif name != "identity":
            raise ValueError(f"matriz de color {name} requiere imagen horneada")
    return factors


def color_at(timeline, seconds):
    before, after, fraction = timeline.color_at(seconds)
    start, end = color_factors(before), color_factors(after)
    return [low + (high - low) * fraction for low, high in zip(start, end)]


def rotated_center(state, zoom, image_size, mirror=False):
    """Screen point where Ren'Py draws the center of a rotated sprite (renpy/display/accelerator.pyx, transform.py).

    With transform_anchor the anchor point turns with the sprite and stays on pos + offset. Without it the anchor
    applies to the rotated box, which rotate_pad (on by default; the kit does not keep it) makes a square as wide as
    the diagonal. Anchors arrive in image pixels (the kit multiplies relative anchors by the image size)."""
    angle = math.radians(state.get("rotate", 0))
    cos, sin = math.cos(angle), math.sin(angle)
    x = state["xpos"] + state.get("xoffset", 0)
    y = state["ypos"] + state.get("yoffset", 0)
    if state.get("transform_anchor"):
        dx = (state["xanchor"] - image_size[0] / 2) * zoom * (-1 if mirror else 1)
        dy = (state["yanchor"] - image_size[1] / 2) * zoom
        return x - (dx * cos - dy * sin), y - (dx * sin + dy * cos)
    box = math.hypot(*image_size) * zoom
    return (x - state["xanchor"] / image_size[0] * box + box / 2,
            y - state["yanchor"] / image_size[1] * box + box / 2)


def child_events(timeline, resolve_child, base_image=None, fps=60, loop_frame=0):
    """ANIM image events for the timeline's ATL child changes.

    resolve_child(child) returns {"image": id[, "flip", "dissolve"]} for one kit child entry.
    """
    children = getattr(timeline, "children", None) or []
    if not children:
        return []
    if resolve_child is None:
        raise ValueError("cambio de imagen en ATL requiere resolver de imagenes")
    if getattr(timeline, "clock_offset", 0) or getattr(timeline, "cycle_tracks", None) is not None:
        raise ValueError("cambio de imagen con reloj de fase heredado sin soporte")
    events = [{**resolve_child(child), "frame": round(child["time"] * fps)} for child in children]
    if timeline.loop_start is None or any(event["frame"] == loop_frame for event in events):
        return events
    # Each later pass starts, in the engine, with the last event up to the loop start (or the sprite's own
    # image); in Ren'Py with the last child of the previous pass.
    before = [event for event in events if event["frame"] <= loop_frame]
    if events[-1]["image"] != (before[-1]["image"] if before else base_image):
        raise ValueError("ANIM no representa cambio de imagen que sigue al reiniciar el ciclo")
    return events


def animation_from_timeline(timeline, screen, image_size, fps=60, max_keys=64, tolerance=1.0,
                            resolve_child=None, base_image=None, allow_flip=False, allow_loop_intro=False):
    """ANIM keys for a kit timeline. Callers that pass the result's `flip` (SHOW flag) and `loop_start`
    (ps1_show key index) opt in with allow_flip / allow_loop_intro; otherwise those timelines are rejected."""
    if timeline.diagnostics:
        raise ValueError("cronologia con diagnosticos: " + str(timeline.diagnostics))
    loop = timeline.loop_start is not None
    clock_offset = getattr(timeline, "clock_offset", 0)
    has_cycle = getattr(timeline, "cycle_tracks", None) is not None
    if (clock_offset or has_cycle) and not loop:
        raise ValueError("ANIM requiere soporte explicito de reloj de fase heredado")
    if type(clock_offset) not in (int, float) or not math.isfinite(clock_offset) or clock_offset < 0:
        raise ValueError("reloj de fase heredado invalido")
    # Intro then cycle: the table plays the first pass once and repeats from the loop start key.
    # A first pass that differs from the steady cycle becomes the intro and the steady cycle follows it.
    intro = allow_loop_intro and loop and not clock_offset and (has_cycle or timeline.loop_start > 0)
    if loop and not intro and timeline.loop_start not in (0, 0.0):
        raise ValueError("ANIM no representa un bucle con introduccion")
    # Without intro the table loops from frame 0, so it encodes the steady cycle rotated to the inherited phase.
    steady = not intro and (bool(clock_offset) or has_cycle)
    if (type(fps) is not int or not 1 <= fps <= 240 or type(max_keys) is not int
            or not 2 <= max_keys <= 64 or not math.isfinite(tolerance) or tolerance < 0):
        raise ValueError("parametros de muestreo invalidos")
    if any(len(dimensions) != 2 or any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0
                                     for value in dimensions) for dimensions in (screen, image_size)):
        raise ValueError("dimensiones de pantalla/imagen invalidas")
    duration = timeline.duration
    if intro and has_cycle:
        duration += timeline.duration - timeline.loop_start
    if not math.isfinite(duration) or not 0 <= duration <= 65535 / fps:
        raise ValueError("duracion fuera de ANIM")
    total = round(duration * fps)
    loop_frame = round((timeline.duration if has_cycle else timeline.loop_start) * fps) if intro else 0
    if intro and loop_frame >= total:
        raise ValueError("ciclo sin duracion en ANIM")
    colored = bool(getattr(timeline, "colors", None))
    keys = ("x", "y", "zoom", "alpha") + (("r", "g", "b") if colored else ())

    def state_at(frame, shift):
        seconds = min(frame / fps, duration)
        if frame == total and loop:
            seconds = max(0, duration - 1e-9)
        return seconds, timeline.sample(seconds + shift)

    # xzoom -1 for the whole event is a mirror: the SHOW flip flag, same size and place.
    flip = allow_flip and all(math.isclose(state_at(frame, duration if steady else 0)[1].get("xzoom", 1), -1)
                              for frame in range(total + 1))
    events = child_events(timeline, resolve_child, base_image, fps, loop_frame)
    events = [{**event, "flip": 1} for event in events] if flip else events
    # Mirror switched instantly inside the animation (a crowd that walks back): image events on the same image
    # carry the mirror bit. One at frame 0 and one at the loop start anchor every pass.
    flips = None
    if allow_flip and not flip and not events and base_image is not None:
        mirrored = [state_at(frame, duration if steady else 0)[1].get("xzoom", 1) for frame in range(total + 1)]
        if any(value < 0 for value in mirrored) and all(math.isclose(abs(value), 1) for value in mirrored):
            flips = [value < 0 for value in mirrored]
            events = [{"image": base_image, "frame": frame, "flip": int(flips[frame])} for frame in range(total + 1)
                      if frame in (0, loop_frame) or flips[frame] != flips[frame - 1]]

    # Rotation: the engine turns the image around its center, so each key places the unrotated image where Ren'Py
    # puts the center of the rotated one. Timelines without rotation keep the plain placement (same bytes as before).
    rotating = any(state_at(frame, duration if steady else 0)[1].get("rotate", 0) for frame in range(total + 1))
    if rotating:
        keys += ("angle",)

    def sample(frame, shift=duration if steady else 0):
        seconds, state = state_at(frame, shift)
        mirror = state.get("xzoom", 1) < 0
        if flip or flips:
            state = {**state, "xzoom": abs(state.get("xzoom", 1))}
        if state.get("xzoom", 1) != 1 or state.get("yzoom", 1) != 1 or state.get("zpos", 0):
            raise ValueError("espejo/escala por eje o profundidad requieren otro adaptador")
        for key, value in state.items():
            # Anything ANIM cannot draw must fail here, never be dropped silently.
            if key not in DRAWN and not (key in NEUTRAL and math.isclose(value, NEUTRAL[key], abs_tol=1e-9)):
                raise ValueError(f"propiedad {key} requiere otro adaptador")
        zoom = state.get("zoom", 1)
        if rotating:
            center = rotated_center(state, zoom, image_size, mirror)
        coordinates = []
        for index, (axis, extent, size) in enumerate(zip(("x", "y"), screen, image_size)):
            if rotating:
                left = center[index] - size * zoom / 2
            else:
                left = state[axis + "pos"] - state[axis + "anchor"] * zoom + state.get(axis + "offset", 0)
            room = extent - size * zoom
            if abs(room) < 1e-6:
                if abs(left) > tolerance:
                    raise ValueError("desplazamiento con imagen del mismo tamano requiere padding")
                alignment = 0.5 if axis == "x" else 1.0
            else:
                alignment = left / room
            value = round(alignment * 256)
            if not -32768 <= value <= 32767:
                raise ValueError("alineacion fuera de 8.8")
            coordinates.append(value)
        scale = round(zoom * 64)
        factors = color_at(timeline, seconds + shift) if colored else (1, 1, 1, 1)
        alpha = round(state.get("alpha", 1) * factors[3] * 255)
        if not 1 <= scale <= 255 or not 0 <= alpha <= 255:
            raise ValueError("zoom/alfa fuera de ANIM")
        key = {"frame": frame, "x": coordinates[0], "y": coordinates[1], "zoom": scale, "alpha": alpha}
        if rotating:
            key["angle"] = round(state.get("rotate", 0) * 4096 / 360)
            if not -32768 <= key["angle"] <= 32767:
                raise ValueError("giro fuera de ANIM")
        if colored:
            # GPU modulation: 128 keeps the texel, 255 almost doubles it.
            for name, factor in zip("rgb", factors):
                key[name] = round(factor * 128)
                if not 0 <= key[name] <= 255:
                    raise ValueError("modulacion de color fuera de ANIM")
        return key

    def difference(actual, predicted):
        worst = 0.0
        for key in keys:
            difference = abs(actual[key] - predicted[key])
            if key in ("x", "y"):
                axis = 0 if key == "x" else 1
                difference *= abs(screen[axis] - image_size[axis] * actual["zoom"] / 64) / 256
            elif key == "zoom":
                difference *= max(image_size) / 64
            elif key == "angle":
                # turn in pixels at the corners: angle in radians times half the diagonal
                difference *= 2 * math.pi / 4096 * math.hypot(*image_size) * actual["zoom"] / 128
            else:
                difference *= tolerance / 2 if tolerance else 1
            worst = max(worst, difference)
        return worst

    samples = {frame: sample(frame) for frame in range(total + 1)}
    if steady and has_cycle:
        # Frames still inside the first pass must already match the steady cycle.
        for frame in range(total + 1):
            if frame / fps + clock_offset >= duration:
                break
            if difference(sample(frame, 0), samples[frame]) > tolerance:
                raise ValueError("ANIM no representa primer pase distinto del ciclo estable")
    selected = {0, loop_frame, total}

    def error(frame, left, right):
        fraction = (frame - left) / (right - left) if right > left else 0
        predicted = {key: samples[left][key] + (samples[right][key] - samples[left][key]) * fraction
                     for key in keys}
        return difference(samples[frame], predicted)

    while True:
        candidates = [(error(frame, left, right), frame) for left, right in zip(sorted(selected), sorted(selected)[1:])
                      for frame in range(left + 1, right)]
        worst, frame = max(candidates, default=(0, 0))
        if worst <= tolerance:
            break
        if len(selected) >= max_keys:
            raise ValueError("cronologia excede presupuesto de claves con la tolerancia requerida")
        selected.add(frame)
    return {"keyframes": [samples[frame] for frame in sorted(selected)], "loop": loop,
            "loop_start": sorted(selected).index(loop_frame), "events": events, "flip": flip,
            "sampling": {"fps": fps, "tolerance_pixels": tolerance, "keys": len(selected)}}
