"""Pruebas del presupuesto del demake de GBA (T-701)."""

from pathlib import Path

from PIL import Image

from tools.demake import gba_budget


def _lz77_decode(data: bytes) -> bytes:
    """Decodificador de referencia del LZ77 de la BIOS de GBA (GBATEK, tipo 0x10)."""
    assert data[0] == 0x10, "cabecera: tipo 0x10"
    size = data[1] | (data[2] << 8) | (data[3] << 16)
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


def test_bios_lz77_roundtrip():
    data = bytes(range(256)) * 16 + b"lorem ipsum " * 300 + bytes(5000)
    compressed = gba_budget.bios_lz77(data)
    assert compressed[0] == 0x10
    assert compressed[1:4] == len(data).to_bytes(3, "little")
    assert _lz77_decode(compressed) == data
    assert len(compressed) < len(data)


def test_bios_lz77_known_vector():
    # 'a' literal + retroreferencia de longitud 3 y desplazamiento 1.
    assert gba_budget.bios_lz77(b"aaaa") == bytes([0x10, 0x04, 0x00, 0x00, 0x80, 0x61, 0x00, 0x00])


def test_bios_lz77_empty():
    assert gba_budget.bios_lz77(b"") == bytes([0x10, 0x00, 0x00, 0x00])


def test_pack_4bpp():
    # Nibble bajo: pixel izquierdo (GBATEK).
    assert gba_budget.pack_4bpp(b"\x01\x02") == b"\x21"
    assert gba_budget.pack_4bpp(b"\x0f") == b"\x0f"


def test_sample_determinista():
    items = [Path(f"{i:03d}.png") for i in range(100)]
    expected = [items[0], items[25], items[50], items[74], items[99]]
    assert gba_budget._sample(items, 5) == expected
    assert gba_budget._sample(items[:3], 5) == items[:3]


def _gradient(size, color_start, color_end):
    row = Image.new("RGB", (256, 1))
    for x in range(256):
        t = x / 255
        row.putpixel((x, 0), tuple(round(a + (b - a) * t) for a, b in zip(color_start, color_end)))
    return row.resize(size)


def test_background_frame_modo4():
    quant, raw = gba_budget.background_frame(_gradient((1920, 1080), (255, 0, 0), (0, 0, 255)))
    assert quant.size == (240, 160)
    assert quant.mode == "P"
    assert len(raw) == gba_budget.FRAME_BYTES
    assert len(gba_budget.bios_lz77(raw)) < len(raw)


def test_sprite_indices_escala_y_color():
    img = Image.new("RGBA", (100, 200), (0, 0, 0, 0))
    for y in range(50, 150):
        for x in range(10, 90):
            img.putpixel((x, y), (200, 100, 50, 255))
    packed = gba_budget.sprite_indices(img)
    # Region opaca de 80x100 escalada a 160 px de alto: 128x160 indices a 4 bpp.
    assert len(packed) == 128 * 160 // 2


def _make_game(tmp_path: Path) -> Path:
    game = tmp_path / "game"
    (game / "images" / "backgrounds").mkdir(parents=True)
    (game / "images" / "fang").mkdir(parents=True)
    (game / "audio").mkdir(parents=True)
    (game / "tl" / "es").mkdir(parents=True)
    _gradient((1920, 1080), (0, 128, 0), (128, 0, 0)).save(game / "images" / "backgrounds" / "park.png")
    sprite = Image.new("RGBA", (64, 128), (0, 0, 0, 0))
    for y in range(10, 118):
        for x in range(10, 54):
            sprite.putpixel((x, y), (240, 240, 240, 255))
    sprite.save(game / "images" / "fang" / "fang neutral.png")
    (game / "audio" / "theme.ogg").write_bytes(b"ogg")
    (game / "audio" / "click.wav").write_bytes(b"wav")
    (game / "tl" / "es" / "script.rpy").write_text("fang " + '"Hola, Anon." ' * 200, encoding="utf-8")
    return game


def test_build_budget(tmp_path, monkeypatch):
    game = _make_game(tmp_path)
    monkeypatch.setattr(gba_budget, "_probe_duration", lambda p: 30.0 if p.name == "theme.ogg" else 2.5)
    out_dir = tmp_path / "out"
    budget = gba_budget.build_budget(game, "es", sample_size=2, out_dir=out_dir)
    cats = {cat["name"]: cat for cat in budget["categories"]}
    assert set(cats) == {"fondos", "sprites", "musica", "efectos", "texto"}
    assert cats["fondos"]["files"] == 1
    assert cats["sprites"]["files"] == 1
    assert cats["musica"]["bytes"] == 20 * 8000
    assert cats["efectos"]["bytes"] == 20 * 1000
    text = (game / "tl" / "es" / "script.rpy").read_bytes()
    assert cats["texto"]["bytes"] == len(gba_budget.bios_lz77(text))
    assert budget["total"] == sum(cat["bytes"] for cat in budget["categories"])
    assert budget["fits"] is True
    assert budget["free"] == gba_budget.CART_BYTES - budget["total"]
    samples = list(out_dir.glob("*.png"))
    assert len(samples) == 1 and samples[0].name == "backgrounds_park.png"


def test_build_budget_no_cabe(tmp_path, monkeypatch):
    game = _make_game(tmp_path)
    monkeypatch.setattr(gba_budget, "_probe_duration", lambda p: 30.0)
    monkeypatch.setattr(gba_budget, "CART_BYTES", 1000)
    budget = gba_budget.build_budget(game, "es", sample_size=2, out_dir=tmp_path / "out2")
    assert budget["fits"] is False
    assert budget["free"] < 0


def test_build_budget_sin_traduccion(tmp_path):
    game = tmp_path / "game"
    (game / "images").mkdir(parents=True)
    try:
        gba_budget.build_budget(game, "es")
    except ValueError as exc:
        assert "traduccion" in str(exc)
    else:
        raise AssertionError("debio fallar sin tl/es")
