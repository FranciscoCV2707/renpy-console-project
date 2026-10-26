#include <stdio.h>
#include <psxapi.h>
#include <psxcd.h>
#include <psxetc.h>
#include <psxgpu.h>
#include <psxgte.h>
#include <psxpad.h>
#include <psxpress.h>
#include <string.h>
#include "audio.h"
#include "cd.h"
#include "input.h"
#include "res.h"
#include "special.h"
#include "video_ps1.h"

/* Video STR (MDEC) a pantalla completa con audio XA intercalado, como el ejemplo examples/mdec/strvideo del PSn00bSDK.
 * El CD lee en continuo (CdlReadS) y la interrupcion del CD copia cada sector de video al cuadro que se esta armando;
 * la lectora reproduce sola los sectores XA (CdlModeRT). Un cuadro completo se descomprime (VLC) en el bucle mientras
 * el MDEC decodifica el anterior en franjas de 16 columnas, que la interrupcion de su DMA sube al framebuffer oculto;
 * despues se muestra ese framebuffer.
 * Los buffers salen de la cache de imagenes de res (la escena no se dibuja durante el video): no ocupan RAM fija.
 * El video se reproduce entero dentro de update (el bucle principal espera); X lo corta. La musica se pausa y al
 * terminar sigue donde habria llegado: el STR ya trae mezclado lo que sonaba en el juego (tools/video en el port). */
#define STR_MAGIC 0x0160
#define STR_TYPE_MDEC 0x8001
#define STR_PAYLOAD 2016
#define FMV_MAX_W SCREEN_W
#define FMV_MAX_H SCREEN_H
#define FMV_BS_SECTORS 12                   /* sectores de un cuadro como maximo (320x176 a 24 cuadros/s en 2x: ~6) */
#define FMV_MDEC_WORDS 0x8000
#define FMV_SLICE_WORDS (16 * FMV_MAX_H / 2)
#define FMV_TIMEOUT 120                     /* cuadros sin sectores de video: el archivo termino o el CD fallo */

typedef struct {
	uint16_t magic, type, sector_id, sector_count;
	uint32_t frame_id, bs_length;
	uint16_t width, height;
	uint8_t bs_header[8];
	uint32_t reserved;
} StrHeader;

typedef struct {
	uint32_t *bs;                           /* FMV_BS_SECTORS sectores de bitstream */
	uint32_t *mdec;                         /* codigos para el MDEC (FMV_MDEC_WORDS) */
	int width, height;
	int bad;                                /* no cabe o le faltan sectores: no se decodifica */
} FmvFrame;

static FmvFrame frames[2];
static uint32_t *slices[2];
static StrHeader sector_header;             /* fuera de la pila: lo escribe la DMA del CD */
static DISPENV disp[2];
static RECT slice_pos;
static int slice_end;
static volatile int frame_id, sector_count, cur_frame, cur_slice, frame_ready, sector_pending, last_sector;

static int fmv_lba, fmv_size;
static int fmv_geom_done;
static int fmv_file = -1;                  /* -1: \VIDEO.STR; n: V<nn>.STR (fmv_select) */

void fmv_select(int file)
{
	fmv_file = file;
}

/* El MDEC necesita la interrupcion de DMA del canal 1 activa para que sus esperas funcionen (docs de
 * DecDCTinSync). Fuera del video basta con que exista. */
static void fmv_dma_idle(void)
{
}

/* Reparte la cache de res entre los dos cuadros y las dos franjas. 0 si no alcanza. */
static int fmv_buffers(void)
{
	int bytes, i;
	uint8_t *p = res_borrow_cache(&bytes);

	if (bytes < 2 * (FMV_BS_SECTORS * STR_PAYLOAD + 4 * (FMV_MDEC_WORDS + FMV_SLICE_WORDS)))
		return 0;
	for (i = 0; i < 2; i++) {
		frames[i].bs = (uint32_t *)p;
		p += FMV_BS_SECTORS * STR_PAYLOAD;
		frames[i].mdec = (uint32_t *)p;
		p += 4 * FMV_MDEC_WORDS;
		slices[i] = (uint32_t *)p;
		p += 4 * FMV_SLICE_WORDS;
	}
	return 1;
}

/* Un sector de video listo: su trozo va al cuadro que se arma. Al empezar otro cuadro, el anterior queda listo si
 * llegaron todos sus sectores. Un sector que no es de STR (otro archivo) o un cuadro anterior terminan el video. */
static void sector_handler(void)
{
	FmvFrame *f = &frames[cur_frame];

	CdGetSector(&sector_header, sizeof(StrHeader) / 4);
	last_sector = VSync(-1);
	if (sector_header.magic != STR_MAGIC || (int)sector_header.frame_id < frame_id) {
		frame_ready = -1;
		return;
	}
	if (sector_header.type != STR_TYPE_MDEC)
		return;
	if ((int)sector_header.frame_id > frame_id) {
		if (frame_id >= 0) {
			if (sector_count)
				f->bad = 1;
			frame_ready = 1;
		}
		frame_id = sector_header.frame_id;
		sector_count = sector_header.sector_count;
		cur_frame ^= 1;
		f = &frames[cur_frame];
		f->width = (sector_header.width + 15) & ~15;
		f->height = (sector_header.height + 15) & ~15;
		f->bad = f->width > FMV_MAX_W || f->height > FMV_MAX_H || sector_count > FMV_BS_SECTORS;
	}
	sector_count--;
	if (f->bad || sector_header.sector_id >= FMV_BS_SECTORS) {
		f->bad = 1;
		return;
	}
	CdGetSector(f->bs + STR_PAYLOAD / 4 * sector_header.sector_id, STR_PAYLOAD / 4);
}

