#pragma once

/* Valores por consola para el backend SDL. Los .c solo usan estas macros. */

#if defined(__PSP__)
#include <pspkernel.h>
#elif defined(__WII__)
#include <fat.h>
#include <ogc/usbgecko.h>
#include <sys/iosupport.h>
#include <wiikeyboard/keyboard.h>
#elif defined(_EE)
#include <sbv_patches.h>
#include <sifrpc.h>
#elif defined(__3DS__)
#include <3ds.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/iosupport.h>
#endif

#if defined(NXDK)
#include <direct.h>
#include <SDL.h>
#else
#include <SDL2/SDL.h>
#endif

#if !defined(NXDK)
#include <sys/stat.h>
#endif

/* PC */
#if !defined(__PSP__) && !defined(__vita__) && !defined(__3DS__) && !defined(__WII__) && !defined(NXDK) &&             \
    !defined(__SWITCH__) && !defined(_EE) && !defined(__ORBIS__) && !defined(__PSL1GHT__)
#define SDL_TARGET_DATA_DIR             "."
#define SDL_TARGET_SAVE_DIR             "build/pc/save"
#define SDL_TARGET_WINDOW_W             960
#define SDL_TARGET_WINDOW_H             720
#define SDL_TARGET_MANUAL_SCALE         0
#define SDL_TARGET_USE_LOGICAL_SIZE     1
#define SDL_TARGET_INIT_FLAGS           (SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_GAMECONTROLLER | SDL_INIT_AUDIO)
#define SDL_TARGET_SET_MAIN_READY       0
#define SDL_TARGET_RENDERER_FLAGS       (SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
#define SDL_TARGET_HAS_GAME_CONTROLLER  1
#define SDL_TARGET_HAS_JOYSTICK         0
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 0
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      0
#define SDL_TARGET_RES_CACHE            512 /* cache de res.c; ~131 KB/imagen RGBA de media (706 medidas) */

/* PSP */
#elif defined(__PSP__)
#define SDL_TARGET_DATA_DIR             "ms0:/PSP/GAME/SNOOT/DATA"
#define SDL_TARGET_SAVE_DIR             "ms0:/PSP/GAME/SNOOT/SAVE"
#define SDL_TARGET_WINDOW_W             480
#define SDL_TARGET_WINDOW_H             272
#define SDL_TARGET_MANUAL_SCALE         1
#define SDL_TARGET_USE_LOGICAL_SIZE     0
#define SDL_TARGET_INIT_FLAGS           (SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_AUDIO)
#define SDL_TARGET_SET_MAIN_READY       1
#define SDL_TARGET_RENDERER_FLAGS       0
#define SDL_TARGET_HAS_GAME_CONTROLLER  0
#define SDL_TARGET_HAS_JOYSTICK         0
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 1
#define SDL_TARGET_PSP_MODULE_INFO      1
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1
#define SDL_TARGET_VIEW_X               60
#define SDL_TARGET_VIEW_Y               0
#define SDL_TARGET_VIEW_W               360
#define SDL_TARGET_VIEW_H               272
#define SDL_TARGET_RES_CACHE            24 /* 32 MB RAM / 2 MB VRAM: 24 imagenes ~ 3 MB de texturas */

/* PS2 (ps2sdk) */
#elif defined(_EE)
#define SDL_TARGET_DATA_DIR             "host:disc"
#define SDL_TARGET_SAVE_DIR             "build/pc/save"
#define SDL_TARGET_WINDOW_W             640
#define SDL_TARGET_WINDOW_H             448
#define SDL_TARGET_MANUAL_SCALE         0
#define SDL_TARGET_USE_LOGICAL_SIZE     1
#define SDL_TARGET_INIT_FLAGS           (SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_AUDIO)
#define SDL_TARGET_SET_MAIN_READY       0
#define SDL_TARGET_RENDERER_FLAGS       SDL_RENDERER_SOFTWARE
#define SDL_TARGET_HAS_GAME_CONTROLLER  0
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 0
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1
#define SDL_TARGET_RES_CACHE            24 /* 32 MB RAM / 4 MB GS: 24 imagenes ~ 3 MB de texturas */

