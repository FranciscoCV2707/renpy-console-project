import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Compila en Docker (minutos): solo con `pytest -m consoles`
pytestmark = pytest.mark.consoles


def test_ds_build_rom():
    if not shutil.which("docker"):
        pytest.skip("docker no disponible")
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "platforms/ds/build.py"], cwd=root, check=True)
    assert (root / "build" / "ds" / "snoot.nds").is_file()
