# Reglas para agentes IA — renpy-console-project

1. **Trabaja solo en la tarea pedida.** Lo demás se anota como pendiente en `docs/bitacora.md`.
2. **No modificar repos hermanos** (`snoot-ps1`, `vn-engine-ps1`, `wani-ps1`, `renpy-port-kit`) sin permiso.
3. **Todo código Python lleva tests** en `tests/` y debe pasar `pytest`.
4. **Cambiar el bytecode** implica actualizar spec, compilador, simulador y motor en el mismo cambio, y subir versión.
5. **C99 para el motor.** Compatible con PSn00bSDK; basarse en ejemplos oficiales y psx-spx; no inventar registros ni funciones.
6. **Windows first.** Archivos con `encoding="utf-8"`; rutas con `pathlib.Path`; scripts en Python; comandos en PowerShell; herramientas externas con `subprocess.run([...], check=True)`, sin `shell=True`.
7. **Commits:** conventional commits en inglés, sin línea de coautor ni mención a Claude.
8. **Documentación en español; código y nombres en inglés.**
9. **Antes de cambios grandes,** propón un plan y espera aprobación.
10. **Al terminar una tarea:** actualiza `docs/bitacora.md` y `STATUS.md`, di cómo probar el cambio y haz commit.
11. **No adivinar.** Si el conversor encuentra algo que no entiende, lo reporta (archivo y línea) en lugar de fallar en silencio o adivinar.
12. **Licencias.** Respetar las licencias de cada juego (AGPL-3.0, CC-BY-SA-4.0, etc.). El motor es MIT.
