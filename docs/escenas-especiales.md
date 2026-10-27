# Escenas especiales

## textscroll (chat del teléfono, capítulo 4)

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
