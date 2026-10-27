#include "input.h"
#include "gba_internal.h"
#include <tonc.h>
#include <string.h>
#include <stdio.h>

volatile uint32_t autotest_autoplay = 0;
volatile uint32_t autotest_quit = 0;

static const uint8_t *script = NULL;
static int count = 0;
static int frame = 0;
static uint8_t done[2800] __attribute__((section(".sbss")));
static uint16_t cur = 0, prev = 0;
static int choice_at = 0;

void input_init(int with_card)
{
	(void)with_card;
	cur = prev = 0;
	frame = 0;
	autotest_autoplay = 0;
	autotest_quit = 0;
	choice_at = 0;
}

void input_set_script(const uint8_t *entries, int n)
{
	script = entries;
	count = n;
	frame = 0;
	choice_at = 0;
	memset(done, 0, sizeof(done));
	char msg[64];
	snprintf(msg, sizeof(msg), "GBA: SCRIPT SET n=%d", n);
	mgba_log(msg);
}

void input_update(void)
{
	key_poll();
	u32 keys = ~REG_KEYINPUT & 0x03FF;
	prev = cur;
	cur = 0;

	if (keys & KEY_A)
		cur |= BTN_CROSS;
	if (keys & KEY_B)
		cur |= BTN_CIRCLE;
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

	for (int i = 0; i < count; i++) {
		const uint8_t *p = script + 6 * i;
		uint32_t at = p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
		uint16_t val = (uint16_t)(p[4] | (p[5] << 8));
		if (frame < (int)at || done[i])
			continue;
		done[i] = 1;
		if (val == 0xfffe) {
			autotest_quit = 1;
			mgba_log("GBA: SCRIPT QUIT");
		} else if (val == 0xfffd) {
			autotest_autoplay = 1;
			mgba_log("GBA: SCRIPT AUTOPLAY");
		} else if (val == 0xfffc) {
			autotest_autoplay = 0;
		} else if (val < 0xffe0) {
			cur |= val;
			char msg[64];
			snprintf(msg, sizeof(msg), "GBA: SCRIPT FRAME %d PRESS 0x%04x", frame, val);
			mgba_log(msg);
		}
	}

	frame++;

	if (autotest_quit) {
		static int done_sent = 0;
		if (!done_sent) {
			done_sent = 1;
			mgba_log("AUTOTEST_DONE");
		}
	}
}

int input_down(uint16_t mask)
{
	return (cur & mask) != 0;
}

int input_pressed(uint16_t mask)
{
	return (cur & mask) && !(prev & mask);
}

int input_raw_down(uint16_t mask)
{
	return input_down(mask);
}

int input_autotest_choice(void)
{
	for (; choice_at < count; choice_at++) {
		const uint8_t *e = script + 6 * choice_at;
		int value = e[4] | (e[5] << 8);

		if (value >= 0xffe0 && value < 0xffe0 + 16) {
			choice_at++;
			return value - 0xffe0;
		}
	}
	return -1;
}

/* La GBA no tiene stick analogico ni pantalla tactil */
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
	(void)x;
	(void)y;
	return 0;
}
