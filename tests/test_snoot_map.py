"""Pruebas del mapa de recursos compilados de Snoot (T-623)."""
import json
from types import SimpleNamespace

from tools.ctl.snoot_map import build_map


def test_build_map_includes_image_track_and_tag_names(tmp_path, monkeypatch):
    meta = {
        "chapters": [{"index": 0, "text_base": 100}],
        "speakers": [{"name": "Anon"}],
        "images": [None, {"names": ["bg classroom"]}, {"names": ["anon happy"]}],
        "audio": [{"path": "audio/music.ogg"}],
        "tags": {"0": "anon"},
    }
    (tmp_path / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    monkeypatch.setattr("tools.ctl.snoot_map._run_compile_all", lambda out: (
        None, None, SimpleNamespace(errors=[], irs={0: SimpleNamespace(strings=[{"id": "line_1"}])})
    ))
    result = build_map(tmp_path)
    assert result["text"] == {100: "line_1"}
    assert result["images"] == {1: ["bg classroom"], 2: ["anon happy"]}
    assert result["tracks"] == {0: "audio/music.ogg"}
    assert result["tags"] == {0: "anon"}
