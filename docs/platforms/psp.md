# PSP — Toolchain Docker

## Imagen Docker

- Imagen: `pspdev/pspdev@sha256:54895e6f5afb71b8f4f6915ee6d5023e1e087ca7afdf2dcb1d7a694a5233e45f`
- Etiqueta de origen: `pspdev/pspdev:latest`
- Digest: `sha256:54895e6f5afb71b8f4f6915ee6d5023e1e087ca7afdf2dcb1d7a694a5233e45f`
- Tamaño: ~790 MB
- Comprobar localmente:

```sh
docker pull pspdev/pspdev@sha256:54895e6f5afb71b8f4f6915ee6d5023e1e087ca7afdf2dcb1d7a694a5233e45f
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
  pspdev/pspdev@sha256:54895e6f5afb71b8f4f6915ee6d5023e1e087ca7afdf2dcb1d7a694a5233e45f make
```

En Windows (PowerShell) usar rutas absolutas:

```powershell
docker run --rm -v "E:/Dev/renpy-console-project:/src" -w /src/platforms/psp/hello `
  pspdev/pspdev@sha256:54895e6f5afb71b8f4f6915ee6d5023e1e087ca7afdf2dcb1d7a694a5233e45f make
```

## Salida esperada

- `platforms/psp/hello/hello.elf` (intermedio).
- `platforms/psp/hello/PARAM.SFO` (metadatos del EBOOT).
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

## Lo que se verificó

Solo se verificó que compila y enlaza en la imagen Docker indicada. No se ha ejecutado el `EBOOT.PBP` resultante en PPSSPP ni en hardware PSP.

## Problemas encontrados

- `EBOOT.PBP` y `PARAM.SFO` no estaban en `.gitignore` en el primer intento; ahora ambos están ignorados en `main` (Claude los agregó). No subir los binarios al repositorio.
- El `main.c` usa `SDL_RENDERER_SOFTWARE`; en PSP SDL2 usa render por software.
- `PSP_EBOOT_TITLE` se fija en el `Makefile` (`Hello SDL2`); cambiar el título requiere recompilar.
- `all:` se define después del `include` de `build.mak` porque `$(PSP_EBOOT)` se define dentro de `build.mak` (ver comentario en el `Makefile`).
