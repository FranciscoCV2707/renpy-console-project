# Nintendo 3DS — Toolchain Docker

## Imagen Docker

- Imagen: `devkitpro/devkitarm@sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5`
- Etiqueta de origen: `devkitpro/devkitarm:latest`
- Digest: `sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5`
- Tamaño: ~512 MB
- Comprobar localmente:

```sh
docker pull devkitpro/devkitarm@sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5
docker inspect --format "{{index .RepoDigests 0}}" devkitpro/devkitarm:latest
```

## Toolchain incluido

- Compilador: `arm-none-eabi-gcc (GCC) 16.1.0` (`/opt/devkitpro/devkitARM/bin/`).
- SDK 3DS: libctru en `/opt/devkitpro/libctru` (más citro3d).
- La imagen trae SDL 1.2 (`3ds-sdl`), **no** SDL2. El backend `platforms/sdl/` usa SDL2, por lo que
  `platforms/3ds/build.py` compila SDL2 2.32.10 desde el repositorio oficial
  (`https://github.com/libsdl-org/SDL`, tag `release-2.32.10`) en el primer arranque y cachea el resultado en
  `build/3ds/sdl2`. El tag está fijado en el script para que la compilación sea reproducible.
- Empaquetado: `3dsxtool` (en `/opt/devkitpro/tools/bin`) convierte el ELF en `.3dsx`.
- `make` y `cmake` incluidos.

## Compilación

```sh
E:/Dev/renpy-console-project/.venv/Scripts/python.exe platforms/3ds/build.py --trace
```

Salida: `build/3ds/snoot.3dsx`. La primera ejecución descarga y compila SDL2 (varios minutos); las siguientes
reutilizan `build/3ds/sdl2`.

En Windows (PowerShell) no hace falta `MSYS_NO_PATHCONV=1`: el script invoca Docker desde Python.

## Pantalla y datos

- Pantalla superior: 400×240; los 320×240 de PS1 se centran sin escalar. La pantalla inferior queda libre.
- Los datos se leen de `sdmc:/3ds/snoot/data/` (o de `VN_DATA_DIR` si está definido). Copia ahí el contenido de
  `build/ctl/ps1/disc/`.
- Entrada: los botones del 3DS se traducen a `BTN_*` vía la capa SDL2 (gamecontroller/teclado).

## Instalación

Copia `snoot.3dsx` (y, si se genera, el `.smdh`) a la tarjeta SD en `/3ds/snoot/` y ejecútalo con el Homebrew
Launcher. También puede probarse en Azahar (antes Citra).

## Cómo se prueba (Console Test Lab, T-610)

```
$ E:\Dev\renpy-console-project\.venv\Scripts\python.exe -m tools.ctl run --target 3ds --scenario tests/scenarios/snoot-route-chapter_x2.yaml
```

Requisito: los datos del disco de PS1 en `build/ctl/ps1/disc/` (los deja
`python -m tools.ctl run --target ps1 --scenario tests/scenarios/snoot-smoke.yaml`).

`tools/ctl/n3ds.py` copia Azahar (`E:\snoot\azahar-2126.2\azahar-windows-msvc-2126.2`) a
`build/ctl/3ds/azahar/`, crea la SD virtual en `user/sdmc/3ds/snoot/data` (disco de PS1 más
el `AUTOTEST.BIN` del escenario), parchea `user/config/qt-config.ini` (filtro de log
`*:Debug` y RPC activado) y arranca `build/3ds/snoot.3dsx` pasándolo como último argumento.

### Opciones de Azahar usadas, con su fuente (2126.2)

- **Arrancar un `.3dsx`**: la ruta va como último argumento sin guion ("Launch game at path");
  el resto de opciones son `-d/--dump-video`, `-f/--fullscreen`, `-g/--gdbport`, `-h/--help`,
  `-i/--install`, `-p/--movie-play`, `-r/--movie-record`, `-a/--movie-record-author`,
  `-m/--multiplayer` (no implementado), `-v/--version`, `-w/--windowed`
  (src/citra_qt/citra_qt.cpp, `GMainWindow::GMainWindow`). `-h` muestra un diálogo Qt
  (`ShowCommandOutput`), no imprime en consola: no sirve para averiguar esto sin interfaz.
