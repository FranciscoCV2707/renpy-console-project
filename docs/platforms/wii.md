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
- Logging por overrides `-C Logger.Options.WriteToFile=True`, `-C Logger.Options.Verbosity=6` y
  `-C Logger.Logs.OSREPORT=True` (claves de `Common/Logging/LogManager.cpp`: `LOGGER_WRITE_TO_FILE`
  en sección `Options` y por tipo en sección `Logs`). Manda el OSReport del juego (`printf` de
  libogc) a `<user>/Logs/dolphin.log`, de donde `tools/ctl/wii.py` extrae las líneas `T|`. El file
  listener escribe con `std::flush` por línea, pero el arranque puede no producir OSReport si el
  juego crashea antes de imprimir.

## Pendientes de la plataforma

- **`boot.dol` crashea en Dolphin al arrancar** (T-611): "Invalid read from 0x00000000,
  PC = 0x800c5ed0. The game probably would have crashed on real hardware." (diálogo Warning,
  leído con UI Automation). `tools/ctl/wii.py` detecta ese diálogo, corta el emulador y reporta el
  texto; no se puede obtener veredicto hasta arreglar el cruce de puntero nulo en el backend SDL
  (`platforms/sdl/**` con `__WII__`).
- Verificar el render y el audio de SDL2 en Dolphin; hoy solo se ha comprobado que compila,
  enlaza y arranca hasta el crasheo.
- Confirmar el mapeo de botones del Wiimote/Classic Controller a `BTN_*`; hoy se reutiliza el
  mapeo genérico de SDL2.
- Las capturas `shot` del protocolo TRACE no salen por el backend Wii (no fija `VN_SHOT_DIR`,
  a diferencia de Vita en `platforms/sdl/sdl_target.h`); hay que usar capturas de la ventana de
  render de Dolphin.
