#include "cd.h"
#include <nds.h>
#include <filesystem.h>
#include <fat.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

static int nitro_ok = 0;
volatile uint32_t cd_sync_vblanks, cd_wait_vblanks;

int cd_init(void)
{
	if (!nitro_ok) {
		nitro_ok = nitroFSInit(NULL);
		bool ok = fatInitDefault();
		(void)ok;
	}
	return nitro_ok ? 1 : 0;
}

static void make_path(char *out, size_t out_sz, const char *prefix, const char *path)
{
	const char *base = strrchr(path, '\\');
	const char *slash = strrchr(path, '/');
	if (slash && slash + 1 > base)
		base = slash + 1;
	if (!base)
		base = path;
	else
		base = base + 1;

	snprintf(out, out_sz, "%s%s", prefix, base);
	size_t pfx_len = strlen(prefix);
	for (size_t i = pfx_len; out[i]; i++)
		out[i] = (char)toupper((unsigned char)out[i]);
}

int cd_find(const char *path, int *lba, int *size)
{
	if (!nitro_ok && !cd_init())
		return -1;
	char filename[128];
	make_path(filename, sizeof(filename), "nitro:/", path);
	FILE *f = fopen(filename, "rb");
	if (!f) {
		make_path(filename, sizeof(filename), "nitro:/DATA/", path);
		f = fopen(filename, "rb");
	}
	if (!f) {
		make_path(filename, sizeof(filename), "fat:/", path);
		f = fopen(filename, "rb");
	}
	if (!f) {
		make_path(filename, sizeof(filename), "fat:/DATA/", path);
		f = fopen(filename, "rb");
	}
	if (!f)
		return -1;
	fseek(f, 0, SEEK_END);
	long n = ftell(f);
	fclose(f);
	if (lba)
		*lba = 0;
	if (size)
		*size = (int)n;
	return 0;
}

int cd_read_file(const char *path, void *buf, int buf_bytes)
{
	if (!nitro_ok && !cd_init())
		return -1;
	char filename[128];
	make_path(filename, sizeof(filename), "nitro:/", path);
	FILE *f = fopen(filename, "rb");
	if (!f) {
		make_path(filename, sizeof(filename), "nitro:/DATA/", path);
		f = fopen(filename, "rb");
	}
	if (!f) {
		make_path(filename, sizeof(filename), "fat:/", path);
		f = fopen(filename, "rb");
	}
	if (!f) {
		make_path(filename, sizeof(filename), "fat:/DATA/", path);
		f = fopen(filename, "rb");
	}
	if (!f)
		return -1;
	fseek(f, 0, SEEK_END);
	long n = ftell(f);
	rewind(f);
	if (n > buf_bytes || fread(buf, 1, (size_t)n, f) != (size_t)n) {
		fclose(f);
		return -1;
	}
	fclose(f);
	return (int)n;
}

int cd_read_sectors(int lba, int sectors, void *buf)
{
	(void)lba;
	(void)sectors;
	(void)buf;
	return -1;
}

int cd_read_start(int owner, int lba, int sectors, void *buf)
{
	(void)owner;
	(void)lba;
	(void)sectors;
	(void)buf;
	return -1;
}

int cd_read_poll(int owner)
{
	(void)owner;
	return 0;
}

int cd_busy(void)
{
	return 0;
}

void cd_wait(void)
{
}
