#ifndef PSX_AUDIO_H
#define PSX_AUDIO_H

#include <stdint.h>

/* Decodifica `blocks` bloques SPU-ADPCM de 16 bytes; hist guarda las dos
 * ultimas muestras entre llamadas. Devuelve la cantidad de muestras PCM. */
int psx_spu_decode(const uint8_t *adpcm, int blocks, int16_t *out, int32_t hist[2]);

/* Decodifica un sector XA (los 2304 bytes de datos tras la subcabecera) de un
 * carril; devuelve muestras por canal. hist[4] guarda old/older por canal. */
int psx_xa_decode_sector(const uint8_t *data, int stereo, int bits8, int16_t *left,
                          int16_t *right, int32_t hist[4]);

#endif
