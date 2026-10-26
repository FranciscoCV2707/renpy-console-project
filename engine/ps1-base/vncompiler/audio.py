"""Validated resolved audio nodes, using the existing VNB audio opcodes."""
import struct

# field name, maximum (all values are unsigned)
AUDIO = {
    "music_play": (0x20, "HBB", (("id", 255), ("fade", 255), ("flags", 3))),
    "music_stop": (0x21, "B", (("fade", 255),)),
    "ambient_play": (0x22, "BHB", (("slot", 3), ("id", 255), ("fade", 255))),
    "ambient_stop": (0x23, "BB", (("slot", 3), ("fade", 255))),
    "sfx_play": (0x24, "H", (("id", 255),)),
    "sfx_stop": (0x25, "B", (("fade", 255),)),
    "volume": (0x26, "BBB", (("channel", 5), ("volume", 255), ("fade", 255))),
    "music_queue": (0x27, "H", (("id", 255),)),
}


def encode_audio(node):
    action = node.get("action")
    if action not in AUDIO:
        raise ValueError(f"accion de audio desconocida: {action}")
    opcode, fmt, fields = AUDIO[action]
    values = []
    for name, maximum in fields:
        value = node.get(name, 0)
        if type(value) is not int or not 0 <= value <= maximum:
            raise ValueError(f"audio {action}: {name} fuera de rango")
        values.append(value)
    return opcode, struct.pack("<" + fmt, *values), action.upper()
