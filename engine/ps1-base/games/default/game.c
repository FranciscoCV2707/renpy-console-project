#include "game.h"

/* Juego sin reglas propias: los capitulos extra se abren al ver cualquier final. */
int game_extra_unlocked(int i, uint32_t endings_mask, uint32_t bonus_mask)
{
	(void)i;
	(void)bonus_mask;
	return endings_mask != 0;
}
