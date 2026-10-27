"""Convierte un fondo de Snoot al bitmap de 256x192 que muestra la pantalla de arriba de la DS.

La entrada es una imagen de ``E:/snoot/snootgame/game/images``; la salida es
``platforms/ds/assets/bg_sample.bin`` con un píxel de 16 bits por punto: bits 0-4 rojo, 5-9 verde,
10-14 azul y bit 15 en 1 (opaco en el modo bitmap de la DS). La conversión es determinista: misma
entrada, mismo hash.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

DEFAULT_SOURCE = Path("E:/snoot/snootgame/game/images/backgrounds/classroom.webp")
OUT = Path(__file__).resolve().parent / "assets" / "bg_sample.bin"
WIDTH = 256
HEIGHT = 192


def convert(source: Path) -> bytes:
    with Image.open(source) as image:
        resized = image.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        raw = resized.tobytes()
        pixels = bytearray()
        for offset in range(0, len(raw), 3):
            red, green, blue = raw[offset], raw[offset + 1], raw[offset + 2]
            color = 0x8000 | (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)
            pixels += color.to_bytes(2, "little")
        return bytes(pixels)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    data = convert(args.source)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(data)
    print(f"{OUT} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
