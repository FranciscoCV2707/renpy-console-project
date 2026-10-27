#include "gbfs.h"
#include <ctype.h>
#include <string.h>

static const char GBFS_MAGIC[16] = {'P', 'i', 'n', 'E', 'i', 'g', 'h', 't', 'G', 'B', 'F', 'S', '\r', '\n', 0x1a, '\n'};

const GbfsHeader *gbfs_find(const void *start)
{
	const uint8_t *p = (const uint8_t *)start;
	const uint8_t *end = (const uint8_t *)0x0A000000;

	/* GBFS está alineado a múltiplos de 256 bytes */
	p = (const uint8_t *)(((uintptr_t)p + 255) & ~255);
	while (p + sizeof(GbfsHeader) <= end) {
		if (memcmp(p, GBFS_MAGIC, 16) == 0) {
			return (const GbfsHeader *)p;
		}
		p += 256;
	}
	return NULL;
}

static void normalize_name(char *out, size_t out_sz, const char *path)
{
	const char *base = strrchr(path, '\\');
	const char *slash = strrchr(path, '/');
	if (slash && (!base || slash > base))
		base = slash;
	if (base)
		base++;
	else
		base = path;

	size_t i = 0;
	while (base[i] && i + 1 < out_sz) {
		out[i] = (char)toupper((unsigned char)base[i]);
		i++;
	}
	out[i] = '\0';
}

const void *gbfs_get_file(const GbfsHeader *gbfs, const char *name, uint32_t *out_len)
{
	if (!gbfs)
		return NULL;

	char norm[32];
	normalize_name(norm, sizeof(norm), name);

	const GbfsEntry *dir = (const GbfsEntry *)((const uint8_t *)gbfs + gbfs->dir_ofs);
	for (uint16_t i = 0; i < gbfs->descs_count; i++) {
		if (strncmp(dir[i].name, norm, sizeof(dir[i].name)) == 0) {
			if (out_len)
				*out_len = dir[i].len;
			return (const uint8_t *)gbfs + dir[i].data_offset;
		}
	}
	return NULL;
}
