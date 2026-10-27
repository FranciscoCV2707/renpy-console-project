"""Pruebas del adapter PS2/PCSX2, sin emulador."""
from tools.ctl.ps2 import extract_trace


def test_extract_trace_mixed_output():
    text = "booting\nT|1|0|SAY|who=1\nnoise\nT|2|1|CHOICE|i=2\n"
    assert extract_trace(text) == "T|1|0|SAY|who=1\nT|2|1|CHOICE|i=2\n"


def test_extract_trace_empty_output():
    assert extract_trace("PCSX2 started\n") == ""
