#include "audio.h"
#include "cd.h"
#include "psx_audio.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define AUDIO_ENTRIES   256
#define AMBIENTS        4
#define VOICES          20
#define XA_SAMPLES      4032
#define XA_SECTOR_BYTES 2336
#define SPU_BASE_RATE   44100

typedef struct {
	uint8_t kind, lane, copies, flags;
	uint32_t start, length, aux, reserved;
} AudioEntry;

typedef struct {
	int16_t *samples;
	int count, rate, loop;
	double position;
} Voice;

static AudioEntry entries[AUDIO_ENTRIES];
static int entry_count, music = -1, queued = -1, end_id = -1, end_at = -1;
static int ambient[AMBIENTS] = {-1, -1, -1, -1};
static int music_volume = 255, sfx_volume = 255, levels[AMBIENTS] = {255, 255, 255, 255};
static int cd_depth, loading;
static double music_position;
static int music_base_sector;
static FILE *music_file;
static int cached_sector = -1;
static int16_t sector_samples[XA_SAMPLES];
static int32_t xa_history[4];
static Voice sfx_voices[VOICES], ambient_voices[AMBIENTS];
static SDL_AudioDeviceID device;

static void free_voice(Voice *voice)
{
	free(voice->samples);
	memset(voice, 0, sizeof(*voice));
}

static int load_voice(Voice *voice, int id, int loop)
{
	char path[32];
	uint8_t *encoded;
	int16_t *decoded;
	int lba, bytes, blocks, count;

	if (id < 0 || id >= entry_count || entries[id].kind == 1)
		return -1;
	snprintf(path, sizeof(path), "\\DATA\\S%03d.SPU", id);
	if (cd_find(path, &lba, &bytes) != 0 || bytes <= 0)
		return -1;
	encoded = malloc((size_t)bytes);
	if (!encoded)
		return -1;
	if (cd_read_file(path, encoded, bytes) != bytes) {
		free(encoded);
		return -1;
	}
	blocks = bytes / 16;
	decoded = malloc((size_t)blocks * 28 * sizeof(*decoded));
	if (!decoded) {
		free(encoded);
		return -1;
	}
	{
		int32_t history[2] = {0, 0};
		count = psx_spu_decode(encoded, blocks, decoded, history);
	}
	free(encoded);
	free_voice(voice);
	voice->samples = decoded;
	voice->count = count;
	voice->rate = entries[id].aux ? (int)entries[id].aux : 22050;
	voice->loop = loop;
	return 0;
}

static int16_t xa_sample(int sector, int sample)
{
	uint8_t data[XA_SECTOR_BYTES];
	long offset;
	int16_t right[XA_SAMPLES];

	if (sector != cached_sector) {
		offset = (long)sector * XA_SECTOR_BYTES;
		if (!music_file || fseek(music_file, offset, SEEK_SET) != 0 ||
		    fread(data, 1, sizeof(data), music_file) != sizeof(data))
			return 0;
		psx_xa_decode_sector(data + 8, 0, 0, sector_samples, right, xa_history);
		cached_sector = sector;
	}
	return sector_samples[sample];
}

static int16_t music_at(double position)
{
	int sector = music_base_sector + (int)(position / XA_SAMPLES) * 16;
	int sample = (int)position % XA_SAMPLES;
	int next_sector = sector;
	int next_sample = sample + 1;
	int a, b;

	if (next_sample == XA_SAMPLES) {
		next_sector += 16;
		next_sample = 0;
	}
	a = xa_sample(sector, sample);
	b = xa_sample(next_sector, next_sample);
	return (int16_t)(a + (b - a) * (position - (int)(position)));
}

static int16_t voice_at(Voice *voice)
{
	int i, next;
	double fraction;
	int value;

	if (!voice->samples || !voice->count)
		return 0;
	i = (int)voice->position;
	if (i >= voice->count) {
		if (!voice->loop) {
			free_voice(voice);
			return 0;
		}
		voice->position = 0;
		i = 0;
	}
	next = i + 1;
	if (next >= voice->count)
		next = voice->loop ? 0 : i;
	fraction = voice->position - i;
	value = voice->samples[i] + (int)((voice->samples[next] - voice->samples[i]) * fraction);
	voice->position += (double)voice->rate / SPU_BASE_RATE;
	return (int16_t)value;
}

