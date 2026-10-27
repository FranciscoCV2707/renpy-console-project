#include "res.h"
#include "cd.h"
#include "video.h"
#include "gba_internal.h"
#include <stdio.h>
#include <string.h>

#define RES_MAX 8

static struct {
	int id;
	Image image;
	uint32_t last_used;
	int last_draw;
} cache[RES_MAX] __attribute__((section(".sbss")));

static uint32_t tick_counter = 0;
volatile uint32_t res_trace_tag = 0;

void res_new_scene(void)
{
	/* D25: al cambiar de escena, liberar todas las imágenes de la escena anterior */
	for (int i = 0; i < RES_MAX; i++) {
		if (cache[i].id) {
			gba_free_texture(cache[i].image.vram_x);
			cache[i].id = 0;
			cache[i].last_used = 0;
			cache[i].last_draw = 0;
		}
	}
}

void res_tick(void)
{
	tick_counter++;
	int now = video_frames();
	/* D25: liberar imágenes que dejaron de verse (HIDE o cambio de expresión) */
	for (int i = 0; i < RES_MAX; i++) {
		if (cache[i].id && cache[i].last_draw > 0) {
			if (now - cache[i].last_draw > 2) {
				gba_free_texture(cache[i].image.vram_x);
				cache[i].id = 0;
				cache[i].last_used = 0;
				cache[i].last_draw = 0;
			}
		}
	}
}

void res_mark_drawn(const Image *img)
{
	if (!img)
		return;
	int now = video_frames();
	for (int i = 0; i < RES_MAX; i++) {
		if (cache[i].id && &cache[i].image == img) {
			cache[i].last_draw = now;
			break;
		}
	}
}

void res_evict_undrawn(void)
{
	int now = video_frames();
	for (int i = 0; i < RES_MAX; i++) {
		if (cache[i].id && cache[i].last_draw != now) {
			gba_free_texture(cache[i].image.vram_x);
			cache[i].id = 0;
			cache[i].last_used = 0;
			cache[i].last_draw = 0;
		}
	}
}

const Image *res_get(int id)
{
	char path[32];
	int i, n;

	for (i = 0; i < RES_MAX; i++) {
		if (cache[i].id == id + 1) {
			cache[i].last_used = ++tick_counter;
			return &cache[i].image;
		}
	}

	snprintf(path, sizeof(path), "I%04d.IMG", id);
	const uint8_t *file_ptr = (const uint8_t *)cd_file_ptr(path, &n);
	if (!file_ptr || n <= 0)
		return NULL;

	int slot = -1;
	for (i = 0; i < RES_MAX; i++) {
		if (!cache[i].id) {
			slot = i;
			break;
		}
	}

	if (slot < 0) {
		int now = video_frames();
		uint32_t oldest = 0xFFFFFFFF;
		for (i = 0; i < RES_MAX; i++) {
			if (cache[i].last_draw != now && cache[i].last_used < oldest) {
				oldest = cache[i].last_used;
				slot = i;
			}
		}
		if (slot < 0)
			slot = 0;
		if (cache[slot].id) {
			gba_free_texture(cache[slot].image.vram_x);
			cache[slot].id = 0;
		}
	}

	if (img_load(&cache[slot].image, file_ptr, n, 0, 0, 0) != 0)
		return NULL;

	if (cache[slot].image.full_w > 240 || cache[slot].image.full_h > 160)
		cache[slot].image.big = 1;

	cache[slot].id = id + 1;
	cache[slot].last_used = ++tick_counter;
	cache[slot].last_draw = 0;
	return &cache[slot].image;
}

void res_touch(int id)
{
	for (int i = 0; i < RES_MAX; i++) {
		if (cache[i].id == id + 1) {
			cache[i].last_used = ++tick_counter;
			break;
		}
	}
}

void res_preload(int id)
{
	(void)res_get(id);
}

const Image *res_peek(int id)
{
	for (int i = 0; i < RES_MAX; i++) {
		if (cache[i].id == id + 1)
			return &cache[i].image;
	}
	return NULL;
}

int res_reserve_snapshot(int *vram_x, int *vram_y)
{
	if (vram_x)
		*vram_x = 0;
	if (vram_y)
		*vram_y = 0;
	return 1;
}

void res_release_snapshot(void)
{
}

void res_prefetch(const uint16_t *ids, int n)
{
	(void)ids;
	(void)n;
}

int res_prefetch_busy(void)
{
	return 0;
}

int res_have(int id)
{
	return res_peek(id) != NULL;
}

const uint8_t *res_cached_file(int id, int *size)
{
	char path[32];
	snprintf(path, sizeof(path), "I%04d.IMG", id);
	return (const uint8_t *)cd_file_ptr(path, size);
}

uint8_t *res_borrow_cache(int *bytes)
{
	if (bytes)
		*bytes = 0;
	return NULL;
}
