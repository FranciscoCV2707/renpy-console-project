#pragma once

#include "img.h"
#include "video.h"
#include <stdint.h>

#define GBA_SCREEN_W 240
#define GBA_SCREEN_H 160

#define GBA_MAX_TEXTURES 16

extern uint16_t gba_backbuffer[GBA_SCREEN_W * GBA_SCREEN_H];
extern int gba_backbuffer_scratched;

void gba_draw_glyph(int layer, int x, int y, int u, int v, int w, int h, int r, int g, int b);
void gba_free_texture(int slot);
uint16_t gba_blend50(uint16_t c1, uint16_t c2);

void gba_queue_rect(int layer, int x, int y, int w, int h, int r, int g, int b, int blend);
void gba_queue_img(const Image *img, int layer, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b,
                   int angle, int brightness, int is_title);
void gba_queue_snapshot(int layer, int blend, int bright, int band_y, int band_bright);

const void *cd_file_ptr(const char *path, int *size);
void mgba_log(const char *msg);
const uint8_t *gba_get_font_atlas(void);
void res_mark_drawn(const Image *img);
int res_evict_undrawn(void);