static void audio_callback(void *userdata, Uint8 *stream, int length)
{
	int16_t *out = (int16_t *)stream;
	int frames = length / (int)(sizeof(*out) * 2), frame, i;
	(void)userdata;
	for (frame = 0; frame < frames; frame++) {
		int left = 0, right = 0;
		if (music >= 0 && !cd_depth && music_file) {
			const AudioEntry *entry = &entries[music];
			double end = (double)entry->length * XA_SAMPLES;
			int current_sector = music_base_sector + (int)(music_position / XA_SAMPLES) * 16;
			if (end_id >= 0 && current_sector >= end_at) {
				music = end_id;
				music_base_sector = end_at;
				music_position = 0;
				end_id = end_at = -1;
				cached_sector = -1;
				memset(xa_history, 0, sizeof(xa_history));
				entry = &entries[music];
				end = (double)entry->length * XA_SAMPLES;
			}
			if (music_position >= end) {
				if (queued >= 0) {
					music = queued;
					queued = -1;
					music_position = 0;
					music_base_sector = (int)entries[music].start;
					cached_sector = -1;
					memset(xa_history, 0, sizeof(xa_history));
				} else if (entry->flags & 1)
					music_position = 0;
				else
					music = -1;
				if (music >= 0 && (entry->flags & 1)) {
					music_base_sector = (int)entry->start;
					cached_sector = -1;
					memset(xa_history, 0, sizeof(xa_history));
				}
			}
			if (music >= 0) {
				int sample = music_at(music_position);
				left += sample * music_volume / 255;
				right += sample * music_volume / 255;
				music_position += 37800.0 / SPU_BASE_RATE;
			}
		}
		for (i = 0; i < VOICES; i++) {
			int sample = voice_at(&sfx_voices[i]) * sfx_volume / 255;
			left += sample;
			right += sample;
		}
		for (i = 0; i < AMBIENTS; i++) {
			int sample = voice_at(&ambient_voices[i]) * levels[i] / 255;
			left += sample;
			right += sample;
		}
		if (left > 32767)
			left = 32767;
		if (left < -32768)
			left = -32768;
		if (right > 32767)
			right = 32767;
		if (right < -32768)
			right = -32768;
		out[frame * 2] = (int16_t)left;
		out[frame * 2 + 1] = (int16_t)right;
	}
}

int audio_init(void)
{
	SDL_AudioSpec wanted, obtained;
	uint8_t index[6 + AUDIO_ENTRIES * 20];
	int bytes, i;
	if (SDL_InitSubSystem(SDL_INIT_AUDIO) != 0)
		return -1;
	bytes = cd_read_file("\\DATA\\AUDIO.BIN", index, sizeof(index));
	if (bytes >= 6 && memcmp(index, "AIX1", 4) == 0) {
		entry_count = index[4] | (index[5] << 8);
		if (entry_count > AUDIO_ENTRIES)
			entry_count = AUDIO_ENTRIES;
		for (i = 0; i < entry_count; i++) {
			const uint8_t *p = index + 6 + i * 20;
			entries[i].kind = p[0];
			entries[i].lane = p[1];
			entries[i].copies = p[2];
			entries[i].flags = p[3];
			memcpy(&entries[i].start, p + 4, 4);
			memcpy(&entries[i].length, p + 8, 4);
			memcpy(&entries[i].aux, p + 12, 4);
			memcpy(&entries[i].reserved, p + 16, 4);
		}
	}
	{
		int lba, size;
		if (cd_find("\\MUSIC.XA", &lba, &size) == 0) {
			char path[600];
			const char *root = getenv("VN_DATA_DIR");
#ifdef __WII__
			snprintf(path, sizeof(path), "%s/MUSIC.XA", root && *root ? root : "sd:/apps/snoot/data");
#else
			snprintf(path, sizeof(path), "%s/MUSIC.XA", root && *root ? root : ".");
#endif
			music_file = fopen(path, "rb");
		}
	}
	SDL_zero(wanted);
	wanted.freq = SPU_BASE_RATE;
	wanted.format = AUDIO_S16SYS;
	wanted.channels = 2;
	wanted.samples = 1024;
	wanted.callback = audio_callback;
	device = SDL_OpenAudioDevice(NULL, 0, &wanted, &obtained, 0);
	if (!device)
		return -1;
	SDL_PauseAudioDevice(device, 0);
	return 0;
}

