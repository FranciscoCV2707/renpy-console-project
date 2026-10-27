"""Pruebas de comparacion cruzada PS1 <-> Ren'Py (T-303)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ctl.trace import (
    parse_trace,
    normalize_engine,
    normalize_renpy,
    compare_cross,
)
from tools.ctl.scenario import load_scenario


FAKE_MAP = {
    "text": {100: "chapter_x3_93919e8e", 101: "chapter_x3_b0f49f92"},
    "speakers": {0: "", 1: "Spears"},
}


def test_normalize_engine_and_renpy_match():
    engine_text = (
        "T|1|0|SAY|who=0;text=100\n"
        "T|2|1|SAY|who=1;text=101\n"
        "T|3|2|CHOICE|i=1\n"
        "T|4|3|SHOW|tag=bg\n"
    )
    renpy_text = (
        "T|10|0|SAY|who=;id=chapter_x3_93919e8e;loc=x.rpy:1\n"
        "T|11|1|SAY|who=Spears;id=chapter_x3_b0f49f92;loc=x.rpy:2\n"
        "T|12|2|CHOICE|i=1\n"
        "T|13|3|SHOW|tag=bg\n"
    )
    eng = normalize_engine(parse_trace(engine_text), FAKE_MAP)
    ref = normalize_renpy(parse_trace(renpy_text))
    assert len(eng) == 3
    assert len(ref) == 3
    assert eng[0].ev == "SAY"
    assert eng[0].fields == {"who": "", "id": "chapter_x3_93919e8e"}
    assert ref[1].fields == {"who": "Spears", "id": "chapter_x3_b0f49f92"}
    result = compare_cross(eng, ref)
    assert result.equal is True
    assert result.verdict == "PASS"


def test_compare_cross_first_divergent():
    engine_text = (
        "T|1|0|SAY|who=0;text=100\n"
        "T|2|1|SAY|who=1;text=101\n"
    )
    renpy_text = (
        "T|10|0|SAY|who=;id=chapter_x3_93919e8e;loc=x.rpy:1\n"
        "T|11|1|SAY|who=Spears;id=chapter_x3_OTHER;loc=x.rpy:2\n"
    )
    eng = normalize_engine(parse_trace(engine_text), FAKE_MAP)
    ref = normalize_renpy(parse_trace(renpy_text))
    result = compare_cross(eng, ref)
    assert result.equal is False
    assert result.verdict == "FAIL"
    assert result.index == 1
    assert result.actual.fields["id"] == "chapter_x3_b0f49f92"
    assert result.reference.fields["id"] == "chapter_x3_OTHER"


def test_compare_cross_length_mismatch():
    eng = normalize_engine(parse_trace("T|1|0|SAY|who=0;text=100\n"), FAKE_MAP)
    ref = normalize_renpy(parse_trace(
        "T|10|0|SAY|who=;id=chapter_x3_93919e8e;loc=x.rpy:1\n"
        "T|11|1|CHOICE|i=0\n"))
    result = compare_cross(eng, ref)
    assert result.equal is False
    assert result.index == 1


def test_scenario_mode_renpy_loads():
    scen = load_scenario(ROOT / "tests" / "scenarios" / "snoot-x3-ps1-vs-renpy.yaml")
    assert scen.compare.mode == "renpy"
    assert scen.compare.events == ["SAY", "CHOICE"]
