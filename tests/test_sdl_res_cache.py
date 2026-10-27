"""Compila platforms/sdl/res.c con tests/core/test_sdl_res_cache.c y prueba el cache en host (sin SDL)."""
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GCC = Path(r"C:\msys64\ucrt64\bin\gcc.exe")

pytestmark = pytest.mark.skipif(not GCC.exists(), reason="falta gcc de MSYS2 ucrt64")


def run_res_cache(tmp_path):
    exe = tmp_path / "test_sdl_res_cache.exe"
    subprocess.run(
        [str(GCC), "-std=c99", "-Wall", "-Wextra", "-pedantic", "-Werror",
         "-I", str(ROOT / "engine" / "platform"),
         "-I", str(ROOT / "platforms" / "sdl"),
         str(ROOT / "platforms" / "sdl" / "res.c"),
         str(ROOT / "tests" / "core" / "test_sdl_res_cache.c"),
         "-o", str(exe)],
        check=True,
    )
    env = dict(os.environ, PATH=f"{GCC.parent}{os.pathsep}{os.environ['PATH']}")
    result = subprocess.run([str(exe)], capture_output=True, text=True, encoding="utf-8", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "TODO OK" in result.stdout
    return result.stdout


def test_res_cache_evicts_and_remembers_missing(tmp_path):
    stdout = run_res_cache(tmp_path)
    assert "id inexistente solo abre el archivo una vez" in stdout
    assert "libera la textura con img_release" in stdout
