#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "psx_audio.h"

static int failures;

static void check(int ok, const char *what)
{
    printf("%s %s\n", ok ? "ok  " : "FAIL", what);
    if (!ok)
        failures++;
}

int main(void)
{
    int16_t *out = malloc(1 << 20);
    int32_t hist[2] = { 0, 0 };
    int32_t hist4[4] = { 0, 0, 0, 0 };
    uint8_t block[16];
    int i, n;
    FILE *f;
    unsigned char *buf;
    long sz;

    /* SPU: filtro 0, shift 0 (shift_val=12), todos los nibbles = 1. */
    memset(block, 0, sizeof(block));
    block[0] = (0 << 4) | 12; /* filter 0, shift_val 12 */
    for (i = 2; i < 16; i++)
        block[i] = 0x11; /* nibble 1 en ambas posiciones */
    n = psx_spu_decode(block, 1, out, hist);
    check(n == 28, "SPU devuelve 28 muestras por bloque");
    {
        int ok = 1;
        for (i = 0; i < 28; i++)
            if (out[i] != 1)
                ok = 0;
        check(ok, "SPU filtro 0 produce muestras = 1");
    }

    /* SPU: bandera de fin en byte 1 no altera la decodificacion. */
    memset(block, 0, sizeof(block));
    block[0] = (0 << 4) | 12;
    block[1] = 0x01; /* Loop End */
    for (i = 2; i < 16; i++)
        block[i] = 0x11;
    n = psx_spu_decode(block, 1, out, hist);
    check(n == 28, "SPU con flag de fin devuelve 28 muestras");
    {
        int ok = 1;
        for (i = 0; i < 28; i++)
            if (out[i] != 1)
                ok = 0;
        check(ok, "SPU flag de fin no cambia las muestras");
    }

    /* SPU: filtro 1, primeras muestras crecientes. */
    memset(block, 0, sizeof(block));
    block[0] = (1 << 4) | 12;
    for (i = 2; i < 16; i++)
        block[i] = 0x11;
    hist[0] = 0;
    hist[1] = 0;
    n = psx_spu_decode(block, 1, out, hist);
    check(n == 28, "SPU filtro 1 devuelve 28 muestras");
    check(out[0] == 1, "SPU filtro 1 primera muestra = 1");
    check(out[1] == 2, "SPU filtro 1 segunda muestra = 2");

    /* SPU: archivo real. */
    f = fopen("E:/Dev/snoot-ps1/build/data/SFX/S000.SPU", "rb");
    check(f != NULL, "se abre S000.SPU");
    if (f) {
        fseek(f, 0, SEEK_END);
        sz = ftell(f);
        fseek(f, 0, SEEK_SET);
        buf = malloc((size_t)sz);
        fread(buf, 1, (size_t)sz, f);
        fclose(f);
        n = psx_spu_decode(buf, (int)(sz / 16), out, hist);
        check(n == (int)(sz / 16) * 28, "SPU real: cantidad de muestras esperada");
        {
            int maxv = 0, nonzero = 0;
            for (i = 0; i < n; i++) {
                int a = out[i] < 0 ? -out[i] : out[i];
                if (a > maxv)
                    maxv = a;
                if (out[i] != 0)
                    nonzero = 1;
            }
            check(nonzero, "SPU real: salida no es silencio");
            check(maxv < 32767, "SPU real: sin saturacion");
            printf("     SPU real: bloques=%ld muestras=%d maxabs=%d\n", sz / 16, n, maxv);
        }
        free(buf);
    }

    /* XA: primer sector de MUSIC.XA (offset 8 tras subcabecera). */
    f = fopen("E:/Dev/snoot-ps1/build/data/MUSIC.XA", "rb");
    check(f != NULL, "se abre MUSIC.XA");
    if (f) {
        unsigned char sector[2336];
        fread(sector, 1, 2336, f);
        fclose(f);
        n = psx_xa_decode_sector(sector + 8, 0, 0, out, out, hist4);
        check(n == 4032, "XA mono 4 bits devuelve 4032 muestras");
        {
            int maxv = 0, nonzero = 0;
            for (i = 0; i < n; i++) {
                int a = out[i] < 0 ? -out[i] : out[i];
                if (a > maxv)
                    maxv = a;
                if (out[i] != 0)
                    nonzero = 1;
            }
            check(nonzero, "XA real: salida no es silencio");
            check(maxv < 32767, "XA real: sin saturacion");
            printf("     XA real: muestras=%d maxabs=%d\n", n, maxv);
        }
    }

    free(out);
    printf("%s\n", failures ? "FALLO" : "TODO OK");
    return failures ? 1 : 0;
}
