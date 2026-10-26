#!/usr/bin/env python3
"""doctor.py - Diagnostico del entorno de renpy-console-project."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# (nombre, ejecutable, args, obligatorio)
CHECKS = [
    ("Git", "git", ["--version"], True),
    ("Python", "python", ["--version"], True),
    ("Node.js", "node", ["--version"], True),
    ("npm", "npm", ["--version"], True),
    ("uv", "uv", ["--version"], True),
    ("Docker", "docker", ["--version"], True),
    ("FFmpeg", "ffmpeg", ["-version"], True),
    ("CMake", "cmake", ["--version"], False),
    ("Ninja", "ninja", ["--version"], True),
    ("GitHub CLI", "gh", ["--version"], False),
    ("GCC (ucrt64)", r"C:\msys64\ucrt64\bin\gcc.exe", ["--version"], True),
    ("Clangd (ucrt64)", r"C:\msys64\ucrt64\bin\clangd.exe", ["--version"], False),
    ("PS1 GCC", r"C:\msys64\usr\local\psn00bsdk\bin\mipsel-none-elf-gcc.exe", ["--version"], True),
    ("Pyright", "pyright", ["--version"], False),
    ("Claude Code", "claude", ["--version"], True),
    ("Codex", "codex", ["--version"], True),
    ("OpenCode", "opencode", ["--version"], True),
    ("Kilo CLI", "kilo", ["--version"], True),
    ("Mistral Vibe", "vibe", ["--version"], True),
    ("Antigravity CLI", "agy", ["--version"], False),
    ("Orca CLI", r"C:\Users\Pako\AppData\Local\Programs\orca\resources\bin\orca.exe", ["status", "--json"], False),
]

SMOKE = [
    ("Beam", ["opencode", "run", "-m", "opencode-go/beam-free", "Responde solo: OK"]),
    ("Codex", ["codex", "exec", "Responde solo: OK"]),
    ("Kilo", ["kilo", "run", "--auto", "Responde solo: OK"]),
    ("Vibe", ["vibe", "--prompt", "Responde solo: OK", "--max-turns", "1"]),
    ("Claude", ["claude", "-p", "Responde solo: OK"]),
]

PATH_CHECKS = [
    ("SDL2 (ucrt64)", r"C:\msys64\ucrt64\bin\sdl2-config", False),
    ("DuckStation", r"E:\snoot\duckstation-windows-x64-release\duckstation-qt-x64-ReleaseLTCG.exe", False),
    ("PCSX-Redux", None, False),  # resuelto con glob
    ("BIOS PS1", r"E:\snoot\ps1 bios\SCPH1001.BIN", False),
    ("Datos VNB", r"E:\Dev\wani-ps1\build\fase0\C00.VNB", False),
]


def run(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    exe = shutil.which(cmd[0])
    if not exe:
        return 127, "no encontrado en PATH"
    try:
        p = subprocess.run(
            [exe, *cmd[1:]],
            capture_output=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return 124, f"timeout tras {timeout}s"
    except OSError as exc:
        return 126, str(exc)
    out = p.stdout
    err = p.stderr
    if isinstance(out, (bytes, bytearray)):
        out = out.decode("utf-8", errors="replace")
    if isinstance(err, (bytes, bytearray)):
        err = err.decode("utf-8", errors="replace")
    text = ((out or "") + "\n" + (err or "")).replace("\x00", "").strip()
    return p.returncode, text


def _pcsx_path() -> Path:
    base = Path(r"E:\snoot")
    matches = sorted(base.glob("pcsx-redux-nightly-*/pcsx-redux.exe"))
    if matches:
        return matches[0]
    return base / "pcsx-redux.exe"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)

    missing_required: list[str] = []

    print("== Herramientas ==")
    for name, exe, vargs, required in CHECKS:
        code, out = run([exe, *vargs])
        ok = code == 0
        first = out.splitlines()[0][:70] if out else ""
        mark = "OK " if ok else ("FALTA" if required else "opc ")
        print(f"[{mark}] {name:<24} {first}")
        if not ok and required:
            missing_required.append(name)

    print("\n== Comprobaciones extra ==")
    if sys.version_info < (3, 12):
        print("[FALTA] Python >= 3.12 (activa el .venv)")
        missing_required.append("Python 3.12")
    else:
        print(f"[OK ] Python {sys.version.split()[0]}")

    code, _ = run(["docker", "info"], timeout=20)
    print(f"[{'OK ' if code == 0 else 'FALTA'}] Docker daemon en marcha")
    if code != 0:
        missing_required.append("Docker daemon")

    code, out = run(["git", "config", "--global", "core.longpaths"])
    longpaths = (out or "").strip()
    mark = "OK " if longpaths == "true" else "aviso"
    print(f"[{mark}] git core.longpaths = {longpaths or '(sin definir)'}")

    code, out = run(["opencode", "models"], timeout=60)
    has_beam = "beam-free" in (out or "")
    mark = "OK " if has_beam else "aviso"
    print(f"[{mark}] Beam listado en opencode-go: {'si' if has_beam else 'no'}")

    print("\n== Rutas ==")
    for name, path, required in PATH_CHECKS:
        if path is None:
            resolved = _pcsx_path()
        else:
            resolved = Path(path)
        ok = resolved.exists()
        mark = "OK " if ok else ("FALTA" if required else "opc ")
        print(f"[{mark}] {name:<24} {resolved}")
        if not ok and required:
            missing_required.append(name)

    if args.smoke:
        print("\n== Smoke test de agentes (usa un poco de cuota) ==")
        for name, cmd in SMOKE:
            code, out = run(cmd, timeout=180)
            ok = code == 0 and "ok" in (out or "").lower()
            last = (out or "").splitlines()[-1][:60] if out else ""
            print(f"[{'OK ' if ok else 'FALLA'}] {name:<8} exit={code} {last}")

    if missing_required:
        print(f"\nFaltan obligatorios: {', '.join(missing_required)}")
        return 1
    print("\nEntorno listo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
