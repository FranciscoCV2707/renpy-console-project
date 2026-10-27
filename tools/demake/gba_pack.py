"""Empaqueta los recursos de Snoot para el demake de Game Boy Advance."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

from PIL import Image

from tools.assetpipe.manifest import classify_kind, inventory, source_file
from tools.demake import gba_budget
from tools.demake.lz77 import bios_lz77, pack_4bpp

_TRANSLATION_ID = re.compile(r"^translate\s+es\s+([\w]+)\s*:\s*$")
_STRINGS_BLOCK = re.compile(r"^translate\s+es\s+strings\s*:\s*$")
_INDENTED_STRING = re.compile(r'^\s+(?:old|new)\s+("(?:[^"\\]|\\.)*")\s*$')
_DIALOGUE_STRING = re.compile(r'^\s+("(?:[^"\\]|\\.)*")\s*$')


def _bgr555_palette(image: Image.Image, size: int) -> bytes:
    palette = image.getpalette() or []
    result = bytearray()
    for index in range(size):
        offset = index * 3
        red, green, blue = (palette[offset : offset + 3] + [0, 0, 0])[:3]
        color = (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)
        result += color.to_bytes(2, "little")
    return bytes(result)


def _sprite_tiles(indices: bytes, width: int, height: int) -> bytes:
    tiled = bytearray()
    for tile_y in range(0, height, 8):
        for tile_x in range(0, width, 8):
            for y in range(tile_y, tile_y + 8):
                for x in range(tile_x, tile_x + 8):
                    tiled.append(indices[y * width + x] if x < width else 0)
    return pack_4bpp(bytes(tiled))


def _convert_background(src: Path) -> bytes:
    with Image.open(src) as image:
        quantized, pixels = gba_budget.background_frame(image)
        compressed = bios_lz77(pixels)
        compressed += bytes((-len(compressed)) % 4)
        return compressed + _bgr555_palette(quantized, 256)


def _convert_sprite(src: Path) -> bytes:
    with Image.open(src) as image:
        rgba = image.convert("RGBA")
        bounds = rgba.getchannel("A").getbbox() or (0, 0, rgba.width, rgba.height)
        crop = rgba.crop(bounds)
        scale = gba_budget.SPRITE_CHAR_HEIGHT / crop.height
        size = (max(1, round(crop.width * scale)), gba_budget.SPRITE_CHAR_HEIGHT)
        resized = crop.resize(size, Image.Resampling.LANCZOS)
        quantized = resized.convert("RGB").quantize(
            colors=15, dither=Image.Dither.FLOYDSTEINBERG
        )
        pixels = bytes(
            index + 1 if alpha >= 128 else 0
            for index, alpha in zip(quantized.tobytes(), resized.getchannel("A").tobytes())
        )
        compressed = bios_lz77(_sprite_tiles(pixels, *size))
        compressed += bytes((-len(compressed)) % 4)
        palette = bytes(2) + _bgr555_palette(quantized, 15)
        return (
            size[0].to_bytes(2, "little")
            + size[1].to_bytes(2, "little")
            + compressed
            + palette
        )


def _convert_audio(src: Path, dst: Path, duration: float) -> bytes:
    args = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(src),
        "-map_metadata",
        "-1",
        "-bitexact",
        "-t",
        str(min(duration, gba_budget.MUSIC_LOOP_S) if duration > gba_budget.MUSIC_THRESHOLD_S else duration),
        "-ar",
        str(gba_budget.PCM_RATE),
        "-ac",
        "1",
        "-af",
        "asetpts=N/SR/TB",
        "-c:a",
        "pcm_s8",
        "-f",
        "s8",
        str(dst),
    ]
    subprocess.run(args, check=True)
    return dst.read_bytes()


def _translation_entries(game_dir: Path, language: str) -> list[dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    translation_dir = game_dir / "tl" / language
    for path in sorted(translation_dir.rglob("*.rpy"), key=lambda item: item.as_posix()):
        rel = path.relative_to(game_dir).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        current_id: str | None = None
        in_strings = False
        old_string: str | None = None
        for line in lines:
            if _STRINGS_BLOCK.match(line):
                current_id = None
                in_strings = True
                old_string = None
                continue
            match = _TRANSLATION_ID.match(line)
            if match:
                current_id = match.group(1)
                in_strings = False
                continue
            if current_id:
                value_match = _DIALOGUE_STRING.match(line)
                if value_match:
                    value = ast.literal_eval(value_match.group(1))
                    entries[current_id] = {"path": rel, "text": value}
                    current_id = None
            elif in_strings:
                value_match = _INDENTED_STRING.match(line)
                if not value_match:
                    continue
                value = ast.literal_eval(value_match.group(1))
                if line.lstrip().startswith("old "):
                    old_string = value
                elif line.lstrip().startswith("new ") and old_string is not None:
                    string_id = f"strings:{hashlib.sha256((rel + old_string).encode('utf-8')).hexdigest()[:16]}"
                    entries[string_id] = {"path": rel, "text": value}
                    old_string = None
    return [
        {"id": key, **entries[key]}
        for key in sorted(entries)
    ]


def _encode_text(entries: list[dict[str, str]]) -> bytes:
    """Tabla LE de pares (offset_id, offset_text), seguida del pool NUL UTF-8."""
    pool = bytearray()
    records = bytearray()
    table_size = 4 + len(entries) * 8
    for entry in entries:
        id_offset = table_size + len(pool)
        pool += entry["id"].encode("utf-8") + b"\0"
        text_offset = table_size + len(pool)
        pool += entry["text"].encode("utf-8") + b"\0"
        records += id_offset.to_bytes(4, "little")
        records += text_offset.to_bytes(4, "little")
    return len(entries).to_bytes(4, "little") + records + pool


def _output_name(resource_id: str) -> str:
    return hashlib.sha256(resource_id.encode("utf-8")).hexdigest()[:16] + ".bin"


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
    categories = {"fondos": 0, "sprites": 0, "musica": 0, "efectos": 0, "texto": 0}
    resources = []
    for rel in inventory(game_dir):
        kind = classify_kind(rel)
        src = source_file(game_dir, rel, language)
        if kind == "image" and rel.parts[0] == "images":
            sprite = len(rel.parts) > 1 and rel.parts[1] in gba_budget.SPRITE_FOLDERS
            category = "sprites" if sprite else "fondos"
            resource_id = rel.as_posix()
            payload = _convert_sprite(src) if sprite else _convert_background(src)
            output = out_dir / ("spr" if sprite else "bg") / _output_name(resource_id)
            type_name = "sprite" if sprite else "background"
        elif kind == "audio":
            duration = gba_budget._probe_duration(src)
            music = duration > gba_budget.MUSIC_THRESHOLD_S
            category = "musica" if music else "efectos"
            resource_id = rel.as_posix()
            output = out_dir / "snd" / _output_name(resource_id)
            output.parent.mkdir(parents=True, exist_ok=True)
            temporary = output.with_suffix(".tmp")
            payload = _convert_audio(src, temporary, duration)
            temporary.unlink()
            type_name = "music" if music else "sound"
        else:
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        categories[category] += len(payload)
        resources.append(
            {
                "id": resource_id,
                "path": rel.as_posix(),
                "type": type_name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    text_entries = _translation_entries(game_dir, language)
    text_payload = _encode_text(text_entries)
    (out_dir / "text.bin").write_bytes(text_payload)
    categories["texto"] = len(text_payload)
    for entry in text_entries:
        text_bytes = entry["text"].encode("utf-8")
        resources.append(
            {
                "id": entry["id"],
                "path": entry["path"],
                "type": "text",
                "bytes": len(text_bytes),
                "sha256": hashlib.sha256(text_bytes).hexdigest(),
            }
        )
    resources.sort(key=lambda item: item["id"])
    manifest = {
        "language": language,
        "categories": categories,
        "total_bytes": sum(categories.values()),
        "cart_bytes": gba_budget.CART_BYTES,
        "text_bin": {
            "bytes": len(text_payload),
            "sha256": hashlib.sha256(text_payload).hexdigest(),
            "count": len(text_entries),
        },
        "resources": resources,
    }
    with (out_dir / "manifest.json").open("w", encoding="utf-8", newline="\n") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Empaqueta recursos para el demake de GBA")
    parser.add_argument("--game", required=True, help="directorio game del juego")
    parser.add_argument("--out", required=True, help="directorio de salida")
    parser.add_argument("--language", default="es", help="idioma Ren'Py (D16: es)")
    args = parser.parse_args(argv)
    manifest = pack_game(Path(args.game), Path(args.out), args.language)
    print("Empaquetado GBA")
    for category, size in manifest["categories"].items():
        print(f"{category:<10}{size:>14,} bytes")
    print(f"{'total':<10}{manifest['total_bytes']:>14,} bytes de {manifest['cart_bytes']:,} (32 MB)")
    digest = hashlib.sha256((Path(args.out) / "manifest.json").read_bytes()).hexdigest()
    print(f"manifest sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
