"""Presupuesto del demake de Snoot Game en GB/GBC (PLAN.md D16 y D19).

Mide si Snoot cabe en una ROM dual GB/GBC con MBC5 de 8 MB con la fidelidad
de D19: fondos en tiles de 8x8 a 2 bits con tramado ordenado Bayer 4x4 de
4 tonos, retratos de 48x48 en vez de sprites completos, efectos simples y
sin musica original, y el texto de ``tl/es`` a 1 byte por glifo comprimido
con el LZ77 de tools/demake/lz77.py (el de la BIOS de GBA; en GB se descomprime por software).

Datos de hardware citados de Pan Docs (gbdev.io/pandocs):
- Pantalla: "an area of 160x144 pixels of this picture can be displayed on
  the LCD screen" (Tile Maps).
- Tiles: "Tile data is stored in VRAM in the memory area at $8000-$97FF;
  with each tile taking 16 bytes, this area defines data for 384 tiles"
  (Tile Data); cada tile es de 8x8 a 2 bpp y el mapa de fondo indexa 256
  tiles sin signo con direccionamiento $8000 (Tile Data).
- GBC: mapa de atributos en el banco 1 de VRAM, bit 3 = banco de tile
  (Tile Maps), y 8 paletas de fondo de 4 colores (FF68/FF69, Palettes).
- MBC5: ROM de hasta 8 MB (MBC5).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from tools.assetpipe.manifest import classify_kind, inventory, source_file
from tools.demake.gba_budget import SPRITE_FOLDERS, _sample
from .lz77 import bios_lz77

CART_BYTES = 8 * 1024 * 1024  # MBC5 (Pan Docs, MBC5)
SCREEN_W, SCREEN_H = 160, 144
TILE = 8
TILE_BYTES = TILE * TILE // 4  # 16 bytes por tile a 2 bpp (Pan Docs, Tile Data)
SCREEN_TILE_W, SCREEN_TILE_H = SCREEN_W // TILE, SCREEN_H // TILE  # 20x18 = 360 tiles
MAP_BYTES = SCREEN_TILE_W * SCREEN_TILE_H
ATTR_BYTES = MAP_BYTES  # mapa de atributos de GBC, 1 byte por celda (Pan Docs, Tile Maps)
VRAM_TILES = 384  # $8000-$97FF (Pan Docs, Tile Data)
BG_MAP_TILES = 256  # indexacion sin signo del mapa de fondo (Pan Docs, Tile Data)
GBC_PALETTE_BYTES = 8 * 4 * 2  # 8 palettes x 4 colores RGB555 (Pan Docs, Palettes)
PORTRAIT = 48  # busto de 48x48 (PLAN.md D19)
TONES = 4  # 4 colores por paleta (Pan Docs, Tile Data)
GLYPHS = 256
FONT_BYTES = GLYPHS * TILE_BYTES
EFFECT_BYTES = 16  # estimado: pares de tono/duracion para los canales de onda cuadrada
SAMPLE_SIZE = 20
BG_SAMPLES = 3
PORTRAIT_SAMPLES = 2
LZ_WINDOW = 4096
LZ_MIN_MATCH = 3
LZ_MAX_MATCH = 18
LZ_MAX_CHAIN = 128

# Matriz de Bayer 4x4 para el tramado ordenado de 4 tonos (PLAN.md D19).
BAYER4 = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))

# Paleta de muestra: tono 0 = negro, 3 = blanco (los indices vienen de la luminancia).
_GRAY_PALETTE = [value for tone in (0, 85, 170, 255) for value in (tone, tone, tone)]


def bayer4_indices(img: Image.Image, width: int, height: int) -> bytes:
    """Recorta la imagen centrada al aspecto ``width:height`` (un fondo 16:9 deja
    la franja que cabe en la pantalla), la escala y cuantiza la luminancia a
    ``TONES`` tonos con tramado ordenado Bayer 4x4 (PLAN.md D19). Devuelve
    ``width*height`` indices: 0 = negro, 3 = blanco."""
    fitted = _fit(img, width, height)
    gray = fitted.convert("L").tobytes()
    step = (256 // TONES) * 16
    out = bytearray(width * height)
    for y in range(height):
        row = BAYER4[y & 3]
        base = y * width
        for x in range(width):
            # Tramado ordenado: el umbral se desplaza (bayer/16 - 0.5) pasos de tono.
            scaled = (gray[base + x] + row[x & 3] * 4 - 32) * 16
            level = scaled // step
            out[base + x] = 0 if level < 0 else 3 if level > 3 else level
    return bytes(out)


def _fit(img: Image.Image, width: int, height: int) -> Image.Image:
    """Recorte centrado al aspecto ``width:height`` y escala final."""
    src_w, src_h = img.size
    ratio = width / height
    if src_w / src_h > ratio:
        crop_w = round(src_h * ratio)
        left = (src_w - crop_w) // 2
        box = (left, 0, left + crop_w, src_h)
    else:
        crop_h = round(src_w / ratio)
        top = (src_h - crop_h) // 2
        box = (0, top, src_w, top + crop_h)
    return img.convert("RGB").crop(box).resize((width, height), Image.LANCZOS)


def split_tiles(indices: bytes, width: int, height: int) -> tuple[list[bytes], bytes]:
    """Parte la pantalla en tiles de 8x8 y los deduplica. Devuelve (tiles unicos,
    bytes del mapa): el byte guarda el indice modulo 256 y los tiles 256-383 van
    al banco 1 de VRAM elegido por el bit 3 del atributo de GBC (Pan Docs, Tile
    Maps y Tile Data)."""
    unique: list[bytes] = []
    index_of: dict[bytes, int] = {}
    map_bytes = bytearray()
    for ty in range(0, height, TILE):
        for tx in range(0, width, TILE):
            tile = bytearray()
            for y in range(ty, ty + TILE):
                base = y * width
                tile += indices[base + tx : base + tx + TILE]
            tile = bytes(tile)
            idx = index_of.get(tile)
            if idx is None:
                idx = len(unique)
                index_of[tile] = idx
                unique.append(tile)
            map_bytes.append(idx & 0xFF)
    return unique, bytes(map_bytes)


def pack_2bpp(tile: bytes) -> bytes:
    """Empaqueta un tile de 64 indices a sus 16 bytes de GB: cada fila son 2 bytes,
    el primero el bit 0 del color y el segundo el bit 1, con el pixel izquierdo en
    el bit 7 (Pan Docs, Tile Data)."""
    out = bytearray(TILE_BYTES)
    for row in range(TILE):
        low = 0
        high = 0
        for col in range(TILE):
            pixel = tile[row * TILE + col]
            low = (low << 1) | (pixel & 1)
            high = (high << 1) | (pixel >> 1)
        out[row * 2] = low
        out[row * 2 + 1] = high
    return bytes(out)


def background_tiles(img: Image.Image) -> tuple[bytes, bytes, bytes, int]:
    """Convierte un fondo a la version GB de D19. Devuelve (indices cuantizados,
    bytes de tiles unicos empaquetados, bytes del mapa, tiles unicos)."""
    indices = bayer4_indices(img, SCREEN_W, SCREEN_H)
    tiles, map_bytes = split_tiles(indices, SCREEN_W, SCREEN_H)
    tile_bytes = b"".join(pack_2bpp(tile) for tile in tiles)
    return indices, tile_bytes, map_bytes, len(tiles)


def portrait_indices(img: Image.Image) -> bytes:
    """Busto de 48x48 (PLAN.md D19: retratos en vez de sprites completos): recorte
    al rectangulo opaco, cuadrado superior centrado del lado minimo y tramado
    Bayer 4x4 a 4 tonos."""
    rgba = img.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox() or (0, 0, rgba.width, rgba.height)
    crop = rgba.crop(bbox)
    side = min(crop.width, crop.height)
    left = (crop.width - side) // 2
    bust = crop.crop((left, 0, left + side, side))
    return bayer4_indices(bust, PORTRAIT, PORTRAIT)


def encode_glyphs(text: str, glyph_ids: dict[str, int]) -> bytes:
    """Codifica texto a 1 byte por caracter con la tabla de glifos; los caracteres
    del espanol entran en la tabla de 256 (PLAN.md D19 y tarea T-703)."""
    table = {ord(ch): idx for ch, idx in glyph_ids.items()}
    return text.translate(table).encode("latin-1")


def _save_sample(indices: bytes, width: int, height: int, dst: Path) -> Path:
    """PNG de muestra escalado x3 con la paleta de 4 tonos."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    img = Image.frombytes("P", (width, height), indices)
    img.putpalette(_GRAY_PALETTE)
    img.resize((width * 3, height * 3), Image.NEAREST).save(dst, format="PNG")
    return dst


