"""Arranca ``build/gba/snoot.gba`` en mGBA (Qt) y guarda capturas 240x160 del título y del diálogo.

La ventana SDL de mGBA dibuja la pantalla con un desplazamiento fijo que recorta las últimas filas,
así que la captura usa ``mGBA.exe`` (frontend Qt): con el área cliente a 960x740 la pantalla de GBA
se dibuja a escala 4x en (8, 92) con bandas negras alrededor (geometría medida con un ROM de patrón
de prueba: cada pixel codifica su x e y, verificado píxel a píxel; el borde derecho del cliente
recorta las 2 últimas columnas de la pantalla y se rellenan de negro). El AUTOTEST del diálogo
sigue el recorrido del escenario ``snoot-route-chapter_x2`` sin autoplay y añade pulsaciones de
CROSS cada 45 cuadros desde el 800, como en T-711: el juego queda esperando en el SAY 13
(``who=3;text=13290``, fondo ``img=293``) para capturarlo con calma.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import struct
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from platforms.gba.build import build  # noqa: E402
from tools.ctl.autotest import autotest_bin  # noqa: E402

MGBA = Path("E:/snoot/mgba-0.10.5/mGBA-0.10.5-win64/mGBA.exe")
SCREEN_W, SCREEN_H = 240, 160
CLIENT_W, CLIENT_H = 960, 740          # área cliente de la ventana de mGBA
IMAGE_LEFT, IMAGE_TOP, IMAGE_SCALE = 8, 92, 4  # pantalla de GBA dibujada a 4x en el cliente
PW_CLIENTONLY = 2
WM_CLOSE = 0x0010
SETTLE_SECONDS = 2.0                   # margen tras el momento: fundido de la caja y texto
BOOT_NEEDLE = "GBFS ARCHIVE FOUND"     # el archivo GBFS del ROM está montado
DIALOG_NEEDLE = "SAY|who=3;text=13290"  # SAY 13 de chapter_x2 (fondo img=293), como en T-711
MAX_WAIT_SECONDS = 120.0


def dialog_autotest() -> bytes:
    """Pasos del escenario chapter_x2 sin autoplay: 24 CROSS desde el 800 dejan el juego en el SAY 13."""
    steps = [(60, "press", "L1"), (60, "press", "R1"), (60, "press", "SELECT")]
    steps += [(130 + 10 * i, "press", "DOWN") for i in range(32)]
    steps.append((470, "press", "CROSS"))
    steps += [(800 + 45 * i, "press", "CROSS") for i in range(24)]
    return autotest_bin(steps)


def find_window(pid: int) -> int:
    """Localiza el HWND visible de mGBA (título "mGBA - ...") del proceso indicado."""
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
            if title.value.startswith("mGBA"):
                found.append(int(hwnd))
        return True

    user32.EnumWindows(callback, 0)
    if not found:
        raise RuntimeError("no se encontró la ventana de mGBA")
    return found[0]


def grab_client(pid: int) -> Image.Image:
    """Captura el área cliente de la ventana de mGBA con PrintWindow (PW_CLIENTONLY)."""
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    hwnd = find_window(pid)

    rect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    if w < CLIENT_W or h < CLIENT_H:
        raise RuntimeError(f"el área cliente mide {w}x{h}, se esperaba al menos {CLIENT_W}x{CLIENT_H}")

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


def resize_client(pid: int) -> None:
    """Ajusta la ventana para que el área cliente mida CLIENT_W x CLIENT_H."""
    user32 = ctypes.windll.user32
    SWP_NOMOVE = 0x0004
    hwnd = find_window(pid)

    outer = ctypes.wintypes.RECT()
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(outer))
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    chrome_x = (outer.right - outer.left) - (rect.right - rect.left)
    chrome_y = (outer.bottom - outer.top) - (rect.bottom - rect.top)
    user32.SetWindowPos(hwnd, 0, 0, 0, CLIENT_W + chrome_x, CLIENT_H + chrome_y, SWP_NOMOVE)


def close_mgba(process: subprocess.Popen) -> None:
    user32 = ctypes.windll.user32
    try:
        hwnd = find_window(process.pid)
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    except RuntimeError:
        pass
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait()


def screen_from_client(shot: Image.Image) -> Image.Image:
    """Recorta la pantalla de GBA (4x, en IMAGE_LEFT/IMAGE_TOP) y la reduce a 240x160.

    El borde derecho del cliente recorta las últimas columnas de la pantalla; se rellenan de negro
    para conservar los 240x160. Antes de recortar se comprueba la geometría medida: las bandas
    negras sobre y bajo la pantalla (letterbox del visor de mGBA) deben ser negras de verdad y el
    área de menús clara; si no, la captura no es de la ventana esperada.
    """
    px = shot.load()
    toolbar = px[CLIENT_W // 2, 20]
    letter_top = px[CLIENT_W // 2, IMAGE_TOP - 8]
    letter_bottom = px[CLIENT_W // 2, IMAGE_TOP + SCREEN_H * IMAGE_SCALE + 4]
    if sum(toolbar) < 300:
        raise RuntimeError("la barra de menús de mGBA no está donde se esperaba (geometría de ventana cambiada)")
    if sum(letter_top) > 60 or sum(letter_bottom) > 60:
        raise RuntimeError("las bandas negras del visor de mGBA no son negras (geometría de ventana cambiada)")

    crop_w = min(CLIENT_W - IMAGE_LEFT, SCREEN_W * IMAGE_SCALE)
    screen4x = Image.new("RGB", (SCREEN_W * IMAGE_SCALE, SCREEN_H * IMAGE_SCALE))
    screen4x.paste(shot.crop((IMAGE_LEFT, IMAGE_TOP, IMAGE_LEFT + crop_w, IMAGE_TOP + SCREEN_H * IMAGE_SCALE)), (0, 0))
    return screen4x.resize((SCREEN_W, SCREEN_H), Image.BOX)


def wait_for_moment(log: Path, needle: str) -> None:
    """Espera a que el log de mGBA contenga el momento buscado (la traza del motor)."""
    deadline = time.monotonic() + MAX_WAIT_SECONDS
    while time.monotonic() < deadline:
        time.sleep(0.2)
        if log.exists():
            try:
                if needle in log.read_text(encoding="utf-8", errors="replace"):
                    return
            except OSError:
                continue
    raise RuntimeError(f"el juego no alcanzó «{needle}» en {MAX_WAIT_SECONDS} s")


def capture(out: Path, autotest: bytes | None, needle: str) -> Path:
    """Compila la ROM, la corre en mGBA, espera el momento ``needle`` y guarda la pantalla 240x160.

    Sin ``-C audioSync=0`` mGBA (Qt) avanza a menos de 5 fps esperando el audio del juego, así que
    se usan las mismas opciones de sincronía que el adapter SDL; el log permite esperar el momento
    exacto en vez de un tiempo fijo.
    """
    if not MGBA.is_file():
        raise FileNotFoundError(f"no se encontró el emulador mGBA en {MGBA}")

    work = Path("build") / "gba" / "capture"
    work.mkdir(parents=True, exist_ok=True)
    autotest_path = None
    if autotest is not None:
        autotest_path = work / "AUTOTEST.BIN"
        autotest_path.write_bytes(autotest)
    rom = build(trace=True, autotest_path=autotest_path)

    log = work / f"{out.stem}_log.txt"
    log.unlink(missing_ok=True)
    cmd = [
        str(MGBA), "-C", "fastForward=1", "-C", "audioSync=0", "-C", "videoSync=0",
        "-C", "fpsTarget=0", "-C", "logToFile=1", "-C", f"logFile={log.as_posix()}",
        "-l", "15", str(rom),
    ]

    ctypes.windll.user32.SetProcessDPIAware()
    process = subprocess.Popen(cmd)
    try:
        for _ in range(30):
            time.sleep(0.5)
            try:
                resize_client(process.pid)
                break
            except RuntimeError:
                continue
        time.sleep(1.0)
        resize_client(process.pid)
        wait_for_moment(log, needle)
        time.sleep(SETTLE_SECONDS)
        screen = screen_from_client(grab_client(process.pid))
    finally:
        close_mgba(process)

    out.parent.mkdir(parents=True, exist_ok=True)
    screen.save(out)
    return out


def main() -> int:
    dialog = capture(Path("build") / "gba" / "snoot-dialog.png", dialog_autotest(), DIALOG_NEEDLE)
    print(dialog)
    title = capture(Path("build") / "gba" / "snoot-title.png", None, BOOT_NEEDLE)
    print(title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
