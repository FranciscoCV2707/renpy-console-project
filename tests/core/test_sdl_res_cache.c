/*
 * Prueba del cache de imagenes del backend SDL (platforms/sdl/res.c) en host: cache negativo y desalojo con
 * proteccion por escena. Compilada junto a res.c con stubs de cd_read_file, img_load e img_release.
 */
#define SDL_MAIN_HANDLED
#include <stdio.h>
#include "cd.h"
#include "img_release.h"
#include "res.h"
#include "sdl_target.h"

static int failures;
static int cd_calls, load_calls, release_calls, slot;

static void check(int ok, const char *what)
{
	printf("%s %s\n", ok ? "ok  " : "FAIL", what);
	if (!ok)
		failures++;
}

int cd_read_file(const char *path, void *buf, int buf_bytes)
{
	int id;

	(void)buf;
	(void)buf_bytes;
	cd_calls++;
	if (sscanf(path, "\\DATA\\I%d.IMG", &id) != 1 || id == 9999)
		return -1;
	return 64;
}

int img_load(Image *img, const uint8_t *file, int file_size, int vram_x, int vram_y, int clut_y)
{
	(void)file;
	(void)file_size;
	(void)vram_x;
	(void)vram_y;
	(void)clut_y;
	load_calls++;
	img->vram_x = (uint16_t)++slot;
	img->loaded = 1;
	return 0;
}

void img_release(Image *img)
{
	release_calls++;
	img->vram_x = 0;
	img->loaded = 0;
}

int main(void)
{
	int cap = SDL_TARGET_RES_CACHE;
	int loaded = 0, i, before;

	check(cap >= 2, "SDL_TARGET_RES_CACHE deja sitio para mas de una imagen");

	/* cache negativo: un id que no existe solo se abre una vez */
	check(res_get(9999) == 0, "res_get de un id inexistente devuelve 0");
	check(res_get(9999) == 0, "res_get de un id inexistente sigue devolviendo 0");
	check(cd_calls == 1, "el id inexistente solo abre el archivo una vez");
	res_preload(9999);
	check(cd_calls == 1, "res_preload tampoco vuelve a abrir el id inexistente");

	/* la primera escena llena el cache */
	res_new_scene();
	for (i = 0; i < cap; i++)
		if (res_get(1000 + i))
			loaded++;
	check(loaded == cap, "res_get llena el cache con las imagenes que existen");
	check(load_calls == cap, "cada imagen cargada pasa por img_load una vez");

	/* con el cache lleno se desaloja la menos usada de otra escena y su textura se libera */
	res_new_scene();
	res_touch(1000);
	check(res_get(2000) != 0, "res_get con el cache lleno desaloja de otra escena");
	check(res_peek(1000) != 0, "lo tocado en la escena actual no se desaloja");
	check(res_peek(1001) == 0, "se desalojo la menos usada de la escena anterior");
	check(res_peek(2000) != 0, "la imagen nueva queda cargada");
	check(release_calls == 1, "desalojar libera la textura con img_release");

	/* la precarga no desaloja lo que se esta mostrando */
	res_new_scene();
	for (i = 0; i < cap; i++)
		res_touch(1000 + i);
	res_touch(2000);
	res_preload(3000);
	check(res_peek(3000) == 0, "res_preload sin sitio libre no carga nada");
	check(release_calls == 1, "res_preload no desaloja lo de la escena actual");
	check(res_peek(2000) != 0 && res_peek(1000) != 0, "lo de la escena actual sigue cargado");

	/* lo de la escena actual que no se dibujo en este cuadro ni en el anterior si sirve para dibujar */
	res_tick();
	res_tick();
	res_new_scene();
	for (i = 0; i < cap; i++)
		res_touch(1000 + i);
	res_touch(2000);
	check(res_get(3000) != 0, "res_get sin sitio desaloja lo no dibujado de la escena");
	check(release_calls == 2, "el segundo desalojo tambien libera la textura");
	check(res_peek(3000) != 0, "la imagen pedida para dibujar queda cargada");

	/* el cache negativo se mantiene entre escenas */
	before = cd_calls;
	check(res_get(9999) == 0, "el id inexistente sigue devolviendo 0 tras varias escenas");
	check(cd_calls == before, "el id inexistente no se reabre despues de varias escenas");

	printf("%s\n", failures ? "FALLO" : "TODO OK");
	return failures ? 1 : 0;
}
