"""Pruebas del adapter Wii / Dolphin (T-611), sin emulador."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.__main__ import main
from tools.ctl.wii import extract_trace, stage_config, stage_sd


def test_extract_trace_from_dolphin_log():
    log = (
        "00:00:01.123 INFO: Booting boot.dol\n"
        "00:00:02.456 OSREPORT: T|1|0|SAY|who=1\n"
        "00:00:02.500 OSREPORT: T|2|30|SHOW|tag=2\n"
        "00:00:03.000 INFO: otra linea\n"
    )
    assert extract_trace(log) == "T|1|0|SAY|who=1\nT|2|30|SHOW|tag=2\n"


def test_extract_trace_direct_lines():
    log = "T|1|0|SAY|who=1\nsin traza\nT|2|1|CHOICE|i=2\n"
    assert extract_trace(log) == "T|1|0|SAY|who=1\nT|2|1|CHOICE|i=2\n"


def test_extract_trace_ignores_log_without_trace():
    assert extract_trace("") == ""
    assert extract_trace("00:00:01.000 OSREPORT: hola\nx\n") == ""


def test_stage_config(tmp_path):
    stage_config(tmp_path)
    ini = (tmp_path / "Config" / "Dolphin.ini").read_text(encoding="utf-8")
    assert "PermissionAsked = True" in ini
    assert "ConfirmStop = False" in ini


def test_stage_sd(tmp_path):
    disc = tmp_path / "disc"
    disc.mkdir()
    (disc / "snoot_game.cue").write_bytes(b"cue")
    data = stage_sd(tmp_path, disc, b"\x01\x00")
    assert data == tmp_path / "apps" / "snoot" / "data"
    assert (data / "snoot_game.cue").read_bytes() == b"cue"
    assert (data / "AUTOTEST.BIN").read_bytes() == b"\x01\x00"


def test_main_accepts_wii_target():
    assert main(["run", "--target", "wii", "--scenario", "inexistente.yaml"]) == 2
