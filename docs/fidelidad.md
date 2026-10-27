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

## Revisión PC de las 14 rutas (T-628)

Se compararon las trazas `pc-routes/snoot-route-*.trace` con las referencias `snoot/*.trace`. El total cuenta diferencias de campo en SAY alineados. Los conteos finales quedan fijados por `tests/test_trace_full.py`.

| Ruta | Antes | Después |
|---|---:|---:|
| chapter_x1 | 5 | 0 |
| chapter_x2 | 0 | 0 |
| chapter_x3 | 87 | 0 |
| chapter_x4 | 6 | 0 |
| chapter_x5 | 3 | 0 |
| chapter_x6 | 9 | 0 |
| chapter_x7 | 432 | 3 |
| chapter_x8 | 168 | 2 |
| chapter_x9 | 554 | 163 |
| chapter_x10 | 187 | 144 |
| ruta-1 | 3961 | 5826 |
| ruta-2 | 3760 | 5848 |
| ruta-3 | 5015 | 8198 |
| ruta-4 | 4498 | 7084 |

Las rutas largas suben porque la corrección dejó de interpretar cada `SHOW` sin atributos como fondo. El normalizador conserva esas capas como sprites y deja que `SCENE` defina el fondo; así expone pérdidas de estado del hook y diferencias sin clasificación en vez de ocultarlas como fondos falsos.

| Patrón | Causa y evidencia | Regla o bug | Dónde |
|---|---|---|---|
| `SHOW` sin atributos sobreescribía el fondo | `x3-PTA-meeting.rpy:18-26` declara `scene auditorium` y luego `show` de personajes sin atributos. `x7-naomi-tribulations.rpy:343-349` muestra `dimmer_darker` y sprites. | Representación: solo una escena reconocida cambia el fondo; los demás `SHOW` son sprites. | Regla simétrica en `trace.py`; X1–X6 quedan en cero. |
| `fang embarrass` / `fang embarass` | El guion original usa `show fang embarass flip` (`x6-passion-of-the-trigga.rpy:767`); el mapa compilado emite `embarrass`. | Errata original canonizada para esa expresión exacta en ambos lados. | Regla en `trace.py`; X6 queda en cero. |
| Atributos por defecto de `fangphonevideocall` y `layeredanonphone` | `src/image_definitions.rpy:1181-1250,1254-1352` declara capas `default`; Ren'Py `get_attributes` entrega atributos activos y el nombre compilado incluye defaults. | Representación: se eliminan solo los defaults verificados y se ordena el conjunto de atributos del teléfono en ambos lados. | Regla en `trace.py`; reduce X7 y las rutas largas. |
| Capas `dimmer_*` | `x9-naomi-tribulations.rpy:923-926` las muestra encima de `scene home fang night`. | Son sprites, no fondos. | Regla en `trace.py`; elimina estas diferencias de fondo. |
| Pistas sincronizadas incompletas | `x9-naomi-tribulations.rpy:101-102,271,678-696` reproduce piano, percusión y sintetizador en canales separados; el hook conserva solo `_rcp_music_cmd` de `channel == "music"`. | Pérdida del hook; no se declara bug de audio del port. Recapturar el conjunto de pistas activas por SAY. | Propuesta para `trace_hook.rpy`; cambio detallado en el reporte. |
| `camera shot NNN` frente a escena y componentes | X10 compone escena, blur/zoom y sprites (`x10-raymbas-observations.rpy:127-176`); motor traza `camera shot NNN`, Ren'Py separa fondo y capas. | La traza no certifica equivalencia visual; no se etiqueta como bug confirmado. Recapturar imagen de escena, atributos y transform aplicado. | Pendiente de recaptura; quedan 144 diferencias en X10. |
| `good faith reprise intro.ogg` | `x8-naomi-tribulations.rpy:422` ejecuta `play music`; aparece en dos SAY de Ren'Py y no en el estado del motor. | Bug de audio por confirmar auditando PLAY/STOP del compilador para esa sección. | Pendiente; 2 diferencias de música en X8. |

Los residuos medidos son X7 3 (cámara y orden de atributos), X8 2 (música), X9 163 (pistas en capas), X10 144 (cámara y composición) y 5.848–8.198 por ruta larga. Salvo las normalizaciones con evidencia citada, no hay información suficiente para llamarlos bugs reales: el hook no conserva el estado de varias capas ni las pistas de otros canales. Esta revisión no certifica `renpy_full` como terminado; el líder debe ajustar el hook y regrabar antes de cerrar la lista de bugs reales.
