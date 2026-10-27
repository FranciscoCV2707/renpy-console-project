# Nintendo DS — demake (nivel C, T-706)

`PLAN.md` D19: fondo arriba (256×192, 16 bits), texto abajo, sprites reducidos, música ADPCM 22 kHz mono, sin
video. Esta página describe la primera ROM mínima (`build/ds/snoot.nds`): fondo de Snoot en la pantalla de arriba
y una línea de texto en español en la de abajo, con fuente propia. Todavía no corre el guion.

## Toolchain

- BlocksDS v1.24.0 (libnds + ndstool) en Docker. Imagen oficial `skylyrac/blocksds` (documentación:
  [Docker – BlocksDS](https://blocksds.github.io/docs/setup/docker/)), fijada por digest:
  `skylyrac/blocksds@sha256:779f6193d1030c62e60d1f0f39c3e32cf4045c0bd224a45c0ceadf9d9ab01a51`
  (tag `slim-latest`, `linux/amd64`).
- En el contenedor el SDK está en `/opt/wonderful/thirdparty/blocksds/core` (la variable `BLOCKSDS` ya viene
  puesta en el entorno).
- `platforms/ds/Makefile` incluye el Makefile de referencia de BlocksDS
  (`$BLOCKSDS/sys/default_makefiles/rom_arm9/Makefile`): compila con `arm-none-eabi-gcc`
  (`-mthumb -mcpu=arm946e-s+nofp`, `-specs=$BLOCKSDS/sys/crts/ds_arm9.specs`), enlaza `-lnds9 -lc` y arma el ROM
  con `ndstool` (`-7 <arm7> -9 <arm9>`). El ARM7 es el core mínimo de BlocksDS
  (`$BLOCKSDS/sys/arm7/main_core/arm7_minimal.elf`), suficiente porque esta ROM no usa audio ni Wi-Fi.

## Compilación

```
E:/Dev/renpy-console-project/.venv/Scripts/python.exe platforms/ds/build.py
```

`platforms/ds/build.py` copia `Makefile`, `source/` y `assets/` a `build/ds/work/`, corre `make` dentro del
contenedor y deja el ROM en `build/ds/snoot.nds`.

## Recursos

- `platforms/ds/convert_bg.py` convierte un fondo de `E:/snoot/snootgame/game/images/backgrounds` a
  `platforms/ds/assets/bg_sample.bin`: 256×192, un píxel de 16 bits por punto con BGR555 (bits 0-4 rojo, 5-9
  verde, 10-14 azul) y el bit 15 en 1. En el modo bitmap de la DS el bit 15 es el de opacidad: los valores son
  `aBBBBBGGGGGRRRRR` y sin `a` el píxel se ve transparente (`BgType_Bmp16`, `nds/arm9/background.h`).
  La conversión es determinista (LANCZOS a 256×192, sin cuantizar); el binario generado se versiona.
- El fondo se embebe con `bin2c` (regla `BINDIRS` del Makefile de referencia): `bg_sample_bin` y
  `bg_sample_bin_size` en `bg_sample_bin.h`.
- `source/font.c` es la fuente propia de la tarea: glifos de 8×8 (5 columnas útiles, avance de 6 píxeles) con los
  caracteres de la línea que se muestra. El espacio y los caracteres sin glifo no se dibujan.

## ROM mínima (`source/main.c`)

- Pantalla de arriba (motor principal): `videoSetMode(MODE_5_2D)`, `vramSetBankA(VRAM_A_MAIN_BG)`, fondo 3 en
  `BgType_Bmp16` / `BgSize_B16_256x256`; las 256×192 primeras filas del bitmap se copian con `dmaCopy`.
- Pantalla de abajo (motor secundario): `videoSetModeSub(MODE_5_2D)`, `vramSetBankC(VRAM_C_SUB_BG)`, fondo azul
  `ARGB16(1, 4, 6, 12)` y la línea "Hola desde Snoot Game" en blanco con `font_draw_text`.
- Bucle de juego: `swiWaitForVBlank()` para siempre.
- APIs de libnds verificadas en los headers de la imagen: `videoSetMode`/`videoSetModeSub`/`MODE_5_2D`
  (`nds/arm9/video.h:562,652,661`), `vramSetBankA`/`vramSetBankC` (`nds/arm9/video.h:407,429`),
  `VRAM_A_MAIN_BG`/`VRAM_C_SUB_BG` (`nds/arm9/video.h:140,186`), `RGB15`/`ARGB16` (`nds/arm9/video.h:110,116`),
  `bgInit`/`bgInitSub` (`nds/arm9/background.h:639,719`), `BgType_Bmp16`/`BgSize_B16_256x256`
  (`nds/arm9/background.h:492,524`), `bgGetGfxPtr` (`nds/arm9/background.h:949`), `dmaCopy` (`nds/dma.h:200`),
  `swiWaitForVBlank` (`nds/interrupts.h:343`).

## Emulador: melonDS 1.1

- Instalado en `E:/snoot/melonds-1.1/melonDS.exe` (sin BIOS ni firmware externos).
- Línea de comandos (salida real de `melonDS.exe --help`): `melonDS [options] nds gba`, con
  `-b, --boot <auto/always/never>`, `-f, --fullscreen` y `-a, --archive-file <rom>`. No hay opción de captura
  por CLI (verificado con `--help` y `--help-all`).
- Arranque: `melonDS.exe build/ds/snoot.nds` (boot directo al pasar un ROM, la opción `auto`). El README de
  melonDS dice que solo el arranque por firmware ("Firmware boot (not direct boot)") exige volcados de
  BIOS/firmware de una DS original; el boot directo no los necesita.
- FreeBIOS: melonDS trae integrado el BIOS libre para homebrew (clave `Emu.ExternalBIOSEnable` de
  `melonDS.ini`, que solo hace falta activar para usar BIOS externos). Referencias:
  - Notas de la versión 1.0 RC: "fix DS/GBA comm not working when using FreeBIOS"
    (<https://github.com/melonDS-emu/melonDS/releases/tag/1.0rc>).
  - PR #2523: "The open DSi BIOS is derived from a modified build of FreeBIOS"
    (<https://github.com/melonDS-emu/melonDS/pull/2523>).
  - README: <https://github.com/melonDS-emu/melonDS#how-to-use> ("Firmware boot (not direct boot) requires a
    BIOS/firmware dump from an original DS or DS Lite").
- Captura de las dos pantallas: `platforms/ds/capture.py`. Como melonDS 1.1 no captura por CLI, el script trae
  la ventana al frente, captura con `PIL.ImageGrab` y recorta las dos pantallas localizando la de abajo por su
  color de fondo (layout por defecto: vertical, sin hueco, escala 1:1). Salida: `build/ds/snoot-screens.png`
  (arriba 256×192, debajo 256×192).

## Prueba

`tests/test_ds_build.py` (marcada `consoles`) corre `platforms/ds/build.py` y comprueba que queda
`build/ds/snoot.nds`:

```
E:/Dev/renpy-console-project/.venv/Scripts/python.exe -m pytest -m consoles -k ds
```
