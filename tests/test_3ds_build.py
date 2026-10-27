import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Compilan en Docker (minutos): solo con `pytest -m consoles`
pytestmark = pytest.mark.consoles


def test_3ds_build_package():
    if not shutil.which("docker"):
        pytest.skip("docker no disponible")
    subprocess.run(
        [sys.executable, "platforms/3ds/build.py", "--trace"],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )
    assert (Path(__file__).resolve().parents[1] / "build" / "3ds" / "snoot.3dsx").is_file()
