# Nintendo Switch — Toolchain Docker

## Imagen Docker

- Imagen: `devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282`
- Etiqueta de origen: `devkitpro/devkita64:latest`
- Digest: `sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282`
- Tamaño: ~ (ver `docker images` tras el pull)
- Comprobar localmente:

```sh
docker pull devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
docker inspect --format "{{index .RepoDigests 0}}" devkitpro/devkita64:latest
```

## Toolchain incluido

- Compilador: `aarch64-none-elf-gcc (GCC) 15.2.0` en `/opt/devkitpro/devkitA64/bin/`.
- SDK: libnx en `/opt/devkitpro/libnx` (headers en `include/`, libs en `lib/`, `switch.specs` y `switch_rules`).
- SDL2 2.28.5 para Switch vía `switch-sdl2` (`sdl2-config` en `/opt/devkitpro/portlibs/switch/bin/`), con `SDL2_image`, `SDL2_mixer`, `SDL2_ttf` disponibles en la misma ruta.
- Empaquetado: `nacptool` y `elf2nro` en `/opt/devkitpro/tools/bin/`.
- La macro del SDK es `__SWITCH__` (la define `sdl2-config --cflags` y `libnx`); se usa en `platforms/sdl/` para los ajustes de consola.
- `make` está incluido en la imagen.

## Compilación

```sh
python platforms/switch/build.py --trace
```

Salida: `build/switch/snoot.nro` (además de `snoot.elf` y `snoot.nacp` intermedios).

El script monta el repositorio en `/src` dentro del contenedor y compila `engine/core`, `engine/app`, `engine/modules`, `games/snoot` y `platforms/sdl` con los flags de `sdl2-config`, enlaza con `switch.specs` y empaqueta con `elf2nro`.

## Pantalla y datos

- Pantalla: 1280×720; el backend SDL usa `SDL_RenderSetLogicalSize` con 320×240, por lo que el área de juego (960×720) queda centrada con barras laterales.
- Los archivos del disco de PS1 se leen desde `sdmc:/switch/snoot/data/` (se puede sobrescribir con `VN_DATA_DIR`). El guardado usa `sdmc:/switch/snoot/save/` por defecto.

## Instalación y prueba

Esta tarea no usa emulador: Switch necesita claves y firmware del usuario. La prueba se hace en hardware propio copiando `snoot.nro` a `sdmc:/switch/snoot/` (o a la carpeta que use el cargador de homebrew) y ejecutándolo desde el homebrew menu. La traza sale por `nxlink`/stdout del cargador.

## Lo que falta para `tools/ctl`

- Adapter de `ctl` para Switch (no implementado en esta tarea): invocación de `build.py`, despliegue por `nxlink` y captura de la traza por red.
- Generación de `AUTOTEST.BIN`/escenarios en la consola real (igual que en PC, con `VN_FAST=1`).
- Verificación de rendimiento y audio en hardware.

## Lo que se verificó

- Compilación y enlace limpios (cero advertencias) con la imagen fijada por digest: `build/switch/snoot.nro` de 6889528 bytes.
- No se ejecutó en hardware ni en emulador.
