"""Pruebas del esqueleto del Console Test Lab (T-202)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.trace import parse_line, parse_trace, TraceParseError, compare_scenario
from tools.ctl.scenario import load_scenario, ScenarioError
from tools.ctl.__main__ import main


def test_parse_line_ok():
    ev = parse_line("T|17|1042|SAY|who=3;text=3121")
    assert ev is not None
    assert ev.seq == 17
    assert ev.frame == 1042
    assert ev.ev == "SAY"
    assert ev.fields == {"who": "3", "text": "3121"}


def test_parse_line_ignored():
    assert parse_line("not a trace line") is None
    assert parse_line("") is None


def test_parse_line_no_fields():
    ev = parse_line("T|1|0|END")
    assert ev is not None
    assert ev.ev == "END"
    assert ev.fields == {}


def test_parse_line_malformed_raises():
    with pytest.raises(TraceParseError):
        parse_line("T|bad|0|EV")
    with pytest.raises(TraceParseError):
        parse_line("T|1|0")
    with pytest.raises(TraceParseError):
        parse_line("T|1|0|EV|badfield")


def test_parse_trace_line_number():
    text = "T|1|0|SAY|who=1\nT|bad|0|EV\n"
    with pytest.raises(TraceParseError) as exc:
        parse_trace(text)
    assert exc.value.line_no == 2


def test_load_snoot_smoke():
    scen = load_scenario(ROOT / "tests" / "scenarios" / "snoot-smoke.yaml")
    assert scen.id == "snoot-smoke"
    assert scen.reference == "tests/reference/traces/snoot/ruta-a.trace"
    assert isinstance(scen.inputs, list) and len(scen.inputs) == 3
    assert scen.compare.events == ["LABEL", "SAY", "SHOW", "HIDE", "SCENE", "PLAY", "STOP", "MENU", "CHOICE"]
    assert scen.limits.max_seconds == 300


def test_invalid_scenario():
    bad = ROOT / "tests" / "scenarios" / "_invalid.yaml"
    bad.write_text("id: ''\n", encoding="utf-8")
    try:
        with pytest.raises(ScenarioError):
            load_scenario(bad)
    finally:
        bad.unlink(missing_ok=True)


def test_compare_equal(tmp_path):
    t1 = tmp_path / "a.trace"
    t2 = tmp_path / "b.trace"
    content = "T|1|0|SAY|who=1\nT|2|1|CHOICE|i=2\n"
    t1.write_text(content, encoding="utf-8")
    t2.write_text(content, encoding="utf-8")
    scen_file = tmp_path / "s.yaml"
    scen_file.write_text(
        f"id: t\nreference: {t1}\ninputs: []\nexpect: []\n"
        f"compare:\n  events: [SAY, CHOICE]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    scen = load_scenario(scen_file)
    result = compare_scenario(scen, t2)
    assert result.equal is True
    assert result.verdict == "PASS"


def test_compare_different(tmp_path):
    t1 = tmp_path / "a.trace"
    t2 = tmp_path / "b.trace"
    t1.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")
    t2.write_text("T|1|0|SHOW|tag=2\n", encoding="utf-8")
    scen_file = tmp_path / "s.yaml"
    scen_file.write_text(
        f"id: t\nreference: {t1}\ninputs: []\nexpect: []\n"
        f"compare:\n  events: [SAY, SHOW]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    scen = load_scenario(scen_file)
    result = compare_scenario(scen, t2)
    assert result.equal is False
    assert result.verdict == "FAIL"
    assert result.actual is not None


def test_compare_different_length(tmp_path):
    t1 = tmp_path / "a.trace"
    t2 = tmp_path / "b.trace"
    t1.write_text("T|1|0|SAY|who=1\nT|2|1|CHOICE|i=2\n", encoding="utf-8")
    t2.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")
    scen_file = tmp_path / "s.yaml"
    scen_file.write_text(
        f"id: t\nreference: {t1}\ninputs: []\nexpect: []\n"
        f"compare:\n  events: [SAY, CHOICE]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    scen = load_scenario(scen_file)
    result = compare_scenario(scen, t2)
    assert result.equal is False
    assert result.verdict == "FAIL"


def test_tolerance_frames(tmp_path):
    t1 = tmp_path / "a.trace"
    t2 = tmp_path / "b.trace"
    t1.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")
    t2.write_text("T|1|5|SAY|who=1\n", encoding="utf-8")
    scen_file = tmp_path / "s.yaml"
    scen_file.write_text(
        f"id: t\nreference: {t1}\ninputs: []\nexpect: []\n"
        f"compare:\n  events: [SAY]\n  tolerance: {{frames: 10}}\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    scen = load_scenario(scen_file)
    result = compare_scenario(scen, t2)
    assert result.equal is True
    assert result.verdict == "PASS"


def test_main_fail_exit_code(tmp_path, capsys):
    t1 = tmp_path / "a.trace"
    t2 = tmp_path / "b.trace"
    t1.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")
    t2.write_text("T|1|0|SHOW|tag=2\n", encoding="utf-8")
    scen_file = tmp_path / "s.yaml"
    scen_file.write_text(
        f"id: t\nreference: {t1}\ninputs: []\nexpect: []\n"
        f"compare:\n  events: [SAY, SHOW]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    rc = main(["compare", "--target", "ps1", "--scenario", str(scen_file), "--trace", str(t2)])
    assert rc == 1


def test_main_missing_file_exit_code(tmp_path, capsys):
    scen_file = tmp_path / "s.yaml"
    scen_file.write_text(
        "id: t\nreference: /no/such.trace\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    rc = main(["compare", "--target", "ps1", "--scenario", str(scen_file), "--trace", str(tmp_path / "no.trace")])
    assert rc == 2


def test_main_build_exit_code():
    rc = main(["build", "--target", "ps1"])
    assert rc == 2


def test_main_run_exit_code():
    rc = main(["run", "--target", "ps1"])
    assert rc == 2
