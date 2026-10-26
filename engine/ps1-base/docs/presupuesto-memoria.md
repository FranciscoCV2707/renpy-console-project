# Presupuesto de memoria del motor (perfil wani)

**Actualizacion 2026-10-24 (PAKO-14): capitulos en el heap.** `chapter_buf` (48 KiB) y `text_buf` (80 KiB) ya no
existen. `core/chapter.c` reserva con `malloc` **un solo bloque** por capitulo con el tamano real de Cxx.VNB y
Txx.TXT (cada uno redondeado a sectores de 2048) y lo libera antes de cargar el siguiente; si `malloc` devuelve NULL
o el archivo excede los limites, el cargador devuelve -1 con un aviso (`capitulo N: sin heap para ...`) y la VM
queda en error en vez de escribir fuera del buffer. FONT.BIN se lee al arrancar en un bloque temporal del heap y se
suelta tras copiarla a la VRAM.

- Limites: `core/vn_limits.h`, 96 KiB para el VNB y 96 KiB para el texto. `vncompiler/formatos.py` lee ese mismo
  archivo y `compile_program`/`compilar_capitulo` fallan con `capitulo NN (etiqueta): VNB|texto de X bytes excede
  el limite del motor de Y bytes` antes de producir el disco.
- Medido con `cmake --preset wani`: bss 1.408.812 (antes 1.539.876), `_end` 0x80181fb0, **heap libre al arrancar
  516.168 bytes** (antes 385.936). El peor capitulo previsto de Wani (~57 KB de VNB + 65 KB de texto = ~122 KB)
  deja ~394 KB para la pila. Snoot: bss 1.407.600.
- Por que heap y no partir capitulos con LOAD_PACK: partir obliga al compilador a cortar el codigo en puntos
  seguros, enlazar saltos y menus entre paquetes y reescribir capitulo/offset en las partidas guardadas. El heap
  solo cambia el cargador, no toca el formato VNB1 ni el guardado, y Snoot gana la misma memoria.
- Fragmentacion: el bloque del capitulo es la unica reserva viva del motor (la fuente se suelta antes del primer
  capitulo; el video usa la cache de `res`; `iso_search` no usa heap), asi que cada carga ve el heap entero libre.
  Quien agregue otro `malloc` permanente debe hacerlo antes del primer capitulo o revisar esta cuenta.
- Prueba: `tests/compiler/test_chapter_limits.py` (chequeo del compilador y `core/chapter.c` nativo con malloc
  contado: capitulo de 60 KB + 70 KB carga, un solo bloque vivo, rechazos sin memoria tomada).

**Actualizacion 2026-10-22 (PAKO-12):** el reproductor STR ya no tiene buffers fijos (`mdec`, `chunk`, `bs0`,
`bs1`, 336 KiB): los toma prestados de `cache_buf` (res_borrow_cache) mientras dura el video. Ahora
`mipsel-none-elf-size` da bss 1.539.876 y el heap libre al arrancar es de **~377 KiB** (antes ~40 KiB). Las filas
de los buffers del video en la tabla de abajo son historicas.

Medido el 2026-10-22 (PAKO-9) con `cmake --preset wani` y `cmake --build build/wani`, leyendo el mapa de
simbolos `build/wani/wani.map` (lo genera el PSN00bSDK con `nm -f posix -l -n` despues de enlazar) y
`mipsel-none-elf-size build/wani/wani.elf` (text 103.560, data 188, bss 1.886.800).

## Reparto de la RAM

| Rango | Simbolos | Bytes | Contenido |
|---|---|---|---|
| 0x80010000..0x80029554 | `__text_start`..`__bss_start` | 103.892 | codigo, rodata y datos inicializados |
| 0x80029554..0x801f5fa4 | `__bss_start`..`_end` | 1.886.800 | BSS: buffers estaticos del motor |
| 0x801f5fa8..0x801ffff8 | heap | **41.044 (~40,1 KiB)** | margen libre en el arranque |

El heap no tiene simbolo en el mapa: lo abre `InitHeap(_end + 4, 0x801ffff8 - _end)` en `libc/start.c`
del PSn00bSDK, justo despues de la BSS, con tope fijo en 0x801ffff8. Ahi arriba empieza la pila del
proceso (baja desde el tope de la RAM, ~0x801ffff0), asi que **heap y pila crecen uno contra el otro
dentro del mismo margen de ~40 KiB**. La pila de interrupciones no sale de ahi: `_isr_stack` (4.096
bytes) ya vive dentro de la BSS. En la epoca del recorrido visual (PAKO-2) `__bss_end` estaba en
0x801f7038 y el margen era 36.800 bytes; hoy es apenas mayor.

