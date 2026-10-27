# Solo para la copia de captura de Snoot (tools/renpy_trace/record.py). La pantalla textscroll del capitulo 4 es el
# telefono que el jugador desliza hasta el final para tocar un boton; kit_capture.rpy no sabe hacerlo y la ruta se
# queda ahi. Esta version devuelve sola, como el boton (misc_definitions.rpy:192), sin decir nada en el guion.
init offset = 999

screen textscroll():
    timer 0.5 action Return()
