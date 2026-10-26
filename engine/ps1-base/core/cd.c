#include <stdio.h>
#include <string.h>
#include <psxapi.h>
#include <psxcd.h>
#include <psxgpu.h>
#include "audio.h"
#include "cd.h"

/* para la prueba en emulador: lecturas que detienen el juego (cantidad, cuadros y sectores) y esperas a la precarga */
volatile uint32_t cd_sync_count, cd_sync_vblanks, cd_sync_sectors, cd_wait_vblanks;

/* Tabla de sectores (FILES.BIN, la arma tools/engine/build_game.py): nombre de 12 bytes, sector y tamano, ordenada
 * por nombre; evita rebuscar en el disco en cada carga. Antes de cargarla (y cuando el disco no trae FTB1) sus
 * primeros bytes sirven de borrador para leer sectores del directorio en iso_search: nunca se usan a la vez. */
#define MAX_FILES 1100
#define ENTRY_BYTES 20

static uint8_t table[6 + MAX_FILES * ENTRY_BYTES + 2048] __attribute__((aligned(4)));
static int table_count, table_valid;

static uint32_t rd32(const uint8_t *p)
{
	return p[0] | (p[1] << 8) | (p[2] << 16) | ((uint32_t)p[3] << 24);
}

/* Comparacion de un identificador de registro ("FILES.BIN;1", "DATA") con un componente de ruta sin
 * version: el sufijo ";n" del identificador se ignora. */
static int iso_id_equal(const uint8_t *id, int id_len, const char *name, int name_len)
{
	int i;

	for (i = 0; i < id_len; i++) {
		if (id[i] == ';' && i >= name_len)
			break;
		if (i >= name_len || id[i] != (uint8_t)name[i])
			return 0;
	}
	return i >= name_len;
}

/* Recorre el directorio de dir_lba sector por sector buscando name. El registro "." del primer sector trae
 * el tamano del directorio, asi que cualquiera (el DATA de 48 KB del disco antiguo de Wani incluido) se
 * revisa con un solo sector de borrador y sin tocar el heap. want_dir busca un subdirectorio en vez de un
 * archivo. 0 con la posicion y el tamano; -1 si no esta o falla la lectura. */
static int iso_dir_find(uint8_t *buf, int dir_lba, const char *name, int name_len, int want_dir, int *lba, int *size)
{
	int dir_len, sectors, s;

	if (cd_read_sectors(dir_lba, 1, buf) != 0)
		return -1;
	dir_len = (int)rd32(buf + 10);        /* "." = el directorio mismo */
	sectors = (dir_len + 2047) / 2048;
	if (dir_len <= 0 || sectors > 512) {  /* registro corrupto: no escanear gigabytes */
		printf("cd: registro de directorio invalido (%d bytes)\n", dir_len);
		return -1;
	}
	for (s = 0; s < sectors; s++) {
		int pos;

		if (s > 0 && cd_read_sectors(dir_lba + s, 1, buf) != 0)
			return -1;
		for (pos = 0; pos + 34 <= 2048 && buf[pos]; pos += buf[pos]) {
			int len = buf[pos], id_len = buf[pos + 32];

			if (pos + len > 2048 || len < 34)
				break;  /* registro trunco: fin del sector */
			if (((buf[pos + 25] & 2) != 0) == want_dir &&
			    iso_id_equal(buf + pos + 33, id_len, name, name_len)) {
				*lba = (int)rd32(buf + pos + 2);
				*size = (int)rd32(buf + pos + 10);
				return 0;
			}
		}
	}
	return -1;
}

/* Busca una ruta en el sistema ISO9660 del disco (con o sin barra inicial, con subdirectorios): lee la
 * raiz del descriptor de volumen (sector 16) y baja componente por componente. Sustituye a CdSearchFile,
 * que cachea el registro de cada directorio con malloc y no revisa NULL: en el disco antiguo de Wani el
 * DATA de 48 KB agotaba el heap y la DMA del CD sobrescribia la RAM desde 0x80000000. Aqui el heap no se
 * toca; lo que no esta falla con error visible. */
static int iso_search(const char *path, int *lba, int *size)
{
	const char *p = path;
	int dir_lba;

	if (*p == '\\' || *p == '/')
		p++;
	if (cd_read_sectors(16, 1, table) != 0 || memcmp(table + 1, "CD001", 5) != 0)
		return -1;
	dir_lba = (int)rd32(table + 156 + 2);  /* registro del directorio raiz del descriptor */
	for (;;) {
		const char *start = p;
		int comp_len, last;

		while (*p && *p != '\\' && *p != '/')
			p++;
		comp_len = (int)(p - start);
		last = *p == '\0';
		if (comp_len <= 0 || comp_len > 31)
			break;  /* vacio o mas largo que un identificador ISO9660 */
		if (iso_dir_find(table, dir_lba, start, comp_len, !last, lba, size) != 0)
			break;
		if (last)
			return 0;
		dir_lba = *lba;
		p++;
	}
	return -1;
}

