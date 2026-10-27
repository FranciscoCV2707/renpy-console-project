"""Presupuesto del demake de Snoot Game en GBA (PLAN.md D16 y D19).

Mide cuánto ocuparía cada categoría de recursos en un cartucho de 32 MB:
fondos (fotogramas de modo 4 de 240x160 a 256 colores), sprites de personaje
(a 16 colores, con el personaje a 160 px de alto), música (PCM de 8 bits mono
a 8 kHz en bucles de 20 s), efectos (PCM completo) y texto (``tl/es`` en
UTF-8). Reutiliza el inventario de assetpipe; no lo duplica.

Datos de hardware citados de GBATEK:
- Cartucho máximo: 32 MB ("GBA Cartridges ... max 32MB").
- Modo 4: 240x160 px, 8 bpp, 256 colores; un fotograma son 38.400 bytes
  ("Video Mode 4 - 240x160, 8bit (256 colors)").
- Sprites y tiles de 4 bpp: 16 colores por paleta ("OBJ Tiles 4bit / 16x16").
- LZ77 de la BIOS: tipo 0x10, ventana de 4096 bytes, coincidencias de 3 a 18
  ("LZ77 Decompression (SWI 11h)").
"""

from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path

from PIL import Image

from tools.assetpipe.manifest import classify_kind, inventory, source_file

CART_BYTES = 32 * 1024 * 1024
SCREEN_W, SCREEN_H = 240, 160
FRAME_BYTES = SCREEN_W * SCREEN_H  # 38.400: modo 4, 1 byte por pixel (GBATEK)
BG_COLORS = 256
BG_PALETTE_BYTES = BG_COLORS * 2  # color BGR555 de 2 bytes (GBATEK)
SPRITE_COLORS = 16
SPRITE_PALETTE_BYTES = SPRITE_COLORS * 2
SPRITE_CHAR_HEIGHT = 160
MUSIC_THRESHOLD_S = 10.0  # mismo criterio musica/efecto que assetpipe (perfiles, D18)
MUSIC_LOOP_S = 20.0
PCM_RATE = 8000
LZ77_WINDOW = 4096
LZ77_MIN_MATCH = 3
LZ77_MAX_MATCH = 18
LZ77_MAX_CHAIN = 128
SAMPLE_SIZE = 20
PNG_SAMPLES = 3

# Carpetas de images/ con sprites de personaje de Snoot; el resto son fondos o CG.
SPRITE_FOLDERS = frozenset(
    {
        "anon",
        "fang",
        "fangparents",
        "highres",
        "moe",
        "naomi",
        "naser",
        "reed",
        "rosa",
        "spears",
        "stella",
        "tracy",
        "trish",
        "trishfam",
    }
)


def bios_lz77(data: bytes) -> bytes:
    """Comprime ``data`` en el formato LZ77 de la BIOS de GBA (GBATEK, tipo 0x10).

    Cabecera: byte 0x10 mas el tamano sin comprimir en 24 bits little-endian.
    Bloques: byte de flags seguido de 8 unidades; bit a 1 (MSB primero) = byte
    literal, bit a 0 = par de bytes con (longitud-3) en el nibble alto y
    (desplazamiento-1) en 12 bits, big-endian. Ventana de 4096, longitudes de
    3 a 18. Busca la coincidencia mas larga con cadenas de hash de 3 bytes.
    """
    size = len(data)
    if size > 0xFFFFFF:
        raise ValueError(f"LZ77 de la BIOS: maximo 16 MiB, recibe {size} bytes")
    out = bytearray((0x10, size & 0xFF, (size >> 8) & 0xFF, (size >> 16) & 0xFF))
    head: dict[int, int] = {}
    prev = [-1] * size
    n = size
    i = 0
    while i < n:
        flags = 0
        block = bytearray()
        for bit in range(7, -1, -1):
            if i >= n:
                break
            length, disp = _longest_match(data, i, n, head, prev)
            if length >= LZ77_MIN_MATCH:
                block.append(((length - LZ77_MIN_MATCH) << 4) | ((disp - 1) >> 8))
                block.append((disp - 1) & 0xFF)
                for pos in range(i, min(i + length, n - LZ77_MIN_MATCH + 1)):
                    _insert(data, head, prev, pos)
                i += length
            else:
                flags |= 1 << bit
                block.append(data[i])
                if i + LZ77_MIN_MATCH <= n:
                    _insert(data, head, prev, i)
                i += 1
        out.append(flags)
        out += block
    return bytes(out)


def _insert(data: bytes, head: dict[int, int], prev: list[int], pos: int) -> None:
    key = (data[pos] << 16) | (data[pos + 1] << 8) | data[pos + 2]
    prev[pos] = head.get(key, -1)
    head[key] = pos


