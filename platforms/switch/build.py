"""Compila Snoot para Nintendo Switch con devkitA64 en Docker."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282"


def build(trace: bool = False) -> Path:
	out = ROOT / "build" / "switch"
	out.mkdir(parents=True, exist_ok=True)
	generated = out / "generated"
	generated.mkdir(exist_ok=True)
	(generated / "game_config.h").write_text(
		'#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE "SNOOT GAME"\n'
		'#define VN_SAVE_PREFIX "BASLUS-99999SNOOT"\n#define VN_SAVE_MAGIC "SNS1"\n',
		encoding="utf-8",
		newline="\n",
	)
	includes = " ".join(
		f"-I/src/{path}"
		for path in (
			"engine/core",
			"engine/platform",
			"engine/app",
			"engine/modules",
			"games/snoot",
			"platforms/sdl",
		)
	)
	sources = " ".join(
		f"/src/{folder}/*.c"
		for folder in ("engine/core", "engine/app", "engine/modules", "games/snoot", "platforms/sdl")
	)
	trace_flag = "-DVN_TRACE" if trace else ""
	script = (
		"export DEVKITPRO=/opt/devkitpro && "
		". /opt/devkitpro/switchvars.sh && "
		"/opt/devkitpro/devkitA64/bin/aarch64-none-elf-gcc -std=c99 -Wall -Wextra "
		"-Wno-unused-parameter -pedantic -O2 "
		f"{includes} -I/src/build/switch/generated {trace_flag} "
		f"{sources} "
		"$(sdl2-config --cflags) $(sdl2-config --libs) -lm "
		"-specs=/opt/devkitpro/libnx/switch.specs -lnx "
		"-o /src/build/switch/snoot.elf && "
		'nacptool --create "Snoot Game" "renpy-console-project" "0.1" /src/build/switch/snoot.nacp && '
		"elf2nro /src/build/switch/snoot.elf /src/build/switch/snoot.nro "
		"--nacp=/src/build/switch/snoot.nacp"
	)
	subprocess.run(
		[
			"docker",
			"run",
			"--rm",
			"-v",
			f"{ROOT.as_posix()}:/src",
			"-w",
			"/src",
			IMAGE,
			"sh",
			"-c",
			script,
		],
		check=True,
	)
	return out / "snoot.nro"


def main() -> int:
	parser = argparse.ArgumentParser()
	parser.add_argument("--trace", action="store_true")
	args = parser.parse_args()
	print(build(args.trace))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