- **Carpeta de usuario propia**: en Windows Azahar usa `<carpeta del exe>/user` si existe
  ("local user directory"; src/common/file_util.cpp, `SetUserPath`), así que la copia dentro
  de `build/` queda aislada del usuario real. La SD virtual es `user/sdmc` (claves
  `sdmc_directory`/`nand_directory` del ini; core/file_sys/archive_sdmc.cpp) y ahí es donde el
  juego lee `sdmc:/3ds/snoot/data` (`platforms/sdl/sdl_target.h`).
- **Log en archivo**: siempre escribe `<user>/log/azahar_log.txt` (src/common/logging/backend.cpp,
  `FileBackend`); el filtro por defecto es `*:Info` (src/common/settings.h), que oculta las
  líneas `Debug.Emulated`, así que el adapter pone `log_filter=*:Debug`. Cada clave del
  `qt-config.ini` lleva una línea `<clave>\default=<bool>`: con `\default=true` Azahar ignora
  el valor y lo reescribe al arrancar; por eso el adapter también fija `\default=false`.
- **Cerrar al terminar**: Azahar vuelve a su lista al terminar el juego y no se cierra solo;
  como en PSP/PPSSPP, el adapter espera la marca de fin y corta el proceso con
  `taskkill /PID <pid> /T /F`.
- **RPC (captura del título)**: `enable_rpc_server=true` en `[Debugging]` abre el servidor UDP
  45987 (src/core/rpc/rpc_server.cpp); el cliente `scripting/AzaharRPC.py` del propio Azahar
  toma capturas PNG (`screenshot()`).

### Canal de traza (T-619)

- Azahar solo recibe por log lo que el juego manda con `svcOutputDebugString`
  (`Kernel::SVC::OutputDebugString` lo escribe como `Debug.Emulated`; src/core/hle/kernel/svc.cpp), y
  libctru descarta `stdout`/`stderr` mientras no haya un `consoleInit` (verificado en T-610 con un
  `.3dsx` de prueba). Por eso el bloque de 3DS de `platforms/sdl/sdl_target.h` instala un devoptab
  propio de stdout (`ctr_svc_write`) que manda cada línea a `svcOutputDebugString`, activado en
  `SDL_TARGET_PREPARE_IOP`; `SDL_TARGET_QUIT_MARKER` imprime `VN_QUIT` por ese mismo canal y
  `tools/ctl/n3ds.py` corta Azahar al verlo.
- Salida de ejemplo del log (`user/log/azahar_log.txt`):
  `Debug.Emulated <Debug> ...OutputDebugString:1190: T|1|0|SAY|who=1`.
- El buffer del log de Azahar es de 4 KB y no se vacía al terminar el juego: las últimas líneas
  (`END|` y `VN_QUIT`) a veces no llegan al archivo antes de que el adapter corte el proceso, así que
  el corte puede esperar los `max_seconds` del escenario. El veredicto no se afecta (la traza ya
  tiene todos los eventos `SAY`), pero conviene revisarlo si algún día importa el tiempo de corrida.

### Capturas del AUTOTEST (T-619)

- El bloque de 3DS fija `VN_SHOT_DIR=sdmc:/3ds/snoot` y lee `VN_SHOT_NAMES` de
  `sdmc:/3ds/snoot/shot_names.txt` (el mismo patrón que Vita: en 3DS no hay variables de entorno del
  SO). `tools/ctl/n3ds.py` escribe ese archivo con los pasos `shot` del escenario y copia los BMP a
  `build/ctl/3ds/`.
- Captura por RPC (`scripting/AzaharRPC.py`, UDP 45987, `enable_rpc_server=true`): la pantalla
  superior muestra el título de Snoot y la inferior queda en negro (el backend solo usa la superior).
  El negro de T-610 era un problema de momento de la captura, no del render.

## Lo que falta

- Perfil de recursos de 3DS en `tools/assetpipe` (T-506).
- Audio por duración (D18) y FMV sin decidir para 3DS.

## Notas

- La imagen no incluye `3ds-sdl2`; por eso se compila SDL2 desde fuente. Si en una versión futura de
  devkitPro aparece `3ds-sdl2` en `dkp-pacman`, puede sustituirse la descarga por el paquete oficial.
- `build/3ds/sdl2*` está ignorado por `.gitignore` (binarios generados).
