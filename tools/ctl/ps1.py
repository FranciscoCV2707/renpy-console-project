"""Adapter PS1/PCSX-Redux del Console Test Lab (T-203).

Arma el disco de Snoot con el motor de este repo compilado con VN_TRACE, lo corre en PCSX-Redux sin interfaz con el
AUTOTEST.BIN del escenario y saca la traza de la TTY. Reutiliza el arnés de vn-engine-ps1 (tests/emu/snoot.py), que
importa las herramientas de snoot-ps1; ninguno de los dos repos se modifica.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

from .autotest import autotest_bin, scenario_steps

REPO = Path(__file__).resolve().parents[2]
HARNESS = Path(r"E:\Dev\vn-engine-ps1\tests\emu\snoot.py")
SNOOT_PS1 = Path(r"E:\Dev\snoot-ps1")


def load_harness():
    """snoot.py hace `from tools.engine import ...` (el paquete tools de snoot-ps1): mientras se carga se quita el
    paquete tools de este repo de sys.modules para que no lo tape."""
    ours = {k: sys.modules.pop(k) for k in list(sys.modules) if k == "tools" or k.startswith("tools.")}
    sys.path.insert(0, str(SNOOT_PS1))
    try:
        spec = importlib.util.spec_from_file_location("vn_snoot", HARNESS)
        snoot = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(snoot)
    finally:
        sys.path.remove(str(SNOOT_PS1))
        sys.modules.update(ours)
    snoot.REPO = REPO
    return snoot


def extract_trace(tty_text: str) -> str:
    """Las líneas TRACE (C3) de la TTY, que también trae los mensajes del emulador y del motor."""
    return "".join(f"{line}\n" for line in tty_text.splitlines() if line.startswith("T|"))


def run_scenario(scenario, out: Path) -> Path:
    """Corre el escenario y devuelve la ruta de la traza (out/trace.txt)."""
    out.mkdir(parents=True, exist_ok=True)
    snoot = load_harness()
    et = snoot.et
    steps = scenario_steps(scenario)
    # build_game configura CMake en cada llamada: con VN_TRACE en el entorno el ejecutable sale con la traza
    os.environ["VN_TRACE"] = "1"
    try:
        cue = snoot.build_disc(REPO, autotest_bin(steps), out / "disc")
    finally:
        del os.environ["VN_TRACE"]
    et.ELF = REPO / "build" / "snoot.elf"
    sym = et.symbols()
    names = ", ".join(f"'{arg}'" for _, action, arg in steps if action == "shot")
    lua = out / "emutest.lua"
    lua.write_text(et.LUA % {
        "names": names, "outdir": out.as_posix(), "shot": sym["autotest_shot"], "quit": sym["autotest_quit"],
        "state": sym["state"], "vm": sym["vm"], "watch": ", ".join(f"{n} = {sym[n]}" for n in et.WATCH if n in sym),
        "failog": sym.get("res_fail_log", "nil"), "stalllog": sym.get("stall_log", "nil"),
        "synclog": sym.get("res_sync_log", "nil"), "triggers": et.parse_triggers(None),
        # un recorrido con autoplay dura lo que dure la ruta: lo corta limits.max_seconds
        "max_frames": 60 * 60 * 60 * 24 if any(a == "autoplay" for _, a, _ in steps)
        else max(f for f, _, _ in steps) + 3000}, encoding="utf-8")
    (out / "final.txt").unlink(missing_ok=True)
    tty = out / "tty.txt"
    # -stdout no sirve: pcsx-redux.exe es un lanzador que no pasa la salida de pcsx-redux.main; -logfile sí
    args = [et.REDUX, "-no-ui", "-run", "-fastboot", "-bios", et.BIOS, "-iso", cue, "-memcard1", out / "card1.mcd",
            "-logfile", tty, "-exec", f"dofile('{lua.as_posix()}')"]
    proc = subprocess.Popen([str(a) for a in args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Mismo criterio que snoot.play: PCSX-Redux no sale tras PCSX.quit(), se le da un margen tras final.txt
    deadline = time.monotonic() + scenario.limits.max_seconds
    final_at = None
    while proc.poll() is None and time.monotonic() < deadline:
        if final_at is None and (out / "final.txt").exists():
            final_at = time.monotonic()
        if final_at is not None and time.monotonic() - final_at > 5:
            break
        time.sleep(1)
    if proc.poll() is None:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        proc.wait()
    trace = out / "trace.txt"
    trace.write_text(extract_trace(tty.read_text(encoding="utf-8", errors="replace") if tty.exists() else ""),
                     encoding="utf-8", newline="\n")
    return trace
