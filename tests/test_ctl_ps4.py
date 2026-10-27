"""Pruebas del adapter PS4/shadPS4 (T-614), sin emulador."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.ps4 import extract_trace, stage_user_dir
from tools.ctl.__main__ import main


def test_stage_user_dir(tmp_path):
    stage_user_dir(tmp_path)
    for sub in ("savedata", "trophy", "inputs"):
        assert (tmp_path / "home" / "1000" / sub).is_dir()


def test_extract_trace_from_shadps4_log():
    log = (
        "[Loader] <Info> (shadPS4:Main) emulator.cpp:300 Run: Starting shadps4 emulator v0.20.0\n"
        "[Tty] <Info> (Game:Main) logger.cpp:55 log_flush: [stdout] T|1|0|SAY|who=1\n"
        "[Tty] <Info> (Game:Main) logger.cpp:55 log_flush: [stdout] sin traza\n"
        "[Tty] <Info> (Game:Main) logger.cpp:55 log_flush: [stdout] T|2|1|CHOICE|i=2\n"
    )
    assert extract_trace(log) == "T|1|0|SAY|who=1\nT|2|1|CHOICE|i=2\n"


def test_extract_trace_accepts_stdin_tag():
    # shadPS4 0.20.0 etiqueta el stdout del juego como [stdin]
    log = "[Tty] <Info> (Game:Main) logger.cpp:62 log_flush: [stdin] T|0|623|SCENE|img=1\n"
    assert extract_trace(log) == "T|0|623|SCENE|img=1\n"


def test_extract_trace_ignores_log_without_trace():
    assert extract_trace("x\ny\n") == ""
    assert extract_trace("[Tty] <Info> (Game:Main) logger.cpp:55 log_flush: [stdout] hola\n") == ""


def test_run_exit_code_success(monkeypatch, tmp_path):
    trace = tmp_path / "trace.txt"
    trace.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")

    def fake_run_scenario(_scenario, _out_dir):
        return trace

    monkeypatch.setattr("tools.ctl.ps4.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(trace) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "ps4", "--scenario", str(scen)]) == 0


def test_run_exit_code_fail(monkeypatch, tmp_path):
    ref = tmp_path / "ref.trace"
    act = tmp_path / "act.trace"
    ref.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")
    act.write_text("T|1|0|SHOW|tag=2\n", encoding="utf-8")

    def fake_run_scenario(_scenario, _out_dir):
        return act

    monkeypatch.setattr("tools.ctl.ps4.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(ref) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY, SHOW]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "ps4", "--scenario", str(scen)]) == 1


def test_run_exit_code_startup(monkeypatch, tmp_path):
    def fake_run_scenario(_scenario, _out_dir):
        raise OSError("no existe shadPS4.exe")

    monkeypatch.setattr("tools.ctl.ps4.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(tmp_path / "no.trace") + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "ps4", "--scenario", str(scen)]) == 2
