#pragma once

#include <stdint.h>
#include "img.h"
#include "video.h"

#define DS_SCREEN_W 256
#define DS_SCREEN_H 192

#define DS_MAX_TEXTURES 64

extern uint16_t top_fb[DS_SCREEN_W * DS_SCREEN_H];
extern uint16_t bottom_fb[DS_SCREEN_W * DS_SCREEN_H];
extern uint8_t ds_font_atlas[256 * 256 / 2];
extern int ds_in_title;
extern int ds_in_dialog;

void ds_draw_glyph(int layer, int x, int y, int u, int v, int w, int h, int r, int g, int b);
void ds_free_texture(int slot);
uint16_t ds_blend50(uint16_t c1, uint16_t c2);
void ds_close_trace(void);

void ds_queue_top_rect(int layer, int x, int y, int w, int h, int r, int g, int b, int blend);
void ds_queue_top_img(const Image *img, int layer, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b,
                      int angle, int brightness, int is_title);
void ds_queue_top_snapshot(int layer, int blend, int bright, int band_y, int band_bright);
void ds_render_img_top(const Image *img, int screen_x, int screen_y, int flip, int zoom, int r, int g, int b, int angle,
                       int brightness, int is_title);
