"""Compila los ``inputs`` de un escenario (C4) en pasos AUTOTEST y en ``AUTOTEST.BIN`` (T-204).

La tabla ``BUTTONS`` y las constantes ``SHOT``, ``QUIT`` y ``AUTOPLAY`` se copian de
``E:\\Dev\\snoot-ps1\\tools\\engine\\emutest.py`` (lineas 31-34). No se importa el repo hermano.
"""
from __future__ import annotations

import struct

from .scenario import Scenario, ScenarioError

Step = tuple[int, str, str]

BUTTONS = {"SELECT": 1 << 0, "START": 1 << 3, "UP": 1 << 4, "RIGHT": 1 << 5, "DOWN": 1 << 6, "LEFT": 1 << 7,
           "L2": 1 << 8, "R2": 1 << 9, "L1": 1 << 10, "R1": 1 << 11, "TRIANGLE": 1 << 12, "CIRCLE": 1 << 13,
           "CROSS": 1 << 14, "SQUARE": 1 << 15}
SHOT, QUIT, AUTOPLAY = 0xFFFF, 0xFFFE, 0xFFFD
# 0xFFE0 + i: la siguiente decision del recorrido elige la opcion i (platforms/ps1/input.c, VM_MENU_MAX = 16)
CHOICE = 0xFFE0


def scenario_steps(scenario: Scenario) -> list[Step]:
    steps: list[Step] = []
    cursor = 0
    has_quit = autoplay = False
    for i, entry in enumerate(scenario.inputs):
        if not isinstance(entry, dict) or len(entry) != 1:
            raise ScenarioError(f"inputs[{i}]", "must be a mapping with one key")
        key, value = next(iter(entry.items()))
        if key == "wait":
            cursor += int(value)
        elif key == "press":
            if not isinstance(value, str) or value.upper() not in BUTTONS:
                raise ScenarioError(f"inputs[{i}]", f"unknown button: {value!r}")
            steps.append((cursor, "press", value.upper()))
            cursor += 30
        elif key == "advance":
            for _ in range(int(value)):
                steps.append((cursor, "press", "CROSS"))
                cursor += 45
        elif key == "choose":
            for _ in range(int(value)):
                steps.append((cursor, "press", "DOWN"))
                cursor += 30
            steps.append((cursor, "press", "CROSS"))
            cursor += 30
        elif key == "shot":
            steps.append((cursor, "shot", str(value)))
        elif key == "autoplay":
            steps.append((cursor, "autoplay", ""))
            autoplay = True
        elif key == "steps":
            # pasos absolutos como los del arnes de vn-engine-ps1 ("60 press L1; 120 shot dev; 400 autoplay")
            for part in str(value).split(";"):
                words = part.split()
                if not words:
                    continue
                action, arg = words[1], (words[2] if len(words) > 2 else "")
                if action not in ("press", "shot", "autoplay", "quit") or (action == "press" and arg not in BUTTONS):
                    raise ScenarioError(f"inputs[{i}]", f"bad step: {part.strip()!r}")
                steps.append((int(words[0]), action, arg))
                cursor = max(cursor, int(words[0]))
                autoplay |= action == "autoplay"
                has_quit |= action == "quit"
        elif key == "choices":
            if not isinstance(value, list) or not all(isinstance(c, int) and 0 <= c < 16 for c in value):
                raise ScenarioError(f"inputs[{i}]", "choices must be a list of option indexes 0..15")
            steps += [(cursor, "choice", str(c)) for c in value]
        elif key == "quit":
            steps.append((cursor, "quit", ""))
            has_quit = True
        else:
            raise ScenarioError(f"inputs[{i}]", f"unknown input: {key!r}")
    # con autoplay el motor pide salir solo al volver al titulo
    if not has_quit and not autoplay:
        steps.append((cursor + 60, "quit", ""))
    return steps


def autotest_bin(steps: list[Step]) -> bytes:
    entries = []
    for frame, action, arg in steps:
        if action == "choice":
            value = CHOICE + int(arg)
        else:
            value = {"shot": SHOT, "quit": QUIT, "autoplay": AUTOPLAY}.get(action) or BUTTONS[arg.upper()]
        entries.append(struct.pack("<IH", frame, value))
    return struct.pack("<H", len(entries)) + b"".join(entries)
