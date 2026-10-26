/* Video: lo que la app y el nucleo dibujan por capas. Cada plataforma lo implementa (API por enlace, PLAN.md D15);
 * lo propio de la GPU de PS1 (primitivas, VRAM, CLUT) esta en platforms/ps1/video_ps1.h. */
#pragma once

#include <stdint.h>

#define SCREEN_W 320
#define SCREEN_H 240
#define VIEW_Y   30            /* la imagen 16:9 de 320x180 va centrada en la pantalla de 4:3 */
#define VIEW_H   180

/* Capas: 0 se dibuja al final (al frente). Dentro de una capa, lo agregado despues se dibuja antes. */
#define LAYER_DEBUG   0
#define LAYER_TEXT    1
#define LAYER_BOX     2
#define LAYER_FX      3        /* transiciones: sobre la escena, debajo de la caja de texto */
#define LAYER_SPRITE0 4        /* 4..19: un sprite por capa (16 como VM_MAX_SPRITES); el menor numero queda al frente */
#define LAYER_BG      20
#define LAYER_COUNT   21

void video_init(void);
void video_rect(int layer, int x, int y, int w, int h, int r, int g, int b, int blend);
void video_triangle_down(int layer, int x, int y, int w, int h, int r, int g, int b);
void video_flip(void);
/* Copia de la pantalla para las transiciones, en el lugar que dio res_reserve_snapshot */
void video_snapshot(int x, int y);
/* bright: modulacion de color (128 = normal, 0 = negro); desde la fila band_y se usa band_bright */
void video_snapshot_draw(int layer, int x, int y, int blend, int bright, int band_y, int band_bright);
int video_frames(void);
void video_clip_scene(void);   /* llamar despues de agregar la escena (se dibuja primero) */
void video_unclip(void);       /* llamar despues de agregar la caja de texto y la interfaz */
/* Retrazado vertical: esperar el siguiente y contador desde el arranque (60 por segundo en NTSC) */
void video_wait_vblank(void);
int video_vblank_count(void);
