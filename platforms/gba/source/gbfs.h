#pragma once

#include <stddef.h>
#include <stdint.h>

typedef struct {
	char magic[16]; /* "PinEightGBFS\r\n\x1a\n" */
	uint32_t total_len;
	uint16_t dir_ofs;
	uint16_t descs_count;
	char reserved[8];
} __attribute__((packed)) GbfsHeader;

typedef struct {
	char name[24]; /* null-padded */
	uint32_t len;
	uint32_t data_offset;
} __attribute__((packed)) GbfsEntry;

const GbfsHeader *gbfs_find(const void *start);
const void *gbfs_get_file(const GbfsHeader *gbfs, const char *name, uint32_t *out_len);
