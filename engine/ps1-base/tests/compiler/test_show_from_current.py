"""SHOW con VM_SHOW_FROM_CURRENT (flags bit3): la animacion nueva parte del aspecto actual del sprite."""
import os
import subprocess
from pathlib import Path

import pytest

from vncompiler.programa import compile_program

ROOT = Path(__file__).resolve().parents[2]
GCC = Path(r"C:\msys64\ucrt64\bin\gcc.exe")
FROM_CURRENT = 0x08


@pytest.fixture(scope="module")
def motion_host(tmp_path_factory):
    if not GCC.is_file():
        pytest.fail("se requiere GCC nativo de MSYS2 para correr core/vm.c y core/scene.c")
    executable = tmp_path_factory.mktemp("motion") / "motion_host.exe"
    environment = {**os.environ, "PATH": str(GCC.parent) + os.pathsep + os.environ["PATH"]}
    subprocess.run([str(GCC), "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT / "core"),
                    str(ROOT / "tests/compiler/motion_host.c"), str(ROOT / "core/vm.c"), str(ROOT / "core/scene.c"),
                    "-o", str(executable)], check=True, capture_output=True, text=True, env=environment)
    return executable, environment


def show(image, keys, flags=0, loop=False):
    return {"op": "ps1_show", "tag": 1, "image": image, "flags": flags, "loop": loop,
            "keyframes": [{"frame": frame, "x": x} for frame, x in keys]}


def say():
    return {"op": "say", "who": None, "text": "..."}


def run(host, tmp_path, nodes, frames_per_say, offsets, skip=0):
    executable, environment = host
    program = compile_program({"characters": {}, "script": {"test.rpy": [
        {"op": "label", "name": "start", "body": nodes + [{"op": "return"}]}]}}, ["start"])
    chapter = tmp_path / "motion.vnb"
    chapter.write_bytes(program.chapters[0][0])
    output = subprocess.run([str(executable), str(chapter), str(frames_per_say), "1", str(skip),
                             ",".join(map(str, offsets))], check=True, capture_output=True, text=True,
                            env=environment).stdout
    return [list(map(int, line.split()[1:])) for line in output.splitlines()]


# 0 -> 240 en 60 cuadros; despues, con claves horneadas desde el estado asentado (240), 240 -> 0
FIRST = [(0, 0), (60, 240)]
SECOND = [(0, 240), (60, 0)]


def test_fast_reading_continues_from_intermediate_position(motion_host, tmp_path):
    rows = run(motion_host, tmp_path, [show(1, FIRST), say(), show(2, SECOND, FROM_CURRENT), say()], 15, [0, 30, 60])
    assert rows[0] == [0, 120, 240]
    # a los 15 cuadros iba en 60: parte de ahi sin saltar a 240 y llega a la misma clave final
    assert rows[1] == [60, 30, 0]


def test_without_flag_new_movement_starts_from_baked_key(motion_host, tmp_path):
    rows = run(motion_host, tmp_path, [show(1, FIRST), say(), show(2, SECOND), say()], 15, [0, 30])
    assert rows[1] == [240, 120]


def test_slow_reading_matches_baked_key(motion_host, tmp_path):
    rows = run(motion_host, tmp_path, [show(1, FIRST), say(), show(2, SECOND, FROM_CURRENT), say()], 600, [0, 30])
    assert rows[1] == [240, 120]


def test_skip_does_not_capture(motion_host, tmp_path):
    rows = run(motion_host, tmp_path, [show(1, FIRST), say(), show(2, SECOND, FROM_CURRENT), say()], 15, [0], skip=1)
    assert rows[1] == [240]


def test_chained_captures_include_previous_capture(motion_host, tmp_path):
    nodes = [show(1, FIRST), say(), show(2, SECOND, FROM_CURRENT), say(), show(1, [(0, 0), (60, 120)], FROM_CURRENT),
             say()]
    rows = run(motion_host, tmp_path, nodes, 15, [0, 60])
    # segunda: 60 -> 0, a los 15 cuadros va en 45; la tercera parte de ahi
    assert rows[2] == [45, 120]


def test_loop_uses_capture_only_on_first_pass(motion_host, tmp_path):
    nodes = [show(1, FIRST), say(), show(2, SECOND, FROM_CURRENT, loop=True), say()]
    rows = run(motion_host, tmp_path, nodes, 15, [0, 60, 90])
    assert rows[1] == [60, 240, 120]


def test_new_sprite_in_reused_slot_ignores_old_capture(motion_host, tmp_path):
    nodes = [show(1, FIRST), say(), show(2, SECOND, FROM_CURRENT), {"op": "ps1_hide", "tag": 1}, show(2, SECOND),
             say()]
    rows = run(motion_host, tmp_path, nodes, 15, [0])
    assert rows[1] == [240]
