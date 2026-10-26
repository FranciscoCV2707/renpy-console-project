import math
import os
import struct
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from vncompiler import formatos
from vncompiler.temporal import animation_from_timeline, rotated_center

ROOT = Path(__file__).resolve().parents[2]
GCC = Path(r"C:\msys64\ucrt64\bin\gcc.exe")
ENVIRONMENT = {**os.environ, "PATH": str(GCC.parent) + os.pathsep + os.environ["PATH"]}


def build(tmp_path, host):
    executable = tmp_path / (host + ".exe")
    subprocess.run([str(GCC), "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT / "core"),
                    str(ROOT / "tests/compiler" / (host + ".c")), str(ROOT / "core/scene.c"), "-o", str(executable)],
                   check=True, capture_output=True, text=True, env=ENVIRONMENT)
    return executable


def run(executable, *arguments):
    return subprocess.run([str(executable), *map(str, arguments)], capture_output=True, check=True, text=True,
                          env=ENVIRONMENT).stdout.split()


@dataclass
class Timeline:
    """rotate_funny of Wani (00src/definitions/transforms.rpy): ease_cubic to rotate 5 around the anchor."""
    state: dict
    rotate: float = 5
    duration: float = 1
    loop_start: float | None = None
    diagnostics: list = field(default_factory=list)

    def sample(self, seconds):
        fraction = min(1, seconds / self.duration)
        eased = 4 * fraction ** 3 if fraction < .5 else 1 - (-2 * fraction + 2) ** 3 / 2
        return {**self.state, **({"rotate": self.rotate * eased} if self.rotate is not None else {})}


FUNNY = {"xpos": 960, "ypos": 1080, "xanchor": 500, "yanchor": 750, "yoffset": 750, "zoom": .5, "alpha": 1,
         "transform_anchor": 1.0}


def test_keys_without_rotation_keep_the_old_bytes():
    keys = [{"frame": 0}, {"frame": 60, "x": 192, "zoom": 48, "curve": 3}]
    blob = formatos.animation(keys, True)
    assert blob == formatos.animation([{**key, "angle": 0} for key in keys], True)
    assert blob[1] == 1
    assert struct.unpack_from("<HhhBBBbbBBBB", blob, 18) == (60, 192, 256, 255, 3, 48, 64, 0, 128, 128, 128, 255)


def test_timeline_without_rotation_is_byte_identical():
    timeline = Timeline({**FUNNY, "transform_anchor": 0.0}, rotate=None)
    result = animation_from_timeline(timeline, (1920, 1080), (1000, 1500), tolerance=6)
    assert all("angle" not in key for key in result["keyframes"])
    blob = formatos.animation(result["keyframes"])
    assert blob[1] & 0x80 == 0 and blob[3 + 9:3 + 11] == bytes([64, 0])


def test_angle_sets_flag_bit_7_and_writes_s16():
    blob = formatos.animation([{"frame": 0}, {"frame": 60, "angle": -4096}, {"frame": 90, "angle": 57}], True,
                              loop_start=1)
    assert blob[1] == 0x80 | 1 << 1 | 1
    assert [struct.unpack_from("<h", blob, 3 + 15 * index + 9)[0] for index in range(3)] == [0, -4096, 57]
    assert struct.unpack_from("<BBBB", blob, 3 + 11) == (128, 128, 128, 255)


@pytest.mark.parametrize("angle", [32768, -32769, 1.5, True])
def test_angle_out_of_range_is_rejected(angle):
    with pytest.raises(ValueError, match="angle"):
        formatos.animation([{"frame": 0, "angle": angle}])


def test_rotation_around_the_anchor_by_hand():
    # 100x200 image, anchor at its foot, 90 degrees clockwise: the foot stays at pos, the center lies to its right.
    state = {"xpos": 500, "ypos": 500, "xanchor": 50, "yanchor": 200, "rotate": 90, "transform_anchor": 1.0}
    assert rotated_center(state, 1, (100, 200)) == pytest.approx((600, 500))
    # Mirrored, the anchor at the right edge goes to the left side of the center before turning.
    state = {**state, "xanchor": 100, "yanchor": 100, "rotate": 0}
    assert rotated_center(state, 1, (100, 200), mirror=True) == pytest.approx((550, 500))


def test_rotation_without_transform_anchor_uses_the_padded_box():
    # rotate_pad: a 300x400 image turns inside a 500x500 square; align (0.5, 1.0) sits that square on pos.
    state = {"xpos": 960, "ypos": 1080, "xanchor": 150, "yanchor": 400, "rotate": 30}
    assert rotated_center(state, 1, (300, 400)) == pytest.approx((960, 830))


def test_rotate_funny_keeps_the_anchor_on_pos():
    screen, size = (1920, 1080), (1000, 1500)
    result = animation_from_timeline(Timeline(FUNNY), screen, size, tolerance=6)
    keys = result["keyframes"]
    assert keys[0]["angle"] == 0 and keys[-1]["angle"] == round(5 * 4096 / 360)
    assert 2 < len(keys) < 64
    blob = formatos.animation(keys)
    assert blob[1] & 0x80
    for key in keys:
        # Engine placement: alignment over the free room, rotation around the image center.
        zoom = key["zoom"] / 64
        width, height = size[0] * zoom, size[1] * zoom
        center = (key["x"] / 256 * (screen[0] - width) + width / 2, key["y"] / 256 * (screen[1] - height) + height / 2)
        angle = key["angle"] * 2 * math.pi / 4096
        dx, dy = (FUNNY["xanchor"] - size[0] / 2) * zoom, (FUNNY["yanchor"] - size[1] / 2) * zoom
        anchor = (center[0] + dx * math.cos(angle) - dy * math.sin(angle),
                  center[1] + dx * math.sin(angle) + dy * math.cos(angle))
        assert anchor[0] == pytest.approx(FUNNY["xpos"], abs=abs(screen[0] - width) / 256)
        assert anchor[1] == pytest.approx(FUNNY["ypos"] + FUNNY["yoffset"], abs=abs(screen[1] - height) / 256 + 1)


def test_scene_core_reads_and_interpolates_the_angle(tmp_path):
    executable = build(tmp_path, "scene_host")
    rotated = formatos.animation([{"frame": 0}, {"frame": 60, "angle": 400}])
    # Snoot writes a rotation in byte 10 without bit 7: the engine must keep ignoring it.
    snoot = bytearray(formatos.animation([{"frame": 0}, {"frame": 60}]))
    snoot[3 + 15 + 10] = 20
    chapter = tmp_path / "test.vnb"
    chapter.write_bytes(formatos.vnb(b"\x46", 0, animations=[rotated, bytes(snoot)]))
    assert [run(executable, chapter, time)[5] for time in (0, 30, -1)] == ["0", "200", "400"]
    assert [run(executable, chapter, time, 2)[5] for time in (0, 30, -1)] == ["0", "0", "0"]


def test_capture_keeps_the_angle_and_rotate_is_clockwise(tmp_path):
    executable = build(tmp_path, "rotate_host")
    chapter = tmp_path / "test.vnb"
    chapter.write_bytes(formatos.vnb(b"\x46", 0, animations=[
        formatos.animation([{"frame": 0}, {"frame": 60, "angle": -1024}]),
        formatos.animation([{"frame": 0}, {"frame": 60}])]))
    assert run(executable, chapter) == ["0", "100", "50", "0", "-512", "-512", "-256", "0"]
