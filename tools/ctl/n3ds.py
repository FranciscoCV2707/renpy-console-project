"""Adapter Nintendo 3DS/Azahar del Console Test Lab (T-610).

Copia Azahar 2126.2 en ``build/ctl/3ds/azahar/`` con una carpeta de usuario propia
(en Windows, ``<exe>/user`` activa el modo portatil: ``common/file_util.cpp`` de
Azahar), monta la SD virtual en ``user/sdmc/3ds/snoot/data`` con los archivos del
disco de PS1 mas el ``AUTOTEST.BIN`` del escenario, arranca ``build/3ds/snoot.3dsx``
y extrae la traza de ``user/log/azahar_log.txt``.

La traza llega por ``svcOutputDebugString``: el bloque de 3DS de
``platforms/sdl/sdl_target.h`` instala un devoptab de stdout que manda cada
linea ahi (T-619), y Azahar lo loguea como ``Debug.Emulated``; sin eso libctru
descartaria el ``puts`` del motor hasta un ``consoleInit``. La marca de fin del
juego (``VN_QUIT``, tambien por svc) cierra Azahar, y las capturas del
AUTOTEST (paso ``shot``) caen en ``user/sdmc/3ds/snoot/*.bmp`` y se copian a
``out/``.
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
AZAHAR = Path(r"E:\snoot\azahar-2126.2\azahar-windows-msvc-2126.2")
EXE = "azahar.exe"
GAME_DATA = Path("3ds") / "snoot" / "data"
# [Miscellaneous] log_filter: "*:Debug" deja pasar las lineas Debug.Emulated; hay que
# poner "<clave>\default=false" porque Azahar ignora el valor mientras "default" sea true
# (azahar_log.txt mostraba solo <Info> aunque el ini dijera *:Debug).
LOG_FILTER = "*:Debug"
# Azahar no se cierra al terminar el juego (vuelve a su lista): se espera la marca de
# fin del juego en el log y se corta el proceso, igual que tools/ctl/psp.py con PPSSPP.
END_MARKER = b"VN_QUIT"


def extract_trace(log: str) -> str:
    """Las lineas ``T|`` que el juego escribio por svcOutputDebugString.

    Azahar las deja como ``Debug.Emulated <Debug> ...OutputDebugString:1190: T|...``.
    """
    lines: list[str] = []
    for raw_line in log.splitlines():
        if "OutputDebugString" not in raw_line:
            continue
        if "T|" in raw_line:
            lines.append(raw_line[raw_line.index("T|"):])
    return "".join(f"{line}\n" for line in lines)


def stage_emulator(out: Path) -> Path:
    """Copia Azahar dentro de ``build/`` y devuelve la ruta de su ejecutable.

    En Windows Azahar usa ``<exe>/user`` como carpeta de usuario si existe
    (``common/file_util.cpp``), asi que la copia dentro de ``build/`` deja fuera del
    emulador los datos del usuario real.
    """
    local = out / "azahar"
    if not (local / EXE).is_file():
        if not AZAHAR.is_dir():
            raise FileNotFoundError(f"no existe Azahar en {AZAHAR}")
        local.mkdir(parents=True, exist_ok=True)
        shutil.copytree(AZAHAR, local, dirs_exist_ok=True)
    return local / EXE


def stage_sd(user: Path, disc: Path, autotest: bytes, shot_names: str = "") -> Path:
    """Copia el disco de PS1 en ``user/sdmc/3ds/snoot/data`` y escribe el AUTOTEST.

    Con ``shot_names`` escribe tambien ``shot_names.txt`` al lado de ``data``:
    el bloque de 3DS de ``sdl_target.h`` lo lee en el arranque para nombrar las
    capturas (``VN_SHOT_DIR``/``VN_SHOT_NAMES``, igual que el de Vita).
    """
    data = user / "sdmc" / GAME_DATA
    data.mkdir(parents=True, exist_ok=True)
    shutil.copytree(disc, data, dirs_exist_ok=True)
    (data / "AUTOTEST.BIN").write_bytes(autotest)
    if shot_names:
        (data.parent / "shot_names.txt").write_text(shot_names, encoding="utf-8")
    return data


def stage_config(user: Path) -> None:
    """Escribe el ``qt-config.ini`` con el filtro de log en Debug y el RPC activado.

    ``log_filter`` y ``enable_rpc_server`` van con su linea ``\\default=false``: con
    ``\\default=true`` Azahar lee el valor por defecto (settings.h) y al arrancar
    reescribe el ini, perdiendo el cambio.
    """
    config = user / "config"
    config.mkdir(parents=True, exist_ok=True)
    ini = config / "qt-config.ini"
    text = ini.read_text(encoding="utf-8") if ini.is_file() else ""
    lines = text.splitlines()
    for key, value in (("log_filter", LOG_FILTER), ("enable_rpc_server", "true")):
        for i, line in enumerate(lines):
            if line.split("\\", 1)[0] == key:
                if "\\" in line:  # linea "key\default=..." justo antes del valor
                    lines[i] = f"{key}\\default=false"
                    if i + 1 < len(lines) and lines[i + 1].split("=", 1)[0] == key:
                        lines[i + 1] = f"{key}={value}"
                        break
                lines[i] = f"{key}={value}"
                lines.insert(i, f"{key}\\default=false")
                break
        else:
            section = _SECTION_FOR_KEY[key]
            if section not in lines:
                lines.append(section)
            lines.extend((f"{key}\\default=false", f"{key}={value}"))
    ini.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\r\n")


_SECTION_FOR_KEY = {"log_filter": "[Miscellaneous]", "enable_rpc_server": "[Debugging]"}


def run_scenario(scenario, out: Path) -> Path:
    """Corre el escenario en Azahar y devuelve la ruta de la traza (out/trace.txt)."""
    out.mkdir(parents=True, exist_ok=True)
    disc = ROOT / "build" / "ctl" / "ps1" / "disc"
    if not disc.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")
    subprocess.run([sys.executable, str(ROOT / "platforms" / "3ds" / "build.py"), "--trace"],
                   cwd=ROOT, check=True)
    rom = ROOT / "build" / "3ds" / "snoot.3dsx"
    if not rom.is_file():
        raise FileNotFoundError(f"no se encontro el ejecutable {rom}")

    exe = stage_emulator(out)
    user = exe.parent / "user"
    steps = scenario_steps(scenario)
    shot_names = ",".join(value for _, action, value in steps if action == "shot")
    stage_sd(user, disc, autotest_bin(steps), shot_names)
    stage_config(user)

    log_path = user / "log" / "azahar_log.txt"
    log_path.unlink(missing_ok=True)
    # el .3dsx se arranca como ultimo argumento sin guion (citra_qt.cpp de Azahar:
    # "Launch game at path"); Azahar sigue abierto tras el juego, como PPSSPP.
    proc = subprocess.Popen([str(exe), str(rom)], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
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
    for bmp in (user / "sdmc" / "3ds" / "snoot").glob("*.bmp"):
        shutil.copy2(bmp, out / bmp.name)
    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    trace_path = out / "trace.txt"
    trace_path.write_text(extract_trace(log), encoding="utf-8", newline="\n")
    if not trace_path.read_text(encoding="utf-8"):
        raise ScenarioError("3ds", "sin traza: el juego no escribio lineas T| por "
                                   "svcOutputDebugString (revisa azahar_log.txt en "
                                   "build/ctl/3ds/azahar/user/log/)")
    return trace_path
