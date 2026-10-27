"""Escenarios de las 14 rutas de Snoot en PS1 (T-304).

    python -m tools.ctl.routes

Por cada ruta de rutas.json del port-kit (solo lectura) escribe tests/scenarios/snoot-route-<ruta>.yaml: juega la ruta
con autoplay y las decisiones que eligió Ren'Py, y se compara con su traza de Ren'Py (compare.mode renpy, PLAN.md D17).
"""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
KIT = Path(r"E:\Dev\renpy-port-kit\juegos\snoot")
ROUTES = KIT / "reporte" / "rutas.json"
# carpeta game/ del juego publicado (trae los .rpy)
GAME = Path(tomllib.loads((KIT / "game.toml").read_text(encoding="utf-8"))["paths"]["game"])
SCENARIOS = ROOT / "tests" / "scenarios"
REFERENCES = "tests/reference/traces/snoot"
# Filas del menú de desarrollo antes de los capítulos extra: chapter_xN es la fila DEV_COUNT + N (engine/app/main.c)
DEV_COUNT = 30
# Mismo camino que DEV y dev_row() de vn-engine-ps1/tests/emu/snoot.py: L1+R1+Select en el título abre el menú
DEV = "60 press L1; 60 press R1; 60 press SELECT; 120 shot dev"
# Segundos por línea que tarda PS1 en autoplay, medidos con chapter_x2 y x3, con margen ×2
SECONDS_PER_LINE = 2


def python_menu_index(decision: dict) -> int:
    """Un "python_menu" es un menú armado en Python: `choices = [(_('Texto'), 'etiqueta'), ...]` y
    `renpy.display_menu(randomize_choices(choices))`. La VM guarda las opciones en el orden de esa lista (el motor solo
    las baraja al mostrarlas), así que el índice es la posición de la etiqueta elegida en la lista del guion."""
    path, line = decision["where"].rsplit(":", 1)
    lines = (GAME.parent / path).read_text(encoding="utf-8").splitlines()
    shown = next(i for i in range(int(line) - 1, len(lines)) if "display_menu" in lines[i])
    # La lista puede armarse antes y reutilizarse en varios menús seguidos: vale la última definida antes del menú
    top = max(i for i in range(shown) if "choices = [" in lines[i])
    block = "\n".join(lines[top:shown]).split("]", 1)[0]
    return re.findall(r",\s*'(\w+)'\s*\)", block).index(decision["value"])


def dev_row(row: int) -> str:
    downs = [f"{130 + 10 * i} press DOWN" for i in range(row)]
    return "; ".join([DEV, *downs, f"{130 + 10 * row + 20} press CROSS", f"{130 + 10 * row + 80} autoplay"])


def scenario(name: str, route: dict) -> dict:
    reference = f"{REFERENCES}/{name}.trace"
    lines = sum(1 for line in (ROOT / reference).read_text(encoding="utf-8").splitlines() if "|SAY|" in line)
    if route["entry"] == "start":
        inputs = [{"wait": 60}, {"press": "CROSS"}, {"autoplay": True}]
    else:
        inputs = [{"steps": dev_row(DEV_COUNT + int(route["entry"].removeprefix("chapter_x")))}]
    choices = [d["index"] if d["kind"] == "menu" else python_menu_index(d) for d in route["decisions"]]
    if choices:
        inputs.append({"choices": choices})
    return {"id": f"snoot-route-{name.replace(' ', '-')}", "reference": reference, "inputs": inputs, "expect": [],
            "compare": {"mode": "renpy", "events": ["SAY"]},
            "limits": {"max_seconds": max(300, lines * SECONDS_PER_LINE)}}


def main() -> int:
    for name, route in json.loads(ROUTES.read_text(encoding="utf-8")).items():
        path = SCENARIOS / f"snoot-route-{name.replace(' ', '-')}.yaml"
        path.write_text(yaml.safe_dump(scenario(name, route), sort_keys=False, allow_unicode=True), encoding="utf-8",
                        newline="\n")
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
