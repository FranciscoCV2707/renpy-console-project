#include "img.h"
#include "video.h"
#include "lz4.h"
#include "gba_internal.h"
#include <tonc.h>
#include <stdlib.h>
#include <stdio.h>
#include <malloc.h>
#include <string.h>

int img_brightness = 256;

typedef struct {
	uint8_t x, y; /* posición dentro de la imagen pre-escalada (0..w-1, 0..h-1) */
	uint8_t idx;
	uint8_t pad;
} GbaPoint;

typedef struct {
	uint8_t *data; /* tile 8-bit (w*h), tile 4-bit (sprites densos) o lista de puntos opacos */
	uint16_t palette[256];
	uint16_t w, h; /* tamaño almacenado: la imagen pre-escalada a la pantalla (3/4 x, 2/3 y) */
	int sparse;    /* 1: data es una lista de puntos opacos en vez de un tile */
	int packed;    /* 1: tile de índices de 4 bits (16 colores) */
	int count;     /* puntos de la lista dispersa */
	int in_use;
} GbaTexture;

static GbaTexture textures[GBA_MAX_TEXTURES] __attribute__((section(".sbss")));

void gba_free_texture(int slot)
{
	if (slot >= 0 && slot < GBA_MAX_TEXTURES && textures[slot].in_use) {
		if (textures[slot].data) {
			free(textures[slot].data);
			textures[slot].data = NULL;
		}
		textures[slot].in_use = 0;
	}
}

static uint16_t rd16(const uint8_t *p)
{
	return (uint16_t)(p[0] | ((unsigned)p[1] << 8));
}

