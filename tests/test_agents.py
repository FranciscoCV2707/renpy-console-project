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
