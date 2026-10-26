"""Escritura de reportes Markdown del Test Lab."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .scenario import Scenario
from .trace import CompareResult


def report_path(target: str, root: Path | None = None) -> Path:
    return (root or Path(".")) / "build" / "ctl" / target / "report.md"


def _divergent(result: CompareResult | None) -> str:
    if result is None:
        return "(none)"
    parts = []
    if result.actual is not None:
        parts.append(f"actual={result.actual.ev} {result.actual.fields}")
    if result.reference is not None:
        parts.append(f"reference={result.reference.ev} {result.reference.fields}")
    if not parts:
        return result.message or "(none)"
    return "; ".join(parts) + (f" ({result.message})" if result.message else "")


def write_report(target: str, result: CompareResult | None = None, scenario: Scenario | None = None,
                 root: Path | None = None) -> Path:
    path = report_path(target, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Test Lab Report — {target}",
        "",
        f"- **Verdict:** {result.verdict if result else 'PENDING'}",
        f"- **Scenario:** {scenario.id if scenario else '(none)'}",
        f"- **First divergent event:** {_divergent(result)}",
        f"- **Generated:** {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
