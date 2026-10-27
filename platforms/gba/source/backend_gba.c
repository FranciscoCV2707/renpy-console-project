#include "vn_platform.h"
#include "cd.h"
#include "video.h"
#include "gba_internal.h"
#include <tonc.h>
#include <stdio.h>
#include <string.h>

#define REG_DEBUG_ENABLE (*(volatile u16 *)0x4FFF780)
#define REG_DEBUG_FLAGS  (*(volatile u16 *)0x4FFF700)
#define REG_DEBUG_STRING ((char *)0x4FFF600)

void mgba_log(const char *msg)
{
	REG_DEBUG_ENABLE = 0xC0DE;
	int i = 0;
	while (msg && msg[i] && i < 255) {
		REG_DEBUG_STRING[i] = msg[i];
		i++;
	}
	REG_DEBUG_STRING[i] = '\0';
	/* Nivel Info (3) + flag de transmisión (0x100) */
	REG_DEBUG_FLAGS = 0x103;
}

static int file_size(const char *name)
{
	int lba, size;
	if (cd_find(name, &lba, &size) == 0)
		return size;
	return -1;
}

static int file_read(const char *name, void *buf, int cap)
{
	return cd_read_file(name, buf, cap);
}

/* Guardamos el puntero al atlas en FONT.BIN (o subido por font_upload) */
static const uint8_t *font_atlas_ptr = NULL;

static void font_upload(const uint8_t *atlas_4bpp)
{
	/* Buscamos FONT.BIN directamente en ROM si es posible */
	int sz = 0;
	const uint8_t *font_bin = (const uint8_t *)cd_file_ptr("FONT.BIN", &sz);
	if (font_bin && sz > 8 + 512 * 10) {
		uint16_t glyph_count = (uint16_t)(font_bin[6] | (font_bin[7] << 8));
		int table_end = 8 + glyph_count * 10;
		int atlas_off = (table_end + 3) & ~3;
		font_atlas_ptr = font_bin + atlas_off;
	} else {
		font_atlas_ptr = atlas_4bpp;
	}
}

static void draw_glyph(int layer, int x, int y, int u, int v, int w, int h, int r, int g, int b)
{
	gba_draw_glyph(layer, x, y, u, v, w, h, r, g, b);
}

static void glyphs_end(int layer)
{
	(void)layer;
}

static void gba_log_line(const char *msg)
{
	if (msg)
		mgba_log(msg);
}

static unsigned int get_time_ms(void)
{
	return (unsigned int)(video_vblank_count() * 1000 / 60);
}

static void sleep_ms(unsigned int ms)
{
	unsigned int frames = (ms * 60 + 999) / 1000;
	while (frames--)
		video_wait_vblank();
}

static const VnPlatformOps gba_ops = {
    .file_size = file_size,
    .file_read = file_read,
    .font_upload = font_upload,
    .draw_glyph = draw_glyph,
    .glyphs_end = glyphs_end,
    .log = gba_log_line,
    .get_time_ms = get_time_ms,
    .sleep_ms = sleep_ms,
};

const VnPlatformOps *vn_platform_default_ops(void)
{
	return &gba_ops;
}

const uint8_t *gba_get_font_atlas(void)
{
	return font_atlas_ptr;
}

void fmv_select(int file)
{
	(void)file;
}
