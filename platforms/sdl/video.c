#include "video.h"

#include "sdl_target.h"
#include <stdlib.h>
#include <string.h>

#define COMMANDS 8192
typedef struct {
	int type, layer, x, y, w, h, r, g, b, blend;
	SDL_Texture *texture;
	SDL_Rect src;
	double angle;
	int flip;
} Draw;
static SDL_Window *window;
static SDL_Renderer *renderer;
static SDL_Surface *headless_surface;
static Draw draws[COMMANDS];
static int draw_count, frames, vblanks, clip;
static uint32_t started;
static SDL_Texture *snapshot, *font;
static uint8_t *last_pixels;
static int shot_requested, shot_number;
static int output_w = SCREEN_W, output_h = SCREEN_H;
void sdl_snapshot_to(const char *path);

/* Mapeo de coordenadas del motor (320x240) a la ventana de la consola. */
static void map_pos(int *mx, int *my, int x, int y)
{
#if SDL_TARGET_MANUAL_SCALE
	*mx = SDL_TARGET_VIEW_X + x * SDL_TARGET_VIEW_W / SCREEN_W;
	*my = SDL_TARGET_VIEW_Y + y * SDL_TARGET_VIEW_H / SCREEN_H;
#else
	*mx = x;
	*my = y;
#endif
}

static void map_rect(SDL_Rect *r, int x, int y, int w, int h)
{
	int mx, my, ex, ey;
	map_pos(&mx, &my, x, y);
	map_pos(&ex, &ey, x + w, y + h);
	r->x = mx;
	r->y = my;
	r->w = ex - mx;
	r->h = ey - my;
}

