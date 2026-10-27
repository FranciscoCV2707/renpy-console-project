"""Adapter SDL2/PCSX2 del Console Test Lab para PS2."""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

from .autotest import autotest_bin, scenario_steps

ROOT = Path(__file__).resolve().parents[2]
PCSX2 = Path(r"E:\snoot\pcsx2-2.8.2\pcsx2-qt.exe")


def extract_trace(text: str) -> str:
    # PCSX2 antepone la hora a cada linea de la consola del EE: "[    1.1670] T|0|0|..."
    lines = (line.split("] ", 1)[1] if line.startswith("[") and "] " in line else line for line in text.splitlines())
    return "".join(f"{line}\n" for line in lines if line.startswith("T|"))


def game_quit(text: str) -> bool:
    """VN_QUIT es la marca que el juego imprime antes de exit(0); PCSX2 no se cierra solo al salir el ELF."""
    return "VN_QUIT" in text


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
    stdout_path = out / "stdout.txt"
    command = [
        str(PCSX2), "-portable", "-nogui", "-fastboot", "-elf", str(executable),
        "-logfile", str(log), "-earlyconsolelog",
    ]
    with stdout_path.open("w", encoding="utf-8", newline="\n") as stdout_file:
        proc = subprocess.Popen(command, cwd=ROOT, stdout=stdout_file, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + scenario.limits.max_seconds
        while proc.poll() is None and time.monotonic() < deadline:
            text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
            if game_quit(text):
                break
            time.sleep(0.5)
        timed_out = proc.poll() is None
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        proc.wait(timeout=10)
    log_text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    console_text = stdout_path.read_text(encoding="utf-8", errors="replace")
    trace = extract_trace(log_text + "\n" + console_text)
    trace_path = out / "trace.txt"
    trace_path.write_text(trace, encoding="utf-8", newline="\n")
    if not game_quit(log_text + "\n" + console_text):
        if timed_out:
            raise subprocess.TimeoutExpired(command, scenario.limits.max_seconds)
        raise subprocess.CalledProcessError(proc.returncode or 1, command, output=console_text, stderr=log_text)
    if not trace:
        raise RuntimeError(f"PCSX2 no produjo líneas TRACE; revisa {log} y {stdout_path}")
    return trace_path
