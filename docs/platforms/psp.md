# PSP (T-501)

## Cómo se compila (PSn00bSDK no aplica: aquí es pspsdk/pspdev, 2026-09)

### Con Docker (lo que usa `platforms/psp/build.py`)

```
$ E:\Dev\renpy-console-project\.venv\Scripts\python.exe platforms\psp\build.py --trace
E:\Dev\renpy-console-wt\T-501-kilo\build\psp\EBOOT.PBP
```

- Imagen: `pspdev/pspdev@sha256:54895e6f5afb71b8f4f6915ee6d5023e1e087ca7afdf2dcb1d7a694a5233e45f`
  (pspdev/pspdev:latest, digest del 2026-08-08).
- El repo se monta en `/src` y `make -f /src/platforms/psp/Makefile` compila `engine/core`, `engine/app`,
  `engine/modules`, `games/snoot` y `platforms/sdl` con `psp-gcc` + SDL2 (`psp-pkg-config sdl2`), arma
  `build/psp/generated/game_config.h` y deja el `EBOOT.PBP` en `build/psp/`. Con `--trace` añade `-DVN_TRACE`.
- El `main` de la app es el del motor, así que no se enlaza `libSDL2main` (su `main` llamaría a `SDL_main`);
  `platforms/sdl/backend_sdl.c` define `PSP_MODULE_INFO` y `sce_newlib_stack_kb_size` (1 MB de pila para
  `user_main`, símbolo débil del `crt0` de pspsdk) bajo `#ifdef __PSP__`.
- `platforms/sdl` solo difiere de PC bajo `#ifdef __PSP__`: ventana 480×272 con los 320×240 del motor escalados a
  360×272 centrados, rutas por defecto `ms0:/PSP/GAME/SNOOT/DATA` (datos) y `.../SAVE` (partidas), `mkdir` POSIX,
  flush de stdout y sin `SDL_GameController`.

### El hola-mundo (referencia mínima)

```
$ MSYS_NO_PATHCONV=1 docker run --rm -v "E:/Dev/renpy-console-wt/T-501-kilo:/src" -w /src/platforms/psp/hello pspdev/pspdev@sha256:54895e6f5afb71b8f4f6915ee6d5023e1e087ca7afdf2dcb1d7a694a5233e45f make
```

(`MSYS_NO_PATHCONV=1` evita que Git Bash convierta `/src` en `C:/Program Files/Git/src`.)

Sin Docker, el mismo Makefile vale con el toolchain local, añadiendo `$(PSPSDK)/lib/build.mak`.

## Herramientas

- `pspdev/pspdev:latest`, GCC 15.2.0 + binutils 2.45 + Newlib 4.5.0 + gdb 17.1 + Python 3.12.13
  (`psp-gcc --version`, `psp-ld --version`, `psp-gdb --version`, `python3 --version`, agosto de 2026).
- SDL2 2.32.10 (`psp-pkg-config --modversion sdl2`, commit 67e1644). La biblioteca se deja precompilada en la
  imagen: `ccache` no sirve porque `CMakeLists.txt:23` de SDL2 hace un `return()` si `SDL2_DISABLE_SDL2MAIN` está
  activo y no permite rehacer solo los objetos. Además, `build.mak` define `PSPDEV=$(shell psp-config --pspdev-path)`
  y sus reglas tienen `:=`, así que se les puede pasar `PSPDEV=/ruta/otra` por línea de comandos.
- `psp-pkg-config --cflags --libs sdl2` y `include $(PSPSDK)/lib/build.mak` funcionan tal cual en una app nueva.

## Cómo se prueba (Console Test Lab)

```
$ E:\Dev\renpy-console-project\.venv\Scripts\python.exe -m tools.ctl run --target psp --scenario tests/scenarios/snoot-route-chapter_x2.yaml
```

Requisito: los datos del disco de PS1 en `build/ctl/ps1/disc/` (los deja
`python -m tools.ctl run --target ps1 --scenario tests/scenarios/snoot-smoke.yaml`).

