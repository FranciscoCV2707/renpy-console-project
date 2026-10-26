"""Adapter PS1/PCSX-Redux para el Console Test Lab (T-203)."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[2]
VN_ENGINE = Path(r"E:\Dev\vn-engine-ps1")
SNOOT_PS1 = Path(r"E:\Dev\snoot-ps1")

try:
    from . import autotest as autotest
except ImportError:
    autotest = None


def _load_snoot():
    """Carga vn-engine-ps1/tests/emu/snoot.py como hace tests/emu/snoot_check.py."""
    global _snoot_cache
    if _snoot_cache is not None:
        return _snoot_cache
    spec = importlib.util.spec_from_file_location("vn_snoot_ps1", VN_ENGINE / "tests" / "emu" / "snoot.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no se puede cargar snoot.py desde {VN_ENGINE}")
    mod = importlib.util.module_from_spec(spec)
    saved_modules = {}
    for key in list(sys.modules):
        if key == "tools" or key.startswith("tools."):
            saved_modules[key] = sys.modules.pop(key)
    sys.path.insert(0, str(SNOOT_PS1))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.update(saved_modules)
    mod.REPO = REPO
    mod.BUILD = REPO / "build" / "ctl" / "ps1"
    _snoot_cache = mod
    return mod


_snoot_cache = None


def extract_trace(tty_text: str) -> str:
    """Devuelve solo las lineas de TTY que empiezan con ``T|``."""
    return "\n".join(line for line in tty_text.splitlines() if line.startswith("T|"))


def run_scenario(scenario, out_dir) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    snoot = _load_snoot()
    et = snoot.et

    autotest_mod = autotest
    if autotest_mod is None:
        from . import autotest as autotest_mod

    steps = autotest_mod.scenario_steps(scenario)
    bin_bytes = autotest_mod.autotest_bin(steps)

    engine = snoot.engine_dir("cur")
    et.ELF = engine / "build" / "snoot.elf"  # noqa

    cue = snoot.build_disc(REPO, bin_bytes, out / "disc")

    sym = et.symbols()
    names = ", ".join(f"'{arg}'" for _, action, arg in steps if action == "shot")
    last = max((f for f, _, _ in steps), default=0)
    lua_src = et.LUA % {
        "names": names,
        "outdir": out.as_posix(),
        "shot": sym["autotest_shot"],
        "quit": sym["autotest_quit"],
        "state": sym["state"],
        "vm": sym["vm"],
        "watch": ", ".join(f"{n} = {sym[n]}" for n in et.WATCH if n in sym),
        "failog": sym.get("res_fail_log", "nil"),
        "stalllog": sym.get("stall_log", "nil"),
        "synclog": sym.get("res_sync_log", "nil"),
        "triggers": et.parse_triggers(None),
        "max_frames": last + 3000,
    }
    lua = out / "emutest.lua"
    lua.write_text(lua_src, encoding="utf-8")

    args = [
        et.REDUX, "-no-ui", "-run", "-fastboot", "-bios", et.BIOS,
        "-iso", cue, "-memcard1", out / "card1.mcd",
        "-exec", f"dofile('{lua.as_posix()}')", "-stdout",
    ]

    tty_path = out / "tty.txt"
    with tty_path.open("wb") as tty_file:
        proc = subprocess.Popen(
            [str(a) for a in args],
            stdout=tty_file,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + float(getattr(scenario.limits, "max_seconds", 0) or 3600)
        final_at: Optional[float] = None
        while proc.poll() is None and time.monotonic() < deadline:
            if final_at is None and (out / "final.txt").exists():
                final_at = time.monotonic()
            if final_at is not None and time.monotonic() - final_at > 30:
                break
            time.sleep(1)
        if proc.poll() is None:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
            )
            proc.wait()

    tty_text = tty_path.read_bytes().decode("utf-8", errors="replace")
    trace_text = extract_trace(tty_text)
    trace_path = out / "trace.txt"
    trace_path.write_text(trace_text, encoding="utf-8")
    return trace_path
