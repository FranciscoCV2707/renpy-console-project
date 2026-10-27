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
- En RPCS3: instalar `snoot.pkg` con `File → Install Packages/Raps` (o arrastrarlo a la ventana) y ejecutar el título `SNOT00001`. Para ejecución headless:
  ```sh
  rpcs3.exe --headless "dev_hdd0/game/SNOT00001/USRDIR/EBOOT.BIN"
  ```
  RPCS3 vuelca `stdout`/TRACE a `RPCS3.log` y a la consola TTY. Requiere firmware oficial de PS3 (`PS3UPDAT.PUP`) instalado en RPCS3.

## Lo que falta para la automatización con `tools/ctl`

- Adapter `ctl` para PS3 (no implementado en esta tarea): instalar el `.pkg` en RPCS3, arrancar en modo headless y capturar la traza TRACE de `RPCS3.log`.
- Verificar en RPCS3 que el render acelerado y el audio de SDL2 funcionan; hoy solo se ha comprobado que compila y enlaza.
- Confirmar el mapeo de botones del DualShock 3 a `BTN_*`; hoy se reutiliza el mapeo genérico de SDL2.
- El firmware de PS3 no se descarga desde este repo (ver `docs/what-to-download.md`).
