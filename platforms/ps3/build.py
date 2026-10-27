"""Compila Snoot para PS3 con PSL1GHT en Docker y empaqueta snoot.self y .pkg.

La libSDL2.a de la imagen Docker mezcla el nucleo de SDL2 2.31 con el driver de audio de
PSL1GHT con la firma antigua de ``OpenDevice`` (crash en ``PSL1GHT_AUD_OpenDevice``, ver
reports/T-613.md), asi que aqui se compila SDL2 desde la fuente del port oficial de ps3dev
(``shagkur/SDL_PSL1GHT``, SDL 2.0.13), cuyo nucleo y drivers usan la misma firma, fijado
por commit ``b81fbad`` ("fix API change": el driver ya recibe ``OpenDevice(_THIS, handle,
devname, iscapture)``).
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "hldtux/ps3dev-sdl2@sha256:2b6154588148336d559fbd37f4f52a3418fa96a86906b5019160baef22c75e55"
SDL2_REPO = "https://github.com/shagkur/SDL_PSL1GHT.git"
SDL2_COMMIT = "b81fbad4489918f5ed9c9c052238d7a25da9bab9"
OUT = ROOT / "build" / "ps3"
SDL2_SRC = OUT / "sdl2-src"
SDL2_PREFIX = OUT / "sdl2"


def docker_sh(script: str, workdir: str = "/src") -> None:
    subprocess.run(
        ["docker", "run", "--rm", "-v", f"{ROOT.as_posix()}:/src", "-w", workdir, IMAGE, "sh", "-c", script],
        cwd=ROOT,
        check=True,
    )


def ensure_sdl2() -> None:
    """Clona el port de SDL2 fijado por commit y lo compila en Docker (cacheado en build/ps3/sdl2)."""
    if (SDL2_PREFIX / "include" / "SDL2" / "SDL.h").is_file() and (SDL2_PREFIX / "lib" / "libSDL2.a").is_file():
        return
    SDL2_SRC.mkdir(parents=True, exist_ok=True)
    docker_sh(
        "rm -rf /src/build/ps3/sdl2-src && git init /src/build/ps3/sdl2-src && "
        f"git -C /src/build/ps3/sdl2-src remote add origin {SDL2_REPO} && "
        f"git -C /src/build/ps3/sdl2-src fetch --depth 1 origin {SDL2_COMMIT} && "
        "git -C /src/build/ps3/sdl2-src checkout --detach FETCH_HEAD"
    )
    docker_sh(
        "cd /src/build/ps3/sdl2-src && "
        'CFLAGS="-O2 -I$PSL1GHT/ppu/include" LDFLAGS="-L$PSL1GHT/ppu/lib -lrt -llv2" '
        "./configure --prefix=/src/build/ps3/sdl2 --host=powerpc64-ps3-elf "
        "--enable-video-psl1ght=yes --enable-joystick=yes --enable-audio=yes && "
        "make -j8 && make install"
    )


def build(trace: bool = False) -> Path:
    generated = OUT / "generated"
    OUT.mkdir(parents=True, exist_ok=True)
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "game_config.h").write_text(
        '#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE "SNOOT GAME"\n'
        '#define VN_SAVE_PREFIX "BASLUS-99999SNOOT"\n#define VN_SAVE_MAGIC "SNS1"\n',
        encoding="utf-8",
        newline="\n",
    )
    ensure_sdl2()
    make_cmd = "make -f /src/platforms/ps3/Makefile"
    if trace:
        make_cmd += " VN_TRACE=1"
    # ppu_rules deja los .self/.pkg en $(CURDIR): el make corre en build/ps3 para que salgan ahi.
    docker_sh(make_cmd, workdir="/src/build/ps3")
    return OUT / "snoot.self"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    self_file = build(args.trace)
    print(self_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
