#include "app.h"
#include "img.h"
#include "input.h"
#include "res.h"
#include "special.h"
#include "text.h"
#include "ui_text.h"
#include "video.h"

/* Tiras de 320x180 que se recorren con arriba/abajo. Snoot: `call screen textscroll` del capitulo 4, el chat del
 * telefono, que se lee de abajo hacia arriba como en el original. */
static int strip_first, strip_count, strip_pos;

/* Fallback debil para consolas que no implementan estas consultas (ej. PS1): no rompe el enlace. */
__attribute__((weak)) int input_stick_x(void)
{
	return 0;
}
__attribute__((weak)) int input_stick_y(void)
{
	return 0;
}
__attribute__((weak)) int input_touch_down(int *x, int *y)
{
	(void)x;
	(void)y;
	return 0;
}

void strips_setup(int first, int count)
{
	strip_first = first;
	strip_count = count;
}

static int strips_begin(void)
{
	if (!strip_count)
		return 0;
	strip_pos = strip_count * VIEW_H - VIEW_H;
	return 1;
}

static int strips_update(void)
{
	int max = strip_count * VIEW_H - VIEW_H;
	int sy = input_stick_y();
	int up = input_down(BTN_UP) || sy < 0;
	int down = input_down(BTN_DOWN) || sy > 0;
	int step = input_down(BTN_R1) ? 8 : 3;
	static int hold = 0;

	if ((up && !down) || (down && !up))
		hold++;
	else
		hold = 0;
	if (hold > 12)
		step = 12;

	if (up && !down) {
		strip_pos = strip_pos - step < 0 ? 0 : strip_pos - step;
	} else if (down && !up) {
		strip_pos = strip_pos + step > max ? max : strip_pos + step;
	}

	/* Saltos de pagina con L/R (solo si no se esta desplazando arriba/abajo) */
	if (!up && !down) {
		if (input_pressed(BTN_L1))
			strip_pos = strip_pos - VIEW_H < 0 ? 0 : strip_pos - VIEW_H;
		if (input_pressed(BTN_R1))
			strip_pos = strip_pos + VIEW_H > max ? max : strip_pos + VIEW_H;
	}

	/* Tactil: arrastrar para desplazar (si el backend lo soporta) */
	{
		int tx = 0, ty = 0;
		static int last_y = -1;
		if (input_touch_down(&tx, &ty)) {
			if (last_y >= 0) {
				int dy = last_y - ty;
				if (dy > 2) {
					int d = dy > 12 ? 12 : dy;
					strip_pos = strip_pos - d < 0 ? 0 : strip_pos - d;
				} else if (dy < -2) {
					int d = -dy > 12 ? 12 : -dy;
					strip_pos = strip_pos + d > max ? max : strip_pos + d;
				}
			}
			last_y = ty;
		} else {
			last_y = -1;
		}
	}

	/* como en el original, el boton para salir esta arriba de todo: X sale al llegar al inicio del chat */
	return strip_pos == 0 && input_pressed(BTN_CROSS);
}

static void strips_draw(void)
{
	int k = strip_pos / VIEW_H, off = strip_pos % VIEW_H, i;

	res_new_scene();
	for (i = 0; i < 2 && k + i < strip_count; i++) {
		const Image *img = res_get(strip_first + k + i);

		if (img && img->kind <= 1)
			img_draw(img, LAYER_SPRITE0, 0, VIEW_Y + i * VIEW_H - off);
	}
	video_clip_scene();
	if (strip_count > 1) {
		/* barra de posicion a la derecha */
		int total = strip_count * VIEW_H, max = total - VIEW_H, th = VIEW_H * VIEW_H / total;

		if (th < 10)
			th = 10;
		video_rect(LAYER_TEXT, SCREEN_W - 7, VIEW_Y + (VIEW_H - th) * strip_pos / max, 5, th, 170, 170, 170, 0);
		video_rect(LAYER_TEXT, SCREEN_W - 7, VIEW_Y, 5, VIEW_H, 40, 40, 40, 0);
	}
	draw_center(8, TX(T_SCROLL_TITLE), 255, 220, 40);
	if (strip_pos == 0) {
		/* se llego al final del chat (arriba, donde el original tenia el boton): aviso para continuar */
		if ((video_frames() / 20) & 1)
			video_triangle_down(LAYER_TEXT, (SCREEN_W - font_width(TX(T_PRESS_CROSS))) / 2 - 16,
			                    SCREEN_H - 20, 10, 7, 255, 220, 40);
		draw_center(SCREEN_H - 24, TX(T_PRESS_CROSS), 255, 220, 40);
	} else {
		draw_center(SCREEN_H - 24, TX(T_SCROLL_HELP), 128, 128, 128);
	}
}

const Special special_strips = {SP_IN_GAME | SP_OWN_R1 | SP_OWN_SCENE, strips_begin, strips_update, strips_draw, 0};
