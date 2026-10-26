#!/usr/bin/env python3
"""Copia las skills del proyecto (.agents/skills/<nombre>/SKILL.md) a .claude/skills/.

Codex, OpenCode (Beam), Kilo, Vibe y Antigravity leen .agents/skills directamente (probado el 2026-10-26);
Claude Code solo lee .claude/skills. Las skills se editan en .agents/skills y se corre este script.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sync(src_root: Path, dst_root: Path) -> list[str]:
    """Copia cada skill de src_root a dst_root reemplazando la copia anterior. Devuelve los nombres copiados."""
    names = []
    dst_root.mkdir(parents=True, exist_ok=True)
    for skill in sorted(p for p in src_root.iterdir() if (p / "SKILL.md").exists()):
        dst = dst_root / skill.name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(skill, dst)
        names.append(skill.name)
    return names


def main() -> None:
    for name in sync(ROOT / ".agents" / "skills", ROOT / ".claude" / "skills"):
        print(f"[sync] {name} -> .claude/skills")


if __name__ == "__main__":
    main()