def _sample_name(rel: Path, prefix: str) -> str:
    folder = f"{rel.parts[1]}_" if len(rel.parts) > 2 else ""
    return f"{prefix}{folder}{rel.stem}.png".replace(" ", "_")


def _split_images(game_dir: Path) -> tuple[list[Path], list[Path]]:
    """Fondos y retratos: las carpetas de personaje son poses de retrato; el resto
    de images/ son fondos o CG (misma clasificacion que el presupuesto de GBA)."""
    backgrounds: list[Path] = []
    portraits: list[Path] = []
    for rel in inventory(game_dir):
        if classify_kind(rel) != "image" or rel.parts[0] != "images":
            continue
        if len(rel.parts) > 1 and rel.parts[1] in SPRITE_FOLDERS:
            portraits.append(rel)
        else:
            backgrounds.append(rel)
    return backgrounds, portraits


def measure_backgrounds(
    game_dir: Path, language: str | None, sample_size: int, out_dir: Path
) -> tuple[dict, list[str], list[str]]:
    """Presupuesto de fondos: muestra de ``sample_size`` fondos convertidos a tiles
    (deduplicados) + mapa + atributos de GBC + paleta, media extrapolada al total.
    Devuelve (categoria, fondos sobre 256 tiles, fondos sobre 384 tiles)."""
    backgrounds, _ = _split_images(game_dir)
    sample = _sample(backgrounds, sample_size)
    sizes: list[int] = []
    over_map: list[str] = []
    over_vram: list[str] = []
    for idx, rel in enumerate(sample):
        with Image.open(source_file(game_dir, rel, language)) as img:
            indices, tile_bytes, map_bytes, unique = background_tiles(img)
        if unique > VRAM_TILES:
            over_vram.append(rel.as_posix())
        if unique > BG_MAP_TILES:
            over_map.append(rel.as_posix())
        if idx < BG_SAMPLES:
            _save_sample(indices, SCREEN_W, SCREEN_H, out_dir / _sample_name(rel, "bg_"))
        sizes.append(len(tile_bytes) + len(map_bytes) + ATTR_BYTES + GBC_PALETTE_BYTES)
    mean = sum(sizes) / len(sizes) if sizes else 0
    category = {
        "name": "fondos",
        "files": len(backgrounds),
        "sample": len(sample),
        "bytes": round(mean * len(backgrounds)),
        "method": (
            f"muestra de {len(sample)}, media {mean:.0f} B por fondo "
            "(tiles unicos + mapa + atributos + paleta), extrapolada"
        ),
    }
    return category, over_map, over_vram


