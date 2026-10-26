"""CLI del Console Test Lab (T-202)."""
from __future__ import annotations

import argparse
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.ctl")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Compila el target (adapter pendiente)")
    p_build.add_argument("--target", required=True)

    p_run = sub.add_parser("run", help="Ejecuta un escenario (adapter pendiente)")
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
        print(f"adapter pendiente: run for target {args.target}", file=sys.stderr)
        return 2

    if args.command == "compare":
        from .scenario import load_scenario
        from .trace import compare_scenario
        from .report import write_report

        try:
            scen = load_scenario(args.scenario)
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        try:
            result = compare_scenario(scen, args.trace)
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        try:
            write_report(args.target, result, scen)
        except Exception as e:
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

        scen = None
        if args.scenario:
            try:
                scen = load_scenario(args.scenario)
            except Exception as e:
                print(f"error: {e}", file=sys.stderr)
                return 2
        try:
            p = write_report(args.target, scenario=scen)
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"report written to {p}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
