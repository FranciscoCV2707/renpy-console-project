#include "video.h"
#include "ds_internal.h"
#include <nds.h>
#include <string.h>

uint16_t top_fb[DS_SCREEN_W * DS_SCREEN_H];
uint16_t bottom_fb[DS_SCREEN_W * DS_SCREEN_H];
static uint16_t snapshot_fb[DS_SCREEN_W * DS_SCREEN_H];
uint8_t ds_font_atlas[256 * 256 / 2];

static int top_bg_id;
static int bottom_bg_id;
static int frame_count = 0;
static int vblank_count = 0;
int ds_in_dialog = 0;
int ds_in_title = 0;

uint16_t ds_blend50(uint16_t c1, uint16_t c2)
{
	return (uint16_t)((((c1 & 0x7bde) >> 1) + ((c2 & 0x7bde) >> 1)) | 0x8000);
}

void ds_draw_glyph(int layer, int x, int y, int u, int v, int w, int h, int r, int g, int b)
{
	uint16_t *target;
	int dx, dy;

	if (layer == LAYER_DEBUG) {
		target = top_fb;
		dx = x * 4 / 5;
		dy = y * 4 / 5;
	} else {
		target = bottom_fb;
		if (ds_in_dialog) {
			dx = 14 + (x - 8) * 4 / 5;
			dy = (y - 168) + 26;
		} else if (ds_in_title) {
			dx = x * 4 / 5;
			dy = (y - 35) * 4 / 5;
		} else {
			dx = x * 4 / 5;
			dy = y * 4 / 5;
		}
	}

	int fr = (r * 2 > 255) ? 255 : (r * 2);
	int fg = (g * 2 > 255) ? 255 : (g * 2);
	int fb = (b * 2 > 255) ? 255 : (b * 2);

	for (int gy = 0; gy < h; gy++) {
		int py = dy + gy;
		if (py < 0 || py >= DS_SCREEN_H)
			continue;
		int atlas_y = v + gy;
		if (atlas_y < 0 || atlas_y >= 256)
			continue;

		for (int gx = 0; gx < w; gx++) {
			int px = dx + gx;
			if (px < 0 || px >= DS_SCREEN_W)
				continue;
			int atlas_x = u + gx;
			if (atlas_x < 0 || atlas_x >= 256)
				continue;

			int byte_idx = (atlas_y * 256 + atlas_x) / 2;
			uint8_t byte = ds_font_atlas[byte_idx];
			uint8_t a = (atlas_x & 1) ? (byte >> 4) : (byte & 0x0F);
			if (a == 0)
				continue;

			if (a >= 15) {
				target[py * DS_SCREEN_W + px] = (uint16_t)ARGB16(1, fr >> 3, fg >> 3, fb >> 3);
			} else {
				uint16_t bg = target[py * DS_SCREEN_W + px];
				int bg_r = (bg & 31) << 3;
				int bg_g = ((bg >> 5) & 31) << 3;
				int bg_b = ((bg >> 10) & 31) << 3;
				int out_r = (fr * a + bg_r * (15 - a)) / (15 * 8);
				int out_g = (fg * a + bg_g * (15 - a)) / (15 * 8);
				int out_b = (fb * a + bg_b * (15 - a)) / (15 * 8);
				if (out_r > 31)
					out_r = 31;
				if (out_g > 31)
					out_g = 31;
				if (out_b > 31)
					out_b = 31;
				target[py * DS_SCREEN_W + px] = (uint16_t)ARGB16(1, out_r, out_g, out_b);
			}
		}
	}
}

void video_init(void)
{
	videoSetMode(MODE_5_2D);
	vramSetBankA(VRAM_A_MAIN_BG);
	top_bg_id = bgInit(3, BgType_Bmp16, BgSize_B16_256x256, 0, 0);

	videoSetModeSub(MODE_5_2D);
	vramSetBankC(VRAM_C_SUB_BG);
	bottom_bg_id = bgInitSub(3, BgType_Bmp16, BgSize_B16_256x256, 0, 0);

	for (int i = 0; i < DS_SCREEN_W * DS_SCREEN_H; i++) {
		top_fb[i] = (uint16_t)ARGB16(1, 0, 0, 0);
		bottom_fb[i] = (uint16_t)ARGB16(1, 4, 6, 12);
	}
	dmaCopy(top_fb, bgGetGfxPtr(top_bg_id), sizeof(top_fb));
	dmaCopy(bottom_fb, bgGetGfxPtr(bottom_bg_id), sizeof(bottom_fb));
}

