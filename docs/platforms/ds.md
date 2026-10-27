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
- Captura de las dos pantallas: `platforms/ds/capture.py`. Como melonDS 1.1 no captura por CLI, el script captura el
  área cliente con `PrintWindow` (PW_CLIENTONLY). La barra de menú de melonDS 1.1 se dibuja dentro del área cliente
  (Qt) y su alto no es el que melonDS reserva al crear la ventana: en este anfitrión mide 53 px, no 22, así que el
  tamaño por defecto (256×406) corta 31 filas de la pantalla inferior. El alto se mide en cada captura: al arranque
  ambas pantallas son negras y la barra es clara, así que la primera fila oscura del cliente es el inicio de la
  pantalla superior; con esa medida se agranda la ventana a cliente 256×(barra+384) y las pantallas quedan
  exactamente en las últimas 384 filas, que es lo que se recorta. Salida: `build/ds/snoot-screens.png`
  (arriba 256×192, debajo 256×192, sin barra ni marco).
- Para capturar un momento concreto de un diálogo se usa un AUTOTEST con pasos absolutos (`steps` del escenario,
  `tools/ctl/autotest.py`): compilar con `build(trace=True, autotest_path=...)` (la traza mide el momento: tras
  `SCENE|img=...` llega el `SAY` con fondo), dejar que el guion agote las pulsaciones y capturar la ventana con el
  recorte de arriba. En chapter_x2, 24 `press CROSS` a 45 cuadros desde el 800 dejan el juego en el SAY 13
  (`who=3;text=13290`, fondo `img=293`), confirmado leyendo `sd/trace.txt` tras cerrar melonDS.
- Ojo con el DLDI: `cd_find` prueba `nitro:/` y luego `fat:/`, y melonDS sincroniza la carpeta `[DLDI]` completa. Un
  `AUTOTEST.BIN` viejo que quede en la carpeta de la SD hace que la ROM "limpia" repita ese recorrido. Usa una
  carpeta vacía para el título.
- melonDS corre el juego a ~60 cuadros por segundo de tiempo real aunque `LimitFPS = false`: los pasos absolutos
  están en cuadros del juego, así que un recorrido de 2000 cuadros tarda ~33 s de reloj, no instantáneo.

## Traza por DLDI en melonDS 1.1 (T-709)

melonDS 1.1 no implementa la consola de depuración del puerto NO$GBA (0x04FFFA1C) en el ARM9 (GitHub Issue #2374).
Para la extracción automatizada de trazas en `tools.ctl`:
- La ROM usa `libfat` (`fatInitDefault()`) de BlocksDS para inicializar el driver DLDI.
- Las líneas del protocolo `TRACE` se escriben a `fat:/trace.txt` por `vn_ops->log`.
- `melonDS.toml` configura la sincronización de carpeta en la sección `[DLDI]`:
  `Enable = true`, `FolderSync = true`, `FolderPath = "<sd>"`, `ImagePath = "<dldi.bin>"`, `ReadOnly = false`, `ImageSize = 1`.
- Al terminar el recorrido o alcanzar `autotest_quit`, el ejecutable cierra la traza y emite `fat:/done.txt`.
- El arnés cierra melonDS limpiamente con el mensaje Win32 `WM_CLOSE`, lo cual desencadena el volcado de `FolderSync` hacia `<sd>/trace.txt` en el disco anfitrión.

## Prueba

`tests/test_ds_build.py` (marcada `consoles`) corre `platforms/ds/build.py` y comprueba que queda
`build/ds/snoot.nds`:

```
E:/Dev/renpy-console-project/.venv/Scripts/python.exe -m pytest -m consoles -k ds
```

Y el escenario de prueba de traza en melonDS:

```
E:/Dev/renpy-console-project/.venv/Scripts/python.exe -m tools.ctl run --target ds --scenario tests/scenarios/snoot-route-chapter_x2.yaml
```
