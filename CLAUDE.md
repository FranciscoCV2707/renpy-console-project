# Proyecto: renpy-console-project (ecosistema de portabilidad de Ren'Py a consolas)

## Qué es
Repositorio del proyecto para llevar Snoot Game (y después Wani y otros juegos Ren'Py) a todas las consolas
posibles con un núcleo C99 compartido, un backend por plataforma y un laboratorio de pruebas automático.
Claude es el arquitecto y orquestador: escribe contratos, divide tareas, revisa e integra.

## Documentos que debes leer al iniciar cada sesión
1. Este `CLAUDE.md`, `PLAN.md` y `STATUS.md`.
2. `AGENTS.md` (reglas comunes a todos los agentes; también valen para ti).
3. `docs/bitacora.md` y, si tocas el motor, `docs/core-api.md`.
4. `docs/plan-maestro-agentes.md` solo para las plantillas de agentes (Parte D); `PLAN.md` manda sobre él.

## Reglas propias del orquestador
- Eres el único que edita los contratos (`PLAN.md` sección 4, `engine/core/vn_platform.h`) y
  `tools/agents/agents.toml`.
- No modificar repos hermanos (`snoot-ps1`, `vn-engine-ps1`, `wani-ps1`, `renpy-port-kit`) sin permiso; las
  correcciones de rutas viejas sí están autorizadas.
- No se avanza de fase sin cumplir su `[GATE]` de `PLAN.md`.
- Pide confirmación para: `git push`, borrar ramas o worktrees, descargas > 1 GB, publicar builds.
- Lees reportes de agentes (`.agents/reports/`), no logs completos.
- Commits: conventional commits en inglés, sin co-autor ni mención a Claude.

## Entorno
- Windows 10, Python 3.12 (`.venv`), Git, CMake, Ninja, ffmpeg.
- PSn00bSDK vía MSYS2 en `C:\msys64\usr\local\psn00bsdk`; gcc y SDL2 2.32 de host en `C:\msys64\ucrt64`.
- Docker Desktop + WSL2 para las toolchains de otras consolas (Docker Desktop hay que abrirlo).
- Emuladores, BIOS y SDKs de Ren'Py en `E:\snoot`. Repos hermanos en `E:\Dev`.
- CLIs de agentes con login: codex, opencode (Beam), kilo (MiMo), vibe, agy. Orca instalado; su CLI está en
  `C:\Users\Pako\AppData\Local\Programs\orca\resources\bin\orca.exe` (en el PATH al activar "Orca CLI").
- Agentes: `python tools/agents/dispatch.py list-agents|run|batch|status|remove`; skills propias en
  `.agents/skills/` (copiar a `.claude/skills/` con `python tools/agents/sync_skills.py`); subagentes de revisión
  en `.claude/agents/` (`port-reviewer` antes de cada merge).

## Comandos (PowerShell, en `E:\Dev\renpy-console-project`)
- Tests: `.\.venv\Scripts\python.exe -m pytest`
- Descargas por fase: `docs/what-to-download.md`.
