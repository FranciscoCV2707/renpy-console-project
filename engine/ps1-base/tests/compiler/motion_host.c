/* Corre un VNB con core/vm.c y core/scene.c como el motor: el reloj avanza `frames_per_say` cuadros por dialogo y
 * VmHost.capture usa scene_capture (salvo con skip = 1). En cada SAY imprime la alineacion x del sprite `tag` en
 * cada desfase de la lista `offsets` (cuadros despues del SAY, separados por comas). */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "scene.h"

static uint8_t buffer[65536];
static size_t buffer_size;
static int skip;

static uint16_t read16(const uint8_t *data)
{
	return (uint16_t)(data[0] | data[1] << 8);
}

static uint32_t read32(const uint8_t *data)
{
	return data[0] | data[1] << 8 | data[2] << 16 | (uint32_t)data[3] << 24;
}

static int load_chapter(void *user, int chapter, VmChapter *out)
{
	(void)user;
	if (chapter != 0)
		return -1;
	out->code = buffer + 32;
	out->code_size = read32(buffer + 8);
	out->text_base = read32(buffer + 12);
	out->text_count = read16(buffer + 16);
	out->anim_count = read16(buffer + 18);
	out->anims = read32(buffer + 24) < buffer_size ? buffer + read32(buffer + 24) : 0;
	return 0;
}

static int capture(void *user, const Vm *vm, const VmSprite *s, VmLook *out)
{
	(void)user;
	return !skip && scene_capture(vm, s, (int)(vm->now - s->shown_at), out);
}

int main(int argc, char **argv)
{
	Vm vm;
	VmHost host = { 0, load_chapter, 0, capture };
	FILE *file;
	int steps, per_say, tag;

	if (argc != 6)
		return 2;
	file = fopen(argv[1], "rb");
	if (!file)
		return 3;
	buffer_size = fread(buffer, 1, sizeof(buffer), file);
	fclose(file);
	if (buffer_size < 32 || memcmp(buffer, "VNB1", 4))
		return 4;
	per_say = atoi(argv[2]);
	tag = atoi(argv[3]);
	skip = atoi(argv[4]);
	vm_init(&vm, &host);
	if (vm_start(&vm, 0, 0))
		return 5;
	for (steps = 0; steps < 100000; steps++) {
		VmEvent event = vm_run(&vm);

		if (event == VM_EV_ERROR) {
			fprintf(stderr, "%s\n", vm.error);
			return 6;
		}
		if (event == VM_EV_END)
			break;
		if (event == VM_EV_SAY) {
			VmSprite *s = vm_sprite(&vm, tag);
			char *offsets = argv[5];

			printf("SAY");
			while (s && *offsets) {
				SpriteLook look;

				scene_look(&vm, s, (int)(vm.now - s->shown_at) + (int)strtol(offsets, &offsets, 10), &look);
				printf(" %d", look.xa);
				if (*offsets == ',')
					offsets++;
			}
			printf("\n");
			vm.now += (uint32_t)per_say;
		}
	}
	return steps == 100000 ? 7 : 0;
}
