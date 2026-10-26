/* Video de PS1: primitivas de la GPU y distribucion de la VRAM. Solo para los modulos de platforms/ps1. */
#pragma once

#include <psxgpu.h>
#include "video.h"

/* Posiciones en VRAM (palabras de 16 bits), ver docs/presupuesto-memoria.md de vn-engine-ps1 */
#define VRAM_BG_X      640
#define VRAM_BG_Y      0
#define VRAM_SPRITE_X  320
#define VRAM_SPRITE_Y  0
#define VRAM_FONT_X    960
#define VRAM_FONT_Y    0
#define CLUT_BG_Y      480
#define CLUT_SPRITE_Y  481
#define CLUT_FONT_X    0
#define CLUT_FONT_Y    500

void *video_alloc(int size);
void video_add(int layer, void *prim);
void video_set_tpage(int layer, int mode, int abr, int x, int y);
