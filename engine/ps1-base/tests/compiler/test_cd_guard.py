"""Execute the production CD directory walker (PAKO-9) without CD hardware.

The old Wani disc searched \\DATA\\FILES.BIN with CdSearchFile: PSn00bSDK caches the
whole directory record with malloc and does not check NULL, so the 48 KB DATA exhausted
the heap and CD DMA overwrote RAM from 0x80000000. The walker in core/cd.c streams the
directory sector by sector with its own buffer, so this test drives it against a
synthetic disc (root file + a 25-sector DATA directory) and poisons malloc: if the
walker ever touched the heap, the run would abort.
"""
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


def test_cd_search_walks_directories_without_heap(tmp_path):
    root = Path(__file__).resolve().parents[2]
    source = (root / "core/cd.c").read_text(encoding="utf-8")
    code = """
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define MAX_FILES 1100
#define ENTRY_BYTES 20
static uint8_t table[6 + MAX_FILES*ENTRY_BYTES + 2048]; /* el mismo borrador de core/cd.c */

/* disco sintetico en memoria: cd_read_sectors sirve sus sectores en lugar del hardware */
#define DISC_SECTORS 700
static uint8_t disc[DISC_SECTORS][2048];
static int cd_read_sectors(int lba, int sectors, void *buf)
{
    while (sectors--) {
        if (lba < 0 || lba >= DISC_SECTORS)
            return -1;
        memcpy(buf, disc[lba++], 2048);
    }
    return 0;
}

/* veneno con puerta: el arranque de Windows usa el heap el solo, asi que solo aborta
 * mientras heap_forbidden este en 1 (la busqueda nunca debe tocar el heap; el crash de
 * PAKO-2 venia de un malloc sin revisar NULL). Los #define de abajo reescriben toda
 * llamada del buscador extraido hacia el veneno. */
static int heap_forbidden;
void poison_alloc(const char *what) { (void)what; assert(!heap_forbidden && "iso_search toco el heap"); }
#define malloc(n) (poison_alloc("malloc"), (void *)0)
#define calloc(n, m) (poison_alloc("calloc"), (void *)0)
#define realloc(p, n) (poison_alloc("realloc"), (void *)0)
#define free(p) poison_alloc("free")
"""
    for marker in ["static uint32_t rd32(", "static int iso_id_equal(", "static int iso_dir_find(",
                   "static int iso_search("]:
        code += function(source, marker) + "\n"
    code += """
#undef malloc
#undef calloc
#undef realloc
#undef free

/* --- construccion del disco sintetico (ISO9660) --- */
static void put32(uint8_t *p, uint32_t v)
{
    p[0] = v; p[1] = v >> 8; p[2] = v >> 16; p[3] = v >> 24;
}

static void dir_add(int *sec, int *pos, const char *id, int id_len, int flags, int lba, int size)
{
    int len = 33 + id_len + !(id_len & 1);
    uint8_t *p;

    if (*pos + len > 2048) { /* el registro no cabe: relleno el sector y salto al siguiente */
        memset(disc[*sec] + *pos, 0, 2048 - *pos);
        (*sec)++;
        *pos = 0;
    }
    p = disc[*sec] + *pos;
    p[0] = len;
    p[1] = 0;
    put32(p + 2, lba);
    put32(p + 10, size);
    p[25] = flags;
    put32(p + 28, 1);
    p[32] = id_len;
    memcpy(p + 33, id, id_len);
    *pos += len;
}

#define ROOT_LBA 20
#define DATA_LBA 40      /* el DATA de varios sectores, como el del disco antiguo de Wani */
#define FILES_LBA 300
#define GAME_LBA 301
#define DATA_FILES_LBA 302

static void build_disc(void)
{
    static const uint8_t dot[1] = {0}, dotdot[1] = {1};
    int sec, pos, i, data_len;

    memset(disc, 0, sizeof(disc));
    /* descriptor de volumen (sector 16) con el registro del directorio raiz en 156 */
    disc[16][0] = 1;
    memcpy(disc[16] + 1, "CD001", 5);
    disc[16][156] = 34;
    disc[16][157] = 0;
    put32(disc[16] + 158, ROOT_LBA);
    put32(disc[16] + 166, 2048);
    disc[16][156 + 25] = 2;
    disc[16][156 + 32] = 1;
    memcpy(disc[16] + 156 + 33, dot, 1);

    /* raiz: ".", "..", "FILES.BIN;1" (disco actual) y "DATA" */
    sec = ROOT_LBA;
    pos = 0;
    dir_add(&sec, &pos, (const char *)dot, 1, 2, ROOT_LBA, 2048);
    dir_add(&sec, &pos, (const char *)dotdot, 1, 2, ROOT_LBA, 2048);
    dir_add(&sec, &pos, "FILES.BIN;1", 11, 0, FILES_LBA, 1234);
    dir_add(&sec, &pos, "DATA", 4, 2, DATA_LBA, 0);
    put32(disc[ROOT_LBA] + 10, pos); /* "." trae el tamano del directorio */

    /* DATA de 25 sectores (~51 KB de registros): antes malloc(49152) devolvia NULL */
    sec = DATA_LBA;
    pos = 0;
    dir_add(&sec, &pos, (const char *)dot, 1, 2, DATA_LBA, 0);
    dir_add(&sec, &pos, (const char *)dotdot, 1, 2, ROOT_LBA, 2048);
    for (i = 0; i < 1100; i++) {
        char id[16];
        sprintf(id, "D%04d.BIN;1", i);
        dir_add(&sec, &pos, id, 11, 0, 400 + i, 2048);
    }
    dir_add(&sec, &pos, "FILES.BIN;1", 11, 0, DATA_FILES_LBA, 5678);
    dir_add(&sec, &pos, "GAME.BIN;1", 10, 0, GAME_LBA, 9012);
    data_len = (sec - DATA_LBA) * 2048 + pos;
    put32(disc[DATA_LBA] + 10, data_len);
}

int main(void)
{
    int lba, size;

    build_disc();

    heap_forbidden = 1; /* desde aqui, cualquier malloc del buscador aborta la prueba */

    /* disco actual: FILES.BIN en la raiz (con y sin barra inicial) */
    assert(iso_search("\\\\FILES.BIN", &lba, &size) == 0);
    assert(lba == FILES_LBA && size == 1234);
    assert(iso_search("FILES.BIN", &lba, &size) == 0);
    assert(lba == FILES_LBA && size == 1234);

    /* la ruta del disco antiguo de Wani, a traves del DATA enorme: hoy funciona sin heap */
    assert(iso_search("\\\\DATA\\\\FILES.BIN", &lba, &size) == 0);
    assert(lba == DATA_FILES_LBA && size == 5678);
    assert(iso_search("\\\\DATA\\\\GAME.BIN", &lba, &size) == 0);
    assert(lba == GAME_LBA && size == 9012);

    /* registros en sectores avanzados y en el ultimo sector con registros del DATA */
    assert(iso_search("\\\\DATA\\\\D0001.BIN", &lba, &size) == 0);
    assert(lba == 401 && size == 2048);
    assert(iso_search("\\\\DATA\\\\D1099.BIN", &lba, &size) == 0);
    assert(lba == 400 + 1099 && size == 2048);

    /* lo que no esta falla visible (-1): archivos, directorios y componentes ausentes */
    assert(iso_search("\\\\AUSENTE.BIN", &lba, &size) == -1);
    assert(iso_search("\\\\DATA\\\\AUSENTE.BIN", &lba, &size) == -1);
    assert(iso_search("\\\\NODIR\\\\X.BIN", &lba, &size) == -1);
    assert(iso_search("\\\\DATA", &lba, &size) == -1); /* es directorio, se pide archivo */
    assert(iso_search("\\\\DATA\\\\", &lba, &size) == -1);

    heap_forbidden = 0;
    return 0;
}
"""
    path, exe = tmp_path / "cd_guard.c", tmp_path / "cd_guard.exe"
    path.write_text(code, encoding="utf-8")
    gcc = Path(r"C:\msys64\ucrt64\bin\gcc.exe")
    env = {**os.environ, "PATH": str(gcc.parent) + os.pathsep + os.environ["PATH"]}
    subprocess.run([str(gcc), "-std=c99", "-Wall", "-Wextra", "-Werror", str(path), "-o", str(exe)], check=True, env=env)
    subprocess.run([str(exe)], check=True, env=env)


def test_engine_sources_never_call_cd_search_file():
    """The engine must not reach CdSearchFile: its malloc of the whole directory record is unchecked."""
    root = Path(__file__).resolve().parents[2]
    for folder in ("core", "app", "modules", "games"):
        for path in (root / folder).rglob("*.c"):
            assert "CdSearchFile(" not in path.read_text(encoding="utf-8"), f"{path} llama CdSearchFile"
