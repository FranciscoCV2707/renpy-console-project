#include "special.h"

static int inco_begin(void)
{
	fmv_select(5);
	return special_fmv.begin();
}

static int olivia_begin(void)
{
	fmv_select(2);
	return special_fmv.begin();
}

static int intro_update(void)
{
	return special_fmv.update();
}

static void intro_draw(void)
{
	special_fmv.draw();
}

static const Special inco_intro = {
	SP_IN_GAME | SP_OWN_R1 | SP_OWN_SCENE, inco_begin, intro_update, intro_draw, 0
};
static const Special olivia_intro = {
	SP_IN_GAME | SP_OWN_R1 | SP_OWN_SCENE, olivia_begin, intro_update, intro_draw, 0
};

const SpecialEntry game_specials[] = {
	{ 1, &special_strips },
	{ 2, &special_credits },
	{ 3, &special_keyboard },
	{ 4, &special_phone },
	{ 5, &special_canvas },
	{ 250, &special_fmv },
	{ 200, &inco_intro },
	{ 201, &olivia_intro },
};
const int game_special_count = sizeof(game_specials) / sizeof(game_specials[0]);
