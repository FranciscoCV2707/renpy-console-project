/*
 * Reproductor de STR sin callbacks de CD: lee bloques de sectores (esperando a que terminen), los alimenta de a un
 * sector al demultiplexor (core/str.c) y decodifica cada cuadro con la VLC y el MDEC en franjas de 16 columnas.
 * El MDEC se espera antes de subir cada franja a VRAM; el callback de DMA del MDEC debe estar instalado.
 * Contadores para leerlos desde el emulador: player_out.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <psxapi.h>
#include <psxcd.h>
#include <psxetc.h>
#include <psxgpu.h>
#include <psxgte.h>
#include <psxpress.h>
#include "str.h"

#define SCREEN_W 320
#define SCREEN_H 240
#define VIDEO_Y 32            /* la imagen 320x176 va centrada en la pantalla de 320x240 */
#define BLOCK 16              /* ancho de cada franja del MDEC, como en el ejemplo */
#define CHUNK 40              /* sectores por lectura: menos busquedas del CD */
#define MAX_H 240
/* Zona libre de VRAM donde se carga el cuadro (16 bits directo, 160x96). Pagina de textura: x en multiplos de 64,
 * y en 0 o 256; el cuadro cruza tres paginas de 64 pixeles. */
#define VRAM_X 640
#define VRAM_Y 256
#define DISP_Y 24             /* el cuadro (160x96) se muestra a doble tamano: 320x192, centrado */

static uint8_t chunk[CHUNK * STR_SECTOR] __attribute__((aligned(4)));
static uint8_t bs0[0x10000] __attribute__((aligned(4)));
static uint8_t bs1[0x10000] __attribute__((aligned(4)));
static uint32_t mdec[0x8000] __attribute__((aligned(4)));
static uint32_t slice[BLOCK * MAX_H / 2] __attribute__((aligned(4)));

/* [0] cuadros mostrados, [1] sectores leidos, [2] vueltas al inicio, [3] tamano del archivo,
 * [4] tiempo en el CD, [5] tiempo en la VLC, [6] tiempo en el MDEC y la subida (unidades del temporizador) */
volatile long player_out[8];

/* El MDEC necesita la interrupcion de DMA del canal 1 activa para que sus esperas funcionen (docs de
 * DecDCTinSync). No hace falta nada al terminar la transferencia: basta con que exista. */
static void mdec_dma_done(void)
{
}

/* Dibuja el cuadro desde VRAM a pantalla a doble tamano: tiras de 64, 64 y 32 pixeles (una por pagina) */
static void draw_frame(int w, int hh)
{
	static const int strip_x[3] = { 0, 64, 128 }, strip_w[3] = { 64, 64, 32 };
	static POLY_FT4 poly[3];
	int i;

	for (i = 0; i < 3; i++) {
		int x0 = strip_x[i] * 2, x1 = (strip_x[i] + strip_w[i]) * 2, y0 = DISP_Y, y1 = DISP_Y + hh * 2;
		int tw = strip_w[i];

		if (strip_x[i] >= w)
			continue;
		setPolyFT4(&poly[i]);
		setRGB0(&poly[i], 128, 128, 128);
		poly[i].x0 = x0; poly[i].y0 = y0;
		poly[i].x1 = x1; poly[i].y1 = y0;
		poly[i].x2 = x0; poly[i].y2 = y1;
		poly[i].x3 = x1; poly[i].y3 = y1;
		poly[i].u0 = 0;      poly[i].v0 = 0;
		poly[i].u1 = tw - 1; poly[i].v1 = 0;
		poly[i].u2 = 0;      poly[i].v2 = hh - 1;
		poly[i].u3 = tw - 1; poly[i].v3 = hh - 1;
		poly[i].tpage = getTPage(2, 0, VRAM_X + strip_x[i], VRAM_Y);
		DrawPrim(&poly[i]);
	}
}

int main(void)
{
	CdlFILE file;
	CdlLOC loc;
	StrDemux d;
	VLC_Context vctx;
	const uint8_t *bs;
	uint32_t len, num, sectors_total, sectors_read = 0;
	uint16_t w, h;
	uint8_t mode = CdlModeSpeed;
	int lba, ci = CHUNK, hh, x;
	unsigned t0, t1;
	RECT r;

	ResetGraph(0);
	{
		DISPENV disp;

		SetDefDispEnv(&disp, 0, 0, SCREEN_W, SCREEN_H);
		PutDispEnv(&disp);
		{
			DRAWENV draw;

			SetDefDrawEnv(&draw, 0, 0, SCREEN_W, SCREEN_H);
			draw.isbg = 0;
			PutDrawEnv(&draw);
		}
		SetDispMask(1);
	}
	CdInit();
	InitGeom();
	DecDCTReset(0);
	DMACallback(1, &mdec_dma_done);

	/* CdSearchFile solo es seguro buscando en directorios pequenos: aqui se busca en la raiz del disco
	 * de prueba. El motor ya no lo usa (core/cd.c recorre los directorios sin heap; ver
	 * docs/presupuesto-memoria.md). */
	if (!CdSearchFile(&file, "\\VIDEO.STR")) {
		printf("no se encontro VIDEO.STR\n");
		while (1)
			;
	}
	sectors_total = file.size / 2048;
	lba = CdPosToInt(&file.pos);
	player_out[3] = file.size;
	CdControl(CdlSetmode, &mode, 0);
	str_init(&d, bs0, bs1, sizeof(bs0));

	while (1) {
		/* un sector al demultiplexor; cuando completa un cuadro, se decodifica antes de seguir */
		if (!str_take(&d, &bs, &len, &w, &h, &num)) {
			if (ci >= CHUNK) {
				if (sectors_read + CHUNK > sectors_total) {
					/* fin del archivo: se vuelve al inicio */
					sectors_read = 0;
					str_init(&d, bs0, bs1, sizeof(bs0));
					player_out[2]++;
				}
				/* CdRead no avanza sola: cada bloque se pide desde su sector, como hace res.c en el motor */
				t0 = TIMER_VALUE(1);
				CdIntToPos(lba + sectors_read, &loc);
				CdControl(CdlSetloc, &loc, 0);
				CdRead(CHUNK, (uint32_t *)chunk, CdlModeSpeed);
				CdReadSync(0, 0);
				player_out[4] += (TIMER_VALUE(1) - t0) & 0xffff;
				sectors_read += CHUNK;
				player_out[1] = sectors_read;
				ci = 0;
			}
			str_feed(&d, chunk + ci * STR_SECTOR);
			ci++;
			continue;
		}

		hh = (h + 15) & 0xfff0;
		if (hh > MAX_H || w > SCREEN_W)
			continue;

		t0 = TIMER_VALUE(1);
		if (DecDCTvlcStart(&vctx, mdec, sizeof(mdec) / 4, (const uint32_t *)bs))
			continue;
		player_out[5] += (TIMER_VALUE(1) - t0) & 0xffff;

		/* el MDEC entrega el cuadro en franjas verticales de 16 columnas: cada franja se espera y se sube a VRAM */
		t1 = TIMER_VALUE(1);
		DecDCTin(mdec, DECDCT_MODE_16BPP);
		for (x = 0; x < w; x += BLOCK) {
			DecDCTout(slice, BLOCK * hh / 2);
			DecDCToutSync(0);
			setRECT(&r, VRAM_X + x, VRAM_Y, BLOCK, hh);
			LoadImage(&r, slice);
		}
		DecDCTinSync(0);
		DrawSync(0);
		draw_frame(w, hh);
		player_out[6] += (TIMER_VALUE(1) - t1) & 0xffff;
		player_out[0]++;
	}
	return 0;
}
