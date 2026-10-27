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

typedef enum { TOP_CMD_RECT, TOP_CMD_IMG, TOP_CMD_SNAPSHOT, TOP_CMD_GLYPH } TopCmdType;

typedef struct {
	TopCmdType type;
	int layer;
	union {
		struct {
			int x, y, w, h;
			int r, g, b, blend;
		} rect;
		struct {
			const Image *img;
			int screen_x, screen_y;
			int flip, zoom;
			int r, g, b;
			int angle;
			int brightness;
			int is_title;
		} img;
		struct {
			int blend;
			int bright;
			int band_y;
			int band_bright;
		} snap;
		struct {
			int x, y, u, v, w, h;
			int r, g, b;
		} glyph;
	};
} TopCmd;

#define MAX_TOP_CMDS 128
static TopCmd top_cmds[MAX_TOP_CMDS];
static int top_cmd_count = 0;

void ds_queue_top_rect(int layer, int x, int y, int w, int h, int r, int g, int b, int blend)
{
	if (top_cmd_count < MAX_TOP_CMDS) {
		TopCmd *c = &top_cmds[top_cmd_count++];
		c->type = TOP_CMD_RECT;
		c->layer = layer;
		c->rect.x = x;
		c->rect.y = y;
		c->rect.w = w;
		c->rect.h = h;
		c->rect.r = r;
		c->rect.g = g;
		c->rect.b = b;
		c->rect.blend = blend;
	}
}

void ds_queue_top_img(const Image *img, int layer, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b,
                      int angle, int brightness, int is_title)
{
	if (top_cmd_count < MAX_TOP_CMDS) {
		TopCmd *c = &top_cmds[top_cmd_count++];
		c->type = TOP_CMD_IMG;
		c->layer = layer;
		c->img.img = img;
		c->img.screen_x = screen_x;
		c->img.screen_y = screen_y;
		c->img.flip = flip;
		c->img.zoom = zoom;
		c->img.r = r;
		c->img.g = g;
		c->img.b = b;
		c->img.angle = angle;
		c->img.brightness = brightness;
		c->img.is_title = is_title;
	}
}

void ds_queue_top_snapshot(int layer, int blend, int bright, int band_y, int band_bright)
{
	if (top_cmd_count < MAX_TOP_CMDS) {
		TopCmd *c = &top_cmds[top_cmd_count++];
		c->type = TOP_CMD_SNAPSHOT;
		c->layer = layer;
		c->snap.blend = blend;
		c->snap.bright = bright;
		c->snap.band_y = band_y;
		c->snap.band_bright = band_bright;
	}
}

uint16_t ds_blend50(uint16_t c1, uint16_t c2)
{
	return (uint16_t)((((c1 & 0x7bde) >> 1) + ((c2 & 0x7bde) >> 1)) | 0x8000);
}