def measure_portraits(game_dir: Path, language: str | None, sample_size: int, out_dir: Path) -> dict:
    """Presupuesto de retratos: un busto de 48x48 por pose distinta de personaje,
    muestra de ``sample_size`` poses, media extrapolada al total."""
    _, portraits = _split_images(game_dir)
    sample = _sample(portraits, sample_size)
    sizes: list[int] = []
    for idx, rel in enumerate(sample):
        with Image.open(source_file(game_dir, rel, language)) as img:
            indices = portrait_indices(img)
        if idx < PORTRAIT_SAMPLES:
            _save_sample(indices, PORTRAIT, PORTRAIT, out_dir / _sample_name(rel, "retrato_"))
        tiles, map_bytes = split_tiles(indices, PORTRAIT, PORTRAIT)
        tile_bytes = b"".join(pack_2bpp(tile) for tile in tiles)
        sizes.append(len(tile_bytes) + len(map_bytes) + GBC_PALETTE_BYTES)
    mean = sum(sizes) / len(sizes) if sizes else 0
    return {
        "name": "retratos",
        "files": len(portraits),
        "sample": len(sample),
        "bytes": round(mean * len(portraits)),
        "method": f"muestra de {len(sample)}, media {mean:.0f} B por busto de 48x48, extrapolada",
    }


def measure_effects(game_dir: Path) -> dict:
    """Presupuesto de efectos (D19: sin musica original): cada audio del juego se
    sustituye por un zumbido simple de canales de onda cuadrada, sin muestras."""
    files = [rel for rel in inventory(game_dir) if classify_kind(rel) == "audio"]
    return {
        "name": "efectos",
        "files": len(files),
        "sample": len(files),
        "bytes": len(files) * EFFECT_BYTES,
        "method": "estimado: zumbidos generados por registros, 16 B por efecto",
    }


