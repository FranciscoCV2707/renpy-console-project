"""Pruebas del presupuesto del demake de GB/GBC (T-703)."""

import random
from pathlib import Path

from PIL import Image

from tools.demake import gb_budget


def _lz77_decode(data: bytes) -> bytes:
    """Decodificador de referencia del LZ77 propio de gb_budget: tamano en 32 bits
    little-endian y bloques de flags + 8 unidades."""
    size = int.from_bytes(data[:4], "little")
    out = bytearray()
    i = 4
    while len(out) < size:
        flags = data[i]
        i += 1
        for bit in range(7, -1, -1):
            if len(out) >= size:
                break
            if flags & (1 << bit):
                out.append(data[i])
                i += 1
            else:
                token = (data[i] << 8) | data[i + 1]
                i += 2
                length = (token >> 12) + 3
                disp = (token & 0xFFF) + 1
                assert 3 <= length <= 18, "longitud fuera de rango"
                assert 1 <= disp <= 4096, "desplazamiento fuera de la ventana"
                assert disp <= len(out), "referencia anterior al inicio"
                for _ in range(length):
                    out.append(out[-disp])
    assert len(out) == size
    return bytes(out)


def test_lz77_roundtrip():
    rng = random.Random(42)
    data = rng.randbytes(1000) + b"lorem ipsum " * 300 + bytes(5000) + rng.randbytes(200)
    compressed = gb_budget.lz77(data)
    assert compressed[:4] == len(data).to_bytes(4, "little")
    assert _lz77_decode(compressed) == data
    assert len(compressed) < len(data)


def test_lz77_known_vector():
    # 'a' literal + retroreferencia de longitud 3 y desplazamiento 1.
    assert gb_budget.lz77(b"aaaa") == bytes([0x04, 0x00, 0x00, 0x00, 0x80, 0x61, 0x00, 0x00])


def test_lz77_empty():
    assert gb_budget.lz77(b"") == bytes(4)


def test_lz77_bloque_grande_rechazado():
    class TooBig:
        def __len__(self):
            return 1 << 32

    try:
        gb_budget.lz77(TooBig())  # type: ignore[arg-type]
    except ValueError as exc:
        assert "4 GiB" in str(exc)
    else:
        raise AssertionError("debio rechazar bloques de mas de 4 GiB")


def test_pack_2bpp():
    # Pan Docs (Tile Data): byte 0 = bit 0 del color, byte 1 = bit 1, bit 7 = pixel izquierdo.
    row = bytes([1, 0, 2, 3, 0, 0, 1, 2])
    tile = row * 8
    packed = gb_budget.pack_2bpp(tile)
    assert len(packed) == 16
    assert packed[0] == 0b10010010  # bit 0 de cada pixel, MSB = izquierda
    assert packed[1] == 0b00110001  # bit 1 de cada pixel


def test_bayer4_indices_recorte_y_tonos():
    # Franja central negra en un fondo 16:9 blanco: el recorte 10:9 la conserva.
    img = Image.new("RGB", (1920, 1080), (255, 255, 255))
    for x in range(860, 1060):
        for y in range(1080):
            img.putpixel((x, y), (0, 0, 0))
    indices = gb_budget.bayer4_indices(img, 160, 144)
    assert len(indices) == 160 * 144
    assert set(indices) <= {0, 1, 2, 3}
    assert 0 in indices and 3 in indices  # negro y blanco presentes