/* PS Vita */
#elif defined(__vita__)
#define SDL_TARGET_DATA_DIR             "ux0:data/snoot"
#define SDL_TARGET_SAVE_DIR             "ux0:data/snoot/save"
#define SDL_TARGET_WINDOW_W             960
#define SDL_TARGET_WINDOW_H             544
#define SDL_TARGET_MANUAL_SCALE         1
#define SDL_TARGET_USE_LOGICAL_SIZE     0
#define SDL_TARGET_INIT_FLAGS           (SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_GAMECONTROLLER | SDL_INIT_AUDIO)
#define SDL_TARGET_SET_MAIN_READY       1
#define SDL_TARGET_RENDERER_FLAGS       (SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
#define SDL_TARGET_HAS_GAME_CONTROLLER  1
#define SDL_TARGET_HAS_JOYSTICK         0
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 1
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1
#define SDL_TARGET_VIEW_X               160
#define SDL_TARGET_VIEW_Y               32
#define SDL_TARGET_VIEW_W               640
#define SDL_TARGET_VIEW_H               480
#define SDL_TARGET_RES_CACHE            64 /* 512 MB RAM / 128 MB VRAM: 64 imagenes ~ 8 MB de texturas */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern struct _reent *__getreent(void);
extern int setenv(const char *name, const char *value, int overwrite);
static inline int vita_flush(FILE *f)
{
	(void)f;
	struct _reent *r = __getreent();
	if (r && r->_stdout)
		return fflush(r->_stdout);
	return 0;
}
#define fflush(f)          vita_flush(f)
static inline void vita_flush_on_exit(void)
{
	vita_flush(NULL);
	SDL_QuitSubSystem(SDL_INIT_AUDIO);
}
static inline void vita_set_main_ready(void)
{
	setenv("VN_SHOT_DIR", "ux0:data/snoot", 0);
	FILE *f = fopen("ux0:data/snoot/shot_names.txt", "r");
	if (f) {
		char names[256];
		if (fgets(names, sizeof(names), f)) {
			size_t l = strlen(names);
			if (l && names[l - 1] == '\n')
				names[l - 1] = 0;
			setenv("VN_SHOT_NAMES", names, 1);
		}
		fclose(f);
	}
	atexit(vita_flush_on_exit);
	(SDL_SetMainReady)();
	SDL_SetHint(SDL_HINT_RENDER_DRIVER, "VITA gxm");
}
#define SDL_SetMainReady() vita_set_main_ready()

/* Nintendo 3DS */
#elif defined(__3DS__)
#define SDL_TARGET_DATA_DIR             "sdmc:/3ds/snoot/data"
#define SDL_TARGET_SAVE_DIR             "build/pc/save"
#define SDL_TARGET_WINDOW_W             400
#define SDL_TARGET_WINDOW_H             240
#define SDL_TARGET_MANUAL_SCALE         0
#define SDL_TARGET_USE_LOGICAL_SIZE     1
#define SDL_TARGET_INIT_FLAGS           (SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_GAMECONTROLLER | SDL_INIT_AUDIO)
#define SDL_TARGET_SET_MAIN_READY       0
#define SDL_TARGET_RENDERER_FLAGS       (SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
#define SDL_TARGET_HAS_GAME_CONTROLLER  1
#define SDL_TARGET_HAS_JOYSTICK         0
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 0
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1
#define SDL_TARGET_RES_CACHE            32 /* 128/256 MB: 32 imagenes ~ 4 MB de texturas */

/* Wii */
#elif defined(__WII__)
#define SDL_TARGET_DATA_DIR             "sd:/apps/snoot/data"
#define SDL_TARGET_SAVE_DIR             "sd:/apps/snoot/save"
#define SDL_TARGET_WINDOW_W             640
#define SDL_TARGET_WINDOW_H             480
#define SDL_TARGET_MANUAL_SCALE         0
#define SDL_TARGET_USE_LOGICAL_SIZE     1
#define SDL_TARGET_INIT_FLAGS           (SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_GAMECONTROLLER | SDL_INIT_AUDIO)
#define SDL_TARGET_SET_MAIN_READY       0
#define SDL_TARGET_RENDERER_FLAGS       (SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
#define SDL_TARGET_HAS_GAME_CONTROLLER  1
#define SDL_TARGET_HAS_JOYSTICK         0
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 0
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       1
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1
#define SDL_TARGET_RES_CACHE            32 /* 24+64 MB: 32 imagenes ~ 4 MB de texturas */

