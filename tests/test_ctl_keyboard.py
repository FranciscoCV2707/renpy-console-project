from pathlib import Path

from tools.ctl.autotest import scenario_steps
from tools.ctl.scenario import load_scenario

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "tests" / "scenarios" / "snoot-keyboard.yaml"


def test_keyboard_scenario_reaches_and_drives_the_keyboard():
    steps = scenario_steps(load_scenario(SCENARIO))
    presses = [(frame, button) for frame, action, button in steps if action == "press"]
    # menu de desarrollo: L1+R1+Select en el titulo y fila 29 (capitulo 13D, ruta 4)
    assert (60, "L1") in presses and (60, "R1") in presses and (60, "SELECT") in presses
    assert (410, "DOWN") in presses and (440, "CROSS") in presses
    # teclado: cruceta hasta la h, escribe, i, borra, mayusculas, escribe, Start confirma
    later = [p for p in presses if p[0] >= 1100]
    assert later == [
        (1100, "CIRCLE"), (1130, "CIRCLE"), (1160, "CIRCLE"),
        (1190, "DOWN"), (1220, "DOWN"),
        (1250, "RIGHT"), (1280, "RIGHT"), (1310, "RIGHT"), (1340, "RIGHT"), (1370, "RIGHT"),
        (1400, "CROSS"),
        (1430, "RIGHT"), (1460, "RIGHT"), (1490, "CROSS"),
        (1560, "CIRCLE"), (1590, "L1"), (1620, "CROSS"),
        (1700, "START"),
    ]
    assert [(f, name) for f, a, name in steps if a == "shot"] == [
        (1180, "teclado"), (1530, "teclado_texto"), (1660, "teclado_mayus"), (1780, "anuario")]
    assert steps[-1] == (2100, "quit", "")


def test_keyboard_scenario_reference_trace_exists():
    scen = load_scenario(SCENARIO)
    assert (ROOT / scen.reference).is_file()
