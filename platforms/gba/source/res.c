#include "res.h"
#include "cd.h"
#include "gba_internal.h"
#include <stdio.h>
#include <string.h>

#define RES_MAX 12

static struct {
	int id;
	Image image;
	uint32_t last_used;
} cache[RES_MAX] __attribute__((section(".sbss")));

static uint32_t tick_counter = 0;
volatile uint32_t res_trace_tag = 0;

void res_new_scene(void)
{
}

void res_tick(void)
{
	tick_counter++;
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
		uint32_t oldest = 0xFFFFFFFF;
		slot = 0;
		for (i = 0; i < RES_MAX; i++) {
			if (cache[i].last_used < oldest) {
				oldest = cache[i].last_used;
				slot = i;
			}
		}
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
