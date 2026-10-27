"""Compila tests/core/test_psx_audio.c con el decodificador PSX y lo ejecuta."""
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GCC = Path(r"C:\msys64\ucrt64\bin\gcc.exe")
DATA = Path(r"E:\Dev\snoot-ps1\build\data")

pytestmark = [
    pytest.mark.skipif(not GCC.exists(), reason="falta gcc de MSYS2 ucrt64"),
    pytest.mark.skipif(not (DATA / "MUSIC.XA").exists(), reason="faltan los datos de Snoot"),
]


def run_psx_audio(tmp_path):
    exe = tmp_path / "test_psx_audio.exe"
    subprocess.run(
        [str(GCC), "-std=c99", "-Wall", "-Wextra", "-pedantic", "-Werror",
         "-I", str(ROOT / "platforms" / "sdl"),
         str(ROOT / "platforms" / "sdl" / "psx_audio.c"),
         str(ROOT / "tests" / "core" / "test_psx_audio.c"),
         "-o", str(exe)],
        check=True,
    )
    env = dict(os.environ, PATH=f"{GCC.parent}{os.pathsep}{os.environ['PATH']}")
    result = subprocess.run([str(exe)], capture_output=True, text=True, encoding="utf-8", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "TODO OK" in result.stdout
    return result.stdout


def test_psx_audio_decoders(tmp_path):
    stdout = run_psx_audio(tmp_path)
    assert "SPU real" in stdout
    assert "XA real" in stdout
