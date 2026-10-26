"""Pruebas del hook de traza Ren'Py (T-301)."""
import os
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "tools" / "renpy_trace" / "trace_hook.rpy"


def _extract_body():
    text = HOOK.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "init -999 python:")
    body = []
    for line in lines[start + 1:]:
        if line.strip() == "":
            body.append("")
            continue
        if not (line.startswith(" ") or line.startswith("\t")):
            break
        body.append(line)
    return textwrap.dedent("\n".join(body))


class FakeRenpy:
    def __init__(self):
        self._loc = ("game/script.rpy", 10)
        self._tags = set()
        self._music = None
        self._display_menu_result = None

        def _display_menu(items, *args, **kwargs):
            if self._display_menu_result is not None:
                return self._display_menu_result
            if items:
                item = items[0]
                if isinstance(item, (tuple, list)):
                    return item[1] if len(item) > 1 else item[0]
                return item
            return None

        self.exports = SimpleNamespace(display_menu=_display_menu)
        self.store = SimpleNamespace(_last_say_who=None)
        self.music = SimpleNamespace(get_playing=lambda channel: self._music)

    def get_filename_line(self):
        return self._loc

    def get_showing_tags(self, layer="master"):
        return set(self._tags)


class FakeConfig:
    def __init__(self):
        self.label_callbacks = []
        self.start_interact_callbacks = []
        self.all_character_callbacks = []


def _run(monkeypatch, tmp_path, env_value=None):
    if env_value is None:
        monkeypatch.delenv("RCP_TRACE_OUT", raising=False)
    else:
        monkeypatch.setenv("RCP_TRACE_OUT", env_value)
    code = _extract_body()
    renpy = FakeRenpy()
    config = FakeConfig()
    ns = {"renpy": renpy, "config": config}
    exec(compile(code, str(HOOK), "exec"), ns)
    return ns, renpy, config


def test_no_env_does_not_write(tmp_path, monkeypatch):
    out = tmp_path / "trace.txt"
    ns, renpy, config = _run(monkeypatch, tmp_path, None)
    if config.label_callbacks:
        config.label_callbacks[0]("start", False)
    if config.start_interact_callbacks:
        renpy._tags = {"bg"}
        config.start_interact_callbacks[0]()
    assert not out.exists() or out.read_text(encoding="utf-8") == ""


def test_sequence_produces_expected_lines(tmp_path, monkeypatch):
    out = tmp_path / "trace.txt"
    ns, renpy, config = _run(monkeypatch, tmp_path, str(out))
    renpy._tags = {"bg"}
    renpy._music = "song.ogg"
    renpy.store._last_say_who = "Eileen"

    config.label_callbacks[0]("start", False)

    renpy._tags = {"bg", "sayori"}
    renpy._music = "song.ogg"
    renpy._loc = ("game/script.rpy", 20)
    config.start_interact_callbacks[0]()

    config.all_character_callbacks[0]("begin", interact=True, who="Eileen", loc="game/script.rpy:20")

    renpy._tags = {"room"}
    renpy._music = None
    config.start_interact_callbacks[0]()

    renpy.exports.display_menu([("Yes", 0), ("No", 1)])

    lines = out.read_text(encoding="utf-8").splitlines()
    expected = [
        "T|1|0|LABEL|name=start",
        "T|2|1|SHOW|tag=bg",
        "T|3|1|SHOW|tag=sayori",
        "T|4|1|PLAY|music=song.ogg",
        "T|5|1|SAY|who=Eileen;loc=game/script.rpy:20",
        "T|6|2|SCENE",
        "T|7|2|SHOW|tag=room",
        "T|8|2|STOP|music=song.ogg",
        "T|9|2|MENU|loc=game/script.rpy:20",
        "T|10|2|CHOICE|i=0",
    ]
    assert lines == expected


def test_escape(tmp_path, monkeypatch):
    out = tmp_path / "trace.txt"
    ns, renpy, config = _run(monkeypatch, tmp_path, str(out))
    renpy._loc = ("p.rpy", 1)
    config.all_character_callbacks[0](
        "begin", interact=True, who="a|b", loc="x;y=z\nline"
    )
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines == ["T|1|0|SAY|who=a\\|b;loc=x\\;y\\=z\\nline"]


def test_escape_function():
    code = _extract_body()
    ns = {}
    exec(compile(code, str(HOOK), "exec"), {"renpy": FakeRenpy(), "config": FakeConfig()}, ns)
    assert ns["_rcp_escape"]("a|b;c=d\ne") == "a\\|b\\;c\\=d\\ne"