"""Pruebas de compilacion de Snoot para PS3 (T-607)."""
from __future__ import annotations

import shutil
import subprocess

import pytest

from platforms.ps3.build import build

pytestmark = pytest.mark.consoles


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return res.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


@pytest.mark.skipif(not _docker_available(), reason="Docker no esta disponible")
def test_ps3_build_package() -> None:
    self_file = build(trace=True)
    assert self_file.is_file()
    assert self_file.name == "snoot.self"
    assert (self_file.parent / "snoot.pkg").is_file()
    assert self_file.stat().st_size > 0
