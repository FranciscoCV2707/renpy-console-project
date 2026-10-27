"""Pruebas del adapter Game Boy Advance/mGBA (T-710), sin emulador."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.__main__ import main
from tools.ctl.gba import extract_trace


def test_extract_trace_from_log():
    log = (
        "GBA Debug: GBA: VIDEO_INIT\n"
        "GBA Debug: T|0|623|SCENE|img=1\n"
        "GBA DMA: Starting DMA 3\n"
        "GBA Debug: T|6|685|SAY|who=2;text=13278\n"
        "GBA Debug: AUTOTEST_DONE\n"
    )
    expected = "T|0|623|SCENE|img=1\nT|6|685|SAY|who=2;text=13278\n"
    assert extract_trace(log) == expected


def test_extract_trace_ignores_lines_without_trace():
    log = "GBA Debug: GBA: VIDEO_INIT\nGBA DMA: Starting DMA 3\n"
    assert extract_trace(log) == ""


def test_run_exit_code_success(monkeypatch, tmp_path):
    trace = tmp_path / "trace.txt"
    trace.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")

    def fake_run_scenario(_scenario, _out_dir):
        return trace

    monkeypatch.setattr("tools.ctl.gba.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(trace) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "gba", "--scenario", str(scen)]) == 0


def test_run_exit_code_fail(monkeypatch, tmp_path):
    ref = tmp_path / "ref.trace"
    act = tmp_path / "act.trace"
    ref.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")
    act.write_text("T|1|0|SHOW|tag=2\n", encoding="utf-8")

    def fake_run_scenario(_scenario, _out_dir):
        return act

    monkeypatch.setattr("tools.ctl.gba.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(ref) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "gba", "--scenario", str(scen)]) == 1
