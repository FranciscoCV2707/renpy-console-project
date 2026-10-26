"""Ejecuta Snoot original en Ren'Py y guarda la traza de referencia (T-302).

Corre ``python -m tools.renpy_trace.record [--route <nombre>]``. Sin ``--route`` recorre
todas las rutas de ``reporte/rutas.json``. Reutiliza ``renpy-port-kit/renpykit/compare/capture.py``
(solo lectura) para preparar la copia, lanzar el juego y seguir una ruta.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PORT_KIT = Path("E:/Dev/renpy-port-kit")
DEFAULT_SNOOT_FOLDER = DEFAULT_PORT_KIT / "juegos" / "snoot"
DEFAULT_BUILD_DIR = ROOT / "build" / "renpy" / "snoot"
DEFAULT_TRACE_DIR = ROOT / "tests" / "reference" / "traces" / "snoot"
DEFAULT_ROUTES = DEFAULT_SNOOT_FOLDER / "reporte" / "rutas.json"
HOOK = Path(__file__).with_name("trace_hook.rpy")

__all__ = [
    "prepare_copy",
    "prepare_game_copy",
    "make_copy",
    "copy_game",
    "capture_settings",
    "launch_command",
    "run_route",
    "load_routes",
    "record",
    "record_route",
    "record_all",
    "main",
]


def _import_port_kit(port_kit=None):
    base = Path(port_kit) if port_kit else DEFAULT_PORT_KIT
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    from renpykit.compare.capture import (  # pylint: disable=import-error
        prepare_copy as _port_prepare_copy,
        launch_command as _port_launch_command,
        run_route as _port_run_route,
        capture_settings as _port_capture_settings,
        safe_name as _port_safe_name,
    )
    return _port_prepare_copy, _port_launch_command, _port_run_route, _port_capture_settings, _port_safe_name


try:
    (_port_prepare_copy, _port_launch_command, _port_run_route,
     _port_capture_settings, _port_safe_name) = _import_port_kit()
except (ImportError, ModuleNotFoundError, OSError):  # pragma: no cover - entorno sin port-kit
    _port_prepare_copy = None
    _port_launch_command = None
    _port_run_route = None
    _port_capture_settings = None
    _port_safe_name = None


def _ensure_port_kit(port_kit=None):
    global _port_prepare_copy, _port_launch_command, _port_run_route
    global _port_capture_settings, _port_safe_name
    if _port_prepare_copy is not None and port_kit is None:
        return
    (prep, launch, run, settings, safe) = _import_port_kit(port_kit)
    _port_prepare_copy = prep
    _port_launch_command = launch
    _port_run_route = run
    _port_capture_settings = settings
    _port_safe_name = safe


# Re-exported names (patchable from tests).
def capture_settings(folder):
    _ensure_port_kit()
    return _port_capture_settings(Path(folder))


def launch_command(settings, copy):
    _ensure_port_kit()
    return _port_launch_command(settings, Path(copy))


def run_route(command, copy, name, route, out_root, *args, **kwargs):
    _ensure_port_kit()
    return _port_run_route(command, Path(copy), name, route, Path(out_root), *args, **kwargs)


def safe_name(text):
    _ensure_port_kit()
    return _port_safe_name(text)


def prepare_copy(game_dir, target, fresh=False, hook_path=None, port_kit=None):
    """Copia del juego + ``trace_hook.rpy`` en ``game/`` (ademas de ``kit_capture.rpy``)."""
    _ensure_port_kit(port_kit)
    target = Path(target)
    result = _port_prepare_copy(Path(game_dir), target, fresh=fresh)
    result = Path(result)
    hook = Path(hook_path) if hook_path is not None else HOOK
    game_game = result / "game"
    game_game.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(hook, game_game / "trace_hook.rpy")
    return result


# Aliases para compatibilidad con nombres probables en pruebas.
prepare_game_copy = prepare_copy
make_copy = prepare_copy
copy_game = prepare_copy


class UnknownRouteError(ValueError):
    """Ruta no presente en ``rutas.json``."""


def load_routes(routes_path=None, port_kit=None):
    pk = Path(port_kit) if port_kit is not None else DEFAULT_PORT_KIT
    path = Path(routes_path) if routes_path is not None else (pk / "juegos" / "snoot" / "reporte" / "rutas.json")
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("rutas.json debe ser un objeto nombre -> ruta")
    return data


def _read_game_dir(snoot_folder):
    snoot_folder = Path(snoot_folder)
    toml_path = snoot_folder / "game.toml"
    with toml_path.open("rb") as fh:
        data = tomllib.load(fh)
    return Path(data["paths"]["game"])


def _event_counts(trace_path):
    try:
        from tools.ctl.trace import parse_file
    except (ImportError, ModuleNotFoundError):
        return {}
    try:
        events = parse_file(trace_path)
    except (OSError, ValueError):
        return {}
    counts = {}
    for ev in events:
        counts[ev.ev] = counts.get(ev.ev, 0) + 1
    return counts


def record(route=None, *, routes=None, route_names=None, snoot_folder=None,
          build_dir=None, trace_dir=None, game_dir=None, port_kit=None,
          fresh=True, timeout=3600, wait=0.2):
    """Graba una o varias rutas. Devuelve lista de resultados (uno por ruta)."""
    pk = Path(port_kit) if port_kit is not None else DEFAULT_PORT_KIT
    sf = Path(snoot_folder) if snoot_folder is not None else (pk / "juegos" / "snoot")
    bd = Path(build_dir) if build_dir is not None else DEFAULT_BUILD_DIR
    td = Path(trace_dir) if trace_dir is not None else DEFAULT_TRACE_DIR

    all_routes = routes if routes is not None else load_routes(None, pk)
    if not isinstance(all_routes, dict):
        raise ValueError("routes debe ser un dict nombre -> ruta")

    if route is None and route_names is None:
        requested = list(all_routes.keys())
    elif route is None:
        requested = list(route_names)
    elif isinstance(route, str):
        requested = [r.strip() for r in route.split(",") if r.strip()]
    else:
        requested = list(route)

    for name in requested:
        if name not in all_routes:
            raise UnknownRouteError(f"ruta desconocida: {name}")

    settings = capture_settings(sf)
    settings = dict(settings)
    if wait is not None:
        settings["wait"] = wait

    if game_dir is None:
        game_dir = _read_game_dir(sf)
    game_dir = Path(game_dir)

    copy_dir = bd / "juego"
    copy = prepare_copy(game_dir, copy_dir, fresh=fresh, port_kit=pk)
    command = launch_command(settings, copy)

    out_root = bd / "captura"
    out_root.mkdir(parents=True, exist_ok=True)
    td.mkdir(parents=True, exist_ok=True)

    results = []
    for name in requested:
        route_data = all_routes[name]
        os.environ["RCP_TRACE_OUT"] = str(out_root / (safe_name(name) + ".trace"))
        started = time.monotonic()
        result = run_route(command, copy, name, route_data, out_root,
                           timeout=timeout, settings=settings)
        elapsed = time.monotonic() - started
        raw_trace = Path(os.environ["RCP_TRACE_OUT"])
        dest_trace = td / (name + ".trace")
        if raw_trace.exists():
            shutil.copyfile(raw_trace, dest_trace)
        result = dict(result)
        result["elapsed_seconds"] = round(elapsed, 2)
        result["trace"] = str(dest_trace)
        result["event_counts"] = _event_counts(dest_trace)
        results.append(result)
        print(f"{name}: {result.get('status')} en {elapsed:.1f}s -> {dest_trace}")
        counts = result["event_counts"]
        if counts:
            print("  eventos: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return results


def record_route(name, **kwargs):
    return record(name, **kwargs)


def record_all(**kwargs):
    return record(None, **kwargs)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.renpy_trace.record",
        description="Graba trazas de referencia de Snoot desde Ren'Py.",
    )
    parser.add_argument("--route", default=None,
                        help="nombre de la ruta (sin este flag: todas)")
    parser.add_argument("--port-kit", default=None, help="carpeta raiz de renpy-port-kit")
    parser.add_argument("--snoot-folder", default=None, help="carpeta del juego en el kit (juegos/snoot)")
    parser.add_argument("--build-dir", default=None, help="carpeta build/renpy/snoot")
    parser.add_argument("--trace-dir", default=None, help="carpeta de salida de trazas")
    parser.add_argument("--game-dir", default=None, help="carpeta game del juego publicado")
    parser.add_argument("--timeout", type=int, default=3600, help="timeout por ruta en segundos")
    parser.add_argument("--wait", type=float, default=0.2, help="segundos de espera por linea")
    parser.add_argument("--no-fresh", action="store_true", help="no borrar la copia existente")
    parser.add_argument("--list", action="store_true", help="listar rutas y salir")

    args = parser.parse_args(argv)

    pk = Path(args.port_kit) if args.port_kit else DEFAULT_PORT_KIT
    sf = Path(args.snoot_folder) if args.snoot_folder else (pk / "juegos" / "snoot")

    try:
        all_routes = load_routes(None, pk) if args.snoot_folder is None and args.port_kit is None else load_routes(
            sf / "reporte" / "rutas.json" if (sf / "reporte" / "rutas.json").exists() else None, pk)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.list:
        for name in all_routes:
            print(name)
        return 0

    try:
        record(args.route, port_kit=pk, snoot_folder=sf,
               build_dir=args.build_dir, trace_dir=args.trace_dir,
               game_dir=args.game_dir, fresh=not args.no_fresh,
               timeout=args.timeout, wait=args.wait)
    except UnknownRouteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
