/* Liberacion de texturas del backend SDL: solo la usan res.c (al desalojar) e img.c. */
#pragma once
#include "img.h"

/* Destruye la textura de la imagen (si la tiene) y la deja descargada. */
void img_release(Image *img);
