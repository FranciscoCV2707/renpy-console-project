import struct
import os
import subprocess
from pathlib import Path

import pytest

from vncompiler import formatos
from vncompiler.programa import compile_program


def test_animation_uses_existing_fifteen_byte_keyframes():
    blob = formatos.animation([{"frame": 0}, {"frame": 60, "x": 192, "zoom": 48, "curve": 3}], True)
    assert blob[:3] == bytes([2, 1, 0])
    assert len(blob) == 33
    assert struct.unpack_from("<HhhBBBbbBBBB", blob, 18) == (60, 192, 256, 255, 3, 48, 64, 0, 128, 128, 128, 255)


@pytest.mark.parametrize("keys", [[], [{"frame": 0}] * 65, [{"frame": 1}, {"frame": 1}],
                                     [{"frame": 0, "zoom": 0}], [{"frame": True}]])
def test_invalid_keyframes_are_rejected(keys):
    with pytest.raises(ValueError):
        formatos.animation(keys)


def test_program_links_and_deduplicates_animation_table():
    visual = {"op": "ps1_show", "image": 1, "tag": 1, "keyframes": [{"frame": 0}, {"frame": 60, "x": 192}]}
    script = {"script": {"test.rpy": [{"op": "label", "name": "start", "body": [visual, visual, {"op": "return"}]}]}}
    program = compile_program(script, ["start"])
    vnb, _, chapter = program.chapters[0]
    assert len(chapter.animations) == 1
    assert struct.unpack_from("<H", vnb, 18)[0] == 1
    table = struct.unpack_from("<I", vnb, 24)[0]
    offset = struct.unpack_from("<I", vnb, table)[0]
    assert offset == 4 and vnb[table + offset:] == chapter.animations[0]
    assert struct.unpack_from("<H", vnb, 39)[0] == 1
    assert struct.unpack_from("<H", vnb, 48)[0] == 1


def test_generated_animation_is_read_by_native_scene_core(tmp_path):
    root = Path(__file__).resolve().parents[2]
    gcc = Path(r"C:\msys64\ucrt64\bin\gcc.exe")
    environment = {**os.environ, "PATH": str(gcc.parent) + os.pathsep + os.environ["PATH"]}
    executable = tmp_path / "scene_host.exe"
    subprocess.run([str(gcc), "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(root / "core"),
                    str(root / "tests/compiler/scene_host.c"), str(root / "core/scene.c"), "-o", str(executable)],
                   check=True, capture_output=True, text=True, env=environment)
    animation = formatos.animation([{"frame": 0}, {"frame": 60, "x": 192, "zoom": 48}])
    chapter = tmp_path / "test.vnb"
    chapter.write_bytes(formatos.vnb(b"\x46", 0, animations=[animation]))
    for time, expected in [(0, "1 128 256 64 255 0"), (30, "1 160 256 56 255 0"), (-1, "1 192 256 48 255 0")]:
        result = subprocess.run([str(executable), str(chapter), str(time)], capture_output=True,
                                check=True, text=True, env=environment)
        assert result.stdout.strip() == expected


def test_image_events_are_written_and_read_by_native_scene_core(tmp_path):
    root = Path(__file__).resolve().parents[2]
    gcc = Path(r"C:\msys64\ucrt64\bin\gcc.exe")
    environment = {**os.environ, "PATH": str(gcc.parent) + os.pathsep + os.environ["PATH"]}
    executable = tmp_path / "scene_host.exe"
    subprocess.run([str(gcc), "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(root / "core"),
                    str(root / "tests/compiler/scene_host.c"), str(root / "core/scene.c"), "-o", str(executable)],
                   check=True, capture_output=True, text=True, env=environment)
    animation = formatos.animation([{"frame": 0}, {"frame": 60}], True,
                                   [{"frame": 20, "image": 7, "dissolve": 30}, {"frame": 40, "image": 9}])
    assert animation[2] == 2 and animation[3 + 30:] == struct.pack("<HHBHHHBH", 20, 7, 0, 30, 40, 9, 0, 0)
    chapter = tmp_path / "test.vnb"
    chapter.write_bytes(formatos.vnb(b"\x46", 0, animations=[animation]))
    for time, image in [(0, "1"), (20, "7"), (45, "9"), (70, "1")]:
        result = subprocess.run([str(executable), str(chapter), str(time)], capture_output=True,
                                check=True, text=True, env=environment)
        assert result.stdout.split()[0] == image


def test_image_events_reject_bad_order_and_ranges():
    with pytest.raises(ValueError, match="orden"):
        formatos.animation([{"frame": 0}], events=[{"frame": 9, "image": 2}, {"frame": 3, "image": 2}])
    with pytest.raises(ValueError, match="image"):
        formatos.animation([{"frame": 0}], events=[{"frame": 0, "image": 0}])


def test_loop_start_key_repeats_only_the_cycle_in_native_scene_core(tmp_path):
    root = Path(__file__).resolve().parents[2]
    gcc = Path(r"C:\msys64\ucrt64\bin\gcc.exe")
    environment = {**os.environ, "PATH": str(gcc.parent) + os.pathsep + os.environ["PATH"]}
    executable = tmp_path / "scene_host.exe"
    subprocess.run([str(gcc), "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(root / "core"),
                    str(root / "tests/compiler/scene_host.c"), str(root / "core/scene.c"), "-o", str(executable)],
                   check=True, capture_output=True, text=True, env=environment)
    # Intro 0 -> 60 moves x 0 -> 256; the cycle 60 -> 100 goes back to 128.
    animation = formatos.animation([{"frame": 0, "x": 0}, {"frame": 60, "x": 256}, {"frame": 100, "x": 128}],
                                   True, loop_start=1)
    assert animation[1] == 1 | 1 << 1
    chapter = tmp_path / "test.vnb"
    chapter.write_bytes(formatos.vnb(b"\x46", 0, animations=[animation]))
    for time, x in [(30, 128), (60, 256), (100, 256), (120, 192), (-1, 256)]:
        result = subprocess.run([str(executable), str(chapter), str(time)], capture_output=True,
                                check=True, text=True, env=environment)
        assert int(result.stdout.split()[1]) == x
    with pytest.raises(ValueError, match="bucle"):
        formatos.animation([{"frame": 0}, {"frame": 9}], False, loop_start=1)