void ds_draw_glyph(int layer, int x, int y, int u, int v, int w, int h, int r, int g, int b)
{
	if (layer == LAYER_DEBUG) {
		if (top_cmd_count < MAX_TOP_CMDS) {
			TopCmd *cmd = &top_cmds[top_cmd_count++];
			cmd->type = TOP_CMD_GLYPH;
			cmd->layer = layer;
			cmd->glyph.x = x * 4 / 5;
			cmd->glyph.y = y * 4 / 5;
			cmd->glyph.u = u;
			cmd->glyph.v = v;
			cmd->glyph.w = w;
			cmd->glyph.h = h;
			cmd->glyph.r = r;
			cmd->glyph.g = g;
			cmd->glyph.b = b;
		}
		return;
	}

	uint16_t *target = bottom_fb;
	int dx, dy;
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

static void draw_top_rect(int x, int y, int w, int h, int r, int g, int b, int blend)
{
	int rx = x * 4 / 5;
	int ry = y * 4 / 5;
	int rw = w * 4 / 5;
	int rh = h * 4 / 5;

	if (rw <= 0 || rh <= 0)
		return;

	int x0 = rx < 0 ? 0 : rx;
	int y0 = ry < 0 ? 0 : ry;
	int x1 = rx + rw > DS_SCREEN_W ? DS_SCREEN_W : rx + rw;
	int y1 = ry + rh > DS_SCREEN_H ? DS_SCREEN_H : ry + rh;

	uint16_t col = (uint16_t)ARGB16(1, r >> 3, g >> 3, b >> 3);

	for (int py = y0; py < y1; py++) {
		uint16_t *row = top_fb + py * DS_SCREEN_W;
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

static void draw_top_snapshot(int blend, int bright)
{
	for (int i = 0; i < DS_SCREEN_W * DS_SCREEN_H; i++) {
		uint16_t c = snapshot_fb[i];
		int cr = ((c & 31) * bright) >> 7;
		int cg = (((c >> 5) & 31) * bright) >> 7;
		int cb = (((c >> 10) & 31) * bright) >> 7;
		if (blend == 2) {
			cr += (top_fb[i] & 31);
			cg += ((top_fb[i] >> 5) & 31);
			cb += ((top_fb[i] >> 10) & 31);
		}
		if (cr > 31)
			cr = 31;
		if (cg > 31)
			cg = 31;
		if (cb > 31)
			cb = 31;
		top_fb[i] = (uint16_t)ARGB16(1, cr, cg, cb);
	}
}

static void exec_top_cmd(const TopCmd *cmd)
{
	if (cmd->type == TOP_CMD_RECT) {
		draw_top_rect(cmd->rect.x, cmd->rect.y, cmd->rect.w, cmd->rect.h, cmd->rect.r, cmd->rect.g, cmd->rect.b,
		              cmd->rect.blend);
	} else if (cmd->type == TOP_CMD_IMG) {
		ds_render_img_top(cmd->img.img, cmd->img.screen_x, cmd->img.screen_y, cmd->img.flip, cmd->img.zoom,
		                  cmd->img.r, cmd->img.g, cmd->img.b, cmd->img.angle, cmd->img.brightness,
		                  cmd->img.is_title);
	} else if (cmd->type == TOP_CMD_SNAPSHOT) {
		draw_top_snapshot(cmd->snap.blend, cmd->snap.bright);
	} else if (cmd->type == TOP_CMD_GLYPH) {
		int fr = (cmd->glyph.r * 2 > 255) ? 255 : (cmd->glyph.r * 2);
		int fg = (cmd->glyph.g * 2 > 255) ? 255 : (cmd->glyph.g * 2);
		int fb = (cmd->glyph.b * 2 > 255) ? 255 : (cmd->glyph.b * 2);
		for (int gy = 0; gy < cmd->glyph.h; gy++) {
			int py = cmd->glyph.y + gy;
			if (py < 0 || py >= DS_SCREEN_H)
				continue;
			int atlas_y = cmd->glyph.v + gy;
			if (atlas_y < 0 || atlas_y >= 256)
				continue;
			for (int gx = 0; gx < cmd->glyph.w; gx++) {
				int px = cmd->glyph.x + gx;
				if (px < 0 || px >= DS_SCREEN_W)
					continue;
				int atlas_x = cmd->glyph.u + gx;
				if (atlas_x < 0 || atlas_x >= 256)
					continue;
				int byte_idx = (atlas_y * 256 + atlas_x) / 2;
				uint8_t byte = ds_font_atlas[byte_idx];
				uint8_t a = (atlas_x & 1) ? (byte >> 4) : (byte & 0x0F);
				if (a == 0)
					continue;
				if (a >= 15) {
					top_fb[py * DS_SCREEN_W + px] = (uint16_t)ARGB16(1, fr >> 3, fg >> 3, fb >> 3);
				} else {
					uint16_t bg = top_fb[py * DS_SCREEN_W + px];
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
					top_fb[py * DS_SCREEN_W + px] = (uint16_t)ARGB16(1, out_r, out_g, out_b);
				}
			}
		}
	}
}

void video_rect(int layer, int x, int y, int w, int h, int r, int g, int b, int blend)
{
	if (layer >= LAYER_FX) {
		ds_queue_top_rect(layer, x, y, w, h, r, g, b, blend);
		return;
	}

	uint16_t *target = bottom_fb;
	int rx, ry, rw, rh;

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
	for (int i = 0; i < DS_SCREEN_W * DS_SCREEN_H; i++) {
		top_fb[i] = (uint16_t)ARGB16(1, 0, 0, 0);
	}

	for (int l = LAYER_BG; l >= LAYER_DEBUG; l--) {
		for (int i = 0; i < top_cmd_count; i++) {
			if (top_cmds[i].layer == l) {
				exec_top_cmd(&top_cmds[i]);
			}
		}
	}
	top_cmd_count = 0;

	swiWaitForVBlank();
	dmaCopy(top_fb, bgGetGfxPtr(top_bg_id), sizeof(top_fb));
	dmaCopy(bottom_fb, bgGetGfxPtr(bottom_bg_id), sizeof(bottom_fb));

	for (int i = 0; i < DS_SCREEN_W * DS_SCREEN_H; i++) {
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
	(void)x;
	(void)y;
	ds_queue_top_snapshot(layer, blend, bright, band_y, band_bright);
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
