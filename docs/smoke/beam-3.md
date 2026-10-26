# Smoke test — beam-3

- **CLI:** opencode v2.1.4
- **Modelo:** Beam Free (opencode-go/beam-free)
- **Fecha:** 2026-10-26

## Resumen de AGENTS.md (10 líneas)

1. Antes de empezar: lee la tarea, trabaja solo en tu worktree y nunca escribas fuera de él.
2. Lee `PLAN.md` (secciones 2 a 4) y `docs/core-api.md` si tocas el motor.
3. Prohibido editar contratos, `engine/ps1-base/`, repos hermanos, hacer push/merge/rebase/reset o tocar archivos no permitidos.
4. No inventes resultados ni adivines detalles de hardware o del juego; repórtalos con archivo y línea.
5. No descargues SDKs ni emuladores.
6. Pruebas con el Python del repo principal (`.venv`); en worktree no hay `.venv`.
7. Host con gcc C99; PS1 con PSn00bSDK; otras consolas solo por Docker.
8. C99 en el núcleo, sin memoria dinámica en el bucle de PS1/GBA/GB; nada fijo de un juego en el núcleo.
9. Python 3.12, Windows first, scripts en Python y conversores deterministas.
10. Al terminar: verifica, commit conventional en inglés con `Refs: T-003`, reporte en `reports/T-003.md`, sin coautor.