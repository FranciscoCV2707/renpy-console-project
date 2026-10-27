#include "res.h"
#include "cd.h"
#include <stdio.h>
#include <string.h>

#define RES_MAX 2048
static struct {
	int id;
	Image image;
} cache[RES_MAX];
volatile uint32_t res_trace_tag;
void res_new_scene(void)
{
}
void res_tick(void)
{
}
const Image *res_get(int id)
{
	char path[32];
	uint8_t file[180000];
	int i, n;
	for (i = 0; i < RES_MAX; i++)
		if (cache[i].id == id + 1)
			return &cache[i].image;
	snprintf(path, sizeof(path), "\\DATA\\I%04d.IMG", id);
	n = cd_read_file(path, file, sizeof(file));
	if (n < 0)
		return NULL;
	for (i = 0; i < RES_MAX && cache[i].id; i++) {
	}
	if (i == RES_MAX)
		return NULL;
	if (img_load(&cache[i].image, file, n, 0, 0, 0))
		return NULL;
	cache[i].id = id + 1;
	return &cache[i].image;
}
void res_touch(int id)
{
	(void)id;
}
void res_preload(int id)
{
	(void)res_get(id);
}
const Image *res_peek(int id)
{
	int i;
	for (i = 0; i < RES_MAX; i++)
		if (cache[i].id == id + 1)
			return &cache[i].image;
	return NULL;
}
int res_reserve_snapshot(int *x, int *y)
{
	if (x)
		*x = 0;
	if (y)
		*y = 0;
	return 1;
}
void res_release_snapshot(void)
{
}
void res_prefetch(const uint16_t *ids, int n)
{
	int i;
	for (i = 0; i < n; i++)
		res_preload(ids[i]);
}
int res_prefetch_busy(void)
{
	return 0;
}
int res_have(int id)
{
	return res_peek(id) != NULL;
}
const uint8_t *res_cached_file(int id, int *n)
{
	(void)id;
	if (n)
		*n = 0;
	return NULL;
}
uint8_t *res_borrow_cache(int *n)
{
	if (n)
		*n = 0;
	return NULL;
}
