#include <tonc.h>

#include "bg_asset.h"

static const unsigned char font8x8[128][8] = {
    [' '] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}, ['A'] = {0x3C, 0x42, 0x42, 0x7E, 0x42, 0x42, 0x42, 0x00},
    ['B'] = {0x7C, 0x42, 0x42, 0x7C, 0x42, 0x42, 0x7C, 0x00}, ['D'] = {0x7C, 0x42, 0x42, 0x42, 0x42, 0x42, 0x7C, 0x00},
    ['E'] = {0x7E, 0x40, 0x40, 0x7C, 0x40, 0x40, 0x7E, 0x00}, ['G'] = {0x3C, 0x40, 0x40, 0x4E, 0x42, 0x42, 0x3C, 0x00},
    ['H'] = {0x42, 0x42, 0x42, 0x7E, 0x42, 0x42, 0x42, 0x00}, ['L'] = {0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x7E, 0x00},
    ['O'] = {0x3C, 0x42, 0x42, 0x42, 0x42, 0x42, 0x3C, 0x00}, ['S'] = {0x3E, 0x40, 0x40, 0x3C, 0x02, 0x02, 0x7C, 0x00},
};

static void draw_text(int x, int y, const char *text, u8 color)
{
	for (; *text != '\0'; ++text) {
		unsigned char c = (unsigned char)*text;
		if (c >= 128) {
			c = ' ';
		}
		const unsigned char *glyph = font8x8[c];
		for (int row = 0; row < 8; ++row) {
			unsigned char bits = glyph[row];
			for (int col = 0; col < 8; ++col) {
				if (bits & (unsigned char)(0x80 >> col)) {
					/* la VRAM no acepta escrituras de 8 bits: se reescribe el par de píxeles */
					int pos = (y + row) * 240 + (x + col);
					volatile u16 *pair = (volatile u16 *)vid_mem + pos / 2;
					*pair = (pos & 1) ? (u16)((*pair & 0x00FF) | (color << 8))
					                  : (u16)((*pair & 0xFF00) | color);
				}
			}
		}
		x += 8;
	}
}

int main(void)
{
	REG_DISPCNT = DCNT_MODE4 | DCNT_BG2;

	LZ77UnCompVram(gba_bg_asset, (void *)MEM_VRAM);

	volatile u16 *palette = (volatile u16 *)MEM_PAL;
	const u16 *asset_palette = (const u16 *)(gba_bg_asset + GBA_BG_ASSET_LEN - 512);
	for (int i = 0; i < 256; ++i) {
		palette[i] = asset_palette[i];
	}
	palette[255] = 0x7FFF;

	draw_text(8, 8, "HOLA DESDE GBA", 255);

	for (;;) {
	}

	return 0;
}
