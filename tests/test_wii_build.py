import shutil
import subprocess

import pytest

# Compilan en Docker (minutos): solo con `pytest -m consoles`
pytestmark = pytest.mark.consoles

from platforms.wii.build import build


def _docker_available() -> bool:
    docker = shutil.which("docker")
    if not docker:
        return False
    try:
        subprocess.run(
            [docker, "info"],
            check=True,
            capture_output=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    return True


@pytest.mark.skipif(not _docker_available(), reason="Docker not available")
def test_wii_build_package():
    executable = build(trace=True)
    assert executable.is_file()
    assert (executable.parent / "meta.xml").is_file()