def _longest_match(data: bytes, i: int, n: int, head: dict[int, int], prev: list[int]) -> tuple[int, int]:
    """La coincidencia mas larga en la ventana de 4096 bytes desde ``i``: (longitud, desplazamiento)."""
    if i + LZ77_MIN_MATCH > n:
        return 0, 0
    max_len = min(LZ77_MAX_MATCH, n - i)
    best_len, best_disp = 0, 0
    pos = head.get((data[i] << 16) | (data[i + 1] << 8) | data[i + 2], -1)
    low = i - LZ77_WINDOW
    chain = 0
    while pos >= 0 and pos >= low and chain < LZ77_MAX_CHAIN:
        length = LZ77_MIN_MATCH
        while length < max_len and data[pos + length] == data[i + length]:
            length += 1
        if length > best_len:
            best_len, best_disp = length, i - pos
            if length >= max_len:
                break
        pos = prev[pos]
        chain += 1
    return best_len, best_disp


def pack_4bpp(indices: bytes) -> bytes:
    """Empaqueta indices de paleta (un byte por pixel) a 4 bpp, como los tiles de GBA
    (GBATEK: el nibble bajo es el pixel izquierdo). Rellena con 0 si la cuenta es impar."""
    out = bytearray((len(indices) + 1) // 2)
    for i in range(0, len(indices), 2):
        left = indices[i]
        right = indices[i + 1] if i + 1 < len(indices) else 0
        out[i // 2] = (right << 4) | left
    return bytes(out)


def _fit_frame(img: Image.Image) -> Image.Image:
    """Encaja la imagen en un fotograma de 240x160 conservando el aspecto, con banda negra."""
    frame = Image.new("RGB", (SCREEN_W, SCREEN_H))
    scale = min(SCREEN_W / img.width, SCREEN_H / img.height)
    size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    resized = img.convert("RGB").resize(size, Image.LANCZOS)
    frame.paste(resized, ((SCREEN_W - size[0]) // 2, (SCREEN_H - size[1]) // 2))
    return frame


def background_frame(img: Image.Image) -> tuple[Image.Image, bytes]:
    """Fotograma de modo 4: 240x160 a 256 colores con tramado Floyd-Steinberg
    (PLAN.md D19). Devuelve (imagen cuantizada, 38.400 bytes de indices a 8 bpp)."""
    quant = _fit_frame(img).quantize(colors=BG_COLORS, dither=Image.Dither.FLOYDSTEINBERG)
    return quant, quant.tobytes()


def sprite_indices(img: Image.Image) -> bytes:
    """Recorta al rectangulo opaco del personaje, lo escala a 160 px de alto y cuantiza
    a 16 colores con tramado (PLAN.md D19). Devuelve los indices empaquetados a 4 bpp."""
    rgba = img.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox() or (0, 0, rgba.width, rgba.height)
    crop = rgba.crop(bbox)
    scale = SPRITE_CHAR_HEIGHT / crop.height
    size = (max(1, round(crop.width * scale)), SPRITE_CHAR_HEIGHT)
    quant = crop.resize(size, Image.LANCZOS).quantize(
        colors=SPRITE_COLORS, dither=Image.Dither.FLOYDSTEINBERG
    )
    return pack_4bpp(quant.tobytes())


def _probe_duration(path: Path) -> float:
    """Duracion en segundos del audio con ffprobe (formato=duration)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return float(out)


def _sample(items: list[Path], size: int) -> list[Path]:
    """Muestra determinista de ``size`` elementos, espaciados uniformemente en la lista ordenada."""
    if len(items) <= size:
        return items
    step = (len(items) - 1) / (size - 1)
    return [items[round(i * step)] for i in range(size)]


def _save_sample(quant: Image.Image, rel: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    folder = f"{rel.parts[1]}_" if len(rel.parts) > 2 else ""
    dst = out_dir / f"{folder}{rel.stem}.png".replace(" ", "_")
    quant.save(dst, format="PNG")
    return dst


def measure_images(
    game_dir: Path, language: str | None, sample_size: int, out_dir: Path
) -> list[dict]:
    """Presupuesto de fondos y sprites: convierte una muestra de ``sample_size`` de cada
    categoria, comprime con LZ77 de la BIOS y extrapola la media al total."""
    backgrounds: list[Path] = []
    sprites: list[Path] = []
    for rel in inventory(game_dir):
        if classify_kind(rel) != "image" or rel.parts[0] != "images":
            continue
        if len(rel.parts) > 1 and rel.parts[1] in SPRITE_FOLDERS:
            sprites.append(rel)
        else:
            backgrounds.append(rel)
    categories = []
    for name, files, convert, palette_bytes in (
        ("fondos", backgrounds, background_frame, BG_PALETTE_BYTES),
        ("sprites", sprites, sprite_indices, SPRITE_PALETTE_BYTES),
    ):
        sample = _sample(files, sample_size)
        compressed = []
        for idx, rel in enumerate(sample):
            with Image.open(source_file(game_dir, rel, language)) as img:
                result = convert(img)
            if name == "fondos":
                quant, raw = result
                if idx < PNG_SAMPLES:
                    _save_sample(quant, rel, out_dir)
            else:
                raw = result
            compressed.append(len(bios_lz77(raw)))
        mean = sum(compressed) / len(compressed) if compressed else 0
        # Un cartucho real guarda cada fotograma y sprite con su paleta BGR555, sin comprimir.
        total = round(mean * len(files) + palette_bytes * len(files))
        categories.append(
            {
                "name": name,
                "files": len(files),
                "sample": len(sample),
                "bytes": total,
                "method": f"muestra de {len(sample)}, media LZ77 x total + paleta",
            }
        )
    return categories


def measure_audio(game_dir: Path) -> list[dict]:
    """Presupuesto de musica y efectos en PCM de 8 bits mono a 8 kHz (PLAN.md D19):
    musica (mas de 10 s) en bucle de 20 s, efectos completos. Bytes exactos."""
    music_files, sfx_files = [], []
    for rel in inventory(game_dir):
        if classify_kind(rel) != "audio":
            continue
        duration = _probe_duration(game_dir / rel)
        (music_files if duration > MUSIC_THRESHOLD_S else sfx_files).append(duration)
    music_bytes = sum(math.ceil(min(d, MUSIC_LOOP_S) * PCM_RATE) for d in music_files)
    sfx_bytes = sum(math.ceil(d * PCM_RATE) for d in sfx_files)
    return [
        {
            "name": "musica",
            "files": len(music_files),
            "sample": len(music_files),
            "bytes": music_bytes,
            "method": "20 s x 8000 Hz x 1 byte por pista",
        },
        {
            "name": "efectos",
            "files": len(sfx_files),
            "sample": len(sfx_files),
            "bytes": sfx_bytes,
            "method": "duracion completa x 8000 Hz x 1 byte",
        },
    ]


def measure_text(game_dir: Path, language: str) -> dict:
    """Presupuesto del texto: bytes UTF-8 de los .rpy de tl/<idioma>, sin comprimir y
    con LZ77 de la BIOS."""
    raw = compressed = 0
    files = 0
    for path in sorted((game_dir / "tl" / language).rglob("*.rpy")):
        data = path.read_bytes()
        raw += len(data)
        compressed += len(bios_lz77(data))
        files += 1
    return {
        "name": "texto",
        "files": files,
        "sample": files,
        "bytes": compressed,
        "method": f"{raw} bytes UTF-8 comprimidos con LZ77",
    }


def build_budget(
    game_dir: Path, language: str, sample_size: int = SAMPLE_SIZE, out_dir: Path | None = None
) -> dict:
    """Ejecuta todas las medidas y devuelve el presupuesto completo."""
    game_dir = Path(game_dir)
    if not game_dir.is_dir():
        raise ValueError(f"no existe el directorio de juego: {game_dir}")
    if not (game_dir / "tl" / language).is_dir():
        raise ValueError(f"el juego no trae la traduccion {language} (falta {game_dir / 'tl' / language})")
    out_dir = Path(out_dir) if out_dir else Path("build/demake/gba")
    categories = [
        *measure_images(game_dir, language, sample_size, out_dir),
        *measure_audio(game_dir),
        measure_text(game_dir, language),
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
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Presupuesto del demake de GBA: dice si el juego cabe en un cartucho de 32 MB"
    )
    parser.add_argument("--game", required=True, help="directorio game del juego")
    parser.add_argument("--language", default="es", help="idioma de la traduccion (D16: es)")
    parser.add_argument("--sample", type=int, default=SAMPLE_SIZE, help="tamano de la muestra de imagenes")
    parser.add_argument("--out", default="build/demake/gba", help="directorio para los PNG de muestra")
    args = parser.parse_args(argv)
    budget = build_budget(Path(args.game), args.language, args.sample, Path(args.out))
    print(f"Presupuesto GBA de {budget['game']} (idioma: {budget['language']})")
    print(f"{'categoria':<10}{'archivos':>10}{'bytes':>14}  metodo")
    for cat in budget["categories"]:
        print(f"{cat['name']:<10}{cat['files']:>10}{cat['bytes']:>14,}  {cat['method']}")
    total, cart = budget["total"], budget["cart_bytes"]
    percent = total / cart * 100
    print(f"{'total':<10}{'':>10}{total:>14,}  {percent:.1f}% de {cart:,} bytes (32 MB)")
    if budget["fits"]:
        print(f"VEREDICTO: CABE en el cartucho de 32 MB; sobran {budget['free']:,} bytes")
    else:
        print(f"VEREDICTO: NO CABE; faltan {-budget['free']:,} bytes (ver docs/demake-gba.md)")
    print(f"PNG de muestra: {budget['samples_dir']}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
