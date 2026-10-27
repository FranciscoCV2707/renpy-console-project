"""Adapter PS4/shadPS4 del Console Test Lab (T-614).

Copia los archivos del disco de PS1 y el ``AUTOTEST.BIN`` del escenario en ``/data/snoot`` del emulador (la
particion ``data`` del usuario de shadPS4), corre shadPS4 sobre el ``eboot.bin`` del build de PS4 y saca la
traza del log, que es donde shadPS4 deja lo que el juego escribe por stdout (clase ``Tty``, prefijo ``[stdout]``).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

from .autotest import autotest_bin, scenario_steps

ROOT = Path(__file__).resolve().parents[2]
SHADPS4 = Path(r"E:\snoot\shadps4-.0.20.0\shadPS4.exe")
USER_DIR = Path.home() / "AppData" / "Roaming" / "shadPS4"
LOG_FILE = "shad_log.txt"
# exit(0) del juego: HLE exit() de shadPS4 escribe esto y muere con int3 (src/core/libraries/kernel/process.cpp);
# si el CRT termina sin exit() queda "Exit function called" (src/core/linker.cpp).
END_MARKERS = (b"Exiting with status code", b"Exit function called")


def extract_trace(log: str) -> str:
    """Las lineas ``T|`` que el juego escribio por stdout (Devices::Logger de shadPS4, src/core/file_sys)."""
    lines = []
    for line in log.splitlines():
        _, sep, rest = line.partition("[stdout] ")
        if sep and rest.startswith("T|"):
            lines.append(rest)
    return "".join(f"{line}\n" for line in lines)


def stage_user_dir(user: Path) -> None:
    """Crea ``home/1000`` y sus subcarpetas: sin ellas shadPS4 muestra el dialogo modal de migracion de partidas
    (``src/core/user_manager.cpp``, ``CreateDefaultUsers``) y el juego no arranca solo."""
    for sub in ("savedata", "trophy", "inputs"):
        (user / "home" / "1000" / sub).mkdir(parents=True, exist_ok=True)


def stage_game_data(data: Path, disc: Path, autotest: bytes) -> None:
    """Copia los archivos del disco de PS1 y el ``AUTOTEST.BIN`` del escenario en ``<user>/data/snoot``."""
    data.mkdir(parents=True, exist_ok=True)
    shutil.copytree(disc, data, dirs_exist_ok=True)
    (data / "AUTOTEST.BIN").write_bytes(autotest)


def run_scenario(scenario, out: Path) -> Path:
    """Corre el escenario en shadPS4 y devuelve la ruta de la traza (out/trace.txt)."""
    out.mkdir(parents=True, exist_ok=True)
    disc = ROOT / "build" / "ctl" / "ps1" / "disc"
    if not disc.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")
    if not SHADPS4.is_file():
        raise FileNotFoundError(f"no existe el emulador shadPS4 en {SHADPS4}")
    subprocess.run([sys.executable, str(ROOT / "platforms" / "ps4" / "build.py"), "--trace"], cwd=ROOT, check=True)
    eboot = ROOT / "build" / "ps4" / "eboot.bin"
    if not eboot.is_file():
        raise FileNotFoundError(f"no se encontro {eboot}")
    stage_user_dir(USER_DIR)
    stage_game_data(USER_DIR / "data" / "snoot", disc, autotest_bin(scenario_steps(scenario)))
    log_path = USER_DIR / "log" / LOG_FILE
    log_path.unlink(missing_ok=True)
    proc = subprocess.Popen([str(SHADPS4), "--game", str(eboot), "-f", "false"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + scenario.limits.max_seconds
    seen = 0
    while proc.poll() is None and time.monotonic() < deadline:
        if log_path.exists():
            with log_path.open("rb") as f:
                f.seek(seen)
                chunk = f.read()
                seen = f.tell()
            if any(marker in chunk for marker in END_MARKERS):
                break
        time.sleep(1)
    time.sleep(2)
    if proc.poll() is None:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        proc.wait()
    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    if log_path.is_file():
        shutil.copy2(log_path, out / "log.txt")
    trace_path = out / "trace.txt"
    trace_path.write_text(extract_trace(log), encoding="utf-8", newline="\n")
    return trace_path
