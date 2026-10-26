"""Pruebas de tools.renpy_trace.record (T-302), sin ejecutar el juego."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.renpy_trace import record


def _fake_game(published):
    published.mkdir(parents=True, exist_ok=True)
    (published / "game").mkdir(exist_ok=True)
    (published / "game" / "script.rpy").write_text("label start: pass", encoding="utf-8")
    (published / "snoot.exe").write_bytes(b"")
    return published


def test_prepare_copy_adds_trace_hook(tmp_path):
    published = _fake_game(tmp_path / "published")
    copy = tmp_path / "copy"
    result = record.prepare_copy(published / "game", copy)
    assert Path(result) == copy
    assert (copy / "game" / "trace_hook.rpy").exists()
    assert (copy / "game" / "zz_kit_capture.rpy").exists()


def test_unknown_route_cli_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(record, "load_routes", lambda *a, **k: {"chapter_x1": {"entry": "chapter_x1", "decisions": []}})
    rc = record.main(["--route", "nope"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "ruta desconocida" in err
    assert "nope" in err


def test_unknown_route_raises():
    with pytest.raises(record.UnknownRouteError):
        record.record("nope", routes={"chapter_x1": {"entry": "chapter_x1", "decisions": []}})


def test_list_routes(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(record, "load_routes", lambda *a, **k: {"chapter_x1": {"entry": "chapter_x1", "decisions": []}})
    rc = record.main(["--list"])
    assert rc == 0
    assert "chapter_x1" in capsys.readouterr().out


def test_record_one_route_with_fakes(tmp_path, monkeypatch):
    # Evita tocar el juego real: sustituye las funciones externas.
    published = _fake_game(tmp_path / "published")
    kit_folder = tmp_path / "kit" / "juegos" / "snoot"
    kit_folder.mkdir(parents=True)
    (kit_folder / "game.toml").write_text(
        '[paths]\ngame = "%s"\n[capture]\nallowed = true\nreason = "t"\nlauncher = "game"\n'
        % str(published / "game").replace("\\", "\\\\"),
        encoding="utf-8",
    )
    (kit_folder / "reporte").mkdir()
    (kit_folder / "reporte" / "rutas.json").write_text(
        json.dumps({"chapter_x1": {"entry": "chapter_x1", "decisions": []}}), encoding="utf-8"
    )

    def fake_run_route(command, copy, name, route, out_root, *a, **k):
        out_root = Path(out_root)
        trace_path = Path(__import__("os").environ["RCP_TRACE_OUT"])
        trace_path.write_text("T|1|0|LABEL|name=start\n", encoding="utf-8")
        return {"route": name, "status": "ok"}

    monkeypatch.setattr(record, "run_route", fake_run_route)
    results = record.record(
        "chapter_x1",
        port_kit=tmp_path / "kit",
        snoot_folder=kit_folder,
        build_dir=tmp_path / "build",
        trace_dir=tmp_path / "traces",
        timeout=10,
    )
    assert len(results) == 1
    assert results[0]["status"] == "ok"
    trace = Path(results[0]["trace"])
    assert trace.exists()
    assert "LABEL" in trace.read_text(encoding="utf-8")
