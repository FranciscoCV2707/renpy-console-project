"""La app, los modulos y los juegos compilan en PC sin ningun header de PS1 (API por enlace, PLAN.md D15)."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GCC = Path(r"C:\msys64\ucrt64\bin\gcc.exe")
CONFIG = {"VN_SEEN_BYTES": "2048", "VN_SAVE_TITLE": "TEST", "VN_SAVE_PREFIX": "BASLUS-99999TEST",
          "VN_SAVE_MAGIC": "TST1"}


@pytest.mark.skipif(not GCC.exists(), reason="falta gcc de MSYS2 ucrt64")
@pytest.mark.parametrize("game", ["default", "snoot", "wani"])
def test_app_builds_without_ps1_headers(tmp_path, game):
    config = (ROOT / "engine/app/game_config.h.in").read_text(encoding="utf-8")
    for key, value in CONFIG.items():
        config = config.replace(f"@{key}@", value)
    (tmp_path / "game_config.h").write_text(config, encoding="utf-8")
    sources = [ROOT / "engine/app/main.c", *sorted((ROOT / "engine/modules").glob("*.c")),
               *sorted((ROOT / "games" / game).glob("*.c"))]
    includes = [f"-I{ROOT / d}" for d in ("engine/core", "engine/platform", "engine/app", "engine/modules")]
    result = subprocess.run([str(GCC), "-std=c99", "-fsyntax-only", "-Werror", *includes, f"-I{tmp_path}",
                             *map(str, sources)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
