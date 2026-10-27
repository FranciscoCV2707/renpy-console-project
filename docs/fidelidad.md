# Diferencias de `renpy_full`

Análisis de `chapter_x2` contra Ren'Py. La referencia disponible en este worktree es
`tests/reference/traces/snoot/chapter_x2.trace`; las trazas indicadas por el líder
(`build/ctl/ps4/trace.txt` y `build/ctl/ds/trace.txt`) no están presentes, así que los conteos posteriores
a la normalización quedan pendientes de reproducir.

## Tipos reportados

| Diferencia observada | Causa y evidencia | ¿Bug real? | Dónde se corrige |
|---|---|---|---|
| `bg`: motor `rec`, Ren'Py `viewfinder` (81 SAY, según la medición del líder) | Son overlays de la escena: `show viewfinder` y `show rec` ocurren después de `scene room anon day alt` en `E:/snoot/snootgame/game/script/x2-the-mous-pad.rpy:74-83`. El hook emite ambos sin atributos (`chapter_x2.trace:15,17`), y el normalizador antiguo los confundía con fondo. | No; es clasificación errónea del comparador. | `tools/ctl/trace.py`, normalización Ren'Py. |
| `room anon day alt` figura como sprite Ren'Py y falta en el estado de motor | El guion usa `scene room anon day alt` (`x2-the-mous-pad.rpy:74`), no `show`; el hook lo representa como `SHOW tag=room;attrs=anon day alt` (`chapter_x2.trace:38`). `room` identifica un fondo, aunque tenga atributos. | No; es diferencia de representación. | `tools/ctl/trace.py`, tag `room` normalizado como fondo. |
| Ren'Py agrega o quita `flip` en `fang happy` / `anon shrug` | Las imágenes son espejos horizontales: `image_definitions.rpy:518,617`. El compilador resuelve el espejo (`tools/script_compiler/images.py:297-311`) y pone `FLAG_FLIP` en `SHOW` (`lower.py:628-655`; también en `show` sin ATL, `lower.py:801`). El núcleo guarda la bandera (`engine/core/scene.c:75,156`) y el bucle la pasa al dibujado (`engine/app/main.c:981-984`); PS1 y DS exponen `img_draw_flip` (`platforms/ps1/img.c:175`, `platforms/ds/source/img.c:309-312`). TRACE solo informa `tag` e `img` (`engine/core/vm.c:394-396`). | No hay evidencia de un bug de orientación; el bytecode sí conserva la bandera. La traza no permite validar el resultado visual. | Comparador: ignorar el token de nombre `flip`. Para medir orientación, proponer `flip=0/1` en TRACE SHOW como cambio de contrato. |
| Ren'Py tiene `fuck you i like this chick.ogg` y el motor ninguno (7 SAY); una línea muestra `bayside bumming it.ogg` en el motor | El guion inicia la primera pista en `x2-the-mous-pad.rpy:33` y la segunda en `:266`. El compilador resuelve la ruta (`tools/script_compiler/project.py:112-113`) y `play_music` emite `MUSIC_PLAY` (`lower.py:855-878`); la VM emite TRACE `PLAY` al ejecutar esa instrucción (`engine/core/vm.c:421-423`). La normalización de nombres ya ignora mayúsculas y separadores. | Sí: es una diferencia real de estado de música, no de nombre. La evidencia disponible no separa fallo de compilación, ejecución o registro de evento sin las trazas del líder. | Revisar compilador de snoot-ps1 y ejecución/TRACE del motor; componente concreto pendiente de aislar. |

## Tabla antes/después de normalizar

Los valores “antes” son los conteos comunicados por el líder; no se recalcularon porque faltan las trazas PS4 y DS.
“Después” describe la regla aplicada, no un resultado medido.

| Plataforma | Antes | Después de las reglas | Estado de verificación |
|---|---|---|---|
| PS4 | 81 SAY con fondo `rec` vs `viewfinder`; discrepancias de `flip`; 7 SAY con música solo en Ren'Py y 1 con `bayside bumming it.ogg` solo en motor. | Los overlays dejan de sobrescribir `bg`; `room anon day alt` se trata como fondo; `flip` no altera el nombre del sprite. Las diferencias de música permanecen como fallos. | Pendiente: falta `build/ctl/ps4/trace.txt`. |
| DS | Conteo no disponible en este worktree. | Aplican las mismas reglas; no se declaran conteos ni PASS sin comparar las trazas. | Pendiente: falta `build/ctl/ds/trace.txt`. |

## Evidencia y límite de TRACE

La traza Ren'Py confirma el evento `room` y los overlays (`chapter_x2.trace:15-17,38`). En el árbol actual no hay
traza del motor para asociar cada `SAY` con el ID de pista o la bandera de flip. Añadir el bit de flip a TRACE es una
propuesta al dueño del contrato C3; este cambio no modifica el protocolo.
