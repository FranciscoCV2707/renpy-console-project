/*
 * Backend PS1 (PSn00bSDK): las operaciones del nucleo sobre los modulos de hardware de esta carpeta (cd, video).
 * El codigo de la fuente y los archivos es el mismo que tenian core/text.c y core/chapter.c en vn-engine-ps1.
 * Lo que el nucleo aun no usa queda en NULL.
 */
#include <stdio.h>
#include <psxgpu.h>
#include "backend_ps1.h"
#include "cd.h"
#include "video.h"

/* Los archivos del juego viven en \DATA\ del disco */
static void data_path(char *out, const char *name)
{
	sprintf(out, "\\DATA\\%s", name);
}

static int ps1_file_size(const char *name)
{
	char path[32];
	int lba, size;

	data_path(path, name);
	return cd_find(path, &lba, &size) == 0 ? size : -1;
}

static int ps1_file_read(const char *name, void *buf, int buf_bytes)
{
	char path[32];

	data_path(path, name);
	return cd_read_file(path, buf, buf_bytes);
}

static void ps1_font_upload(const uint8_t *atlas_4bpp)
{
	static uint16_t clut[16] __attribute__((aligned(4)));
	RECT rect;
	int i;

	/* Atlas de 256x256 a 4 bits = 64 palabras de ancho */
	setRECT(&rect, VRAM_FONT_X, VRAM_FONT_Y, 64, 256);
	LoadImage(&rect, (const uint32_t *)atlas_4bpp);
	DrawSync(0);

	/* 16 niveles de gris; el indice 0 es transparente */
	for (i = 0; i < 16; i++) {
		int v = (i * 31) / 15;
		clut[i] = i ? (uint16_t)(v | (v << 5) | (v << 10)) : 0;
	}
	setRECT(&rect, CLUT_FONT_X, CLUT_FONT_Y, 16, 1);
	LoadImage(&rect, (const uint32_t *)clut);
	DrawSync(0);
}

static void ps1_draw_glyph(int layer, int x, int y, int u, int v, int w, int h, int r, int g, int b)
{
	SPRT *s = (SPRT *)video_alloc(sizeof(SPRT));

	if (!s)
		return;
	setSprt(s);
	setXY0(s, x, y);
	setWH(s, w, h);
	setUV0(s, u, v);
	setRGB0(s, r, g, b);
	setClut(s, CLUT_FONT_X, CLUT_FONT_Y);
	setSemiTrans(s, 1);                      /* mezcla aditiva: el borde suave se funde con el fondo */
	video_add(layer, s);
}

/* En la tabla de orden lo agregado despues se dibuja antes: el tpage de la fuente queda delante de sus glifos */
static void ps1_glyphs_end(int layer)
{
	video_set_tpage(layer, 0, 1, VRAM_FONT_X, VRAM_FONT_Y);
}

static void ps1_log(const char *msg)
{
	printf("%s\n", msg);
}

static const VnPlatformOps ps1_ops = {
	.file_size = ps1_file_size,
	.file_read = ps1_file_read,
	.font_upload = ps1_font_upload,
	.draw_glyph = ps1_draw_glyph,
	.glyphs_end = ps1_glyphs_end,
	.log = ps1_log,
};

const VnPlatformOps *vn_platform_ps1_ops(void)
{
	return &ps1_ops;
}
