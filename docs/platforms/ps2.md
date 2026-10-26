# PS2 — Toolchain Docker

## Imagen Docker

- Imagen: `ps2dev/ps2dev@sha256:5476fdfbf34d35eb644fde0a6f6533fb554a4a8171ce53dad7cd1df6077dfb05`
- Etiqueta de origen: `ps2dev/ps2dev:latest`
- Digest: `sha256:5476fdfbf34d35eb644fde0a6f6533fb554a4a8171ce53dad7cd1df6077dfb05`
- Tamaño: ~1.05 GB
- Comprobar localmente:

```sh
docker pull ps2dev/ps2dev@sha256:5476fdfbf34d35eb644fde0a6f6533fb554a4a8171ce53dad7cd1df6077dfb05
docker inspect --format "{{index .RepoDigests 0}}" ps2dev/ps2dev:latest
```

## Toolchain incluido

- Compilador EE: `mips64r5900el-ps2-elf-gcc (GCC) 15.2.0` (`/usr/local/ps2dev/ee/bin/`).
- IOP: `mipsel-none-elf-gcc` en `/usr/local/ps2dev/iop/bin/`.
- `PS2SDK=/usr/local/ps2dev/ps2sdk`, `PS2DEV=/usr/local/ps2dev`, `GSKIT=/usr/local/ps2dev/gsKit`.
- SDL2 2.32.10 portado a PS2 en `/usr/local/ps2dev/ps2sdk/ports` (`sdl2.pc`); también `SDL2_image`, `SDL2_mixer`, `SDL2_ttf`.
- gsKit en `/usr/local/ps2dev/gsKit`.
- `make` **no** está en la imagen: instalarlo con `apk add --no-cache make` dentro del contenedor.
- No hay `pkg-config`; las rutas se ponen a mano (ver `Makefile`).

## Compilación del hello

Fuente: `platforms/ps2/hello/` (`main.c` + `Makefile`).

```sh
docker run --rm -v "${PWD}:/src" -w /src/platforms/ps2/hello \
  ps2dev/ps2dev@sha256:5476fdfbf34d35eb644fde0a6f6533fb554a4a8171ce53dad7cd1df6077dfb05 \
  sh -c "apk add --no-cache make >/tmp/apk.log 2>&1 && make"
```

En Windows (PowerShell):

```powershell
docker run --rm -v "E:/Dev/renpy-console-project:/src" -w /src/platforms/ps2/hello `
  ps2dev/ps2dev@sha256:5476fdfbf34d35eb644fde0a6f6533fb554a4a8171ce53dad7cd1df6077dfb05 `
  sh -c "apk add --no-cache make >/tmp/apk.log 2>&1 && make"
```

## Salida esperada

- `platforms/ps2/hello/hello.elf` (ejecutable ELF de PS2).

Salida real del build (recortada):

```
mips64r5900el-ps2-elf-gcc ... -c main.c -o main.o
mips64r5900el-ps2-elf-gcc -T.../linkfile -O2 -o hello.elf main.o \
  -L.../ee/lib ... -L.../ports/lib -L.../gsKit/lib \
  -lSDL2main -lSDL2 -lm -lpatches -lgskit -ldmakit -lps2_drivers
```

## Lo que se verificó

Solo se verificó que compila y enlaza en la imagen Docker indicada. No se ha ejecutado el `hello.elf` resultante en PCSX2 ni en hardware PS2.

## Problemas encontrados

- La imagen no trae `make` ni `pkg-config`: el `Makefile` fija las rutas de include/lib a mano y el comando de build instala `make` con `apk`.
- El enlazado necesita `-L$(PS2SDK)/ports/lib` y `-L$(PS2DEV)/gsKit/lib`; sin ellas falla con `cannot find -lSDL2` / `-lgskit`.
- `*.elf` ya está ignorado por `.gitignore`, así que no se sube el binario.
- El `main.c` usa `SDL_RENDERER_SOFTWARE`; el render por software es el más portable en PS2.
