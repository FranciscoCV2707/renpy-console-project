# Escenas especiales

## textscroll (chat del teléfono, capítulo 4)
- Escena: `call screen textscroll` en el capítulo 4 de Snoot Game. El compilador corta la imagen `texts` en tiras de 320x180 a escala 0.4 (pensado para PS1).
- Módulo: `engine/modules/strips.c`, registrado como especial id 1 (`games/snoot/specials.c`).
- Comportamiento: empieza abajo (`strip_pos = strip_count*VIEW_H - VIEW_H`). Se desplaza con UP/DOWN; manteniendo R1 acelera. En el motor modificado se añade aceleración con stick analógico, saltos con L1/R1 (página) y soporte básico de arrastre táctil si el backend lo provee.
- Salida: al llegar al inicio (arriba) se muestra el aviso "PULSA X PARA CONTINUAR"; pulsando CROSS se sale. Esto coincide con el flujo original.
- Legibilidad: 0.4 es correcto para 320x240 (PS1). En resoluciones mayores (PSP, Vita, PS2, Switch, PS4) el chat se ve más pequeño; para cada plataforma conviene valorar una escala distinta (o generar otra versión de las tiras) sin cambiar el contrato VNB. Ver `reports/T-625.md` con capturas y medidas.
- Controles por consola: D-pad/stick para desplazar (con aceleración), L/R para salto de página; táctil (arrastrar) en DS/3DS/Vita cuando el backend lo implemente. La lógica de entrada va en `platforms/*/input` o macros en `platforms/sdl/sdl_target.h`, sin `#ifdef` en `engine/`.
