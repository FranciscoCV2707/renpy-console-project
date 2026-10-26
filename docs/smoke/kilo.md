# Prueba de humo — agente kilo

- **CLI:** kilo, versión `7.8.17` (salida de `kilo --version`)
- **Modelo:** mimo-v2.6-pro (`xiaomi-token-plan-sgp/mimo-v2.6-pro`)
- **Fecha:** 2026-10-26

## Resumen de AGENTS.md (10 líneas)

1. La tarea está en `.agents/inbox/<T-xxx>.md` y se trabaja solo dentro del worktree propio.
2. Antes de empezar se leen `PLAN.md` (secciones 2–4) y, si se toca el motor, `docs/core-api.md`.
3. Prohibido editar contratos (`vn_platform.h`, formato VNB, protocolo TRACE, escenarios, `agents.toml`); los cambios se proponen en el reporte.
4. Prohibido editar `engine/ps1-base/` (copia de referencia) o cualquier repo hermano.
5. Prohibido `git push`, `git merge`, `git rebase`, `git reset --hard` y borrar ramas.
6. Prohibido tocar archivos fuera de la lista "Archivos permitidos" de la tarea.
7. Prohibido inventar resultados ni adivinar: se pega la salida real y, en PS1, se basa en PSn00bSDK y psx-spx.
8. Pruebas con el `.venv` del repo principal; host con gcc C99 y PS1 con `mipsel-none-elf-gcc` y los flags de `docs/core-api.md`.
9. Estilo: C99 en el núcleo y backends sin memoria dinámica en PS1/GBA/GB; Python 3.12 en `tools/`; Windows first; conversores deterministas; documentación en español.
10. Al terminar: correr la verificación, commit en conventional commits en inglés con `Refs: T-xxx` en el cuerpo y reporte con la plantilla; los bloqueos se documentan y se termina.
