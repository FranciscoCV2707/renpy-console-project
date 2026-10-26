# Prueba de humo: claude

- **CLI:** Claude Code (`claude --version` → `2.1.310 (Claude Code)`)
- **Modelo:** Claude Opus 5.5 (`claude-opus-5-5`)
- **Fecha:** 2026-10-26

## Resumen de AGENTS.md
1. La tarea está en `.agents/inbox/<T-xxx>.md`; se lee completa antes de empezar.
2. Se trabaja solo dentro del worktree propio, nunca fuera.
3. Hay que leer `PLAN.md` (secciones 2 a 4) y `docs/core-api.md` si se toca el motor.
4. Prohibido editar contratos (`vn_platform.h`, VNB, TRACE, escenarios, `agents.toml`); se proponen en el reporte.
5. Prohibido tocar `engine/ps1-base/`, repos hermanos o archivos fuera de la lista permitida.
6. Prohibido push, merge, rebase, reset --hard, borrar ramas, descargar SDKs e inventar resultados.
7. Pruebas con el `.venv` del repo principal; host con gcc C99 estricto; otras consolas por Docker.
8. Estilo: C99 sin memoria dinámica en el bucle de consolas pequeñas; núcleo sin nada de consola ni de juego.
9. Python 3.12 en `tools/`, Windows first, conversores deterministas; docs en español y código en inglés.
10. Al terminar: verificar, commit convencional con `Refs: T-xxx` sin coautor, y reporte de máximo 60 líneas.
