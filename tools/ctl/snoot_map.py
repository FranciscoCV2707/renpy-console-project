"""Tabla de equivalencia Snoot PS1 <-> Ren'Py (PLAN.md D17).

Corre ``compile_all`` de ``snoot-ps1`` dentro de ``build/`` (sin modificar ese
repo) y traduce ``text=<gid>`` al id de traduccion y ``who=<n>`` al nombre del
hablante que usa Ren'Py.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tomllib
from functools import cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SNOOT_PS1 = Path(r"E:\Dev\snoot-ps1")
MAP_PATH = REPO / "build" / "ctl" / "snoot-map.json"
COMPILE_OUT = REPO / "build" / "ctl" / "snoot-ps1-data"
KIT_GAME = Path("E:/Dev/renpy-port-kit/juegos/snoot/game.toml")


def _run_compile_all(out: Path):
    """compile.py importa el paquete tools de snoot-ps1: mientras corre se quita el de este repo de sys.modules."""
    ours = {k: sys.modules.pop(k) for k in list(sys.modules) if k == "tools" or k.startswith("tools.")}
    sys.path.insert(0, str(SNOOT_PS1))
    try:
        spec = importlib.util.spec_from_file_location(
            "snoot_compile", SNOOT_PS1 / "tools" / "script_compiler" / "compile.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.compile_all(out)
    finally:
        sys.path.remove(str(SNOOT_PS1))
        sys.modules.update(ours)


def build_map(out: Path) -> dict:
    """Corre ``compile_all(out)`` y devuelve las equivalencias TRACE del compilador."""
    out.mkdir(parents=True, exist_ok=True)
    _, _, result = _run_compile_all(out)
    if result.errors:
        raise ValueError("el compilador de snoot-ps1 fallo: " + "; ".join(result.errors))
    meta_path = out / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    base_by_index = {ch["index"]: ch["text_base"] for ch in meta["chapters"]}

    text_map: dict = {}
    for idx, ir in result.irs.items():
        base = base_by_index[idx]
        for i, entry in enumerate(ir.strings):
            text_map[base + i] = entry["id"]

    speakers = {i: info.get("name", "") for i, info in enumerate(meta["speakers"])}
    images = {
        i: entry.get("names", [])
        for i, entry in enumerate(meta["images"])
        if entry is not None and entry.get("names")
    }
    tracks = {i: entry["path"] for i, entry in enumerate(meta["audio"]) if "path" in entry}
    tags = {int(i): name for i, name in meta["tags"].items()}
    return {"text": text_map, "speakers": speakers, "images": images, "tracks": tracks, "tags": tags}


def load_map() -> dict:
    """Lee ``build/ctl/snoot-map.json``; si falta, lo arma con el compilador (unos segundos) y lo guarda."""
    if not MAP_PATH.exists():
        MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        MAP_PATH.write_text(json.dumps(build_map(COMPILE_OUT), ensure_ascii=False), encoding="utf-8")
    raw = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    if not {"images", "tracks", "tags"}.issubset(raw):
        raw = build_map(COMPILE_OUT)
        MAP_PATH.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    # JSON guarda las claves como texto
    return {name: {int(k): v for k, v in table.items()} for name, table in raw.items()}


@cache
def load_spanish() -> dict:
    """Texto en español de cada id de traducción (game/tl/es del juego publicado): lo que se ve en pantalla, sin el
    hablante ni los espacios de los bordes. Dos líneas con el mismo texto se ven igual aunque su id sea otro."""
    game = Path(tomllib.loads(KIT_GAME.read_text(encoding="utf-8"))["paths"]["game"])
    lines, current = {}, None
    for path in sorted((game / "tl" / "es").rglob("*.rpy")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if m := re.match(r"translate es (\w+):", line):
                current = m.group(1)
            elif current and (m := re.search(r'"(.*)"\s*(?:with \w+)?$', line)) and not line.lstrip().startswith("#"):
                lines[current] = m.group(1).strip()
                current = None
    return lines