/* Xbox clasica (nxdk) */
#elif defined(NXDK)
#define SDL_TARGET_DATA_DIR             "D:/data"
#define SDL_TARGET_SAVE_DIR             "build/pc/save"
#define SDL_TARGET_WINDOW_W             640
#define SDL_TARGET_WINDOW_H             480
#define SDL_TARGET_MANUAL_SCALE         0
#define SDL_TARGET_USE_LOGICAL_SIZE     1
#define SDL_TARGET_INIT_FLAGS           (SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_GAMECONTROLLER | SDL_INIT_AUDIO)
#define SDL_TARGET_SET_MAIN_READY       0
#define SDL_TARGET_RENDERER_FLAGS       (SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
#define SDL_TARGET_HAS_GAME_CONTROLLER  1
#define SDL_TARGET_HAS_JOYSTICK         0
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 0
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  0
#define SDL_TARGET_MKDIR_WITH_MODE      0
#define SDL_TARGET_RES_CACHE            32 /* 64 MB unificada: 32 imagenes ~ 4 MB de texturas */

/* Nintendo Switch */
#elif defined(__SWITCH__)
#define SDL_TARGET_DATA_DIR             "sdmc:/switch/snoot/data"
#define SDL_TARGET_SAVE_DIR             "build/pc/save"
#define SDL_TARGET_WINDOW_W             1280
#define SDL_TARGET_WINDOW_H             720
#define SDL_TARGET_MANUAL_SCALE         0
#define SDL_TARGET_USE_LOGICAL_SIZE     1
#define SDL_TARGET_INIT_FLAGS           (SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_GAMECONTROLLER | SDL_INIT_AUDIO)
#define SDL_TARGET_SET_MAIN_READY       0
#define SDL_TARGET_RENDERER_FLAGS       (SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
#define SDL_TARGET_HAS_GAME_CONTROLLER  1
#define SDL_TARGET_HAS_JOYSTICK         0
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 0
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1
#define SDL_TARGET_RES_CACHE            256 /* 4 GB: 256 imagenes ~ 33 MB de texturas */

/* PS4 (OpenOrbis) */
#elif defined(__ORBIS__)
#define SDL_TARGET_DATA_DIR             "/data/snoot"
#define SDL_TARGET_SAVE_DIR             "/data/snoot/save"
#define SDL_TARGET_WINDOW_W             1920
#define SDL_TARGET_WINDOW_H             1080
#define SDL_TARGET_MANUAL_SCALE         1
#define SDL_TARGET_USE_LOGICAL_SIZE     0
#define SDL_TARGET_INIT_FLAGS           (SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_JOYSTICK | SDL_INIT_AUDIO)
#define SDL_TARGET_SET_MAIN_READY       1
#define SDL_TARGET_RENDERER_FLAGS       0
#define SDL_TARGET_HAS_GAME_CONTROLLER  0
#define SDL_TARGET_HAS_JOYSTICK         1
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 1
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1
#define SDL_TARGET_VIEW_X               320
#define SDL_TARGET_VIEW_Y               60
#define SDL_TARGET_VIEW_W               1280
#define SDL_TARGET_VIEW_H               960
#define SDL_TARGET_RES_CACHE            256 /* 8 GB: 256 imagenes ~ 33 MB de texturas */

