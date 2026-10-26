#include "special.h"

/* Juego sin tabla propia: los tres modulos de siempre con los ids de Snoot */
const SpecialEntry game_specials[] = {
	{ 1, &special_strips },
	{ 2, &special_credits },
	{ 3, &special_keyboard },
	{ 250, &special_fmv },     /* video de la galeria (SPECIAL_VIDEO en app/main.c) */
};
const int game_special_count = sizeof(game_specials) / sizeof(game_specials[0]);
