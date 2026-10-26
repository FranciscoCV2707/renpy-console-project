# Proyecto: renpy-console-project (ecosistema de portabilidad de Ren'Py a consolas)

## Qué es
Repositorio maestro que coordina el esfuerzo de llevar Snoot Game y otros juegos Ren'Py a
múltiples consolas (PS1, PS2, PS3, PS4, PS5, PSP, PSP Go, PS Vita, GB, GBC, GBA, NDS,
3DS, Wii, Switch 1, Xbox Classic, Xbox 360, Xbox One, Xbox Series S/X).

No modifica los repos hermanos (`snoot-ps1`, `vn-engine-ps1`, `wani-ps1`, `renpy-port-kit`).
Propone cambios mediante copias explícitas o pull requests.

## Documentos que debes leer al iniciar cada sesión
1. Este `CLAUDE.md`, `PLAN.md` y `STATUS.md`.
2. `docs/ai-agent-rules.md`.
3. `docs/bitacora.md` (cuando exista).

## Reglas
- No modificar repos hermanos sin permiso.
- Todo código Python lleva tests en `tests/` y debe pasar `pytest`.
- Cambiar el formato del bytecode implica actualizar spec, compilador, simulador y motor juntos.
- C99 para el motor; compatible con PSn00bSDK.
- Windows first: `encoding="utf-8"`, `pathlib.Path`, scripts en Python, comandos en PowerShell.
- Commits: conventional commits en inglés, sin co-autor ni mención a Claude.
- Documentación en español; código y nombres en inglés.

## Entorno
- Windows 10/11, Python 3.12, Git, CMake, Ninja, ffmpeg.
- PSn00bSDK vía MSYS2 en `C:\msys64\usr\local\psn00bsdk`.
- Emuladores en `E:\snoot`.
- Repos hermanos en `E:\Dev`.

## Descargas necesarias
Ver `docs/what-to-download.md` para la lista completa por fase.
Prioridad inmediata: SDL2 dev (backend PC). Siguiente: PS2SDK, PSPSDK, PCSX2, PPSSPP.

## Comandos (PowerShell, en `E:\Dev\renpy-console-project`)
- Verificar entorno: `.\.venv\Scripts\python.exe tools\check_env.py` (cuando exista)
- Tests: `.\.venv\Scripts\python.exe -m pytest`
