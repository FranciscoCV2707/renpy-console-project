#include "video.h"
#include "gba_internal.h"
#include <tonc.h>
#include <string.h>

uint16_t gba_backbuffer[GBA_SCREEN_W * GBA_SCREEN_H] __attribute__((section(".sbss")));

static int frame_count = 0;
static int vblank_count = 0;

typedef enum { CMD_RECT, CMD_IMG, CMD_SNAPSHOT, CMD_GLYPH } CmdType;

typedef struct {
	CmdType type;
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
	} u;
} GbaCmd;

#define MAX_CMDS 256
static GbaCmd cmds[MAX_CMDS] __attribute__((section(".sbss")));
static int cmd_count = 0;

uint16_t gba_blend50(uint16_t c1, uint16_t c2)
{
	return (uint16_t)(((c1 & 0x7BDE) >> 1) + ((c2 & 0x7BDE) >> 1));
}

void gba_queue_rect(int layer, int x, int y, int w, int h, int r, int g, int b, int blend)
{
	if (cmd_count < MAX_CMDS) {
		GbaCmd *c = &cmds[cmd_count++];
		c->type = CMD_RECT;
		c->layer = layer;
		c->u.rect.x = x;
		c->u.rect.y = y;
		c->u.rect.w = w;
		c->u.rect.h = h;
		c->u.rect.r = r;
		c->u.rect.g = g;
		c->u.rect.b = b;
		c->u.rect.blend = blend;
	}
}

void gba_queue_img(const Image *img, int layer, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b,
                   int angle, int brightness, int is_title)
{
	if (cmd_count < MAX_CMDS) {
		GbaCmd *c = &cmds[cmd_count++];
		c->type = CMD_IMG;
		c->layer = layer;
		c->u.img.img = img;
		c->u.img.screen_x = screen_x;
		c->u.img.screen_y = screen_y;
		c->u.img.flip = flip;
		c->u.img.zoom = zoom;
		c->u.img.r = r;
		c->u.img.g = g;
		c->u.img.b = b;
		c->u.img.angle = angle;
		c->u.img.brightness = brightness;
		c->u.img.is_title = is_title;
	}
}

void gba_queue_snapshot(int layer, int blend, int bright, int band_y, int band_bright)
{
	if (cmd_count < MAX_CMDS) {
		GbaCmd *c = &cmds[cmd_count++];
		c->type = CMD_SNAPSHOT;
		c->layer = layer;
		c->u.snap.blend = blend;
		c->u.snap.bright = bright;
		c->u.snap.band_y = band_y;
		c->u.snap.band_bright = band_bright;
	}
}

void gba_draw_glyph(int layer, int x, int y, int u, int v, int w, int h, int r, int g, int b)
{
	if (cmd_count < MAX_CMDS) {
		GbaCmd *c = &cmds[cmd_count++];
		c->type = CMD_GLYPH;
		c->layer = layer;
		c->u.glyph.x = x;
		c->u.glyph.y = y;
		c->u.glyph.u = u;
		c->u.glyph.v = v;
		c->u.glyph.w = w;
		c->u.glyph.h = h;
		c->u.glyph.r = r;
		c->u.glyph.g = g;
		c->u.glyph.b = b;
	}
}

void video_init(void)
{
	mgba_log("GBA: VIDEO_INIT");
	REG_DISPCNT = DCNT_MODE3 | DCNT_BG2;
	cmd_count = 0;
	frame_count = 0;
	vblank_count = 0;
	memset(gba_backbuffer, 0, sizeof(gba_backbuffer));
}

void video_rect(int layer, int x, int y, int w, int h, int r, int g, int b, int blend)
{
	gba_queue_rect(layer, x, y, w, h, r, g, b, blend);
}

void video_triangle_down(int layer, int x, int y, int w, int h, int r, int g, int b)
{
	/* Flecha hacia abajo del diálogo: un pequeño triángulo; el escalado a 240x160
	 * lo aplica render_cmd igual que al resto de los rectángulos */
	int sw = w;
	int sh = h;
	if (sw < 1)
		sw = 1;
	if (sh < 1)
		sh = 1;
	gba_queue_rect(layer, x, y, sw, sh, r, g, b, 0);
}

void video_snapshot(int x, int y)
{
	(void)x;
	(void)y;
}

void video_snapshot_draw(int layer, int x, int y, int blend, int bright, int band_y, int band_bright)
{
	(void)x;
	(void)y;
	gba_queue_snapshot(layer, blend, bright, band_y, band_bright);
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
	while (REG_VCOUNT >= 160) {
	}
	while (REG_VCOUNT < 160) {
	}
	vblank_count++;
}

int video_vblank_count(void)
{
	return vblank_count;
}

extern void gba_render_img(const Image *img, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b,
                           int angle, int brightness, int is_title);

