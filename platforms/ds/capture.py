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

from PIL import Image

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


def grab_window(hwnd: int) -> Image.Image:
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    rect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top

    hdc_window = user32.GetDC(hwnd)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_window)
    hbm = gdi32.CreateCompatibleBitmap(hdc_window, w, h)
    gdi32.SelectObject(hdc_mem, hbm)

    pw_clientonly = 2
    user32.PrintWindow(hwnd, hdc_mem, pw_clientonly)

    bmp_info = ctypes.create_string_buffer(40)
    import struct
    struct.pack_into("<IiiHHIIIIII", bmp_info, 0, 40, w, -h, 1, 32, 0, w * h * 4, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbm, 0, h, buf, bmp_info, 0)

    gdi32.DeleteObject(hbm)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(hwnd, hdc_window)

    im = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)
    return im.convert("RGB")


def capture(out_path: Path | None = None, boot_seconds: int = BOOT_SECONDS) -> Path:
    out = out_path or OUT
    ctypes.windll.user32.SetProcessDPIAware()
    process = subprocess.Popen([str(MELONDS), str(ROM)])
    try:
        time.sleep(boot_seconds)
        hwnd = find_window(process.pid)
        shot = grab_window(hwnd)
    finally:
        user32 = ctypes.windll.user32
        WM_CLOSE = 0x0010
        try:
            hwnd = find_window(process.pid)
            if hwnd:
                user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            process.wait(timeout=5)
        except (RuntimeError, subprocess.TimeoutExpired):
            process.terminate()
            process.wait()

    w, h = shot.size
    if w == SCREEN_WIDTH and h == SCREEN_HEIGHT * 2 + 22:
        top_crop = shot.crop((0, 22, SCREEN_WIDTH, SCREEN_HEIGHT + 22))
        bot_crop = shot.crop((0, SCREEN_HEIGHT + 22, SCREEN_WIDTH, h))
    elif w == SCREEN_WIDTH and h == SCREEN_HEIGHT * 2:
        top_crop = shot.crop((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        bot_crop = shot.crop((0, SCREEN_HEIGHT, SCREEN_WIDTH, h))
    else:
        top_rect, bottom_rect = screen_rects(shot)
        top_crop = shot.crop(top_rect)
        bot_crop = shot.crop(bottom_rect)

    screens = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT * 2))
    screens.paste(top_crop, (0, 0))
    screens.paste(bot_crop, (0, SCREEN_HEIGHT))
    out.parent.mkdir(parents=True, exist_ok=True)
    screens.save(out)
    return out


def main() -> int:
    print(capture())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