void audio_update(void)
{
	loading = 0;
}

void audio_music_play(int id, int fade, int flags)
{
	int sector, k;
	(void)fade;
	if (id < 0 || id >= entry_count)
		return;
	SDL_LockAudioDevice(device);
	if (entries[id].kind == 2 && music >= 0) {
		sector = music_base_sector + (int)(music_position / XA_SAMPLES) * 16;
		for (k = 0; k < 8 && (int)(entries[id].start + (uint32_t)k * entries[id].aux * 16u) < sector; k++)
			;
		end_id = id;
		end_at = (int)(entries[id].start + (uint32_t)k * entries[id].aux * 16u);
		queued = -1;
		SDL_UnlockAudioDevice(device);
		return;
	}
	if (entries[id].kind != 1) {
		SDL_UnlockAudioDevice(device);
		return;
	}
	if (!(flags & 2) || music < 0)
		music_position = 0;
	music = id;
	queued = -1;
	end_id = end_at = -1;
	music_base_sector = (int)entries[id].start;
	cached_sector = -1;
	memset(xa_history, 0, sizeof(xa_history));
	SDL_UnlockAudioDevice(device);
}

void audio_music_queue(int id)
{
	if (id < 0 || id >= entry_count)
		return;
	SDL_LockAudioDevice(device);
	if (music < 0) {
		music = id;
		music_position = 0;
		music_base_sector = (int)entries[id].start;
	} else
		queued = id;
	SDL_UnlockAudioDevice(device);
}

void audio_music_stop(int fade)
{
	(void)fade;
	SDL_LockAudioDevice(device);
	music = queued = -1;
	end_id = end_at = -1;
	SDL_UnlockAudioDevice(device);
}

void audio_ambient_play(int slot, int id, int fade)
{
	(void)fade;
	if (slot < 0 || slot >= AMBIENTS)
		return;
	SDL_LockAudioDevice(device);
	if (load_voice(&ambient_voices[slot], id, 1) == 0)
		ambient[slot] = id;
	SDL_UnlockAudioDevice(device);
}

void audio_ambient_stop(int slot, int fade)
{
	(void)fade;
	if (slot < 0 || slot >= AMBIENTS)
		return;
	SDL_LockAudioDevice(device);
	free_voice(&ambient_voices[slot]);
	ambient[slot] = -1;
	SDL_UnlockAudioDevice(device);
}

void audio_sfx_play(int id)
{
	static int next_voice;
	SDL_LockAudioDevice(device);
	load_voice(&sfx_voices[next_voice], id, 0);
	next_voice = (next_voice + 1) % VOICES;
	SDL_UnlockAudioDevice(device);
}

void audio_sfx_stop(void)
{
	int i;
	SDL_LockAudioDevice(device);
	for (i = 0; i < VOICES; i++)
		free_voice(&sfx_voices[i]);
	SDL_UnlockAudioDevice(device);
}

void audio_sfx_stop_fade(int time)
{
	(void)time;
	audio_sfx_stop();
}

void audio_volume(int channel, int volume, int time)
{
	(void)time;
	if (channel == AUDIO_CH_MUSIC)
		music_volume = volume;
	else if (channel == AUDIO_CH_SFX)
		sfx_volume = volume;
	else if (channel > 0 && channel <= AMBIENTS)
		levels[channel - 1] = volume;
}

void audio_stop_all(void)
{
	int i;
	audio_music_stop(0);
	audio_sfx_stop();
	for (i = 0; i < AMBIENTS; i++)
		audio_ambient_stop(i, 0);
}

void audio_preload(int id)
{
	(void)id;
}

int audio_loading(void)
{
	return loading;
}

int audio_ambient_missing(int slot, int id)
{
	return slot >= 0 && slot < AMBIENTS && ambient[slot] != id;
}

int audio_sfx_missing(int id)
{
	(void)id;
	return 0;
}

void audio_set_levels(int music_level, int effects_level)
{
	music_volume = music_level * 255 / 10;
	sfx_volume = effects_level * 255 / 10;
}

int audio_music_current(void)
{
	return music;
}

int audio_ambient_current(int slot)
{
	return slot >= 0 && slot < AMBIENTS ? ambient[slot] : -1;
}

void audio_cd_begin(void)
{
	cd_depth++;
}

void audio_cd_end(void)
{
	if (cd_depth > 0)
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
