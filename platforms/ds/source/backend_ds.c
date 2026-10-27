#include "vn_platform.h"
#include "cd.h"
#include "video.h"
#include "ds_internal.h"
#include <nds.h>
#include <fat.h>
#include <stdio.h>
#include <string.h>

static FILE *trace_file = NULL;

void ds_close_trace(void)
{
	if (trace_file) {
		fclose(trace_file);
		trace_file = NULL;
	}
}

static int file_size(const char *name)
{
	char path[64];
	int lba, size;
	snprintf(path, sizeof(path), "\\DATA\\%s", name);
	if (cd_find(path, &lba, &size) == 0)
		return size;
	return cd_find(name, &lba, &size) == 0 ? size : -1;
}

static int file_read(const char *name, void *buf, int cap)
{
	char path[64];
	snprintf(path, sizeof(path), "\\DATA\\%s", name);
	int sz = cd_read_file(path, buf, cap);
	if (sz >= 0)
		return sz;
	return cd_read_file(name, buf, cap);
}

static void font_upload(const uint8_t *atlas_4bpp)
{
	memcpy(ds_font_atlas, atlas_4bpp, sizeof(ds_font_atlas));
}

static void draw_glyph(int layer, int x, int y, int u, int v, int w, int h, int r, int g, int b)
{
	ds_draw_glyph(layer, x, y, u, v, w, h, r, g, b);
}

static void glyphs_end(int layer)
{
	(void)layer;
}

static void ds_log_line(const char *msg)
{
	FILE *f = fopen("fat:/trace.txt", "a");
	if (!f)
		f = fopen("fat:/trace.txt", "w");
	if (!f)
		f = fopen("trace.txt", "a");
	if (!f)
		f = fopen("trace.txt", "w");
	if (f) {
		if (msg)
			fputs(msg, f);
		fputc('\n', f);
		fclose(f);
	}
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

static const VnPlatformOps ds_ops = {
    .file_size = file_size,
    .file_read = file_read,
    .font_upload = font_upload,
    .draw_glyph = draw_glyph,
    .glyphs_end = glyphs_end,
    .log = ds_log_line,
    .get_time_ms = get_time_ms,
    .sleep_ms = sleep_ms,
};

const VnPlatformOps *vn_platform_default_ops(void)
{
	return &ds_ops;
}

void fmv_select(int file)
{
	(void)file;
}
