# Prueba de humo — Mistral Vibe

- **CLI:** Mistral Vibe, versión `vibe 3.0.2` (salida de `vibe --version`).
- **Modelo:** `mistral-medium-3.5` (thinking: high), único modelo en `~/.vibe/config.toml`.
- **Fecha:** 2026-10-26.
- **Tarea:** T-008 (pista de agentes, paso A4).

## Resumen de AGENTS.md (10 líneas)

1. La tarea está en `.agents/inbox/<T-xxx>.md`; se lee completa antes de empezar.
2. Solo se trabaja dentro del propio worktree; nunca se escribe fuera.
3. Antes de tocar código se lee `PLAN.md` (secciones 2 a 4) y, si hay motor, `docs/core-api.md`.
4. Prohibido editar contratos: `vn_platform.h`, VNB, TRACE, escenarios y `agents.toml`; cambios solo como propuesta.
5. Prohibido tocar `engine/ps1-base/` y los repos hermanos; nada de push, merge, rebase o borrar ramas.
6. Solo se editan los archivos de la lista "Archivos permitidos" de cada tarea.
7. No inventar resultados: se pega la salida real de las verificaciones; en PS1 solo se usan PSn00bSDK y psx-spx.
8. Pruebas con el `python.exe` del repo principal; host con gcc de MSYS2; otras consolas por Docker.
9. Estilo: C99 portable sin memoria dinámica en bucles de juego; Python 3.12 Windows-first; conversores deterministas.
10. Al terminar: verificación, commit conventional (con `Refs: T-xxx`), reporte con plantilla y commit; en bloqueo se documenta y se termina.
