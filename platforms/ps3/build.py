"""Compila Snoot para PS3 con PSL1GHT en Docker y empaqueta snoot.self y .pkg."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "hldtux/ps3dev-sdl2@sha256:2b6154588148336d559fbd37f4f52a3418fa96a86906b5019160baef22c75e55"


def build(trace: bool = False) -> Path:
    out = ROOT / "build" / "ps3"
    generated = out / "generated"
    out.mkdir(parents=True, exist_ok=True)
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "game_config.h").write_text(
        '#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE "SNOOT GAME"\n'
        '#define VN_SAVE_PREFIX "BASLUS-99999SNOOT"\n#define VN_SAVE_MAGIC "SNS1"\n',
        encoding="utf-8",
        newline="\n",
    )
    make_cmd = "make -f /src/platforms/ps3/Makefile"
    if trace:
        make_cmd += " VN_TRACE=1"
    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{ROOT.as_posix()}:/src",
        "-w",
        "/src/build/ps3",
        IMAGE,
        "sh",
        "-c",
        make_cmd,
    ]
    subprocess.run(command, check=True)
    return out / "snoot.self"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    self_file = build(args.trace)
    print(self_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
