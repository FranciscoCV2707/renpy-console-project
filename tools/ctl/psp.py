"""Adapter PSP/PPSSPP del Console Test Lab (T-501).

Arma la Memory Stick en ``build/ctl/psp/ms/`` con el ``EBOOT.PBP``, los archivos del disco de PS1 y el
``AUTOTEST.BIN`` del escenario, corre PPSSPP sobre ella y saca la traza del log, que es donde PPSSPP deja lo que
el juego escribe por stdout.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

from .autotest import autotest_bin, scenario_steps

ROOT = Path(__file__).resolve().parents[2]
PPSSPP = Path(r"E:\snoot\ppsspp-1.20.4")
EXE = "PPSSPPWindows64.exe"
GAME = Path("PSP") / "GAME" / "SNOOT"
# --loglevel=4 es LogLevel::LINFO (Common/Log.h de PPSSPP); stdout sale como "I[PRINTF]: ... stdout: ..."
LOG_LEVEL_INFO = "4"
# EmuScreen::checkPowerDown lo escribe cuando el juego llama a sceKernelExitGame (UI/EmuScreen.cpp)
END_MARKER = b"SELF-POWERDOWN!"


def extract_trace(log: str) -> str:
    """Las lineas ``T|`` que el juego escribio por stdout (sceIoWrite con fd 1, Log::Printf de PPSSPP)."""
    lines = []
    for line in log.splitlines():
        _, sep, rest = line.partition("stdout: ")
        if sep and rest.startswith("T|"):
            lines.append(rest)
    return "".join(f"{line}\n" for line in lines)


def stage_memory_stick(ms: Path, disc: Path, autotest: bytes) -> Path:
    """Copia EBOOT y datos del disco en ``ms/PSP/GAME/SNOOT/`` y devuelve la ruta del EBOOT."""
    game = ms / GAME
    (game / "DATA").mkdir(parents=True, exist_ok=True)
    (disc / "AUTOTEST.BIN").write_bytes(autotest)
    shutil.copytree(disc, game / "DATA", dirs_exist_ok=True)
    shutil.copy2(ROOT / "build" / "psp" / "EBOOT.PBP", game / "EBOOT.PBP")
    return game / "EBOOT.PBP"


def stage_ppsspp(out: Path, ms: Path) -> Path:
    """Copia PPSSPP dentro de ``build/`` con un ``installed.txt`` que apunta a la Memory Stick (Windows/main.cpp)."""
    local = out / "ppsspp"
    if not (local / EXE).is_file():
        local.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PPSSPP / EXE, local / EXE)
        shutil.copytree(PPSSPP / "assets", local / "assets", dirs_exist_ok=True)
    (local / "installed.txt").write_text(str(ms.resolve()), encoding="utf-8")
    return local / EXE


def run_scenario(scenario, out: Path) -> Path:
    """Corre el escenario en PPSSPP y devuelve la ruta de la traza (out/trace.txt)."""
    out.mkdir(parents=True, exist_ok=True)
    disc = ROOT / "build" / "ctl" / "ps1" / "disc"
    if not disc.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")
    subprocess.run([sys.executable, str(ROOT / "platforms" / "psp" / "build.py"), "--trace"], cwd=ROOT, check=True)
    eboot = stage_memory_stick(out / "ms", disc, autotest_bin(scenario_steps(scenario)))
    exe = stage_ppsspp(out, out / "ms")
    log_path = out / "log.txt"
    log_path.unlink(missing_ok=True)
    # PPSSPP 1.20.4 no cierra al terminar el juego (--pause-menu-exit solo cambia el menu de pausa): se espera la
    # marca de fin y se corta el proceso, igual que hace tools/ctl/ps1.py con PCSX-Redux.
    proc = subprocess.Popen([str(exe), str(eboot), f"--log={log_path}", f"--loglevel={LOG_LEVEL_INFO}"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + scenario.limits.max_seconds
    seen = 0
    while proc.poll() is None and time.monotonic() < deadline:
        if log_path.exists():
            with log_path.open("rb") as f:
                f.seek(seen)
                chunk = f.read()
                seen = f.tell()
            if END_MARKER in chunk:
                break
        time.sleep(1)
    time.sleep(2)
    if proc.poll() is None:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        proc.wait()
    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    trace_path = out / "trace.txt"
    trace_path.write_text(extract_trace(log), encoding="utf-8", newline="\n")
    return trace_path
