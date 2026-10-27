"""tools.renpy_trace.record sin correr el juego."""
import json
import os
from pathlib import Path

import pytest

record = pytest.importorskip("tools.renpy_trace.record", reason="falta renpy-port-kit en E:\\Dev")

ROUTES = {"chapter_x1": {"entry": "chapter_x1", "decisions": []}}


def fake_game(tmp_path):
    published = tmp_path / "published"
    (published / "game").mkdir(parents=True)
    (published / "game" / "script.rpy").write_text("label start:\n    return\n", encoding="utf-8")
    (published / "snoot.exe").write_bytes(b"")
    folder = tmp_path / "kit"
    folder.mkdir()
    (folder / "game.toml").write_text(f"[paths]\ngame = '{published / 'game'}'\n[capture]\nallowed = true\n"
                                      "reason = 'prueba'\n", encoding="utf-8")
    return published, folder


def test_prepare_copy_adds_both_hooks(tmp_path):
    published, _ = fake_game(tmp_path)
    copy = record.prepare_copy(published / "game", tmp_path / "copy")
    assert (copy / "game" / "trace_hook.rpy").is_file()
    assert (copy / "game" / "zz_kit_capture.rpy").is_file()
    assert (copy / "game" / "zz_rcp_snoot_capture.rpy").is_file()


def test_unknown_route_fails_before_running_anything(tmp_path):
    with pytest.raises(ValueError, match="ruta desconocida: nope"):
        record.record(["nope"], ROUTES, tmp_path, tmp_path / "build", tmp_path / "traces")


def test_record_writes_the_trace_of_each_route(tmp_path, monkeypatch):
    _, folder = fake_game(tmp_path)

    routes = {**ROUTES, "ruta 1": {"entry": "start", "decisions": []}}

    def run_route(command, copy, name, route, out_root, settings):
        assert settings["wait"] == 0.2
        # como Ren'Py en Windows: CRLF
        Path(os.environ["RCP_TRACE_OUT"]).write_bytes(b"T|1|0|LABEL|name=start\r\n")
        return {"status": "ok" if name == "chapter_x1" else "se detuvo a los 3600 s"}

    monkeypatch.setattr(record.capture, "run_route", run_route)
    failed = record.record(["chapter_x1", "ruta 1"], routes, folder, tmp_path / "build", tmp_path / "traces")
    assert failed == ["ruta 1"]
    assert (tmp_path / "traces" / "chapter_x1.trace").read_bytes() == b"T|1|0|LABEL|name=start\n"
    assert not (tmp_path / "traces" / "ruta 1.trace").exists()


def test_routes_file_is_name_to_route():
    routes = record.load_routes()
    assert "chapter_x1" in routes and json.dumps(routes["chapter_x1"])