`tools/ctl/psp.py` arma `build/ctl/psp/ms/PSP/GAME/SNOOT/` con el `EBOOT.PBP`, los datos del disco en `DATA/` y el
`AUTOTEST.BIN` del escenario, copia PPSSPP (`E:\snoot\ppsspp-1.20.4`) a `build/ctl/psp/ppsspp/`, corre el
emulador y saca `build/ctl/psp/trace.txt` de `build/ctl/psp/log.txt`.

### Opciones de PPSSPP usadas, con su fuente

- **Arrancar un `EBOOT.PBP` directo**: la ruta va como argumento sin opción. Fuente: `UI/NativeApp.cpp` de
  PPSSPP 1.20.4 ("This parameter should be a boot filename") y `Core/System.cpp` ("Booted %s..."); la guía
  oficial da por hecho el archivo que arranca un frontend
  (https://www.ppsspp.org/docs/reference/command-line, opción `--pause-menu-exit`).
- **`--log=FILE` y `--loglevel=N`**: escriben el log en un archivo y fijan su nivel; `N=4` es `LogLevel::LINFO`
  (`Common/Log.h`). Lo que el juego escribe por stdout/`printf` sale como `stdout: ...` porque `sceIoWrite` con
  fd 1 lo manda al log (`Core/HLE/sceIo.cpp`, `INFO_LOG(Log::Printf, ...)`). Fuentes:
  https://www.ppsspp.org/docs/reference/command-line y
  https://www.ppsspp.org/docs/troubleshooting/getting-log-output/
- **Carpeta como Memory Stick**: en 1.20.4 no existe `--memstick` (llega en 1.21; misma página de comandos). En
  Windows la carpeta sale de `installed.txt` junto al ejecutable (una ruta por línea) o, si no existe, de
  `<carpeta del ejecutable>/memstick` (código: `Windows/main.cpp`, `InitMemstickDirectory`; `ms0:` se monta sobre
  esa carpeta en `Core/HLE/sceIo.cpp`, `__IoInit`). El adapter copia el emulador dentro de `build/` y escribe
  `installed.txt` con la ruta de `build/ctl/psp/ms`.
- **Cerrar al terminar**: `--pause-menu-exit` solo cambia "Exit to menu" por "Exit" en el menú de pausa
  (`UI/PauseScreen.cpp`, `GamePauseScreen::OnExit`; la propia documentación avisa: "Before PPSSPP 1.21, only the
  pause menu choice exited"). Cuando el juego llama a `sceKernelExitGame`, PPSSPP escribe `SELF-POWERDOWN!`
  (`UI/EmuScreen.cpp`, `checkPowerDown`) y vuelve a su menú sin cerrar; el adapter espera esa marca y termina el
  proceso con `taskkill /PID <pid> /T /F`.

## Observaciones del puerto

- `platforms/psp/hello/main.c` no define `PSP_MODULE_INFO`: lo aporta `libSDL2main`. Como aquí el `main` es el
  del motor, `platforms/sdl/backend_sdl.c` lo define bajo `#ifdef __PSP__` y el Makefile filtra `-lSDL2main`.
- `platforms/sdl/save.c` usa el `mkdir` de un argumento de MinGW; en PSP el de newlib es `mkdir(path, mode)`.
- En una PSP real el cable USB es para la Memory Stick (`usb_device`); para los periféricos va `usbhost0:`
  (`docs/psp/PR.md`, notas de limitaciones).
- PR descubierto tarde (entregable D20 de PS2, no está en main): `platforms/psp/hello/main.c` compila un
  `EBOOT.PBP` con SDL2 2.32.10 en la imagen de pspdev; ventana 480×272, fondo de color, botón para salir. Los
  datos de PS1 con nombres de 8.3 van bien en `ms0:`, pero la imagen `MUSIC.XA` (unos 200 MB) no cabe entera en
  la RAM de la PSP: hay que partirlo antes de meter música.
