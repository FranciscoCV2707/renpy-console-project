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
import ast
import json
import os
import shutil
import subprocess
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CFG_PATH = ROOT / "tools" / "agents" / "agents.toml"
AG = ROOT / ".agents"
CMD_UNSAFE = set('&|<>^%"\r\n')
# Frases de error reales; las sueltas ("429", "rate limit") salen en docs que los agentes leen
RATE_LIMIT_HINTS = ("429 too many requests", "status code 429", "http 429", "error 429", "rate limit exceeded",
                    "rate_limit_exceeded", "ratelimiterror", "rate limit reached",
                    "timed out waiting for response headers")
PYTHON = Path(sys.executable)
CLANG_FORMAT = Path("C:/msys64/ucrt64/bin/clang-format.exe")
TEXT_SUFFIXES = {".py", ".c", ".h", ".md", ".toml", ".yaml", ".yml", ".txt", ".rpy", ".json", ".cmake"}
FIX_PROMPT = ("Eres el agente {agent} del proyecto renpy-console-project. Ya trabajaste la tarea {task} en este "
              "directorio, pero el despachador encontro problemas. Lee .agents/inbox/{task}-fix.md, corrige cada "
              "uno sin agregar nada que la tarea no pida, corre las verificaciones, actualiza reports/{task}.md y haz "
              "un commit nuevo con Refs: {task}. No hagas push, merge ni rebase.")


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
    # {gitdir}: el .git del repo principal, donde escribe el commit de un worktree
    cmd = [p.replace("{prompt}", prompt).replace("{worktree}", str(wt)).replace("{gitdir}", str(ROOT / ".git"))
           for p in agent_cfg["cmd"]]
    cmd[0] = resolve_exe(cmd[0])
    if os.name == "nt" and cmd[0].lower().endswith((".cmd", ".bat")):
        bad = CMD_UNSAFE.intersection(prompt)
        if bad:
            raise DispatchError(f"El prompt contiene caracteres peligrosos para .cmd: {sorted(bad)}")
    return cmd


def escaped_worktree(task: str, main_head: str, root: Path = ROOT) -> bool:
    """El agente trabajó en el repo principal: commit en main con `Refs: <task>`, su reporte escrito ahí o cambios
    preparados en el índice de main (Claude no deja nada preparado: commitea al momento; pasó en T-609)."""
    bodies = git("log", "--format=%B", f"{main_head}..HEAD", cwd=root, check=False).stdout
    staged = git("diff", "--cached", "--name-only", cwd=root, check=False).stdout.strip()
    return f"Refs: {task}" in bodies or (root / "reports" / f"{task}.md").exists() or bool(staged)


def allowed_files(task_text: str) -> list[str]:
    """Rutas y globs entre comillas invertidas de la sección `## Archivos permitidos` de una tarea."""
    if "## Archivos permitidos" not in task_text:
        return []
    section = task_text.split("## Archivos permitidos", 1)[1].split("\n## ", 1)[0]
    # una carpeta (`tests/`) permite todo lo de adentro
    return [p + "**" if p.endswith("/") else p
            for g in section.split("`")[1::2] if "/" in g or "." in g for p in expand_braces(g)]


def expand_braces(pattern: str) -> list[str]:
    """`platforms/{psp,vita}/**` -> una ruta por opción (fnmatch no entiende llaves)."""
    if "{" not in pattern:
        return [pattern]
    head, rest = pattern.split("{", 1)
    options, tail = rest.split("}", 1)
    return [p for option in options.split(",") for p in expand_braces(head + option + tail)]


