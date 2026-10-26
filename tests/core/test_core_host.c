/*
 * Prueba del nucleo en host con el backend PC: carga la fuente y un capitulo reales, ejecuta la VM hasta el primer
 * dialogo y lo dibuja con la maquina de escribir.
 * Uso: test_core_host <carpeta con FONT.BIN, C00.VNB y T00.TXT>
 */
#include <stdio.h>
#include <stdlib.h>
#include "chapter.h"
#include "text.h"
#include "vm.h"
#include "vn_platform.h"
#include "backend.h"

static int failures;

static void check(int ok, const char *what)
{
	printf("%s %s\n", ok ? "ok  " : "FAIL", what);
	if (!ok)
		failures++;
}

static int load_chapter(void *user, int chapter, VmChapter *out)
{
	(void)user;
	return chapter_open(chapter, out);
}

int main(int argc, char **argv)
{
	static const VmHost host = { 0, load_chapter, 0, 0 };
	static Vm vm;
	uint8_t *font;
	int font_size, i, glyphs;
	VmEvent ev = VM_EV_NONE;
	TextRun run;

	if (argc < 2) {
		fprintf(stderr, "uso: %s <carpeta de datos>\n", argv[0]);
		return 2;
	}
	vn_platform_pc_init(0, argv[1]);
	vn_platform_set(vn_platform_default_ops());

	font_size = vn_ops->file_size("FONT.BIN");
	check(font_size > 0, "FONT.BIN existe");
	if (font_size <= 0)
		return 1;
	font = malloc(font_size);
	check(vn_ops->file_read("FONT.BIN", font, font_size) == font_size, "FONT.BIN se lee completo");
	check(font_load(font, font_size) == 0, "font_load acepta FONT.BIN");
	check(font_line_height() > 0, "la fuente trae alto de linea");

	vm_init(&vm, &host);
	check(vm_start(&vm, 0, 0) == 0, "vm_start abre el capitulo 0");
	for (i = 0; i < 10000; i++) {
		ev = vm_run(&vm);
		if (ev == VM_EV_SAY || ev == VM_EV_END || ev == VM_EV_ERROR)
			break;
		if (ev == VM_EV_MENU)
			vm.choice = 0;
	}
	check(ev == VM_EV_SAY, "la VM llega a un dialogo");
	if (ev != VM_EV_SAY) {
		if (ev == VM_EV_ERROR && vm.error)
			printf("     error de la VM: %s\n", vm.error);
		return 1;
	}

	printf("     texto: %s\n", chapter_text(vm.ev_text));
	text_start(&run, chapter_text(vm.ev_text));
	text_reveal_page(&run);
	check(text_page_done(&run), "la pagina se revela completa");
	text_draw(&run, 1, 10, 200, 128, 128, 128);
	glyphs = vn_platform_pc_glyph_count();
	printf("     glifos dibujados: %d\n", glyphs);
	check(glyphs > 0, "text_draw dibuja glifos por el backend");

	printf("%s\n", failures ? "FALLO" : "TODO OK");
	return failures ? 1 : 0;
}