void video_rect(int layer, int x, int y, int w, int h, int r, int g, int b, int blend)
{
	uint16_t *target;
	int rx, ry, rw, rh;

	if (layer >= LAYER_FX) {
		target = top_fb;
		rx = x * 4 / 5;
		ry = y * 4 / 5;
		rw = w * 4 / 5;
		rh = h * 4 / 5;
	} else {
		target = bottom_fb;
		if (layer == LAYER_BOX && y == 168) {
			ds_in_dialog = 1;
			rx = 6;
			rw = DS_SCREEN_W - 12;
			ry = 18;
			rh = 156;
		} else {
			rx = x * 4 / 5;
			ry = y * 4 / 5;
			rw = w * 4 / 5;
			rh = h * 4 / 5;
		}
	}

	if (rw <= 0 || rh <= 0)
		return;

	int x0 = rx < 0 ? 0 : rx;
	int y0 = ry < 0 ? 0 : ry;
	int x1 = rx + rw > DS_SCREEN_W ? DS_SCREEN_W : rx + rw;
	int y1 = ry + rh > DS_SCREEN_H ? DS_SCREEN_H : ry + rh;

	uint16_t col = (uint16_t)ARGB16(1, r >> 3, g >> 3, b >> 3);

	for (int py = y0; py < y1; py++) {
		uint16_t *row = target + py * DS_SCREEN_W;
		for (int px = x0; px < x1; px++) {
			if (blend == 1) {
				row[px] = ds_blend50(row[px], col);
			} else if (blend == 2) {
				int cr = (row[px] & 31) + (r >> 3);
				int cg = ((row[px] >> 5) & 31) + (g >> 3);
				int cb = ((row[px] >> 10) & 31) + (b >> 3);
				if (cr > 31)
					cr = 31;
				if (cg > 31)
					cg = 31;
				if (cb > 31)
					cb = 31;
				row[px] = (uint16_t)ARGB16(1, cr, cg, cb);
			} else if (blend == 3) {
				int cr = (row[px] & 31) - (r >> 3);
				int cg = ((row[px] >> 5) & 31) - (g >> 3);
				int cb = ((row[px] >> 10) & 31) - (b >> 3);
				if (cr < 0)
					cr = 0;
				if (cg < 0)
					cg = 0;
				if (cb < 0)
					cb = 0;
				row[px] = (uint16_t)ARGB16(1, cr, cg, cb);
			} else {
				row[px] = col;
			}
		}
	}
}

void video_triangle_down(int layer, int x, int y, int w, int h, int r, int g, int b)
{
	(void)layer;
	int dx, dy;
	if (ds_in_dialog) {
		dx = 232;
		dy = 154;
	} else if (ds_in_title) {
		dx = x * 4 / 5;
		dy = (y - 35) * 4 / 5;
	} else {
		dx = x * 4 / 5;
		dy = y * 4 / 5;
	}

	int tr = (r * 2 > 255) ? 255 : (r * 2);
	int tg = (g * 2 > 255) ? 255 : (g * 2);
	int tb = (b * 2 > 255) ? 255 : (b * 2);
	uint16_t col = (uint16_t)ARGB16(1, tr >> 3, tg >> 3, tb >> 3);

	for (int row = 0; row < h; row++) {
		int py = dy + row;
		if (py < 0 || py >= DS_SCREEN_H)
			continue;
		int span = (w * (h - row)) / h;
		if (span <= 0)
			span = 1;
		int sx = dx + (w - span) / 2;
		for (int px = sx; px < sx + span; px++) {
			if (px >= 0 && px < DS_SCREEN_W)
				bottom_fb[py * DS_SCREEN_W + px] = col;
		}
	}
}

void video_flip(void)
{
	swiWaitForVBlank();
	dmaCopy(top_fb, bgGetGfxPtr(top_bg_id), sizeof(top_fb));
	dmaCopy(bottom_fb, bgGetGfxPtr(bottom_bg_id), sizeof(bottom_fb));

	for (int i = 0; i < DS_SCREEN_W * DS_SCREEN_H; i++) {
		top_fb[i] = (uint16_t)ARGB16(1, 0, 0, 0);
		bottom_fb[i] = (uint16_t)ARGB16(1, 4, 6, 12);
	}

	ds_in_dialog = 0;
	ds_in_title = 0;
	vblank_count++;
	frame_count++;
}

void video_snapshot(int x, int y)
{
	(void)x;
	(void)y;
	memcpy(snapshot_fb, top_fb, sizeof(snapshot_fb));
}

void video_snapshot_draw(int layer, int x, int y, int blend, int bright, int band_y, int band_bright)
{
	(void)layer;
	(void)x;
	(void)y;
	(void)blend;
	(void)band_y;
	(void)band_bright;

	for (int i = 0; i < DS_SCREEN_W * DS_SCREEN_H; i++) {
		uint16_t c = snapshot_fb[i];
		int cr = ((c & 31) * bright) >> 7;
		int cg = (((c >> 5) & 31) * bright) >> 7;
		int cb = (((c >> 10) & 31) * bright) >> 7;
		if (cr > 31)
			cr = 31;
		if (cg > 31)
			cg = 31;
		if (cb > 31)
			cb = 31;
		top_fb[i] = (uint16_t)ARGB16(1, cr, cg, cb);
	}
}

int video_frames(void)
{
	return frame_count;
}

void video_clip_scene(void)
{
}

void video_unclip(void)
{
}

void video_wait_vblank(void)
{
	swiWaitForVBlank();
	vblank_count++;
}

int video_vblank_count(void)
{
	return vblank_count;
}
