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

## Lo que falta para automatizar con `tools/ctl`

- Adapter `ctl` para 3DS/Azahar (captura de traza y capturas) no implementado en esta tarea.
- Perfil de recursos de 3DS en `tools/assetpipe` (T-506).
- Audio por duración (D18) y FMV sin decidir para 3DS.

## Notas

- La imagen no incluye `3ds-sdl2`; por eso se compila SDL2 desde fuente. Si en una versión futura de
  devkitPro aparece `3ds-sdl2` en `dkp-pacman`, puede sustituirse la descarga por el paquete oficial.
- `build/3ds/sdl2*` está ignorado por `.gitignore` (binarios generados).
