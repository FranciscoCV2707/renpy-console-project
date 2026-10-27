#include "img.h"
#include "video.h"
#include "lz4.h"
#include "ds_internal.h"
#include <nds.h>
#include <stdlib.h>
#include <string.h>

int img_brightness = 256;

#define DS_MAX_TEXTURES 64

typedef struct {
	uint8_t *indices;
	uint16_t palette[256];
	uint16_t w, h;
	int in_use;
} DsTexture;

static DsTexture textures[DS_MAX_TEXTURES];

void ds_free_texture(int slot)
{
	if (slot >= 0 && slot < DS_MAX_TEXTURES && textures[slot].in_use) {
		if (textures[slot].indices) {
			free(textures[slot].indices);
			textures[slot].indices = NULL;
		}
		textures[slot].in_use = 0;
	}
}

static uint16_t rd16(const uint8_t *p)
{
	return (uint16_t)(p[0] | ((unsigned)p[1] << 8));
}

static uint32_t rd32(const uint8_t *p)
{
	return p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

int img_load(Image *img, const uint8_t *file, int file_size, int vram_x, int vram_y, int clut_y)
{
	(void)vram_x;
	(void)vram_y;
	(void)clut_y;

	img->loaded = 0;
	img->big = 0;
	img->vram_x = 0;

	if (file_size < 544 || memcmp(file, "IMG1", 4) != 0)
		return -1;

	img->kind = file[4];
	img->flags = file[5];
	img->full_w = rd16(file + 6);
	img->full_h = rd16(file + 8);
	img->x = rd16(file + 10);
	img->y = rd16(file + 12);
	img->w = rd16(file + 14);
	img->h = rd16(file + 16);
	memcpy(img->solid, file + 18, 4);

	if (img->kind > 1 || !img->w) {
		img->loaded = 1;
		return 0;
	}

	uint32_t raw = rd32(file + 536);
	uint32_t comp = rd32(file + 540);
	if (raw != (uint32_t)img->w * img->h || comp > (uint32_t)(file_size - 544))
		return -1;

	int slot = -1;
	for (int i = 0; i < DS_MAX_TEXTURES; i++) {
		if (!textures[i].in_use) {
			slot = i;
			break;
		}
	}
	if (slot < 0)
		return -1;

	uint8_t *indices = malloc(raw);
	if (!indices)
		return -1;

	if (lz4_decode(file + 544, (int)comp, indices, (int)raw) != (int)raw) {
		free(indices);
		return -1;
	}

	textures[slot].indices = indices;
	textures[slot].w = img->w;
	textures[slot].h = img->h;
	textures[slot].in_use = 1;

	for (int i = 0; i < 256; i++) {
		uint16_t c = rd16(file + 24 + i * 2);
		textures[slot].palette[i] = (uint16_t)((c & 0x7fff) | 0x8000);
	}
	if (img->flags & 1)
		textures[slot].palette[0] = 0;

	img->vram_x = (uint16_t)slot;
	img->loaded = 1;
	return 0;
}

int img_load_big(Image *img, const uint8_t *file, int file_size, int vram_x, int vram_y, int clut_y)
{
	int ok = img_load(img, file, file_size, vram_x, vram_y, clut_y);
	if (ok == 0)
		img->big = 1;
	return ok;
}

static void draw_ex(const Image *img, int layer, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b,
                    int angle)
{
	(void)r;
	(void)g;
	(void)b;
	(void)angle;

	if (!img->loaded)
		return;

	if (img->kind == 2) {
		video_rect(layer, screen_x, screen_y, img->full_w * zoom / 64, img->full_h * zoom / 64, img->solid[0],
		           img->solid[1], img->solid[2], 0);
		return;
	}
	if (img->kind == 3)
		return;

	int slot = img->vram_x;
	if (slot >= DS_MAX_TEXTURES || !textures[slot].in_use)
		return;

	DsTexture *tex = &textures[slot];
	int dst_x, dst_y, dst_w, dst_h;

	if (layer == LAYER_TEXT && screen_y < 120) {
		ds_in_title = 1;
		dst_w = (img->w * zoom / 64) * 4 / 5;
		dst_h = (img->h * zoom / 64) * 4 / 5;
		dst_x = (DS_SCREEN_W - dst_w) / 2;
		dst_y = (DS_SCREEN_H - dst_h) / 2;
	} else {
		int fw = img->full_w;
		int eff_x = screen_x + (flip ? (fw - img->x - img->w) * zoom / 64 : img->x * zoom / 64);
		int eff_y = screen_y + img->y * zoom / 64;
		dst_x = eff_x * 4 / 5;
		dst_y = ds_in_title ? ((eff_y - 35) * 4 / 5) : (eff_y * 4 / 5);
		dst_w = (img->w * zoom / 64) * 4 / 5;
		dst_h = (img->h * zoom / 64) * 4 / 5;
	}

	if (dst_w <= 0 || dst_h <= 0)
		return;

	for (int dy = 0; dy < dst_h; dy++) {
		int py = dst_y + dy;
		if (py < 0 || py >= DS_SCREEN_H)
			continue;
		int sy = dy * img->h / dst_h;
		if (sy >= img->h)
			sy = img->h - 1;

		const uint8_t *src_row = tex->indices + sy * img->w;
		uint16_t *dst_base =
		    ((layer == LAYER_TEXT && screen_y >= 120) || layer == LAYER_BOX) ? bottom_fb : top_fb;
		uint16_t *dst_row = dst_base + py * DS_SCREEN_W;

		for (int dx = 0; dx < dst_w; dx++) {
			int px = dst_x + dx;
			if (px < 0 || px >= DS_SCREEN_W)
				continue;
			int sx = flip ? (img->w - 1 - (dx * img->w / dst_w)) : (dx * img->w / dst_w);
			if (sx < 0)
				sx = 0;
			if (sx >= img->w)
				sx = img->w - 1;

			uint8_t idx = src_row[sx];
			if (idx == 0 && (img->flags & 1))
				continue;
			uint16_t c = tex->palette[idx];
			if (!(c & 0x8000))
				continue;

			if (img_brightness < 256) {
				int cr = ((c & 31) * img_brightness) >> 8;
				int cg = (((c >> 5) & 31) * img_brightness) >> 8;
				int cb = (((c >> 10) & 31) * img_brightness) >> 8;
				c = (uint16_t)ARGB16(1, cr, cg, cb);
			}

			if (img->flags & IMG_TRANSLUCENT) {
				dst_row[px] = ds_blend50(dst_row[px], c);
			} else {
				dst_row[px] = c;
			}
		}
	}
}

void img_draw_ex(const Image *img, int layer, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b)
{
	draw_ex(img, layer, screen_x, screen_y, flip, zoom, r, g, b, 0);
}

void img_draw(const Image *img, int layer, int screen_x, int screen_y)
{
	draw_ex(img, layer, screen_x, screen_y, 0, 64, 128, 128, 128, 0);
}

void img_draw_flip(const Image *img, int layer, int screen_x, int screen_y, int flip)
{
	draw_ex(img, layer, screen_x, screen_y, flip, 64, 128, 128, 128, 0);
}

void img_draw_ex_rot(const Image *img, int layer, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b,
                     int angle)
{
	draw_ex(img, layer, screen_x, screen_y, flip, zoom, r, g, b, angle);
}

void img_draw_big(const Image *img, int layer, int screen_x, int screen_y)
{
	img_draw(img, layer, screen_x, screen_y);
}