/* Franja decodificada: sube a VRAM y pide la siguiente. Los sectores que llegaron mientras el MDEC usaba la DMA se
 * leen ahora (la DMA del CD y la salida del MDEC no pueden ir a la vez). */
static void mdec_dma_handler(void)
{
	if (sector_pending) {
		sector_handler();
		sector_pending = 0;
	}
	LoadImage(&slice_pos, slices[cur_slice]);
	cur_slice ^= 1;
	slice_pos.x += 16;
	if (slice_pos.x < slice_end)
		DecDCTout(slices[cur_slice], 16 * slice_pos.h / 2);
}

static void cd_event_handler(CdlIntrResult event, uint8_t *payload)
{
	(void)payload;
	if (event != CdlDataReady)
		return;
	if (DecDCTinSync(1))
		sector_pending = 1;
	else
		sector_handler();
}

/* Espera el siguiente cuadro completo (revisa X una vez por cuadro de pantalla). Su indice, o -1 al terminar. */
static int fmv_wait_frame(void)
{
	int seen = VSync(-1);

	while (!frame_ready) {
		int now = VSync(-1);

		if (now == seen)
			continue;
		seen = now;
		input_update();
		if (input_pressed(PAD_CROSS) || now - last_sector > FMV_TIMEOUT)
			return -1;
	}
	if (frame_ready < 0)
		return -1;
	frame_ready = 0;
	return cur_frame ^ 1;
}

static void fmv_play(void)
{
	uint8_t mode = CdlModeRT | CdlModeSpeed;
	void *old_dma;
	CdlCB old_ready;
	CdlLOC loc;
	FILL clear;
	int db = 0, shown = 0, t0, f;

	if (!fmv_buffers())
		return;
	cd_wait();
	audio_video_begin();
	setFill(&clear);                        /* los dos framebuffers en negro (las barras del 16:9 quedan asi) */
	setRGB0(&clear, 0, 0, 0);
	setXY0(&clear, 0, 0);
	setWH(&clear, SCREEN_W, 2 * SCREEN_H);
	DrawSync(0);
	DrawPrim(&clear);
	DrawSync(0);
	SetDefDispEnv(&disp[0], 0, 0, SCREEN_W, SCREEN_H);
	SetDefDispEnv(&disp[1], 0, SCREEN_H, SCREEN_W, SCREEN_H);
	PutDispEnv(&disp[db]);
	DecDCTvlcCopyTableV3((VLC_TableV3 *)0x1f800000);

	frame_id = -1;
	sector_count = cur_frame = cur_slice = frame_ready = sector_pending = 0;
	frames[0].bad = frames[1].bad = 1;
	last_sector = t0 = VSync(-1);
	EnterCriticalSection();
	old_dma = DMACallback(DMA_MDEC_OUT, &mdec_dma_handler);
	old_ready = CdReadyCallback(&cd_event_handler);
	ExitCriticalSection();
	CdControl(CdlSetmode, &mode, 0);
	CdIntToPos(fmv_lba, &loc);
	CdControl(CdlReadS, &loc, 0);

	while ((f = fmv_wait_frame()) >= 0) {
		FmvFrame *fr = &frames[f];
		VLC_Context vlc;

		if (fr->bad || DecDCTvlcStart(&vlc, fr->mdec, FMV_MDEC_WORDS, fr->bs) != 0)
			continue;
		/* el MDEC termina el cuadro anterior en el framebuffer oculto: se muestra y este va al otro */
		DecDCTinSync(0);
		DecDCToutSync(0);
		DrawSync(0);
		if (shown) {
			VSync(0);
			db ^= 1;
			PutDispEnv(&disp[db]);
		}
		DecDCTin(fr->mdec, DECDCT_MODE_16BPP);
		slice_pos.x = (SCREEN_W - fr->width) / 2;
		slice_pos.y = (db ? 0 : SCREEN_H) + (SCREEN_H - fr->height) / 2;
		slice_pos.w = 16;
		slice_pos.h = fr->height;
		slice_end = slice_pos.x + fr->width;
		DecDCTout(slices[cur_slice], 16 * fr->height / 2);
		shown = 1;
	}

	CdControlB(CdlPause, 0, 0);
	if (shown) {
		DecDCTinSync(0);
		DecDCToutSync(0);
	}
	DrawSync(0);
	EnterCriticalSection();
	CdReadyCallback(old_ready);
	DMACallback(DMA_MDEC_OUT, old_dma ? (void (*)(void))old_dma : &fmv_dma_idle);
	ExitCriticalSection();
	audio_video_end(VSync(-1) - t0);
}

static int fmv_begin(void)
{
	char name[12];

	if (fmv_file < 0)
		strcpy(name, "VIDEO.STR");
	else
		sprintf(name, "V%02d.STR", fmv_file);
	if (cd_find(name, &fmv_lba, &fmv_size) != 0)
		return 0;
	if (!fmv_geom_done) {
		InitGeom();                         /* el VLC usa la GTE */
		DecDCTReset(0);
		DMACallback(DMA_MDEC_OUT, &fmv_dma_idle);
		fmv_geom_done = 1;
	}
	return 1;
}

/* Reproduce el video completo y vuelve al guion */
static int fmv_update(void)
{
	fmv_play();
	return 1;
}

static void fmv_draw(void)
{
}

const Special special_fmv = { SP_IN_GAME | SP_OWN_R1 | SP_OWN_SCENE, fmv_begin, fmv_update, fmv_draw, 0 };
