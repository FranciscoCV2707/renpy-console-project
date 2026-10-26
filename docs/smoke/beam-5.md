# Smoke test beam-5

- CLI: opencode v2.1.4
- Modelo: Beam Free (opencode-go/beam-free)
- Fecha: 2026-10-26

## Resumen de AGENTS.md (10 líneas)

1. Lee AGENTS.md y la tarea antes de empezar; trabaja solo en tu worktree.
2. No edites contratos, ps1-base ni repos hermanos; no push/merge/rebase/reset.
3. No toques archivos fuera de la lista permitida de la tarea.
4. Compila/prueba con pytest del repo principal; host gcc C99.
5. C99 en núcleo/backends; sin memoria dinámica en bucle de PS1/GBA/GB.
6. Nada fijo de un juego en el núcleo; lo propio va en datos o módulo.
7. Python 3.12, tests en tests/, Windows first, scripts en Python.
8. Conversores deterministas: misma entrada -> mismo hash.
9. Documentación en español; código y nombres en inglés.
10. Al terminar: verificación, commit conventional con Refs, reporte en reports/.
