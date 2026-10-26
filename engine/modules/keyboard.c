#include <string.h>
#include "app.h"
#include "input.h"
#include "special.h"
#include "text.h"
#include "ui_text.h"
#include "video.h"

/* Teclado en pantalla (renpy.input). Snoot: el mensaje del capitulo 13D; lo escrito no se guarda. */
#define KB_COLS 10
#define KB_ROWS 6                            /* 5 de teclas y la de acciones */
#define KB_MAX 36                            /* caracteres: una linea */
#define KB_X 20
#define KB_Y 84
#define KB_W 28
#define KB_H 18

static const char *const kb_keys[2][KB_ROWS - 1][KB_COLS] = {
	{ { "1", "2", "3", "4", "5", "6", "7", "8", "9", "0" },
	  { "q", "w", "e", "r", "t", "y", "u", "i", "o", "p" },
	  { "a", "s", "d", "f", "g", "h", "j", "k", "l", "ñ" },
	  { "z", "x", "c", "v", "b", "n", "m", ",", ".", "?" },
	  { "á", "é", "í", "ó", "ú", "¿", "¡", "!", "'", "-" } },
	{ { "1", "2", "3", "4", "5", "6", "7", "8", "9", "0" },
	  { "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P" },
	  { "A", "S", "D", "F", "G", "H", "J", "K", "L", "Ñ" },
	  { "Z", "X", "C", "V", "B", "N", "M", ",", ".", "?" },
	  { "Á", "É", "Í", "Ó", "Ú", "¿", "¡", "!", "'", "-" } },
};
#define kb_actions (game_text + T_KB_SHIFT)              /* 4 entradas seguidas en ui_text.h */
static char kb_text[KB_MAX * 2 + 1];
static int kb_len, kb_row, kb_col, kb_upper, kb_wait;

static int kb_begin(void)
{
	kb_len = kb_row = kb_col = kb_upper = 0;
	kb_text[0] = 0;
	return 1;
}

static void kb_type(const char *s)
{
	int n = (int)strlen(s), used = (int)strlen(kb_text);

	if (kb_len >= KB_MAX || used + n >= (int)sizeof(kb_text))
		return;
	memcpy(kb_text + used, s, n + 1);
	kb_len++;
}

static void kb_erase(void)
{
	int used = (int)strlen(kb_text);

	if (!kb_len)
		return;
	while (used > 0 && (kb_text[used - 1] & 0xC0) == 0x80)   /* bytes de continuacion de UTF-8 */
		used--;
	kb_text[used - 1] = 0;
	kb_len--;
}

static int kb_update(void)
{
	if (input_pressed(BTN_UP))
		kb_row = (kb_row + KB_ROWS - 1) % KB_ROWS;
	if (input_pressed(BTN_DOWN))
		kb_row = (kb_row + 1) % KB_ROWS;
	if (input_pressed(BTN_LEFT))
		kb_col = (kb_col + KB_COLS - 1) % KB_COLS;
	if (input_pressed(BTN_RIGHT))
		kb_col = (kb_col + 1) % KB_COLS;
	if (input_pressed(BTN_L1))
		kb_upper = !kb_upper;
	if (input_pressed(BTN_CIRCLE))
		kb_erase();
	if (input_pressed(BTN_START))
		return 1;
	if (!input_pressed(BTN_CROSS))
		return 0;
	if (kb_row < KB_ROWS - 1) {
		kb_type(kb_keys[kb_upper][kb_row][kb_col]);
		return 0;
	}
	switch (kb_col * 4 / KB_COLS) {
	case 0:
		kb_upper = !kb_upper;
		break;
	case 1:
		kb_type(" ");
		break;
	case 2:
		kb_erase();
		break;
	default:
		return 1;
	}
	return 0;
}

static void kb_key(int x, int y, int w, const char *label, int sel)
{
	font_draw(LAYER_TEXT, x + (w - font_width(label)) / 2, y + 2, label, sel ? 255 : 128, sel ? 220 : 128, sel ? 40 : 128);
	video_rect(LAYER_TEXT, x + 1, y, w - 2, KB_H - 2, sel ? 90 : 40, sel ? 70 : 40, sel ? 10 : 40, 0);
}

static void kb_draw(void)
{
	int r, c, action = kb_row == KB_ROWS - 1 ? kb_col * 4 / KB_COLS : -1;

	panel();
	draw_center(28, TX(T_KB_TITLE), 255, 220, 40);
	font_draw(LAYER_TEXT, 24, 56, kb_text, 128, 128, 128);
	if ((video_frames() / 20) & 1)
		video_rect(LAYER_TEXT, 25 + font_width(kb_text), 57, 2, font_line_height() - 2, 255, 220, 40, 0);
	video_rect(LAYER_TEXT, 16, 52, SCREEN_W - 32, KB_H + 2, 30, 30, 30, 0);
	for (r = 0; r < KB_ROWS - 1; r++)
		for (c = 0; c < KB_COLS; c++)
			kb_key(KB_X + c * KB_W, KB_Y + r * KB_H, KB_W, kb_keys[kb_upper][r][c], r == kb_row && c == kb_col);
	for (c = 0; c < 4; c++)
		kb_key(KB_X + c * (KB_W * KB_COLS / 4), KB_Y + (KB_ROWS - 1) * KB_H, KB_W * KB_COLS / 4,
		       c == 0 && kb_upper ? TX(T_KB_SHIFT_ON) : kb_actions[c], c == action);
	draw_center(SCREEN_H - 22, TX(T_KB_HELP), 96, 96, 96);
}

/* Prueba automatica: escribe un texto de ejemplo y lo deja un segundo en pantalla (para las capturas) */
static int kb_autoplay(void)
{
	if (!kb_len) {
		const char *s = TX(T_KB_SAMPLE);

		for (; *s; s++) {
			char c[2] = { *s, 0 };

			kb_type(c);
		}
		kb_row = KB_ROWS - 1;
		kb_col = KB_COLS - 1;
		kb_wait = 0;
	}
	return ++kb_wait >= 60;
}

const Special special_keyboard = { 0, kb_begin, kb_update, kb_draw, kb_autoplay };
