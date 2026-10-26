# Proyecto: vn-engine-ps1 (motor compartido de novelas visuales para PS1)

## Qué es
El motor en C (PSn00bSDK) que ejecutan los ports de novelas visuales de Ren'Py a PlayStation 1.
Nació del motor de `E:\Dev\snoot-ps1` (v1.0 publicada), copiado tal cual en su commit `ae2f4f0`, y
crece con cada juego: lo que un port agrega y sirve a otros juegos vive aquí.

- **Lo usa:** `E:\Dev\wani-ps1` (port de I Wani Hug that Gator!), desde su Fase 0.
- **Más adelante:** snoot-ps1 puede pasarse a este motor (por ahora no se toca: su v1.0 funciona).
- **Datos de entrada:** los genera cada port a partir del kit `E:\Dev\renpy-port-kit`.

## Documentos que debes leer al iniciar cada sesión
1. Este `CLAUDE.md`, `PLAN.md` y `STATUS.md`.
2. `docs/bitacora.md`.
3. `docs/bytecode.md` cuando exista (hasta entonces, `docs/snoot-ps1/bytecode.md`, la v1).

## Reglas
- **Nada fijo de un juego en el código común.** Lo propio de cada juego (cuántos finales, qué
  desbloquean, su galería, sus pantallas especiales) va en datos del disco o en un módulo del juego
  aparte. Es el mismo principio del kit.
- **No romper a los juegos que ya lo usan.** Todo cambio se prueba con cada juego que use el motor.
- No modificar `E:\Dev\snoot-ps1`, `E:\Dev\wani-ps1` ni `E:\Dev\renpy-port-kit` desde aquí sin
  preguntar.
- Si cambias el formato del bytecode, actualiza `docs/bytecode.md`, el motor, el compilador y el
  simulador del bytecode en el mismo cambio, y sube el número de versión.
- C99 compatible con PSn00bSDK. Basarse en sus ejemplos oficiales y en psx-spx; no inventar
  registros ni funciones.
- Antes de cambios grandes, propón un plan y espera aprobación.
- Todo código Python lleva tests en `tests/` y debe pasar `pytest`.
- Al terminar una tarea: actualiza `docs/bitacora.md` y `STATUS.md`, di cómo probar el cambio y haz
  commit.
- Explicaciones y documentación en español; código y nombres en inglés.
- Commits: conventional commits en inglés, sin línea de coautor ni mención a Claude.

## Reglas de Windows (obligatorias)
- Archivos de texto con `encoding="utf-8"`; rutas con `pathlib.Path`.
- Scripts en Python, no `.sh` ni `.bat`. Comandos para el usuario en PowerShell.
- Herramientas externas con `subprocess.run([...], check=True)`, sin `shell=True`.

## Entorno
El mismo de snoot-ps1: PSn00bSDK vía MSYS2 en `C:\msys64\usr\local\psn00bsdk` (variable
`PSN00BSDK_LIBS` definida), CMake, Ninja, Python 3.12, ffmpeg. Emuladores en
`C:\Users\Pako\Desktop\snoot` (DuckStation, PCSX-Redux).

## Comandos (PowerShell, en E:\Dev\vn-engine-ps1)
- Configurar y compilar Snoot: `cmake --preset default` y `cmake --build build` (deja `build\snoot.exe`).
- Otro juego: `cmake --preset <juego>` y `cmake --build build\<juego>` (presets en `CMakePresets.json`;
  `generic` usa `games\default`).
- Wani usa `cmake --preset wani` y `cmake --build build/wani`: perfil y memory card propios.
- Compilador compartido y simulador de flujo: `vncompiler/`; pruebas con `python -m pytest`.
  `games/<juego>/config.cmake` puede ajustar progreso e identidad de la memory card sin cambiar Snoot.
- Pruebas de Snoot en emulador (PCSX-Redux sin ventana, capturas píxel a píxel contra la v1.0):
  `.\.venv\Scripts\python.exe tests\emu\snoot.py check [--only escenario ...]`; la referencia se graba
  con `record`. Escenarios: titulo, menus, partida, cargar, teclado, chat, creditos.
- Estructura: `core\` núcleo, `app\` bucle e interfaz, `modules\` pantallas especiales, `games\<juego>\`
  lo propio de cada juego (`game.c` reglas, `text.c` textos, `specials.c` pantallas especiales).