def test_bayer4_indices_determinista_y_ordenado():
    img = Image.new("RGB", (320, 240), (128, 128, 128))
    indices = gb_budget.bayer4_indices(img, 160, 144)
    assert indices == gb_budget.bayer4_indices(img, 160, 144)
    # Gris medio con Bayer 4x4: solo tonos 1 y 2, en proporcion cercana a mitad y mitad.
    assert set(indices) <= {1, 2}
    ones = indices.count(1)
    assert abs(ones - len(indices) // 2) < len(indices) * 0.05


def test_split_tiles_deduplica():
    flat = bytes(160 * 144)  # pantalla negra plana
    tiles, map_bytes = gb_budget.split_tiles(flat, 160, 144)
    assert len(tiles) == 1
    assert len(map_bytes) == 360
    assert set(map_bytes) == {0}


def test_split_tiles_ruido_360_unicos():
    rng = random.Random(7)
    noise = bytes(rng.randrange(4) for _ in range(160 * 144))
    tiles, map_bytes = gb_budget.split_tiles(noise, 160, 144)
    assert len(tiles) == 360  # 20x18 tiles, todos distintos
    assert len(map_bytes) == 360
    # Indices 256-359: el byte guarda el modulo 256 y el banco lo da el atributo.
    assert map_bytes == bytes(i & 0xFF for i in range(360))


def test_background_tiles():
    rng = random.Random(7)
    tones = bytes(rng.randrange(4) for _ in range(160 * 144))
    img = Image.new("L", (160, 144))
    img.putdata([tone * 85 for tone in tones])
    indices, tile_bytes, map_bytes, unique = gb_budget.background_tiles(img)
    assert len(indices) == 160 * 144
    assert unique == 360
    assert len(tile_bytes) == 360 * 16
    assert len(map_bytes) == 360


def test_portrait_indices_busto():
    sprite = Image.new("RGBA", (100, 200), (0, 0, 0, 0))
    for y in range(50, 150):
        for x in range(10, 90):
            sprite.putpixel((x, y), (200, 100, 50, 255))
    indices = gb_budget.portrait_indices(sprite)
    assert len(indices) == 48 * 48
    assert set(indices) <= {0, 1, 2, 3}


def test_encode_glyphs():
    glyph_ids = {ch: idx for idx, ch in enumerate(" !áHola")}
    encoded = gb_budget.encode_glyphs("Hola!", glyph_ids)
    assert encoded == bytes([glyph_ids["H"], glyph_ids["o"], glyph_ids["l"], glyph_ids["a"], glyph_ids["!"]])
    # El espanol entra en la tabla: 1 byte por caracter.
    assert len(gb_budget.encode_glyphs("¡Ño!", glyph_ids)) == 4


def test_measure_text_tabla_de_glifos(tmp_path):
    (tmp_path / "tl" / "es").mkdir(parents=True)
    (tmp_path / "tl" / "es" / "script.rpy").write_text(
        "fang \"¡Hola, Anon! ¿Qué tal?\"", encoding="utf-8"
    )
    (tmp_path / "tl" / "es" / "extra.rpy").write_text("naser ññ", encoding="utf-8")
    category, glyphs_used = gb_budget.measure_text(tmp_path, "es")
    assert category["files"] == 2
    assert category["bytes"] > 0
    expected = set('fang "¡Hola, Anon! ¿Qué tal?"') | set("naser ññ")
    assert glyphs_used == len(expected)


def _make_game(tmp_path: Path) -> Path:
    game = tmp_path / "game"
    (game / "images" / "backgrounds").mkdir(parents=True)
    (game / "images" / "fang").mkdir(parents=True)
    (game / "audio").mkdir(parents=True)
    (game / "tl" / "es").mkdir(parents=True)
    rng = random.Random(7)
    noise = bytes(rng.randrange(256) for _ in range(160 * 144))
    park = Image.new("L", (160, 144))
    park.putdata(noise)
    park.save(game / "images" / "backgrounds" / "park.png")
    sprite = Image.new("RGBA", (64, 128), (0, 0, 0, 0))
    for y in range(10, 118):
        for x in range(10, 54):
            sprite.putpixel((x, y), (240, 240, 240, 255))
    sprite.save(game / "images" / "fang" / "fang neutral.png")
    (game / "audio" / "click.wav").write_bytes(b"wav")
    (game / "tl" / "es" / "script.rpy").write_text("fang \"¡Hola, Anon!\" " * 50, encoding="utf-8")
    return game


def test_build_budget(tmp_path):
    game = _make_game(tmp_path)
    out_dir = tmp_path / "out"
    budget = gb_budget.build_budget(game, "es", sample_size=2, out_dir=out_dir)
    cats = {cat["name"]: cat for cat in budget["categories"]}
    assert set(cats) == {"fondos", "retratos", "glifos", "efectos", "texto"}
    assert cats["fondos"]["files"] == 1
    assert cats["retratos"]["files"] == 1
    assert cats["glifos"]["bytes"] == 256 * 16
    assert cats["efectos"]["bytes"] == gb_budget.EFFECT_BYTES
    assert cats["texto"]["bytes"] > 0
    assert budget["total"] == sum(cat["bytes"] for cat in budget["categories"])
    assert budget["fits"] is True
    assert budget["free"] == gb_budget.CART_BYTES - budget["total"]
    assert budget["glyphs"] < 256
    samples = sorted(p.name for p in out_dir.glob("*.png"))
    assert samples == ["bg_backgrounds_park.png", "retrato_fang_fang_neutral.png"]
    assert out_dir.joinpath("bg_backgrounds_park.png").stat().st_size > 0


def test_build_budget_no_cabe(tmp_path, monkeypatch):
    game = _make_game(tmp_path)
    monkeypatch.setattr(gb_budget, "CART_BYTES", 1000)
    budget = gb_budget.build_budget(game, "es", sample_size=2, out_dir=tmp_path / "out2")
    assert budget["fits"] is False
    assert budget["free"] < 0


def test_build_budget_fondo_sobre_256_tiles(tmp_path):
    game = _make_game(tmp_path)
    rng = random.Random(7)
    noise = bytes(rng.randrange(4) for _ in range(160 * 144))
    noisy = Image.new("L", (160, 144))
    noisy.putdata([tone * 85 for tone in noise])
    noisy.save(game / "images" / "backgrounds" / "noise.png")
    budget = gb_budget.build_budget(game, "es", sample_size=2, out_dir=tmp_path / "out3")
    # Los dos fondos de ruido tienen tiles de sobra: sobre 256 (solo GBC), no sobre 384.
    assert len(budget["over_map"]) == 2
    assert any(rel.endswith("noise.png") for rel in budget["over_map"])
    assert budget["over_vram"] == []


def test_build_budget_sin_traduccion(tmp_path):
    game = tmp_path / "game"
    (game / "images").mkdir(parents=True)
    try:
        gb_budget.build_budget(game, "es")
    except ValueError as exc:
        assert "traduccion" in str(exc)
    else:
        raise AssertionError("debio fallar sin tl/es")


def test_measure_text_glifos_insuficientes(tmp_path):
    (tmp_path / "tl" / "es").mkdir(parents=True)
    (tmp_path / "tl" / "es" / "script.rpy").write_text(
        "".join(chr(i) for i in range(300)), encoding="utf-8"
    )
    try:
        gb_budget.measure_text(tmp_path, "es")
    except ValueError as exc:
        assert "glifos" in str(exc)
    else:
        raise AssertionError("debio fallar con mas de 256 caracteres distintos")
