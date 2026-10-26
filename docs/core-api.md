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

## Hooks que el backend implementa (`VnPlatformOps`, en `engine/core/vn_platform.h`)

El backend activo se fija con `vn_platform_set(ops)` al arrancar; el núcleo lo usa por `vn_ops`.

- Archivos: `file_size(name)`, `file_read(name, buf, buf_bytes)`. `name` es el nombre corto (`C01.VNB`); el
  backend PS1 lo busca en `\DATA\`, el de PC en la carpeta que recibe `vn_platform_pc_init`.
- Fuente: `font_upload(atlas_4bpp)` (256x256 a 4 bits), `draw_glyph(...)`, `glyphs_end(layer)`.
- Gráficos: `clear`, `draw_sprite`, `present`
- Audio: `play_music`, `play_sfx`
- Entrada: `poll_input`
- Almacenamiento: `save`, `load`
- Debug: `log`
- Tiempo: `get_time_ms`, `sleep_ms`

Hoy el núcleo solo llama a archivos y fuente. Las demás quedan en `NULL` en el backend PS1 hasta que un módulo del
núcleo las necesite (no se adivina su semántica).

## Tareas de extracción (Fase 1)

1. Copiar `engine/ps1-base/core/` a `engine/core/`.
2. Reemplazar llamadas directas a hardware PS1 por callbacks `VnPlatformOps`.
3. Eliminar dependencias de PSn00bSDK del núcleo (mover a backend).
4. Compilar el núcleo para PC (SDL2) y probar.
5. Documentar cada función pública en este archivo.

## Estado de la extracción

| Módulo | Estado | Dependencia |
|---|---|---|
| `vm`, `scene`, `str`, `lz4`, `opcodes.h`, `vn_limits.h` | En `engine/core/` (copia exacta) | Ninguna; la VM ya habla con el exterior por `VmHost` |
| `chapter` | En `engine/core/`, sobre `vn_ops` | `file_size`, `file_read` |
| `text` | En `engine/core/`, sobre `vn_ops` | `font_upload`, `draw_glyph`, `glyphs_end` |
| `audio`, `cd`, `img`, `input`, `res`, `save`, `video`, `video_clip` | En `platforms/ps1/` (copia exacta) | PSn00bSDK directo |
| `app/main.c` (2371 líneas: bucle, menús, guardado, galería) | Sin extraer | Todo lo anterior |

`res` (gestor de VRAM) e `img` quedan como código de PS1: su lógica está atada a coordenadas de VRAM y CLUT.

## Pruebas

- Host: `tests/core/test_core_host.c` carga `FONT.BIN` y `C00.VNB`/`T00.TXT` reales, corre la VM hasta el primer
  diálogo y lo dibuja con el backend PC. Compilar y correr (PowerShell):

  ```powershell
  C:\msys64\ucrt64\bin\gcc.exe -std=c99 -Wall -Wextra -pedantic -Iengine/core -Iplatforms/pc engine/core/*.c platforms/pc/backend.c tests/core/test_core_host.c -o build/test_core_host.exe
  $env:PATH = "C:\msys64\ucrt64\bin;$env:PATH"; .\build\test_core_host.exe E:\Dev\wani-ps1\build\fase0
  ```

- PS1: `engine/core/*.c` y `platforms/ps1/*.c` compilan con `mipsel-none-elf-gcc` de PSn00bSDK (`save.c` necesita
  `game_config.h`, que genera el CMake de `vn-engine-ps1`). Todavía no se enlaza un ejecutable: falta `main.c`.

## Origen del código

- `engine/ps1-base/` = `E:\Dev\vn-engine-ps1` (commit `947cb3b`), idéntico a su `core/`. Es la base.
- `E:\Dev\snoot-ps1\engine\` es el motor de la v1.0 publicada de Snoot, del que nació `vn-engine-ps1` (commit
  `ae2f4f0`). Es un subconjunto (sin capítulos en heap, sin giro, sin módulos especiales): sirve de referencia
  validada en hardware, no de base.

## Notas

- El núcleo original usa C99 y es compatible con PSn00bSDK.
- Los límites de memoria (`vn_limits.h`) deben ser configurables por plataforma.
- El bytecode VNB (v1/v2) se define en `engine/ps1-base/docs/bytecode.md`.
- El compilador y simulador viven en `engine/ps1-base/vncompiler/`.
