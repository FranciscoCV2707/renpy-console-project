"""Pruebas de tools/ctl/autotest.py (T-204)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.autotest import (
    BUTTONS,
    SHOT,
    QUIT,
    AUTOPLAY,
    scenario_steps,
    autotest_bin,
)
from tools.ctl.scenario import Scenario, ScenarioError, CompareSpec, LimitsSpec, load_scenario


def _scen(inputs):
    return Scenario(
        id="t",
        reference="r",
        inputs=inputs,
        expect=[],
        compare=CompareSpec(events=[]),
        limits=LimitsSpec(max_seconds=10),
    )


def test_wait():
    assert scenario_steps(_scen([{"wait": 5}])) == [(65, "quit", "")]


def test_press():
    assert scenario_steps(_scen([{"press": "CROSS"}])) == [(0, "press", "CROSS"), (90, "quit", "")]


def test_advance():
    assert scenario_steps(_scen([{"advance": 2}])) == [
        (0, "press", "CROSS"),
        (45, "press", "CROSS"),
        (150, "quit", ""),
    ]


def test_choose_zero():
    assert scenario_steps(_scen([{"choose": 0}])) == [(0, "press", "CROSS"), (90, "quit", "")]


def test_choose_two():
    assert scenario_steps(_scen([{"choose": 2}])) == [
        (0, "press", "DOWN"),
        (30, "press", "DOWN"),
        (60, "press", "CROSS"),
        (150, "quit", ""),
    ]


def test_shot():
    assert scenario_steps(_scen([{"shot": "a"}])) == [(0, "shot", "a"), (60, "quit", "")]


def test_autoplay():
    assert scenario_steps(_scen([{"autoplay": True}])) == [(0, "autoplay", ""), (60, "quit", "")]


def test_quit_no_final():
    assert scenario_steps(_scen([{"quit": True}])) == [(0, "quit", "")]


def test_final_quit():
    assert scenario_steps(_scen([{"wait": 10}])) == [(70, "quit", "")]


def test_unknown_input_index():
    with pytest.raises(ScenarioError) as exc:
        scenario_steps(_scen([{"foo": 1}]))
    assert getattr(exc.value, "field", "") == "inputs[0]"
    assert "inputs[0]" in str(exc.value)


def test_bad_button_index():
    with pytest.raises(ScenarioError) as exc:
        scenario_steps(_scen([{"press": "NOPE"}]))
    assert getattr(exc.value, "field", "") == "inputs[0]"


def test_bad_button_second_index():
    with pytest.raises(ScenarioError) as exc:
        scenario_steps(_scen([{"wait": 1}, {"press": "NOPE"}]))
    assert getattr(exc.value, "field", "") == "inputs[1]"


def test_autotest_bin_bytes():
    steps = [(60, "press", "CROSS"), (120, "shot", "a"), (200, "quit", "")]
    assert autotest_bin(steps).hex() == "03003c000000004078000000ffffc8000000feff"


def test_snoot_smoke_compiles():
    scen = load_scenario(ROOT / "tests" / "scenarios" / "snoot-smoke.yaml")
    steps = scenario_steps(scen)
    assert isinstance(steps, list)
    assert len(steps) == 32
    assert steps[-1][1] == "quit"


def test_buttons_constants():
    assert BUTTONS["CROSS"] == (1 << 14)
    assert (SHOT, QUIT, AUTOPLAY) == (0xFFFF, 0xFFFE, 0xFFFD)
