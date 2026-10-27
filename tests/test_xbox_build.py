import shutil
import subprocess

import pytest

# Compilan en Docker (minutos): solo con `pytest -m consoles`
pytestmark = pytest.mark.consoles

from platforms.xbox.build import build


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    return True


@pytest.mark.skipif(not _docker_available(), reason="Docker no disponible")
def test_xbox_build_trace_package():
    executable = build(trace=True)
    assert executable.is_file()
    assert executable.name == "default.xbe"
