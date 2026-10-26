# Camara con perspectiva (CAMERA con profundidad)

Estado: diseno, sin implementar. Origen: la camara master de I Wani Hug that Gator! usa
`camera: perspective True` desde la linea 1753 del capitulo 1 y no se reinicia antes de la 402. Con
perspectiva, cada capa se proyecta segun su profundidad, asi que el fondo casi no se mueve y los
personajes si. El CAMERA plano del motor (desplazar toda la escena igual) no reproduce eso.

## Semantica de Ren'Py 8.3.7 (fuente: SDK local)

- `renpy/display/scenelists.py`: la transform de camara se guarda por capa y se aplica a la capa master.
- `renpy/display/accelerator.pyx` (`get_point_to` con `Camera`): con `perspective` en la camara, el punto
  de mira es
  - x = (xplacement + width/2), y = (yplacement + height/2), z = zpos_camara + z11,
  - donde (xplacement, yplacement) es la posicion de la camara (xpos/ypos/xanchor/yanchor/xoffset/yoffset)
    resuelta con `displayable.place`.
- `z11` = `config.perspective[1]` = 1000.0 (por defecto). `config.perspective = (100.0, 1000.0, 100000.0)`
  = (near, z11, far). `perspective True` usa esos valores; un numero solo cambia z11.
- Matriz (`renpy/display/matrix_functions.pxi`, `perspective_matrix(w, h, n, p, f)`):
  p = z11 (ya no es la distancia de la camara: es el parametro de proyeccion)
  xdx = ydy = p, xdz = -w/2, ydz = -h/2, zdz = -(f+n)/(f-n), zdw = (-2fn + p(f+n))/(f-n), wdz = -1, wdw = p.
- Cada capa con `zpos` (de su transform) se proyecta hacia ese punto de mira.

## Lo que falta en el port

1. El kit (`renpykit/compare/reference.py:project`) aproxima con escala = foco / profundidad y resta el
   desplazamiento de la camara. No usa el punto de mira ni la matriz, y el signo de `xpos` no esta
   verificado contra Ren'Py. Hay que reemplazarlo por la formula exacta y probarla contra la matriz.
2. El motor no tiene profundidad por sprite ni punto de mira: CAMERA solo lleva zoom, x, y, cuadros y
   curva. Hay que anadir profundidad a SHOW/SCENE (o a los keyframes ANIM) y el punto de mira a CAMERA.
   Eso cambia el bytecode: subir version, actualizar docs/bytecode.md, compilador, simulador y motor en
   el mismo cambio.
3. La profundidad de las capas viene de sus transforms (`zpos`). En el capitulo 1, 387 de 875 capas
   tienen `zpos` en su ATL, y 188 de 189 escenas tienen camara con perspectiva.

## Orden propuesto

1. Kit: implementar la matriz exacta de Ren'Py en Python y validarla con casos numericos (test).
2. Kit: comparar la proyeccion contra un fotograma del PC conocido (cambio de camara sin otros movimientos).
3. Motor: anadir profundidad y punto de mira en fijo (aritmetica entera), con version de bytecode nueva.
4. Wani: emitir la profundidad y el punto de mira desde el kit; medir los ocho puntos de control.

## Plan propuesto para el paso 3 (requiere aprobacion: cambia el bytecode)

`CLAUDE.md` de vn-engine-ps1 exige plan y aprobacion antes de cambios grandes, y versionar el bytecode al
cambiar el formato. Este es el plan; no se ha implementado.

Opcodes nuevos (libres: 0x1B, 0x1C):
- `OP_PERSPECTIVE 0x1B`: activa o desactiva la camara con perspectiva; lleva z11 (u16, por defecto 1000) y
  profundidad de la camara zc (s16). Formato "HhB" (z11, zc, activa).
- `OP_DEPTH 0x1C`: profundidad de la capa `tag` para los siguientes SHOW/SCENE de ese tag. Formato "Bh" (tag, z).

