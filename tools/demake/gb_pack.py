"""Empaqueta los recursos de Snoot para el demake de Game Boy y Game Boy Color."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tools.assetpipe.manifest import classify_kind, inventory, source_file
from tools.demake import gb_budget, gba_pack
from tools.demake.lz77 import bios_lz77


def _palette() -> bytes:
    """Devuelve ocho paletas GBC iguales de cuatro tonos en RGB555 little-endian."""
    palette = bytearray()
    for _ in range(8):
        for tone in (0, 85, 170, 255):
            value = (tone >> 3) * 0x0421
            palette += value.to_bytes(2, "little")
    return bytes(palette)


def _background(src: Path) -> tuple[bytes, int]:
    with Image.open(src) as image:
        indices = gb_budget.bayer4_indices(image, gb_budget.SCREEN_W, gb_budget.SCREEN_H)
    tiles, full_map = gb_budget.split_tiles_full(indices, gb_budget.SCREEN_W, gb_budget.SCREEN_H)
    unique = len(tiles)
    tile_map = bytes(index & 0xFF for index in full_map)
    if unique > gb_budget.VRAM_TILES:
        raise ValueError(f"{src}: {unique} tiles unicos exceden los {gb_budget.VRAM_TILES} de VRAM")
    attributes = bytes(0 if index < 256 else 0x08 for index in full_map)
    payload = bios_lz77(b"".join(tiles)) + tile_map + attributes + _palette()
    return payload, unique


def _portrait(src: Path) -> bytes:
    with Image.open(src) as image:
        indices = gb_budget.portrait_indices(image)
    tiles, tile_map = gb_budget.split_tiles(indices, gb_budget.PORTRAIT, gb_budget.PORTRAIT)
    tile_data = b"".join(gb_budget.pack_2bpp(tile) for tile in tiles)
    return bios_lz77(tile_data) + tile_map + bytes(len(tile_map)) + _palette()


def _glyph_font(game_dir: Path, language: str, glyph_ids: dict[str, int]) -> tuple[bytes, str]:
    fonts = [path for path in inventory(game_dir) if classify_kind(path) == "font"]
    font_rel = fonts[0] if fonts else None
    font_path = source_file(game_dir, font_rel, language) if font_rel else None
    font = ImageFont.truetype(str(font_path), 8) if font_path else ImageFont.load_default()
    pixels = bytearray(gb_budget.GLYPHS * gb_budget.TILE * gb_budget.TILE)
    for character, glyph_id in glyph_ids.items():
        image = Image.new("L", (8, 8))
        draw = ImageDraw.Draw(image)
        bounds = draw.textbbox((0, 0), character, font=font)
        x = (8 - (bounds[2] - bounds[0])) // 2 - bounds[0]
        y = (8 - (bounds[3] - bounds[1])) // 2 - bounds[1]
        draw.text((x, y), character, fill=255, font=font)
        indices = bytes(min(3, value // 86) for value in image.tobytes())
        start = glyph_id * gb_budget.TILE * gb_budget.TILE
        pixels[start : start + len(indices)] = indices
    packed = b"".join(
        gb_budget.pack_2bpp(bytes(pixels[offset : offset + 64]))
        for offset in range(0, len(pixels), 64)
    )
    return packed, font_rel.as_posix() if font_rel else "(Pillow default font)"


def _text_data(entries: list[dict[str, str]], glyph_ids: dict[str, int]) -> tuple[bytes, list[dict]]:
    table_size = 2 + len(entries) * 8
    pool = bytearray()
    records = bytearray()
    index = []
    for entry in entries:
        id_offset = table_size + len(pool)
        pool += entry["id"].encode("utf-8") + b"\0"
        text_offset = table_size + len(pool)
        encoded = gb_budget.encode_glyphs(entry["text"], glyph_ids)
        pool += encoded + b"\0"
        records += id_offset.to_bytes(4, "little") + text_offset.to_bytes(4, "little")
        index.append(
            {
                "id": entry["id"],
                "path": entry["path"],
                "type": "text",
                "output": "text.bin",
                "offset": text_offset,
                "bytes": len(encoded),
                "sha256": hashlib.sha256(encoded).hexdigest(),
            }
        )
    return len(entries).to_bytes(2, "little") + records + pool, index


def pack_game(game: Path, out: Path, language: str = "es") -> dict:
    game_dir = Path(game)
    out_dir = Path(out)
    if not game_dir.is_dir():
        raise ValueError(f"no existe el directorio de juego: {game_dir}")
    if not (game_dir / "tl" / language).is_dir():
        raise ValueError(f"el juego no trae la traduccion {language}")
    if out_dir.resolve().is_relative_to(game_dir.resolve()):
        raise ValueError("--out no puede estar dentro de --game")

    out_dir.mkdir(parents=True, exist_ok=True)
    entries = gba_pack._translation_entries(game_dir, language)
    glyph_ids = gb_budget.glyph_table(game_dir, language)
    resources = []
    categories = {"fondos": 0, "retratos": 0, "glifos": 0, "texto": 0}
    over_vram = []

    image_paths = [
        rel
        for rel in inventory(game_dir)
        if classify_kind(rel) == "image" and rel.parts[0] == "images"
    ]
    for rel in image_paths:
        is_portrait = len(rel.parts) > 1 and rel.parts[1] in gb_budget.SPRITE_FOLDERS
        resource_id = rel.as_posix()
        source = source_file(game_dir, rel, language)
        if is_portrait:
            payload = _portrait(source)
            folder, type_name, category = "face", "portrait", "retratos"
            unique = 0
        else:
            payload, unique = _background(source)
            folder, type_name, category = "bg", "background", "fondos"
            if unique > gb_budget.VRAM_TILES:
                over_vram.append(resource_id)
        output = out_dir / folder / f"{hashlib.sha256(resource_id.encode('utf-8')).hexdigest()[:16]}.bin"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        categories[category] += len(payload)
        resources.append(
            {
                "id": resource_id,
                "path": rel.as_posix(),
                "type": type_name,
                "output": output.relative_to(out_dir).as_posix(),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                **({"unique_tiles": unique} if not is_portrait else {}),
            }
        )

    font_data, font_source = _glyph_font(game_dir, language, glyph_ids)
    (out_dir / "font.bin").write_bytes(font_data)
    categories["glifos"] = len(font_data)
    resources.append(
        {
            "id": "font",
            "path": font_source,
            "type": "font",
            "output": "font.bin",
            "bytes": len(font_data),
            "sha256": hashlib.sha256(font_data).hexdigest(),
        }
    )

    text_data, text_entries = _text_data(entries, glyph_ids)
    (out_dir / "text.bin").write_bytes(text_data)
    categories["texto"] = len(text_data)
    resources.append(
        {
            "id": "text-table",
            "path": f"tl/{language}",
            "type": "text_table",
            "output": "text.bin",
            "bytes": len(text_data),
            "sha256": hashlib.sha256(text_data).hexdigest(),
            "count": len(entries),
        }
    )
    resources.extend(text_entries)
    resources.sort(key=lambda item: (item["id"], item["type"]))
    total = sum(categories.values())
    manifest = {
        "language": language,
        "cart_bytes": gb_budget.CART_BYTES,
        "categories": categories,
        "total_bytes": total,
        "free_bytes": gb_budget.CART_BYTES - total,
        "fits": total <= gb_budget.CART_BYTES,
        "glyphs": len(glyph_ids),
        "backgrounds_over_vram": over_vram,
        "resources": resources,
    }
    with (out_dir / "manifest.json").open("w", encoding="utf-8", newline="\n") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Empaqueta recursos para el demake de GB/GBC")
    parser.add_argument("--game", required=True, help="directorio game del juego")
    parser.add_argument("--out", required=True, help="directorio de salida")
    parser.add_argument("--language", default="es", help="idioma Ren'Py (D16: es)")
    args = parser.parse_args(argv)
    manifest = pack_game(Path(args.game), Path(args.out), args.language)
    print("Empaquetado GB/GBC")
    for category, size in manifest["categories"].items():
        print(f"{category:<10}{size:>14,} bytes")
    print(f"{'total':<10}{manifest['total_bytes']:>14,} bytes de {manifest['cart_bytes']:,} (8 MB)")
    print(f"fondos sobre 384 tiles: {len(manifest['backgrounds_over_vram'])}")
    digest = hashlib.sha256((Path(args.out) / "manifest.json").read_bytes()).hexdigest()
    print(f"manifest sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
