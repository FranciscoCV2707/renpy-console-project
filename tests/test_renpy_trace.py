"""Pruebas del hook de traza Ren'Py (T-301)."""
import textwrap
from pathlib import Path
from types import SimpleNamespace

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
        self._attrs = {}
        self._who = {}

        def _display_menu(items, *args, **kwargs):
            if self._display_menu_result is not None:
                return self._display_menu_result
            if items:
                return items[0][1]
            return None

        self.exports = SimpleNamespace(display_menu=_display_menu)
        self.store = SimpleNamespace(_last_say_who=None)
        def _play(filenames, channel="music", *args, **kwargs):
            self._music = filenames

        def _stop(channel="music", *args, **kwargs):
            self._music = None

        self.music = SimpleNamespace(get_playing=lambda channel: self._music, play=_play, stop=_stop)
        self.game = SimpleNamespace(context=lambda: SimpleNamespace(translate_identifier="start_1a2b3c4d"))

    def get_filename_line(self):
        return self._loc

    def scene(self, layer="master"):
        self._tags = set()

    def get_showing_tags(self, layer="master"):
        return set(self._tags)

    def get_attributes(self, tag, layer=None, if_hidden=None):
        return self._attrs.get(tag, ())

    def eval_who(self, who):
        return self._who[who]

    def translate_string(self, s):
        return s


class FakeConfig:
    def __init__(self):
        self.label_callbacks = []
        self.start_interact_callbacks = []
        self.all_character_callbacks = []


def _run(monkeypatch, env_value=None):
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
    ns, renpy, config = _run(monkeypatch, None)
    if config.label_callbacks:
        config.label_callbacks[0]("start", False)
    if config.start_interact_callbacks:
        renpy._tags = {"bg"}
        config.start_interact_callbacks[0]()
    assert not out.exists() or out.read_text(encoding="utf-8") == ""


def test_sequence_produces_expected_lines(tmp_path, monkeypatch):
    out = tmp_path / "trace.txt"
    ns, renpy, config = _run(monkeypatch, str(out))
    renpy._tags = {"bg"}
    # el hook envuelve renpy.music.play/stop: la musica sale de las ordenes del guion
    renpy.music.play("song.ogg", channel="music")
    renpy._who = {"e": SimpleNamespace(name="Eileen")}
    renpy._attrs = {"sayori": ("smile", "happy")}
    renpy.store._last_say_who = "e"

    config.label_callbacks[0]("start", False)

    renpy._tags = {"bg", "sayori"}
    renpy._loc = ("game/script.rpy", 20)
    config.all_character_callbacks[0]("begin", interact=True)
    config.start_interact_callbacks[0]()

    renpy._tags = {"room"}
    renpy.music.stop(channel="music")
    renpy._music = "song.ogg"  # el canal sigue sonando (fadeout): no debe contar
    config.start_interact_callbacks[0]()

    renpy.exports.display_menu([("Yes", 0), ("No", 1)])

    lines = out.read_text(encoding="utf-8").splitlines()
    expected = [
        "T|1|0|LABEL|name=start",
        "T|2|1|SHOW|tag=bg;attrs=",
        "T|3|1|SHOW|tag=sayori;attrs=smile happy",
        "T|4|1|PLAY|music=song.ogg",
        "T|5|1|SAY|who=Eileen;id=start_1a2b3c4d;loc=game/script.rpy:20",
        "T|6|2|SCENE",
        "T|7|2|SHOW|tag=room;attrs=",
        "T|8|2|STOP|music=song.ogg",
        "T|9|2|MENU|loc=game/script.rpy:20",
        "T|10|2|CHOICE|i=0",
    ]
    assert lines == expected


def test_say_who_from_store_contract(tmp_path, monkeypatch):
    out = tmp_path / "trace.txt"
    ns, renpy, config = _run(monkeypatch, str(out))
    renpy._who = {"e": SimpleNamespace(name="Eileen")}
    renpy._loc = ("game/script.rpy", 12)
    renpy.store._last_say_who = "e"
    config.all_character_callbacks[0]("begin", interact=True)
    config.start_interact_callbacks[0]()
    renpy.store._last_say_who = None
    config.all_character_callbacks[0]("begin", interact=False)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines == [
        "T|1|1|SAY|who=Eileen;id=start_1a2b3c4d;loc=game/script.rpy:12",
        "T|2|1|SAY|who=;id=start_1a2b3c4d;loc=game/script.rpy:12",
    ]


def test_escape(tmp_path, monkeypatch):
    out = tmp_path / "trace.txt"
    ns, renpy, config = _run(monkeypatch, str(out))
    renpy._who = {"e": SimpleNamespace(name="a|b")}
    renpy.store._last_say_who = "e"
    renpy._loc = ("x;y=z\nline.rpy", 1)
    config.all_character_callbacks[0]("begin", interact=True)
    config.start_interact_callbacks[0]()
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines == ["T|1|1|SAY|who=a\\|b;id=start_1a2b3c4d;loc=x\\;y\\=z\\nline.rpy:1"]


def test_escape_function():
    code = _extract_body()
    ns = {}
    exec(compile(code, str(HOOK), "exec"), {"renpy": FakeRenpy(), "config": FakeConfig()}, ns)
    assert ns["_rcp_escape"]("a|b;c=d\ne") == "a\\|b\\;c\\=d\\ne"


def test_choice_title_index(tmp_path, monkeypatch):
    out = tmp_path / "trace.txt"
    ns, renpy, config = _run(monkeypatch, str(out))
    renpy._loc = ("game/script.rpy", 5)
    renpy._display_menu_result = 0
    renpy.exports.display_menu([("Title", None), ("Yes", 0), ("No", 1)])
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines == ["T|1|0|MENU|loc=game/script.rpy:5", "T|2|0|CHOICE|i=0"]


def test_unknown_choice_not_emitted(tmp_path, monkeypatch):
    out = tmp_path / "trace.txt"
    ns, renpy, config = _run(monkeypatch, str(out))
    renpy._display_menu_result = object()
    renpy._loc = ("game/script.rpy", 5)
    renpy.exports.display_menu([("Yes", 0), ("No", 1)])
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines == ["T|1|0|MENU|loc=game/script.rpy:5"]