Regla practica: cada KiB de buffer estatico nuevo es un KiB menos de ese margen. No hay presupuesto
para buffers grandes fuera de la BSS, y el heap solo puede usarse con comprobacion de NULL.

## Que consume la BSS (1.886.800 bytes)

| Bytes | Simbolo | Donde |
|---|---|---|
| 524.288 | `big_raw` | core/img.c:110 — descompresion de la imagen mas grande (stairs, 512 KiB) |
| 327.680 | `cache_buf` | core/res.c:159 — cache de imagenes decodificadas (320 KiB) |
| 176.128 | `file_buf` | core/res.c:28 — el archivo de imagen mas grande (172 KiB) |
| 131.072 | `mdec` | modules/fmv.c:29 — cuadro del MDEC para el video STR (128 KiB) |
| 98.304 | `scratch` | core/img.c:12 — descompresion LZ4 (96 KiB) |
| 81.920 | `text_buf` | app/main.c:62 — textos del capitulo (80 KiB) |
| 81.920 | `chunk` | modules/fmv.c:26 — 40 sectores del STR |
| 80.000 | `prim_buf` | core/video.c:10 — ordenes de dibujo, dos paginas de 40.000 |
| 65.536 + 65.536 | `bs0`, `bs1` | modules/fmv.c:27-28 — bitstream del STR (64 KiB cada uno) |
| 49.152 | `chapter_buf` | app/main.c:61 — capitulo VNB1 (48 KiB) |
| 32.768 | `bg_chunk` | core/audio.c:401 — musica ambiental por bloques (16 sectores) |
| 32.768 | `chunk` | core/audio.c:45 — musica XA por bloques (16 sectores) |
| 24.054 | `table` | core/cd.c — tabla FTB1 (1100 entradas + sector de sobra) y borrador de `iso_search` |
| 16.384 | `autotest` | app/main.c — guion de la prueba automatica |
| 16.384 | `file_buf` | app/main.c:60 — iconos de memory card |
| 8.192 | `block` | core/save.c:12 — bloque de memory card |
| 7.936 | `save_buf` | core/save.c — datos de guardado |
| 7.936 | `other` | core/save.c:99 — copia para comparar ranuras |
| 4.096 | `_isr_stack` | PSn00bSDK — pila de interrupciones |

Los ~290 simbolos menores (tablas de animaciones, sprites, menu, telefono, lienzo, SDK) suman el
resto. Los buffers del video STR (`mdec`, `chunk`, `bs0`, `bs1` = 336 KiB) y la cache de imagenes
(`cache_buf` + `big_raw` + `file_buf` + `scratch` = 1,1 MiB) dominan la BSS.

## CdSearchFile y el disco antiguo de Wani

Contexto (PAKO-2, docs/recorrido-visual.md en wani-ps1): un disco antiguo de Wani llamaba
`CdSearchFile("\\DATA\\FILES.BIN")`. El registro del directorio \DATA ocupaba 48 KB; PSn00bSDK cachea
ese registro completo con `malloc(49152)` y **no comprueba NULL**: con ~36 KB de heap libre devolvio
NULL, la DMA del CD escribio desde 0x80000000 y tumbo la CPU.

Desde PAKO-9 el motor no llama a `CdSearchFile` (lo comprueba
`tests/compiler/test_cd_guard.py::test_engine_sources_never_call_cd_search_file`):
`core/cd.c` implementa `iso_search`, que baja del descriptor de volumen (sector 16) componente por
componente y recorre cada directorio **sector a sector** usando como borrador la propia tabla FTB1,
asi que no toca el heap en absoluto y admite directorios de cualquier tamano; lo que no encuentra
falla con error visible (`cd: no se encuentra ...`). Con esto el motor reserva cero bytes de heap:
los ~40 KiB del margen quedan completos para la pila.

Fuera del motor quedan dos llamadas de prueba, las dos buscando un archivo en la raiz de un disco de
prueba chico (el caso "solo directorios pequenos" que no agota el heap): `tests/str/main.c` (el
ejemplo MPL-2.0 del SDK, que no se modifica) y `tests/str/player/main.c`.

## Volver a medir

```powershell
cmake --preset wani
cmake --build build/wani
C:\msys64\usr\local\psn00bsdk\bin\mipsel-none-elf-size.exe build\wani\wani.elf
Select-String -Path build\wani\wani.map -Pattern '^(__bss_start|_end) '
```

Heap libre = 0x801ffff8 - `_end` (InitHeap resta 4 bytes al abrirlo en `_end + 4`); BSS = `_end - __bss_start`.
