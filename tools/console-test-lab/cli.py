"""Console Test Lab — CLI minimo (esqueleto).

Uso futuro:
  python -m console_test_lab build --target ps2
  python -m console_test_lab launch --target ps2 --game path
  python -m console_test_lab run --scenario tests/scenarios/snoot_intro.yaml
"""
import argparse
import sys


def cmd_build(args):
    print(f"[CTL] build target={args.target} (stub)")


def cmd_launch(args):
    print(f"[CTL] launch target={args.target} game={args.game} (stub)")


def cmd_run(args):
    print(f"[CTL] run scenario={args.scenario} (stub)")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Console Test Lab")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build")
    p.add_argument("--target", required=True)
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("launch")
    p.add_argument("--target", required=True)
    p.add_argument("--game", required=True)
    p.set_defaults(func=cmd_launch)

    p = sub.add_parser("run")
    p.add_argument("--scenario", required=True)
    p.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
