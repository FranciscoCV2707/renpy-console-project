"""Adapter PS Vita / Vita3K del Console Test Lab (T-608).

Prepara la raiz de emulacion de Vita en ``build/ctl/vita/pref/`` con el ``snoot.vpk``, los archivos del disco de PS1
en ``ux0:data/snoot/`` y el ``AUTOTEST.BIN`` del escenario, corre Vita3K con el frontend SDL y extrae la traza del log.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

from .autotest import autotest_bin, scenario_steps

ROOT = Path(__file__).resolve().parents[2]
VITA3K_DIR = Path(r"E:\snoot\vita3k-continuous")
VITA3K_EXE = VITA3K_DIR / "Vita3K.exe"
FIRMWARE_DIR = Path(r"E:\snoot\vita firmware")
PUP_MAIN = FIRMWARE_DIR / "PSVUPDAT.PUP"
PUP_FONTS = FIRMWARE_DIR / "PSP2UPDAT-preinst.PUP"
APPDATA_VITA = Path.home() / "AppData" / "Roaming" / "Vita3K" / "Vita3K"
BLOCK_MARKER = b"Failed to read module file ur0:/data/libshacccg.suprx"


def extract_trace(log: str) -> str:
    """Extrae las lineas ``T|`` escritas por el juego (write_file *** TTY: o stdout directo)."""
    lines = []
    for raw_line in log.splitlines():
        line = raw_line.strip()
        if "*** TTY: " in line:
            _, _, rest = line.partition("*** TTY: ")
            if rest.startswith("T|"):
                lines.append(rest)
        elif line.startswith("T|"):
            lines.append(line)
    return "".join(f"{line}\n" for line in lines)


def stage_firmware(pref: Path) -> None:
    """Asegura que los modulos os0 y vs0 del firmware esten instalados en el pref-path."""
    vs0 = pref / "vs0"
    os0 = pref / "os0"
    if vs0.is_dir() and os0.is_dir() and any(vs0.iterdir()) and any(os0.iterdir()):
        return
    if not (APPDATA_VITA / "vs0").is_dir() or not any((APPDATA_VITA / "vs0").iterdir()):
        if PUP_MAIN.is_file():
            subprocess.run([str(VITA3K_EXE), "--firmware", str(PUP_MAIN)], check=True)
        if PUP_FONTS.is_file():
            subprocess.run([str(VITA3K_EXE), "--firmware", str(PUP_FONTS)], check=True)
    if (APPDATA_VITA / "os0").is_dir():
        shutil.copytree(APPDATA_VITA / "os0", os0, dirs_exist_ok=True)
    if (APPDATA_VITA / "vs0").is_dir():
        shutil.copytree(APPDATA_VITA / "vs0", vs0, dirs_exist_ok=True)


def stage_config(out: Path, pref: Path) -> Path:
    """Genera un config.yml apuntando pref-path a la carpeta aislada del escenario."""
    base_cfg_path = VITA3K_DIR / "config.yml"
    if base_cfg_path.is_file():
        base_lines = base_cfg_path.read_text(encoding="utf-8").splitlines()
    else:
        base_lines = ["---", "backend-renderer: Vulkan"]
    pref_str = pref.resolve().as_posix()
    out_lines = []
    for line in base_lines:
        if line.startswith("pref-path:"):
            out_lines.append(f'pref-path: "{pref_str}"')
        elif line.startswith("log-level:"):
            out_lines.append("log-level: 0")
        elif line.startswith("initial-setup:"):
            out_lines.append("initial-setup: false")
        elif line.startswith("show-live-area-screen:"):
            out_lines.append("show-live-area-screen: false")
        elif line.startswith("boot-apps-full-screen:"):
            out_lines.append("boot-apps-full-screen: false")
        else:
            out_lines.append(line)
    if not any(line.startswith("pref-path:") for line in out_lines):
        out_lines.append(f'pref-path: "{pref_str}"')
    cfg_file = out / "config.yml"
    cfg_file.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return cfg_file


def stage_game_data(pref: Path, disc: Path, autotest: bytes) -> Path:
    """Copia los archivos de disco y el AUTOTEST.BIN a ux0:data/snoot."""
    data_dir = pref / "ux0" / "data" / "snoot"
    data_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(disc, data_dir, dirs_exist_ok=True)
    (data_dir / "AUTOTEST.BIN").write_bytes(autotest)
    (data_dir / "save").mkdir(exist_ok=True)
    return data_dir


def run_scenario(scenario, out: Path) -> Path:
    """Corre el escenario en Vita3K y devuelve la ruta de la traza (out/trace.txt)."""
    out.mkdir(parents=True, exist_ok=True)
    disc = ROOT / "build" / "ctl" / "ps1" / "disc"
    if not disc.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")
    if not VITA3K_EXE.is_file():
        raise FileNotFoundError(f"no existe el emulador Vita3K en {VITA3K_EXE}")

    subprocess.run([sys.executable, str(ROOT / "platforms" / "vita" / "build.py"), "--trace"],
                   cwd=ROOT, check=True)
    vpk_path = ROOT / "build" / "vita" / "snoot.vpk"
    if not vpk_path.is_file():
        raise FileNotFoundError(f"no se encontro el paquete {vpk_path}")

    pref = out / "pref"
    pref.mkdir(parents=True, exist_ok=True)
    stage_firmware(pref)
    cfg_path = stage_config(out, pref)
    stage_game_data(pref, disc, autotest_bin(scenario_steps(scenario)))

    log_path = out / "log.txt"
    log_path.unlink(missing_ok=True)

    cmd = [
        str(VITA3K_EXE),
        "-c", str(cfg_path),
        str(vpk_path),
        "--frontend", "sdl",
        "-l", "0",
    ]

    with log_path.open("wb") as log_file:
        proc = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + scenario.limits.max_seconds
        seen = 0
        while proc.poll() is None and time.monotonic() < deadline:
            time.sleep(1)
            if log_path.exists():
                with log_path.open("rb") as f:
                    f.seek(seen)
                    chunk = f.read()
                    seen = f.tell()
                if BLOCK_MARKER in chunk:
                    time.sleep(2)
                    break
        if proc.poll() is None:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, check=False)
            proc.wait()

    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    trace_path = out / "trace.txt"
    trace_path.write_text(extract_trace(log), encoding="utf-8", newline="\n")
    return trace_path
