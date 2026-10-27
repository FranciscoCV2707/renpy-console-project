"""tools/ctl/routes.py sin emulador: los escenarios de las rutas cargan, compilan y siguen las decisiones."""
import json
from pathlib import Path

import yaml

from tools.ctl.autotest import scenario_steps
from tools.ctl.routes import ROUTES, scenario
from tools.ctl.scenario import Scenario, load_scenario

ROOT = Path(__file__).resolve().parent.parent


def test_committed_route_scenarios_load_and_compile():
    paths = sorted((ROOT / "tests" / "scenarios").glob("snoot-route-*.yaml"))
    assert len(paths) == 14
    for path in paths:
        assert scenario_steps(load_scenario(path))


def test_route_choices_follow_the_ren_py_decisions_in_order():
    route = json.loads(ROUTES.read_text(encoding="utf-8"))["ruta 1"]
    steps = scenario_steps(Scenario.from_dict(yaml.safe_load(yaml.safe_dump(scenario("ruta 1", route)))))
    assert [int(arg) for _, action, arg in steps if action == "choice"] == \
        [d["index"] for d in route["decisions"] if d["kind"] == "menu"]
