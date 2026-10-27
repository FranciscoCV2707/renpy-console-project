"""Compila Snoot para SDL2 con el toolchain MSYS2 ucrt64."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MSYS = Path(r"C:\msys64\ucrt64\bin")


def build(trace: bool = False) -> Path:
    out = ROOT / "build" / "pc"
    out.mkdir(parents=True, exist_ok=True)
    generated = out / "generated"
    generated.mkdir(exist_ok=True)
    (generated / "game_config.h").write_text(
        '#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE "SNOOT GAME"\n'
        '#define VN_SAVE_PREFIX "BASLUS-99999SNOOT"\n#define VN_SAVE_MAGIC "SNS1"\n',
        encoding="utf-8",
        newline="\n",
    )
    env = os.environ.copy()
    env["PATH"] = str(MSYS) + os.pathsep + r"C:\msys64\usr\bin" + os.pathsep + env.get("PATH", "")
    config = subprocess.run([r"C:\msys64\usr\bin\bash.exe", str(MSYS / "sdl2-config"), "--cflags", "--libs"],
                            check=True, capture_output=True, text=True, encoding="utf-8", env=env)
    flags = [flag for flag in config.stdout.split() if flag != "-mwindows"]
    sources = []
    for folder in ("engine/core", "engine/app", "engine/modules", "games/snoot", "platforms/sdl"):
        sources.extend(sorted((ROOT / folder).glob("*.c")))
    command = [str(MSYS / "gcc.exe"), "-std=c99", "-Wall", "-Wextra", "-Wno-unused-parameter", "-pedantic", "-O2"]
    command.extend(f"-I{ROOT / path}" for path in (
        "engine/core", "engine/platform", "engine/app", "engine/modules", "games/snoot",
        "platforms/sdl", "build/pc/generated",
    ))
    if trace:
        command.append("-DVN_TRACE")
    command.extend(str(source) for source in sources)
    command.extend(flags)
    target = out / "snoot.exe"
    command.extend(["-o", str(target)])
    subprocess.run(command, cwd=ROOT, env=env, check=True)
    shutil.copy2(MSYS / "SDL2.dll", out / "SDL2.dll")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    print(build(args.trace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