/* PS3 (PSL1GHT) */
#elif defined(__PSL1GHT__)
#define SDL_TARGET_DATA_DIR             "/dev_hdd0/game/SNOT00001/USRDIR/data"
#define SDL_TARGET_SAVE_DIR             "/dev_hdd0/game/SNOT00001/USRDIR/save"
#define SDL_TARGET_WINDOW_W             1280
#define SDL_TARGET_WINDOW_H             720
#define SDL_TARGET_MANUAL_SCALE         1
#define SDL_TARGET_USE_LOGICAL_SIZE     0
#define SDL_TARGET_INIT_FLAGS           (SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_GAMECONTROLLER | SDL_INIT_AUDIO)
#define SDL_TARGET_SET_MAIN_READY       1
#define SDL_TARGET_RENDERER_FLAGS       (SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
#define SDL_TARGET_HAS_GAME_CONTROLLER  1
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 1
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
/* SDL 2.0.13 del port PSL1GHT no tiene SDL_RenderGeometry (llego en 2.0.18): fallback a SDL_RenderFillRect. */
#define SDL_TARGET_HAS_RENDER_GEOMETRY  0
#define SDL_TARGET_MKDIR_WITH_MODE      1
#define SDL_TARGET_VIEW_X               480
#define SDL_TARGET_VIEW_Y               240
#define SDL_TARGET_VIEW_W               320
#define SDL_TARGET_VIEW_H               240
#define SDL_TARGET_RES_CACHE            64 /* 256 MB: 64 imagenes ~ 8 MB de texturas */

#else
#error                                                                                                                 \
    "Consola SDL no soportada: define __PSP__, _EE, __vita__, __3DS__, __WII__, NXDK, __SWITCH__, __ORBIS__ o __PSL1GHT__"
#endif

#if SDL_TARGET_SET_MAIN_READY
#define SDL_TARGET_CALL_SET_MAIN_READY() SDL_SetMainReady()
#else
#define SDL_TARGET_CALL_SET_MAIN_READY() ((void)0)
#endif

#if SDL_TARGET_NEEDS_FAT_INIT
#define SDL_TARGET_FAT_INIT() (void)fatInitDefault()
#else
#define SDL_TARGET_FAT_INIT() ((void)0)
#endif

#if SDL_TARGET_FLUSH_STDOUT_ENABLED
#define SDL_TARGET_FLUSH_STDOUT() fflush(stdout)
#else
#define SDL_TARGET_FLUSH_STDOUT() ((void)0)
#endif

#if defined(_EE)
/* El audio de SDL2 en PS2 carga libsd.irx y audsrv.irx por SIF (init_audio_driver de ps2_drivers): sin
 * SifInitRpc(0) y los parches SBV la RPC se queda esperando al IOP para siempre. */
#define SDL_TARGET_PREPARE_IOP()                                                                                       \
	do {                                                                                                           \
		SifInitRpc(0);                                                                                         \
		sbv_patch_enable_lmb();                                                                                \
		sbv_patch_disable_prefix_check();                                                                      \
	} while (0)
/* El ELF termina con exit(0) pero PCSX2 no se cierra: tools/ctl/ps2.py ve esta marca en el log y lo cierra. */
#define SDL_TARGET_QUIT_MARKER()                                                                                       \
	do {                                                                                                           \
		printf("VN_QUIT\n");                                                                                   \
		fflush(stdout);                                                                                        \
	} while (0)
#elif defined(__3DS__)
/* Canal de traza: Azahar solo recibe por log lo que el juego manda con svcOutputDebugString
 * (Kernel::SVC::OutputDebugString lo escribe como Debug.Emulated; verificado en T-610) y libctru
 * descarta stdout mientras no haya un consoleInit. Un devoptab propio de stdout manda cada linea
 * ahi sin tocar la consola de la GPU. */
static ssize_t ctr_svc_write(struct _reent *r, void *fd, const char *ptr, size_t len)
{
	const char *p = ptr;
	const char *end = ptr + len;
	(void)r;
	(void)fd;
	while (p < end) {
		const char *nl = (const char *)memchr(p, '\n', (size_t)(end - p));
		size_t n = nl ? (size_t)(nl - p) : (size_t)(end - p);
		if (n)
			svcOutputDebugString(p, (s32)n);
		p = nl ? nl + 1 : end;
	}
	return (ssize_t)len;
}
static const devoptab_t ctr_svc_devoptab = {
    .name = "stdout",
    .write_r = ctr_svc_write,
};
/* Las capturas del AUTOTEST (paso "shot") van a la SD, igual que en Vita: sin VN_SHOT_DIR el
 * video.c del backend no escribe nada, y en 3DS no hay forma de pasar variables de entorno. */
