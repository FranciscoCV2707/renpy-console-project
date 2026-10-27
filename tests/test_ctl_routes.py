"""Pruebas de tools/ctl/routes.py (T-304), sin emulador."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.autotest import scenario_steps
from tools.ctl.routes import main as routes_main
from tools.ctl.scenario import load_scenario


def test_routes_generate_and_load():
    assert routes_main() == 0
    scen_dir = ROOT / "tests" / "scenarios"
    generated = sorted(scen_dir.glob("snoot-route-*.yaml"))
    assert len(generated) == 14
    for path in generated:
        scen = load_scenario(path)
        steps = scenario_steps(scen)
        assert isinstance(steps, list)


def test_route_with_decisions_choices_in_order():
    scen = load_scenario(ROOT / "tests" / "scenarios" / "snoot-route-ruta-1.yaml")
    steps = scenario_steps(scen)
    choice_values = [int(arg) for _, action, arg in steps if action == "choice"]
    data = json.loads((Path(r"E:\Dev\renpy-port-kit\juegos\snoot\reporte\rutas.json")).read_text(encoding="utf-8"))
    expected = [d["index"] for d in data["ruta 1"]["decisions"] if d.get("kind") == "menu"]
    assert choice_values == expected
