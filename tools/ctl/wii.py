"""Adapter Wii / Dolphin del Console Test Lab (T-611).

Prepara la raiz de usuario de Dolphin en ``build/ctl/wii/user/`` con la carpeta de sincronizacion
``user/Load/WiiSDSync/apps/snoot/data`` (archivos del disco de PS1 mas el ``AUTOTEST.BIN`` del
escenario), corre ``build/wii/boot.dol`` en modo batch con la SD virtual sincronizada y extrae la
traza del log ``user/Logs/dolphin.log``, donde Dolphin deja el OSReport del juego.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

from .autotest import autotest_bin, scenario_steps
from .scenario import ScenarioError

ROOT = Path(__file__).resolve().parents[2]
DOLPHIN_EXE = Path(r"E:\snoot\dolphin-2609a\Dolphin-x64\Dolphin.exe")
GAME_DATA = Path("apps") / "snoot" / "data"
# WiiSDCardFilesize esta en bytes (MainSettings.cpp escribe MebibytesToBytes); el disco de PS1
# pesa ~222 MB, asi que 2 GiB cubre datos y partidas (el minimo de la GUI, 128 MiB, no alcanza).
SD_FILESIZE_BYTES = "2147483648"

_UIA_SCAN_PS = r'''
Add-Type -AssemblyName UIAutomationClient
$target = {pid}
$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ProcessIdProperty, $target)
$els = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
foreach ($e in $els) {{
  Write-Output ("WIN <" + $e.Current.Name + ">")
  $kids = $e.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                      [System.Windows.Automation.Condition]::TrueCondition)
  foreach ($k in $kids) {{
    if ($k.Current.ControlType.ProgrammaticName -eq "ControlType.Window") {{
      Write-Output ("DLG <" + $k.Current.Name + ">")
    }}
    if ($k.Current.ControlType.ProgrammaticName -eq "ControlType.Text") {{
      Write-Output ("TEXT " + $k.Current.Name)
    }}
  }}
}}
'''


def extract_trace(log: str) -> str:
    """Las lineas ``T|`` que el juego escribio por OSReport, quitando el prefijo del log."""
    lines: list[str] = []
    for raw_line in log.splitlines():
        line = raw_line.strip()
        if "T|" not in line:
            continue
        lines.append(line[line.index("T|"):])
    return "".join(f"{line}\n" for line in lines)


def stage_config(user: Path) -> None:
    """Escribe el Dolphin.ini del user folder aislado.

    [Analytics] PermissionAsked evita el dialogo "Allow Usage Statistics Reporting" que en batch
    bloquea el arranque; [Interface] ConfirmStop evita el "Do you want to stop the current
    emulation?" al cerrar. El logging va por overrides `-C Logger.*` (LogManager.cpp).
    """
    config = user / "Config"
    config.mkdir(parents=True, exist_ok=True)
    (config / "Dolphin.ini").write_text(
        "[Analytics]\r\nEnabled = False\r\nPermissionAsked = True\r\n\r\n"
        "[Interface]\r\nConfirmStop = False\r\n",
        encoding="utf-8", newline="\r\n")


def stage_sd(sync: Path, disc: Path, autotest: bytes) -> Path:
    """Copia los archivos del disco de PS1 en ``WiiSDSync/apps/snoot/data`` y escribe el AUTOTEST."""
    data = sync / GAME_DATA
    data.mkdir(parents=True, exist_ok=True)
    shutil.copytree(disc, data, dirs_exist_ok=True)
    (data / "AUTOTEST.BIN").write_bytes(autotest)
    return data


def _scan_windows(pid: int) -> tuple[bool, str]:
    """Si el proceso tiene un dialogo Warning (crash del juego), devuelve (True, su texto)."""
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          _UIA_SCAN_PS.format(pid=pid)],
                         capture_output=True, check=False).stdout
    text = out.decode("mbcs", errors="replace")
    warning = False
    for line in text.splitlines():
        if line.startswith("WIN <") or line.startswith("DLG <"):
            if line[5:-1] == "Warning":
                warning = True
    body = " ".join(line[5:] for line in text.splitlines() if line.startswith("TEXT "))
    return warning, " ".join(body.split())


def run_scenario(scenario, out: Path) -> Path:
    """Corre el escenario en Dolphin y devuelve la ruta de la traza (out/trace.txt)."""
    out.mkdir(parents=True, exist_ok=True)
    disc = ROOT / "build" / "ctl" / "ps1" / "disc"
    if not disc.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")
    if not DOLPHIN_EXE.is_file():
        raise FileNotFoundError(f"no existe el emulador Dolphin en {DOLPHIN_EXE}")

    subprocess.run([sys.executable, str(ROOT / "platforms" / "wii" / "build.py"), "--trace"],
                   cwd=ROOT, check=True)
    dol = ROOT / "build" / "wii" / "boot.dol"
    if not dol.is_file():
        raise FileNotFoundError(f"no se encontro el ejecutable {dol}")

    user = out / "user"
    stage_config(user)
    stage_sd(user / "Load" / "WiiSDSync", disc, autotest_bin(scenario_steps(scenario)))
    # sin SD previa Dolphin crea la imagen con el tamaño de WiiSDCardFilesize al insertar la SD
    (user / "Load" / "WiiSD.raw").unlink(missing_ok=True)

    log_path = user / "Logs" / "dolphin.log"
    log_path.unlink(missing_ok=True)
    cmd = [
        str(DOLPHIN_EXE),
        "-u", str(user),
        "-C", f"Dolphin.Core.WiiSDCardFilesize={SD_FILESIZE_BYTES}",
        "-C", "Dolphin.Core.WiiSDCardEnableFolderSync=True",
        # OSReport del juego a <user>/Logs/dolphin.log (Common/Logging/LogManager.cpp: LOGGER_* y
        # el bloque "Logs" de LogManager.cpp); el file listener escribe con flush por linea
        "-C", "Logger.Options.WriteToFile=True",
        "-C", "Logger.Options.Verbosity=6",
        "-C", "Logger.Logs.OSREPORT=True",
        "-C", "Logger.Logs.OSREPORT_HLE=True",
        "-b", "-e", str(dol),
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + scenario.limits.max_seconds
    crash = ""
    while proc.poll() is None and time.monotonic() < deadline:
        time.sleep(10)
        if proc.poll() is not None:
            break
        warning, text = _scan_windows(proc.pid)
        if warning:
            crash = text
            break
    # cerrar la ventana de render con WM_CLOSE no detiene el batch: solo queda el corte forzoso
    if proc.poll() is None:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, check=False)
        proc.wait()
    if crash:
        raise ScenarioError("dolphin", f"boot.dol crasheo al arrancar: {crash}")

    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    trace_path = out / "trace.txt"
    trace_path.write_text(extract_trace(log), encoding="utf-8", newline="\n")
    return trace_path
