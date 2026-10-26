# Bytecode v3 (en curso)

Todo lo de la v1 de Snoot sigue igual: `docs/snoot-ps1/bytecode.md`. Esta página lista lo que la v2 agrega.
Desde 2026-10-15 existe el compilador común inicial en `vncompiler/` (Fase D en progreso).
Por ahora emite VNB1 con los operadores existentes: CALL/RETURN y LOAD_CHAPTER enlazan paquetes,
las variables son comunes y los textos tienen bases globales distintas. No hay cambio de formato ni versión.
Wani lo usa mediante su adaptador; el simulador de flujo se contrasta con `core/vm.c` nativo.
Python, pantallas, resolución visual de Ren'Py/audio y cobertura exhaustiva siguen pendientes.

## Entrada visual resuelta del compilador
El compilador acepta nodos intermedios `ps1_scene` (image, anim), `ps1_show`
(tag, image, position, z, flags, anim) y `ps1_hide` (tag). Emite los operadores existentes
SCENE 0x10, SHOW 0x11 y HIDE 0x12, validando rangos enteros antes de escribir.
No cambia VNB1, la VM ni la interpretación de los argumentos. El adaptador debe resolver
previamente imágenes, posiciones y animaciones; estos nodos no interpretan ATL de Ren'Py.

### Claves resueltas del compilador
`ps1_show` y `ps1_scene` aceptan `keyframes` y `loop` en vez de un índice `anim` explícito.
Cada clave contiene frame (cuadros), x/y (alineación 8.8), alpha (0..255), curve (0..3),
zoom (1/64, 1..255) y r/g/b (modulación, 128 neutro). De 1 a 64 claves, tiempos crecientes.
El compilador deduplica las secuencias dentro del paquete y escribe los offsets relativos de ANIM.
Se conserva el registro de 15 bytes y los encabezados VNB1.
No se aceptan todavía xzoom independiente ni recorte dentro de estas claves resueltas. El giro sí (abajo).

Desde 2026-10-23 también aceptan:
- `events`: cambios de imagen (`frame`, `image`, `flip`, `dissolve`), registro de 7 bytes que el motor ya
  leía (`scene_look` aplica el último evento cuyo cuadro ya pasó; el disolver se guarda pero hoy se corta).
  Vienen de los `"imagen" with transicion` dentro de un ATL.
- `loop_start`: índice de la clave donde vuelve a empezar el bucle, en los bits 1-6 del byte de flags de
  ANIM (0 en todo bytecode anterior: se repite completo). Así un ATL con `pause 4` y después `repeat`
  reproduce la introducción una vez. `core/scene.c` interpreta el bit; probado con `scene.c` compilado nativo.

`vncompiler.temporal.animation_from_timeline` traduce las cronologías del kit:
- `matrixcolor` que la GPU puede multiplicar (`TintMatrix`, `ColorizeMatrix` desde negro, `OpacityMatrix`)
  pasa a r/g/b/alfa de las claves. Las demás matrices fallan con "requiere imagen horneada".
- `xzoom -1` durante todo el evento devuelve `flip` (bit 0 de los flags de SHOW).
- Si `xzoom` salta entre 1 y -1 dentro de la animacion (y no hay cambios de imagen), el adaptador emite eventos de
  imagen sobre la misma imagen con el bit de espejo: uno en el cuadro 0, uno en cada cambio y uno al inicio del bucle.
- Cualquier propiedad que ANIM no dibuja (blur, giro 3D, crop, xsize, perspective...) falla con su nombre;
  nunca se descarta en silencio.
- `flip` y `loop_start` son opcionales (`allow_flip`, `allow_loop_intro`): un adaptador que no los copia al
  `ps1_show` sigue recibiendo el rechazo de antes. Los cambios de imagen exigen `resolve_child`.

### Giro en las claves ANIM (v3, flags de ANIM bit 7, PAKO-17)
- **Bit 7 del byte de flags de ANIM** (0x80): las claves traen giro. Con el bit en 1, los **bytes 9-10 de cada
  clave** son un `s16` con el ángulo en **1/4096 de vuelta** (0,088°), sentido horario como Ren'Py; alcanza
  ±8 vueltas sin envolver. Se interpola en línea recta con la curva de la clave, igual que el zoom.
- **Con el bit en 0 los bytes 9-10 se ignoran**, como siempre. Snoot (v1) escribe ahí `xzoom` y un giro de
  360/256 que su motor nunca dibujó; por eso no se leen sin el bit. El compilador solo enciende el bit si alguna
  clave tiene ángulo distinto de 0: lo que no gira sale byte a byte igual que antes (`64, 0`).
- **Pivote: el centro de la imagen** (escalada). `x`/`y` de la clave siguen siendo la alineación de la imagen
  sin girar; el motor la gira después alrededor de su centro (`img_draw_ex_rot`, un POLY_FT4 por pieza de
  ≤256 px con las cuatro esquinas giradas con `isin`/`icos`).
