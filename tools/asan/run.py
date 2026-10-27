"""Compila el backend SDL con ASan/UBSan en Docker Linux y corre escenarios headless (T-618, Paso 1).

Imagen: ``gcc:13-bookworm`` (oficial) fijada por digest, con ``libsdl2-dev`` (ver tools/asan/Dockerfile).
El binario resultante se corre con el mismo entorno que ``tools/ctl/pc.py`` (VN_FAST, VN_DATA_DIR,
SDL_VIDEODRIVER=dummy) para que el escenario se conduzca con su AUTOTEST.BIN.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ctl.autotest import autotest_bin, scenario_steps  # noqa: E402
from tools.ctl.scenario import load_scenario  # noqa: E402

IMAGE = "renpy-console-asan:t618"
DISC = ROOT / "build" / "ctl" / "ps1" / "disc"
OUT = ROOT / "build" / "asan"
SOURCES = ("engine/core", "engine/app", "engine/modules", "games/snoot", "platforms/sdl")
INCLUDES = (
    "engine/core",
    "engine/platform",
    "engine/app",
    "engine/modules",
    "games/snoot",
    "platforms/sdl",
    "build/asan/generated",
)

GAME_CONFIG = (
    "#pragma once\n#define VN_SEEN_BYTES 2048\n#define VN_SAVE_TITLE \"SNOOT GAME\"\n"
    "#define VN_SAVE_PREFIX \"BASLUS-99999SNOOT\"\n#define VN_SAVE_MAGIC \"SNS1\"\n"
)


def docker_sh(script: str) -> subprocess.CompletedProcess:
    command = [
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
    ]
    return subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8")


def build_image() -> None:
    subprocess.run(
        ["docker", "build", "-f", str(ROOT / "tools" / "asan" / "Dockerfile"), "-t", IMAGE, str(ROOT / "tools" / "asan")],
        cwd=ROOT,
        check=True,
    )


def compile_game() -> Path:
    generated = OUT / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "game_config.h").write_text(GAME_CONFIG, encoding="utf-8", newline="\n")
    sources = " ".join(f"{folder}/*.c" for folder in SOURCES)
    includes = " ".join(f"-I{path}" for path in INCLUDES)
    script = (
        "gcc -std=c99 -Wall -Wextra -Wno-unused-parameter -pedantic -O1 -g -fno-omit-frame-pointer "
        "-fsanitize=address,undefined -DVN_TRACE -include tools/asan/linux_shim.h "
        f"{includes} {sources} $(sdl2-config --cflags --libs) -o build/asan/snoot"
    )
    docker_sh(script)
    return OUT / "snoot"


def run_scenario(scenario_path: Path) -> Path:
    scen = load_scenario(scenario_path)
    out = OUT / scen.id
    out.mkdir(parents=True, exist_ok=True)
    if not DISC.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")
    (DISC / "AUTOTEST.BIN").write_bytes(autotest_bin(scenario_steps(scen)))
    (out / "save").mkdir(exist_ok=True)
    shot_names = ",".join(value for _, action, value in scenario_steps(scen) if action == "shot")
    env = [
        "-e",
        "VN_FAST=1",
        "-e",
        f"VN_DATA_DIR=/src/{DISC.relative_to(ROOT).as_posix()}",
        "-e",
        f"VN_SAVE_DIR=/src/{(out / 'save').relative_to(ROOT).as_posix()}",
        "-e",
        "SDL_VIDEODRIVER=dummy",
        "-e",
        "SDL_AUDIODRIVER=dummy",
        "-e",
        "ASAN_OPTIONS=halt_on_error=1:detect_leaks=0",
        "-e",
        "UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1",
    ]
    if shot_names:
        env += ["-e", f"VN_SHOT_DIR=/src/{out.relative_to(ROOT).as_posix()}", "-e", f"VN_SHOT_NAMES={shot_names}"]
    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{ROOT.as_posix()}:/src",
        "-w",
        "/src",
        *env,
        IMAGE,
        "/src/build/asan/snoot",
    ]
    proc = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=scen.limits.max_seconds or 300,
        check=False,
    )
    (out / "stdout.txt").write_text(proc.stdout, encoding="utf-8", newline="\n")
    (out / "stderr.txt").write_text(proc.stderr, encoding="utf-8", newline="\n")
    report = out / "asan.txt"
    report.write_text(proc.stderr if proc.stderr.strip() else proc.stdout, encoding="utf-8", newline="\n")
    print(f"exit={proc.returncode} -> {report}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", action="append", default=[], help="yaml del escenario (se puede repetir)")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    os.chdir(ROOT)
    if not args.skip_build:
        build_image()
        compile_game()
    for scenario in args.scenario:
        run_scenario(Path(scenario))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
