#pragma once

/* Valores por consola para el backend SDL. Los .c solo usan estas macros. */

#if defined(__PSP__)
#include <pspkernel.h>
#elif defined(__WII__)
#include <fat.h>
#elif defined(_EE)
#include <sbv_patches.h>
#include <sifrpc.h>
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
<<<<<<< HEAD
    !defined(__SWITCH__) && !defined(_EE)
=======
    !defined(__SWITCH__) && !defined(__ORBIS__)
>>>>>>> agent/beam/T-609
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

#else
<<<<<<< HEAD
#error "Consola SDL no soportada: define __PSP__, _EE, __vita__, __3DS__, __WII__, NXDK o __SWITCH__"
=======
#error "Consola SDL no soportada: define __PSP__, __vita__, __3DS__, __WII__, NXDK, __SWITCH__ o __ORBIS__"
>>>>>>> agent/beam/T-609
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
