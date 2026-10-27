# PS Vita (T-601)

## Imagen Docker

- Imagen: `vitasdk/vitasdk@sha256:8227da1b596d981f4513cd9b36bda1e43857f6dae5bcf4312c1cd40167f7d9bb`
- Etiqueta de origen: `vitasdk/vitasdk:latest`
- Digest: `sha256:8227da1b596d981f4513cd9b36bda1e43857f6dae5bcf4312c1cd40167f7d9bb`
- Tamaño: ~2.18 GB
- Comprobar localmente:

```sh
docker pull vitasdk/vitasdk@sha256:8227da1b596d981f4513cd9b36bda1e43857f6dae5bcf4312c1cd40167f7d9bb
docker inspect --format "{{index .RepoDigests 0}}" vitasdk/vitasdk:latest
```

## Toolchain incluido

- Compilador: `arm-vita-eabi-gcc (GNU Tools for ARM Embedded Processors) 15.2.0`
  (`/usr/local/vitasdk/bin/`).
- `VITASDK=/usr/local/vitasdk`.
- SDL2 2.32.8 (`arm-vita-eabi-pkg-config --modversion sdl2`).
- Herramientas de empaquetado: `vita-elf-create`, `vita-make-fself`, `vita-mksfoex`,
  `vita-pack-vpk`.
- `make` está en la imagen (`/usr/bin/make`).

## Compilación de Snoot

```sh
E:/Dev/renpy-console-project/.venv/Scripts/python.exe platforms/vita/build.py --trace
```

Salida: `build/vita/snoot.vpk`. El script crea `build/vita/generated/game_config.h`, compila
`engine/core`, `engine/app`, `engine/modules`, `games/snoot` y `platforms/sdl`, y empaqueta
el ELF resultante como VPK. Con `--trace` define `VN_TRACE`.

El backend SDL solo difiere de PC bajo `#ifdef __vita__` (macro definida por el compilador de
VitaSDK): ventana 960×544 con los 320×240 del motor escalados a 640×480 centrados, rutas por
defecto `ux0:data/snoot/` (datos) y `ux0:data/snoot/save` (partidas), `mkdir` POSIX, flush de
stdout y `SDL_SetMainReady()` (el `main` es el del motor, no el de SDL2).

## Instalación y ejecución

1. Copiar `build/vita/snoot.vpk` a la PS Vita (o a Vita3K) e instalarlo con VitaShell.
2. Colocar los archivos del disco de PS1 en `ux0:data/snoot/` (los genera
   `python -m tools.ctl run --target ps1 --scenario tests/scenarios/snoot-smoke.yaml`
   en `build/ctl/ps1/disc/`).
3. Lanzar el bubble "Snoot Game".

Para probar en Vita3K: abrir el VPK con el emulador; Vita3K carga el `eboot.bin` y el
`param.sfo` del paquete.

## Console Test Lab (`tools/ctl/vita.py`, T-608)

El adapter `tools/ctl/vita.py` automatiza la configuración de Vita3K y la ejecución de escenarios:

- **Instalación de firmware:** `--firmware <archivo.pup>` instala `PSVUPDAT.PUP` y `PSP2UPDAT-preinst.PUP` (`Vita3K.exe --help`).
- **Instalación y auto-arranque del VPK:** argumento posicional `content-path` (`Vita3K.exe --help`).
- **Directorio de datos aislado:** `-c <config.yml>` con la directiva `pref-path:` en el archivo YAML de configuración (`Vita3K.exe --help`).
- **Cierre automático:** `--frontend sdl` ejecuta la aplicación en ventana independiente y finaliza con ella (`Vita3K.exe --help`).
- **Captura de traza/printf:** `-l 0` (nivel TRACE en CLI y `log-level: 0` en YAML) registra los accesos a terminal en `|T| [write_file]: *** TTY: <texto>` (`Vita3K.exe --help` e implementación de `write_file` en `iofilemgr.cpp`).

### Renderizado GXM sin `libshacccg.suprx` (T-612)

El paquete `sdl2` preinstalado en la imagen Docker (`vdpm/vitasdk-packages`) viene compilado con `-DHAVE_VITAGL=ON`, lo que obliga a enlazar con `vitaGL` (`-lvitaGL -lvitashark -lSceShaccCgExt`) y a requerir el compilador de shaders dinámico propietario `ur0:data/libshacccg.suprx`.

Para eliminar esta dependencia por completo:
- Se compila SDL2 2.32.10 (`release-2.32.10`) desde su fuente oficial dentro del contenedor usando `vita.toolchain.cmake` con destino en `build/vita/sdl2/`.
- El renderer oficial `VITA gxm` de SDL2 (`src/render/vitagxm/SDL_render_vita_gxm.c`) utiliza shaders precompilados en formato GXP (`SDL_render_vita_gxm_shaders.h`), operando directamente sobre la API nativa SceGxm de Sony sin runtime shader compiler.
- `platforms/vita/Makefile` enlaza directamente contra `$(OUT)/sdl2/lib/pkgconfig/sdl2.pc`, eliminando `-lvitaGL`, `-lvitashark`, `-lSceShaccCgExt` y `-ltaihen_stub`.
- `platforms/sdl/sdl_target.h` define `SDL_SetHint(SDL_HINT_RENDER_DRIVER, "VITA gxm")` en `SDL_SetMainReady()`.
- Se añade `vita_flush()` sobre `__getreent()->_stdout` para vaciar los buffers stdio de newlib en entornos multihilo, y `SDL_QuitSubSystem(SDL_INIT_AUDIO)` en `atexit` para cerrar el hilo de audio antes del desmontaje de memoria, evitando fallos de acceso en emuladores como Vita3K.
- Con esta configuración, `build/vita/snoot.vpk` arranca tanto en emulación (Vita3K) como en hardware real sin necesidad de `libshacccg.suprx`, pasando los escenarios de regresión con `verdict: PASS`.

## Observaciones

- `*.vpk`, `*.elf`, `*.velf` y `*.bin` están ignorados por `.gitignore`.
- El VPK incluye los recursos de LiveArea copiados de la muestra de VitaSDK
  (`sce_sys/`); sustituirlos por arte propio antes de publicar.
