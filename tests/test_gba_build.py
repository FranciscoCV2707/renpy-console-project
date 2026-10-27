import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Compilan en Docker (minutos): solo con `pytest -m consoles`
pytestmark = pytest.mark.consoles


def test_gba_build_package():
    if not shutil.which("docker"):
        pytest.skip("docker no disponible")
    subprocess.run(
        [sys.executable, "platforms/gba/build.py"],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )
    assert (Path(__file__).resolve().parents[1] / "build" / "gba" / "snoot.gba").is_file()
