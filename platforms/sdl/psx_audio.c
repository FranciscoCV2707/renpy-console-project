/* Decodificadores de audio de PS1 (SPU-ADPCM y XA-ADPCM) a PCM 16 bits.
 * Algoritmo tomado de psx-spx (nocash), secciones "SPU ADPCM Samples" y
 * "CDROM XA Audio ADPCM Compression": tablas de filtro y formula de predictor. */
#include "psx_audio.h"

/* Tablas de filtro de psx-spx, seccion "Pos/neg Tables":
 *   pos_xa_adpcm_table[0..4] = (0, +60, +115, +98, +122)
 *   neg_xa_adpcm_table[0..4] = (0, 0, -52, -55, -60) */
static const int psx_filter_pos[5] = { 0, 60, 115, 98, 122 };
static const int psx_filter_neg[5] = { 0, 0, -52, -55, -60 };

static int clamp16(int v)
{
    if (v > 32767)
        return 32767;
    if (v < -32768)
        return -32768;
    return v;
}

int psx_spu_decode(const uint8_t *adpcm, int blocks, int16_t *out, int32_t hist[2])
{
    int32_t old = 0, older = 0;
    int samples = 0;
    int b;

    if (adpcm == 0 || out == 0 || blocks <= 0)
        return 0;
    if (hist != 0) {
        old = hist[0];
        older = hist[1];
    }

    for (b = 0; b < blocks; b++) {
        const uint8_t *blk = adpcm + b * 16;
        int shift_val = blk[0] & 0x0F;
        int shift;
        int filter = blk[0] >> 4;
        int f0, f1;
        int i;

        if (shift_val >= 13)
            shift = 9;
        else
            shift = 12 - shift_val;
        if (filter > 4)
            filter = 4;
        f0 = psx_filter_pos[filter];
        f1 = psx_filter_neg[filter];

        for (i = 0; i < 28; i++) {
            int byte = blk[2 + i / 2];
            int nibble = (i & 1) ? (byte >> 4) & 0x0F : byte & 0x0F;
            int t = (nibble >= 8) ? (nibble - 16) : nibble;
            int s = (t << shift) + (old * f0 + older * f1 + 32) / 64;

            s = clamp16(s);
            out[samples++] = (int16_t)s;
            older = old;
            old = s;
        }
    }

    if (hist != 0) {
        hist[0] = old;
        hist[1] = older;
    }
    return samples;
}

static void xa_decode_28(const uint8_t *src, int blk, int nibble, int bits8,
                         int32_t *old, int32_t *older,
                         int16_t *dst, int *count)
{
    int header;
    int shift_val;
    int shift;
    int filter;
    int f0, f1;
    int j;

    if (bits8) {
        header = src[4 + blk];
    } else {
        header = src[4 + blk * 2 + nibble];
    }
    shift_val = header & 0x0F;
    if (shift_val >= 13)
        shift = 9;
    else
        shift = 12 - shift_val;
    filter = (header & 0x30) >> 4;
    if (filter > 4)
        filter = 4;
    f0 = psx_filter_pos[filter];
    f1 = psx_filter_neg[filter];

    for (j = 0; j < 28; j++) {
        int t;
        int s;
        int byte = src[16 + blk + j * 4];

        if (bits8) {
            t = (signed char)byte;
        } else {
            int n = (byte >> (nibble * 4)) & 0x0F;
            t = (n >= 8) ? (n - 16) : n;
        }
        s = (t << shift) + ((*old) * f0 + (*older) * f1 + 32) / 64;
        s = clamp16(s);
        dst[(*count)++] = (int16_t)s;
        *older = *old;
        *old = s;
    }
}

int psx_xa_decode_sector(const uint8_t *data, int stereo, int bits8, int16_t *left,
                          int16_t *right, int32_t hist[4])
{
    int32_t oldL = 0, olderL = 0;
    int32_t oldR = 0, olderR = 0;
    int countL = 0;
    int countR = 0;
    const uint8_t *src;
    int i;

    if (data == 0 || left == 0 || right == 0)
        return 0;
    if (hist != 0) {
        oldL = hist[0];
        olderL = hist[1];
        oldR = hist[2];
        olderR = hist[3];
    }

    src = data;
    for (i = 0; i < 0x12; i++) {
        int blk;
        if (bits8) {
            if (stereo) {
                for (blk = 0; blk < 2; blk++) {
                    xa_decode_28(src, blk, 0, bits8,
                                 &oldL, &olderL, left, &countL);
                }
                for (blk = 2; blk < 4; blk++) {
                    xa_decode_28(src, blk, 0, bits8,
                                 &oldR, &olderR, right, &countR);
                }
            } else {
                for (blk = 0; blk < 4; blk++) {
                    xa_decode_28(src, blk, 0, bits8,
                                 &oldL, &olderL, left, &countL);
                }
            }
        } else {
            if (stereo) {
                for (blk = 0; blk < 4; blk++) {
                    xa_decode_28(src, blk, 0, bits8,
                                 &oldL, &olderL, left, &countL);
                    xa_decode_28(src, blk, 1, bits8,
                                 &oldR, &olderR, right, &countR);
                }
            } else {
                for (blk = 0; blk < 4; blk++) {
                    xa_decode_28(src, blk, 0, bits8,
                                 &oldL, &olderL, left, &countL);
                    xa_decode_28(src, blk, 1, bits8,
                                 &oldL, &olderL, left, &countL);
                }
            }
        }
        src += 128;
    }

    if (hist != 0) {
        hist[0] = oldL;
        hist[1] = olderL;
        if (stereo) {
            hist[2] = oldR;
            hist[3] = olderR;
        }
    }
    return stereo ? countR : countL;
}
