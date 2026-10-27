"""Adapter Nintendo DS/melonDS del Console Test Lab (T-709).

Compila la ROM snoot.nds con VN_TRACE habilitado y el AUTOTEST.BIN del escenario en la tarjeta
SD emulada (DLDI). melonDS 1.1 sincroniza la carpeta SD con la imagen virtual dldi.bin mediante
las opciones [DLDI] del melonDS.toml (Enable, FolderSync, FolderPath, ImagePath). Al concluir
el escenario o alcanzar autotest_quit, el juego cierra la traza en fat:/trace.txt y genera fat:/done.txt;
el adapter cierra melonDS limpiamente con WM_CLOSE para asegurar la sincronización de archivos
a disco y extrae las líneas T| del trace.txt.
"""
from __future__ import annotations

import ctypes
import shutil
import subprocess
import time
from pathlib import Path

from .autotest import autotest_bin, scenario_steps

ROOT = Path(__file__).resolve().parents[2]
MELONDS = Path("E:/snoot/melonds-1.1/melonDS.exe")
CONFIG = Path("E:/snoot/melonds-1.1/melonDS.toml")
DISC = ROOT / "build" / "ctl" / "ps1" / "disc"


def extract_trace(log: str) -> str:
    """Las líneas T| emitidas por la traza del motor."""
    lines = []
    for line in log.splitlines():
        line = line.strip()
        if line.startswith("T|"):
            lines.append(line)
        elif "stdout: " in line:
            _, _, rest = line.partition("stdout: ")
            if rest.startswith("T|"):
                lines.append(rest)
    return "".join(f"{line}\n" for line in lines)


def find_window(pid: int) -> int:
    """Localiza el HWND de la ventana visible de melonDS perteneciente al PID."""
    user32 = ctypes.windll.user32
    found: list[int] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def callback(hwnd, _lparam):
        proc = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc))
        if proc.value == pid and user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            if "melonDS" in title.value:
                found.append(int(hwnd))
        return True

    user32.EnumWindows(callback, 0)
    return found[0] if found else 0


def close_melonds(proc: subprocess.Popen) -> None:
    """Cierra la ventana de melonDS con WM_CLOSE para permitir el volcado de FolderSync."""
    user32 = ctypes.windll.user32
    WM_CLOSE = 0x0010
    hwnd = 0
    for _ in range(25):
        hwnd = find_window(proc.pid)
        if hwnd:
            break
        time.sleep(0.1)

    if hwnd:
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

    try:
        proc.wait(timeout=6)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def configure_melonds_dldi(sd_path: Path, dldi_path: Path) -> None:
    """Configura las opciones de DLDI en melonDS.toml."""
    if not CONFIG.is_file():
        raise FileNotFoundError(f"no se encontró la configuración de melonDS en {CONFIG}")

    text = CONFIG.read_text(encoding="utf-8")
    lines = text.splitlines()
    new_lines: list[str] = []
    in_dldi = False
    dldi_found = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("LimitFPS"):
            new_lines.append("LimitFPS = false")
            continue
        if stripped == "[DLDI]":
            in_dldi = True
            dldi_found = True
            new_lines.append(line)
            new_lines.append(f'FolderPath = "{sd_path.resolve().as_posix()}"')
            new_lines.append("FolderSync = true")
            new_lines.append("ReadOnly = false")
            new_lines.append(f'ImagePath = "{dldi_path.resolve().as_posix()}"')
            new_lines.append("ImageSize = 1")
            new_lines.append("Enable = true")
            continue

        if in_dldi:
            if stripped.startswith("["):
                in_dldi = False
                new_lines.append(line)
            elif stripped.startswith(
                ("FolderPath", "FolderSync", "ReadOnly", "ImagePath", "ImageSize", "Enable")
            ):
                continue
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if not dldi_found:
        new_lines.append("")
        new_lines.append("[DLDI]")
        new_lines.append(f'FolderPath = "{sd_path.resolve().as_posix()}"')
        new_lines.append("FolderSync = true")
        new_lines.append("ReadOnly = false")
        new_lines.append(f'ImagePath = "{dldi_path.resolve().as_posix()}"')
        new_lines.append("ImageSize = 1")
        new_lines.append("Enable = true")

    CONFIG.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def run_scenario(scenario, out: Path) -> Path:
    """Corre el escenario en melonDS con DLDI y devuelve la ruta de la traza (out/trace.txt)."""
    out.mkdir(parents=True, exist_ok=True)
    if not DISC.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")

    from platforms.ds.build import build

    steps = scenario_steps(scenario)
    raw_autotest = autotest_bin(steps)

    sd_dir = out / "sd"
    if sd_dir.exists():
        shutil.rmtree(sd_dir)
    sd_dir.mkdir(parents=True, exist_ok=True)
    autotest_path = sd_dir / "AUTOTEST.BIN"
    autotest_path.write_bytes(raw_autotest)

    dldi_path = out / "dldi.bin"
    trace_path = sd_dir / "trace.txt"
    done_path = sd_dir / "done.txt"

    if dldi_path.exists():
        dldi_path.unlink()

    # Compilar snoot.nds con VN_TRACE y autotest
    rom = build(trace=True, autotest_path=autotest_path)

    # Configurar melonDS.toml
    configure_melonds_dldi(sd_dir, dldi_path)

    # Determinar límite de tiempo
    limits = getattr(scenario, "limits", None)
    if hasattr(limits, "max_seconds"):
        max_seconds = int(getattr(limits, "max_seconds") or 60)
    elif isinstance(limits, dict):
        max_seconds = int(limits.get("max_seconds", 60))
    else:
        max_seconds = 60

    proc = subprocess.Popen([str(MELONDS), str(rom)])
    start_time = time.time()
    try:
        while time.time() - start_time < max_seconds:
            time.sleep(0.5)
            # Comprobar si concluyo por done.txt en la SD o en la tabla de directorio FAT
            if done_path.exists():
                break
            elapsed = time.time() - start_time
            if elapsed >= 2.0 and dldi_path.exists():
                try:
                    raw_dldi = dldi_path.read_bytes()
                    if b"DONE    TXT" in raw_dldi:
                        break
                except OSError:
                    pass
    finally:
        close_melonds(proc)

    # Extraer traza
    trace_text = ""
    if trace_path.exists():
        trace_text = trace_path.read_text(encoding="utf-8", errors="replace")
    elif dldi_path.exists():
        # Fallback de lectura desde la partición FAT virtual si el emulador no completó el sync
        raw_dldi = dldi_path.read_bytes()
        lines = []
        for line in raw_dldi.split(b"\n"):
            line = line.strip(b"\r\x00")
            if line.startswith(b"T|"):
                lines.append(line.decode("utf-8", errors="replace"))
        trace_text = "\n".join(lines) + "\n"

    out_trace = out / "trace.txt"
    clean = extract_trace(trace_text)
    out_trace.write_text(clean, encoding="utf-8")
    return out_trace
