# Wii — Toolchain Docker

## Imagen Docker

- Imagen: `devkitpro/devkitppc@sha256:d50f8a886f2ce1d3c22685a774afb0845379876b47d9b41a9b729f4f63a54813`
- Etiqueta de origen: `devkitpro/devkitppc:latest`
- Digest: `sha256:d50f8a886f2ce1d3c22685a774afb0845379876b47d9b41a9b729f4f63a54813`
- Comprobar localmente:

```sh
docker pull devkitpro/devkitppc@sha256:d50f8a886f2ce1d3c22685a774afb0845379876b47d9b41a9b729f4f63a54813
docker inspect --format "{{index .RepoDigests 0}}" devkitpro/devkitppc:latest
```

## Toolchain incluido

- Compilador: `powerpc-eabi-gcc (devkitPPC) 16.2.0` (`/opt/devkitpro/devkitPPC/bin/`).
- `make` ya está en la imagen; no hace falta instalarlo.
- Macro de plataforma: `-D__WII__` (la define `wiivars.sh` con `CPPFLAGS=-D__WII__ ...`); por eso en `platforms/sdl` se usa `#ifdef __WII__`.
- SDL2 2.28.5 para Wii: paquete `wii-sdl2` (`wii-sdl2 2.28.5-17`, `dkp-pacman -Ss wii-sdl2`), en `/opt/devkitpro/portlibs/wii` (`sdl2-config` y `sdl2.pc`). También están `wii-sdl2_image`, `wii-sdl2_mixer`, `wii-sdl2_ttf` y `wii-sdl2_gfx`.
- libogc 3.2.1 (`libogc 3.2.1-1`, `dkp-pacman -Ss libogc`), en `/opt/devkitpro/libogc`.
- Conversión ELF → DOL: `elf2dol` en `/opt/devkitpro/tools/bin/`.

## Cómo se compila

```sh
E:/Dev/renpy-console-project/.venv/Scripts/python.exe platforms/wii/build.py --trace
```

Genera `build/wii/boot.dol` y `build/wii/meta.xml`. Con `--trace` define `VN_TRACE`. El backend SDL se ajusta para Wii bajo `#ifdef __WII__`: ventana 640×480, rutas por defecto `sd:/apps/snoot/data` (lectura) y `sd:/apps/snoot/save` (partidas), `fatInitDefault()` al arrancar y `mkdir` con modo POSIX.

## Cómo se instala (consola o Dolphin)

- Copiar `build/wii/boot.dol` y `build/wii/meta.xml` a `sd:/apps/snoot/` en la tarjeta SD. Los datos del disco de PS1 van en `sd:/apps/snoot/data/`.
- En Dolphin, cargar `boot.dol` con `-b -e <archivo>` (flags verificados con `Dolphin.exe --help` de `E:\snoot\dolphin-2609a`). Dolphin emula la SD a partir de la imagen cruda
  configurada (`Dolphin.General.WiiSDCardPath`; por defecto `<user>/Load/WiiSD.raw`).

## Automatización con `tools/ctl` (T-611)

