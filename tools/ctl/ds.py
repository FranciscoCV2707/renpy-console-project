"""Adapter Nintendo DS/melonDS del Console Test Lab (T-708).

melonDS 1.1 implementa la intercepción del puerto de depuración NO$GBA (0x04FFFA1C) únicamente en la CPU
ARM7 (MMU_ARM7.cpp: writes a 0x04FFFA1C). La CPU ARM9, donde corre el juego homebrew, no implementa
dicha intercepción (MMU_ARM9.cpp carece de control para 0x04FFFA1C) y lanzar escrituras allí provoca
excepciones Data Abort en el ARM9 (melonDS GitHub Issue #2374: "Not seeing stderr with libnds consoleDebugInit()").
Por lo tanto, la extracción de trazas en melonDS 1.1 no está soportada.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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


def run_scenario(scenario, out: Path) -> Path:
    """Corre el escenario en melonDS y devuelve la ruta de la traza (out/trace.txt).

    Lanza OSError indicando la limitación exacta de melonDS 1.1 si se invoca.
    """
    out.mkdir(parents=True, exist_ok=True)
    disc = ROOT / "build" / "ctl" / "ps1" / "disc"
    if not disc.is_dir():
        raise FileNotFoundError("faltan los datos del disco PS1; ejecuta primero ctl run --target ps1")

    # Documentar la limitación exacta de melonDS 1.1 para que el arnés ctl lo capture
    raise OSError(
        "melonDS 1.1 no emite trazas de depuracion de ARM9: el puerto NO$GBA 0x04FFFA1C "
        "solo esta implementado en ARM7 (GitHub melonDS #2374)"
    )
