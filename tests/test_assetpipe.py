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


def _make_console_game(tmp_path: Path) -> Path:
    from PIL import Image

    game = tmp_path / "game"
    (game / "images").mkdir(parents=True)
    Image.new("RGB", (1920, 1080), (200, 30, 30)).save(game / "images" / "bg.jpg")
    Image.new("RGBA", (100, 50), (0, 0, 0, 0)).save(game / "images" / "icon.png")
    (game / "audio").mkdir()
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                    "-c:a", "libvorbis", str(game / "audio" / "beep.ogg")], check=True)
    (game / "video").mkdir()
    (game / "video" / "intro.webm").write_bytes(b"webm-bytes")
    return game


@pytest.mark.parametrize(
    "profile, size, rate, channels, skips_video",
    [
        ("psp", (480, 270), 22050, 1, True),
        ("ps2", (640, 360), 22050, 1, True),
        ("vita", (960, 540), 22050, 1, False),
        ("3ds", (400, 225), 22050, 1, True),
        ("wii", (640, 360), 22050, 1, True),
        ("xbox", (640, 360), 22050, 1, False),
        ("switch", (1280, 720), 44100, 1, False),
    ],
)
def test_console_profiles_reduce_resources(tmp_path, profile, size, rate, channels, skips_video):
    import wave

    from PIL import Image

    from tools.assetpipe.manifest import run

    game = _make_console_game(tmp_path)
    manifest = run(profile, game, tmp_path / "out")
    by_source = {r["source"]: r for r in manifest["resources"]}
    assert by_source["images/bg.jpg"]["path"] == "images/bg.png"
    with Image.open(tmp_path / "out" / "images" / "bg.png") as img:
        assert img.size == size
    with Image.open(tmp_path / "out" / "images" / "icon.png") as img:
        assert img.size == (100, 50)
    with wave.open(str(tmp_path / "out" / "audio" / "beep.wav")) as w:
        assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (rate, channels, 2)
    if skips_video:
        assert manifest["skipped"] == [{"source": "video/intro.webm"}]
        assert not (tmp_path / "out" / "video" / "intro.webm").exists()
    else:
        assert manifest["skipped"] == []
        assert (tmp_path / "out" / "video" / "intro.webm").read_bytes() == b"webm-bytes"
    first = (tmp_path / "out" / "manifest.json").read_bytes()
    run(profile, game, tmp_path / "out2")
    assert (tmp_path / "out2" / "manifest.json").read_bytes() == first


def test_language_uses_translated_files(tmp_path):
    from tools.assetpipe.manifest import run

    game = _make_game(tmp_path)
    (game / "tl" / "es" / "images").mkdir(parents=True)
    (game / "tl" / "es" / "images" / "hero.png").write_bytes(b"png-es")
    manifest = run("pc", game, tmp_path / "out", "es")
    assert (tmp_path / "out" / "images" / "hero.png").read_bytes() == b"png-es"
    assert (tmp_path / "out" / "audio" / "theme.ogg").read_bytes() == b"ogg-bytes"
    assert manifest["language"] == "es"
    assert not any(r["path"].startswith("tl/") for r in manifest["resources"])
    with pytest.raises(ValueError, match="traduccion fr"):
        run("pc", game, tmp_path / "out2", "fr")


def _make_audio_duration_game(tmp_path: Path) -> Path:
    game = tmp_path / "game"
    (game / "audio").mkdir(parents=True)
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
         "sine=frequency=440:duration=15", "-c:a", "libvorbis", str(game / "audio" / "long.ogg")],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
         "sine=frequency=440:duration=1", str(game / "audio" / "short.ogg")],
        check=True,
    )
    return game


@pytest.mark.parametrize(
    "profile, music_rate, music_channels, quality, sound_rate",
    [
        ("psp", 44100, 2, 0, 22050),
        ("ps2", 44100, 2, 2, 22050),
        ("vita", 44100, 2, 4, 22050),
        ("3ds", 32000, 2, 1, 22050),
        ("wii", 32000, 2, 2, 22050),
        ("xbox", 44100, 2, 3, 22050),
        ("switch", 44100, 2, 5, 44100),
    ],
)
def test_console_audio_split_by_duration(
    tmp_path, profile, music_rate, music_channels, quality, sound_rate
):
    import wave

    from tools.assetpipe.manifest import run
    from tools.assetpipe.profiles import PROFILES

    assert PROFILES[profile]["music_rate"] == music_rate
    assert PROFILES[profile]["music_channels"] == music_channels
    assert PROFILES[profile]["music_quality"] == quality
    assert PROFILES[profile]["music_threshold"] == 10
    game = _make_audio_duration_game(tmp_path)
    out = tmp_path / "out"
    manifest = run(profile, game, out)
    by_source = {r["source"]: r for r in manifest["resources"]}
    assert by_source["audio/long.ogg"]["kind"] == "music"
    assert by_source["audio/long.ogg"]["path"] == "audio/long.ogg"
    assert by_source["audio/short.ogg"]["kind"] == "sound"
    assert by_source["audio/short.ogg"]["path"] == "audio/short.wav"
    assert (out / "audio" / "long.ogg").is_file()
    assert (out / "audio" / "short.wav").is_file()
    with wave.open(str(out / "audio" / "short.wav")) as w:
        assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (sound_rate, 1, 2)
    # OGG de musica: 44100 Hz estereo
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
         "stream=sample_rate,channels", "-of", "csv=p=0", str(out / "audio" / "long.ogg")],
        capture_output=True, text=True, check=True,
    )
    assert probe.stdout.strip() == f"{music_rate},{music_channels}"
    # determinismo del manifest
    out2 = tmp_path / "out2"
    run(profile, game, out2)
    assert (out / "manifest.json").read_bytes() == (out2 / "manifest.json").read_bytes()
