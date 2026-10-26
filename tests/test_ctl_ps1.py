"""Pruebas del adapter PS1 (T-203), sin emulador."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.ps1 import extract_trace
from tools.ctl.__main__ import main


def test_extract_trace_mixed():
    tty = "booting\nT|1|0|SAY|who=1\nnoise\nT|2|1|CHOICE|i=2\n"
    assert extract_trace(tty) == "T|1|0|SAY|who=1\nT|2|1|CHOICE|i=2\n"


def test_extract_trace_empty():
    assert extract_trace("no trace here\n") == ""


def test_run_exit_code_success(monkeypatch, tmp_path):
    trace = tmp_path / "trace.txt"
    trace.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")

    def fake_run_scenario(scenario, out_dir):
        return trace

    monkeypatch.setattr("tools.ctl.ps1.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(trace) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "ps1", "--scenario", str(scen)]) == 0


def test_run_exit_code_fail(monkeypatch, tmp_path):
    ref = tmp_path / "ref.trace"
    act = tmp_path / "act.trace"
    ref.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")
    act.write_text("T|1|0|SHOW|tag=2\n", encoding="utf-8")

    def fake_run_scenario(scenario, out_dir):
        return act

    monkeypatch.setattr("tools.ctl.ps1.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(ref) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY, SHOW]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "ps1", "--scenario", str(scen)]) == 1


def test_run_exit_code_startup(monkeypatch, tmp_path):
    def fake_run_scenario(scenario, out_dir):
        raise OSError("no existe pcsx-redux.exe")

    monkeypatch.setattr("tools.ctl.ps1.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(tmp_path / "no.trace") + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "ps1", "--scenario", str(scen)]) == 2
