"""Pruebas del adapter Nintendo 3DS/Azahar (T-610), sin emulador."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.__main__ import main
from tools.ctl.n3ds import extract_trace, stage_config, stage_sd


def test_extract_trace_from_azahar_log():
    log = (
        "[   0.995330] Service.FS <Debug> ...OpenFile:68: path=[Wchar: /3ds/snoot/data/AUDIO.BIN]\n"
        "[   1.052322] Debug.Emulated <Debug> ...svc.cpp:Kernel::SVC::OutputDebugString:1190: T|1|0|SAY|who=1\n"
        "[   1.100000] Debug.Emulated <Debug> ...svc.cpp:Kernel::SVC::OutputDebugString:1190: T|2|30|SHOW|tag=2\n"
    )
    assert extract_trace(log) == "T|1|0|SAY|who=1\nT|2|30|SHOW|tag=2\n"


def test_extract_trace_ignores_lines_without_trace():
    log = (
        "[   1.052322] Debug.Emulated <Debug> ...OutputDebugString:1190: IOTEST svc line\n"
        "T|1|0|SAY|who=1\n"
        "sin traza\n"
    )
    assert extract_trace(log) == ""


def test_stage_sd(tmp_path):
    disc = tmp_path / "disc"
    disc.mkdir()
    (disc / "C00.VNB").write_bytes(b"vnb")
    data = stage_sd(tmp_path, disc, b"\x01\x00")
    assert data == tmp_path / "sdmc" / "3ds" / "snoot" / "data"
    assert (data / "C00.VNB").read_bytes() == b"vnb"
    assert (data / "AUTOTEST.BIN").read_bytes() == b"\x01\x00"


def test_stage_config_creates_ini(tmp_path):
    stage_config(tmp_path)
    ini = (tmp_path / "config" / "qt-config.ini").read_text(encoding="utf-8")
    assert "log_filter\\default=false" in ini
    assert "log_filter=*:Debug" in ini
    assert "enable_rpc_server\\default=false" in ini
    assert "enable_rpc_server=true" in ini


def test_stage_config_overwrites_ignored_value(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "qt-config.ini").write_text(
        "[Miscellaneous]\r\nlog_filter\\default=true\r\nlog_filter=*:Info\r\n",
        encoding="utf-8", newline="")
    stage_config(tmp_path)
    lines = (config / "qt-config.ini").read_text(encoding="utf-8").splitlines()
    assert lines == [
        "[Miscellaneous]",
        "log_filter\\default=false",
        "log_filter=*:Debug",
        "[Debugging]",
        "enable_rpc_server\\default=false",
        "enable_rpc_server=true",
    ]


def test_main_accepts_3ds_target():
    assert main(["run", "--target", "3ds", "--scenario", "inexistente.yaml"]) == 2