`python -m tools.ctl run --target wii --scenario <escenario>` hace todo con el Dolphin de
`E:\snoot\dolphin-2609a\Dolphin-x64\` (portable: no instala nada, toda su configuración va en la
carpeta `-u <user>` bajo `build/ctl/wii/user/`). Opciones verificadas (`Dolphin.exe --help` y el
código fuente de dolphin-emu en GitHub, rama master):

- `-u <dir>`: user folder aislado (lo documentan también `--help` y `UICommon/CommandLineParse.cpp`).
- `-b -e <dol>`: modo batch sin interfaz (`--help`: "Run Dolphin without the user interface
  (Requires --exec or --nand-title)"); `CommandLineParse.cpp` desactiva render-to-main en batch.
- `-C <System>.<Section>.<Key>=<Value>`: override de configuración; `System::Main` se llama
  "Dolphin" (`Common/Config/Config.cpp`, `system_to_name`). Claves de la SD (`Core/Config/MainSettings.cpp`):
  `Dolphin.Core.WiiSDCard` (por defecto `true`), `Dolphin.Core.WiiSDCardEnableFolderSync`,
  `Dolphin.Core.WiiSDCardFilesize` (en **bytes**; 0 = 128 MiB), `Dolphin.Core.WiiSDCardAllowWrites`.
  La carpeta de sincronización por defecto es `<user>/Load/WiiSDSync` (la crea Dolphin;
  `DolphinQt/Settings/WiiPane.cpp` la liga con `D_WIISDCARDSYNCFOLDER_IDX`); Dolphin la empaqueta en
  `WiiSD.raw` "when starting and ending emulation" (tooltip de la GUI). Con 222 MB de datos del
  disco PS1 hay que fijar `WiiSDCardFilesize` en 2 GiB.
- `Config/Dolphin.ini`: `[Analytics] PermissionAsked = True` evita el diálogo "Allow Usage
  Statistics Reporting" que bloquea el arranque en batch; `[Interface] ConfirmStop = False` evita
  la confirmación al detener.
- Logging por overrides `-C Logger.*`: descartado (T-617). En libogc 3.2.1 `printf`/`puts` van a la
  consola GX (`__console_write` de `libogc/console.c`), no a OSReport, asi que `dolphin.log` sale
  vacio y esa via no puede transportar las lineas `T|`.

## Traza por el USB Gecko (T-617)

El stdout del juego viaja por el USB Gecko emulado y `tools/ctl/wii.py` lo lee por TCP:

- `-C Dolphin.Core.SerialPort2=7`: adjunta el dispositivo gecko (`EXIDeviceType::Gecko` = 7 en
  `EXI_Device.h`) al canal EXI 2 (`EXI.cpp`: `Slot::SP2` mapea al canal 2, device 0).
- Dolphin abre un servidor TCP en 0xd6ec = 55020 (`EXI_DeviceGecko.cpp`, `GeckoConnectionWaiter`:
  "USBGecko: Listening on TCP {}", probando 55020+ si esta ocupado) y reenvia al primer cliente lo
  que el gecko manda por `CMD_SEND`.
- El bloque de Wii de `platforms/sdl/sdl_target.h` instala un devoptab propio de stdout que escribe
  con `usb_sendbuffer(2, ...)`: el canal 2 funciona sin sondeo porque `libogc/exi.c` responde
  "Always succeed for EXI2 as it has no probe line" (`__exi_probe`), mientras que `CON_EnableGecko`
  solo acepta 0/1 y el bit de insercion EXT de `EXI_STATUS` que Dolphin expone en esos canales solo
  se pone con un dispositivo en el device 1, asi que esa API siempre desactiva el gecko en Dolphin.
- `VN_QUIT` (macro `SDL_TARGET_QUIT_MARKER`, igual que PS2): el `exit(0)` del AUTOTEST no cierra el
  batch de Dolphin; `wii.py` ve la marca en el TCP, corta el emulador y escribe `trace.txt` con las
  lineas `T|`.

## Bloqueo de arranque arreglado (T-617)

- SDL2-Wii sondea `KEYBOARD_GetEvent` en cada vuelta del pump (`SDL_ogckeyboard.c`) sin llamar nunca
  a `KEYBOARD_Init`: la cola estatica de libwiikeyboard queda a cero y `__lwp_queue_get` lee
  0x00000000 (Invalid read al primer `SDL_PumpEvents`). El bloque de Wii llama `KEYBOARD_Init(NULL)`
  en `SDL_TARGET_PREPARE_IOP`.
- `res_get` (`platforms/sdl/res.c`) ponia 180 KB en el stack y el hilo principal de libogc tiene
  128 KB (`s_mainStack`): el primer `SCENE` (carga de `I0001.IMG`) desbordaba sobre los stacks de
  BSS y crasheaba en `KTickTaskStop` con un puntero corrupto. El buffer es estatico.

## Pendientes de la plataforma

- Verificar el audio de SDL2 en Dolphin (sin `MUSIC.XA` en el disco de pruebas no hay musica XA; los
  efectos SPU se decodifican igual que en PC).
- Confirmar el mapeo de botones del Wiimote/Classic Controller a `BTN_*`; hoy se reutiliza el
  mapeo generico de SDL2.
- Las capturas `shot` del protocolo TRACE no salen por el backend Wii (no fija `VN_SHOT_DIR`, a
  diferencia de Vita en `platforms/sdl/sdl_target.h`); hay que usar capturas de la ventana de
  render de Dolphin.
