/* platforms/pc/backend.c
 * Backend PC minimo: archivos desde una carpeta, graficos y audio sin salida. Reemplazar el dibujo con SDL2.
 */
#include "backend.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

static char data_dir[512] = ".";
static int glyph_count;

static FILE *open_data(const char *name) {
    char path[600];
    snprintf(path, sizeof(path), "%s/%s", data_dir, name);
    return fopen(path, "rb");
}

static int pc_file_size(const char *name) {
    FILE *f = open_data(name);
    long size;
    if (!f) return -1;
    fseek(f, 0, SEEK_END);
    size = ftell(f);
    fclose(f);
    return (int)size;
}

static int pc_file_read(const char *name, void *buf, int buf_bytes) {
    FILE *f = open_data(name);
    long size;
    if (!f) return -1;
    fseek(f, 0, SEEK_END);
    size = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (size > buf_bytes || fread(buf, 1, (size_t)size, f) != (size_t)size) {
        fclose(f);
        return -1;
    }
    fclose(f);
    return (int)size;
}

static void pc_font_upload(const uint8_t *atlas_4bpp) { (void)atlas_4bpp; /* TODO: textura SDL2 */ }
static void pc_draw_glyph(int layer, int x, int y, int u, int v, int w, int h, int r, int g, int b) {
    (void)layer; (void)x; (void)y; (void)u; (void)v; (void)w; (void)h; (void)r; (void)g; (void)b;
    glyph_count++;
}
static void pc_glyphs_end(int layer) { (void)layer; }

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
    .file_size = pc_file_size,
    .file_read = pc_file_read,
    .font_upload = pc_font_upload,
    .draw_glyph = pc_draw_glyph,
    .glyphs_end = pc_glyphs_end,
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

int vn_platform_pc_init(const VnPlatformCaps *caps, const char *dir) {
    if (caps) pc_caps = *caps;
    if (dir) snprintf(data_dir, sizeof(data_dir), "%s", dir);
    glyph_count = 0;
    return 0;
}

void vn_platform_pc_shutdown(void) {
}

int vn_platform_pc_glyph_count(void) { return glyph_count; }
