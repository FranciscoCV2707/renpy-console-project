# Prueba de humo: antigravity

- **CLI:** agy (`agy --version` → `1.4.7`)
- **Modelo:** Gemini 3.8 Flash (High)
- **Fecha:** 2026-10-26

## Resumen de AGENTS.md
1. La tarea está en `.agents/inbox/<T-xxx>.md`; leerla completa y trabajar solo dentro del worktree propio.
2. Consultar `PLAN.md` (secciones 2 a 4) y `docs/core-api.md` si se toca el motor.
3. Prohibido modificar contratos (`vn_platform.h`, formato VNB, TRACE, escenarios, `agents.toml`).
4. Prohibido tocar `engine/ps1-base/`, repos hermanos o archivos fuera de la lista permitida de la tarea.
5. Prohibido `git push`, `merge`, `rebase`, `reset --hard`, borrar ramas, descargar SDKs e inventar resultados.
6. Pruebas con el `.venv` del repo principal (`E:/Dev/renpy-console-project/.venv`), host con gcc C99.
7. Estilo C99 sin memoria dinámica en bucle de juego; el núcleo no incluye consolas ni código específico de juego.
8. Python 3.12 en Windows first (`pathlib.Path`, `encoding="utf-8"`, `subprocess.run` sin `shell=True`).
9. Conversores deterministas; documentación en español y código en inglés.
10. Al terminar: verificar, commit en conventional commits en inglés con `Refs: T-xxx` sin coautor, y reporte.
