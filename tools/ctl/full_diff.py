"""Agrupa diferencias de ``renpy_full`` por campo y valores."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .snoot_map import load_map, load_spanish
from .trace import engine_background_names, normalize_engine_full, normalize_renpy_full, parse_file

REPO = Path(__file__).resolve().parents[2]
DEFAULT_REFERENCE = REPO / "tests" / "reference" / "traces" / "snoot" / "chapter_x2.trace"


def diff_rows(actual, reference) -> tuple[int, list[dict]]:
    """Devuelve SAY alineados con diferencias y filas agrupadas por campo/valores."""
    counts = Counter()
    for left, right in zip(actual, reference):
        for field in sorted(set(left.fields) | set(right.fields)):
            actual_value = left.fields.get(field)
            reference_value = right.fields.get(field)
            if actual_value != reference_value:
                key = (field, json.dumps(actual_value, ensure_ascii=False, sort_keys=True),
                       json.dumps(reference_value, ensure_ascii=False, sort_keys=True))
                counts[key] += 1
    rows = [
        {"field": field, "actual": json.loads(actual_value), "reference": json.loads(reference_value), "count": count}
        for (field, actual_value, reference_value), count in sorted(counts.items())
    ]
    return sum(counts.values()), rows


def compare_files(engine_path: Path, renpy_path: Path = DEFAULT_REFERENCE) -> tuple[int, list[dict]]:
    """Normaliza y agrupa las diferencias entre una traza de motor y Ren'Py."""
    snoot_map = load_map()
    spanish = load_spanish()
    engine_events = parse_file(engine_path)
    engine = normalize_engine_full(engine_events, snoot_map, spanish)
    renpy = normalize_renpy_full(parse_file(renpy_path), spanish,
                                 engine_background_names(engine_events, snoot_map))
    return diff_rows(engine, renpy)


def format_table(path: Path, difference_count: int, rows: list[dict]) -> str:
    lines = [f"{path}: {difference_count} diferencias de campo", "| Campo | Motor | Ren'Py | SAY |",
             "|---|---|---|---:|"]
    lines.extend(f"| {row['field']} | `{row['actual']}` | `{row['reference']}` | {row['count']} |" for row in rows)
    if not rows:
        lines.append("| — | — | — | 0 |")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine_trace", type=Path, help="Traza TRACE del motor")
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE,
                        help="Traza TRACE Ren'Py (por defecto: chapter_x2)")
    args = parser.parse_args(argv)
    difference_count, rows = compare_files(args.engine_trace, args.reference)
    print(format_table(args.engine_trace, difference_count, rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
