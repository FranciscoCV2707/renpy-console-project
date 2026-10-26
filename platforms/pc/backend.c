/* platforms/pc/backend.c
 * Implementacion minima del backend PC (stubs). Reemplazar con SDL2 cuando este disponible.
 */
#include "platforms/pc/backend.h"

#include <stdio.h>
#include <stdlib.h>

static VnPlatformCaps pc_caps = {
    .screen_w = 320,
    .screen_h = 240,
    .max_sprites = 32,
    .vram_bytes = 0,
    .ram_bytes = 64 * 1024 * 1024,
    .audio_channels = 16,
    .has_video = 1,
    .has_touch = 0,
    .color_depth = 32
};

static void pc_clear(void) { /* TODO: SDL_RenderClear */ }
static void pc_draw_sprite(int id, int x, int y, int w, int h, const void *tex) {
    (void)id; (void)x; (void)y; (void)w; (void)h; (void)tex;
    /* TODO: SDL_RenderCopy */
}
static void pc_present(void) { /* TODO: SDL_RenderPresent */ }
static void pc_play_music(int track_id, int loop) { (void)track_id; (void)loop; }
static void pc_play_sfx(int sfx_id) { (void)sfx_id; }
static int  pc_poll_input(void) { return 0; }
static int  pc_save(const void *data, size_t size, int slot) { (void)data; (void)size; (void)slot; return 0; }
static int  pc_load(void *data, size_t size, int slot) { (void)data; (void)size; (void)slot; return 0; }
static void pc_log(const char *msg) { printf("[PC] %s\n", msg); }
static unsigned int pc_get_time_ms(void) { return 0; }
static void pc_sleep_ms(unsigned int ms) { (void)ms; }

static VnPlatformOps pc_ops = {
    .clear = pc_clear,
    .draw_sprite = pc_draw_sprite,
    .present = pc_present,
    .play_music = pc_play_music,
    .play_sfx = pc_play_sfx,
    .poll_input = pc_poll_input,
    .save = pc_save,
    .load = pc_load,
    .log = pc_log,
    .get_time_ms = pc_get_time_ms,
    .sleep_ms = pc_sleep_ms
};

const VnPlatformOps *vn_platform_pc_ops(void) { return &pc_ops; }

int vn_platform_pc_init(const VnPlatformCaps *caps) {
    if (caps) pc_caps = *caps;
    pc_log("PC backend init (stub)");
    return 0;
}

void vn_platform_pc_shutdown(void) {
    pc_log("PC backend shutdown");
}
