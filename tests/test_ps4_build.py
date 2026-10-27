"""Pruebas de compilacion de Snoot para PS4 (T-606)."""
from __future__ import annotations

import shutil
import subprocess

import pytest

# Compilan en Docker (minutos): solo con `pytest -m consoles`
pytestmark = pytest.mark.consoles

from platforms.ps4.build import build


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return res.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


@pytest.mark.skipif(not _docker_available(), reason="Docker no disponible")
def test_ps4_build_package() -> None:
    pkg = build(trace=True)
    assert pkg.is_file()
    assert (pkg.parent / "eboot.bin").is_file()
    assert (pkg.parent / "IV0000-SNOT00001_00-SNOOTGAME0000000.pkg").is_file()


@pytest.mark.skipif(not _docker_available(), reason="Docker no disponible")
def test_ps4_elf_without_sce_libc_mspace() -> None:
    """El asignador propio (T-616) deja el ELF sin sceLibcMspace*: shadPS4 los tiene como stubs."""
    elf = build(trace=True).parent / "snoot.elf"
    assert elf.is_file()
    assert b"sceLibcMspace" not in elf.read_bytes()