- El compilador (`vncompiler/temporal.py`, `rotated_center`) lleva Ren'Py a esa convención: calcula dónde
  queda el centro del sprite girado y alinea ahí el centro de la imagen. Con `transform_anchor` el anchor gira
  con el sprite y se queda en `pos + offset` (también con espejo). Sin él, el anchor se aplica a la caja girada,
  que con `rotate_pad` (activado por defecto; el kit no lo conserva) es un cuadrado del lado de la diagonal;
  los anchors se toman como fracción de la imagen. Una cronología sin ningún giro sigue el cálculo de antes.
- La tolerancia de claves suma el giro en píxeles (ángulo × media diagonal).
- `VM_SHOW_FROM_CURRENT` también captura el ángulo (`VmLook.angle`); una animación sin giro que parte de una
  captura girada vuelve a 0 en su primer tramo.
- Lo que se pierde: con el bit en 1 el byte 9 (`xzoom` de la v1) queda ocupado. La escala por eje necesitará
  otro bit o una versión nueva de la clave.
- Guardado: sin cambios (el aspecto se recalcula desde ANIM; `Vm.from` no se guarda).

### SHOW desde el aspecto actual (v3, flags bit3, PAKO-6)
`flags` de `SHOW` bit3 (`VM_SHOW_FROM_CURRENT`, 0x08): si el tag ya existe, trae animación y el SHOW la
reinicia (pos distinta de 254), el motor captura el aspecto que el sprite tiene en ese cuadro (x/y, alpha,
zoom, r/g/b, con `now - shown_at`) y lo usa en lugar de la clave 0 hasta la clave 1, solo en el primer
pase; en bucle las vueltas siguientes usan la clave 0 horneada. Imagen y volteo no se capturan.
Como Ren'Py con `show x at t` cuando el movimiento anterior sigue en curso por lectura rápida.
- El bit no se guarda en `VmSprite.flags`. Sin el bit, o en un sprite nuevo, todo sigue igual.
- Capturas encadenadas: la captura usa el aspecto vigente, que puede venir de otra captura.
- Al saltar no se captura (`VmHost.capture` devuelve 0): todo está asentado y vale la clave 0.
- Guardar/cargar: la captura (`Vm.from`) no va en el guardado; al cargar las animaciones se asientan
  como antes. El tamaño del guardado no cambia.
- El compilador solo debe poner el bit si la clave 0 es exactamente el estado asentado anterior (todo
  heredado). Si el ATL nuevo fija algo al empezar, la captura lo taparía.
- Formato: el registro SHOW de 9 bytes y el encabezado VNB1 no cambian; bit antes reservado (cero en
  todo bytecode anterior). `VmHost` gana el campo opcional `capture` (NULL: sin captura).

## Texto: etiquetas de temblor (Fase C)

Códigos de control nuevos en `TEXT_*` (`core/text.h`). Son de ancho cero: no se revelan como carácter.

| Código | Significado | Etiqueta Ren'Py |
|---|---|---|
| 0x07 | `{sh}`: el tramo tiembla junto (un mismo desplazamiento por cuadro) | `{sh}` ... `{/sh}` (382 usos en Wani) |
| 0x08 | fin de `{sh}` | `{/sh}` |
| 0x0E | `{sc}`: cada letra tiembla por su cuenta | `{sc}` ... `{/sc}` (9 usos en Wani) |
| 0x0F | fin de `{sc}` | `{/sc}` |

Decisión: la amplitud es de 1 píxel de PS1. Ren'Py usa 2 a 5 px en un lienzo de 1920 de ancho, y eso se
redondea a cero en una vista de 320.

## Menú de imágenes (Fase C, paso 6)

| Op | Nombre | Argumentos | Ren'Py |
|---|---|---|---|
| 0x19 | `IMGMENU` | fondo u16, n u8, n × (imagen u16, x s16, y s16, visto u16, destino u32) (4 + 12n) | pantalla con `imagebutton` y `action Jump(...)` (cofre de Olivia en Wani) |

- `x`, `y`: píxeles de la vista de 320x180 (la PC convierte desde 1920x1080). `y` se cuenta desde el borde
  superior de la vista.
- `visto`: id de bit de progreso (el mismo que `MARK_SEEN`). Si está marcado, el botón se dibuja apagado
  (`at grayout`) y sigue elegible. `0xFFFF` = nunca se apaga.
- Navegación: izquierda/arriba anterior, derecha/abajo siguiente, X elige. El cursor se marca con un
  recuadro amarillo.
- Usa el mismo camino que `MENU` para reanudar (`menu_target[elegido]`).
- Las imágenes del fondo y de los botones deben estar en el índice de imágenes para que el disco las cargue.
- Sin probar: ninguna escena de Snoot usa `IMGMENU`; falta una escena de Wani o de prueba.

## Chat de teléfono (Fase C, paso 7)

