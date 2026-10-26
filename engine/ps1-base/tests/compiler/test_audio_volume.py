"""Execute the production volume/fade routines without CD/SPU hardware."""
import os
import subprocess
from pathlib import Path


def function(source, marker):
    start = source.index(marker)
    end = source.index("{", start)
    depth = 1
    pos = end + 1
    while depth:
        depth += (source[pos] == "{") - (source[pos] == "}")
        pos += 1
    return source[start:pos]


def test_volume_without_fade_is_visible_to_play_in_the_same_frame(tmp_path):
    root = Path(__file__).resolve().parents[2]
    source = (root / "core/audio.c").read_text(encoding="utf-8")
    code = """
#include <assert.h>
#define VOL_ONE 4096
#define AUDIO_CH_MUSIC 0
#define AUDIO_CH_SFX 5
#define AMBIENT_SLOTS 4
typedef struct {int cur, target, step;} Fade;
static Fade music_script, sfx_script, ambient_script[4];
""" + function(source, "static void fade_set(") + "\n" + function(source, "void audio_volume(") + """
int main(void) {
    music_script.cur = 4096;
    audio_volume(0, 128, 0);
    assert(music_script.cur == 128 * 4096 / 255);
    audio_volume(0, 255, 20);
    assert(music_script.cur == 128 * 4096 / 255);
    assert(music_script.target == 4096 && music_script.step > 0);
    audio_volume(4, 64, 0);
    assert(ambient_script[3].cur == 64 * 4096 / 255);
    audio_volume(5, 255, 0);
    assert(sfx_script.cur == 4096);
    audio_volume(6, 0, 0);
    assert(sfx_script.cur == 4096);
    return 0;
}
"""
    path, exe = tmp_path / "volume.c", tmp_path / "volume.exe"
    path.write_text(code, encoding="utf-8")
    gcc = Path(r"C:\msys64\ucrt64\bin\gcc.exe")
    env = {**os.environ, "PATH": str(gcc.parent) + os.pathsep + os.environ["PATH"]}
    subprocess.run([str(gcc), "-std=c99", "-Wall", "-Wextra", "-Werror", str(path), "-o", str(exe)], check=True, env=env)
    subprocess.run([str(exe)], check=True, env=env)


def test_sfx_stop_fade_updates_spu_voices_and_keys_off_at_zero(tmp_path):
    root = Path(__file__).resolve().parents[2]
    source = (root / "core/audio.c").read_text(encoding="utf-8")
    code = """
#include <assert.h>
#include <stdint.h>
#define VOL_ONE 4096
#define AMBIENT_SLOTS 4
#define SFX_VOICES 20
#define SFX_FIRST_VOICE 4
typedef struct {int cur, target, step;} Fade;
static Fade sfx_script, sfx_stop_fade, ambient_fade[4], ambient_script[4];
static int sfx_stop_pending, ambient_stop[4], sfx_level=10;
static int left[24], right[24], stopped;
#define SPU_CH_VOL_L(i) left[i]
#define SPU_CH_VOL_R(i) right[i]
static void SpuSetKey(int on, int mask) { (void)on; stopped |= mask; }
static void music_update(void) {}
static void bg_update(void) {}
static int ambient_volume(int i) { (void)i; return 0; }
"""
    for marker in ["static void fade_set(", "static int fade_tick(", "static int sfx_volume(",
                   "void audio_sfx_stop(void)", "void audio_sfx_stop_fade(", "void audio_update("]:
        code += function(source, marker) + "\n"
    code += """
int main(void) {
    int before, i;
    sfx_script.cur = sfx_script.target = VOL_ONE;
    sfx_stop_fade.cur = sfx_stop_fade.target = VOL_ONE;
    audio_update();
    before = left[4];
    assert(before > 0);
    audio_sfx_stop_fade(10);
    for (i=0; i<59; i++) {
        audio_update();
        if (sfx_stop_pending) {
            assert(left[4] <= before);
            assert(left[4] == right[23]);
            before = left[4];
        }
    }
    audio_update();
    assert(!sfx_stop_pending);
    assert(stopped == (((1 << 20) - 1) << 4));
    audio_sfx_stop_fade(0);
    assert(sfx_stop_fade.cur == VOL_ONE);
    return 0;
}
"""
    path, exe = tmp_path / "sfx.c", tmp_path / "sfx.exe"
    path.write_text(code, encoding="utf-8")
    gcc = Path(r"C:\msys64\ucrt64\bin\gcc.exe")
    env = {**os.environ, "PATH": str(gcc.parent) + os.pathsep + os.environ["PATH"]}
    subprocess.run([str(gcc), "-std=c99", "-Wall", "-Wextra", "-Werror", str(path), "-o", str(exe)], check=True, env=env)
    subprocess.run([str(exe)], check=True, env=env)
