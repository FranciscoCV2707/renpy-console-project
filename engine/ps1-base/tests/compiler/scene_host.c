#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "scene.h"

static uint16_t read16(const uint8_t *data)
{
	return (uint16_t)(data[0] | data[1] << 8);
}

static uint32_t read32(const uint8_t *data)
{
	return data[0] | data[1] << 8 | data[2] << 16 | (uint32_t)data[3] << 24;
}

int main(int argc, char **argv)
{
	uint8_t buffer[65536];
	Vm vm;
	VmSprite sprite;
	SpriteLook look;
	FILE *file;
	size_t size;
	uint32_t offset;

	if (argc != 3 && argc != 4)
		return 2;
	file = fopen(argv[1], "rb");
	if (!file)
		return 3;
	size = fread(buffer, 1, sizeof(buffer), file);
	fclose(file);
	if (size < 32 || memcmp(buffer, "VNB1", 4))
		return 4;
	offset = read32(buffer + 24);
	if (offset >= size)
		return 5;
	memset(&vm, 0, sizeof(vm));
	memset(&sprite, 0, sizeof(sprite));
	vm.ch.anim_count = read16(buffer + 18);
	vm.ch.anims = buffer + offset;
	sprite.image = 1;
	sprite.anim = argc == 4 ? atoi(argv[3]) : 1;
	scene_look(&vm, &sprite, atoi(argv[2]), &look);
	printf("%d %d %d %d %d %d\n", look.image, look.xa, look.ya, look.zoom, look.alpha, look.angle);
	return 0;
}