| Op | Nombre | Argumentos | Ren'Py |
|---|---|---|---|
| 0x1A | `PHONE` | n u8, n × (lado u8, texto u16, foto u16) (2 + 5n) | los mensajes de `phone discussion` (Better EMR Phone) |

- Va seguido de una instrucción `SPECIAL` con el id del chat (el módulo `special_phone`, `modules/phone.c`).
  `PHONE` solo deja los mensajes; `SPECIAL` abre el chat.
- `lado`: 0 = el otro personaje (izquierda), 1 = la protagonista (derecha).
- `texto`: id de la tabla de textos (se revisa contra el rango del capítulo). Los saltos de línea van dentro del
  texto (el compilador los pone; el motor no parte líneas). La PC tiene que partir las líneas para que quepan en la burbuja de 150 px; el motor no las parte.
- `foto`: 0 = sin foto; si no, id de imagen que va encima del texto.
- Máximo 32 mensajes. Arriba/abajo recorre, X sale.
- Sin probar: ninguna escena de Snoot usa el chat nuevo; falta una escena de Wani.

## Lienzo de dibujo (Fase C, paso 8) y memory card

- Lienzo `modules/canvas.c`, abierto con una instrucción `SPECIAL` del id que asigne cada juego. La cruceta mueve
  el cursor, X traza mientras se mantiene, O deshace el último trazo, L1 cambia el grosor (1 a 3), Start termina.
- El dibujo es un mapa de 128x72 a 1 bit (1152 bytes), después de las tres ranuras (`OFS_CANVAS`).
  El perfil determina el tamaño del texto leído: Snoot usa 2048 bytes (dibujo en 5184; total 6336),
  Wani usa 3072 bytes (dibujo en 6208; total 7360), de 7936 bytes de datos por copia.
  Los perfiles tienen archivos de memory card distintos y una comprobación de tamaño al compilar.
- No es un operador del bytecode: no cambia el formato del guion.

## Orden de dibujo (ORDER)

`0x18 ORDER` (tag u8, ref u8, above u8) existia en el motor desde snoot-ps1; el compilador lo emite con el nodo
`ps1_order`. Pone `tag` con la z de `ref` y justo encima (above 1) o debajo (above 0) en el orden de creacion; con
above 0 no hace nada si `tag` ya esta debajo de `ref`. No cambia el formato del guion.

## Perspectiva por capa (v3)

Dos opcodes nuevos. No cambian el encabezado VNB1 ni los demas opcodes.

| Opcode | Nombre | Campos | Uso |
|---|---|---|---|
| 0x1B | `PERSPECTIVE` | z11 u16, zc s16, activa u8 (4 bytes + 1) | Camara con perspectiva de Ren'Py. z11 por defecto 1000; zc es la profundidad de la camara; activa 0/1. |
| 0x1C | `DEPTH` | tag u8, z s16, zzoom u8 (4 bytes) | Profundidad de la capa `tag` para el SHOW que sigue. zzoom 1 compensa el tamano como `zzoom` de Ren'Py (la capa conserva su tamano y solo se desplaza). Solo cuenta si la perspectiva esta activa. |

Escala de cada sprite (Ren'Py 8.3.7): `s = z11 / (z11 - (z - zc))`. El motor traslada primero por la camara
(CAMERA, en pixeles de vista) y despues escala desde el centro de la vista; el centro queda fijo. Si
`z11 - (z - zc) <= 0` la capa no se dibuja.

La perspectiva no va en el guardado (igual que CAMERA): al cargar, la siguiente SAY vuelve a emitir las capas
con su profundidad, porque el compilador repite SCENE/SHOW en cada dialogo.

Validado con capturas del PC (ver `docs/camara-perspectiva.md`): la escena se desplaza en sentido contrario a xpos.


## Audio resuelto del compilador (2026-10-18)

`ps1_audio` recibe `action` y campos enteros ya resueltos por el port. Acciones:
`music_play` (id, fade, flags), `music_stop` (fade), `music_queue` (id),
`ambient_play` (slot, id, fade), `ambient_stop` (slot, fade), `sfx_play` (id),
`sfx_stop` (fade) y `volume` (channel, volume, fade). `fade` en decimas,
`volume` 0..255, ranuras 0..3 y canales VOLUME 0..5. Ids 0..255 (MAX_AUDIO).
Se serializan los opcodes 0x20..0x27 existentes; no cambia VNB ni AIX1.

SFX_STOP ahora aplica su argumento de fundido: actualiza el volumen de las voces
SPU 4..23 y las apaga al llegar a cero. VOLUME sin fundido tiene efecto inmediato,
incluso si PLAY se ejecuta en el mismo cuadro. El port puede crear un fadein de
SFX con VOLUME(0), VOLUME(255, tiempo), SFX_PLAY. La entrada de la onda conserva
la ganancia propia del efecto. Los ambientes usan sus cuatro voces independientes.
