"""Adapter PS3/RPCS3 del Console Test Lab (T-613, T-621).

Instala el firmware oficial y el ``snoot.pkg`` en RPCS3 si faltan, copia el disco de PS1 a
``dev_hdd0/game/SNOT00001/USRDIR/data`` con el ``AUTOTEST.BIN`` del escenario, escribe la configuracion
propia del juego (renderer OpenGL y opciones del RSX, T-621), corre RPCS3 con ``--no-gui`` (sin la
ventana del emulador, con renderer real) sobre el ``EBOOT.BIN`` instalado y extrae la traza del
``log/TTY.log``, que es donde RPCS3 deja lo que el juego escribe por ``printf`` (sys_tty_write).

``--headless`` (renderer Null) no sirve para este juego: SDL_PSL1GHT bloquea cada cuadro en
``waitFlip`` (``build/ps3/sdl2-src/src/render/psl1ght/SDL_psl1ghtrender.c:113``, bucle sobre
``gcmGetFlipStatus`` + ``usleep(200)`` desde ``PSL1GHT_RenderPresent``, linea 798) y el renderer Null
nunca completa el flip, asi que el juego no avanza del primer cuadro.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

from .autotest import autotest_bin, scenario_steps

ROOT = Path(__file__).resolve().parents[2]
RPCS3_DIR = Path(r"E:\snoot\rpcs3-c365ea76a552961ff078")
RPCS3_EXE = RPCS3_DIR / "rpcs3.exe"
FIRMWARE = Path(r"E:\snoot\ps3 firmware") / "PS3UPDAT.PUP"
GAME_ID = "SNOT00001"
# RPCS3 portable: EmulatorDir es el directorio del rpcs3.exe, ahi van dev_flash y dev_hdd0 (RPCS3.log, "Mounted
# path /dev_hdd0"), y el TTY del juego queda en log/TTY.log.
DEV_FLASH = RPCS3_DIR / "dev_flash"
GAME_DIR = RPCS3_DIR / "dev_hdd0" / "game" / GAME_ID
DATA_DIR = GAME_DIR / "USRDIR" / "data"
EBOOT = GAME_DIR / "USRDIR" / "EBOOT.BIN"
TTY_LOG = RPCS3_DIR / "log" / "TTY.log"
# Configuracion propia del juego en RPCS3 (T-621). El renderer OpenGL con "Force CPU Blit" evita el
# crash del cache de texturas con los blits chicos del renderer software de SDL_PSL1GHT
# (GLTextureCache.h:729 / VKTextureCache.cpp:1053, "Verification failed (object: 0x0)"); "Write/Read
# Color Buffers" y las opciones strict son las que acompanan la unica corrida con flips continuos a
# ~30 fps en este host (RPCS3.log: 7 "Flip texture was not found in cache" y despues silencio).
CUSTOM_CONFIG = RPCS3_DIR / "config" / "custom_configs" / "config_SNOT00001.yml"
CUSTOM_CONFIG_TEXT = (
    "Video:\n"
    "  Renderer: OpenGL\n"
    "  Resolution: 1280x720\n"
    "  Force CPU Blit: true\n"
    "  Write Color Buffers: true\n"
    "  Read Color Buffers: true\n"
    "  Strict Texture Flushing: true\n"
    "  Strict Rendering Mode: true\n"
)
# RPCS3 no corre el juego en tiempo real: el puerto SDL2 de PSL1GHT solo tiene renderer software y el
# guion avanza por cuadros de juego, asi que el plazo del escenario (max_seconds, pensado para consolas
# en tiempo real) se escala por este factor.
TIMEOUT_FACTOR = 8


def extract_trace(log: str) -> str:
    """Las lineas ``T|`` que el juego escribio por stdout (sys_tty_write de RPCS3 en TTY.log)."""
    return "".join(f"{line}\n" for line in log.splitlines() if line.startswith("T|"))


def install_firmware() -> None:
    """Instala el firmware oficial con ``--headless --installfw`` si ``dev_flash`` esta vacio."""
    if DEV_FLASH.is_dir() and (DEV_FLASH / "sys").is_dir():
        return
    if not FIRMWARE.is_file():
        raise FileNotFoundError(f"no existe el firmware de PS3 en {FIRMWARE}")
    # RPCS3 termina el instalador headless con ruido de teardown ("Verification failed") aunque la instalacion
    # termine bien; el exit code no es fiable, se comprueba el efecto en dev_flash.
    subprocess.run([str(RPCS3_EXE), "--headless", "--installfw", str(FIRMWARE)], capture_output=True)
    if not (DEV_FLASH / "sys").is_dir():
        raise RuntimeError(f"RPCS3 no instalo el firmware {FIRMWARE}; revisa {RPCS3_DIR / 'log' / 'RPCS3.log'}")


def install_pkg(pkg: Path) -> None:
    """Instala el ``snoot.pkg`` con ``--headless --installpkg`` si falta el EBOOT.BIN o es mas viejo que el paquete."""
    if EBOOT.is_file() and pkg.is_file() and EBOOT.stat().st_mtime >= pkg.stat().st_mtime:
        return
    EBOOT.unlink(missing_ok=True)
    if not pkg.is_file():
        raise FileNotFoundError(f"no existe el paquete {pkg}; ejecuta platforms/ps3/build.py --trace")
    # Ruta absoluta obligatoria: con ruta relativa RPCS3 reporta "PKG file not found". Mismo ruido de teardown
    # que --installfw, por eso se comprueba EBOOT.BIN y no el exit code.
    subprocess.run([str(RPCS3_EXE), "--headless", "--installpkg", str(pkg.resolve())], capture_output=True)
    if not EBOOT.is_file():
        raise RuntimeError(f"RPCS3 no instalo el paquete {pkg}; revisa {RPCS3_DIR / 'log' / 'RPCS3.log'}")


def install_custom_config() -> None:
    """Escribe ``config/custom_configs/config_SNOT00001.yml`` si falta (RPCS3 la aplica al arrancar)."""
    if CUSTOM_CONFIG.is_file():
        return
    CUSTOM_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CUSTOM_CONFIG.write_text(CUSTOM_CONFIG_TEXT, encoding="utf-8", newline="\n")


def stage_data(data_dir: Path, disc: Path, autotest: bytes) -> Path:
    """Copia los archivos del disco de PS1 en ``USRDIR/data`` y escribe el ``AUTOTEST.BIN`` del escenario."""
    data_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(disc, data_dir, dirs_exist_ok=True)
    (data_dir / "AUTOTEST.BIN").write_bytes(autotest)
    return data_dir


def run_scenario(scenario, out: Path) -> Path:
    """Corre el escenario en RPCS3 y devuelve la ruta de la traza (out/trace.txt)."""
    out.mkdir(parents=True, exist_ok=True)
    disc = ROOT / "build" / "ctl" / "ps1" / "disc"
    if not disc.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")
    if not RPCS3_EXE.is_file():
        raise FileNotFoundError(f"no existe el emulador RPCS3 en {RPCS3_EXE}")

    subprocess.run([sys.executable, str(ROOT / "platforms" / "ps3" / "build.py"), "--trace"], cwd=ROOT, check=True)
    install_firmware()
    install_pkg(ROOT / "build" / "ps3" / "snoot.pkg")
    install_custom_config()
    stage_data(DATA_DIR, disc, autotest_bin(scenario_steps(scenario)))

    TTY_LOG.parent.mkdir(exist_ok=True)
    TTY_LOG.unlink(missing_ok=True)
    # --no-gui corre el (S)ELF con el renderer de la configuracion propia (OpenGL), sin la ventana del
    # emulador: --headless fuerza el renderer Null y el juego se queda esperando el flip del RSX para
    # siempre (ver waitFlip en el docstring del modulo). El juego termina con exit(0) del AUTOTEST, que
    # detiene la emulacion. Si no sale, lo corta limits.max_seconds.
    proc = subprocess.Popen([str(RPCS3_EXE), "--no-gui", str(EBOOT.resolve())],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + scenario.limits.max_seconds * TIMEOUT_FACTOR
    while proc.poll() is None and time.monotonic() < deadline:
        time.sleep(1)
    if proc.poll() is None:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        proc.wait()

    log = TTY_LOG.read_text(encoding="utf-8", errors="replace") if TTY_LOG.exists() else ""
    trace_path = out / "trace.txt"
    trace_path.write_text(extract_trace(log), encoding="utf-8", newline="\n")
    return trace_path
