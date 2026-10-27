#include <nds.h>

#include "bg_sample_bin.h"
#include "font.h"

#define SCREEN_WIDTH  256
#define SCREEN_HEIGHT 192

static void fill_screen(u16 *framebuffer, u16 color)
{
	for (int i = 0; i < SCREEN_WIDTH * SCREEN_HEIGHT; i++) {
		framebuffer[i] = color;
	}
}

int main(void)
{
	videoSetMode(MODE_5_2D);
	vramSetBankA(VRAM_A_MAIN_BG);
	int top = bgInit(3, BgType_Bmp16, BgSize_B16_256x256, 0, 0);
	dmaCopy(bg_sample_bin, bgGetGfxPtr(top), bg_sample_bin_size);

	videoSetModeSub(MODE_5_2D);
	vramSetBankC(VRAM_C_SUB_BG);
	int bottom = bgInitSub(3, BgType_Bmp16, BgSize_B16_256x256, 0, 0);
	u16 *framebuffer = bgGetGfxPtr(bottom);
	fill_screen(framebuffer, ARGB16(1, 4, 6, 12));
	font_draw_text(framebuffer, 65, 92, "Hola desde Snoot Game", ARGB16(1, 31, 31, 31));

	while (1) {
		swiWaitForVBlank();
	}

	return 0;
}
