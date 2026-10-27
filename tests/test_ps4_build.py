"""Pruebas de compilacion de Snoot para PS4 (T-606)."""
from __future__ import annotations

import shutil
import subprocess

import pytest

from platforms.ps4.build import build


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return res.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


@pytest.mark.skipif(not _docker_available(), reason="Docker no esta disponible")
def test_ps4_build_package() -> None:
    pkg = build(trace=True)
    assert pkg.is_file()
    assert (pkg.parent / "eboot.bin").is_file()
    assert (pkg.parent / "IV0000-SNOT00001_00-SNOOTGAME0000000.pkg").is_file()
