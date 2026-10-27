"""Compila Snoot para Wii con libogc y SDL2 de devkitPro (Docker)."""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "devkitpro/devkitppc@sha256:d50f8a886f2ce1d3c22685a774afb0845379876b47d9b41a9b729f4f63a54813"
SOURCE_DIRS = ("engine/core", "engine/app", "engine/modules", "games/snoot", "platforms/sdl")
INCLUDE_DIRS = ("engine/core", "engine/platform", "engine/app", "engine/modules", "games/snoot", "platforms/sdl")


def prepare_sources(out: Path, trace: bool) -> Path:
    source = out / "src"
    if source.exists():
        shutil.rmtree(source)
    source.mkdir(parents=True)
    sources = []
    for folder in SOURCE_DIRS:
        for path in sorted((ROOT / folder).glob("*.c")):
            name = folder.replace("/", "_") + "_" + path.name
            target = source / name
            shutil.copy2(path, target)
            sources.append(name)

    generated = source / "generated"
    generated.mkdir()
    (generated / "game_config.h").write_text(
        '#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE "SNOOT GAME"\n'
        '#define VN_SAVE_PREFIX "BASLUS-99999SNOOT"\n#define VN_SAVE_MAGIC "SNS1"\n',
        encoding="utf-8",
        newline="\n",
    )
    (source / "Makefile").write_text(makefile(sources, trace), encoding="utf-8", newline="\n")
    return source


def makefile(sources: list[str], trace: bool) -> str:
    flags = "-DVN_TRACE" if trace else ""
    includes = " ".join(f"-iquote /src/{path}" for path in INCLUDE_DIRS)
    includes += " -I/src/build/wii/src/generated"
    objects = " ".join(path.removesuffix(".c") + ".o" for path in sources)
    sdl_cflags = "$$(/opt/devkitpro/portlibs/wii/bin/sdl2-config --cflags)"
    sdl_libs = "$$(/opt/devkitpro/portlibs/wii/bin/sdl2-config --libs)"
    return (
        "CC = powerpc-eabi-gcc\n"
        f"OBJS = {objects}\n"
        "CFLAGS = -std=c99 -Wall -Wextra -Wno-unused-parameter -pedantic -O2 "
        "-DGEKKO -D__WII__ -mrvl -mcpu=750 -meabi -mhard-float "
        "-ffunction-sections -fdata-sections "
        f"{flags}\n"
        f"INCLUDES = {includes} -I/opt/devkitpro/libogc/include "
        "-I/opt/devkitpro/portlibs/wii/include -I/opt/devkitpro/portlibs/ppc/include "
        f"{sdl_cflags}\n"
        f"LIBS = {sdl_libs}\n"
        "all: /src/build/wii/boot.dol\n"
        "/src/build/wii/boot.elf: $(OBJS)\n"
        "\t$(CC) $(OBJS) $(LIBS) -o $@\n"
        "/src/build/wii/boot.dol: /src/build/wii/boot.elf\n"
        "\telf2dol $< $@\n"
        "%.o: %.c\n"
        "\t$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@\n"
    )


def build(trace: bool = False) -> Path:
    out = ROOT / "build" / "wii"
    out.mkdir(parents=True, exist_ok=True)
    prepare_sources(out, trace)
    command = [
        "docker", "run", "--rm",
        "-v", f"{ROOT.as_posix()}:/src",
        "-w", "/src/build/wii/src",
        IMAGE,
        "sh", "-c",
        ". /opt/devkitpro/wiivars.sh && make",
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    meta = out / "meta.xml"
    if not meta.exists():
        meta.write_text(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            "<app version=\"1\">\n"
            "  <name>Snoot Game</name>\n"
            "  <coder>renpy-console-project</coder>\n"
            "  <version>1.0</version>\n"
            "  <release_date>20261027</release_date>\n"
            "  <short_description>Snoot Game (port Wii)</short_description>\n"
            "  <long_description>Port de Snoot Game con el backend SDL.</long_description>\n"
            "</app>\n",
            encoding="utf-8",
            newline="\n",
        )
    return out / "boot.dol"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    print(build(args.trace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
