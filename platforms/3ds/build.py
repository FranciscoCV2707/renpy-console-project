"""Compila Snoot para Nintendo 3DS con SDL2 (compilado desde fuente) dentro de Docker.

La imagen devkitPro/devkitarm trae SDL 1.2 (`3ds-sdl`), no SDL2 (`3ds-sdl2`). Por eso este script
compila SDL2 2.32.10 desde el repositorio oficial (tag fijado) en el primer arranque y reutiliza
el resultado cacheado en build/3ds/sdl2.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "devkitpro/devkitarm@sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5"
SDL2_TAG = "release-2.32.10"
SDL2_SRC = ROOT / "build" / "3ds" / "sdl2-src"
SDL2_BUILD = ROOT / "build" / "3ds" / "sdl2-build"
SDL2_PREFIX = ROOT / "build" / "3ds" / "sdl2"
OUT = ROOT / "build" / "3ds"


def docker_sh(script: str) -> None:
    subprocess.run(
        ["docker", "run", "--rm", "-v", f"{ROOT.as_posix()}:/src", "-w", "/src", IMAGE, "sh", "-c", script],
        cwd=ROOT,
        check=True,
    )


def ensure_sdl2() -> None:
    if (SDL2_PREFIX / "include" / "SDL2" / "SDL.h").is_file() and (SDL2_PREFIX / "lib" / "libSDL2.a").is_file():
        return
    SDL2_SRC.mkdir(parents=True, exist_ok=True)
    SDL2_BUILD.mkdir(parents=True, exist_ok=True)
    SDL2_PREFIX.mkdir(parents=True, exist_ok=True)
    if not (SDL2_SRC / "CMakeLists.txt").is_file():
        docker_sh(
            "rm -rf /src/build/3ds/sdl2-src && "
            f"git clone --depth 1 --branch {SDL2_TAG} https://github.com/libsdl-org/SDL.git /src/build/3ds/sdl2-src"
        )
    docker_sh(
        ". /opt/devkitpro/devkitarm.sh && "
        "rm -rf /src/build/3ds/sdl2-build && mkdir -p /src/build/3ds/sdl2-build && "
        "cd /src/build/3ds/sdl2-build && "
        "cmake -S /src/build/3ds/sdl2-src -B . "
        "-DCMAKE_TOOLCHAIN_FILE=/opt/devkitpro/cmake/3DS.cmake -DCMAKE_BUILD_TYPE=Release "
        "-DCMAKE_INSTALL_PREFIX=/src/build/3ds/sdl2 && "
        "make -j4 && make install"
    )


def build(trace: bool = False) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    generated = OUT / "generated"
    generated.mkdir(exist_ok=True)
    (generated / "game_config.h").write_text(
        '#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE "SNOOT GAME"\n'
        '#define VN_SAVE_PREFIX "BASLUS-99999SNOOT"\n#define VN_SAVE_MAGIC "SNS1"\n',
        encoding="utf-8",
        newline="\n",
    )

    ensure_sdl2()

    sources = []
    for folder in ("engine/core", "engine/app", "engine/modules", "games/snoot", "platforms/sdl"):
        for path in sorted((ROOT / folder).glob("*.c")):
            sources.append(f"/src/{folder}/{path.name}")

    include_dirs = (
        "engine/core", "engine/platform", "engine/app", "engine/modules",
        "games/snoot", "platforms/sdl",
    )
    includes = " ".join(f"-iquote /src/{path}" for path in include_dirs)
    includes += " -I/src/build/3ds/generated -I/src/build/3ds/sdl2/include -I/opt/devkitpro/libctru/include"

    flags = (
        "-std=c99 -Wall -Wextra -Wno-unused-parameter -pedantic -O2 "
        "-march=armv6k -mtune=mpcore -mfloat-abi=hard -mtp=soft -mword-relocations "
        "-ffunction-sections -fdata-sections -D__3DS__"
    )
    if trace:
        flags += " -DVN_TRACE"

    script = (
        ". /opt/devkitpro/devkitarm.sh && "
        f"arm-none-eabi-gcc {flags} {includes} {' '.join(sources)} "
        "-o /src/build/3ds/snoot.elf "
        "-L/src/build/3ds/sdl2/lib -L/opt/devkitpro/libctru/lib "
        "-lSDL2 -lcitro3d -lctru -lm -specs=3dsx.specs && "
        "3dsxtool /src/build/3ds/snoot.elf /src/build/3ds/snoot.3dsx"
    )
    docker_sh(script)
    return OUT / "snoot.3dsx"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    print(build(args.trace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
