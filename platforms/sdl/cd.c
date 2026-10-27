#include "cd.h"
#include "audio.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#ifdef _EE
static char root[512] = "host:disc";
#else
static char root[512] = ".";
#endif
static char filename[600];
volatile uint32_t cd_sync_vblanks, cd_wait_vblanks;
int cd_init(void)
{
	const char *p = getenv("VN_DATA_DIR");
	if (p && *p)
		snprintf(root, sizeof(root), "%s", p);
	return 1;
}
static void make_path(const char *path)
{
	const char *base = strrchr(path, '\\');
	const char *slash = strrchr(path, '/');
	int i;
	base = base ? base + 1 : path;
	if (slash && slash + 1 > base)
		base = slash + 1;
	snprintf(filename, sizeof(filename), "%s/%s", root, base);
	for (i = (int)strlen(root) + 1; filename[i]; i++)
		filename[i] = (char)toupper((unsigned char)filename[i]);
}
int cd_find(const char *p, int *lba, int *size)
{
	FILE *f;
	long n;
	make_path(p);
	f = fopen(filename, "rb");
	if (!f)
		return -1;
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	fclose(f);
	if (lba)
		*lba = 0;
	if (size)
		*size = (int)n;
	return 0;
}
int cd_read_file(const char *p, void *b, int cap)
{
	FILE *f;
	long n;
	make_path(p);
	f = fopen(filename, "rb");
	if (!f)
		return -1;
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	rewind(f);
	if (n > cap || fread(b, 1, (size_t)n, f) != (size_t)n) {
		fclose(f);
		return -1;
	}
	fclose(f);
	return (int)n;
}
int cd_read_sectors(int l, int n, void *b)
{
	(void)l;
	(void)n;
	(void)b;
	return -1;
}
int cd_read_start(int o, int l, int n, void *b)
{
	(void)o;
	(void)l;
	(void)n;
	(void)b;
	return -1;
}
int cd_read_poll(int o)
{
	(void)o;
	return 0;
}
int cd_busy(void)
{
	return 0;
}
void cd_wait(void)
{
}
