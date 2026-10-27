#include "save.h"
#include <string.h>

static uint8_t ram_save[SAVE_DATA_BYTES];
static int has_save = 0;

void save_set_icon(const uint8_t *p)
{
	(void)p;
}

SaveResult save_read(uint8_t *data)
{
	if (!has_save)
		return SAVE_NO_FILE;
	memcpy(data, ram_save, SAVE_DATA_BYTES);
	return SAVE_OK;
}

SaveResult save_write(uint8_t *data)
{
	memcpy(ram_save, data, SAVE_DATA_BYTES);
	has_save = 1;
	return SAVE_OK;
}
