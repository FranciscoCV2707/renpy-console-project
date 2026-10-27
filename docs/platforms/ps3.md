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
- SDL2 2.31.0 para PSL1GHT: en `/usr/local/ps3dev/portlibs/ppu` (`sdl2-config`, `sdl2.pc`, `libSDL2.a`).
- Empaquetado: `make_self`, `make_self_npdrm`, `fself`, `pkg.py`, `sfo.py` (en `/usr/local/ps3dev/bin`).

## Cómo se compila

```sh
E:/Dev/renpy-console-project/.venv/Scripts/python.exe platforms/ps3/build.py --trace
```

Genera `build/ps3/snoot.self` y `build/ps3/snoot.pkg`. Con `--trace` define `VN_TRACE`. El backend SDL se ajusta para PS3 bajo `#ifdef __PSL1GHT__`: ventana 1280×720, área de juego 960×720 centrada (320×240 ×3), rutas por defecto `/dev_hdd0/game/SNOT00001/USRDIR/data` (lectura) y `/dev_hdd0/game/SNOT00001/USRDIR/save` (partidas), `mkdir` con modo POSIX y salida estándar con `fflush`.

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

**Bloqueo conocido (2026-10-27):** el juego arranca en RPCS3 (video SDL2/RSX OK, lee `USRDIR/data`) y se congela
en `audio_init`: el driver de audio de SDL2-PSL1GHT (`SDL_psl1ghtaudio.o` de la imagen Docker) imprime
`PSL1GHT_AUD_OpenDevice(%08X.%08X, %s, %d)` pasando como `%s` un registro que el llamador de SDL2 2.31 no
inicializa (firma de `OpenDevice` antigua); en RPCS3 ese registro vale `0x1` y el `vfprintf` de newlib lo
desreferencia: `VM: Access violation reading location 0x1` y "Emulation has been frozen" antes de escribir
cualquier evento de traza. Reproduce igual con el decodificador PPU en intérprete. No es arreglable desde este
repo (haría falta parchear `libSDL2.a` de la imagen o saltar el audio en el backend, ambos fuera de los archivos
permitidos de T-613); propuesto como tarea nueva.

## Lo que falta para la automatización con `tools/ctl`

- Resolver el bloqueo del driver de audio SDL2-PSL1GHT (arriba) para obtener traza y veredicto del escenario.
- Verificar en RPCS3 que el render acelerado y el audio de SDL2 funcionan; hoy solo se ha comprobado que compila,
  enlaza y que el video inicializa (RSX y `USRDIR/data` montados) en el emulador.
- Confirmar el mapeo de botones del DualShock 3 a `BTN_*`; hoy se reutiliza el mapeo genérico de SDL2.
- El firmware de PS3 no se descarga desde este repo (ver `docs/what-to-download.md`).
