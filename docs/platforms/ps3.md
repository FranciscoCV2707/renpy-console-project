# PS3 — Toolchain Docker (PSL1GHT)

## Imagen Docker

- Imagen: `hldtux/ps3dev-sdl2@sha256:2b6154588148336d559fbd37f4f52a3418fa96a86906b5019160baef22c75e55`
- Etiqueta de origen: `hldtux/ps3dev-sdl2:latest`
- Digest: `sha256:2b6154588148336d559fbd37f4f52a3418fa96a86906b5019160baef22c75e55`
- Comprobar localmente:

```sh
docker pull hldtux/ps3dev-sdl2@sha256:2b6154588148336d559fbd37f4f52a3418fa96a86906b5019160baef22c75e55
docker inspect --format "{{index .RepoDigests 0}}" hldtux/ps3dev-sdl2:latest
```

## Toolchain incluido

- Compilador: `powerpc64-ps3-elf-gcc` / `ppu-gcc` (PSL1GHT v2, `/usr/local/ps3dev`).
- `make` ya está en la imagen; no hace falta instalarlo.
- Macro de plataforma: `-D__PSL1GHT__` (la define el build de PS3 en `platforms/ps3/Makefile`; `platforms/sdl/sdl_target.h` la usa con `#elif defined(__PSL1GHT__)`). SDL2 para PSL1GHT solo expone `__PSL1GHT__` cuando se define esta macro.
- SDL2 2.0.13 desde la fuente del port oficial de ps3dev (`shagkur/SDL_PSL1GHT`), fijado por commit
  `b81fbad4489918f5ed9c9c052238d7a25da9bab9` ("fix API change"): `platforms/ps3/build.py` la clona y compila en
  Docker a `build/ps3/sdl2` (cacheada). La `libSDL2.a` de la imagen (`/usr/local/ps3dev/portlibs/ppu`, SDL 2.31)
  mezcla su núcleo con un driver de audio compilado con la firma antigua de `OpenDevice` y truena en
  `audio_init` (reports/T-613.md); el port fuente trae núcleo y drivers con la misma firma.
- Empaquetado: `make_self`, `make_self_npdrm`, `fself`, `pkg.py`, `sfo.py` (en `/usr/local/ps3dev/bin`).

## Cómo se compila

```sh
E:/Dev/renpy-console-project/.venv/Scripts/python.exe platforms/ps3/build.py --trace
```

Genera `build/ps3/snoot.self` y `build/ps3/snoot.pkg`. Con `--trace` define `VN_TRACE`. El backend SDL se ajusta para PS3 bajo `#ifdef __PSL1GHT__`: ventana 1280×720, área de juego 320×240 centrada a escala 1:1, rutas por defecto `/dev_hdd0/game/SNOT00001/USRDIR/data` (lectura) y `/dev_hdd0/game/SNOT00001/USRDIR/save` (partidas), `mkdir` con modo POSIX y salida estándar con `fflush`. El área va a ×1 (antes ×3 en 960×720) porque el único renderer del port de SDL2 para PSL1GHT es software: el escalado por píxel de 960×720 corría el juego a ~1.5 fps en RPCS3 y a ×1 llega a ~30 fps; en hardware se puede volver a ×3 cuando haya renderer acelerado.

## Cómo se instala (consola o RPCS3)