def alias_problems(name: str, source: str) -> list[str]:
    """Alias de funciones o clases del mismo módulo y `__all__` fuera de `__init__.py`: vulture no los ve (un nombre
    en `__all__` cuenta como usado) y la regla de estilo los prohíbe."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []  # ruff ya lo reporta (E9)
    defs = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    problems = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if isinstance(node.value, ast.Name) and node.value.id in defs:
            problems.append(f"{name}:{node.lineno}: alias de {node.value.id}; deja un solo nombre")
        if not name.endswith("__init__.py") and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            problems.append(f"{name}:{node.lineno}: __all__ fuera de __init__.py; borralo")
    return problems


def quality_problems(wt: Path, base: str, allowed: list[str] | None = None) -> list[str]:
    """Lo que la revisión rechazaría siempre: archivos fuera de los permitidos, errores de ruff, código muerto
    (vulture), falta de salto de línea final y pruebas rotas. Solo mira lo que la rama cambió respecto de `base`."""
    # Contra el punto donde nació la rama: lo que main avanzó mientras tanto no es del agente
    base = git("merge-base", base, "HEAD", cwd=wt, check=False).stdout.strip() or base
    touched = git("diff", "--name-only", base, cwd=wt, check=False).stdout.split()
    touched += git("ls-files", "--others", "--exclude-standard", cwd=wt, check=False).stdout.split()
    touched = list(dict.fromkeys(touched))
    problems = [f"{c}: la tarea no permite cambiar este archivo; deja el de {base} tal cual" for c in touched
                if allowed is not None and not any(fnmatch(c, pattern) for pattern in allowed)]
    changed = [c for c in touched if (wt / c).is_file()]
    # En .py el salto de línea final lo revisa ruff (W292)
    problems += [f"{c}: falta el salto de linea final" for c in changed
                if Path(c).suffix in TEXT_SUFFIXES - {".py"} and (data := (wt / c).read_bytes())
                and not data.endswith(b"\n")]
    py = [c for c in changed if c.endswith(".py")]
    if py:
        out = subprocess.run([str(PYTHON), "-m", "ruff", "check", "--output-format", "concise", *py], cwd=wt,
                             text=True, capture_output=True, encoding="utf-8", errors="replace").stdout
        problems += [line for line in out.splitlines() if ": " in line and not line.startswith("Found")]
        # Las pruebas cuentan como uso; solo se reporta código muerto en archivos de la rama que no son pruebas
        dirs = [d for d in ("tools", "tests") if (wt / d).is_dir()]
        out = subprocess.run([str(PYTHON), "-m", "vulture", *dirs, "--min-confidence", "60"], cwd=wt,
                             text=True, capture_output=True, encoding="utf-8", errors="replace").stdout
        mine = {Path(c) for c in py if not c.startswith("tests/")}
        problems += [line for line in out.splitlines() if Path(line.split(":", 1)[0]) in mine]
        for c in py:
            problems += alias_problems(c, (wt / c).read_text(encoding="utf-8"))
    # C nuevo con el estilo del motor (.clang-format); el C que ya existía no se reformatea
    added = set(git("diff", "--name-only", "--diff-filter=A", base, cwd=wt, check=False).stdout.split())
    added |= set(git("ls-files", "--others", "--exclude-standard", cwd=wt, check=False).stdout.split())
    for c in sorted(c for c in added if c.endswith((".c", ".h")) and (wt / c).is_file()):
        formatted = subprocess.run([str(CLANG_FORMAT), "--style=file", c], cwd=wt, capture_output=True).stdout
        if formatted != (wt / c).read_bytes():
            problems.append(f"{c}: no sigue el estilo del motor; corre {CLANG_FORMAT} --style=file -i {c}")
    tests = subprocess.run([str(PYTHON), "-m", "pytest", "-q", "-x"], cwd=wt, text=True, capture_output=True,
                           encoding="utf-8", errors="replace")
    if tests.returncode not in (0, 5):  # 5: no hay pruebas
        problems.append("pytest falla:\n" + "\n".join(tests.stdout.splitlines()[-25:]))
    return problems


def agent_env(agent_cfg: dict, wt: Path) -> dict:
    """Entorno del agente: el del sistema más `env` de agents.toml, con {worktree} reemplazado."""
    env = os.environ.copy()
    env.update({k: str(v).replace("{worktree}", str(wt)) for k, v in agent_cfg.get("env", {}).items()})
    return env


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
    # Sin sección de archivos permitidos no se revisa el alcance; el reporte siempre se permite
    allowed = allowed_files(task_file.read_text(encoding="utf-8")) or None
    if allowed:
        allowed.append(f"reports/{task}.md")

    wt, branch = ensure_worktree(cfg, task, agent)
    inbox = wt / ".agents" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    shutil.copy2(task_file, inbox / f"{task}.md")
    # El reporte va fuera de .agents/: el sandbox de Codex no deja escribir ahí
    (wt / "reports").mkdir(parents=True, exist_ok=True)
    (wt / ".tmp").mkdir(exist_ok=True)

    prompt = cfg["settings"]["prompt_template"].format(task=task, agent=agent)
    cmd = build_cmd(acfg, prompt, wt)

    for d in ("logs", "status", "reports"):
        (AG / d).mkdir(parents=True, exist_ok=True)
    log_path = AG / "logs" / f"{task}-{agent}.log"
    timeout_min = int(acfg.get("timeout_min", cfg["settings"].get("default_timeout_min", 45)))
    env = agent_env(acfg, wt)

    status: dict = {
        "task": task, "agent": agent, "branch": branch, "worktree": str(wt),
        "started": now(), "cmd": [Path(cmd[0]).name, *cmd[1:]],
    }
    print(f"[dispatch] -> {agent} {task}  ({wt})", flush=True)

    # Para detectar un agente que se salió de su worktree y escribió en el repo principal (Claude puede hacer sus
    # propios commits en main mientras tanto, así que solo cuentan las huellas de esta tarea)
    main_head = git("rev-parse", "HEAD", check=False).stdout.strip()
    rounds = int(acfg.get("fix_rounds", cfg["settings"].get("fix_rounds", 1)))
    auto_committed = False
    problems: list[str] = []
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(f"# {status['started']} agent={agent} task={task}\n# cwd={wt}\n\n")
        for attempt in range(rounds + 1):
            if attempt:
                fix = inbox / f"{task}-fix.md"
                fix.write_text(f"# Problemas en {task} (ronda {attempt})\n\n"
                               + "\n".join(f"- {p}" for p in problems) + "\n", encoding="utf-8")
                cmd = build_cmd(acfg, FIX_PROMPT.format(task=task, agent=agent), wt)
                log.write(f"\n# --- ronda de correccion {attempt}: {len(problems)} problemas ---\n")
                print(f"[dispatch] .. {agent} {task}: {len(problems)} problemas, ronda de correccion {attempt}",
                      flush=True)
            log.flush()
            timed_out = False
            proc = subprocess.Popen(cmd, cwd=wt, env=env, stdin=subprocess.DEVNULL, stdout=log,
                                    stderr=subprocess.STDOUT)
            try:
                code = proc.wait(timeout=timeout_min * 60)
            except subprocess.TimeoutExpired:
                # .CMD lanza el CLI como nieto: matar solo al hijo lo dejaba vivo tocando el worktree
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, check=False)
                proc.wait()
                timed_out, code = True, -1
            if acfg.get("auto_commit") and git("status", "--porcelain", cwd=wt, check=False).stdout.strip():
                # Agentes cuyo sandbox no deja escribir en .git (Codex en Windows): el commit lo hace el despachador
                git("add", "-A", cwd=wt)
                git("commit", "-m", f"chore(agents): {task} work by {agent}\n\nRefs: {task}", cwd=wt, check=False)
                auto_committed = True
            if timed_out:
                break
            problems = quality_problems(wt, base_branch(cfg), allowed)
            if not problems:
                break

    # Las copias de la tarea ya no se necesitan: así el worktree queda limpio
    for f in (inbox / f"{task}.md", inbox / f"{task}-fix.md"):
        f.unlink(missing_ok=True)
    if inbox.exists() and not any(inbox.iterdir()):
        inbox.rmdir()

    report_src = wt / "reports" / f"{task}.md"
    report_found = report_src.exists()
    if report_found:
        shutil.copy2(report_src, AG / "reports" / f"{task}-{agent}.md")

    commits = git("rev-list", "--count", f"{base_branch(cfg)}..{branch}", check=False).stdout.strip()
    dirty = bool(git("status", "--porcelain", cwd=wt, check=False).stdout.strip())
    # Solo el final del log: los agentes leen este archivo y los documentos, que citan las mismas frases
    log_text = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").lower().splitlines()[-40:])
    escaped = escaped_worktree(task, main_head)

    status.update({
        "escaped_worktree": escaped,
        "finished": now(),
        "exit_code": code,
        "timed_out": timed_out,
        "report_found": report_found,
        "commits_ahead": int(commits) if commits.isdigit() else None,
        "uncommitted_changes": dirty,
        "auto_committed": auto_committed,
        "fix_rounds_used": attempt,
        "quality_problems": problems,
        "possible_rate_limit": any(h in log_text for h in RATE_LIMIT_HINTS),
        "log": str(log_path),
    })
    (AG / "status" / f"{task}-{agent}.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

    verdict = "OK" if (code == 0 and report_found and not timed_out and not escaped and not problems) else "REVISAR"
    print(f"[dispatch] <- {agent} {task}: {verdict} exit={code} commits={status['commits_ahead']} "
          f"reporte={'si' if report_found else 'NO'}{' TIMEOUT' if timed_out else ''}"
          f"{f' PROBLEMAS={len(problems)}' if problems else ''}"
          f"{' FUGA: cambio el repo principal' if escaped else ''}", flush=True)
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
