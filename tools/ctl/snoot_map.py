"""Tabla de equivalencia Snoot PS1 <-> Ren'Py (PLAN.md D17).

Corre ``compile_all`` de ``snoot-ps1`` dentro de ``build/`` (sin modificar ese
repo) y traduce ``text=<gid>`` al id de traduccion y ``who=<n>`` al nombre del
hablante que usa Ren'Py.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SNOOT_PS1 = Path(r"E:\Dev\snoot-ps1")
MAP_PATH = REPO / "build" / "ctl" / "snoot-map.json"
DEFAULT_OUT = REPO / "build" / "data"


def _run_compile_all(out: Path):
    ours = {k: sys.modules.pop(k) for k in list(sys.modules)
            if k == "tools" or k.startswith("tools.")}
    sys.path.insert(0, str(SNOOT_PS1))
    try:
        spec = importlib.util.spec_from_file_location(
            "snoot_compile", SNOOT_PS1 / "tools" / "script_compiler" / "compile.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        project, registry, result = mod.compile_all(out)
    finally:
        sys.path.remove(str(SNOOT_PS1))
        sys.modules.update(ours)
    return project, registry, result


def build_map(out: Path) -> dict:
    """Corre ``compile_all(out)`` y devuelve ``{"text": {gid: tid}, "speakers": {indice: nombre}}``."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    project, registry, result = _run_compile_all(out)
    if getattr(result, "errors", None):
        raise RuntimeError("; ".join(result.errors))
    meta_path = out / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    base_by_index = {ch["index"]: ch["text_base"] for ch in meta["chapters"]}

    text_map: dict = {}
    for idx, ir in result.irs.items():
        base = base_by_index[idx]
        for i, entry in enumerate(ir.strings):
            text_map[base + i] = entry["id"]

    speakers = {i: info.get("name", "") for i, info in enumerate(meta["speakers"])}
    return {"text": text_map, "speakers": speakers}


def load_map(out: Path = None) -> dict:
    """Lee ``build/ctl/snoot-map.json``; lo (re)genera si falta."""
    if out is None:
        out = DEFAULT_OUT
    out = Path(out)
    if MAP_PATH.exists():
        raw = json.loads(MAP_PATH.read_text(encoding="utf-8"))
        if isinstance(raw.get("text"), dict):
            raw["text"] = {int(k): v for k, v in raw["text"].items()}
        if isinstance(raw.get("speakers"), dict):
            raw["speakers"] = {int(k): v for k, v in raw["speakers"].items()}
        return raw
    m = build_map(out)
    MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    MAP_PATH.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    return m
