"""Compila Snoot para PSP con el toolchain de pspdev (Docker) y empaqueta EBOOT.PBP."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "pspdev/pspdev@sha256:54895e6f5afb71b8f4f6915ee6d5023e1e087ca7afdf2dcb1d7a694a5233e45f"


def build(trace: bool = False) -> Path:
    out = ROOT / "build" / "psp"
    generated = out / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "game_config.h").write_text(
        '#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE "SNOOT GAME"\n'
        '#define VN_SAVE_PREFIX "BASLUS-99999SNOOT"\n#define VN_SAVE_MAGIC "SNS1"\n',
        encoding="utf-8",
        newline="\n",
    )
    command = ["docker", "run", "--rm", "-v", f"{ROOT.as_posix()}:/src", "-w", "/src/build/psp",
               IMAGE, "make", "-f", "/src/platforms/psp/Makefile"]
    if trace:
        command.append("VN_TRACE=1")
    subprocess.run(command, check=True)
    return out / "EBOOT.PBP"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    print(build(args.trace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
