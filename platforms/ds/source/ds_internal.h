#pragma once

#include <stdint.h>

#define DS_SCREEN_W 256
#define DS_SCREEN_H 192

extern uint16_t top_fb[DS_SCREEN_W * DS_SCREEN_H];
extern uint16_t bottom_fb[DS_SCREEN_W * DS_SCREEN_H];
extern uint8_t ds_font_atlas[256 * 256 / 2];
extern int ds_in_title;
extern int ds_in_dialog;

void ds_draw_glyph(int layer, int x, int y, int u, int v, int w, int h, int r, int g, int b);
void ds_free_texture(int slot);
uint16_t ds_blend50(uint16_t c1, uint16_t c2);
