# Escenas especiales por consola

Pantallas que no son guion (`SPECIAL id` del VNB): cómo se controlan en cada consola y cómo se ven. El
teclado de cada módulo es siempre el mismo (dibujado por el núcleo en 320×240); los backends solo traducen
sus mandos y su táctil a esa pantalla.

## Chat del teléfono (SPECIAL 1, `textscroll`, capítulo 4 de Snoot)

- **Ren'Py original:** `call screen textscroll with dissolve` en `E:\snoot\snootgame\game\script\4.anon-needs-help-during-music-period.rpy:1238`. Pantalla en `E:\snoot\snootgame\game\src\misc_definitions.rpy:192` (`screen textscroll():`): `viewport` con `draggable True` + `arrowkeys True`, `yinitial 1.0` (empieza abajo), imagen larga `add "texts"` y botón `fangbutton` que hace `Return()`.
- **Compilador:** `E:\Dev\snoot-ps1\tools\script_compiler\lower.py:115-133` (`textscroll_pages`) y `TEXTSCROLL_SCALE = 0.4` (`lower.py:20`): corta `images/other/texts.webp` en tiras de `180 / 0.4` filas del original, receta `Transform zoom` y emite `SPECIAL 1`.
- **Motor:** `engine/modules/strips.c` (`special_strips`), registrado como `SPECIAL 1` en `games/snoot/specials.c`. Captura de Ren'Py la omite (`tools/renpy_trace/snoot_capture.rpy:5-6` redefine `screen textscroll()` con `timer 0.5 Return()`).
- **Comportamiento:** empieza abajo (`strip_pos = strip_count*VIEW_H - VIEW_H`). Desplaza con cruceta/arriba-abajo o stick analógico (`input_stick_y` en `engine/platform/input.h`); si se mantiene, acelera a 12 px/cuadro. L1/R1 saltan una pantalla (`VIEW_H`) cuando no se está desplazando. Arrastre táctil (`input_touch_down`) mueve proporcional al desplazamiento del dedo.
- **Salida:** al llegar arriba (`strip_pos == 0`) aparece “PULSA X PARA CONTINUAR” y `CROSS` sale (`return strip_pos == 0 && input_pressed(BTN_CROSS)`), como el botón del original.
- **Legibilidad (escala):** 0.4 es para PS1 (320x240, `VIEW_H=180`). En resoluciones mayores el chat ocupa menos del alto y el texto puede verse pequeño. Propuesta por resolución (ver capturas en `reports/T-625.md`):
  - 320x240 (PS1): 0.4 (actual, una tira = 450 filas originales).
  - 360x272–480x272 (PSP/3DS): 0.55–0.6 (texto ~37% más grande, ~3 tiras menos).
  - 640x480 (Vita/PS2): 0.8–0.9; 960x544+ (Switch/PS4): 1.0 (sin reducción).
  - Para no romper el contrato VNB, el empaquetador generaría un segundo juego de tiras con otro `TEXTSCROLL_SCALE` y el backend elegiría el set por `SCREEN_W` (sin cambiar `special_strips`).
- **Controles por consola:** D-pad y stick con aceleración al mantener; L1/R1 salto de página; táctil al arrastrar en DS/3DS/Vita (cuando el backend implementa `input_touch_down`). Lógica dependiente de consola en `platforms/*/input` o macros en `platforms/sdl/sdl_target.h`, sin `#ifdef` en `engine/`.

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
