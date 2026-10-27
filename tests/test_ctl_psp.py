"""Pruebas del adapter PSP/PPSSPP (T-501), sin emulador."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.psp import extract_trace
from tools.ctl.__main__ import main


def test_extract_trace_from_ppsspp_log():
    log = (
        "12:00:001 user_main    N[BOOT]: UI\\EmuScreen.cpp:391 Booted EBOOT.PBP...\n"
        "12:00:002 user_main    I[PRINTF]: HLE\\sceIo.cpp:1206 stdout: T|1|0|SAY|who=1\n"
        "12:00:002 user_main    I[PRINTF]: HLE\\sceIo.cpp:1206 stdout: \n"
        "12:00:003 user_main    I[PRINTF]: HLE\\sceIo.cpp:1206 stdout: T|2|1|CHOICE|i=2\n"
        "12:00:004 idle0        I[SYSTEM]: UI\\EmuScreen.cpp:1537 SELF-POWERDOWN!\n"
    )
    assert extract_trace(log) == "T|1|0|SAY|who=1\nT|2|1|CHOICE|i=2\n"


def test_extract_trace_ignores_stdout_without_trace():
    assert extract_trace("x\ny\n") == ""
    assert extract_trace("I[PRINTF]: HLE\\sceIo.cpp:1206 stdout: hola\n") == ""


def test_run_exit_code_success(monkeypatch, tmp_path):
    trace = tmp_path / "trace.txt"
    trace.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")

    def fake_run_scenario(scenario, out_dir):
        return trace

    monkeypatch.setattr("tools.ctl.psp.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(trace) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "psp", "--scenario", str(scen)]) == 0


def test_run_exit_code_fail(monkeypatch, tmp_path):
    ref = tmp_path / "ref.trace"
    act = tmp_path / "act.trace"
    ref.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")
    act.write_text("T|1|0|SHOW|tag=2\n", encoding="utf-8")

    def fake_run_scenario(scenario, out_dir):
        return act

    monkeypatch.setattr("tools.ctl.psp.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(ref) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY, SHOW]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "psp", "--scenario", str(scen)]) == 1


def test_run_exit_code_startup(monkeypatch, tmp_path):
    def fake_run_scenario(scenario, out_dir):
        raise OSError("no existe PPSSPPWindows64.exe")

    monkeypatch.setattr("tools.ctl.psp.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(tmp_path / "no.trace") + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "psp", "--scenario", str(scen)]) == 2
