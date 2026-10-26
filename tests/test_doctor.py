"""Diagnostico del entorno (tools/doctor.py)."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import doctor  # noqa: E402


class FakeResult:
    def __init__(self, returncode=0, stdout="version 1.0", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _patch_all_present(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: name)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeResult())
    monkeypatch.setattr(Path, "exists", lambda self: True)


def test_all_present(monkeypatch):
    _patch_all_present(monkeypatch)
    assert doctor.main([]) == 0


def test_missing_required(monkeypatch):
    def which(name):
        return None if name == "git" else name

    monkeypatch.setattr(shutil, "which", which)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeResult())
    monkeypatch.setattr(Path, "exists", lambda self: True)
    assert doctor.main([]) == 1


def test_missing_optional(monkeypatch):
    def which(name):
        return None if name == "cmake" else name

    monkeypatch.setattr(shutil, "which", which)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeResult())
    monkeypatch.setattr(Path, "exists", lambda self: True)
    assert doctor.main([]) == 0


def test_run_missing_returns_127(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    assert doctor.run(["nope", "--version"]) == (127, "no encontrado en PATH")


def test_smoke_not_run_without_flag(monkeypatch):
    calls = []

    def fake_run(*a, **k):
        calls.append(a[0] if a else k.get("args"))
        return FakeResult(stdout="OK")

    monkeypatch.setattr(shutil, "which", lambda name: name)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(Path, "exists", lambda self: True)
    doctor.main([])
    assert not any("Responde solo: OK" in str(c) for c in calls)


def test_smoke_runs_with_flag(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: name)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeResult(stdout="OK"))
    monkeypatch.setattr(Path, "exists", lambda self: True)
    assert doctor.main(["--smoke"]) == 0
