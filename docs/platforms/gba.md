# Game Boy Advance — Toolchain Docker

## Imagen Docker

- Imagen: `devkitpro/devkitarm@sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5`
- Etiqueta de origen: `devkitpro/devkitarm:latest`
- Digest: `sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5`
- Tamaño: ~512 MB
- Comprobar localmente:

```sh
docker pull devkitpro/devkitarm@sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5
```

## Toolchain incluido

- Compilador: `arm-none-eabi-gcc (GCC) 16.1.0` (`/opt/devkitpro/devkitARM/bin/`).
- SDK GBA: **libtonc 1.4.5** en `/opt/devkitpro/libtonc` (cabeceras en
  `/opt/devkitpro/libtonc/include`, biblioteca en `/opt/devkitpro/libtonc/lib/libtonc.a`).
  Se usa libtonc por macros de registros GBA y funciones DMA (`dma3_cpy`).
- Empaquetado: `gbafix` (en `/opt/devkitpro/tools/bin`) corrige la cabecera del ROM.
- `make` y `cmake` incluidos.

## Compilación

```sh
E:/Dev/renpy-console-project/.venv/Scripts/python.exe platforms/gba/build.py
```

Salida: `build/gba/snoot.gba`. Los recursos de juego (`build/ctl/ps1/disc`) se empaquetan en
formato GBFS v1 alineado a 256 bytes y se anexan a la ROM.

## Hardware y arquitectura del backend

- Modo de video 3: 240×160 píxeles, 16 bpp BGR555 directo (GBATEK, "Video Mode 3").
- Framebuffer doble: `gba_backbuffer` en EWRAM renderiza capas por orden z; en VBlank se copia a `vid_mem` (`0x06000000`) vía DMA3 (`dma3_cpy`).
- Layout de pantalla (D19): 240×160. Escena y sprites arriba (y=0..111), caja de diálogo translúcida abajo (y=112..159).
- Memoria RAM: 256 KB EWRAM + 32 KB IWRAM. El núcleo compartido (`engine/core` + `engine/app`) cabe completamente: ~176 KB bss en EWRAM (67%) y ~6.5 KB en IWRAM (20%), con ~85 KB libres para heap y pila.
- Gestión de imágenes (D25): carga bajo demanda en `res_get` y liberación inmediata al dejar de verse (cambio de escena en `res_new_scene`, o `HIDE`/cambio de expresión en `res_tick`).

## Emulador y traza para verificar

- mGBA 0.10.5 en `E:\snoot\mgba-0.10.5\mGBA-0.10.5-win64\`.
- Traza de depuración: canal homebrew de mGBA usando registros de I/O `REG_DEBUG_*` (0x4FFF600-0x4FFF780).
- Ejecución CLI sin interfaz: `mgba-sdl.exe` con `-C fastForward=1 -C audioSync=0 -C videoSync=0 -C fpsTarget=0 -C logToFile=1 -C logFile=<ruta> -l 31`.
- Integración con `tools/ctl`: adapter `tools/ctl/gba.py` implementa `run_scenario` y extrae las líneas `T|` para comparar con la referencia.

## Lo que falta

- Audio (FIFO PCM / timers).
- Recursos comprimidos específicos de GBA (`tools/demake/gba_pack.py`).
- Perfil de recursos de GBA en `tools/assetpipe` (T-506).
