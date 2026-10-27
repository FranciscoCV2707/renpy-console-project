"""Parser y comparacion de lineas TRACE (contrato C3)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class TraceParseError(ValueError):
    def __init__(self, line_no: int, message: str):
        super().__init__(f"line {line_no}: {message}")
        self.line_no = line_no


@dataclass
class TraceEvent:
    seq: int
    frame: int
    ev: str
    fields: dict = None

    def __post_init__(self):
        if self.fields is None:
            self.fields = {}


@dataclass
class CompareResult:
    equal: bool
    index: Optional[int]
    actual: Optional[TraceEvent]
    reference: Optional[TraceEvent]
    message: str
    verdict: str
    scenario: Optional[str] = None


def parse_line(line: str, line_no: int = 1) -> Optional[TraceEvent]:
    """Parsea una linea TRACE. Devuelve None si no empieza con ``T|`` (se ignora)."""
    s = line.strip()
    if s == "" or not s.startswith("T|"):
        return None
    parts = s[2:].split("|", 3)
    if len(parts) < 3:
        raise TraceParseError(line_no, "malformed trace line: expected seq|frame|EV")
    seq_str, frame_str, ev = parts[0], parts[1], parts[2]
    if ev == "":
        raise TraceParseError(line_no, "empty event name")
    try:
        seq = int(seq_str)
    except ValueError:
        raise TraceParseError(line_no, f"invalid seq: {seq_str!r}")
    try:
        frame = int(frame_str)
    except ValueError:
        raise TraceParseError(line_no, f"invalid frame: {frame_str!r}")
    fields: dict = {}
    if len(parts) == 4:
        field_str = parts[3]
        if field_str != "":
            for pair in field_str.split(";"):
                if "=" not in pair:
                    raise TraceParseError(line_no, f"malformed field: {pair!r}")
                key, value = pair.split("=", 1)
                if key == "":
                    raise TraceParseError(line_no, "empty field name")
                fields[key] = value
    return TraceEvent(seq=seq, frame=frame, ev=ev, fields=fields)


def parse_trace(text: str) -> list[TraceEvent]:
    events: list[TraceEvent] = []
    for i, line in enumerate(text.splitlines(), 1):
        ev = parse_line(line, i)
        if ev is not None:
            events.append(ev)
    return events


def parse_file(path) -> list[TraceEvent]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    return parse_trace(text)


def _filter_events(events, allowed):
    if not allowed:
        return list(events)
    allowed_set = set(allowed)
    return [e for e in events if e.ev in allowed_set]


def _events_equal(a, b, tolerance_frames=0):
    if a.ev != b.ev:
        return False
    if a.fields != b.fields:
        return False
    if abs(a.frame - b.frame) > tolerance_frames:
        return False
    return True


def compare_events(actual, reference, allowed_events=None, tolerance_frames=0) -> CompareResult:
    fa = _filter_events(actual, allowed_events)
    fr = _filter_events(reference, allowed_events)
    n = min(len(fa), len(fr))
    for i in range(n):
        if not _events_equal(fa[i], fr[i], tolerance_frames):
            return CompareResult(
                equal=False,
                index=i,
                actual=fa[i],
                reference=fr[i],
                message=f"first divergent at index {i}: actual {fa[i].ev} vs reference {fr[i].ev}",
                verdict="FAIL",
            )
    if len(fa) != len(fr):
        i = n
        a = fa[i] if i < len(fa) else None
        r = fr[i] if i < len(fr) else None
        return CompareResult(
            equal=False,
            index=i,
            actual=a,
            reference=r,
            message=f"length mismatch: actual {len(fa)} vs reference {len(fr)} events",
            verdict="FAIL",
        )
    return CompareResult(
        equal=True,
        index=None,
        actual=None,
        reference=None,
        message="traces match",
        verdict="PASS",
    )


def normalize_engine(events, snoot_map, spanish) -> list:
    """Traza del motor en la forma comun (PLAN.md D17): lo que ve el jugador en cada SAY, el hablante y el texto en
    español (`spanish`: id de traduccion -> texto; si dos lineas dicen lo mismo, da igual que id les toco). Sin cuadros
    ni CHOICE: los tiempos no se comparan entre motores, el hook de Ren'Py no ve las decisiones (kit_capture elige
    antes) y el camino elegido ya se ve en la secuencia de lineas."""
    return [say(e.seq, snoot_map["speakers"][int(e.fields["who"])], snoot_map["text"][int(e.fields["text"])], spanish)
            for e in events if e.ev == "SAY"]


def normalize_renpy(events, spanish) -> list:
    """Traza de Ren'Py en la misma forma que normalize_engine. Una linea con el mismo id dos veces seguidas es una
    interaccion que Ren'Py reinicio (pasa antes del renpy.input del anuario en la ruta 4): el jugador la ve una vez."""
    says = [e for e in events if e.ev == "SAY"]
    return [say(e.seq, e.fields["who"], e.fields["id"], spanish) for k, e in enumerate(says)
            if k == 0 or e.fields["id"] != says[k - 1].fields["id"]]


