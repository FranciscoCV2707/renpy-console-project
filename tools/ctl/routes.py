"""Genera los escenarios de las 14 rutas de Snoot (T-304).

Lee ``rutas.json`` del port-kit (solo lectura) y escribe
``tests/scenarios/snoot-route-<ruta>.yaml`` (espacios -> ``-``) con la entrada
del menu de desarrollo para los capitulos extra y ``choices`` con los indices de
las decisiones de la ruta en orden.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUTAS_JSON = Path(r"E:\Dev\renpy-port-kit\juegos\snoot\reporte\rutas.json")
SCENARIOS_DIR = ROOT / "tests" / "scenarios"
REFERENCE_DIR = "tests/reference/traces/snoot"

DEV_COUNT = 30  # filas del menu de desarrollo antes de los capitulos extra (engine/app/main.c)


def _say_count(reference_path: Path) -> int:
    n = 0
    if reference_path.exists():
        for line in reference_path.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split("|")
            if len(parts) >= 4 and parts[3] == "SAY":
                n += 1
    return n


def _dev_menu_inputs(row: int) -> list[dict]:
    """Camino del menu de desarrollo (DEV + dev_row) expresado como inputs del Test Lab."""
    inputs: list[dict] = []
    cursor = 0

    def wait_to(target: int) -> None:
        nonlocal cursor
        inputs.append({"wait": target - cursor})
        cursor = target

    # DEV: L1 + R1 + SELECT en el titulo (frame 60), captura en 120.
    wait_to(60)
    inputs.append({"press": "L1"})
    cursor += 30
    wait_to(60)
    inputs.append({"press": "R1"})
    cursor += 30
    wait_to(60)
    inputs.append({"press": "SELECT"})
    cursor += 30
    wait_to(120)
    inputs.append({"shot": "dev"})
    # dev_row(row, start=130)
    row_start = 130
    for i in range(row):
        wait_to(row_start + 10 * i)
        inputs.append({"press": "DOWN"})
        cursor += 30
    cross_frame = row_start + 10 * row + 20
    wait_to(cross_frame)
    inputs.append({"press": "CROSS"})
    cursor += 30
    autoplay_frame = row_start + 10 * row + 80
    wait_to(autoplay_frame)
    inputs.append({"autoplay": True})
    return inputs


def build_scenario(name: str, data: dict) -> str:
    entry = data["entry"]
    decisions = data.get("decisions", [])
    # Solo las decisiones de menu presentan opciones al jugador; las python_menu
    # son saltos condicionales del juego (no requieren CHOICE en la VM).
    indices = [d["index"] for d in decisions if d.get("kind") == "menu"]

    reference = f"{REFERENCE_DIR}/{name}.trace"
    reference_path = ROOT / reference
    say_count = _say_count(reference_path)
    max_seconds = max(300, say_count * 2)

    if entry == "start":
        inputs = [{"wait": 60}, {"press": "CROSS"}, {"autoplay": True}]
    else:
        # chapter_xN -> fila del menu de desarrollo = DEV_COUNT + N
        n = int(entry.removeprefix("chapter_x"))
        row = DEV_COUNT + n
        inputs = _dev_menu_inputs(row)
    if indices:
        inputs.append({"choices": indices})

    lines: list[str] = []
    lines.append(f"id: snoot-route-{name.replace(' ', '-')}")
    lines.append(f"reference: {reference}")
    lines.append("inputs:")
    for item in inputs:
        key, value = next(iter(item.items()))
        if isinstance(value, bool):
            lines.append(f"  - {key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            lines.append(f"  - {key}: {value}")
        elif isinstance(value, str):
            lines.append(f"  - {key}: {value}")
        else:
            lines.append(f"  - {key}: {value}")
    lines.append("expect: []")
    lines.append("compare:")
    lines.append("  mode: renpy")
    lines.append("  events: [SAY, CHOICE]")
    lines.append("limits:")
    lines.append(f"  max_seconds: {max_seconds}")
    return "\n".join(lines) + "\n"


def main() -> int:
    data = json.loads(RUTAS_JSON.read_text(encoding="utf-8"))
    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
    for name, info in data.items():
        slug = name.replace(" ", "-")
        path = SCENARIOS_DIR / f"snoot-route-{slug}.yaml"
        path.write_text(build_scenario(name, info), encoding="utf-8", newline="\n")
        print(f"written {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
