#include "input.h"
#include "ds_internal.h"
#include <nds.h>
#include <stdio.h>
#include <string.h>

volatile uint32_t autotest_autoplay, autotest_quit;
static const uint8_t *script;
static int count, choice_at, frame;
static uint8_t done[2800];
static uint16_t cur, prev;
static int touch_x, touch_y, touch_hit;

void input_init(int with_card)
{
	(void)with_card;
	cur = prev = 0;
	frame = 0;
	choice_at = 0;
	autotest_autoplay = 0;
	autotest_quit = 0;
}

void input_set_script(const uint8_t *entries, int n)
{
	script = entries;
	count = n;
	choice_at = 0;
	frame = 0;
	memset(done, 0, sizeof(done));
}

void input_update(void)
{
	scanKeys();
	uint32_t keys = keysHeld();
	prev = cur;
	cur = 0;

	if (keys & KEY_A)
		cur |= BTN_CROSS;
	if (keys & KEY_B)
		cur |= BTN_CIRCLE;
	if (keys & KEY_X)
		cur |= BTN_SQUARE;
	if (keys & KEY_Y)
		cur |= BTN_TRIANGLE;
	if (keys & KEY_START)
		cur |= BTN_START;
	if (keys & KEY_SELECT)
		cur |= BTN_SELECT;
	if (keys & KEY_UP)
		cur |= BTN_UP;
	if (keys & KEY_DOWN)
		cur |= BTN_DOWN;
	if (keys & KEY_LEFT)
		cur |= BTN_LEFT;
	if (keys & KEY_RIGHT)
		cur |= BTN_RIGHT;
	if (keys & KEY_L)
		cur |= BTN_L1;
	if (keys & KEY_R)
		cur |= BTN_R1;

	/* Tactil de la pantalla de abajo: el teclado se dibuja ahi con la escala 4/5 del guion (video.c),
	 * asi que la posicion se convierte de 256x192 a 320x240. Solo al tocar, no mientras se mantiene. */
	if (keysDown() & KEY_TOUCH) {
		touchPosition touch = touchReadXY();

		touch_x = touch.px * 5 / 4;
		touch_y = touch.py * 5 / 4;
		touch_hit = 1;
	}

	for (int i = 0; i < count; i++) {
		const uint8_t *p = script + 6 * i;
		uint32_t at = p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
		uint16_t val = (uint16_t)(p[4] | (p[5] << 8));
		if (frame < (int)at || done[i])
			continue;
		done[i] = 1;
		if (val == 0xfffe) {
			autotest_quit = 1;
		} else if (val == 0xfffd) {
			autotest_autoplay = 1;
		} else if (val == 0xfffc) {
			autotest_autoplay = 0;
		} else if (val < 0xffe0) {
			cur |= val;
		}
	}
	frame++;

	if (autotest_quit) {
		static int done_written = 0;
		if (!done_written) {
			done_written = 1;
			FILE *f = fopen("fat:/done.txt", "w");
			if (f) {
				fputs("AUTOTEST_DONE\n", f);
				fclose(f);
			}
			ds_close_trace();
		}
	}
}

int input_down(uint16_t mask)
{
	return (cur & mask) != 0;
}

int input_pressed(uint16_t mask)
{
	return (cur & ~prev & mask) != 0;
}

int input_raw_down(uint16_t mask)
{
	return input_down(mask);
}

int input_touch(int *x, int *y)
{
	if (!touch_hit)
		return 0;
	touch_hit = 0;
	*x = touch_x;
	*y = touch_y;
	return 1;
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

int input_stick_x(void)
{
	return 0;
}

int input_stick_y(void)
{
	return 0;
}

int input_touch_down(int *x, int *y)
{
	uint32_t keys = keysHeld();
	if (keys & KEY_TOUCH) {
		touchPosition touch;
		touchRead(&touch);
		if (x)
			*x = touch.px;
		if (y)
			*y = touch.py;
		return 1;
	}
	if (x)
		*x = 0;
	if (y)
		*y = 0;
	return 0;
}
