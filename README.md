# renpy-console-project

Ecosistema de portabilidad de Ren'Py a consolas, asistido por IA.

Objetivo: tomar un proyecto compatible de Ren'Py, importarlo una sola vez y generar
versiones para múltiples consolas (PS1, PS2, PS3, PS4, PS5, PSP, PSP Go, PS Vita,
GB, GBC, GBA, NDS, 3DS, Wii, Switch 1, Xbox Classic, Xbox 360, Xbox One, Xbox
Series S/X) desde un núcleo compartido y datos de escena comunes.

## Estructura

- `tools/` — conversor Ren'Py, conversor de recursos, analizador de compatibilidad, Console Test Lab.
- `engine/` — núcleo compartido (VM, escena, texto, audio, guardado, lógica).
- `platforms/` — backends por consola.
- `tests/` — escenarios, trazas de referencia, regresión visual.
- `docs/` — arquitectura, contratos, bitácora.

## Primer objetivo

Snoot Game funcionando en **PS1, PS2 y PSP** desde el mismo código de lógica y los
mismos datos de escena.

## Reglas

Ver `CLAUDE.md` y `docs/ai-agent-rules.md`.

## Licencia

Motor: MIT. Los ports son obras derivadas de sus juegos originales y respetan sus licencias.
