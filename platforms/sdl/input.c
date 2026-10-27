#include "input.h"
#include "video.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

volatile uint32_t autotest_autoplay, autotest_quit;
static volatile uint32_t autotest_shot;
static const uint8_t *script;
static int count, choice_at, frame;
static uint8_t done[2800];
static uint16_t cur, prev;
static int shot_pending;
#ifndef __PSP__
static SDL_GameController *controller;
#endif
extern void sdl_shot_request(void);
void input_init(int card)
{
	(void)card;
#ifndef __PSP__
	if (SDL_NumJoysticks() > 0 && SDL_IsGameController(0))
		controller = SDL_GameControllerOpen(0);
#endif
}
void input_set_script(const uint8_t *p, int n)
{
	script = p;
	count = n;
	choice_at = 0;
	frame = 0;
	memset(done, 0, sizeof(done));
}
void input_update(void)
{
	SDL_Event e;
	const Uint8 *k;
	int i;
	prev = cur;
	cur = 0;
	while (SDL_PollEvent(&e))
		if (e.type == SDL_QUIT)
			autotest_quit = 1;
	k = SDL_GetKeyboardState(NULL);
#define KEY(key, bit)                                                                                                  \
	if (k[SDL_GetScancodeFromKey(key)])                                                                            \
	cur |= (bit)
	KEY(SDLK_ESCAPE, BTN_CIRCLE);
	KEY(SDLK_RETURN, BTN_CROSS);
	KEY(SDLK_SPACE, BTN_CROSS);
	KEY(SDLK_BACKSPACE, BTN_SQUARE);
	KEY(SDLK_TAB, BTN_TRIANGLE);
	KEY(SDLK_UP, BTN_UP);
	KEY(SDLK_w, BTN_UP);
	KEY(SDLK_RIGHT, BTN_RIGHT);
	KEY(SDLK_d, BTN_RIGHT);
	KEY(SDLK_DOWN, BTN_DOWN);
	KEY(SDLK_s, BTN_DOWN);
	KEY(SDLK_LEFT, BTN_LEFT);
	KEY(SDLK_a, BTN_LEFT);
	KEY(SDLK_q, BTN_L1);
	KEY(SDLK_e, BTN_R1);
	KEY(SDLK_LSHIFT, BTN_L2);
	KEY(SDLK_RSHIFT, BTN_R2);
	KEY(SDLK_F1, BTN_START);
	KEY(SDLK_F2, BTN_SELECT);
#undef KEY
#ifndef __PSP__
	if (controller) {
		SDL_GameControllerUpdate();
#define PAD(button, bit)                                                                                               \
	if (SDL_GameControllerGetButton(controller, button))                                                           \
	cur |= (bit)
		PAD(SDL_CONTROLLER_BUTTON_BACK, BTN_SELECT);
		PAD(SDL_CONTROLLER_BUTTON_START, BTN_START);
		PAD(SDL_CONTROLLER_BUTTON_DPAD_UP, BTN_UP);
		PAD(SDL_CONTROLLER_BUTTON_DPAD_RIGHT, BTN_RIGHT);
		PAD(SDL_CONTROLLER_BUTTON_DPAD_DOWN, BTN_DOWN);
		PAD(SDL_CONTROLLER_BUTTON_DPAD_LEFT, BTN_LEFT);
		PAD(SDL_CONTROLLER_BUTTON_LEFTSHOULDER, BTN_L1);
		PAD(SDL_CONTROLLER_BUTTON_RIGHTSHOULDER, BTN_R1);
		PAD(SDL_CONTROLLER_BUTTON_Y, BTN_TRIANGLE);
		PAD(SDL_CONTROLLER_BUTTON_B, BTN_CIRCLE);
		PAD(SDL_CONTROLLER_BUTTON_A, BTN_CROSS);
		PAD(SDL_CONTROLLER_BUTTON_X, BTN_SQUARE);
#undef PAD
		if (SDL_GameControllerGetAxis(controller, SDL_CONTROLLER_AXIS_TRIGGERLEFT) > 16000)
			cur |= BTN_L2;
		if (SDL_GameControllerGetAxis(controller, SDL_CONTROLLER_AXIS_TRIGGERRIGHT) > 16000)
			cur |= BTN_R2;
	}
#endif
	for (i = 0; i < count; i++) {
		const uint8_t *p = script + 6 * i;
		uint32_t at = p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
		uint16_t val = (uint16_t)(p[4] | (p[5] << 8));
		if (frame < (int)at || done[i])
			continue;
		done[i] = 1;
		if (val == 0xffff) {
			autotest_shot++;
			shot_pending = 1;
		} else if (val == 0xfffe)
			autotest_quit = 1;
		else if (val == 0xfffd)
			autotest_autoplay = 1;
		else if (val < 0xffe0)
			cur |= val;
	}
	frame++;
	if (shot_pending) {
		sdl_shot_request();
		shot_pending = 0;
	}
	if (autotest_quit)
		exit(0);
}
int input_down(uint16_t m)
{
	return (cur & m) != 0;
}
int input_pressed(uint16_t m)
{
	return (cur & ~prev & m) != 0;
}
int input_raw_down(uint16_t m)
{
	return input_down(m);
}
int input_autotest_choice(void)
{
	for (; choice_at < count; choice_at++) {
		const uint8_t *p = script + 6 * choice_at;
		int v = p[4] | (p[5] << 8);
		if (v >= 0xffe0 && v < 0xfff0) {
			choice_at++;
			return v - 0xffe0;
		}
	}
	return -1;
}