def measure_text(game_dir: Path, language: str) -> tuple[dict, int]:
    """Presupuesto del texto: los .rpy de tl/<idioma> a 1 byte por glifo con la
    tabla de 256 glifos, comprimidos con LZ77. Devuelve (categoria, caracteres
    distintos usados)."""
    paths = sorted((game_dir / "tl" / language).rglob("*.rpy"))
    contents = [path.read_bytes().decode("utf-8") for path in paths]
    glyphs = sorted(set("".join(contents)))
    if len(glyphs) > GLYPHS:
        raise ValueError(
            f"{len(glyphs)} caracteres distintos en tl/{language}: no caben en la tabla de {GLYPHS} glifos"
        )
    glyph_ids = {ch: idx for idx, ch in enumerate(glyphs)}
    raw = 0
    compressed = 0
    for text in contents:
        raw += len(text)
        compressed += len(bios_lz77(encode_glyphs(text, glyph_ids)))
    category = {
        "name": "texto",
        "files": len(paths),
        "sample": len(paths),
        "bytes": compressed,
        "method": f"{raw} caracteres a 1 byte por glifo, comprimidos con LZ77 propio",
    }
    return category, len(glyphs)


def build_budget(
    game_dir: Path, language: str, sample_size: int = SAMPLE_SIZE, out_dir: Path | None = None
) -> dict:
    """Ejecuta todas las medidas y devuelve el presupuesto completo."""
    game_dir = Path(game_dir)
    if not game_dir.is_dir():
        raise ValueError(f"no existe el directorio de juego: {game_dir}")
    if not (game_dir / "tl" / language).is_dir():
        raise ValueError(f"el juego no trae la traduccion {language} (falta {game_dir / 'tl' / language})")
    out_dir = Path(out_dir) if out_dir else Path("build/demake/gb")
    backgrounds, over_map, over_vram = measure_backgrounds(game_dir, language, sample_size, out_dir)
    text, glyphs_used = measure_text(game_dir, language)
    categories = [
        backgrounds,
        measure_portraits(game_dir, language, sample_size, out_dir),
        {
            "name": "glifos",
            "files": GLYPHS,
            "sample": GLYPHS,
            "bytes": FONT_BYTES,
            "method": f"tabla de {GLYPHS} glifos de 8x8 a 2 bpp ({glyphs_used} caracteres de tl/es)",
        },
        measure_effects(game_dir),
        text,
    ]
    total = sum(cat["bytes"] for cat in categories)
    return {
        "game": str(game_dir),
        "language": language,
        "cart_bytes": CART_BYTES,
        "categories": categories,
        "total": total,
        "free": CART_BYTES - total,
        "fits": total <= CART_BYTES,
        "samples_dir": str(out_dir),
        "over_map": over_map,
        "over_vram": over_vram,
        "glyphs": glyphs_used,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Presupuesto del demake de GB/GBC: dice si el juego cabe en una ROM MBC5 de 8 MB"
    )
    parser.add_argument("--game", required=True, help="directorio game del juego")
    parser.add_argument("--language", default="es", help="idioma de la traduccion (D16: es)")
    parser.add_argument("--sample", type=int, default=SAMPLE_SIZE, help="tamano de la muestra de imagenes")
    parser.add_argument("--out", default="build/demake/gb", help="directorio para los PNG de muestra")
    args = parser.parse_args(argv)
    budget = build_budget(Path(args.game), args.language, args.sample, Path(args.out))
    print(f"Presupuesto GB/GBC de {budget['game']} (idioma: {budget['language']})")
    print(f"{'categoria':<10}{'archivos':>10}{'bytes':>14}  metodo")
    for cat in budget["categories"]:
        print(f"{cat['name']:<10}{cat['files']:>10}{cat['bytes']:>14,}  {cat['method']}")
    total, cart = budget["total"], budget["cart_bytes"]
    percent = total / cart * 100
    print(f"{'total':<10}{'':>10}{total:>14,}  {percent:.1f}% de {cart:,} bytes (8 MB, MBC5)")
    if budget["fits"]:
        print(f"VEREDICTO: CABE en la ROM de 8 MB; sobran {budget['free']:,} bytes")
    else:
        print(f"VEREDICTO: NO CABE; faltan {-budget['free']:,} bytes (ver docs/demake-gb.md)")
    for label, over in (
        ("256 tiles (solo GBC: mapa de atributos, banco de VRAM 1)", budget["over_map"]),
        ("384 tiles (no caben ni en GBC: mas tramado o recorte)", budget["over_vram"]),
    ):
        count = len(over)
        print(f"fondos de la muestra sobre {label}: {count}")
        for rel in over:
            print(f"  {rel}")
    print(f"PNG de muestra: {budget['samples_dir']}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
