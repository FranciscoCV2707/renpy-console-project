"""Graba las trazas de referencia de Snoot corriendo el juego original en Ren'Py (T-302).

    python -m tools.renpy_trace.record [--route NOMBRE ...]

Usa la captura de renpy-port-kit (renpykit/compare/capture.py, solo lectura): copia el juego publicado a
build/renpy/snoot/juego con kit_capture.rpy, que sigue las decisiones de cada ruta de reporte/rutas.json, y le agrega
trace_hook.rpy. Cada ruta deja tests/reference/traces/snoot/<ruta>.trace; las capturas de pantalla quedan en build/.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import tomllib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORT_KIT = Path(r"E:\Dev\renpy-port-kit")
GAME_FOLDER = PORT_KIT / "juegos" / "snoot"
BUILD = ROOT / "build" / "renpy" / "snoot"
TRACES = ROOT / "tests" / "reference" / "traces" / "snoot"
HOOK = Path(__file__).with_name("trace_hook.rpy")
SNOOT_CAPTURE = Path(__file__).with_name("snoot_capture.rpy")
# Snoot se porta solo en español (PLAN.md D16): la referencia sale de la traducción oficial game/tl/es
LANGUAGE = "es"

sys.path.insert(0, str(PORT_KIT))
from renpykit.compare import capture  # noqa: E402


def load_routes(folder: Path = GAME_FOLDER) -> dict:
    return json.loads((folder / "reporte" / "rutas.json").read_text(encoding="utf-8"))


def prepare_copy(game_dir: Path, target: Path) -> Path:
    copy = capture.prepare_copy(game_dir, target)
    shutil.copyfile(HOOK, copy / "game" / "trace_hook.rpy")
    shutil.copyfile(SNOOT_CAPTURE, copy / "game" / "zz_rcp_snoot_capture.rpy")
    return copy


def record(names: list[str], routes: dict, folder: Path = GAME_FOLDER, build: Path = BUILD, traces: Path = TRACES,
           wait: float = 0.2) -> list[str]:
    """Graba las rutas y devuelve las que no terminaron; su traza parcial queda en build/, no en las referencias."""
    unknown = [n for n in names if n not in routes]
    if unknown:
        raise ValueError(f"ruta desconocida: {', '.join(unknown)} (hay: {', '.join(routes)})")
    # Menos espera por línea que la captura normal (0.7 s): la traza no depende de las capturas de pantalla
    settings = dict(capture.capture_settings(folder), wait=wait)
    game_dir = Path(tomllib.loads((folder / "game.toml").read_text(encoding="utf-8"))["paths"]["game"])
    copy = prepare_copy(game_dir, build / "juego")
    command = capture.launch_command(settings, copy)
    traces.mkdir(parents=True, exist_ok=True)
    failed = []
    for name in names:
        raw = build / f"{name}.trace"
        raw.unlink(missing_ok=True)
        os.environ["RCP_TRACE_OUT"] = str(raw)
        start = time.monotonic()
        result = capture.run_route(command, copy, name, routes[name], build / "captura", LANGUAGE,
                                   settings=settings)
        # Ren'Py escribe en modo texto (CRLF en Windows); la referencia se guarda con LF
        lines = raw.read_text(encoding="utf-8").splitlines() if raw.exists() else []
        counts = Counter(line.split("|")[3] for line in lines)
        print(f"{name}: {result.get('status')} en {time.monotonic() - start:.0f} s, "
              + ", ".join(f"{ev}={n}" for ev, n in sorted(counts.items())))
        if result.get("status") == "ok":
            (traces / f"{name}.trace").write_text("".join(f"{line}\n" for line in lines), encoding="utf-8",
                                                  newline="\n")
        else:
            failed.append(name)
    return failed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.renpy_trace.record")
    parser.add_argument("--route", nargs="+", help="rutas de reporte/rutas.json (sin esto: todas)")
    args = parser.parse_args(argv)
    routes = load_routes()
    try:
        failed = record(args.route or list(routes), routes)
    except (ValueError, OSError, capture.CaptureError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if failed:
        print(f"sin terminar (no se guardaron): {', '.join(failed)}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
