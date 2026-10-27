"""Arranca ``build/ds/snoot.nds`` en melonDS 1.1 y guarda una captura de las dos pantallas.

Las opciones de línea de comandos de melonDS 1.1 (``melonDS.exe --help``) no incluyen captura de
pantalla, así que se trae la ventana al frente, se captura con ``PIL.ImageGrab`` y se recortan las
dos pantallas: la de abajo se localiza por su color de fondo y la de arriba va justo encima (el
layout por defecto de melonDS es vertical sin hueco, a escala 1:1). La salida es
``build/ds/snoot-screens.png``, con la pantalla de arriba (256x192) sobre la de abajo (256x192).
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageGrab

ROOT = Path(__file__).resolve().parents[2]
MELONDS = Path("E:/snoot/melonds-1.1/melonDS.exe")
ROM = ROOT / "build" / "ds" / "snoot.nds"
OUT = ROOT / "build" / "ds" / "snoot-screens.png"
BOOT_SECONDS = 10
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 192
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
# Fondo de la pantalla inferior en main.c: ARGB16(1, 4, 6, 12) convertido a 8 bits por canal.
BOTTOM_COLOR = (33, 49, 99)
COLOR_TOLERANCE = 6


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


def screen_rects(shot: Image.Image) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    width, height = shot.size
    pixels = shot.load()
    row_hits = [0] * height
    for y in range(height):
        for x in range(width):
            color = pixels[x, y]
            if all(abs(color[channel] - BOTTOM_COLOR[channel]) <= COLOR_TOLERANCE for channel in range(3)):
                row_hits[y] += 1
    rows = [y for y in range(height) if row_hits[y] * 4 >= SCREEN_WIDTH * 3]
    if not rows:
        raise RuntimeError("no se encontró la pantalla inferior en la captura")
    col_hits = [0] * width
    for y in range(rows[0], rows[-1] + 1):
        for x in range(width):
            color = pixels[x, y]
            if all(abs(color[channel] - BOTTOM_COLOR[channel]) <= COLOR_TOLERANCE for channel in range(3)):
                col_hits[x] += 1
    columns = [x for x in range(width) if col_hits[x] * 4 >= (rows[-1] - rows[0] + 1) * 3]
    if not columns:
        raise RuntimeError("no se encontró la pantalla inferior en la captura")
    bottom = (columns[0], rows[0], columns[-1] + 1, rows[-1] + 1)
    if (bottom[2] - bottom[0], bottom[3] - bottom[1]) != (SCREEN_WIDTH, SCREEN_HEIGHT):
        raise RuntimeError("la pantalla inferior de la captura no mide 256x192")
    top = (columns[0], rows[0] - SCREEN_HEIGHT, columns[-1] + 1, rows[0])
    return top, bottom


def capture() -> Path:
    ctypes.windll.user32.SetProcessDPIAware()
    process = subprocess.Popen([str(MELONDS), str(ROM)])
    try:
        time.sleep(BOOT_SECONDS)
        user32 = ctypes.windll.user32
        hwnd = find_window(process.pid)
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        user32.SetWindowPos(hwnd, ctypes.c_void_p(-1), 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
        time.sleep(1)
        shot = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
        user32.SetWindowPos(hwnd, ctypes.c_void_p(-2), 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
    finally:
        process.terminate()
        process.wait()
    top_rect, bottom_rect = screen_rects(shot)
    screens = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT * 2))
    screens.paste(shot.crop(top_rect), (0, 0))
    screens.paste(shot.crop(bottom_rect), (0, SCREEN_HEIGHT))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    screens.save(OUT)
    return OUT


def main() -> int:
    print(capture())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