static void add(Draw d)
{
	if (draw_count < COMMANDS)
		draws[draw_count++] = d;
}
static void capture_pixels(void)
{
	uint8_t *raw;
	int x, y;
	if (!renderer || !last_pixels)
		return;
	SDL_GetRendererOutputSize(renderer, &output_w, &output_h);
	raw = malloc((size_t)output_w * output_h * 4);
	if (!raw)
		return;
	if (SDL_RenderReadPixels(renderer, NULL, SDL_PIXELFORMAT_RGBA32, raw, output_w * 4) == 0)
		for (y = 0; y < SCREEN_H; y++)
			for (x = 0; x < SCREEN_W; x++) {
				int sx = x * output_w / SCREEN_W, sy = y * output_h / SCREEN_H;
				uint8_t *pixel = last_pixels + ((size_t)y * SCREEN_W + x) * 4;
				memcpy(pixel, raw + ((size_t)sy * output_w + sx) * 4, 4);
				pixel[3] = 255;
			}
	free(raw);
}
static void rect(int layer, int x, int y, int w, int h, int r, int g, int b, int blend)
{
	Draw d = {0};
	d.type = 1;
	d.layer = layer;
	d.x = x;
	d.y = y;
	d.w = w;
	d.h = h;
	d.r = r;
	d.g = g;
	d.b = b;
	d.blend = blend;
	add(d);
}
void video_init(void)
{
	SDL_TARGET_CALL_SET_MAIN_READY();
	if (SDL_InitSubSystem(SDL_TARGET_INIT_FLAGS) != 0)
		return;
	if (getenv("SDL_VIDEODRIVER") && strcmp(getenv("SDL_VIDEODRIVER"), "dummy") == 0) {
		headless_surface = SDL_CreateRGBSurfaceWithFormat(0, SCREEN_W, SCREEN_H, 32, SDL_PIXELFORMAT_RGBA32);
		if (headless_surface)
			renderer = SDL_CreateSoftwareRenderer(headless_surface);
	} else {
		window = SDL_CreateWindow("Snoot Game", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, SDL_TARGET_WINDOW_W,
		                          SDL_TARGET_WINDOW_H, SDL_WINDOW_SHOWN);
		if (window)
			renderer = SDL_CreateRenderer(window, -1, SDL_TARGET_RENDERER_FLAGS);
		if (!renderer && window)
			renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_SOFTWARE);
	}
	if (renderer) {
#if SDL_TARGET_USE_LOGICAL_SIZE
		SDL_RenderSetLogicalSize(renderer, SCREEN_W, SCREEN_H);
#endif
		SDL_GetRendererOutputSize(renderer, &output_w, &output_h);
	}
	last_pixels = malloc(SCREEN_W * SCREEN_H * 4);
	started = SDL_GetTicks();
}
void video_rect(int l, int x, int y, int w, int h, int r, int g, int b, int blend)
{
	rect(l, x, y, w, h, r, g, b, blend);
}
void video_triangle_down(int l, int x, int y, int w, int h, int r, int g, int b)
{
	Draw d = {0};
	d.type = 2;
	d.layer = l;
	d.x = x;
	d.y = y;
	d.w = w;
	d.h = h;
	d.r = r;
	d.g = g;
	d.b = b;
	add(d);
}
void video_snapshot(int x, int y)
{
	(void)x;
	(void)y;
	if (!renderer || !last_pixels)
		return;
	capture_pixels();
	if (!snapshot)
		snapshot =
		    SDL_CreateTexture(renderer, SDL_PIXELFORMAT_RGBA32, SDL_TEXTUREACCESS_STATIC, SCREEN_W, SCREEN_H);
	SDL_UpdateTexture(snapshot, NULL, last_pixels, SCREEN_W * 4);
}
void video_snapshot_draw(int l, int x, int y, int blend, int bright, int band_y, int band_bright)
{
	(void)x;
	(void)y;
	(void)band_y;
	(void)band_bright;
	if (snapshot) {
		Draw d = {0};
		d.type = 3;
		d.layer = l;
		d.x = 0;
		d.y = VIEW_Y;
		d.w = SCREEN_W;
		d.h = VIEW_H;
		d.r = bright;
		d.g = bright;
		d.b = bright;
		d.blend = blend;
		d.texture = snapshot;
		d.src = (SDL_Rect){0, VIEW_Y, SCREEN_W, VIEW_H};
		add(d);
	}
}
void video_clip_scene(void)
{
	clip = 1;
}
void video_unclip(void)
{
	clip = 0;
}
void video_flip(void)
{
	int layer, i;
	if (getenv("VN_FAST") && getenv("SDL_VIDEODRIVER") && strcmp(getenv("SDL_VIDEODRIVER"), "dummy") == 0 &&
	    (!getenv("VN_SHOT_DIR") || !shot_requested)) {
		draw_count = 0;
		frames++;
		vblanks++;
		return;
	}
	if (renderer) {
		SDL_SetRenderTarget(renderer, NULL);
		SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
		SDL_RenderClear(renderer);
		for (layer = LAYER_BG; layer >= LAYER_DEBUG; layer--) {
			if (clip && layer >= LAYER_SPRITE0) {
				SDL_Rect c;
				map_rect(&c, 0, VIEW_Y, SCREEN_W, VIEW_H);
				SDL_RenderSetClipRect(renderer, &c);
			} else
				SDL_RenderSetClipRect(renderer, NULL);
			for (i = draw_count - 1; i >= 0; i--) {
				Draw *d = &draws[i];
				SDL_Rect dst;
				if (d->layer != layer)
					continue;
				map_rect(&dst, d->x, d->y, d->w, d->h);
				if (d->type == 1) {
					SDL_SetRenderDrawBlendMode(renderer,
					                           d->blend ? SDL_BLENDMODE_BLEND : SDL_BLENDMODE_NONE);
					SDL_SetRenderDrawColor(renderer, d->r, d->g, d->b, d->blend ? 128 : 255);
					SDL_RenderFillRect(renderer, &dst);
				} else if (d->type == 2) {
#if SDL_TARGET_HAS_RENDER_GEOMETRY
					int ax, ay, bx, by, cx, cy;
					SDL_Vertex v[3];
					map_pos(&ax, &ay, d->x, d->y);
					map_pos(&bx, &by, d->x + d->w, d->y);
					map_pos(&cx, &cy, d->x + d->w / 2, d->y + d->h);
					v[0] = (SDL_Vertex){{(float)ax, (float)ay},
					                    {(Uint8)d->r, (Uint8)d->g, (Uint8)d->b, 255},
					                    {0, 0}};
					v[1] = (SDL_Vertex){{(float)bx, (float)by},
					                    {(Uint8)d->r, (Uint8)d->g, (Uint8)d->b, 255},
					                    {0, 0}};
					v[2] = (SDL_Vertex){{(float)cx, (float)cy},
					                    {(Uint8)d->r, (Uint8)d->g, (Uint8)d->b, 255},
					                    {0, 0}};
					SDL_RenderGeometry(renderer, NULL, v, 3, NULL, 0);
#else
					SDL_Rect tr = {d->x, d->y, d->w > 0 ? d->w : 1, d->h > 0 ? d->h : 1};
					SDL_SetRenderDrawColor(renderer, d->r, d->g, d->b, 255);
					SDL_RenderFillRect(renderer, &tr);
#endif
				} else if (d->type == 3) {
					SDL_SetTextureColorMod(d->texture, d->r, d->g, d->b);
					SDL_SetTextureBlendMode(d->texture,
					                        d->blend ? SDL_BLENDMODE_BLEND : SDL_BLENDMODE_NONE);
					SDL_RenderCopy(renderer, d->texture, &d->src, &dst);
				} else if (d->texture) {
					SDL_SetTextureColorMod(d->texture, d->r, d->g, d->b);
					SDL_SetTextureBlendMode(d->texture,
					                        d->blend ? SDL_BLENDMODE_BLEND : SDL_BLENDMODE_BLEND);
					SDL_RenderCopyEx(renderer, d->texture, &d->src, &dst, d->angle, NULL,
					                 d->flip ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
				}
			}
		}
		SDL_RenderSetClipRect(renderer, NULL);
		if (shot_requested) {
			SDL_RenderFlush(renderer);
			capture_pixels();
		}
		SDL_RenderPresent(renderer);
	}
	if (shot_requested) {
		const char *dir = getenv("VN_SHOT_DIR"), *names = getenv("VN_SHOT_NAMES");
		if (dir && *dir) {
			char p[800], name[128] = "shot";
			int i = 0, j = 0, n = shot_number++;
			if (names) {
				const char *s = names;
				while (n && *s) {
					if (*s == ',')
						n--;
					s++;
				}
				if (*s) {
					while (*s && *s != ',' && j + 1 < (int)sizeof(name))
						name[j++] = *s++;
					name[j] = 0;
				}
			}
			for (i = 0; dir[i] && i < 400; i++)
				p[i] = dir[i];
			p[i++] = '/';
			snprintf(p + i, sizeof(p) - (size_t)i, "%s.bmp", name);
			sdl_snapshot_to(p);
		}
		shot_requested = 0;
	}
	draw_count = 0;
	frames++;
	vblanks++;
}
int video_frames(void)
{
	return frames;
}
void video_wait_vblank(void)
{
	if (getenv("VN_FAST"))
		return;
	uint32_t due = started + (uint32_t)((frames + 1) * 1000 / 60), now = SDL_GetTicks();
	if (due > now)
		SDL_Delay(due - now);
	vblanks++;
}
int video_vblank_count(void)
{
	return vblanks;
}

void sdl_draw_texture(SDL_Texture *t, int layer, int x, int y, int w, int h, int sx, int sy, int sw, int sh, int r,
                      int g, int b, int blend, int flip, int zoom, int angle)
{
	Draw d = {0};
	d.type = 4;
	d.layer = layer;
	d.x = x;
	d.y = y;
	d.w = w * zoom / 64;
	d.h = h * zoom / 64;
	d.texture = t;
	d.src = (SDL_Rect){sx, sy, sw, sh};
	/* SDL_SetTextureColorMod toma Uint8: el tinte normal de la PS1 (128) duplicado da 256, que se volvia 0 (negro) */
	d.r = r > 255 ? 255 : r;
	d.g = g > 255 ? 255 : g;
	d.b = b > 255 ? 255 : b;
	d.blend = blend;
	d.flip = flip;
	d.angle = (double)angle * 360.0 / 4096.0;
	add(d);
}
SDL_Renderer *sdl_renderer(void)
{
	return renderer;
}
SDL_Texture *sdl_font_texture(void)
{
	return font;
}
void sdl_set_font(SDL_Texture *t)
{
	font = t;
}
static void put16(FILE *f, unsigned v)
{
	fputc((int)(v & 255), f);
	fputc((int)((v >> 8) & 255), f);
}
static void put32(FILE *f, unsigned v)
{
	put16(f, v & 65535);
	put16(f, v >> 16);
}
void sdl_snapshot_to(const char *path)
{
	FILE *f;
	int y, x;
	if (!last_pixels || !path || !*path)
		return;
	f = fopen(path, "wb");
	if (!f)
		return;
	fputc('B', f);
	fputc('M', f);
	put32(f, 54 + SCREEN_W * SCREEN_H * 3);
	put32(f, 0);
	put32(f, 54);
	put32(f, 40);
	put32(f, SCREEN_W);
	put32(f, SCREEN_H);
	put16(f, 1);
	put16(f, 24);
	put32(f, 0);
	put32(f, SCREEN_W * SCREEN_H * 3);
	put32(f, 2835);
	put32(f, 2835);
	put32(f, 0);
	put32(f, 0);
	for (y = SCREEN_H - 1; y >= 0; y--)
		for (x = 0; x < SCREEN_W; x++) {
			const uint8_t *p = last_pixels + ((size_t)y * SCREEN_W + x) * 4;
			fputc(p[2], f);
			fputc(p[1], f);
			fputc(p[0], f);
		}
	fclose(f);
}
void sdl_shot_request(void)
{
	shot_requested = 1;
}