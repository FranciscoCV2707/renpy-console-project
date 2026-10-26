# PSP — Toolchain Docker

## Imagen Docker

- Imagen: `pspdev/pspdev:latest`
- Digest: `sha256:54895e6f5afb71b8f4f6915ee6d5023e1e087ca7afdf2dcb1d7a694a5233e45f`
- Tamaño: ~790 MB
- Comprobar localmente:

```sh
docker pull pspdev/pspdev:latest
docker inspect --format "{{index .RepoDigests 0}}" pspdev/pspdev:latest
```

## Toolchain incluido

- Compilador: `psp-gcc (GCC) 15.2.0` (`/usr/local/pspdev/bin/psp-gcc`).
- SDK PSP: `psp-config --pspsdk-path` → `/usr/local/pspdev/psp/sdk`; `psp-config --pspdev-path` → `/usr/local/pspdev`.
- SDL2 2.32.10 disponible vía `psp-pkg-config --cflags/--libs sdl2` (junto con `SDL2_image`, `SDL2_mixer`, `SDL2_ttf`).
- Empaquetado: `pack-pbp`, `mksfoex`, `psp-fixup-imports`, `psp-strip` (reglas en `$(PSPSDK)/lib/build.mak`).
- `make` incluido.

## Compilación del hello

Fuente: `platforms/psp/hello/` (`main.c` + `Makefile`).

```sh
docker run --rm -v "${PWD}:/src" -w /src/platforms/psp/hello \
  pspdev/pspdev:latest make
```

En Windows (PowerShell) usar rutas absolutas:

```powershell
docker run --rm -v "E:/Dev/renpy-console-project:/src" -w /src/platforms/psp/hello `
  pspdev/pspdev:latest make
```

## Salida esperada

- `platforms/psp/hello/hello.elf` (intermedio).
- `platforms/psp/hello/EBOOT.PBP` (ejecutable final para PSP).

Salida real del build (recortada):

```
psp-gcc ... -c -o main.o main.c
psp-gcc ... main.o ... -o hello.elf
psp-fixup-imports hello.elf
mksfoex -d MEMSIZE=2  'Hello SDL2' PARAM.SFO
psp-strip hello.elf -o hello_strip.elf
pack-pbp EBOOT.PBP PARAM.SFO NULL ... hello_strip.elf NULL
[6]    1312900 bytes | hello_strip.elf
```

## Problemas encontrados

- `EBOOT.PBP` no está en `.gitignore` (solo `*.elf` lo está); no subir el binario al repositorio.
- El `main.c` usa `SDL_RENDERER_SOFTWARE`; el backend de video de SDL2 en PSP se selecciona en tiempo de ejecución.
- `PSP_EBOOT_TITLE` se fija en el `Makefile` (`Hello SDL2`); cambiar el título requiere recompilar.
