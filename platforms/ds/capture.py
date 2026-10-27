"""Arranca ``build/ds/snoot.nds`` en melonDS 1.1 y guarda una captura de las dos pantallas.

Las opciones de línea de comandos de melonDS 1.1 (``melonDS.exe --help``) no incluyen captura de
pantalla, así que se captura el área cliente con ``PrintWindow`` (PW_CLIENTONLY). La barra de menú de
melonDS 1.1 se dibuja dentro del área cliente (Qt) y su alto no es el que melonDS reserva al tamaño de
la ventana: en este anfitrión mide 53 px, no 22, y con el tamaño por defecto la pantalla inferior queda
cortada. Por eso el alto se mide: al arranque ambas pantallas son negras y la barra es clara, así que la
primera fila oscura es el inicio de la pantalla superior; con esa medida se agranda la ventana para que
el cliente mida 256 x (barra + 384) y las pantallas quedan exactamente en las últimas 384 filas, que es
lo que se recorta. La salida es ``build/ds/snoot-screens.png``: la pantalla de arriba (256x192) sobre la
de abajo (256x192), sin barra de menú ni marco.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import struct
import subprocess
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MELONDS = Path("E:/snoot/melonds-1.1/melonDS.exe")
ROM = ROOT / "build" / "ds" / "snoot.nds"
OUT = ROOT / "build" / "ds" / "snoot-screens.png"
BOOT_SECONDS = 10
MEASURE_SECONDS = 4
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 192
SCREEN_ROWS = SCREEN_HEIGHT * 2
DARK_ROW_MEAN = 128
PW_CLIENTONLY = 2
SWP_NOMOVE = 0x0004
WM_CLOSE = 0x0010
MAX_MEASURE_TRIES = 10


def find_window(pid: int) -> int:
    user32 = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def callback(hwnd, _lparam):
        process = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process))
        if process.value == pid and user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            if "melonDS" in title.value:
                found.append(int(hwnd))
        return True

    user32.EnumWindows(callback, 0)
    if not found:
        raise RuntimeError("no se encontró la ventana de melonDS")
    return found[0]


def grab_client(pid: int) -> Image.Image:
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    hwnd = find_window(pid)

    rect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top

    hdc_window = user32.GetDC(hwnd)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_window)
    hbm = gdi32.CreateCompatibleBitmap(hdc_window, w, h)
    gdi32.SelectObject(hdc_mem, hbm)

    user32.PrintWindow(hwnd, hdc_mem, PW_CLIENTONLY)

    bmp_info = ctypes.create_string_buffer(40)
    struct.pack_into("<IiiHHIIIIII", bmp_info, 0, 40, w, -h, 1, 32, 0, w * h * 4, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbm, 0, h, buf, bmp_info, 0)

    gdi32.DeleteObject(hbm)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(hwnd, hdc_window)

    return Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")


def measure_menubar_rows(shot: Image.Image) -> int:
    """Alto de la barra de menú: primera fila oscura del área cliente (al arranque las pantallas son negras)."""
    w, h = shot.size
    pixels = shot.load()
    for y in range(1, h):
        mean = sum(sum(pixels[x, y]) for x in range(0, w, 4)) / (w / 4 * 3)
        if mean < DARK_ROW_MEAN:
            return y
    raise RuntimeError("no se pudo medir la barra de menú: no hay filas osuras en la ventana")


def resize_client(pid: int, client_height: int) -> None:
    """Agranda la ventana para que el área cliente mida 256 x client_height (la barra más las dos pantallas)."""
    user32 = ctypes.windll.user32
    hwnd = find_window(pid)

    outer = ctypes.wintypes.RECT()
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(outer))
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    chrome_x = (outer.right - outer.left) - (rect.right - rect.left)
    chrome_y = (outer.bottom - outer.top) - (rect.bottom - rect.top)
    user32.SetWindowPos(hwnd, 0, 0, 0, SCREEN_WIDTH + chrome_x, client_height + chrome_y, SWP_NOMOVE)
    time.sleep(0.5)


def close_melonds(process: subprocess.Popen) -> None:
    user32 = ctypes.windll.user32
    try:
        hwnd = find_window(process.pid)
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        process.wait(timeout=6)
    except (RuntimeError, subprocess.TimeoutExpired):
        process.terminate()
        process.wait()


def capture(out_path: Path | None = None, boot_seconds: int = BOOT_SECONDS) -> Path:
    out = out_path or OUT
    ctypes.windll.user32.SetProcessDPIAware()
    process = subprocess.Popen([str(MELONDS), str(ROM)])
    try:
        time.sleep(MEASURE_SECONDS)
        menubar_rows = 0
        for _ in range(MAX_MEASURE_TRIES):
            shot = grab_client(process.pid)
            try:
                menubar_rows = measure_menubar_rows(shot)
            except RuntimeError:
                time.sleep(1)
                continue
            break
        if not menubar_rows:
            raise RuntimeError("no se pudo medir la barra de menú de melonDS")
        resize_client(process.pid, menubar_rows + SCREEN_ROWS)
        time.sleep(max(0, boot_seconds - MEASURE_SECONDS))
        shot = grab_client(process.pid)
    finally:
        close_melonds(process)

    w, h = shot.size
    if w != SCREEN_WIDTH or h != menubar_rows + SCREEN_ROWS:
        raise RuntimeError(f"el área cliente mide {w}x{h}, se esperaba {SCREEN_WIDTH}x{menubar_rows + SCREEN_ROWS}")
    screens = shot.crop((0, h - SCREEN_ROWS, SCREEN_WIDTH, h))
    out.parent.mkdir(parents=True, exist_ok=True)
    screens.save(out)
    return out


def main() -> int:
    print(capture())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
