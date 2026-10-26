/*
 * Prueba del demultiplexor STR en el PC: lee un .str de psxavenc (sectores de 2336 bytes), busca donde empieza el
 * sector de datos (cabecera 0x0160) y reensambla los cuadros. Uso: test_demux <video.str>
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "str.h"

#define RAW_SECTOR 2336

static uint16_t rd16(const uint8_t *p)
{
	return (uint16_t)(p[0] | p[1] << 8);
}

/* Donde empieza el dato de usuario en cada sector: la cabecera de video (0x0160, 0x8001) aparece en un
 * desplazamiento fijo. Se busca en los primeros sectores de video; los de audio no la tienen. */
static int find_offset(const uint8_t *file, long size)
{
	static const int candidates[] = { 0, 8, 12, 16, 24 };
	long pos;
	int i;

	for (pos = 0; pos + RAW_SECTOR <= size && pos < 64L * RAW_SECTOR; pos += RAW_SECTOR)
		for (i = 0; i < (int)(sizeof(candidates) / sizeof(candidates[0])); i++) {
			long o = pos + candidates[i];

			if (o + 4 <= size && rd16(file + o) == 0x0160 && rd16(file + o + 2) == 0x8001)
				return candidates[i];
		}
	return -1;
}

int main(int argc, char **argv)
{
	FILE *f;
	uint8_t *file, *buf0, *buf1;
	long size, pos;
	int off, sectors = 0, video = 0, bad = 0;
	StrDemux d;
	const uint8_t *bs;
	uint32_t len;
	uint16_t w, h;
	uint32_t num;
	uint32_t cap = 0x40000;
	int taken = 0, last_id = -1, gaps = 0;

	if (argc < 2)
		return 2;
	f = fopen(argv[1], "rb");
	if (!f)
		return 2;
	fseek(f, 0, SEEK_END);
	size = ftell(f);
	fseek(f, 0, SEEK_SET);
	file = malloc(size);
	buf0 = malloc(cap);
	buf1 = malloc(cap);
	if (!file || !buf0 || !buf1 || fread(file, 1, size, f) != (size_t)size)
		return 2;
	fclose(f);

	off = find_offset(file, size);
	if (off < 0) {
		printf("no se encontro la cabecera STR en el primer sector\n");
		return 1;
	}
	printf("desplazamiento de datos: %d bytes en cada sector de %d\n", off, RAW_SECTOR);

	str_init(&d, buf0, buf1, cap);
	for (pos = 0; pos + RAW_SECTOR <= size; pos += RAW_SECTOR) {
		int r = str_feed(&d, file + pos + off);

		sectors++;
		if (r == 1)
			video++;
		if (r < 0)
			bad++;
		while (str_take(&d, &bs, &len, &w, &h, &num)) {
			int id = (int)num;

			if (w != 320 || h != 176 || len == 0)
				printf("cuadro %d raro: %ux%u, %u bytes\n", id, w, h, len);
			if (last_id >= 0 && id != last_id + 1)
				gaps++;
			last_id = id;
			taken++;
		}
	}

	printf("sectores %d, de video %d, sin cabecera STR %d\n", sectors, video, bad);
	printf("cuadros completos %d, sacados %d, perdidos %d, huecos en la secuencia %d\n", d.frames, taken,
	       d.dropped, gaps);
	free(file);
	free(buf0);
	free(buf1);
	return (taken > 0 && d.dropped == 0 && gaps == 0) ? 0 : 1;
}
