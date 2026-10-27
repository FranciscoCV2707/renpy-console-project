"""Compila Snoot para Xbox clasica con nxdk dentro de Docker."""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "xboxdev/nxdk@sha256:14aeace40a9aa3ffdf14501827459cb2ab04766e836200228d87bfeb52f7f6ed"
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
    includes = " ".join(f"-I/src/{path}" for path in INCLUDE_DIRS)
    objects = " ".join(path.removesuffix(".c") + ".obj" for path in sources)
    # nxdk compila con clang (MSVC) y necesita los headers propios del SDK.
    return (
        "XBE_TITLE = Snoot\\ Game\n"
        "NXDK_SDL = y\n"
        "OUTPUT_DIR = /src/build/xbox\n"
        f"SRCS = {' '.join(sources)}\n"
        f"OBJS = {objects}\n"
        f"NXDK_CFLAGS += -std=c99 -Wall -Wextra -Wno-unused-parameter {flags}\n"
        f"NXDK_CFLAGS += {includes} -I/src/build/xbox/src/generated\n"
        "NXDK_LDFLAGS +=\n"
        "all: $(TARGET)\n"
        "NXDK_DIR ?= /usr/src/nxdk\n"
        "include $(NXDK_DIR)/Makefile\n"
    )


def build(trace: bool = False) -> Path:
    out = ROOT / "build" / "xbox"
    out.mkdir(parents=True, exist_ok=True)
    prepare_sources(out, trace)
    command = [
        "docker", "run", "--rm",
        "-v", f"{ROOT.as_posix()}:/src",
        "-w", "/src/build/xbox/src",
        IMAGE, "make",
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    return out / "default.xbe"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    print(build(args.trace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