static int search_file(const char *path, int *lba, int *size)
{
	if (iso_search(path, lba, size) != 0) {
		printf("cd: no se encuentra %s\n", path);
		return -1;
	}
	return 0;
}

int cd_init(void)
{
	int lba, size;

	table_count = table_valid = 0;
	if (!CdInit())
		return 0;
	/* Bootstrap desde la raiz. search_file recorre los directorios sector por sector con la tabla de
	 * borrador (sin malloc): el heap queda intacto aunque el disco traiga un DATA enorme. */
	if ((search_file("\\FILES.BIN", &lba, &size) == 0 ||
	     search_file("\\DATA\\FILES.BIN", &lba, &size) == 0) &&
	    size >= 6 && size <= 6 + MAX_FILES * ENTRY_BYTES &&
	    cd_read_sectors(lba, (size + 2047) / 2048, table) == 0 && memcmp(table, "FTB1", 4) == 0) {
		int count = table[4] | (table[5] << 8);

		if (count > 0 && count <= MAX_FILES && 6 + count * ENTRY_BYTES <= size) {
			table_count = count;
			table_valid = 1;
		}
	}
	return 1;
}

int cd_find(const char *path, int *lba, int *size)
{
	const char *name = strrchr(path, '\\');
	int lo = 0, hi = table_count - 1;

	name = name ? name + 1 : path;
	while (lo <= hi) {
		int mid = (lo + hi) / 2, cmp;
		const uint8_t *e = table + 6 + mid * ENTRY_BYTES;

		cmp = strncmp(name, (const char *)e, 12);
		if (cmp == 0) {
			*lba = (int)rd32(e + 12);
			*size = (int)rd32(e + 16);
			return 0;
		}
		if (cmp < 0)
			hi = mid - 1;
		else
			lo = mid + 1;
	}
	/* La tabla enumera el disco completo. Un nombre ausente (NOCARD/AUTOTEST, etc.)
	 * no debe disparar otra busqueda en el disco; sin tabla solo arrancan discos sin FTB1. */
	return table_valid ? -1 : search_file(path, lba, size); /* compatibilidad sin FTB1 */
}

/* Lectura en segundo plano (precargas de imagenes y de efectos): una sola a la vez; cualquier otro comando del CD
 * espera a que termine. Cada dueno consulta la suya: si ya no es la que esta en curso, termino. */
static int async_busy, async_owner, owner_result[CD_OWNERS];

void cd_wait(void)
{
	if (async_busy) {
		int t0 = VSync(-1);

		owner_result[async_owner] = CdReadSync(0, 0) < 0 ? -1 : 0;
		async_busy = 0;
		cd_wait_vblanks += VSync(-1) - t0;
	}
}

int cd_busy(void)
{
	if (async_busy && CdReadSync(1, 0) <= 0)
		cd_wait();
	return async_busy;
}

int cd_read_start(int owner, int lba, int sectors, void *buf)
{
	CdlLOC loc;

	cd_wait();
	CdIntToPos(lba, &loc);
	CdControl(CdlSetloc, &loc, 0);
	if (!CdRead(sectors, (uint32_t *)buf, CdlModeSpeed))
		return -1;
	async_busy = 1;
	async_owner = owner;
	return 0;
}

int cd_read_poll(int owner)
{
	if (async_busy && async_owner == owner && cd_busy())
		return 1;
	return owner_result[owner];
}

int cd_read_sectors(int lba, int sectors, void *buf)
{
	CdlLOC loc;
	int ok, t0;

	cd_wait();
	t0 = VSync(-1);
	audio_cd_begin();                /* la musica XA se pausa durante la lectura (D7) */
	CdIntToPos(lba, &loc);
	CdControl(CdlSetloc, &loc, 0);
	ok = CdRead(sectors, (uint32_t *)buf, CdlModeSpeed) && CdReadSync(0, 0) >= 0;
	audio_cd_end();
	cd_sync_count++;
	cd_sync_sectors += sectors;
	cd_sync_vblanks += VSync(-1) - t0;
	return ok ? 0 : -1;
}

int cd_read_file(const char *path, void *buf, int buf_bytes)
{
	int lba, size, sectors;

	if (cd_find(path, &lba, &size) != 0)
		return -1;
	sectors = (size + 2047) / 2048;
	if (sectors * 2048 > buf_bytes) {
		printf("cd: %s no cabe en el buffer\n", path);
		return -1;
	}
	if (cd_read_sectors(lba, sectors, buf) != 0)
		return -1;
	return size;
}
