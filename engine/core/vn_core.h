/* engine/core/vn_core.h
 * Contrato 2: interfaz del nucleo compartido.
 * El nucleo NO conoce ninguna consola. Los backends implementan VnPlatformOps.
 */
#ifndef VN_CORE_H
#define VN_CORE_H

#include <stddef.h>

/* Capacidades declaradas por cada plataforma (Contrato 3). */
typedef struct VnPlatformCaps {
    int screen_w;
    int screen_h;
    int max_sprites;
    int vram_bytes;
    int ram_bytes;
    int audio_channels;
    int has_video;   /* 1 si soporta video */
    int has_touch;   /* 1 si tiene tactil */
    int color_depth; /* 4, 8, 16, 32 */
} VnPlatformCaps;

/* Operaciones que el backend debe implementar. */
typedef struct VnPlatformOps {
    /* graficos */
    void (*clear)(void);
    void (*draw_sprite)(int id, int x, int y, int w, int h, const void *tex);
    void (*present)(void);
    /* audio */
    void (*play_music)(int track_id, int loop);
    void (*play_sfx)(int sfx_id);
    /* entrada */
    int  (*poll_input)(void);
    /* almacenamiento */
    int  (*save)(const void *data, size_t size, int slot);
    int  (*load)(void *data, size_t size, int slot);
    /* debug/log */
    void (*log)(const char *msg);
    /* tiempo */
    unsigned int (*get_time_ms)(void);
    void (*sleep_ms)(unsigned int ms);
} VnPlatformOps;

/* Contexto opaco del nucleo. */
typedef struct VnContext VnContext;

/* Configuracion de inicio. */
typedef struct VnConfig {
    const VnPlatformCaps *caps;
    const char            *game_id;
    const char            *entry_scene;
} VnConfig;

/* API publica del nucleo. */
VnContext *vn_init(const VnPlatformOps *ops, const VnConfig *cfg);
int        vn_load_scene(VnContext *ctx, const char *scene_id);
int        vn_step(VnContext *ctx);          /* avanza un frame/linea */
void       vn_shutdown(VnContext *ctx);

/* Helpers de log estructurado (Contrato: logs [ENGINE]). */
void vn_log(VnContext *ctx, const char *fmt, ...);

#endif /* VN_CORE_H */