static int color_distance(const uint8_t *file, int a, int b)
{
	int ca = rd16(file + 24 + a * 2), cb = rd16(file + 24 + b * 2);
	int dr = (ca & 31) - (cb & 31);
	int dg = ((ca >> 5) & 31) - ((cb >> 5) & 31);
	int db = ((ca >> 10) & 31) - ((cb >> 10) & 31);
	return dr * dr + dg * dg + db * db;
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
	for (int i = 0; i < GBA_MAX_TEXTURES; i++) {
		if (!textures[i].in_use) {
			slot = i;
			break;
		}
	}
	if (slot < 0) {
		/* Desalojar el primer slot en uso */
		slot = 0;
		gba_free_texture(slot);
	}

	uint8_t *indices = (uint8_t *)malloc(raw);
	while (!indices && res_evict_undrawn())
		indices = (uint8_t *)malloc(raw);
	{
		struct mallinfo mi = mallinfo();
		char msg[110];
		snprintf(msg, sizeof(msg), "DBG LOAD w%u h%u raw %lu ok %d arena %lu usado %lu libre %lu",
		         img->w, img->h, (unsigned long)raw, indices ? 1 : 0, (unsigned long)mi.arena,
		         (unsigned long)mi.uordblks, (unsigned long)mi.fordblks);
		mgba_log(msg);
	}
	if (!indices)
		return -1;

	if (lz4_decode(file + 544, (int)comp, indices, (int)raw) != (int)raw) {
		free(indices);
		return -1;
	}

	/* La pantalla de GBA es 3/4 del ancho y 2/3 del alto de los 320x240 del motor: la imagen se
	 * guarda ya reducida con esa proporción (la misma que usa render_cmd) para que fondo y
	 * personajes de una escena quepan juntos en el heap. La reducción se hace dentro del propio
	 * buffer (el destino siempre va por detrás del origen) y después se libera la cola con
	 * realloc. */
	int sw = img->w * 3 / 4;
	int sh = img->h * 2 / 3;
	if (sw < 1)
		sw = 1;
	if (sh < 1)
		sh = 1;
	for (int y = 0; y < sh; y++) {
		const uint8_t *src_row = indices + (y * img->h / sh) * img->w;
		uint8_t *dst_row = indices + y * sw;
		for (int x = 0; x < sw; x++)
			dst_row[x] = src_row[x * img->w / sw];
	}

	/* Un sprite casi transparente ocupa muchísimo menos como lista de puntos opacos que como
	 * tile: en las escenas con un fondo grande y un overlay fino (como el cuarto de chapter_x2)
	 * es lo que permite tener ambos en memoria a la vez (D25). */
	int sparse = 0;
	int count = 0;
	if (img->flags & 1) {
		for (int i = 0; i < sw * sh; i++) {
			if (indices[i])
				count++;
		}
		if (count > 0 && (size_t)count * sizeof(GbaPoint) < (size_t)sw * sh) {
			/* La lista se arma tras el tile reducido (siempre cabe: la condición exige
			 * count*4 < sw*sh, así que tile + lista < 2*sw*sh = w*h = raw) y luego se
			 * mueve al principio del buffer para soltar el resto con realloc. */
			GbaPoint *points = (GbaPoint *)(indices + sw * sh);
			int n = 0;
			for (int y = 0; y < sh; y++) {
				for (int x = 0; x < sw; x++) {
					uint8_t idx = indices[y * sw + x];
					if (!idx)
						continue;
					points[n].x = (uint8_t)x;
					points[n].y = (uint8_t)y;
					points[n].idx = idx;
					points[n].pad = 0;
					n++;
				}
			}
			memmove(indices, points, (size_t)n * sizeof(GbaPoint));
			sparse = 1;
			count = n;
		}
	}

	size_t stored = sparse ? (size_t)count * sizeof(GbaPoint) : (size_t)sw * sh;

	/* Los personajes se guardan a 16 colores (D19) en índices de 4 bits: con el fondo de la
	 * escena residente (28,8 KB a 256 colores) el temporal de decodificación del fondo solo
	 * cabe si los sprites densos ocupan la mitad. La paleta nueva son los 15 colores más usados
	 * de la original; cada píxel pasa al más cercano. */
	int packed = 0;
	if (!sparse && (img->flags & 1) && stored > 512) {
		int usage[256];
		uint8_t best[256];
		memset(usage, 0, sizeof(usage));
		for (int i = 0; i < sw * sh; i++)
			usage[indices[i]]++;

		int picked[15];
		int npicked = 0;
		for (int k = 0; k < 15 && npicked < 15; k++) {
			int top = -1;
			for (int i = 1; i < 256; i++) {
				if (usage[i] > 0 && (top < 0 || usage[i] > usage[top]))
					top = i;
			}
			if (top < 0)
				break;
			picked[npicked++] = top;
			usage[top] = 0;
		}

		for (int i = 0; i < 256; i++) {
			best[i] = 0;
			if (i == 0)
				continue;
			int top_dist = -1;
			for (int k = 0; k < npicked; k++) {
				int d = color_distance(file, i, picked[k]);
				if (top_dist < 0 || d < top_dist) {
					top_dist = d;
					best[i] = (uint8_t)(k + 1);
				}
			}
		}

		for (int i = 0; i < sw * sh; i += 2) {
			uint8_t lo = best[indices[i]];
			uint8_t hi = (i + 1 < sw * sh) ? best[indices[i + 1]] : 0;
			indices[i / 2] = (uint8_t)(lo | (hi << 4));
		}
		for (int k = 0; k < npicked; k++) {
			uint16_t c = rd16(file + 24 + picked[k] * 2);
			textures[slot].palette[k + 1] = (uint16_t)((c & 0x7fff) | 0x8000);
		}
		textures[slot].palette[0] = 0;
		packed = 1;
		stored = ((size_t)sw * sh + 1) / 2;
	}

	uint8_t *shrunk = (uint8_t *)realloc(indices, stored);
	if (shrunk)
		indices = shrunk;

	textures[slot].data = indices;
	textures[slot].w = (uint16_t)sw;
	textures[slot].h = (uint16_t)sh;
	textures[slot].sparse = sparse;
	textures[slot].packed = packed;
	textures[slot].count = count;
	textures[slot].in_use = 1;

	if (!packed) {
		for (int i = 0; i < 256; i++) {
			uint16_t c = rd16(file + 24 + i * 2);
			/* Formato PS1 BGR555 -> GBA BGR555 (ambos son 0bbbbbgggggrrrrr) */
			textures[slot].palette[i] = (uint16_t)((c & 0x7fff) | 0x8000);
		}
		if (img->flags & 1)
			textures[slot].palette[0] = 0;
	}

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

void gba_render_img(const Image *img, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b, int angle,
                    int brightness, int is_title)
{
	(void)r;
	(void)g;
	(void)b;
	(void)angle;

	if (!img || !img->loaded)
		return;

	if (img->kind == 2) {
		int w = img->full_w * zoom / 64;
		int h = img->full_h * zoom / 64;
		gba_queue_rect(LAYER_BG, screen_x, screen_y, w, h, img->solid[0], img->solid[1], img->solid[2], 0);
		return;
	}
	if (img->kind > 2)
		return;

	int slot = img->vram_x;
	if (slot >= GBA_MAX_TEXTURES || !textures[slot].in_use || !textures[slot].data)
		return;

	GbaTexture *tex = &textures[slot];
	int dst_x, dst_y, dst_w, dst_h;

	if (is_title) {
		dst_w = (img->w * zoom / 64) * 3 / 4;
		dst_h = (img->h * zoom / 64) * 2 / 3;
		dst_x = (GBA_SCREEN_W - dst_w) / 2;
		dst_y = 12;
	} else {
		/* Todas las imágenes (fondos y personajes) se dibujan en su posición del motor 320x240
		 * escalada 3/4 x y 2/3 y, como el resto de los comandos; la textura ya está
		 * pre-escalada, así que a zoom normal se copia 1:1. */
		int fw = img->full_w;
		int eff_x = screen_x + (flip ? (fw - img->x - img->w) * zoom / 64 : img->x * zoom / 64);
		int eff_y = screen_y + img->y * zoom / 64;
		dst_x = eff_x * 3 / 4;
		dst_y = eff_y * 2 / 3;
		dst_w = (img->w * zoom / 64) * 3 / 4;
		dst_h = (img->h * zoom / 64) * 2 / 3;
	}

	if (dst_w <= 0 || dst_h <= 0)
		return;

	if (tex->sparse) {
		/* Lista de puntos opacos: misma proyección que el muestreo del tile, un punto por
		 * píxel opaco de la imagen pre-escalada. */
		const GbaPoint *points = (const GbaPoint *)tex->data;
		for (int i = 0; i < tex->count; i++) {
			int sx = points[i].x;
			if (flip)
				sx = tex->w - 1 - sx;
			int px = dst_x + sx * dst_w / tex->w;
			int py = dst_y + points[i].y * dst_h / tex->h;
			if (px < 0 || px >= GBA_SCREEN_W || py < 0 || py >= GBA_SCREEN_H)
				continue;
			uint16_t c = tex->palette[points[i].idx];
			if (!(c & 0x8000))
				continue;
			if (brightness < 256) {
				int cr = ((c & 31) * brightness) >> 8;
				int cg = (((c >> 5) & 31) * brightness) >> 8;
				int cb = (((c >> 10) & 31) * brightness) >> 8;
				c = (uint16_t)(cr | (cg << 5) | (cb << 10) | 0x8000);
			}
			uint16_t *dst = gba_backbuffer + py * GBA_SCREEN_W + px;
			if (img->flags & IMG_TRANSLUCENT)
				*dst = gba_blend50(*dst, (uint16_t)(c & 0x7fff));
			else
				*dst = (uint16_t)(c & 0x7fff);
		}
		return;
	}

	int x0 = dst_x < 0 ? 0 : dst_x;
	int y0 = dst_y < 0 ? 0 : dst_y;
	int x1 = dst_x + dst_w > GBA_SCREEN_W ? GBA_SCREEN_W : dst_x + dst_w;
	int y1 = dst_y + dst_h > GBA_SCREEN_H ? GBA_SCREEN_H : dst_y + dst_h;

	for (int py = y0; py < y1; py++) {
		int dy = py - dst_y;
		int sy = dy * tex->h / dst_h;
		if (sy >= tex->h)
			sy = tex->h - 1;

		const uint8_t *src_row = tex->packed ? tex->data + (size_t)sy * tex->w / 2 : tex->data + sy * tex->w;
		uint16_t *dst_row = gba_backbuffer + py * GBA_SCREEN_W;

		for (int px = x0; px < x1; px++) {
			int dx = px - dst_x;
			int sx = flip ? (tex->w - 1 - (dx * tex->w / dst_w)) : (dx * tex->w / dst_w);
			if (sx < 0)
				sx = 0;
			if (sx >= tex->w)
				sx = tex->w - 1;

			uint8_t idx;
			if (tex->packed) {
				uint8_t pair = src_row[sx / 2];
				idx = (sx & 1) ? (pair >> 4) : (pair & 0x0F);
			} else {
				idx = src_row[sx];
			}
			if (idx == 0 && (img->flags & 1))
				continue;
			uint16_t c = tex->palette[idx];
			if (!(c & 0x8000))
				continue;

			if (brightness < 256) {
				int cr = ((c & 31) * brightness) >> 8;
				int cg = (((c >> 5) & 31) * brightness) >> 8;
				int cb = (((c >> 10) & 31) * brightness) >> 8;
				c = (uint16_t)(cr | (cg << 5) | (cb << 10) | 0x8000);
			}

			if (img->flags & IMG_TRANSLUCENT) {
				dst_row[px] = gba_blend50(dst_row[px], (uint16_t)(c & 0x7fff));
			} else {
				dst_row[px] = (uint16_t)(c & 0x7fff);
			}
		}
	}
}

static void draw_ex(const Image *img, int layer, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b,
                    int angle)
{
	if (!img || !img->loaded)
		return;

	res_mark_drawn(img);

	int is_title = (layer == LAYER_TEXT && screen_y < 120);
	gba_queue_img(img, layer, screen_x, screen_y, flip, zoom, r, g, b, angle, img_brightness, is_title);
}

void img_draw(const Image *img, int layer, int screen_x, int screen_y)
{
	draw_ex(img, layer, screen_x, screen_y, 0, 64, 128, 128, 128, 0);
}

void img_draw_flip(const Image *img, int layer, int screen_x, int screen_y, int flip)
{
	draw_ex(img, layer, screen_x, screen_y, flip, 64, 128, 128, 128, 0);
}

void img_draw_ex(const Image *img, int layer, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b)
{
	draw_ex(img, layer, screen_x, screen_y, flip, zoom, r, g, b, 0);
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
