"""Configuracion de agentes, despachador y sincronizacion de skills."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "agents"))

import dispatch  # noqa: E402
import sync_skills  # noqa: E402


def test_every_agent_command_takes_the_prompt():
    cfg = dispatch.load_cfg()
    assert cfg["agents"], "agents.toml sin agentes"
    for name, agent in cfg["agents"].items():
        assert "{prompt}" in agent["cmd"], name


def test_prompt_template_is_safe_for_npm_cmd_shims():
    prompt = dispatch.load_cfg()["settings"]["prompt_template"].format(task="T-001", agent="beam")
    assert not dispatch.CMD_UNSAFE.intersection(prompt)
    assert "AGENTS.md" in prompt and ".agents/inbox/T-001.md" in prompt


def test_build_cmd_fills_placeholders(monkeypatch, tmp_path):
    monkeypatch.setattr(dispatch, "resolve_exe", lambda name: name + ".exe")
    cmd = dispatch.build_cmd({"cmd": ["codex", "-C", "{worktree}", "--add-dir", "{gitdir}", "{prompt}"]}, "hola",
                             tmp_path)
    assert cmd == ["codex.exe", "-C", str(tmp_path), "--add-dir", str(ROOT / ".git"), "hola"]


def test_build_cmd_rejects_unsafe_prompt_for_cmd_shims(monkeypatch, tmp_path):
    monkeypatch.setattr(dispatch, "resolve_exe", lambda name: name + ".CMD")
    monkeypatch.setattr(dispatch.os, "name", "nt")
    with pytest.raises(dispatch.DispatchError):
        dispatch.build_cmd({"cmd": ["opencode", "{prompt}"]}, "a & b", tmp_path)


def test_agent_env_points_temp_at_the_worktree(tmp_path):
    env = dispatch.agent_env({"env": {"TMP": "{worktree}/.tmp"}}, tmp_path)
    assert env["TMP"] == f"{tmp_path}/.tmp"
    assert "PATH" in env or "Path" in env


def test_escape_is_only_flagged_by_the_task_own_traces(tmp_path):
    import subprocess
    run = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    run("init", "-q")
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "base")
    head = dispatch.git("rev-parse", "HEAD", cwd=tmp_path).stdout.strip()
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "orchestrator work")
    assert not dispatch.escaped_worktree("T-900", head, tmp_path)
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "x\n\nRefs: T-900")
    assert dispatch.escaped_worktree("T-900", head, tmp_path)


def test_unknown_or_disabled_agent_fails():
    cfg = {"agents": {"off": {"cmd": ["x", "{prompt}"], "enabled": False}}}
    with pytest.raises(dispatch.DispatchError):
        dispatch.agent_cfg_or_fail(cfg, "nadie")
    with pytest.raises(dispatch.DispatchError):
        dispatch.agent_cfg_or_fail(cfg, "off")


def test_worktree_path_is_outside_the_repo():
    cfg = dispatch.load_cfg()
    wt = dispatch.worktree_path(cfg, "T-001", "beam")
    assert wt.name == "T-001-beam"
    assert ROOT not in wt.parents


def test_sync_copies_skills_and_replaces_old_copies(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    (src / "uno").mkdir(parents=True)
    (src / "uno" / "SKILL.md").write_text("nuevo", encoding="utf-8")
    (src / "sin-skill").mkdir()
    (dst / "uno").mkdir(parents=True)
    (dst / "uno" / "viejo.md").write_text("viejo", encoding="utf-8")
    assert sync_skills.sync(src, dst) == ["uno"]
    assert (dst / "uno" / "SKILL.md").read_text(encoding="utf-8") == "nuevo"
    assert not (dst / "uno" / "viejo.md").exists()
    assert not (dst / "sin-skill").exists()


def test_project_skills_have_frontmatter():
    skills = sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md"))
    assert len(skills) == 5
    for path in skills:
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert f"name: {path.parent.name}\n" in text
        assert "\ndescription: " in text


def test_fix_prompt_is_safe_for_npm_cmd_shims():
    prompt = dispatch.FIX_PROMPT.format(task="T-001", agent="beam")
    assert not dispatch.CMD_UNSAFE.intersection(prompt)
    assert ".agents/inbox/T-001-fix.md" in prompt


def test_quality_problems_catch_dead_code_and_missing_newline(tmp_path):
    import subprocess
    run = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    run("init", "-q", "-b", "main")
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "base")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "lib.py").write_text("import os\n\n\ndef scan():\n    return 1\n\n\nfind = scan\n",
                                               encoding="utf-8")
    (tmp_path / "notes.md").write_text("sin salto", encoding="utf-8")
    problems = "\n".join(dispatch.quality_problems(tmp_path, "main", ["tools/*"]))
    assert "F401" in problems
    assert "unused variable 'find'" in problems
    assert "notes.md: falta el salto de linea final" in problems
    assert "notes.md: la tarea no permite" in problems
    assert "tools/lib.py: la tarea no permite" not in problems


def test_allowed_files_reads_the_task_section():
    task = ("## Archivos permitidos\n- `tools/ctl/ps1.py` (nuevo), `tools/ctl/__main__.py` (solo la rama `run`)\n"
            "- `tests/reference/traces/snoot/*.trace`\n\n## Archivos prohibidos\n- `engine/core/vm.c`\n")
    assert dispatch.allowed_files(task) == ["tools/ctl/ps1.py", "tools/ctl/__main__.py",
                                            "tests/reference/traces/snoot/*.trace"]
    assert dispatch.allowed_files("# sin seccion\n") == []


def test_alias_problems_flag_aliases_and_all_outside_init():
    source = ('__all__ = ["scan"]\n\n\ndef scan():\n    return 1\n\n\nfind = scan\nlimit = 3\n')
    problems = dispatch.alias_problems("tools/x/lib.py", source)
    assert problems == ["tools/x/lib.py:1: __all__ fuera de __init__.py; borralo",
                        "tools/x/lib.py:8: alias de scan; deja un solo nombre"]
    assert dispatch.alias_problems("tools/x/__init__.py", '__all__ = ["scan"]\n') == []


def test_allowed_files_expand_braces():
    task = "## Archivos permitidos\n- `platforms/{psp,vita}/**`, `docs/platforms/*.md`\n"
    assert dispatch.allowed_files(task) == ["platforms/psp/**", "platforms/vita/**", "docs/platforms/*.md"]


def test_escape_is_flagged_by_changes_staged_in_main(tmp_path):
    import subprocess
    run = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    run("init", "-q")
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "base")
    head = dispatch.git("rev-parse", "HEAD", cwd=tmp_path).stdout.strip()
    assert not dispatch.escaped_worktree("T-900", head, tmp_path)
    (tmp_path / "leak.txt").write_text("x\n", encoding="utf-8")
    run("add", "leak.txt")
    assert dispatch.escaped_worktree("T-900", head, tmp_path)
