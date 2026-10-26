"""Escritura de reportes Markdown del Test Lab."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .trace import CompareResult
from .scenario import Scenario


def report_path(target, root=None) -> Path:
    base = Path(root) if root is not None else Path(".")
    return base / "build" / "ctl" / str(target) / "report.md"


def _format_divergent(fd):
    if fd is None:
        return "(none)"
    if isinstance(fd, str):
        return fd
    if isinstance(fd, CompareResult):
        parts = []
        if fd.actual is not None:
            parts.append(f"actual={fd.actual.ev} {fd.actual.fields}")
        if fd.reference is not None:
            parts.append(f"reference={fd.reference.ev} {fd.reference.fields}")
        if not parts:
            return fd.message if fd.message else "(none)"
        suffix = f" ({fd.message})" if fd.message else ""
        return "; ".join(parts) + suffix
    return f"{fd.ev} {fd.fields}"


def write_report(target, result=None, scenario=None, root=None,
                 verdict=None, first_divergent=None, compare_result=None) -> Path:
    if compare_result is not None:
        result = compare_result
    if first_divergent is not None and result is None:
        result = first_divergent
    if verdict is None:
        if isinstance(result, CompareResult):
            verdict = result.verdict
        else:
            verdict = "PENDING"
    if isinstance(scenario, str):
        scen_str = scenario
    elif scenario is None:
        scen_str = "(none)"
    elif isinstance(scenario, Scenario):
        scen_str = scenario.id
    else:
        scen_str = str(scenario)
    fd = result if isinstance(result, CompareResult) else first_divergent
    fd_str = _format_divergent(fd)
    p = report_path(target, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Test Lab Report — {target}",
        "",
        f"- **Verdict:** {verdict}",
        f"- **Scenario:** {scen_str}",
        f"- **First divergent event:** {fd_str}",
        f"- **Generated:** {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    p.write_text("\n".join(lines), encoding="utf-8")
    return p
