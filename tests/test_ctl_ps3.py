"""Pruebas del adapter PS3/RPCS3 (T-613), sin emulador."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.__main__ import main
from tools.ctl.ps3 import CUSTOM_CONFIG_TEXT, extract_trace, install_custom_config, install_pkg, stage_data


def test_extract_trace_from_tty_log():
    log = (
        "PSL1GHT_AUD_Init(00000000.100F05E8)\n"
        "T|1|0|SAY|who=1\n"
        "createRendered\n"
        "T|2|1|CHOICE|i=2\n"
    )
    assert extract_trace(log) == "T|1|0|SAY|who=1\nT|2|1|CHOICE|i=2\n"


def test_extract_trace_ignores_logs_without_trace():
    assert extract_trace("x\ny\n") == ""
    assert extract_trace("") == ""


def test_stage_data(tmp_path):
    disc = tmp_path / "disc"
    (disc / "DATA").mkdir(parents=True)
    (disc / "DATA" / "C00.VNB").write_bytes(b"vnb")
    data_dir = tmp_path / "data"
    staged = stage_data(data_dir, disc, b"\x01\x00\x00\x00\xff\xff")
    assert staged == data_dir
    assert (data_dir / "DATA" / "C00.VNB").read_bytes() == b"vnb"
    assert (data_dir / "AUTOTEST.BIN").read_bytes() == b"\x01\x00\x00\x00\xff\xff"


def test_install_custom_config_writes_once(tmp_path, monkeypatch):
    cfg = tmp_path / "custom_configs" / "config_SNOT00001.yml"
    monkeypatch.setattr("tools.ctl.ps3.CUSTOM_CONFIG", cfg)
    install_custom_config()
    assert cfg.read_text(encoding="utf-8") == CUSTOM_CONFIG_TEXT
    install_custom_config()  # ya existe: no la reescribe
    assert cfg.read_text(encoding="utf-8") == CUSTOM_CONFIG_TEXT


def test_install_pkg_skips_when_eboot_is_newer(tmp_path, monkeypatch):
    pkg = tmp_path / "snoot.pkg"
    pkg.write_bytes(b"pkg")
    eboot = tmp_path / "EBOOT.BIN"
    eboot.write_bytes(b"bin")
    os.utime(pkg, (1000, 1000))
    monkeypatch.setattr("tools.ctl.ps3.EBOOT", eboot)
    # si intentara instalar lanzaria el exe del emulador, que no existe en tmp_path
    install_pkg(pkg)
    assert eboot.is_file()


def test_install_pkg_reinstalls_when_pkg_is_newer(tmp_path, monkeypatch):
    eboot = tmp_path / "EBOOT.BIN"
    eboot.write_bytes(b"old")
    os.utime(eboot, (1000, 1000))
    pkg = tmp_path / "snoot.pkg"
    pkg.write_bytes(b"pkg")
    monkeypatch.setattr("tools.ctl.ps3.EBOOT", eboot)
    monkeypatch.setattr("tools.ctl.ps3.RPCS3_EXE", tmp_path / "rpcs3.exe")
    try:
        install_pkg(pkg)
    except (FileNotFoundError, OSError, RuntimeError):
        pass
    assert not eboot.is_file()


def test_install_pkg_requires_pkg(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.ctl.ps3.EBOOT", tmp_path / "no" / "EBOOT.BIN")
    monkeypatch.setattr("tools.ctl.ps3.RPCS3_EXE", tmp_path / "rpcs3.exe")
    try:
        install_pkg(tmp_path / "missing.pkg")
    except FileNotFoundError as e:
        assert "missing.pkg" in str(e)
    else:
        raise AssertionError("debio fallar con el paquete inexistente")


def test_run_exit_code_success(monkeypatch, tmp_path):
    trace = tmp_path / "trace.txt"
    trace.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")

    def fake_run_scenario(_scenario, _out_dir):
        return trace

    monkeypatch.setattr("tools.ctl.ps3.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(trace) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "ps3", "--scenario", str(scen)]) == 0


def test_run_exit_code_fail(monkeypatch, tmp_path):
    ref = tmp_path / "ref.trace"
    act = tmp_path / "act.trace"
    ref.write_text("T|1|0|SAY|who=1\n", encoding="utf-8")
    act.write_text("T|1|0|SHOW|tag=2\n", encoding="utf-8")

    def fake_run_scenario(_scenario, _out_dir):
        return act

    monkeypatch.setattr("tools.ctl.ps3.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(ref) + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY, SHOW]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "ps3", "--scenario", str(scen)]) == 1


def test_run_exit_code_startup(monkeypatch, tmp_path):
    def fake_run_scenario(_scenario, _out_dir):
        raise OSError("no existe el emulador RPCS3")

    monkeypatch.setattr("tools.ctl.ps3.run_scenario", fake_run_scenario)

    scen = tmp_path / "s.yaml"
    scen.write_text(
        "id: t\nreference: " + str(tmp_path / "no.trace") + "\ninputs: []\nexpect: []\n"
        "compare:\n  events: [SAY]\nlimits:\n  max_seconds: 10\n",
        encoding="utf-8",
    )
    assert main(["run", "--target", "ps3", "--scenario", str(scen)]) == 2
