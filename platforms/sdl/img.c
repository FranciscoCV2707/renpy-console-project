#include "img.h"
#include "sdl_target.h"
#include "video.h"

#include <stdlib.h>
#include <string.h>
#include "lz4.h"

extern void sdl_draw_texture(SDL_Texture *, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int,
                             int);
extern SDL_Renderer *sdl_renderer(void);
static SDL_Texture *textures[4096];
int img_brightness = 256;
static unsigned rd16(const uint8_t *p)
{
	return p[0] | ((unsigned)p[1] << 8);
}
static unsigned rd32(const uint8_t *p)
{
	return p[0] | ((unsigned)p[1] << 8) | ((unsigned)p[2] << 16) | ((unsigned)p[3] << 24);
}
int img_load(Image *img, const uint8_t *f, int n, int vx, int vy, int cy)
{
	uint32_t raw, comp;
	uint8_t *indices;
	uint32_t *pixels;
	SDL_Surface *surface;
	SDL_Renderer *r = sdl_renderer();
	int i;
	(void)vx;
	(void)vy;
	(void)cy;
	img->loaded = 0;
	img->big = 0;
	if (n < 544 || memcmp(f, "IMG1", 4))
		return -1;
	img->kind = f[4];
	img->flags = f[5];
	img->full_w = rd16(f + 6);
	img->full_h = rd16(f + 8);
	img->x = rd16(f + 10);
	img->y = rd16(f + 12);
	img->w = rd16(f + 14);
	img->h = rd16(f + 16);
	memcpy(img->solid, f + 18, 4);
	if (img->kind > 1 || !img->w) {
		img->loaded = 1;
		return 0;
	}
	raw = rd32(f + 536);
	comp = rd32(f + 540);
	if (raw != (uint32_t)img->w * img->h || comp > (uint32_t)(n - 544))
		return -1;
	indices = malloc(raw);
	pixels = malloc((size_t)img->w * img->h * 4);
	if (!indices || !pixels) {
		free(indices);
		free(pixels);
		return -1;
	}
	if (lz4_decode(f + 544, (int)comp, indices, (int)raw) != (int)raw) {
		free(indices);
		free(pixels);
		return -1;
	}
	for (i = 0; i < (int)raw; i++) {
		unsigned ix = indices[i];
		unsigned c = rd16(f + 24 + ix * 2);
		unsigned r = (c & 31) * 255 / 31, g = ((c >> 5) & 31) * 255 / 31, b = ((c >> 10) & 31) * 255 / 31;
		unsigned a = (ix == 0 && (img->flags & 1)) ? 0 : 255;
		if ((img->flags & IMG_TRANSLUCENT) && (c & 0x8000))
			a = 128;
		pixels[i] = (a << 24) | (b << 16) | (g << 8) | r;
	}
	surface = SDL_CreateRGBSurfaceWithFormatFrom(pixels, img->w, img->h, 32, img->w * 4, SDL_PIXELFORMAT_RGBA32);
	if (surface) {
		int slot;
		for (slot = 1; slot < 4096 && textures[slot]; slot++)
			;
		if (slot < 4096) {
			textures[slot] = SDL_CreateTextureFromSurface(r, surface);
			img->vram_x = (uint16_t)slot;
		}
		SDL_FreeSurface(surface);
	}
	free(indices);
	free(pixels);
	img->loaded = img->vram_x > 0;
	return img->loaded ? 0 : -1;
}
static SDL_Texture *tex(const Image *i)
{
	return i->vram_x < 4096 ? textures[i->vram_x] : NULL;
}
static void draw_ex(const Image *i, int l, int x, int y, int flip, int zoom, int r, int g, int b, int angle)
{
	int fw = i->full_w, scale = (i->flags & IMG_HALF) ? 2 : 1;
	if (!i->loaded)
		return;
	if (i->kind == 2) {
		video_rect(l, x, y, i->full_w * zoom / 64, i->full_h * zoom / 64, i->solid[0], i->solid[1], i->solid[2],
		           0);
		return;
	}
	if (i->kind == 3)
		return;
	if (scale == 2) {
		zoom *= 2;
		fw = (i->full_w + 1) / 2;
	}
	sdl_draw_texture(tex(i), l, x + (flip ? (fw - i->x - i->w) * zoom / 64 : i->x * zoom / 64),
	                 y + i->y * zoom / 64, i->w, i->h, 0, 0, i->w, i->h, r * img_brightness / 256,
	                 g * img_brightness / 256, b * img_brightness / 256, (i->flags & IMG_TRANSLUCENT) != 0, flip,
	                 zoom, angle);
}
void img_draw_ex(const Image *i, int l, int x, int y, int flip, int zoom, int r, int g, int b)
{
	draw_ex(i, l, x, y, flip, zoom, r, g, b, 0);
}
void img_draw(const Image *i, int l, int x, int y)
{
	img_draw_ex(i, l, x, y, 0, 64, 128, 128, 128);
}
void img_draw_flip(const Image *i, int l, int x, int y, int f)
{
	img_draw_ex(i, l, x, y, f, 64, 128, 128, 128);
}
void img_draw_ex_rot(const Image *i, int l, int x, int y, int f, int z, int r, int g, int b, int a)
{
	draw_ex(i, l, x, y, f, z, r, g, b, a);
}
int img_load_big(Image *i, const uint8_t *f, int n, int x, int y, int c)
{
	int ok = img_load(i, f, n, x, y, c);
	if (!ok)
		i->big = 1;
	return ok;
}
void img_draw_big(const Image *i, int l, int x, int y)
{
	img_draw(i, l, x, y);
}
