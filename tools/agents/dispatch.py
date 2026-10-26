#!/usr/bin/env python3
"""
dispatch.py - Despachador headless de agentes para renpy-console-project.

Crea un git worktree por (tarea, agente), copia la tarea a .agents/inbox/, lanza el CLI del agente en modo no
interactivo con timeout, guarda el log y recoge el reporte en .agents/reports/ del repo principal.
Basado en docs/plan-maestro-agentes.md (Parte D9).

Uso:
  python tools/agents/dispatch.py list-agents
  python tools/agents/dispatch.py run    --agent beam --task T-202
  python tools/agents/dispatch.py batch  --agent beam --tasks T-202 T-205 --parallel 2
  python tools/agents/dispatch.py status
  python tools/agents/dispatch.py remove --agent beam --task T-202 --yes
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CFG_PATH = ROOT / "tools" / "agents" / "agents.toml"
AG = ROOT / ".agents"
CMD_UNSAFE = set('&|<>^%"\r\n')
RATE_LIMIT_HINTS = ("429", "rate limit", "rate_limit", "too many requests")


class DispatchError(Exception):
    pass


def load_cfg(path: Path = CFG_PATH) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git(*args: str, cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=check, text=True,
        capture_output=True, encoding="utf-8", errors="replace",
    )


def base_branch(cfg: dict) -> str:
    return cfg["settings"].get("base_branch", "main")


def worktree_path(cfg: dict, task: str, agent: str) -> Path:
    base = Path(cfg["settings"]["worktree_root"])
    if not base.is_absolute():
        base = (ROOT / base).resolve()
    return base / f"{task}-{agent}"


def ensure_worktree(cfg: dict, task: str, agent: str) -> tuple[Path, str]:
    wt = worktree_path(cfg, task, agent)
    branch = f"agent/{agent}/{task}"
    if wt.exists():
        return wt, branch
    wt.parent.mkdir(parents=True, exist_ok=True)
    has_branch = git("rev-parse", "--verify", "--quiet", branch, check=False).returncode == 0
    if has_branch:
        git("worktree", "add", str(wt), branch)
    else:
        git("worktree", "add", "-b", branch, str(wt), base_branch(cfg))
    return wt, branch


def resolve_exe(name: str) -> str:
    exe = shutil.which(name)
    if not exe:
        raise DispatchError(f"No encuentro '{name}' en el PATH.")
    return exe


def build_cmd(agent_cfg: dict, prompt: str, wt: Path) -> list[str]:
    cmd = [p.replace("{prompt}", prompt).replace("{worktree}", str(wt)) for p in agent_cfg["cmd"]]
    cmd[0] = resolve_exe(cmd[0])
    if os.name == "nt" and cmd[0].lower().endswith((".cmd", ".bat")):
        bad = CMD_UNSAFE.intersection(prompt)
        if bad:
            raise DispatchError(f"El prompt contiene caracteres peligrosos para .cmd: {sorted(bad)}")
    return cmd


def agent_cfg_or_fail(cfg: dict, agent: str) -> dict:
    agents = cfg.get("agents", {})
    if agent not in agents:
        raise DispatchError(f"Agente desconocido: {agent}. Opciones: {', '.join(agents)}")
    acfg = agents[agent]
    if not acfg.get("enabled", True):
        raise DispatchError(f"El agente '{agent}' está deshabilitado en agents.toml")
    return acfg


def run_one(cfg: dict, agent: str, task: str) -> dict:
    acfg = agent_cfg_or_fail(cfg, agent)
    task_file = AG / "tasks" / f"{task}.md"
    if not task_file.exists():
        raise DispatchError(f"No existe {task_file}")

    wt, branch = ensure_worktree(cfg, task, agent)
    inbox = wt / ".agents" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    shutil.copy2(task_file, inbox / f"{task}.md")
    (wt / ".agents" / "reports").mkdir(parents=True, exist_ok=True)

    prompt = cfg["settings"]["prompt_template"].format(task=task, agent=agent)
    cmd = build_cmd(acfg, prompt, wt)

    for d in ("logs", "status", "reports"):
        (AG / d).mkdir(parents=True, exist_ok=True)
    log_path = AG / "logs" / f"{task}-{agent}.log"
    timeout_min = int(acfg.get("timeout_min", cfg["settings"].get("default_timeout_min", 45)))
    env = os.environ.copy()
    env.update({k: str(v) for k, v in acfg.get("env", {}).items()})

    status: dict = {
        "task": task, "agent": agent, "branch": branch, "worktree": str(wt),
        "started": now(), "cmd": [Path(cmd[0]).name, *cmd[1:]],
    }
    print(f"[dispatch] -> {agent} {task}  ({wt})", flush=True)

    timed_out = False
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(f"# {status['started']} agent={agent} task={task}\n# cwd={wt}\n\n")
        log.flush()
        try:
            proc = subprocess.run(
                cmd, cwd=wt, env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, timeout=timeout_min * 60,
            )
            code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out, code = True, -1

    # La copia de la tarea ya no se necesita: así el worktree queda limpio
    (inbox / f"{task}.md").unlink(missing_ok=True)
    if inbox.exists() and not any(inbox.iterdir()):
        inbox.rmdir()

    report_src = wt / ".agents" / "reports" / f"{task}.md"
    report_found = report_src.exists()
    if report_found:
        shutil.copy2(report_src, AG / "reports" / f"{task}-{agent}.md")

    commits = git("rev-list", "--count", f"{base_branch(cfg)}..{branch}", check=False).stdout.strip()
    dirty = bool(git("status", "--porcelain", cwd=wt, check=False).stdout.strip())
    log_text = log_path.read_text(encoding="utf-8", errors="replace").lower()

    status.update({
        "finished": now(),
        "exit_code": code,
        "timed_out": timed_out,
        "report_found": report_found,
        "commits_ahead": int(commits) if commits.isdigit() else None,
        "uncommitted_changes": dirty,
        "possible_rate_limit": any(h in log_text for h in RATE_LIMIT_HINTS),
        "log": str(log_path),
    })
    (AG / "status" / f"{task}-{agent}.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

    verdict = "OK" if (code == 0 and report_found and not timed_out) else "REVISAR"
    print(f"[dispatch] <- {agent} {task}: {verdict} exit={code} commits={status['commits_ahead']} "
          f"reporte={'si' if report_found else 'NO'}{' TIMEOUT' if timed_out else ''}", flush=True)
    return status


def cmd_batch(cfg: dict, agent: str, tasks: list[str], parallel: int) -> list[dict]:
    acfg = agent_cfg_or_fail(cfg, agent)
    workers = max(1, min(parallel, int(acfg.get("max_parallel", 1))))
    for t in tasks:  # crear worktrees en serie evita bloqueos de git
        ensure_worktree(cfg, t, agent)
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(run_one, cfg, agent, t): t for t in tasks}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except DispatchError as e:
                results.append({"task": futures[fut], "agent": agent, "error": str(e)})
                print(f"[dispatch] ERROR {futures[fut]}: {e}", flush=True)
    if any(r.get("possible_rate_limit") for r in results):
        print("[dispatch] Aviso: posibles limites de tasa. Baja --parallel o max_parallel.")
    return results


def cmd_status() -> None:
    files = sorted((AG / "status").glob("*.json")) if (AG / "status").exists() else []
    if not files:
        print("Sin ejecuciones registradas.")
        return
    print(f"{'TAREA':<10} {'AGENTE':<8} {'EXIT':>5} {'COMMITS':>7} {'REPORTE':>8} {'TIMEOUT':>8}  FIN")
    for f in files:
        s = json.loads(f.read_text(encoding="utf-8"))
        print(f"{s['task']:<10} {s['agent']:<8} {s.get('exit_code', ''):>5} "
              f"{str(s.get('commits_ahead', '')):>7} {('si' if s.get('report_found') else 'NO'):>8} "
              f"{('SI' if s.get('timed_out') else 'no'):>8}  {s.get('finished', '')}")


def cmd_remove(cfg: dict, agent: str, task: str, yes: bool, force: bool) -> None:
    wt = worktree_path(cfg, task, agent)
    if not wt.exists():
        print(f"No existe el worktree {wt}")
        return
    if not yes:
        raise DispatchError("Borrar un worktree requiere --yes (la rama se conserva).")
    args = ["worktree", "remove", str(wt)] + (["--force"] if force else [])
    git(*args)
    print(f"Worktree eliminado: {wt} (rama agent/{agent}/{task} conservada)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Despachador headless de agentes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list-agents")
    p_run = sub.add_parser("run")
    p_run.add_argument("--agent", required=True)
    p_run.add_argument("--task", required=True)
    p_batch = sub.add_parser("batch")
    p_batch.add_argument("--agent", required=True)
    p_batch.add_argument("--tasks", nargs="+", required=True)
    p_batch.add_argument("--parallel", type=int, default=3)
    sub.add_parser("status")
    p_rm = sub.add_parser("remove")
    p_rm.add_argument("--agent", required=True)
    p_rm.add_argument("--task", required=True)
    p_rm.add_argument("--yes", action="store_true")
    p_rm.add_argument("--force", action="store_true")
    args = ap.parse_args()

    try:
        cfg = load_cfg()
        if args.cmd == "list-agents":
            for name, a in cfg.get("agents", {}).items():
                state = "on " if a.get("enabled", True) else "off"
                print(f"{name:<8} [{state}] max_parallel={a.get('max_parallel', 1)}  {' '.join(a['cmd'][:3])} ...")
        elif args.cmd == "run":
            s = run_one(cfg, args.agent, args.task)
            return 0 if s.get("exit_code") == 0 and s.get("report_found") else 1
        elif args.cmd == "batch":
            res = cmd_batch(cfg, args.agent, args.tasks, args.parallel)
            return 0 if all(r.get("exit_code") == 0 and r.get("report_found") for r in res) else 1
        elif args.cmd == "status":
            cmd_status()
        elif args.cmd == "remove":
            cmd_remove(cfg, args.agent, args.task, args.yes, args.force)
    except (DispatchError, subprocess.CalledProcessError) as e:
        msg = e.stderr if isinstance(e, subprocess.CalledProcessError) and e.stderr else str(e)
        print(f"[dispatch] ERROR: {msg}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
