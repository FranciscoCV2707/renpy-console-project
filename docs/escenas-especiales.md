# Escenas especiales por consola

Pantallas que no son guion (`SPECIAL id` del VNB): cómo se controlan en cada consola y cómo se ven. El
teclado de cada módulo es siempre el mismo (dibujado por el núcleo en 320×240); los backends solo traducen
sus mandos y su táctil a esa pantalla.

## Teclado en pantalla (SPECIAL 3, capítulo 13D de Snoot)

El `renpy.input("What will you write?")` del anuario
(`E:\snoot\snootgame\game\script\13D...rpy:3240`) compila a `SPECIAL 3` y abre
`engine/modules/keyboard.c`: 5 filas de 10 teclas (números, qwerty con ñ, acentos, signos) más una fila de
acciones (Mayús, espacio, borrar, OK). **En Ren'Py lo escrito no se usa después**: el resultado del
`renpy.input` no se asigna a nada (línea 3240, sin variable), así que el teclado solo tiene que dejar
escribir algo y continuar.

### Controles (un botón escribe, otro borra, otro cambia mayúsculas, Start confirma)

| Plataforma | Moverse | Escribir | Borrar | Mayúsculas | Confirmar | Táctil |
|---|---|---|---|---|---|---|
| PC (teclado) | flechas o WASD | X, Enter, Espacio | Esc | Q | F1 | — |
| PC (mando SDL) | cruceta o stick izquierdo | A (cruz) | B (círculo) | L1 | Start | — |
| PS1 | cruceta | ✗ | ○ | L1 | Start | — |
| PS2 / PSP / Vita / PS3 / PS4 / Switch | cruceta o stick | ✗ / A | ○ / B | L1 | Start / Options | Vita: tocar la tecla |
| Wii | cruceta o stick | A | B | L1 (C) | Start | — |
| 3DS | cruceta o stick (C-pad) | A | B | L | Start | tocar la tecla (pantalla inferior) |
| DS | cruceta o stick | A | B | L | Start | tocar la tecla (pantalla de abajo) |
| Xbox clásica | cruceta o stick | A | B | L1 | Start | — |

- El stick izquierdo mueve el cursor igual que la cruceta en todos los backends SDL
  (`platforms/sdl/input.c`, umbral 16000).
- La táctil llega al núcleo con `input_touch(&x, &y)` (`engine/platform/input.h`): una consulta de una
  lectura con la posición en coordenadas de guion (320×240). Tocar una tecla la activa directamente
  (escribe, cambia Mayús, borra o confirma); tocar fuera del teclado no hace nada. Los backends sin
  táctil (PS1, GBA) no la definen: el teclado lleva un símbolo débil que devuelve 0.
- DS: el teclado ya se dibuja en la pantalla de abajo (todos los textos del motor van ahí); el táctil de
  libnds se convierte de 256×192 a 320×240 (escala 4/5 de `platforms/ds/source/video.c`).
- SDL (Vita, 3DS, Switch): `SDL_FINGERDOWN` da la posición normalizada a la ventana; se convierte con el
  mapeo inverso del que usa `video.c` para dibujar (escala manual en PSP/Vita/PS3/PS4, tamaño lógico en
  3DS/Switch). En 3DS el teclado queda 1:1 en la pantalla táctil (320×240).

### Tamaño de teclas por resolución (propuesta)

El núcleo dibuja en 320×240 y cada backend lo escala a su ventana, así que la geometría es la misma
(tecla 28×18 en coordenadas de guion). Tamaño efectivo según la vista de `sdl_target.h`:

| Plataforma | Vista | Tecla efectiva | Comentario |
|---|---|---|---|
| PC | 960×720 (lógico 320×240) | 84×54 | Verificado en las capturas del escenario |
| PSP | 360×272 en 480×272 | ~32×20 | Legible; el margen de 60 px deja el fondo visible |
| Vita | 640×480 en 960×544 | 56×36 | Cómodo para el dedo |
| Switch | 1280×720 | 112×72 | Muy cómodo; sobra espacio |
| PS4 | 1280×960 en 1920×1080 | 112×72 | Igual que Switch |
| PS3 | 320×240 en 1280×720 | 28×18 | Tecla pequeña: proponer subir la vista a 2× (pendiente de T-627) |
| 3DS | 320×240 en 400×240 | 28×18 | 1:1 con la pantalla táctil inferior |
| DS | 256×192 (escala 4/5) | ~22×14 | El más pequeño: tocable en la pantalla de abajo; si en melonDS cuesta acertar, duplicar la altura de tecla solo en DS |

Capturas verificadas (PC, `ctl run --target pc --scenario tests/scenarios/snoot-keyboard.yaml`):
`teclado` (teclado abierto, campo vacío), `teclado_texto` ("hi" escrito con la cruceta),
`teclado_mayus` ("hI" tras borrar una letra y pasar a mayúsculas), `anuario` (la escena tras confirmar).

### Prueba

`tests/scenarios/snoot-keyboard.yaml` llega por el menú de desarrollo (L1+R1+Select, fila 29 = 13D ruta 4),
salta el capítulo con R1 y en el teclado escribe "hi" con la cruceta, borra una letra, pasa a mayúsculas
("hI"), confirma con Start y sigue el guion. La traza se compara contra
`tests/reference/traces/pc/snoot-keyboard.trace` (D22: cuadros solo contra la misma plataforma).