extern int setenv(const char *name, const char *value, int overwrite);
static inline void ctr_shot_env(void)
{
	FILE *f;
	char names[256];
	setenv("VN_SHOT_DIR", "sdmc:/3ds/snoot", 0);
	f = fopen("sdmc:/3ds/snoot/shot_names.txt", "r");
	if (f) {
		if (fgets(names, sizeof(names), f)) {
			size_t l = strlen(names);
			if (l && names[l - 1] == '\n')
				names[l - 1] = 0;
			setenv("VN_SHOT_NAMES", names, 1);
		}
		fclose(f);
	}
}
#define SDL_TARGET_PREPARE_IOP()                                                                                       \
	do {                                                                                                           \
		devoptab_list[STD_OUT] = &ctr_svc_devoptab;                                                            \
		setvbuf(stdout, NULL, _IOLBF, 0);                                                                      \
		ctr_shot_env();                                                                                        \
	} while (0)
/* Igual que en PS2/Wii: el exit(0) del AUTOTEST no cierra Azahar, tools/ctl/n3ds.py ve esta marca en el
 * log (via svcOutputDebugString) y corta el proceso. */
#define SDL_TARGET_QUIT_MARKER()                                                                                       \
	do {                                                                                                           \
		printf("VN_QUIT\n");                                                                                   \
		fflush(stdout);                                                                                        \
	} while (0)
#elif defined(__WII__)
/* El canal de traza: stdout hacia el USB Gecko del EXI 2. El puerto serie 2 de Dolphin expone el
 * gecko en ese canal y libogc no lo sondea (exi.c: el canal 2 "has no probe line"), mientras que
 * CON_EnableGecko solo acepta los canales 0/1, cuyo bit de insercion (EXT de EXI_STATUS) Dolphin
 * solo reporta con un dispositivo en el device 1: con el gecko en un slot siempre falla. Un
 * devoptab propio de stdout manda cada linea por usb_sendbuffer(2). */
static ssize_t wii_gecko_write(struct _reent *r, void *fd, const char *ptr, size_t len)
{
	(void)r;
	(void)fd;
	return usb_sendbuffer(2, ptr, (int)len) == (int)len ? (ssize_t)len : -1;
}
static const devoptab_t wii_gecko_devoptab = {
    .name = "stdout",
    .write_r = wii_gecko_write,
};
/* El pump de eventos de SDL2-Wii (SDL_ogckeyboard.c) llama KEYBOARD_GetEvent en cada vuelta pero
 * nunca KEYBOARD_Init: sin init la cola estatica de libwiikeyboard queda a cero y __lwp_queue_get
 * lee 0x00000000 (crash "Invalid read" antes de pintar nada). */
#define SDL_TARGET_PREPARE_IOP()                                                                                       \
	do {                                                                                                           \
		devoptab_list[STD_OUT] = &wii_gecko_devoptab;                                                          \
		setvbuf(stdout, NULL, _IOLBF, 0);                                                                      \
		(void)KEYBOARD_Init(NULL);                                                                             \
	} while (0)
/* Igual que en PS2: el exit(0) del AUTOTEST no cierra el batch de Dolphin, tools/ctl/wii.py ve esta
 * marca en el TCP del gecko y lo cierra. */
#define SDL_TARGET_QUIT_MARKER()                                                                                       \
	do {                                                                                                           \
		printf("VN_QUIT\n");                                                                                   \
		fflush(stdout);                                                                                        \
	} while (0)
#else
#define SDL_TARGET_PREPARE_IOP() ((void)0)
#define SDL_TARGET_QUIT_MARKER() ((void)0)
#endif

#if defined(NXDK)
#define make_dir(path) _mkdir(path)
#elif SDL_TARGET_MKDIR_WITH_MODE
#define make_dir(path) mkdir((path), 0777)
#else
#define make_dir(path) mkdir(path)
#endif
