# Wii — Toolchain Docker

## Imagen Docker

- Imagen: `devkitpro/devkitppc@sha256:d50f8a886f2ce1d3c22685a774afb0845379876b47d9b41a9b729f4f63a54813`
- Etiqueta de origen: `devkitpro/devkitppc:latest`
- Digest: `sha256:d50f8a886f2ce1d3c22685a774afb0845379876b47d9b41a9b729f4f63a54813`
- Comprobar localmente:

```sh
docker pull devkitpro/devkitppc@sha256:d50f8a886f2ce1d3c22685a774afb0845379876b47d9b41a9b729f4f63a54813
docker inspect --format "{{index .RepoDigests 0}}" devkitpro/devkitppc:latest
```

## Toolchain incluido

- Compilador: `powerpc-eabi-gcc (devkitPPC) 16.2.0` (`/opt/devkitpro/devkitPPC/bin/`).
- `make` ya está en la imagen; no hace falta instalarlo.
- Macro de plataforma: `-D__WII__` (la define `wiivars.sh` con `CPPFLAGS=-D__WII__ ...`); por eso en `platforms/sdl` se usa `#ifdef __WII__`.
- SDL2 2.28.5 para Wii: paquete `wii-sdl2` (`wii-sdl2 2.28.5-17`, `dkp-pacman -Ss wii-sdl2`), en `/opt/devkitpro/portlibs/wii` (`sdl2-config` y `sdl2.pc`). También están `wii-sdl2_image`, `wii-sdl2_mixer`, `wii-sdl2_ttf` y `wii-sdl2_gfx`.
- libogc 3.2.1 (`libogc 3.2.1-1`, `dkp-pacman -Ss libogc`), en `/opt/devkitpro/libogc`.
- Conversión ELF → DOL: `elf2dol` en `/opt/devkitpro/tools/bin/`.

## Cómo se compila

```sh
E:/Dev/renpy-console-project/.venv/Scripts/python.exe platforms/wii/build.py --trace
```

Genera `build/wii/boot.dol` y `build/wii/meta.xml`. Con `--trace` define `VN_TRACE`. El backend SDL se ajusta para Wii bajo `#ifdef __WII__`: ventana 640×480, rutas por defecto `sd:/apps/snoot/data` (lectura) y `sd:/apps/snoot/save` (partidas), `fatInitDefault()` al arrancar y `mkdir` con modo POSIX.

## Cómo se instala (consola o Dolphin)

- Copiar `build/wii/boot.dol` y `build/wii/meta.xml` a `sd:/apps/snoot/` en la tarjeta SD. Los datos del disco de PS1 van en `sd:/apps/snoot/data/`.
- En Dolphin, cargar `boot.dol` con `-b -e <archivo>` (verificar flags en la versión instalada). Dolphin emula la SD a partir de la carpeta configurada como tarjeta SD.

## Lo que falta para la automatización con `tools/ctl`

- Adapter `ctl` para Wii (no implementado en esta tarea): empaquetar `boot.dol` + `meta.xml` + datos de `build/ctl/ps1/disc/` en la estructura `sd:/apps/snoot/`, arrancar Dolphin y capturar la traza (OSReport / stdout) de `build/ctl/wii/trace.txt`.
- Verificar en Dolphin que el render por software/accelerated y el audio de SDL2 funcionan; hoy solo se ha comprobado que compila y enlaza.
- Confirmar el mapeo de botones del Wiimote/Classic Controller a `BTN_*`; hoy se reutiliza el mapeo genérico de SDL2.
PY