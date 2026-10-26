#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "vm.h"

static const char *directory;
static uint8_t buffer[65536];

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
	char path[1024];
	FILE *file;
	size_t size;

	(void)user;
	snprintf(path, sizeof(path), "%s/C%02d.VNB", directory, chapter);
	file = fopen(path, "rb");
	if (!file)
		return -1;
	size = fread(buffer, 1, sizeof(buffer), file);
	fclose(file);
	if (size < 32 || memcmp(buffer, "VNB1", 4) || read32(buffer + 8) > size - 32)
		return -1;
	out->code = buffer + 32;
	out->code_size = read32(buffer + 8);
	out->text_base = read32(buffer + 12);
	out->text_count = read16(buffer + 16);
	out->anim_count = 0;
	out->anims = 0;
	return 0;
}

int main(int argc, char **argv)
{
	Vm vm;
	VmHost host = { 0, load_chapter, 0, 0 };
	char *choices;
	int steps, index;

	if (argc < 3)
		return 2;
	directory = argv[1];
	choices = argc > 3 ? argv[3] : "";
	vm_init(&vm, &host);
	if (vm_start(&vm, atoi(argv[2]), 0))
		return 3;
	for (steps = 0; steps < 1000000; steps++) {
		VmEvent event = vm_run(&vm);

		if (event == VM_EV_ERROR) {
			fprintf(stderr, "%s\n", vm.error);
			return 4;
		}
		if (event == VM_EV_END)
			break;
		if (event == VM_EV_SAY)
			printf("SAY %d %d %d %d\n", vm.chapter, vm.ev_text, vm.ev_gid, vm.ev_speaker);
		if (event == VM_EV_MENU) {
			printf("MENU %d", vm.menu_n);
			for (index = 0; index < vm.menu_n; index++)
				printf(" %d", vm.menu_text[index]);
			printf("\n");
			vm.choice = (int)strtol(choices, &choices, 10);
			if (*choices == ',')
				choices++;
		}
	}
	if (steps == 1000000)
		return 5;
	printf("END\nVARS ");
	for (index = 0; index < VM_VARS; index++)
		printf("%s%d", index ? "," : "", vm.vars[index]);
	printf("\n");
	return 0;
}
