"""Inventario, copia y manifiesto de recursos para un perfil de assetpipe."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Iterable

from .profiles import PROFILES

# Extensiones consideradas recurso, por tipo.
_KIND_BY_EXT: dict[str, str] = {
    # Imagenes
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".gif": "image",
    ".bmp": "image",
    ".tif": "image",
    ".tiff": "image",
    ".ico": "image",
    ".svg": "image",
    # Audio
    ".ogg": "audio",
    ".wav": "audio",
    ".mp3": "audio",
    ".flac": "audio",
    ".opus": "audio",
    ".m4a": "audio",
    ".aac": "audio",
    # Video
    ".webm": "video",
    ".mp4": "video",
    ".avi": "video",
    ".mov": "video",
    ".mkv": "video",
    ".ogv": "video",
    ".m4v": "video",
    # Fuentes
    ".ttf": "font",
    ".otf": "font",
}

# Carpetas de cache que se ignoran siempre.
_CACHE_DIR_NAMES = {"__pycache__", "cache", ".cache", "renpy_cache"}

# Directorios de nivel superior del juego que se recorren como recursos.
_RESOURCE_ROOTS = {"images", "audio", "video", "movies"}


def _is_cached(parts: tuple[str, ...]) -> bool:
    return any(part.lower() in _CACHE_DIR_NAMES for part in parts)


def classify_kind(rel_path) -> str | None:
    """Devuelve el tipo de recurso para una ruta relativa, o None si no es recurso."""
    path = Path(rel_path)
    parts = path.parts
    if not parts or _is_cached(parts):
        return None
    ext = path.suffix.lower()
    if ext in (".rpy", ".rpyc"):
        return None
    if parts and parts[0].lower() in _RESOURCE_ROOTS:
        return _KIND_BY_EXT.get(ext)
    # Fuentes en cualquier carpeta.
    if ext in (".ttf", ".otf"):
        return "font"
    return None


def inventory(game_dir) -> list[Path]:
    """Lista ordenada de rutas relativas (Path) de recursos del juego."""
    game_dir = Path(game_dir)
    found: list[Path] = []
    for path in game_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(game_dir)
        kind = classify_kind(rel)
        if kind is not None:
            found.append(rel)
    found.sort(key=lambda p: p.as_posix())
    return found


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_resources(game_dir, out_dir, resources: Iterable) -> None:
    """Copia los recursos al directorio de salida."""
    game_dir = Path(game_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for rel in resources:
        rel = Path(rel)
        src = game_dir / rel
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


def build_manifest(profile: str, game_dir, resources: Iterable) -> dict:
    """Construye el diccionario del manifiesto (sin escribirlo)."""
    game_dir = Path(game_dir)
    entries = []
    for rel in resources:
        rel = Path(rel)
        full = game_dir / rel
        entries.append(
            {
                "path": rel.as_posix(),
                "kind": classify_kind(rel),
                "bytes": full.stat().st_size,
                "sha256": sha256_file(full),
            }
        )
    return {
        "profile": profile,
        "count": len(entries),
        "resources": entries,
    }


def _is_out_inside_game(game_dir: Path, out_dir: Path) -> bool:
    try:
        out_dir.resolve().relative_to(game_dir.resolve())
        return True
    except ValueError:
        return False


def run(profile: str, game, out) -> dict:
    """Ejecuta el pipeline completo y devuelve el manifiesto."""
    if profile not in PROFILES:
        raise ValueError(
            f"perfil desconocido: {profile} (disponibles: {', '.join(sorted(PROFILES))})"
        )
    game_dir = Path(game)
    out_dir = Path(out)
    if not game_dir.is_dir():
        raise ValueError(f"no existe el directorio de juego: {game_dir}")
    if _is_out_inside_game(game_dir, out_dir):
        raise ValueError("--out no puede estar dentro de --game")
    resources = inventory(game_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    copy_resources(game_dir, out_dir, resources)
    manifest = build_manifest(profile, game_dir, resources)
    manifest_path = out_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    return manifest
