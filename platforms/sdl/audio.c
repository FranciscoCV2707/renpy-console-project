#include "audio.h"
#include "cd.h"
#include <SDL2/SDL.h>
#include <string.h>

#define AMBIENTS 4
static int music = -1, ambient[AMBIENTS] = {-1, -1, -1, -1}, music_volume = 255, sfx_volume = 255,
           levels[AMBIENTS] = {255, 255, 255, 255};
static int queue_id = -1, cd_depth, loading;
int audio_init(void)
{
	return SDL_InitSubSystem(SDL_INIT_AUDIO) == 0 ? 0 : -1;
}
void audio_update(void)
{
	loading = 0;
}
void audio_music_play(int id, int fade, int flags)
{
	(void)fade;
	(void)flags;
	music = id; /* TODO(T-403): mezclar la decodificacion PSX de psx_audio.h con el dispositivo SDL. */
}
void audio_music_queue(int id)
{
	queue_id = id;
}
void audio_music_stop(int fade)
{
	(void)fade;
	music = -1;
	queue_id = -1;
}
void audio_ambient_play(int s, int id, int fade)
{
	if (s >= 0 && s < AMBIENTS) {
		ambient[s] = id;
		(void)fade;
	}
}
void audio_ambient_stop(int s, int fade)
{
	(void)fade;
	if (s >= 0 && s < AMBIENTS)
		ambient[s] = -1;
}
void audio_sfx_play(int id)
{
	(void)id;
}
void audio_sfx_stop(void)
{
}
void audio_sfx_stop_fade(int t)
{
	(void)t;
}
void audio_volume(int c, int v, int t)
{
	(void)t;
	if (c == AUDIO_CH_MUSIC)
		music_volume = v;
	else if (c == AUDIO_CH_SFX)
		sfx_volume = v;
	else if (c > 0 && c <= AMBIENTS)
		levels[c - 1] = v;
}
void audio_stop_all(void)
{
	int i;
	music = -1;
	for (i = 0; i < AMBIENTS; i++)
		ambient[i] = -1;
}
void audio_preload(int id)
{
	(void)id;
}
int audio_loading(void)
{
	return loading;
}
int audio_ambient_missing(int s, int id)
{
	return s >= 0 && s < AMBIENTS && ambient[s] != id;
}
int audio_sfx_missing(int id)
{
	(void)id;
	return 0;
}
void audio_set_levels(int m, int s)
{
	music_volume = m;
	sfx_volume = s;
}
int audio_music_current(void)
{
	return music;
}
int audio_ambient_current(int s)
{
	return s >= 0 && s < AMBIENTS ? ambient[s] : -1;
}
void audio_cd_begin(void)
{
	cd_depth++;
}
void audio_cd_end(void)
{
	if (cd_depth)
		cd_depth--;
}
void audio_batch_begin(void)
{
	audio_cd_begin();
}
void audio_batch_end(void)
{
	audio_cd_end();
}
int audio_cd_paused(void)
{
	return cd_depth > 0 || music < 0;
}
void audio_video_begin(void)
{
	audio_cd_begin();
}
void audio_video_end(int frames)
{
	(void)frames;
	audio_cd_end();
}
