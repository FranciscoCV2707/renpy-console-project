/* platforms/pc/backend.h
 * Contrato 3: backend PC (SDL2 o similar) para pruebas rapidas.
 */
#ifndef VN_PLATFORM_PC_H
#define VN_PLATFORM_PC_H

#include "engine/core/vn_core.h"

/* Devuelve las operaciones del backend PC. */
const VnPlatformOps *vn_platform_pc_ops(void);

/* Inicializa/cierra el backend PC. */
int  vn_platform_pc_init(const VnPlatformCaps *caps);
void vn_platform_pc_shutdown(void);

#endif /* VN_PLATFORM_PC_H */
