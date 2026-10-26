"""Pruebas del pipeline de recursos (assetpipe)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _make_game(tmp_path: Path) -> Path:
    game = tmp_path / "game"
    (game / "images").mkdir(parents=True)
    (game / "images" / "hero.png").write_bytes(b"png-bytes")
    (game / "images" / "ignore.rpy").write_text("print('x')", encoding="utf-8")
    (game / "audio").mkdir()
    (game / "audio" / "theme.ogg").write_bytes(b"ogg-bytes")
    (game / "video").mkdir()
    (game / "video" / "intro.webm").write_bytes(b"webm-bytes")
    (game / "gui" / "fonts").mkdir(parents=True)
    (game / "gui" / "fonts" / "main.ttf").write_bytes(b"ttf-bytes")
    (game / "script.rpy").write_text("label start: pass", encoding="utf-8")
    return game


def test_copy_and_manifest(tmp_path):
    from tools.assetpipe.manifest import run

    game = _make_game(tmp_path)
    out = tmp_path / "out"
    manifest = run("pc", game, out)

    # Copia correcta
    assert (out / "images" / "hero.png").read_bytes() == b"png-bytes"
    assert (out / "audio" / "theme.ogg").read_bytes() == b"ogg-bytes"
    assert (out / "video" / "intro.webm").read_bytes() == b"webm-bytes"
    assert (out / "gui" / "fonts" / "main.ttf").read_bytes() == b"ttf-bytes"

    # Ignora .rpy
    assert not (out / "script.rpy").exists()
    assert not (out / "images" / "ignore.rpy").exists()

    # Manifest
    assert manifest["profile"] == "pc"
    assert manifest["count"] == 4
    paths = {r["path"] for r in manifest["resources"]}
    assert paths == {"images/hero.png", "audio/theme.ogg", "video/intro.webm", "gui/fonts/main.ttf"}
    for entry in manifest["resources"]:
        assert set(entry) == {"path", "kind", "bytes", "sha256"}


def test_manifest_deterministic(tmp_path):
    from tools.assetpipe.manifest import run

    game = _make_game(tmp_path)
    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    run("pc", game, out1)
    run("pc", game, out2)
    m1 = (out1 / "manifest.json").read_text(encoding="utf-8")
    m2 = (out2 / "manifest.json").read_text(encoding="utf-8")
    assert m1 == m2


def test_out_inside_game_rejected(tmp_path):
    game = _make_game(tmp_path)
    out = game / "out"
    result = subprocess.run(
        [sys.executable, "-m", "tools.assetpipe", "--profile", "pc", "--game", str(game), "--out", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_cli_real_game_smoke(tmp_path):
    # Solo si el juego real existe.
    game = Path("E:/snoot/snootgame/game")
    if not game.is_dir():
        pytest.skip("juego real no disponible")
    out = tmp_path / "pc"
    result = subprocess.run(
        [sys.executable, "-m", "tools.assetpipe", "--profile", "pc", "--game", str(game), "--out", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["profile"] == "pc"
    assert manifest["count"] > 0
