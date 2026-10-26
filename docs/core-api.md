# Core API — Contrato 2 (núcleo compartido)

> Basado en `engine/ps1-base/core/` (copia de `vn-engine-ps1`). El núcleo NO conoce ninguna consola.

## Módulos del núcleo (de `engine/ps1-base/core/`)

| Módulo | Archivos | Responsabilidad |
|---|---|---|
| VM | `vm.c`, `vm.h` | Máquina virtual del bytecode (VNB) |
| Escena | `scene.c`, `scene.h` | Gestión de escenas, sprites, capas, ATL |
| Imágenes | `img.c`, `img.h` | Carga y gestión de imágenes (IMG1) |
| Audio | `audio.c`, `audio.h` | Música XA, efectos VAG, ambientes |
| CD | `cd.c`, `cd.h` | Lectura de CD/ISO, carga sin búsquedas |
| Recursos | `res.c`, `res.h` | Carga de recursos desde disco |
| Texto | `text.c`, `text.h` | Fuente, máquina de escribir, paginación |
| Guardado | `save.c`, `save.h` | Memory card, ranuras, checksum |
| Entrada | `input.c`, `input.h` | Botones, cruceta |
| LZ4 | `lz4.c`, `lz4.h` | Descompresión LZ4 |
| Video | `video.c`, `video.h`, `video_clip.c`, `str.c`, `str.h` | Video STR (MDEC), animaciones por cuadros |
| Capítulos | `chapter.c`, `chapter.h` | Carga de capítulos, heap |
| Límites | `vn_limits.h` | Topes de memoria (VNB 96 KiB, texto 96 KiB) |
| OpCodes | `opcodes.h` | Definición de opcodes VNB |

## Interfaz pública (a extraer)

El núcleo expone (ver `engine/core/vn_core.h`):

```c
VnContext *vn_init(const VnPlatformOps *ops, const VnConfig *cfg);
int        vn_load_scene(VnContext *ctx, const char *scene_id);
int        vn_step(VnContext *ctx);
void       vn_shutdown(VnContext *ctx);
void       vn_log(VnContext *ctx, const char *fmt, ...);
```

## Hooks que el backend implementa (`VnPlatformOps`)

- Gráficos: `clear`, `draw_sprite`, `present`
- Audio: `play_music`, `play_sfx`
- Entrada: `poll_input`
- Almacenamiento: `save`, `load`
- Debug: `log`
- Tiempo: `get_time_ms`, `sleep_ms`

## Tareas de extracción (Fase 1)

1. Copiar `engine/ps1-base/core/` a `engine/core/`.
2. Reemplazar llamadas directas a hardware PS1 por callbacks `VnPlatformOps`.
3. Eliminar dependencias de PSn00bSDK del núcleo (mover a backend).
4. Compilar el núcleo para PC (SDL2) y probar.
5. Documentar cada función pública en este archivo.

## Notas

- El núcleo original usa C99 y es compatible con PSn00bSDK.
- Los límites de memoria (`vn_limits.h`) deben ser configurables por plataforma.
- El bytecode VNB (v1/v2) se define en `engine/ps1-base/docs/bytecode.md`.
- El compilador y simulador viven en `engine/ps1-base/vncompiler/`.
