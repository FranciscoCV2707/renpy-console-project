#include "vn_platform.h"
#include "cd.h"
#include "video.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef __PSP__
#include <pspkernel.h>
#endif

extern SDL_Renderer *sdl_renderer(void);
extern SDL_Texture *sdl_font_texture(void);
extern void sdl_set_font(SDL_Texture *);
extern void sdl_draw_texture(SDL_Texture *, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int,
                             int);
static uint32_t started;
#ifdef __PSP__
/* Sin SDL2main (el main es el del motor): la info de modulo y la pila de user_main van aqui (crt0 de pspsdk). */
PSP_MODULE_INFO("snoot", 0, 1, 0);
int sce_newlib_stack_kb_size = 1024;
#endif
static FILE *open_file(const char *n)
{
	const char *root = getenv("VN_DATA_DIR");
#ifdef _EE
	const char *base = root && *root ? root : "host:disc";
#elif defined(__PSP__)
	const char *base = root && *root ? root : "ms0:/PSP/GAME/SNOOT/DATA";
#else
	const char *base = root && *root ? root : ".";
#endif
	char p[600];
	snprintf(p, sizeof(p), "%s/%s", base, n);
	return fopen(p, "rb");
}
static int file_size(const char *n)
{
	FILE *f = open_file(n);
	long z;
	if (!f)
		return -1;
	fseek(f, 0, SEEK_END);
	z = ftell(f);
	fclose(f);
	return (int)z;
}
static int file_read(const char *n, void *b, int cap)
{
	FILE *f = open_file(n);
	long z;
	if (!f)
		return -1;
	fseek(f, 0, SEEK_END);
	z = ftell(f);
	rewind(f);
	if (z > cap || fread(b, 1, (size_t)z, f) != (size_t)z) {
		fclose(f);
		return -1;
	}
	fclose(f);
	return (int)z;
}
static void font_upload(const uint8_t *src)
{
	uint32_t *pixels = malloc(256 * 256 * 4);
	SDL_Surface *s;
	SDL_Texture *t;
	int x, y;
	if (!pixels)
		return;
	for (y = 0; y < 256; y++)
		for (x = 0; x < 256; x++) {
			int i = y * 256 + x, byte = src[i / 2], a = (i & 1) ? byte >> 4 : byte & 15;
			pixels[i] = ((uint32_t)(a * 17) << 24) | 0x00ffffffu;
		}
	s = SDL_CreateRGBSurfaceWithFormatFrom(pixels, 256, 256, 32, 1024, SDL_PIXELFORMAT_RGBA32);
	t = s ? SDL_CreateTextureFromSurface(sdl_renderer(), s) : NULL;
	if (s)
		SDL_FreeSurface(s);
	free(pixels);
	sdl_set_font(t);
}
static void draw_glyph(int l, int x, int y, int u, int v, int w, int h, int r, int g, int b)
{
	SDL_Texture *t = sdl_font_texture();
	if (t)
		sdl_draw_texture(t, l, x, y, w, h, u, v, w, h, r * 2, g * 2, b * 2, 1, 0, 64, 0);
	else
		video_rect(l, x, y, w, h, r, g, b, 0);
}
static void glyphs_end(int l)
{
	(void)l;
}
static void log_line(const char *s)
{
	puts(s);
#ifdef __PSP__
	fflush(stdout);
#endif
}
static unsigned int time_ms(void)
{
	return SDL_GetTicks() - started;
}
static void sleep_ms(unsigned int n)
{
	if (getenv("VN_FAST"))
		return;
	SDL_Delay(n);
}
static const VnPlatformOps ops = {.file_size = file_size,
                                  .file_read = file_read,
                                  .font_upload = font_upload,
                                  .draw_glyph = draw_glyph,
                                  .glyphs_end = glyphs_end,
                                  .log = log_line,
                                  .get_time_ms = time_ms,
                                  .sleep_ms = sleep_ms};
const VnPlatformOps *vn_platform_default_ops(void)
{
	started = SDL_GetTicks();
	return &ops;
}
void fmv_select(int file)
{
	(void)file;
}
