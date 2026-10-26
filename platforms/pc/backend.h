/* platforms/pc/backend.h
 * Contrato C2: backend PC para pruebas en host. Sin ventana todavia (SDL2 pendiente): lee los archivos de una
 * carpeta y registra lo que se dibuja.
 */
#ifndef VN_PLATFORM_PC_H
#define VN_PLATFORM_PC_H

#include "vn_platform.h"

/* Devuelve las operaciones del backend PC. */
const VnPlatformOps *vn_platform_pc_ops(void);

/* Inicializa/cierra el backend PC. `data_dir` es la carpeta con los archivos del disco (C00.VNB, FONT.BIN...). */
int  vn_platform_pc_init(const VnPlatformCaps *caps, const char *data_dir);
void vn_platform_pc_shutdown(void);

/* Glifos dibujados desde el inicio (para pruebas). */
int vn_platform_pc_glyph_count(void);

#endif /* VN_PLATFORM_PC_H */