def say(seq, who, tid, spanish) -> TraceEvent:
    # un id sin texto en tl/es se compara por el id mismo
    return TraceEvent(seq=seq, frame=0, ev="SAY", fields={"who": who, "text": spanish.get(tid, tid)})


def _resource_name(snoot_map, image_id, tag=None):
    name = snoot_map["images"].get(image_id, f"image:{image_id}")
    names = name if isinstance(name, list) else [name]
    if tag is not None:
        for candidate in names:
            if candidate == tag or candidate.startswith(tag + " "):
                return candidate
    return names[0]


def _sprite_name(tag, image_name):
    return image_name[len(tag):].strip() if image_name.startswith(tag) else image_name


def _music_name(value):
    return value.replace("\\", "/").casefold() if value else None


def _background_name(value):
    return value[3:] if value.startswith("bg ") else value


def _is_background_tag(tag):
    return tag in ("bg", "background")


def _state_event(seq, who, text, bg, sprites, music):
    return TraceEvent(seq=seq, frame=0, ev="SAY", fields={
        "who": who,
        "text": text,
        "bg": bg,
        "sprites": sorted(f"{tag} {expression}".strip() for tag, expression in sprites.items()),
        "music": music,
    })


def normalize_engine_full(events, snoot_map, spanish) -> list[TraceEvent]:
    """Normaliza cada SAY junto al fondo, sprites y música activos en el motor."""
    bg = None
    sprites = {}
    music = None
    result = []
    for event in events:
        fields = event.fields
        if event.ev == "SCENE":
            bg_name = _background_name(_resource_name(snoot_map, int(fields["img"]))) if "img" in fields else None
            bg = (bg_name, bg_name) if bg_name is not None else None
            sprites.clear()
        elif event.ev == "SHOW":
            tag = snoot_map["tags"].get(int(fields["tag"]), f"tag:{fields['tag']}")
            image_name = _resource_name(snoot_map, int(fields["img"]), tag)
            expression = _sprite_name(tag, image_name)
            if expression and not _is_background_tag(tag):
                sprites[tag] = expression
                if bg is not None and tag == bg[0]:
                    bg = None
            else:
                bg_name = _background_name(image_name)
                bg = (tag, bg_name)
                sprites.pop(tag, None)
        elif event.ev == "HIDE":
            tag = snoot_map["tags"].get(int(fields["tag"]), f"tag:{fields['tag']}")
            sprites.pop(tag, None)
            if bg is not None and bg[0] == tag:
                bg = None
        elif event.ev == "PLAY":
            music = _music_name(snoot_map["tracks"].get(int(fields["track"]), f"track:{fields['track']}"))
        elif event.ev == "STOP":
            music = None
        elif event.ev == "SAY":
            who = snoot_map["speakers"][int(fields["who"])]
            text = spanish.get(snoot_map["text"][int(fields["text"])], snoot_map["text"][int(fields["text"])])
            result.append(_state_event(event.seq, who, text, bg[1] if bg else None, sprites, music))
    return result


