"""Compila el nucleo con el backend PC y corre tests/core/test_core_host.c contra datos reales de Wani."""
import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GCC = Path(r"C:\msys64\ucrt64\bin\gcc.exe")
DATA = Path(r"E:\Dev\wani-ps1\build\fase0")

pytestmark = [
    pytest.mark.skipif(not GCC.exists(), reason="falta gcc de MSYS2 ucrt64"),
    pytest.mark.skipif(not (DATA / "C00.VNB").exists(), reason="faltan los datos compilados de Wani"),
]


def run_core(tmp_path, *defines):
    exe = tmp_path / "test_core_host.exe"
    sources = sorted((ROOT / "engine/core").glob("*.c"))
    subprocess.run(
        [str(GCC), "-std=c99", "-Wall", "-Wextra", "-pedantic", "-Werror", *defines,
         "-I", str(ROOT / "engine/core"), "-I", str(ROOT / "platforms/pc"),
         *map(str, sources), str(ROOT / "platforms/pc/backend.c"), str(ROOT / "tests/core/test_core_host.c"),
         "-o", str(exe)],
        check=True,
    )
    env = dict(os.environ, PATH=f"{GCC.parent}{os.pathsep}{os.environ['PATH']}")
    result = subprocess.run([str(exe), str(DATA)], capture_output=True, text=True, encoding="utf-8", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "TODO OK" in result.stdout
    return result.stdout


def test_core_runs_to_first_line_on_host(tmp_path):
    assert "T|" not in run_core(tmp_path)


def test_trace_build_logs_events_up_to_the_first_line(tmp_path):
    lines = [line.removeprefix("[PC] ") for line in run_core(tmp_path, "-DVN_TRACE").splitlines()
             if line.startswith("[PC] T|")]
    assert lines, "el build con VN_TRACE no emitio ninguna linea"
    assert all(re.fullmatch(r"T\|\d+\|\d+\|[A-Z]+\|\S*", line) for line in lines), lines
    assert [int(line.split("|")[1]) for line in lines] == list(range(len(lines)))
    assert lines[-1].split("|")[3] == "SAY"
