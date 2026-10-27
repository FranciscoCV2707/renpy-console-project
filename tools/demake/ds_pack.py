"""Empaqueta recursos de Snoot para NitroFS en el demake de Nintendo DS."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from tools.assetpipe.manifest import classify_kind, inventory, source_file
from tools.demake import gba_budget
from tools.demake.ima_adpcm import encode as encode_ima_adpcm
from tools.demake.lz77 import bios_lz77

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 192
AUDIO_RATE = 22050
_TRANSLATION_ID = re.compile(r"^translate\s+es\s+([\w]+)\s*:\s*$")
_STRINGS_BLOCK = re.compile(r"^translate\s+es\s+strings\s*:\s*$")
_INDENTED_STRING = re.compile(r'^\s+(?:old|new)\s+("(?:[^"\\]|\\.)*")\s*$')
_DIALOGUE_STRING = re.compile(r'^\s+("(?:[^"\\]|\\.)*")\s*$')


def _bgr555(red: int, green: int, blue: int) -> int:
    return 0x8000 | (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)


def convert_background(src: Path) -> bytes:
    """Redimensiona a 256x192, convierte a BGR555 opaco y comprime con LZ77 0x10."""
    with Image.open(src) as image:
        resized = image.convert("RGB").resize(
            (SCREEN_WIDTH, SCREEN_HEIGHT), Image.Resampling.LANCZOS
        )
        raw = resized.tobytes()
    pixels = bytearray()
    for offset in range(0, len(raw), 3):
        pixels.extend(
            _bgr555(raw[offset], raw[offset + 1], raw[offset + 2]).to_bytes(2, "little")
        )
    return bios_lz77(bytes(pixels))


def _bgr555_palette(image: Image.Image) -> bytes:
    palette = image.getpalette() or []
    result = bytearray(2)
    for index in range(255):
        offset = index * 3
        red, green, blue = (palette[offset : offset + 3] + [0, 0, 0])[:3]
        result.extend((_bgr555(red, green, blue) & 0x7FFF).to_bytes(2, "little"))
    return bytes(result)


def _sprite_tiles(indices: bytes, width: int, height: int) -> bytes:
    padded_width = (width + 7) & ~7
    padded_height = (height + 7) & ~7
    tiles = bytearray()
    for tile_y in range(0, padded_height, 8):
        for tile_x in range(0, padded_width, 8):
            for y in range(tile_y, tile_y + 8):
                for x in range(tile_x, tile_x + 8):
                    tiles.append(indices[y * width + x] if x < width and y < height else 0)
    return bytes(tiles)


def convert_sprite(src: Path) -> bytes:
    """Reduce a la mitad, cuantiza a 255 colores más transparencia y ordena tiles 8x8."""
    with Image.open(src) as image:
        rgba = image.convert("RGBA")
    bounds = rgba.getchannel("A").getbbox() or (0, 0, rgba.width, rgba.height)
    crop = rgba.crop(bounds)
    size = (max(1, round(crop.width / 2)), max(1, round(crop.height / 2)))
    resized = crop.resize(size, Image.Resampling.LANCZOS)
    quantized = resized.convert("RGB").quantize(colors=255, dither=Image.Dither.FLOYDSTEINBERG)
    indices = bytes(
        index + 1 if alpha >= 128 else 0
        for index, alpha in zip(
            quantized.tobytes(), resized.getchannel("A").tobytes(), strict=True
        )
    )
    tile_data = bios_lz77(_sprite_tiles(indices, *size))
    header = size[0].to_bytes(2, "little") + size[1].to_bytes(2, "little")
    return header + tile_data + _bgr555_palette(quantized)


def _translation_entries(game_dir: Path, language: str) -> list[dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    translation_dir = game_dir / "tl" / language
    for path in sorted(translation_dir.rglob("*.rpy"), key=lambda item: item.as_posix()):
        rel = path.relative_to(game_dir).as_posix()
        current_id: str | None = None
        in_strings = False
        old_string: str | None = None
        for line in path.read_text(encoding="utf-8").splitlines():
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
                    entries[current_id] = {
                        "path": rel,
                        "text": ast.literal_eval(value_match.group(1)),
                    }
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
    return [{"id": key, **entries[key]} for key in sorted(entries)]


def _encode_text(entries: list[dict[str, str]]) -> bytes:
    """Tabla LE de pares (offset_id, offset_text), seguida del pool NUL UTF-8."""
    pool = bytearray()
    records = bytearray()
    table_size = 4 + len(entries) * 8
    for entry in entries:
        id_offset = table_size + len(pool)
        pool.extend(entry["id"].encode("utf-8") + b"\0")
        text_offset = table_size + len(pool)
        pool.extend(entry["text"].encode("utf-8") + b"\0")
        records.extend(id_offset.to_bytes(4, "little"))
        records.extend(text_offset.to_bytes(4, "little"))
    return len(entries).to_bytes(4, "little") + records + pool


def _output_name(resource_id: str) -> str:
    return hashlib.sha256(resource_id.encode("utf-8")).hexdigest()[:16] + ".bin"


def _convert_audio(src: Path) -> tuple[bytes, int]:
    with tempfile.TemporaryDirectory() as temp_dir:
        pcm_path = Path(temp_dir) / "audio.pcm"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                "-map_metadata", "-1", "-bitexact", "-ar", str(AUDIO_RATE), "-ac", "1",
                "-c:a", "pcm_s16le", "-f", "s16le", str(pcm_path),
            ],
            check=True,
        )
        pcm = pcm_path.read_bytes()
    if len(pcm) % 2:
        raise ValueError(f"PCM de ffmpeg con longitud inválida: {src}")
    samples = [int.from_bytes(pcm[offset : offset + 2], "little", signed=True)
               for offset in range(0, len(pcm), 2)]
    return encode_ima_adpcm(samples), len(samples)


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
    categories = {"fondos": 0, "sprites": 0, "audio": 0, "texto": 0}
    resources = []
    for rel in inventory(game_dir):
        kind = classify_kind(rel)
        src = source_file(game_dir, rel, language)
        if kind == "image" and rel.parts[0] == "images":
            sprite = len(rel.parts) > 1 and rel.parts[1] in gba_budget.SPRITE_FOLDERS
            category = "sprites" if sprite else "fondos"
            resource_id = rel.as_posix()
            payload = convert_sprite(src) if sprite else convert_background(src)
            output = out_dir / ("spr" if sprite else "bg") / _output_name(resource_id)
            type_name = "sprite" if sprite else "background"
        elif kind == "audio":
            category = "audio"
            resource_id = rel.as_posix()
            payload, sample_count = _convert_audio(src)
            output = out_dir / "snd" / _output_name(resource_id)
            type_name = "adpcm"
        else:
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        categories[category] += len(payload)
        resources.append(
            {
                "id": resource_id,
                "path": rel.as_posix(),
                "output": output.relative_to(out_dir).as_posix(),
                "type": type_name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                **({"sample_rate": AUDIO_RATE, "samples": sample_count} if kind == "audio" else {}),
            }
        )

    text_entries = _translation_entries(game_dir, language)
    text_payload = _encode_text(text_entries)
    (out_dir / "text.bin").write_bytes(text_payload)
    categories["texto"] = len(text_payload)
    resources.append(
        {
            "id": "text-table",
            "path": f"tl/{language}",
            "output": "text.bin",
            "type": "text_table",
            "bytes": len(text_payload),
            "sha256": hashlib.sha256(text_payload).hexdigest(),
            "count": len(text_entries),
        }
    )
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
    resources.sort(key=lambda item: (item["id"], item["type"]))
    manifest = {
        "language": language,
        "audio_rate": AUDIO_RATE,
        "rom_limit_bytes": 512 * 1024 * 1024,
        "categories": categories,
        "total_bytes": sum(categories.values()),
        "rom_limit_remaining_bytes": 512 * 1024 * 1024 - sum(categories.values()),
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
    parser = argparse.ArgumentParser(description="Empaqueta recursos para NitroFS de Nintendo DS")
    parser.add_argument("--game", required=True, help="directorio game del juego")
    parser.add_argument("--out", required=True, help="directorio NitroFS de salida")
    parser.add_argument("--language", default="es", help="idioma Ren'Py (D16: es)")
    args = parser.parse_args(argv)
    manifest = pack_game(Path(args.game), Path(args.out), args.language)
    print("Empaquetado DS")
    for category, size in manifest["categories"].items():
        print(f"{category:<10}{size:>14,} bytes")
    print(f"{'total':<10}{manifest['total_bytes']:>14,} bytes de {manifest['rom_limit_bytes']:,} (512 MB)")
    print(f"{'restan':<10}{manifest['rom_limit_remaining_bytes']:>14,} bytes")
    largest = sorted(manifest["resources"], key=lambda item: (-item["bytes"], item["id"]))[:5]
    print("5 recursos más grandes:")
    for resource in largest:
        print(f"{resource['bytes']:>14,} bytes  {resource['id']}")
    digest = hashlib.sha256((Path(args.out) / "manifest.json").read_bytes()).hexdigest()
    print(f"manifest sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
