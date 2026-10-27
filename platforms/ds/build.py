"""Compila ``build/ds/snoot.nds`` con BlocksDS dentro de Docker (T-708)."""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "skylyrac/blocksds@sha256:779f6193d1030c62e60d1f0f39c3e32cf4045c0bd224a45c0ceadf9d9ab01a51"
SRC = Path(__file__).resolve().parent
WORK = ROOT / "build" / "ds" / "work"
OUT = ROOT / "build" / "ds" / "snoot.nds"
DISC = ROOT / "build" / "ctl" / "ps1" / "disc"

IGNORE_EXTENSIONS = {".cue", ".iso", ".exe", ".cnf"}
IGNORE_NAMES = {"snoot_game.bin", "autotest.bin"}


def prepare_work(autotest_path: Path | None = None) -> None:
    if not DISC.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")

    if WORK.exists():
        # Keep build objects if Makefile unchanged to speed up, or clear
        for folder in ("source", "engine_core", "engine_app", "engine_modules", "games_snoot", "include", "generated", "nitrofs"):
            target = WORK / folder
            if target.exists():
                shutil.rmtree(target)
        if (WORK / "snoot.nds").exists():
            (WORK / "snoot.nds").unlink()
    WORK.mkdir(parents=True, exist_ok=True)

    shutil.copy2(SRC / "Makefile", WORK / "Makefile")
    shutil.copytree(SRC / "source", WORK / "source")
    shutil.copytree(ROOT / "engine" / "core", WORK / "engine_core")
    shutil.copytree(ROOT / "engine" / "app", WORK / "engine_app")
    shutil.copytree(ROOT / "engine" / "modules", WORK / "engine_modules")
    shutil.copytree(ROOT / "games" / "snoot", WORK / "games_snoot")

    include_dir = WORK / "include"
    include_dir.mkdir(parents=True, exist_ok=True)
    for header in (ROOT / "engine" / "platform").glob("*.h"):
        shutil.copy2(header, include_dir / header.name)

    generated = WORK / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "game_config.h").write_text(
        '#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE "SNOOT GAME"\n'
        '#define VN_SAVE_PREFIX "BASLUS-99999SNOOT"\n#define VN_SAVE_MAGIC "SNS1"\n',
        encoding="utf-8",
        newline="\n",
    )

    nitrofs = WORK / "nitrofs"
    nitrofs.mkdir(parents=True, exist_ok=True)
    for item in DISC.glob("*"):
        if item.is_file():
            if item.suffix.lower() in IGNORE_EXTENSIONS or item.name.lower() in IGNORE_NAMES:
                continue
            shutil.copy2(item, nitrofs / item.name)

    if autotest_path and autotest_path.is_file():
        shutil.copy2(autotest_path, nitrofs / "AUTOTEST.BIN")


def build(trace: bool = False, autotest_path: Path | None = None) -> Path:
    prepare_work(autotest_path)
    command = [
        "docker", "run", "--rm",
        "-v", f"{ROOT.as_posix()}:/src",
        "-w", "/src/build/ds/work",
        IMAGE, "make",
    ]
    if trace:
        command.append("VN_TRACE=1")

    subprocess.run(command, cwd=ROOT, check=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(WORK / "snoot.nds", OUT)
    return OUT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--autotest-path", type=Path, default=None)
    args = parser.parse_args()
    print(build(args.trace, args.autotest_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