static void render_cmd(const GbaCmd *c)
{
	if (c->type == CMD_RECT) {
		int sx = c->u.rect.x * 3 / 4;
		int sy = c->u.rect.y * 2 / 3;
		int sw = c->u.rect.w * 3 / 4;
		int sh = c->u.rect.h * 2 / 3;
		if (c->u.rect.x == 0 && c->u.rect.w >= 320) {
			sx = 0;
			sw = GBA_SCREEN_W;
		}
		if (c->u.rect.y == 0 && c->u.rect.h >= 240) {
			sy = 0;
			sh = GBA_SCREEN_H;
		}
		if (sx < 0) {
			sw += sx;
			sx = 0;
		}
		if (sy < 0) {
			sh += sy;
			sy = 0;
		}
		if (sx + sw > GBA_SCREEN_W)
			sw = GBA_SCREEN_W - sx;
		if (sy + sh > GBA_SCREEN_H)
			sh = GBA_SCREEN_H - sy;
		if (sw <= 0 || sh <= 0)
			return;

		uint16_t color = (uint16_t)(((c->u.rect.r >> 3) & 31) | (((c->u.rect.g >> 3) & 31) << 5) |
		                            (((c->u.rect.b >> 3) & 31) << 10));

		for (int py = sy; py < sy + sh; py++) {
			uint16_t *row = gba_backbuffer + py * GBA_SCREEN_W;
			if (c->u.rect.blend) {
				for (int px = sx; px < sx + sw; px++)
					row[px] = gba_blend50(row[px], color);
			} else {
				for (int px = sx; px < sx + sw; px++)
					row[px] = color;
			}
		}
	} else if (c->type == CMD_IMG) {
		gba_render_img(c->u.img.img, c->u.img.screen_x, c->u.img.screen_y, c->u.img.flip, c->u.img.zoom,
		               c->u.img.r, c->u.img.g, c->u.img.b, c->u.img.angle, c->u.img.brightness,
		               c->u.img.is_title);
	} else if (c->type == CMD_GLYPH) {
		const uint8_t *atlas = gba_get_font_atlas();
		if (!atlas)
			return;

		int dx = c->u.glyph.x * 3 / 4;
		int dy = c->u.glyph.y * 2 / 3;

		int fr = c->u.glyph.r * 2 > 255 ? 255 : c->u.glyph.r * 2;
		int fg = c->u.glyph.g * 2 > 255 ? 255 : c->u.glyph.g * 2;
		int fb = c->u.glyph.b * 2 > 255 ? 255 : c->u.glyph.b * 2;

		for (int gy = 0; gy < c->u.glyph.h; gy++) {
			int py = dy + gy;
			if (py < 0 || py >= GBA_SCREEN_H)
				continue;
			int atlas_y = c->u.glyph.v + gy;
			if (atlas_y < 0 || atlas_y >= 256)
				continue;

			uint16_t *dst_row = gba_backbuffer + py * GBA_SCREEN_W;
			for (int gx = 0; gx < c->u.glyph.w; gx++) {
				int px = dx + gx;
				if (px < 0 || px >= GBA_SCREEN_W)
					continue;
				int atlas_x = c->u.glyph.u + gx;
				if (atlas_x < 0 || atlas_x >= 256)
					continue;

				int byte_idx = (atlas_y * 256 + atlas_x) / 2;
				uint8_t byte = atlas[byte_idx];
				uint8_t a = (atlas_x & 1) ? (byte >> 4) : (byte & 0x0F);
				if (a == 0)
					continue;

				if (a >= 15) {
					dst_row[px] = (uint16_t)(((fr >> 3) & 31) | (((fg >> 3) & 31) << 5) |
					                         (((fb >> 3) & 31) << 10));
				} else {
					uint16_t bg = dst_row[px];
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
					dst_row[px] = (uint16_t)(out_r | (out_g << 5) | (out_b << 10));
				}
			}
		}
	}
}

void video_flip(void)
{
	/* Dibujar en orden de capas: de fondo (LAYER_COUNT - 1) a frente (0) */
	for (int layer = LAYER_COUNT - 1; layer >= 0; layer--) {
		for (int i = 0; i < cmd_count; i++) {
			if (cmds[i].layer == layer)
				render_cmd(&cmds[i]);
		}
	}

	/* Esperar VBlank */
	while (REG_VCOUNT < 160) {
	}

	/* Copiar a VRAM en modo 3 con DMA (dma3_cpy espera tamaño en bytes y divide por 4 internamente) */
	dma3_cpy(vid_mem, gba_backbuffer, sizeof(gba_backbuffer));

	while (REG_VCOUNT >= 160) {
	}

	vblank_count++;
	frame_count++;

	cmd_count = 0;
}