def normalize_renpy_full(events, spanish) -> list[TraceEvent]:
    """Normaliza los cambios SHOW/SCENE/PLAY de Ren'Py al estado de cada SAY."""
    bg = None
    sprites = {}
    music = None
    result = []
    previous_say_id = None
    for event in events:
        fields = event.fields
        if event.ev == "SCENE":
            bg = None
            sprites.clear()
        elif event.ev == "SHOW":
            tag = fields["tag"]
            attrs = fields.get("attrs", "").split()
            if attrs and not _is_background_tag(tag):
                sprites[tag] = " ".join(attrs)
                if bg is not None and bg[0] == tag:
                    bg = None
            else:
                bg_name = " ".join([tag, *attrs]) if _is_background_tag(tag) else tag
                bg = (tag, _background_name(bg_name))
                sprites.pop(tag, None)
        elif event.ev == "HIDE":
            tag = fields["tag"]
            sprites.pop(tag, None)
            if bg is not None and bg[0] == tag:
                bg = None
        elif event.ev == "PLAY":
            music = _music_name(fields.get("music", ""))
        elif event.ev == "STOP":
            music = None
        elif event.ev == "SAY":
            tid = fields["id"]
            if tid == previous_say_id:
                continue
            result.append(_state_event(event.seq, fields["who"], spanish.get(tid, tid), bg[1] if bg else None,
                                       sprites, music))
            previous_say_id = tid
    return result


def compare_renpy_full(actual, reference, exceptions=None) -> CompareResult:
    """Compara las líneas y su estado visible/audible con excepciones exactas por índice."""
    allowed = {(item["index"], item["field"]): (item["actual"], item["reference"])
               for item in (exceptions or [])}
    n = min(len(actual), len(reference))
    for index in range(n):
        left, right = actual[index], reference[index]
        fields = set(left.fields) | set(right.fields)
        mismatch = next((name for name in sorted(fields)
                         if left.fields.get(name) != right.fields.get(name)
                         and allowed.get((index, name)) != (left.fields.get(name), right.fields.get(name))), None)
        if mismatch is not None:
            return CompareResult(False, index, left, right,
                                 f"first divergent at SAY {index}: {mismatch} differs", "FAIL")
    if len(actual) != len(reference):
        index = n
        return CompareResult(False, index, actual[index] if index < len(actual) else None,
                             reference[index] if index < len(reference) else None,
                             f"length mismatch: actual {len(actual)} vs reference {len(reference)} SAY events", "FAIL")
    return CompareResult(True, None, None, None, "traces match", "PASS")


def compare_scenario(scenario, trace_path) -> CompareResult:
    ref_path = Path(scenario.reference)
    if not ref_path.is_absolute():
        base = scenario.source
        if base is not None:
            base_path = Path(base)
            cand_base = base_path.parent if base_path.is_file() else base_path
            cand = cand_base / ref_path
            if cand.exists():
                ref_path = cand
            else:
                cand2 = Path.cwd() / ref_path
                if cand2.exists():
                    ref_path = cand2
        else:
            cand = Path.cwd() / ref_path
            if cand.exists():
                ref_path = cand
    ref_events = parse_file(ref_path)
    actual_events = parse_file(trace_path)
    if scenario.compare.mode == "renpy":
        from .snoot_map import load_map, load_spanish

        spanish = load_spanish()
        result = compare_events(normalize_engine(actual_events, load_map(), spanish), normalize_renpy(ref_events, spanish))
        result.scenario = scenario.id
        return result
    if scenario.compare.mode == "renpy_full":
        from .snoot_map import load_map, load_spanish

        snoot_map = load_map()
        spanish = load_spanish()
        result = compare_renpy_full(
            normalize_engine_full(actual_events, snoot_map, spanish),
            normalize_renpy_full(ref_events, spanish),
            scenario.compare.exceptions,
        )
        result.scenario = scenario.id
        return result
    allowed = scenario.compare.events
    tol_frames = scenario.compare.tolerance.get("frames", 0)
    result = compare_events(actual_events, ref_events, allowed, tol_frames)
    result.scenario = scenario.id
    return result
