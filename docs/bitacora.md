# Bitácora — renpy-console-project

## 2026-10-26
- `git init` y commit inicial; rutas de `C:\Users\Pako\Desktop\snoot` cambiadas a `E:\snoot`.
- Extraídos a `engine/core/` los módulos sin hardware de `ps1-base` (`vm`, `scene`, `str`, `lz4`,
  `opcodes.h`, `vn_limits.h`). Compilan en host con `C:\msys64\ucrt64\bin\gcc.exe -std=c99 -Wall -Wextra -pedantic`.
- Pendiente: no hay `.venv` ni pytest (resuelto más abajo).
- Commit inicial reescrito sin línea de coautor (regla del proyecto).
- Contrato `VnPlatformOps` movido a `engine/core/vn_platform.h` y ampliado con archivos y fuente. `chapter.c` y
  `text.c` ya no incluyen nada de PS1. Hardware (`audio`, `cd`, `img`, `input`, `res`, `save`, `video`,
  `video_clip`) copiado a `platforms/ps1/` con `backend_ps1.c`.
- Cambio de conducta: `font_load` ahora rechaza un `FONT.BIN` más corto que su atlas (antes leía de más).
- Prueba host `tests/core/test_core_host.c` pasa con los datos de Wani; el núcleo y el backend PS1 compilan con
  `mipsel-none-elf-gcc`. No hay ejecutable PS1 todavía (falta `main.c`), así que no se probó en emulador.
- Referencias: base = `vn-engine-ps1` (`947cb3b`); `snoot-ps1/engine` = motor v1.0, solo referencia.
- Rutas `C:\Users\Pako\Desktop\snoot` cambiadas a `E:\snoot` en los repos hermanos, con permiso del usuario:
  `vn-engine-ps1` f63d4a6, `snoot-ps1` 2b22e15, `wani-ps1` 3810b25, `renpy-port-kit` 59fc01d, `snoot-ps2` ce0eccd.
  `check_env.py` de snoot-ps1 y wani-ps1 en verde; renpy-port-kit 404 pruebas pasan. `engine/ps1-base` no se tocó
  (copia de 947cb3b).
- `.venv` con Python 3.12 y pytest; `pytest.ini` limita las pruebas a `tests/`. `tests/test_core_host.py` compila
  y corre la prueba de host: 1 pasa.
- Plan integrado v0.2: `PLAN.md` reescrito uniendo el v0.1 y `E:\Dev\PLAN_MAESTRO_SNOOT_PORTS.md` v2.0 (copiado
  sin cambios a `docs/plan-maestro-agentes.md`). Decisiones clave: este repo es el del proyecto, VNB es el formato
  intermedio (se descartan SnootIR y VNSCENE), backend SDL2 compartido, Docker para toolchains, TRACE + Test Lab
  CLI, agentes en paralelo desde la Fase 4. `AGENTS.md` reemplaza a `docs/ai-agent-rules.md`; se borraron
  `docs/formats/vnscene.md`, el stub `tools/console-test-lab` y las carpetas vacías.
- Rutas `Path.home() / "Desktop" / "snoot"` (no las tomó el script anterior) cambiadas a `E:\snoot`:
  snoot-ps1 4385f4c (`emutest.py`, `audit/capture.py`), wani-ps1 81c56d8 (`playtest.py`), renpy-port-kit d395512
  (`paths.py`). Kit 404 pasan; snoot-ps1 59 pasan; wani-ps1 146 pasan y 1 falla por `psxavenc.exe` 0xC0000139
  (falla igual antes del cambio).
- Pista de agentes A3: skills de Orca (`orca-cli` ya estaba, `orchestration` instalada con el CLI de Orca) en
  `~/.agents`, `~/.claude` y `~/.gemini`. Probado con una skill falsa: OpenCode/Beam, Kilo y Antigravity leen
  `.agents/skills` (OpenCode y Kilo también `.claude/skills`); Codex y Vibe leen `.agents/skills` (código fuente).
  `agy -p` 1.4.7 responde sin terminal. 5 skills propias en `.agents/skills/` adaptadas a VNB y a las rutas reales,
  3 subagentes en `.claude/agents/`, plantillas, `agents.toml` con flags verificados con `--help`, `dispatch.py` y
  `sync_skills.py` con 8 pruebas. `npx skills` no se pudo correr (código externo bloqueado por permisos).
- Orca: las skills de Codex, OpenCode, Kilo, Vibe y MiMo van a `~/.agents/skills` (carpeta compartida), por eso
  Orca solo mostraba enlaces para Claude y Antigravity. Los 6 agentes arrancan con `orca agent launch`. Codex fallaba
  por `service_tier = "default"` en `~/.codex/config.toml` (se quitó la línea) y Orca usaba Codex 0.128 y OpenCode
  1.14.33 viejos de `AppData\Roaming\npm` (Orca pone esa carpeta antes que `C:\nvm4w\nodejs`); se desinstalaron con
  permiso del usuario. Ahora Orca lanza Codex 0.164 y OpenCode 2.1.4. Repo agregado a Orca.
- Prueba de humo A4 (10 tareas T-001..T-010): Claude (Opus 5.5), Antigravity (Gemini 3.8 Flash) y Codex 0.164
  completas, con commit y reporte; 9 pruebas pasan en cada worktree. Codex necesitó `auto_commit` y `.tmp/` propio
  (su sandbox de Windows no escribe en `.git`, `.agents` ni el temporal global); los reportes pasan a
  `reports/<T>.md`. Los 5 Beam, Kilo y Vibe no se lanzaron: el clasificador de permisos de la sesión de Claude los
  bloqueó por correr con aprobación automática. Faltan por correr desde una terminal del usuario.
- GA cumplida: las 10 tareas de humo en verde (5 Beam en paralelo en ~1,5 min, Codex, Kilo, Vibe, Antigravity,
  Claude), cada rama con solo sus 2 archivos y sin coautor. Kilo se salió del worktree la primera vez (commit en
  `main`): se movió el commit a su rama, se quitó de `main` y ahora recibe `--dir`; `dispatch.py` marca FUGA si un
  agente cambia el repo principal. Detección de límites de tasa solo con frases de error reales.
- Regla de permiso en `.claude/settings.local.json` (personal, ignorada por git) para que Claude lance
  `dispatch.py`. Instalados `clangd` 22.1.4 (MSYS2) y `pyright` 1.1.414 (npm) con los plugins `clangd-lsp` y
  `pyright-lsp`; `compile_flags.txt` para que clangd encuentre los headers. No se instalaron Superpowers ni
  mattpocock (chocan con los comandos propios del usuario).
