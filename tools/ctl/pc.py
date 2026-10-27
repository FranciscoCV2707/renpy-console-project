"""Adapter SDL2: corre el ejecutable de PC sobre los archivos del disco PS1."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .autotest import autotest_bin, scenario_steps

ROOT = Path(__file__).resolve().parents[2]


def run_scenario(scenario, out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    disc = ROOT / "build" / "ctl" / "ps1" / "disc"
    if not disc.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")
    steps = scenario_steps(scenario)
    (disc / "AUTOTEST.BIN").write_bytes(autotest_bin(steps))
    executable = ROOT / "build" / "pc" / "snoot.exe"
    subprocess.run([sys.executable, str(ROOT / "platforms" / "sdl" / "build.py"), "--trace"],
                   cwd=ROOT, check=True)
    env = os.environ.copy()
    env.update({
        "VN_FAST": "1",
        "VN_DATA_DIR": str(disc),
        "VN_SAVE_DIR": str(out / "save"),
    })
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    shot_names = ",".join(value for _, action, value in steps if action == "shot")
    if shot_names:
        env["VN_SHOT_DIR"] = str(out)
        env["VN_SHOT_NAMES"] = shot_names
    (out / "save").mkdir(exist_ok=True)
    proc = subprocess.run([str(executable)], cwd=ROOT, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=scenario.limits.max_seconds, check=False)
    trace = "".join(f"{line}\n" for line in proc.stdout.splitlines() if line.startswith("T|"))
    trace_path = out / "trace.txt"
    trace_path.write_text(trace, encoding="utf-8", newline="\n")
    (out / "stdout.txt").write_text(proc.stdout + proc.stderr, encoding="utf-8", newline="\n")
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, str(executable), output=proc.stdout, stderr=proc.stderr)
    return trace_path
