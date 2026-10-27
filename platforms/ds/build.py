"""Compila ``build/ds/snoot.nds`` con BlocksDS dentro de Docker (T-706).

La imagen oficial de BlocksDS queda fijada por digest (ver ``docs/platforms/ds.md``). El proyecto de
``platforms/ds`` (Makefile, source y assets) se copia a ``build/ds/work``, se compila dentro del
contenedor con el Makefile de referencia de BlocksDS y el ROM se copia a ``build/ds/snoot.nds``.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "skylyrac/blocksds@sha256:779f6193d1030c62e60d1f0f39c3e32cf4045c0bd224a45c0ceadf9d9ab01a51"
SRC = Path(__file__).resolve().parent
WORK = ROOT / "build" / "ds" / "work"
OUT = ROOT / "build" / "ds" / "snoot.nds"


def build() -> Path:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copy2(SRC / "Makefile", WORK / "Makefile")
    shutil.copytree(SRC / "source", WORK / "source")
    shutil.copytree(SRC / "assets", WORK / "assets")
    subprocess.run(
        ["docker", "run", "--rm", "-v", f"{ROOT.as_posix()}:/src", "-w", "/src/build/ds/work", IMAGE, "make"],
        cwd=ROOT,
        check=True,
    )
    shutil.copy2(WORK / "snoot.nds", OUT)
    return OUT


def main() -> int:
    print(build())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
