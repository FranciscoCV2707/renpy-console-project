"""Compila Snoot para PS Vita con VitaSDK en Docker y empaqueta snoot.vpk."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "vitasdk/vitasdk@sha256:8227da1b596d981f4513cd9b36bda1e43857f6dae5bcf4312c1cd40167f7d9bb"


def build(trace: bool = False) -> Path:
	out = ROOT / "build" / "vita"
	generated = out / "generated"
	generated.mkdir(parents=True, exist_ok=True)
	(generated / "game_config.h").write_text(
		'#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE "SNOOT GAME"\n'
		'#define VN_SAVE_PREFIX "BASLUS-99999SNOOT"\n#define VN_SAVE_MAGIC "SNS1"\n',
		encoding="utf-8",
		newline="\n",
	)
	command = [
		"docker", "run", "--rm",
		"-v", f"{ROOT.as_posix()}:/src",
		"-w", "/src",
		IMAGE, "make", "-f", "/src/platforms/vita/Makefile",
	]
	if trace:
		command.append("VN_TRACE=1")
	subprocess.run(command, cwd=ROOT, check=True)
	return out / "snoot.vpk"


def main() -> int:
	parser = argparse.ArgumentParser()
	parser.add_argument("--trace", action="store_true")
	args = parser.parse_args()
	print(build(args.trace))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
