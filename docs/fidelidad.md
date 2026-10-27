# Fidelidad de `renpy_full`: `chapter_x2`

Comparación de las referencias PS4 y DS contra `tests/reference/traces/snoot/chapter_x2.trace` (97 SAY alineados en
cada caso). Las dos trazas del motor producen las mismas diferencias agrupadas.

## Diferencias antes y después de normalizar

| Estado | Campo | Diferencia agrupada | PS4 | DS |
|---|---|---|---:|---:|
| Antes | `bg` | `rec` vs. `room anon day alt` (69), `rec` vs. `skinrow` (12), `None` vs. `room anon day alt` (16) | 97 | 97 |
| Antes | `sprites` | overlays `rec`/`viewfinder` ausentes en motor (81 estados); `flip` en nombres del motor (14 estados) | 95 | 95 |
| Antes | `music` | `None` o `bayside bumming it.ogg` vs. `fuck you i like this chick.ogg` | 8 | 8 |
| Después | `music` | `None` vs. `fuck you i like this chick.ogg` (7); `bayside bumming it.ogg` vs. `fuck you i like this chick.ogg` (1) | 8 | 8 |

Antes había 200 diferencias de campo por plataforma; después quedan 8, todas de música. Los conteos pueden
reproducirse con `python -m tools.ctl.full_diff <traza>`.

## Causas y clasificación

| Diferencia | Causa con evidencia | ¿Bug real del port? | Dónde se arregla |
|---|---|---|---|
| `bg` toma `rec`, falta o usa otro nombre | El hook Ren'Py emite la imagen de `scene skinrow`/`scene room anon day alt` como `SHOW` de imagen (traza Ren'Py, SAY 0 y 12). El motor emite `SCENE` seguido de `SHOW rec`/`SHOW viewfinder`; el normalizador anterior convertía el overlay vacío en fondo. | No; era asignación incorrecta de roles y nombres en el comparador. | Comparador, `trace.py`: comparar el `SCENE` del motor con el `SHOW` de fondo Ren'Py; overlays simétricos. |
| `rec` y `viewfinder` faltan en sprites del motor | El guion coloca `show viewfinder` y `show rec` después de cada escena (`E:/snoot/snootgame/game/script/x2-the-mous-pad.rpy:13-21`, `75-84`). TRACE Ren'Py conserva tags vacíos y el compilador asigna tags propios (`E:/Dev/snoot-ps1/tools/script_compiler/lower.py:623-660`). | No; ambos son overlays presentes en las trazas. | Comparador, `trace.py`, reconocerlos como overlays por su tag. |
| Diferencias de nombre con `flip` | El guion usa `anon neutral flip`, `anon shrug flip` y `fang happy flip` (`E:/snoot/snootgame/game/script/x2-the-mous-pad.rpy:10,55,286`). `images.py:294-311` reduce la envoltura a imagen base más booleano; `lower.py:623-660` coloca ese booleano en `FLAG_FLIP`; `scene.c:70-76,131-135` lo conserva y `main.c:890` lo entrega al dibujador. | No hay bug de render confirmado; la traza no expone la orientación efectiva. | Para certificarlo, TRACE necesita un campo de flip en `SHOW`; propuesta en reporte, contrato C3 sin cambios aquí. |
| 7 SAY con motor sin música y Ren'Py con `fuck you i like this chick.ogg` | El guion inicia esa pista en línea 33 y la detiene con `stop music fadeout 3` en línea 238. El motor registra `PLAY track=55`, luego `STOP`; el hook de referencia no emite el `STOP`, por lo que su normalizador conserva la pista hasta el siguiente PLAY. | No confirmado; la evidencia apunta a una omisión del hook Ren'Py. | Recapturar o reparar el hook en `renpy-port-kit` (repo hermano, solo propuesta). No normalizar esta diferencia a ciegas. |
| 1 SAY: motor `bayside bumming it.ogg`, Ren'Py aún `fuck you...` | El guion cambia a `bayside bumming it.ogg` en línea 266. El compilador genera PLAY para la fuente en `lower.py:828-882`, y procesa STOP del canal en `lower.py:890-904`. El motor registra `PLAY track=50`, que el mapa resuelve a `bayside bumming it.ogg`; Ren'Py registra el nuevo PLAY pero no el STOP anterior. | No; el cambio coincide con la fuente y el compilador. | Hook Ren'Py / recaptura de referencia en repo hermano. |
| `show black` transitorio no está en la referencia Ren'Py | El guion lo muestra en línea 12 y lo oculta en línea 34; no aparece como SHOW en la traza de referencia. Se excluye del estado comparable para no tratarlo como fondo. | Sin verificación visual del hook, no se concluye si la capa falta en el juego o solo en la captura. | Mejorar captura Ren'Py; no se modifica el motor en esta tarea. |

La regla para `room anon day alt` se apoya en `scene room anon day alt` en el guion, línea 74: es fondo, no sprite. Los
8 residuos de música son todos diferencias de estado derivadas del STOP no capturado; la evidencia actual no apunta
a una falla de compilación del port. La traza no permite validar el flip efectivo ni la capa `black` transitoria.
