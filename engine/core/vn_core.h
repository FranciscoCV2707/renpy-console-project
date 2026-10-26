/* engine/core/vn_core.h
 * Contrato 2: interfaz del nucleo compartido.
 * El nucleo NO conoce ninguna consola. Los backends implementan VnPlatformOps.
 */
#ifndef VN_CORE_H
#define VN_CORE_H

#include <stddef.h>

#include "vn_platform.h"   /* VnPlatformCaps, VnPlatformOps (Contrato 3) */

/* Contexto opaco del nucleo. */
typedef struct VnContext VnContext;

/* Configuracion de inicio. */
typedef struct VnConfig {
    const VnPlatformCaps *caps;
    const char            *game_id;
    const char            *entry_scene;
} VnConfig;

/* API publica del nucleo. */
VnContext *vn_init(const VnPlatformOps *ops, const VnConfig *cfg);
int        vn_load_scene(VnContext *ctx, const char *scene_id);
int        vn_step(VnContext *ctx);          /* avanza un frame/linea */
void       vn_shutdown(VnContext *ctx);

/* Helpers de log estructurado (Contrato: logs [ENGINE]). */
void vn_log(VnContext *ctx, const char *fmt, ...);

#endif /* VN_CORE_H */
