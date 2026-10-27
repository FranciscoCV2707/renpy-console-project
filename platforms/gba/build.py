"""Compila el demake de GBA con devkitARM dentro de Docker.

Genera build/gba/snoot.gba a partir de un fondo convertido por
tools/demake/gba_pack.py (modo 4, LZ77 de la BIOS) y de platforms/gba/main.c.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "devkitpro/devkitarm@sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5"
OUT = ROOT / "build" / "gba"
ASSETS = ROOT / "build" / "demake" / "gba" / "assets"
GAME_DIR = Path("E:/snoot/snootgame/game")


def docker_sh(script: str) -> None:
    subprocess.run(
        ["docker", "run", "--rm", "-v", f"{ROOT.as_posix()}:/src", "-w", "/src", IMAGE, "sh", "-c", script],
        cwd=ROOT,
        check=True,
    )


def ensure_assets() -> Path:
    manifest_path = ASSETS / "manifest.json"
    if not manifest_path.is_file():
        ASSETS.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.demake.gba_pack",
                "--game",
                str(GAME_DIR),
                "--out",
                str(ASSETS),
            ],
            cwd=ROOT,
            check=True,
        )
    if not manifest_path.is_file():
        raise RuntimeError(f"no se genero el manifest: {manifest_path}")
    return ASSETS


def generate_background_header(assets: Path) -> None:
    bg_files = sorted((assets / "bg").glob("*.bin"))
    if not bg_files:
        raise RuntimeError("no hay fondos convertidos en build/demake/gba/assets/bg")
    data = bg_files[0].read_bytes()
    generated = OUT / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    lines = [
        "#pragma once",
        "#include <stdint.h>",
        f"#define GBA_BG_ASSET_LEN {len(data)}",
        "static const uint8_t gba_bg_asset[] = {",
    ]
    for offset in range(0, len(data), 12):
        chunk = data[offset : offset + 12]
        lines.append("    " + ", ".join(f"0x{byte:02x}" for byte in chunk) + ",")
    lines.append("};")
    (generated / "bg_asset.h").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def build() -> Path:
    assets = ensure_assets()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "generated").mkdir(parents=True, exist_ok=True)
    generate_background_header(assets)

    script = (
        ". /opt/devkitpro/devkitarm.sh && "
        "arm-none-eabi-gcc -std=c99 -Wall -Wextra -Wno-unused-parameter -pedantic "
        "-mcpu=arm7tdmi -mthumb -mthumb-interwork -O2 "
        "-I/src/platforms/gba -I/src/build/gba/generated -I/opt/devkitpro/libtonc/include "
        "-c /src/platforms/gba/main.c -o /src/build/gba/main.o && "
        "arm-none-eabi-gcc -mcpu=arm7tdmi -mthumb -mthumb-interwork -specs=gba.specs "
        "/src/build/gba/main.o -L/opt/devkitpro/libtonc/lib -ltonc "
        "-o /src/build/gba/snoot.elf && "
        "arm-none-eabi-objcopy -O binary /src/build/gba/snoot.elf /src/build/gba/snoot.gba && "
        "/opt/devkitpro/tools/bin/gbafix /src/build/gba/snoot.gba -tSNOOT -c0000 -m00"
    )
    docker_sh(script)
    return OUT / "snoot.gba"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    print(build())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
