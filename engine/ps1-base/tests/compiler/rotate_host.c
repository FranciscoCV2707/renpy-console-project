/* Native check of the rotation pieces of core/scene.c: scene_rotate and the angle kept by scene_capture.
 * Usage: rotate_host chapter.vnb  (animation 1 rotates, animation 2 does not) */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "scene.h"

static uint32_t read32(const uint8_t *data)
{
	return data[0] | data[1] << 8 | data[2] << 16 | (uint32_t)data[3] << 24;
}

int main(int argc, char **argv)
{
	static uint8_t buffer[65536];
	static Vm vm;
	VmSprite *sprite = &vm.sprites[0];
	SpriteLook look;
	FILE *file;
	int x, y;

	scene_rotate(100, 0, 4096, 0, &x, &y);          /* 90 degrees: right turns into down */
	printf("%d %d\n", x, y);
	scene_rotate(0, -50, 4096, 0, &x, &y);          /* up turns into right */
	printf("%d %d\n", x, y);
	if (argc != 2)
		return 2;
	file = fopen(argv[1], "rb");
	if (!file)
		return 3;
	(void)fread(buffer, 1, sizeof(buffer), file);
	fclose(file);
	vm.ch.anim_count = (uint16_t)(buffer[18] | buffer[19] << 8);
	vm.ch.anims = buffer + read32(buffer + 24);
	sprite->used = 1;
	sprite->image = 1;
	sprite->anim = 1;
	scene_capture(&vm, sprite, 30, &vm.from[0]);
	printf("%d\n", vm.from[0].angle);
	/* the new animation (without rotation) starts from the captured angle and turns back to 0 */
	sprite->anim = 2;
	scene_look(&vm, sprite, 0, &look);
	printf("%d", look.angle);
	scene_look(&vm, sprite, 30, &look);
	printf(" %d", look.angle);
	scene_look(&vm, sprite, 60, &look);
	printf(" %d\n", look.angle);
	return 0;
}
