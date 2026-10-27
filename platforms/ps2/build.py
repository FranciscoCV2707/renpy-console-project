"""Compila Snoot con el toolchain y SDL2 de PS2SDK dentro de Docker."""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "ps2dev/ps2dev@sha256:5476fdfbf34d35eb644fde0a6f6533fb554a4a8171ce53dad7cd1df6077dfb05"
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
    includes += " -Igenerated -I$(PS2SDK)/ports/include"
    objects = " ".join(path.removesuffix(".c") + ".o" for path in sources)
    return (
        "EE_BIN = /src/build/ps2/snoot.elf\n"
        f"EE_OBJS = {objects}\n"
        f"EE_INCS = {includes}\n"
        "EE_CFLAGS = -std=c99 -Wall -Wextra -Wno-unused-parameter -pedantic -O2 "
        f"{flags}\n"
        "EE_LDFLAGS = -L$(PS2SDK)/ports/lib -L$(PS2DEV)/gsKit/lib\n"
        "EE_LIBS = -lSDL2main -lSDL2 -lm -lpatches -lgskit -ldmakit -lps2_drivers\n"
        "all: $(EE_BIN)\n"
        "include $(PS2SDK)/samples/Makefile.pref\n"
        "include $(PS2SDK)/samples/Makefile.eeglobal\n"
    )


def build(trace: bool = False) -> Path:
    out = ROOT / "build" / "ps2"
    out.mkdir(parents=True, exist_ok=True)
    prepare_sources(out, trace)
    command = [
        "docker", "run", "--rm", "-v", f"{ROOT.as_posix()}:/src", "-w", "/src/build/ps2/src",
        IMAGE, "sh", "-c", "apk add --no-cache make >/tmp/apk.log 2>&1 && make",
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    return out / "snoot.elf"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    print(build(args.trace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
