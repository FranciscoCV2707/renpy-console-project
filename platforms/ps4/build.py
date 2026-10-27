"""Compila Snoot para PS4 con el toolchain OpenOrbis en Docker y empaqueta eboot.bin y FPKG (.pkg)."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "xfangfang/pacbrew@sha256:4774ccb28f5e05cd848a7c9204532ea409d1af63e9689d2dbb3e4cec925439d2"


def build(trace: bool = False) -> Path:
    out = ROOT / "build" / "ps4"
    generated = out / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "game_config.h").write_text(
        '#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE "SNOOT GAME"\n'
        '#define VN_SAVE_PREFIX "BASLUS-99999SNOOT"\n#define VN_SAVE_MAGIC "SNS1"\n',
        encoding="utf-8",
        newline="\n",
    )
    make_cmd = "make -f /src/platforms/ps4/Makefile"
    if trace:
        make_cmd += " VN_TRACE=1"
    command = [
        "docker",
        "run",
        "--rm",
        "--entrypoint",
        "/bin/bash",
        "-v",
        f"{ROOT.as_posix()}:/src",
        "-w",
        "/src/build/ps4",
        IMAGE,
        "-c",
        make_cmd,
    ]
    subprocess.run(command, check=True)
    return out / "snoot.pkg"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    pkg = build(args.trace)
    print(pkg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
