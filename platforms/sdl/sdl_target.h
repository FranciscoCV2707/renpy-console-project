#pragma once

/* Valores por consola para el backend SDL. Los .c solo usan estas macros. */

#if defined(__PSP__)
#include <pspkernel.h>
#elif defined(__WII__)
#include <fat.h>
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
    !defined(__SWITCH__)
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
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 0
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      0

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
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 1
#define SDL_TARGET_PSP_MODULE_INFO      1
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1
#define SDL_TARGET_VIEW_X               60
#define SDL_TARGET_VIEW_Y               0
#define SDL_TARGET_VIEW_W               360
#define SDL_TARGET_VIEW_H               272

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
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 1
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1
#define SDL_TARGET_VIEW_X               160
#define SDL_TARGET_VIEW_Y               32
#define SDL_TARGET_VIEW_W               640
#define SDL_TARGET_VIEW_H               480
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
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 0
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1

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
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 0
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       1
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1

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
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 0
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  0
#define SDL_TARGET_MKDIR_WITH_MODE      0

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
#define SDL_TARGET_FLUSH_STDOUT_ENABLED 0
#define SDL_TARGET_PSP_MODULE_INFO      0
#define SDL_TARGET_NEEDS_FAT_INIT       0
#define SDL_TARGET_HAS_RENDER_GEOMETRY  1
#define SDL_TARGET_MKDIR_WITH_MODE      1

#else
#error "Consola SDL no soportada: define __PSP__, __vita__, __3DS__, __WII__, NXDK o __SWITCH__"
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

#if defined(NXDK)
#define make_dir(path) _mkdir(path)
#elif SDL_TARGET_MKDIR_WITH_MODE
#define make_dir(path) mkdir((path), 0777)
#else
#define make_dir(path) mkdir(path)
#endif
