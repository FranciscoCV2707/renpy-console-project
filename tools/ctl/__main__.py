"""CLI del Console Test Lab (T-202, T-203)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def _invoke_run_scenario(scenario, out_dir):
    """Resuelve run_scenario permitiendo parches en ps1 o en este modulo (pruebas)."""
    main_mod = sys.modules[__name__]
    if "run_scenario" in main_mod.__dict__ and main_mod.run_scenario is not _invoke_run_scenario:
        return main_mod.run_scenario(scenario, out_dir)
    from . import ps1

    if hasattr(ps1, "run_scenario"):
        return ps1.run_scenario(scenario, out_dir)
    raise RuntimeError("run_scenario no disponible")


# Re-export for compatibility with tests that patch tools.ctl.__main__.run_scenario.
try:
    from .ps1 import run_scenario as run_scenario
except ImportError:
    run_scenario = _invoke_run_scenario


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.ctl")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Compila el target (adapter pendiente)")
    p_build.add_argument("--target", required=True)

    p_run = sub.add_parser("run", help="Ejecuta un escenario (adapter PS1)")
    p_run.add_argument("--target", required=True)
    p_run.add_argument("--scenario", default=None)
    p_run.add_argument("--suite", default=None)

    p_cmp = sub.add_parser("compare", help="Compara una traza contra la referencia del escenario")
    p_cmp.add_argument("--target", required=True)
    p_cmp.add_argument("--scenario", required=True)
    p_cmp.add_argument("--trace", required=True)

    p_rep = sub.add_parser("report", help="Escribe el reporte Markdown del target")
    p_rep.add_argument("--target", required=True)
    p_rep.add_argument("--scenario", default=None)

    args = parser.parse_args(argv)

    if args.command == "build":
        print(f"adapter pendiente: build for target {args.target}", file=sys.stderr)
        return 2

    if args.command == "run":
        if args.suite is not None:
            print("run --suite is still pending (no implementado)", file=sys.stderr)
            return 2
        if not args.scenario:
            print("error: --scenario is required", file=sys.stderr)
            return 2
        from .scenario import load_scenario
        from .trace import compare_scenario
        from .report import write_report

        try:
            scen = load_scenario(args.scenario)
        except (ValueError, OSError, yaml.YAMLError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2

        out_dir = Path("build") / "ctl" / args.target
        try:
            trace_path = _invoke_run_scenario(scen, out_dir)
        except (ImportError, OSError, RuntimeError, ValueError) as e:
            print(f"error: startup failed: {e}", file=sys.stderr)
            return 2

        try:
            result = compare_scenario(scen, trace_path)
            write_report(args.target, result, scen)
        except (ValueError, OSError, yaml.YAMLError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2

        print(result.message)
        print(f"verdict: {result.verdict}")
        return 0 if result.equal else 1

    if args.command == "compare":
        from .scenario import load_scenario
        from .trace import compare_scenario
        from .report import write_report

        try:
            scen = load_scenario(args.scenario)
            result = compare_scenario(scen, args.trace)
            write_report(args.target, result, scen)
        except (ValueError, OSError, yaml.YAMLError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(result.message)
        if result.actual is not None:
            print(f"actual:    {result.actual.ev} {result.actual.fields}")
        if result.reference is not None:
            print(f"reference: {result.reference.ev} {result.reference.fields}")
        return 0 if result.equal else 1

    if args.command == "report":
        from .scenario import load_scenario
        from .report import write_report

        try:
            scen = load_scenario(args.scenario) if args.scenario else None
            p = write_report(args.target, scenario=scen)
        except (ValueError, OSError, yaml.YAMLError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"report written to {p}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
