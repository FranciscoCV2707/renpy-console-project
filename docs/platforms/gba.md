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
  Se usa libtonc por su envoltura de llamadas BIOS (`tonc_bios.h`), incluida `LZ77UnCompVram`.
- Empaquetado: `gbafix` (en `/opt/devkitpro/tools/bin`) corrige la cabecera del ROM.
- `make` y `cmake` incluidos.

## Compilación

```sh
E:/Dev/renpy-console-project/.venv/Scripts/python.exe -m tools.demake.gba_pack --game E:/snoot/snootgame/game --out build/demake/gba/assets
E:/Dev/renpy-console-project/.venv/Scripts/python.exe platforms/gba/build.py
```

Salida: `build/gba/snoot.gba`. El fondo se toma del primer archivo de `build/demake/gba/assets/bg/*.bin`
(generado por `gba_pack.py`).

## Hardware y descompresión

- Modo de video 4: 240×160, 8 bpp (un índice de color por píxel), paleta de 256 colores BGR555
  (GBATEK, "Video Mode 4").
- El fondo comprimido se descomprime en VRAM con la llamada BIOS `LZ77UnCompVram` (SWI 12h, GBATEK
  "BIOS Decompression Functions"); el formato es LZ77 tipo 0x10 con ventana de 4096 bytes.
- La paleta BGR555 sigue al flujo comprimido en el mismo archivo y se copia a `MEM_PAL`.
- Fuente propia de 8×8 embebida en `platforms/gba/main.c`; el texto se dibuja píxel a píxel en el
  framebuffer de modo 4.

## Emulador para verificar

- mGBA 0.10.5 en `E:\snoot\mgba-0.10.5\mGBA-0.10.5-win64\`.
- Ejecución sin interfaz: `mgba-sdl.exe` con un script Lua pasado mediante `-C script=<ruta>` (mGBA 0.10
  expone `emu:screenshot()` y el callback `frame` en su API de scripting; ver
  https://mgba.io/docs/scripting.html). El script guarda `screenshot()` tras unos fotogramas y el
  proceso se detiene después.
- Captura manual: menú "Tools → Scripting" en la interfaz gráfica y botón de captura.

## Lo que falta

- Entrada de botones, audio (FIFO PCM) y guardado: no incluidos en este ROM mínimo.
- Integración con `tools/ctl`: sin adapter todavía.
- Perfil de recursos de GBA en `tools/assetpipe` (T-506) y audio por duración (D18).
