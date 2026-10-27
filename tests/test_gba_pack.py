"""Pruebas del empaquetador de recursos GBA (T-702)."""

import hashlib
import json
import random
from pathlib import Path

from PIL import Image

from tools.demake import gba_pack
from tools.demake.lz77 import bios_lz77, bios_lz77_decompress


def test_lz77_roundtrip_determinista():
    rng = random.Random(702)
    data = bytes(rng.randrange(32) for _ in range(12_000)) + b"GBA" * 2000
    compressed = bios_lz77(data)
    assert compressed == bios_lz77(data)
    assert compressed[:4] == b"\x10" + len(data).to_bytes(3, "little")
    assert bios_lz77_decompress(compressed) == data


def test_lz77_vector_y_errores():
    assert bios_lz77(b"aaaa") == bytes([0x10, 4, 0, 0, 0x80, 0x61, 0, 0])
    assert bios_lz77_decompress(bios_lz77(b"")) == b""
    for invalid in (b"", b"\x11\x00\x00\x00", b"\x10\x03\x00\x00\x00"):
        try:
            bios_lz77_decompress(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("el flujo LZ77 invalido debio rechazarse")


def _make_game(root: Path) -> Path:
    game = root / "game"
    (game / "images" / "backgrounds").mkdir(parents=True)
    (game / "images" / "fang").mkdir(parents=True)
    (game / "audio").mkdir()
    (game / "tl" / "es" / "script").mkdir(parents=True)
    (game / "tl" / "es" / "images" / "backgrounds").mkdir(parents=True)
    Image.new("RGB", (48, 32), (200, 80, 20)).save(game / "images" / "backgrounds" / "park.png")
    Image.new("RGB", (48, 32), (20, 80, 200)).save(
        game / "tl" / "es" / "images" / "backgrounds" / "park.png"
    )
    sprite = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    Image.Image.paste(sprite, Image.new("RGBA", (16, 16), (250, 250, 250, 255)), (4, 4))
    sprite.save(game / "images" / "fang" / "fang.png")
    (game / "audio" / "click.wav").write_bytes(b"audio-fixture")
    (game / "tl" / "es" / "script" / "scene.rpy").write_text(
        'translate es chapter_demo_12345678:\n\n    "Hola, Anon."\n\n'
        'translate es strings:\n\n    old "Start"\n    new "Comenzar"\n',
        encoding="utf-8",
    )
    return game


def test_pack_game_determinista_y_formatos(tmp_path, monkeypatch):
    game = _make_game(tmp_path)
    monkeypatch.setattr(gba_pack.gba_budget, "_probe_duration", lambda _path: 2.0)

    def convert_audio(_src, dst, _duration):
        dst.write_bytes(bytes([0x80, 0, 0x7F]))
        return dst.read_bytes()

    monkeypatch.setattr(gba_pack, "_convert_audio", convert_audio)
    first_out = tmp_path / "out-one"
    second_out = tmp_path / "out-two"
    first = gba_pack.pack_game(game, first_out)
    second = gba_pack.pack_game(game, second_out)
    first_manifest = (first_out / "manifest.json").read_bytes()
    assert first_manifest == (second_out / "manifest.json").read_bytes()
    assert hashlib.sha256(first_manifest).hexdigest() == hashlib.sha256(
        (second_out / "manifest.json").read_bytes()
    ).hexdigest()
    assert first == second
    assert first["categories"]["fondos"] > 512
    assert first["categories"]["sprites"] > 32
    assert first["categories"]["efectos"] == 3
    assert first["text_bin"]["count"] == 2
    assert (first_out / "text.bin").read_bytes() == (second_out / "text.bin").read_bytes()
    assert list((first_out / "bg").glob("*.bin"))
    assert list((first_out / "spr").glob("*.bin"))
    assert list((first_out / "snd").glob("*.bin"))
    assert not list((first_out / "snd").glob("*.tmp"))
    translated = next(item for item in first["resources"] if item["type"] == "background")
    assert translated["path"] == "images/backgrounds/park.png"
    assert translated["sha256"] != hashlib.sha256(
        (game / translated["path"]).read_bytes()
    ).hexdigest()
    assert json.loads(first_manifest)["total_bytes"] == sum(first["categories"].values())

