"""Serializacion de capitulos y textos VNB1, compatible con core/vm.c."""
import re
import struct
from pathlib import Path

LIMITS_HEADER = Path(__file__).resolve().parents[1] / "core" / "vn_limits.h"


def engine_limits(header=LIMITS_HEADER):
    """Lee los `#define NOMBRE entero` de core/vn_limits.h, los mismos que usa el motor."""
    text = header.read_text(encoding="utf-8")
    return {name: int(value) for name, value in re.findall(r"^#define\s+(\w+)\s+(\d+)\b", text, re.M)}


def check_chapter_size(name, vnb_bytes, text_bytes, limits=None):
    """Falla si el capitulo no cabe en el motor (core/chapter.c rechazaria cargarlo)."""
    limits = limits or engine_limits()
    for kind, size, limit in [("VNB", len(vnb_bytes), limits["VN_CHAPTER_MAX_BYTES"]),
                              ("texto", len(text_bytes), limits["VN_TEXT_MAX_BYTES"])]:
        if size > limit:
            raise ValueError(f"capitulo {name}: {kind} de {size} bytes excede el limite del motor de {limit} bytes "
                             f"(core/vn_limits.h)")


def bloque_texto(cadenas):
    if len(cadenas) > 65535:
        raise ValueError("demasiados textos en un capitulo")
    offsets = []
    position = 4 * len(cadenas)
    for cadena in cadenas:
        offsets.append(position)
        position += len(cadena) + 1
    return (struct.pack("<H", len(cadenas)) + struct.pack(f"<{len(offsets)}I", *offsets)
            + b"".join(cadena + b"\x00" for cadena in cadenas))


def animation(keyframes, loop=False, events=(), loop_start=0):
    if not 1 <= len(keyframes) <= 64 or type(loop) is not bool:
        raise ValueError("animacion requiere 1 a 64 claves y loop booleano")
    if len(events) > 255:
        raise ValueError("animacion admite hasta 255 eventos")
    if type(loop_start) is not int or not 0 <= loop_start < len(keyframes) or (loop_start and not loop):
        raise ValueError("inicio de bucle fuera de las claves")
    # Flags bit 7: the keys carry an s16 angle in bytes 9-10 (1/4096 turn). Off unless some angle is not 0, so
    # animations without rotation keep the old bytes (64, 0) that the engine ignores.
    rotated = any(key.get("angle", 0) != 0 for key in keyframes)
    blob = bytearray([len(keyframes), int(loop) | loop_start << 1 | rotated << 7, len(events)])
    previous = -1
    for key in keyframes:
        if set(key) - {"frame", "x", "y", "alpha", "curve", "zoom", "r", "g", "b", "angle"}:
            raise ValueError("propiedad de animacion sin soporte")
        fields = []
        for name, default, minimum, maximum in [("frame", None, 0, 65535), ("x", 128, -32768, 32767),
                ("y", 256, -32768, 32767), ("alpha", 255, 0, 255), ("curve", 0, 0, 3),
                ("zoom", 64, 1, 255), ("r", 128, 0, 255), ("g", 128, 0, 255), ("b", 128, 0, 255),
                ("angle", 0, -32768, 32767)]:
            value = key.get(name, default)
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f"clave de animacion: {name} fuera de rango")
            fields.append(value)
        frame, horizontal, vertical, alpha, curve, zoom, red, green, blue, angle = fields
        if frame <= previous:
            raise ValueError("tiempos de animacion deben crecer estrictamente")
        previous = frame
        blob.extend(struct.pack("<HhhBBB", frame, horizontal, vertical, alpha, curve, zoom))
        blob.extend(struct.pack("<h", angle) if rotated else bytes([64, 0]))
        blob.extend(bytes([red, green, blue, 255]))
    # Image change events (7 bytes, docs/bytecode.md): the engine applies the last one whose frame has passed.
    previous = -1
    for event in events:
        if set(event) - {"frame", "image", "flip", "dissolve"}:
            raise ValueError("propiedad de evento sin soporte")
        frame, image = event.get("frame"), event.get("image")
        flip, dissolve = event.get("flip", 0), event.get("dissolve", 0)
        for name, value, minimum, maximum in [("frame", frame, 0, 65535), ("image", image, 1, 65535),
                                              ("flip", flip, 0, 1), ("dissolve", dissolve, 0, 65535)]:
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f"evento de animacion: {name} fuera de rango")
        if frame < previous:
            raise ValueError("eventos de animacion deben ir en orden de tiempo")
        previous = frame
        blob.extend(struct.pack("<HHBH", frame, image, flip, dissolve))
    return bytes(blob)


def vnb(code, text_count, chapter=0, text_base=0, animations=()):
    end = 32 + len(code)
    if len(animations) > 32767:
        raise ValueError("demasiadas animaciones")
    offsets, position = [], 4 * len(animations)
    for item in animations:
        offsets.append(position)
        position += len(item)
    table = struct.pack(f"<{len(offsets)}I", *offsets) + b"".join(animations)
    return b"VNB1" + struct.pack("<HHIIHHIII", chapter, 0, len(code), text_base,
                                text_count, len(animations), end, end, 0) + code + table
