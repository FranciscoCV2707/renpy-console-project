"""Pruebas del empaquetador de recursos GB/GBC (T-704)."""

import hashlib
import json
import random

from PIL import Image

from tools.demake import gb_budget, gb_pack


def _make_game(root):
    game = root / "game"
    (game / "images" / "backgrounds").mkdir(parents=True)
    (game / "images" / "fang").mkdir(parents=True)
    (game / "tl" / "es" / "script").mkdir(parents=True)
    image = Image.new("L", (160, 144))
    rng = random.Random(704)
    image.putdata([rng.randrange(256) for _ in range(160 * 144)])
    image.save(game / "images" / "backgrounds" / "noise.png")
    portrait = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    portrait.paste(Image.new("RGBA", (32, 32), (230, 120, 70, 255)), (8, 8))
    portrait.save(game / "images" / "fang" / "fang.png")
    (game / "tl" / "es" / "script" / "scene.rpy").write_text(
        'translate es chapter_demo_12345678:\n    "¡Hola, Anon!"\n',
        encoding="utf-8",
    )
    return game


def test_pack_game_es_determinista_y_layouts(tmp_path):
    game = _make_game(tmp_path)
    first_out = tmp_path / "first"
    second_out = tmp_path / "second"
    first = gb_pack.pack_game(game, first_out)
    second = gb_pack.pack_game(game, second_out)
    first_manifest = (first_out / "manifest.json").read_bytes()
    assert first_manifest == (second_out / "manifest.json").read_bytes()
    assert hashlib.sha256(first_manifest).hexdigest() == hashlib.sha256(
        (second_out / "manifest.json").read_bytes()
    ).hexdigest()
    assert first == second
    assert first["fits"] is True
    assert first["glyphs"] == len(gb_budget.glyph_table(game, "es"))
    assert len((first_out / "font.bin").read_bytes()) == gb_budget.FONT_BYTES
    assert (first_out / "text.bin").read_bytes() == (second_out / "text.bin").read_bytes()
    assert list((first_out / "bg").glob("*.bin"))
    assert list((first_out / "face").glob("*.bin"))
    background = next(item for item in first["resources"] if item["type"] == "background")
    assert background["unique_tiles"] <= gb_budget.VRAM_TILES
    assert first["total_bytes"] == sum(first["categories"].values())
    assert json.loads(first_manifest)["resources"] == first["resources"]


def test_background_banco_atributos_y_mapas(tmp_path):
    image = Image.new("L", (160, 144))
    rng = random.Random(704)
    image.putdata([rng.randrange(4) * 85 for _ in range(160 * 144)])
    path = tmp_path / "tiles.png"
    image.save(path)
    payload, unique = gb_pack._background(path)
    assert unique == 360
    assert len(payload) > gb_budget.MAP_BYTES * 2 + gb_budget.GBC_PALETTE_BYTES


def test_pack_rechaza_salida_dentro_del_juego(tmp_path):
    game = _make_game(tmp_path)
    try:
        gb_pack.pack_game(game, game / "packed")
    except ValueError as exc:
        assert "dentro de --game" in str(exc)
    else:
        raise AssertionError("debio rechazar una salida dentro de --game")
