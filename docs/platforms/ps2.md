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

## Snoot con el backend SDL

`python platforms/ps2/build.py --trace` copia las fuentes a `build/ps2/src/`, genera la configuración de Snoot y las
compila con la misma imagen fijada arriba. El resultado es `build/ps2/snoot.elf`; no se necesita `make` ni
`pkg-config` en Windows.

El adapter prepara `build/ps2/disc/` copiando los archivos planos de `build/ctl/ps1/disc/` y escribiendo ahí
`AUTOTEST.BIN`. PCSX2 ejecuta el ELF directamente; `host:disc` accede a la carpeta hermana `disc/` desde el ELF
(HostFS fija la raíz `host:` en la carpeta del ELF, verificado en el log: `HLE Host: Set 'host:' root path to:
.../build/ps2`). La opción **Host Filesystem** de PCSX2 debe estar habilitada para que funcione `host:`; no hay
parámetro CLI para activarla, se fija en `inis/PCSX2.ini` (`HostFs = true`). [HostFS en PCSX2](https://github.com/PCSX2/pcsx2/issues/10259).
La pantalla SDL usa 640×448 y mantiene el lienzo lógico 320×240; SDL conserva la proporción 4:3 y deja bandas
laterales para llenar la salida 10:7.

PCSX2 se inicia con `-portable -nogui -fastboot -elf <archivo> -logfile <archivo> -earlyconsolelog`. La documentación
oficial indica que `-nogui` también activa batch, que `-elf` sustituye el ELF de arranque, y que `-logfile` guarda el
log de la aplicación. La BIOS se selecciona mediante la configuración portable ya instalada; el CLI de PCSX2 no
ofrece una opción de ruta de BIOS. `-earlyconsolelog` envía los mensajes tempranos del emulador a la consola. [Opciones
de línea de comandos de PCSX2](https://pcsx2.net/docs/advanced/cli/).

El adapter combina el log de PCSX2 y su salida de consola y conserva las líneas `T|` (con la hora que PCSX2
antepone quitada). El `printf` del EE llega al log por la consola del EE (`EnableEEConsole = true`), verificado en
ejecución. Al terminar el recorrido el juego imprime `VN_QUIT` y sale (`exit(0)`); el adapter ve la marca en el log
y cierra PCSX2 (`taskkill /T`) sin esperar el timeout, porque el emulador no se cierra solo al salir el ELF.

## Arranque en PS2: SIF RPC antes del audio

Sin más, `snoot.elf` se colgaba antes de escribir nada: `SDL_InitSubSystem(SDL_INIT_AUDIO)` ejecuta
`init_audio_driver()` de `ps2_drivers`, que carga `libsd.irx` y `audsrv.irx` por SIF y llama a `audsrv_init()`. Sin
`SifInitRpc(0)` previo la llamada RPC se queda esperando al IOP para siempre. `video_init` llama antes a
`SifInitRpc(0)`, `sbv_patch_enable_lmb()` y `sbv_patch_disable_prefix_check()`, la misma secuencia `prepare_IOP()` de
la muestra `wav_sample` de [ps2_drivers](https://github.com/fjtrujy/ps2_drivers) (la librería se enlaza con
`-lps2_drivers` y `-lpatches`). Con eso el arranque llega al título y a la primera línea y las lecturas por `host:`
(AUDIO.BIN, FONT.BIN, GAME.BIN, AUTOTEST.BIN) funcionan.

`python -m tools.ctl run --target ps2 --scenario tests/scenarios/snoot-route-chapter_x2.yaml` compara por eventos
contra Ren'Py (D17): veredicto PASS con las 97 líneas de la ruta; el emulador corre ~172 s hasta `VN_QUIT` y el
adapter lo cierra en el momento (límite del escenario: 300 s).

## Problemas encontrados

- La imagen no trae `make` ni `pkg-config`: el `Makefile` fija las rutas de include/lib a mano y el comando de build instala `make` con `apk`.
- El enlazado necesita `-L$(PS2SDK)/ports/lib` y `-L$(PS2DEV)/gsKit/lib`; sin ellas falla con `cannot find -lSDL2` / `-lgskit`.
- `*.elf` ya está ignorado por `.gitignore`, así que no se sube el binario.
- El `main.c` usa `SDL_RENDERER_SOFTWARE`; el render por software es el más portable en PS2.
- El audio de SDL2 para PS2 se colgaba sin `SifInitRpc`: ver la sección de arranque arriba.
- PCSX2 puede quedarse colgado en el arranque del host en la enumeración de mandos SDL (el log se corta tras
  `SDLInputSource: Using Controller DB from resources.`); al repetir la corrida funciona. El adapter lo detecta como
  timeout y deja el log para revisarlo.

