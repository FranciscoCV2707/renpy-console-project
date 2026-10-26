---
name: renpy-source-analyzer
description: Analiza los scripts Ren'Py (.rpy) de Snoot Game, Wani u otro juego para inventariar labels, menús, variables, ATL, screens, audio e imágenes, y detectar lo que el compilador VNB no cubre. Úsala antes de tocar el compilador o el kit, o al investigar cómo se comporta una escena del original.
---
# Analizador de fuentes Ren'Py

## Entradas (solo lectura)
- Snoot: `E:\Dev\snoot-ps1\original\game\**\*.rpy` (fuente oficial; también `E:\snoot\snootgame\game`).
- Wani: `E:\snoot\I Wani Hug that Gator!\game\**\*.rpy`.
- Análisis que ya hace el kit: `E:\Dev\renpy-port-kit` (`.\.venv\Scripts\python.exe -m renpykit analyze juegos\<juego>`,
  reportes en `juegos\<juego>\reporte\`). Úsalo antes de repetir trabajo.

## Procedimiento
1. Inventario con `rg -n` sobre la fuente: `^\s*label\s`, `menu:`, `jump`, `call`, `show`, `scene`, `hide`, `play`,
   `stop`, `queue`, `with`, `transform`, `screen`, `python`, `$`.
2. Cada `python` o `$`: (a) asignación simple, (b) expresión que el compilador soporta, (c) lógica que necesita un
   módulo propio (`modules/` del motor). Lista archivo:línea.
3. Cada `transform`/ATL: propiedades, duraciones, interpolaciones, `repeat`/`parallel`/`block`.
4. Screens propias: qué hacen y si cambian el flujo de la historia.
5. Salida: `docs/analysis/<tema>.md` con tablas y referencias archivo:línea.

## Reglas
- Nunca modificar la fuente ni los repos hermanos.
- Citar siempre archivo:línea.
- Marcar explícitamente lo que el compilador VNB no cubre; no adivinar cómo funciona.
