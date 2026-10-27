from tools.ctl.autotest import autotest_bin, scenario_steps
from tools.ctl.scenario import load_scenario


def test_pc_adapter_uses_ps1_autotest_format():
    scenario = load_scenario("tests/scenarios/snoot-smoke.yaml")
    steps = scenario_steps(scenario)
    data = autotest_bin(steps)
    assert int.from_bytes(data[:2], "little") == len(steps)
    assert data[2:6] == bytes((60, 0, 0, 0))
