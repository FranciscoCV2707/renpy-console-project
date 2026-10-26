"""Escritura de reportes Markdown del Test Lab."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path


def report_path(target, root=None) -> Path:
    base = Path(root) if root is not None else Path(".")
    return base / "build" / "ctl" / str(target) / "report.md"


def _format_divergent(fd) -> str:
    if fd is None:
        return "(none)"
    if isinstance(fd, str):
        return fd
    if hasattr(fd, "actual") and hasattr(fd, "reference"):
        parts = []
        a = getattr(fd, "actual", None)
        r = getattr(fd, "reference", None)
        if a is not None:
            parts.append(f"actual={getattr(a, 'ev', a)} {getattr(a, 'fields', {})}")
        if r is not None:
            parts.append(f"reference={getattr(r, 'ev', r)} {getattr(r, 'fields', {})}")
        if not parts:
            msg = getattr(fd, "message", None)
            return msg if msg else "(none)"
        msg = getattr(fd, "message", None)
        suffix = f" ({msg})" if msg else ""
        return "; ".join(parts) + suffix
    if hasattr(fd, "ev"):
        return f"{fd.ev} {getattr(fd, 'fields', {})}"
    return str(fd)


def write_report(target, verdict="PENDING", scenario=None, first_divergent=None,
                 root=None, **kwargs) -> Path:
    p = report_path(target, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(scenario, str):
        scen_str = scenario
    elif scenario is None:
        scen_str = "(none)"
    else:
        scen_str = getattr(scenario, "id", None)
        if scen_str is None and isinstance(scenario, dict):
            scen_str = scenario.get("id", "(none)")
        if scen_str is None:
            scen_str = str(scenario)
    fd_str = _format_divergent(first_divergent)
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


def generate_report(*args, **kwargs):
    return write_report(*args, **kwargs)