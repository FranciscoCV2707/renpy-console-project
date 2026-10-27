#include "audio.h"

int audio_init(void)
{
	return 1;
}

void audio_update(void)
{
}

void audio_music_play(int id, int fade, int flags)
{
	(void)id;
	(void)fade;
	(void)flags;
}

void audio_music_queue(int id)
{
	(void)id;
}

void audio_music_stop(int fade)
{
	(void)fade;
}

void audio_ambient_play(int slot, int id, int fade)
{
	(void)slot;
	(void)id;
	(void)fade;
}

void audio_ambient_stop(int slot, int fade)
{
	(void)slot;
	(void)fade;
}

void audio_sfx_play(int id)
{
	(void)id;
}

void audio_sfx_stop(void)
{
}

void audio_sfx_play_pos(int id, int x, int y)
{
	(void)id;
	(void)x;
	(void)y;
}

void audio_sound_pos(int x, int y)
{
	(void)x;
	(void)y;
}

void audio_pause(void)
{
}

void audio_resume(void)
{
}

int audio_music_is_playing(void)
{
	return 0;
}

int audio_sfx_is_playing(void)
{
	return 0;
}

void audio_volumes(int music, int sound)
{
	(void)music;
	(void)sound;
}

void audio_fade_step(void)
{
}

void audio_stop_all(void)
{
}

void audio_sfx_stop_fade(int fade)
{
	(void)fade;
}

void audio_volume(int channel, int volume, int time)
{
	(void)channel;
	(void)volume;
	(void)time;
}

void audio_preload(int id)
{
	(void)id;
}

int audio_loading(void)
{
	return 0;
}

int audio_ambient_missing(int slot, int id)
{
	(void)slot;
	(void)id;
	return 0;
}

int audio_sfx_missing(int id)
{
	(void)id;
	return 0;
}

void audio_set_levels(int music, int sfx)
{
	(void)music;
	(void)sfx;
}

int audio_music_current(void)
{
	return -1;
}

int audio_ambient_current(int slot)
{
	(void)slot;
	return -1;
}

void audio_cd_begin(void)
{
}

void audio_cd_end(void)
{
}

void audio_batch_begin(void)
{
}

void audio_batch_end(void)
{
}

int audio_cd_paused(void)
{
	return 1;
}

void audio_video_begin(void)
{
}

void audio_video_end(int frames)
{
	(void)frames;
}
