"""Pruebas del adapter PS Vita / Vita3K (T-608), sin emulador."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.__main__ import main
from tools.ctl.vita import extract_trace, stage_config


def test_extract_trace_from_vita3k_log():
    log = (
        "[00:00:01.000] |I| [sdl_frontend::run]: Booting game 'SNOOT001'\n"
        "[00:00:02.000] |T| [write_file]: *** TTY: T|1|0|SAY|who=1\n"
        "[00:00:02.100] |T| [write_file]: *** TTY: algo sin traza\n"
        "[00:00:03.000] |T| [write_file]: *** TTY: T|2|1|CHOICE|i=2\n"
        "[00:00:04.000] |I| [main]: Game finished\n"
    )
    assert extract_trace(log) == "T|1|0|SAY|who=1\nT|2|1|CHOICE|i=2\n"


def test_extract_trace_direct_stdout():
    log = "T|1|0|SAY|who=1\notra linea\nT|2|1|SHOW|tag=2\n"
    assert extract_trace(log) == "T|1|0|SAY|who=1\nT|2|1|SHOW|tag=2\n"


def test_extract_trace_multiline_chunk():
    log = (
        "[00:00:02.000] |T| [write_file]: *** TTY: T|1|0|SAY|who\n"
        "[00:00:02.001] |T| [write_file]: *** TTY: =1\n"
        "[00:00:03.000] |T| [write_file]: *** TTY: T|2|1|CHOICE|i=2\n"
    )
    assert extract_trace(log) == "T|1|0|SAY|who=1\nT|2|1|CHOICE|i=2\n"


def test_extract_trace_ignores_logs_without_trace():
    assert extract_trace("x\ny\n") == ""
    assert extract_trace("[00:00:01.000] |T| [write_file]: *** TTY: hola mundo\n") == ""


def test_stage_config(tmp_path):
    pref = tmp_path / "pref"
    cfg = stage_config(tmp_path, pref)
    content = cfg.read_text(encoding="utf-8")
    assert f'pref-path: "{pref.resolve().as_posix()}"' in content
    assert "log-level: 0" in content
    assert "initial-setup: false" in content


def test_run_exit_code_success(monkeypatch, tmp_path):
    trace = tmp_path / "trace.txt"
    trace.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")

    def fake_run_scenario(_scenario, _out_dir):
        return trace

    monkeypatch.setattr("tools.ctl.vita.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(trace) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "vita", "--scenario", str(scen)]) == 0


def test_run_exit_code_fail(monkeypatch, tmp_path):
    ref = tmp_path / "ref.trace"
    act = tmp_path / "act.trace"
    ref.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")
    act.write_text("T|1|0|SHOW|tag=2\n", encoding="utf-8")

    def fake_run_scenario(_scenario, _out_dir):
        return act

    monkeypatch.setattr("tools.ctl.vita.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(ref) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY, SHOW]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "vita", "--scenario", str(scen)]) == 1


def test_run_exit_code_startup(monkeypatch, tmp_path):
    def fake_run_scenario(_scenario, _out_dir):
        raise OSError("no existe Vita3K.exe")

    monkeypatch.setattr("tools.ctl.vita.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(tmp_path / "no.trace") + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "vita", "--scenario", str(scen)]) == 2