Archivos a tocar en el mismo cambio:
1. `core/opcodes.h` (generado por tools/engine/gen_opcodes.py): los dos opcodes.
2. `core/vm.h`, `core/vm.c`: estado de perspectiva y profundidad por tag; guardado en `core/save.c` con la
   version nueva del formato de guardado.
3. `core/scene.c` / `app/main.c`: al dibujar, escala s = z11/(z11 - (z - zc)) en punto fijo, y posicion
   c + (x + dx - c) * s, con dx = -cam_x (mismo signo validado en capturas del PC).
4. `vncompiler/compilar.py` y `vncompiler/simulador.py`: nodos ps1_perspective y ps1_depth; tabla FORMATS.
5. `docs/bytecode.md`: subir la version y documentar 0x1B y 0x1C.
6. `tests/compiler/`: pruebas del formato y del simulador; prueba del motor en emulador con una escena de
   prueba (dos capas a profundidades distintas) comparada con el calculo del kit (renpykit/compare/perspective.py).

Validacion: primero el calculo del motor contra `perspective.py` con casos numericos; despues el disco de
prueba de Wani con perspectiva nativa, comparado contra la preview horneada (build/jugar-horneado) en los
ocho puntos de control. Solo entonces se decide si el horneado se reemplaza.

## Estado (2026-10-17, noche)

- Implementado: opcodes PERSPECTIVE (0x1B) y DEPTH (0x1C) en core/opcodes.h, VM (core/vm.c, core/vm.h), dibujo con escala desde el centro (app/main.c), compilador (vncompiler/compilar.py), simulador (FORMATS) y docs/bytecode.md (v3). 58 pruebas del compilador pasan; el motor compila para el preset wani.
- No usado en la preview de Wani todavia. Motivo medido: con DEPTH activo, la linea 113 pasa de 8.3 a 79.4 (el fondo se encoge 0.77 porque su zpos es -300; el PC no lo encoge). Con profundidad cero la linea 113 vuelve a 8.3, pero 369/428/478 empeoran. Sin resolver: el estado de perspectiva entre los dialogos 96 y 219 (bloque metro, tf_metro_cameramove) no coincide con el PC.
- Wani sigue con el horneado por dialogo (`camara_horneado.py`), que da 8.4/10.4/10.3/36.9/24.0/19.5/8.0 en los ocho puntos.
- Siguiente paso: entender que apaga la perspectiva del PC en el bloque metro y si el zpos de las capas aplica en ese caso.

## Estado (2026-10-17, madrugada): zzoom y modo de validacion

- Causa resuelta de la linea 113: el fondo tiene zpos -300 y `zzoom` (Ren'Py compensa el tamano y solo desplaza). El motor ahora tiene el indicador zzoom en DEPTH (formato BhB, bytecode v3) y aplica la misma formula que `reference.py:project` (compensacion (z11 - z)/z11, esquina a la izquierda y arriba, camara antes de escalar).
- Modo de validacion en Wani: `chapter_replay --camara-motor` (PERSPECTIVE y CAMERA del motor en vez de fotos horneadas). Resultado: 113 = 16.8, 369 = 82.4, 428 = 86.9, 478 = 86.8; el horneado da 8.4, 36.9, 24.0, 19.5.
- Causa encontrada (no es el dibujo nativo): el compositor del kit compensa zzoom con el ANCHO DE LA IMAGEN ORIGINAL (727 px en el fondo de 428), no con el lienzo de 320 px. Con 727 px el fondo queda en x = -200 y cubre el cuadro; con 320 px queda en x = -56 y deja un borde negro. Las capas del port son lienzos de 320 px ya colocados, asi que el motor no puede reproducir la compensacion.
- Para que el motor reproduzca el horneado hace falta stagear las capas originales (tamano real) y colocarlas con posicion absoluta. Eso es otro cambio de formato (posicion absoluta en SHOW o en ANIM). Hasta entonces, el horneado es la version fiel.
- La preview sigue con el horneado. Pruebas: wani-ps1 91 pasan (2 omitidas por audio); compilador del motor 58 pasan.
