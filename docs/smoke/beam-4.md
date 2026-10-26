# Smoke test — beam-4

- CLI: opencode v2.1.4
- Modelo: Beam Free (opencode-go/beam-free)
- Fecha: 2026-10-26

## Resumen de AGENTS.md (10 líneas)

1. Lee tu tarea completa y trabaja solo dentro de tu worktree.
2. No edites contratos, repos hermanos ni archivos fuera de los permitidos.
3. Prohibido git push, merge, rebase, reset --hard o borrar ramas.
4. No inventes resultados: pega la salida real de las verificaciones.
5. Compila y prueba con el venv del repo principal en worktrees.
6. C99 en el núcleo, sin memoria dinámica en el bucle de juego.
7. Nada fijo de un juego en el núcleo; va en datos o módulo.
8. Python 3.12 con encoding UTF-8 y pathlib en tools/.
9. Conversores deterministas: misma entrada, mismo hash.
10. Al terminar: verifica, commit conventional con Refs y reporte.