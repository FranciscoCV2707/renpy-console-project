#include "res.h"
#include "cd.h"
#include "sdl_target.h"
#include <stdio.h>
#include <string.h>

extern void img_release(Image *img);

/* Cache de imagenes acotado (SDL_TARGET_RES_CACHE) con desalojo por escena, como el res.c de platforms/ps1: lo que
 * se toco en la escena actual (res_touch) no se desaloja; si hace falta sitio para dibujar tambien sirve lo que no
 * se dibujo en este cuadro ni en el anterior (res_tick cuenta los cuadros). Los ids que no existen quedan marcados
 * en `missing` (1 bit por id de 16 bits) para no reabrir el archivo cada vez que se piden. */
#define RES_IDS 0x10000

typedef struct {
	int id; /* 0 = libre; si no, id de la imagen + 1 */
	Image image;
	uint32_t last_use;  /* ultima escena en que se pidio (res_get o res_touch) */
	uint32_t last_draw; /* ultimo cuadro de res_get; 0 si solo se precargo */
} Entry;

static Entry cache[SDL_TARGET_RES_CACHE];
static uint8_t missing[RES_IDS / 8];
static uint32_t scene_now = 1, draw_clock = 2;
volatile uint32_t res_trace_tag;

static Entry *find(int id)
{
	int i;

	for (i = 0; i < SDL_TARGET_RES_CACHE; i++)
		if (cache[i].id == id + 1)
			return &cache[i];
	return 0;
}

static int missing_get(int id)
{
	return id >= 0 && id < RES_IDS && (missing[id >> 3] >> (id & 7)) & 1;
}

static void missing_set(int id)
{
	if (id >= 0 && id < RES_IDS)
		missing[id >> 3] |= (uint8_t)(1 << (id & 7));
}

/* Desaloja la entrada menos usada que no pertenece a la escena actual. Con for_draw tambien puede desalojar una de
 * la escena actual que no se dibujo en este cuadro ni en el anterior (cuadros de animacion ya pasados o precargados).
 * Devuelve 0 si no hay ninguna. */
static int evict_one(int for_draw)
{
	int i, best = -1;

	for (i = 0; i < SDL_TARGET_RES_CACHE; i++)
		if (cache[i].id && cache[i].last_use < scene_now &&
		    (best < 0 || cache[i].last_use < cache[best].last_use))
			best = i;
	if (best < 0 && for_draw)
		for (i = 0; i < SDL_TARGET_RES_CACHE; i++)
			if (cache[i].id && cache[i].last_draw + 1 < draw_clock &&
			    (best < 0 || cache[i].last_draw < cache[best].last_draw))
				best = i;
	if (best < 0)
		return 0;
	img_release(&cache[best].image);
	cache[best].id = 0;
	return 1;
}

static Entry *new_entry(int for_draw)
{
	int i;

	for (;;) {
		for (i = 0; i < SDL_TARGET_RES_CACHE; i++)
			if (!cache[i].id)
				return &cache[i];
		if (!evict_one(for_draw))
			return 0;
	}
}

static const Image *load_image(int id, int for_draw)
{
	/* Estatico: 180 KB en el stack desbordan el del hilo principal de consolas como Wii (128 KB)
	 * y corrompen la memoria que sigue (crash en el primer SCENE). */
	static uint8_t file[180000];
	char path[32];
	Entry *e;
	int n;

	e = find(id);
	if (e) {
		e->last_use = scene_now;
		if (for_draw)
			e->last_draw = draw_clock;
		return &e->image;
	}
	if (missing_get(id))
		return 0;
	snprintf(path, sizeof(path), "\\DATA\\I%04d.IMG", id);
	n = cd_read_file(path, file, sizeof(file));
	if (n < 0) {
		missing_set(id);
		return 0;
	}
	e = new_entry(for_draw);
	if (!e)
		return 0;
	memset(e, 0, sizeof(*e));
	e->id = id + 1;
	e->last_use = scene_now;
	e->last_draw = for_draw ? draw_clock : 0;
	if (img_load(&e->image, file, n, 0, 0, 0)) {
		e->id = 0;
		return 0;
	}
	return &e->image;
}

void res_new_scene(void)
{
	scene_now++;
}

void res_tick(void)
{
	draw_clock++;
}

const Image *res_get(int id)
{
	return load_image(id, 1);
}

void res_touch(int id)
{
	Entry *e = find(id);

	if (e)
		e->last_use = scene_now;
}

void res_preload(int id)
{
	load_image(id, 0);
}

const Image *res_peek(int id)
{
	Entry *e = find(id);

	return e ? &e->image : 0;
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
	/* RES_SOUND: look_ahead mezcla sonidos ambientales con las imagenes (en PS1 van a la cache de RAM); aqui el
	 * audio los lee solo al sonar. Tratarlos como imagen buscaba I32770.IMG y demas en cada vistazo. */
	for (i = 0; i < n; i++)
		if (!(ids[i] & RES_SOUND))
			res_preload(ids[i]);
}

int res_prefetch_busy(void)
{
	return 0;
}

int res_have(int id)
{
	/* un sonido no espera a esta cache: con 0 el motor volvia a pedir toda la precarga en cada linea */
	return (id & RES_SOUND) || res_peek(id) != NULL;
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
