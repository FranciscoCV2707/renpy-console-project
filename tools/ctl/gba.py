"""Adapter Game Boy Advance/mGBA del Console Test Lab (T-710).

Compila la ROM snoot.gba con VN_TRACE habilitado y el AUTOTEST.BIN del escenario dentro del archivo
GBFS anexado a la ROM. Ejecuta mGBA CLI (mgba-sdl) con fastForward=1 y volcado de depuración
a archivo (opciones -C logToFile=1 -C logFile=... -l 31). El motor emite la traza en los registros
de depuración REG_DEBUG_* de mGBA. Al concluir el recorrido (AUTOTEST_DONE o GBA: SCRIPT QUIT),
el adapter cierra mGBA y extrae las líneas T| de la traza para su comparación contra la referencia.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .autotest import autotest_bin, scenario_steps

ROOT = Path(__file__).resolve().parents[2]
MGBA_SDL = Path(r"E:\snoot\mgba-0.10.5\mGBA-0.10.5-win64\mgba-sdl.exe")
DISC = ROOT / "build" / "ctl" / "ps1" / "disc"


def extract_trace(log: str) -> str:
    """Extrae las líneas T| emitidas por la traza del motor en el registro de depuración."""
    lines = []
    for line in log.splitlines():
        line = line.strip()
        idx = line.find("T|")
        if idx != -1:
            lines.append(line[idx:])
    return "".join(f"{line}\n" for line in lines)


def run_scenario(scenario, out: Path) -> Path:
    """Corre el escenario en mGBA y devuelve la ruta de la traza (out/trace.txt)."""
    out.mkdir(parents=True, exist_ok=True)
    if not DISC.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")

    if not MGBA_SDL.is_file():
        raise FileNotFoundError(f"no se encontró el emulador mGBA en {MGBA_SDL}")

    from platforms.gba.build import build

    steps = scenario_steps(scenario)
    raw_autotest = autotest_bin(steps)

    autotest_path = out / "AUTOTEST.BIN"
    autotest_path.write_bytes(raw_autotest)

    rom = build(trace=True, autotest_path=autotest_path)

    log_path = out / "mgba_log.txt"
    if log_path.exists():
        log_path.unlink()

    limits = getattr(scenario, "limits", None)
    if hasattr(limits, "max_seconds"):
        max_seconds = int(getattr(limits, "max_seconds") or 60)
    elif isinstance(limits, dict):
        max_seconds = int(limits.get("max_seconds", 60))
    else:
        max_seconds = 60

    cmd = [
        str(MGBA_SDL),
        "-C",
        "fastForward=1",
        "-C",
        "audioSync=0",
        "-C",
        "videoSync=0",
        "-C",
        "fpsTarget=0",
        "-C",
        "logToFile=1",
        "-C",
        f"logFile={log_path.as_posix()}",
        "-l",
        "31",
        str(rom),
    ]

    proc = subprocess.Popen(cmd)
    start_time = time.time()
    try:
        while time.time() - start_time < max_seconds:
            time.sleep(0.5)
            if log_path.exists():
                try:
                    text = log_path.read_text(encoding="utf-8", errors="replace")
                    if "AUTOTEST_DONE" in text or "GBA: SCRIPT QUIT" in text:
                        break
                except OSError:
                    pass
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    clean = extract_trace(log_text)
    out_trace = out / "trace.txt"
    out_trace.write_text(clean, encoding="utf-8", newline="\n")
    return out_trace
