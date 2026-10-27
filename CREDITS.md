# CREDITS — Snoot Game en consolas (port no oficial)

Port no oficial hecho por el proyecto **renpy-console-project** a partir de Snoot Game de **Cavemanon**.
Este archivo lista todo lo que se distribuye dentro de un build del port (disco, ROM o ejecutable con
datos) y su licencia; lo que exige cada licencia al publicar está en `docs/licencias.md`.

## Juego

| Qué se distribuye | Autores | Licencia | Fuente de la licencia |
|---|---|---|---|
| Código del juego (scripts `.rpy`/`.rpyc` recompilados a VNB) | Cavemanon | **AGPL-3.0** | `LICENSE` y `GNU Affero General Public License Version Three.txt` de `SnootGame-Patch14-MunichAgreement-win` (copias en `E:\Dev\snoot-ps1\original\`) |
| Guion, imágenes, audio y demás recursos de Cavemanon, convertidos a los formatos de cada consola | Cavemanon y colaboradores | **CC-BY-SA 4.0** | `LICENSE` y `CC-BY-SA-4.0.txt` del juego (ídem) |
| Audio de terceros con cláusula de atribución (Freesound.org, Sonniss GDC 2015-2017, imágenes de stock) | Autores listados uno por uno | Atribución exigida por el `LICENSE` del juego | Sección "Non-Cavemanon sourced items with attribution clauses" del `LICENSE` del juego |
| Excepción de tienda digital (`GPL-Exception`) | Cavemanon | Solo aplica a distribuir en tiendas; un port libre no la necesita | `GPL-Exception` del juego |

## Port

| Qué se distribuye | Autores | Licencia | Fuente de la licencia |
|---|---|---|---|
| Núcleo C99 (`engine/core`) y datos VNB | renpy-console-project | **MIT** | `PLAN.md` D11 y sección 10 |
| Código fuente de cada backend publicado junto al build (discos/ROM con datos del juego) | renpy-console-project | **AGPL-3.0** (obra derivada del juego) | `PLAN.md` D11 y sección 10 |

## Fuentes tipográficas del juego

| Qué se distribuye | Autores | Licencia | Fuente de la licencia |
|---|---|---|---|
| `FallingSky.otf` (modificado por el juego con glifos de Noto Sans Thai Looped; el port lo rasteriza a `FONT.BIN`) | Falling Sky (derivada de Source Sans Pro de Adobe), modificación de Cavemanon | **Por verificar**: el juego no incluye archivo de licencia de la fuente; la familia es derivada de Source Sans Pro (SIL OFL) | `game/gui.rpy:22-27` y fichas de la fuente (font.download/font-falling-sky: "derivative of the SIL Open Font Licensed open source font, Source Sans Pro by Adobe") |
| `NotoSansJP-Regular.ttf` | Google / Noto Project | **SIL OFL 1.1** | notofonts.github.io ("All Noto fonts are licensed under the Open Font License") |
| `NotoSansThaiLooped-Regular.ttf` (`game/tl/th/fonts/`) | Google / Noto Project | **SIL OFL 1.1** | Ídem |

## Motor y SDKs enlazados en el binario de cada plataforma

| Componente | Plataformas | Licencia | Fuente de la licencia |
|---|---|---|---|
| SDL2 (y mezclador del backend PC) | PC, PSP, PS2 | **zlib** | `C:\msys64\ucrt64\share\licenses\SDL2\LICENSE.txt` (copyleft local; texto también en SDL2 upstream) |
| PSn00bSDK (núcleo, libpsx, etc.) | PS1 | **MPL 2.0** | `C:\msys64\usr\local\psn00bsdk\share\psn00bsdk\doc\LICENSE.md` |
| pspsdk | PSP | **BSD** (excepción: `tools/PrxEncrypter`, GPLv3, no se usa) | `README.md` de github.com/pspdev/pspsdk ("PSPSDK is distributed under a BSD-compatible license, with the exception of the files located in tools/PrxEncrypter") |
| ps2sdk | PS2 | **Academic Free License 2.0** | `README.md` de github.com/ps2dev/ps2sdk ("PS2SDK is licensed under the Academic Free License version 2.0") |
| gsKit | PS2 | **Academic Free License 2.0** | `README.md` de github.com/ps2dev/gsKit y cabeceras (`gsInit.h`: "Licenced under Academic Free License version 2.0") |
| libctru | 3DS | **zlib** | Listado de repos de github.com/devkitPro (libctru marcado "Zlib License") |
| libogc | Wii/GC | **Por verificar** (GitHub marca "Other"; licencia propia estilo BSD) | github.com/devkitPro/libogc |
| libnx | Switch | **ISC** | Listado de repos de github.com/switchbrew (libnx marcado "ISC License") |
| VitaSDK (cabeceras del sistema) | Vita | **MIT** para las cabeceras; **por verificar** los paquetes que se enlacen | docs.vitasdk.org ("The header files of the vitasdk are released under the terms of the MIT license") |
| nxdk | Xbox | **MIT** (lwIP: BSD modificada; PDCLib: CC0; NVIDIA Cg: licencia NVIDIA) | `README.md` de github.com/XboxDev/nxdk y cabeceras SPDX (`lib/nxdk/path.h`) |
| libogg | Todas (audio Ogg) | **BSD 3-cláusulas** | `C:\msys64\ucrt64\share\licenses\libogg\COPYING` |
| libvorbis | Todas (audio Ogg) | **BSD** (estilo Xiph) | `README` de github.com/xiph/vorbis ("a BSD-style license software implementation of the Vorbis specification") |

## Herramientas de compilación y conversión (no se distribuyen en el build)

| Componente | Licencia | Fuente |
|---|---|---|
| Ren'Py (8.3.7; kit de análisis/conversión y juego de referencia) | MIT (+ LGPL/MIT según componentes; lista oficial) | `renpy/LICENSE.txt` del juego y renpy.org/l/license |
| mkpsxiso / dumpsxiso (imagen del CD PS1) | GPLv2 o posterior | `C:\msys64\usr\local\psn00bsdk\share\psn00bsdk\doc\mkpsxiso\LICENSE.md` |
| zlib, libpng, freetype, ffmpeg (asset pipeline y tooling) | zlib, PNG Reference Library 2, FTL/GPL según componente | `C:\msys64\ucrt64\share\licenses\{zlib,libpng,freetype}` |
| GCC y toolchains (host, Docker) | GPL con excepción de runtime (solo se usan para compilar) | gcc.gnu.org; no se distribuye el compilador |

Los builds no incluyen BIOS, firmware ni claves de ninguna consola.
