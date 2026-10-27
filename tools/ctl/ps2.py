"""Adapter SDL2/PCSX2 del Console Test Lab para PS2."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .autotest import autotest_bin, scenario_steps

ROOT = Path(__file__).resolve().parents[2]
PCSX2 = Path(r"E:\snoot\pcsx2-2.8.2\pcsx2-qt.exe")


def extract_trace(text: str) -> str:
    return "".join(f"{line}\n" for line in text.splitlines() if line.startswith("T|"))


def run_scenario(scenario, out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    disc = ROOT / "build" / "ctl" / "ps1" / "disc"
    if not disc.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")
    ps2_disc = ROOT / "build" / "ps2" / "disc"
    if ps2_disc.exists():
        shutil.rmtree(ps2_disc)
    shutil.copytree(disc, ps2_disc)
    steps = scenario_steps(scenario)
    (ps2_disc / "AUTOTEST.BIN").write_bytes(autotest_bin(steps))

    subprocess.run([sys.executable, str(ROOT / "platforms" / "ps2" / "build.py"), "--trace"],
                   cwd=ROOT, check=True)
    executable = ROOT / "build" / "ps2" / "snoot.elf"
    log = out / "pcsx2.log"
    command = [
        str(PCSX2), "-portable", "-nogui", "-fastboot", "-elf", str(executable),
        "-logfile", str(log), "-earlyconsolelog",
    ]
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=scenario.limits.max_seconds, check=False)
    log_text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    console_text = proc.stdout + proc.stderr
    (out / "stdout.txt").write_text(console_text, encoding="utf-8", newline="\n")
    trace = extract_trace(log_text + "\n" + console_text)
    trace_path = out / "trace.txt"
    trace_path.write_text(trace, encoding="utf-8", newline="\n")
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, command, output=console_text, stderr=log_text)
    if not trace:
        raise RuntimeError(f"PCSX2 no produjo líneas TRACE; revisa {log} y {out / 'stdout.txt'}")
    return trace_path
