#include "cd.h"
#include "gbfs.h"
#include "gba_internal.h"
#include <string.h>

static const GbfsHeader *gbfs_archive = NULL;
volatile uint32_t cd_sync_vblanks = 0;
volatile uint32_t cd_wait_vblanks = 0;

int cd_init(void)
{
	mgba_log("GBA: CD_INIT START");
	if (!gbfs_archive) {
		gbfs_archive = gbfs_find((const void *)0x08000000);
	}
	if (gbfs_archive) {
		mgba_log("GBA: GBFS ARCHIVE FOUND!");
	} else {
		mgba_log("GBA: GBFS ARCHIVE NOT FOUND!");
	}
	return gbfs_archive != NULL ? 1 : 0;
}

const void *cd_file_ptr(const char *path, int *size)
{
	if (!gbfs_archive && !cd_init())
		return NULL;
	uint32_t len = 0;
	const void *ptr = gbfs_get_file(gbfs_archive, path, &len);
	if (!ptr)
		return NULL;
	if (size)
		*size = (int)len;
	return ptr;
}

int cd_find(const char *path, int *lba, int *size)
{
	int sz = 0;
	if (!cd_file_ptr(path, &sz))
		return -1;
	if (lba)
		*lba = 0;
	if (size)
		*size = sz;
	return 0;
}

int cd_read_file(const char *path, void *buf, int buf_bytes)
{
	int sz = 0;
	const void *ptr = cd_file_ptr(path, &sz);
	if (!ptr || sz > buf_bytes)
		return -1;
	memcpy(buf, ptr, (size_t)sz);
	return sz;
}