- En una PS3 con CFW/PS3HEN: copiar `build/ps3/snoot.pkg` a una memoria USB e instalarlo desde el menú XMB en *Package Manager*. El paquete instala `EBOOT.BIN` en `/dev_hdd0/game/SNOT00001/USRDIR/`; los datos del disco de PS1 van en `/dev_hdd0/game/SNOT00001/USRDIR/data/`.
- En RPCS3: instalar `snoot.pkg` con `File → Install Packages/Raps` (o arrastrarlo a la ventana) y ejecutar el título `SNOT00001`. Opciones verificadas con `rpcs3 --help` (build `0.0.43-20410-c365ea76`):
  - `--headless --installfw <PS3UPDAT.PUP>` instala el firmware oficial sin GUI; deja `dev_flash/` junto al `rpcs3.exe`
    (RPCS3 portable: `$(EmulatorDir)` es el directorio del exe) y al terminar escupe ruido de teardown
    (`RPCS3: Verification failed (object: 0x0)`), así que el exit code no es fiable: se comprueba `dev_flash/sys`.
  - `--headless --installpkg <ruta absoluta>` instala el pkg en `dev_hdd0/game/SNOT00001/`; con ruta relativa
    falla con `PKG file not found!`.
  - `--no-gui <EBOOT.BIN>` ejecuta el juego sin la ventana del emulador y sale cuando el juego llama a `exit(0)`.
    `--headless` NO sirve para correr el juego: fuerza el renderer Null (RPCS3.log: "The video renderer 'Vulkan'
    is currently not supported in headless mode").
  - Lo que el juego escribe por `printf` queda en `log/TTY.log` junto al exe (sys_tty_write); el log del emulador,
    en `log/RPCS3.log`. RPCS3 congela la emulación si el juego descarga memoria (`VM: Access violation`).

## Ejecución con `tools/ctl` (T-613)

```
E:/Dev/renpy-console-project/.venv/Scripts/python.exe -m tools.ctl run --target ps3 --scenario tests/scenarios/snoot-route-chapter_x2.yaml
```

`tools/ctl/ps3.py` compila con `platforms/ps3/build.py --trace`, instala firmware y pkg si faltan, copia el disco
de PS1 (`build/ctl/ps1/disc`, prerrequisito de `ctl run --target ps1`) con el `AUTOTEST.BIN` del escenario a
`dev_hdd0/game/SNOT00001/USRDIR/data`, corre con `--no-gui` y extrae las líneas `T|` de `log/TTY.log`.

**Bloqueo resuelto (T-615):** el crash de `audio_init` (reports/T-613.md) venía de la `libSDL2.a` de la imagen
Docker (núcleo 2.31 con el driver `SDL_psl1ghtaudio` compilado contra la firma antigua de `OpenDevice`: el
llamador pasa 4 argumentos y el driver leía `devname` de un registro sin inicializar, que en RPCS3 valía `0x1`
→ `vfprintf` desreferenciaba → `VM: Access violation reading location 0x1`). Se compila SDL2 desde la fuente
del port (commit `b81fbad`, arriba), donde núcleo y driver usan la misma firma; con eso `audio_init` pasa en
RPCS3 (TTY.log: `PSL1GHT_AUD_OpenDevice(..., (null), 0)`, `audioPortOpen: 0`, `audioPortStart: 0`), el juego
arranca con el puerto de audio activo y consume el `AUTOTEST.BIN` (navegó el menú de capítulos del guion en
corridas manuales de RPCS3 a ~4-30 fps).

**Bloqueo resuelto (T-621): `--headless` no sirve para este juego.** El puerto de SDL2 espera el flip
del RSX en cada cuadro: `waitFlip` en `build/ps3/sdl2-src/src/render/psl1ght/SDL_psl1ghtrender.c:113`
(bucle `while (gcmGetFlipStatus() != 0) usleep(200)`), llamado desde `PSL1GHT_RenderPresent` (línea 798);
el modo flip es vsync (`gcmSetFlipMode(GCM_FLIP_VSYNC)`, `src/video/psl1ght/SDL_PSL1GHTvideo.c:90`). Con
el renderer Null de `--headless` el flip nunca se completa, el juego se bloquea en el primer
`SDL_RenderPresent` (~79 millones de `sys_timer_usleep` en `RPCS3.log`) y no abre `C00.VNB` nunca.
`tools/ctl/ps3.py` ahora corre con `--no-gui` y escribe `config/custom_configs/config_SNOT00001.yml`
si falta (claves reales de RPCS3 0.0.43-20410, verificadas en `RPCS3.log`: "Applying custom config"):
`Video: Renderer: OpenGL`, `Resolution: 1280x720`, `Force CPU Blit: true`, `Write/Read Color Buffers:
true`, `Strict Texture Flushing: true`, `Strict Rendering Mode: true`. Sin `Force CPU Blit` el cache de
texturas truena a los ~3-5 s con los blits chicos del renderer software de SDL (OpenGL:
`GLTextureCache.h:729 create_new_texture`, Vulkan: `VKTextureCache.cpp:1053`, ambas
`Verification failed (object: 0x0)`); con CPU blit el juego arranca, lee `FONT/GAME/MCICON/AUTOTEST`,
abre los saves, lee `AUDIO.BIN`/`MUSIC.XA` y pasa los créditos de arranque a ~60 fps.

**Bloqueo actual (2026-10-27, T-621): el pipeline de flip/texturas de RPCS3 en este host se muere en
silencio.** Con la configuración anterior (OpenGL + CPU blit) el RSX procesa los primeros flips y
después deja de completarlos sin error en el log (`RSX: Flip texture was not found in cache. Uploading
surface from CPU` ×7-12 y silencio; `sys_rsx_context_attribute` congelado; `sys_timer_usleep` girando a
~33k/s en el bucle de `waitFlip`): el FPS de la ventana queda congelado y el juego no pasa del título.
En una corrida de ~15 min los flips continuaron a ~30 fps (título y menús dibujados, captura en
`build/ctl/ps3`), pero no llegó a abrir `C00.VNB`. Variante Vulkan sobre la iGPU Intel UHD 770
(`Video: Vulkan: Adapter`): la emulación congela en el arranque (swapchain creado, PPU nunca inicia).
Mismo `EBOOT.BIN` y datos corrieron a 30 fps con menús navegables en la primera mitad de la sesión de
T-615: es el mismo fallo del host que ya documentaba T-615 (además su sensor de CPU reporta "The
required API is not initialized"); el veredicto de `snoot-route-chapter_x2` sigue pendiente de una
corrida sana del emulador.

## Lo que falta para la automatización con `tools/ctl`

- Verificar en una PS3 real: hoy solo se ha verificado en RPCS3 (build 0.0.43-20410, firmware 4.93) que compila,
  enlaza, inicializa audio y video, lee `USRDIR/data` y navega el menú con el `AUTOTEST.BIN`.
- Obtener el veredicto de `snoot-route-chapter_x2` en RPCS3 cuando el renderer del emulador vuelva a correr
  (ver "Bloqueo actual" arriba).
- Confirmar el mapeo de botones del DualShock 3 a `BTN_*`; hoy se reutiliza el mapeo genérico de SDL2.
- El firmware de PS3 no se descarga desde este repo (ver `docs/what-to-download.md`).
