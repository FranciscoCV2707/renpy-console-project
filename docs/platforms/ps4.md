# PlayStation 4 (T-606)

Puerto de Snoot Game para PlayStation 4 utilizando el backend compartido `platforms/sdl` sobre la cadena de herramientas homebrew **OpenOrbis PS4 Toolchain** y empaquetado Fake PKG (FPKG).

## Imagen Docker y Toolchain

- **Imagen:** `xfangfang/pacbrew@sha256:4774ccb28f5e05cd848a7c9204532ea409d1af63e9689d2dbb3e4cec925439d2`
- **Etiqueta origen:** `xfangfang/pacbrew:latest`
- **Digest fijado:** `sha256:4774ccb28f5e05cd848a7c9204532ea409d1af63e9689d2dbb3e4cec925439d2`
- **Paquetes verificados de la imagen (vía pacman):**
  - `ps4-openorbis-clang 12.0.1-1`: Clang/LLVM 12 configurado para el target `x86_64-pc-freebsd12-elf`.
  - `ps4-openorbis-headers 0.5.2-4`: Cabeceras C y stubs de Orbis OS (`libkernel`, `libScePad`, `libSceAudioOut`, `libSceVideoOut`, etc.).
  - `ps4-openorbis-musl 1.5-2`: Biblioteca estándar C de musl adaptada para PS4.
  - `ps4-openorbis-sdl2 2.0.18-16`: Puerto oficial de SDL2 para OpenOrbis en `/opt/pacbrew/ps4/openorbis/usr/include/SDL2` y `/opt/pacbrew/ps4/openorbis/usr/lib/libSDL2.a`.
  - `ps4-openorbis-create-fself 1.2-3`: Generador de binarios autofirmados FSELF (`eboot.bin`).
  - `ps4-openorbis-create-gp4 1.0-5`: Generador de proyectos GP4 para empaquetado de títulos PS4.
  - `ps4-openorbis-pkgtools 0.2.231-5`: Incluye `PkgTool.Core` para manipulación de `param.sfo` y construcción de paquetes FPKG `.pkg`.

## Cómo compilar

Desde la raíz del repositorio:

```bash
# Compilacion estandar
E:/Dev/renpy-console-project/.venv/Scripts/python.exe platforms/ps4/build.py

# Compilacion con salida de trazas (define VN_TRACE)
E:/Dev/renpy-console-project/.venv/Scripts/python.exe platforms/ps4/build.py --trace
```

El script monta el directorio del proyecto en `/src` dentro del contenedor Docker y ejecuta `make -f /src/platforms/ps4/Makefile`.

### Artefactos generados en `build/ps4/`
- `eboot.bin`: Ejecutable firmado FSELF de PS4 (~2.6 MB).
- `snoot.pkg` / `IV0000-SNOT00001_00-SNOOTGAME0000000.pkg`: Paquete FPKG instalable (~6.3 MB).
- `sce_sys/param.sfo`: Metadatos del juego (Title ID `SNOT00001`, Content ID `IV0000-SNOT00001_00-SNOOTGAME0000000`, categoría `gd`).
- `pkg.gp4`: Descriptor del proyecto de empaquetado GP4.

## Ajustes del Backend SDL (`platforms/sdl`)

Bloque `__ORBIS__` de `platforms/sdl/sdl_target.h` (sin `#ifdef` de consola en los `.c`):
- **Pantalla:** Resolución nativa de 1920×1080. Los 320×240 de PS1 se escalan ×4 (1280×960) y se centran en pantalla (desplazamiento `X=320`, `Y=60`).
- **Ruta de datos:** Lee los archivos del disco desde `/data/snoot/` (y `/data/snoot/MUSIC.XA`).
- **Ruta de guardado:** Carpeta de partidas en `/data/snoot/save/` utilizando `mkdir(folder, 0777)` POSIX.
- **Entrada DualShock 4:** Vía subsistema `SDL_Joystick` mapeando los botones nativos:
  - `0`: Cruz (`BTN_CROSS`)
  - `1`: Círculo (`BTN_CIRCLE`)
  - `2`: Cuadrado (`BTN_SQUARE`)
  - `3`: Triángulo (`BTN_TRIANGLE`)
  - `4`: L1 (`BTN_L1`)
  - `5`: R1 (`BTN_R1`)
  - `9`: Options (`BTN_START`)
  - `13`: Cruceta Arriba (`BTN_UP`)
  - `14`: Cruceta Abajo (`BTN_DOWN`)
  - `15`: Cruceta Izquierda (`BTN_LEFT`)
  - `16`: Cruceta Derecha (`BTN_RIGHT`)
  - `17`: Touchpad / Share (`BTN_SELECT`)
  - `18` / `19`: L2 / R2 (`BTN_L2`, `BTN_R2`)
  - Ejes del joystick analógico izquierdo mapeados a direcciones del D-pad para navegación.

## Cómo instalar y ejecutar en una consola física

1. **Requisitos:** Consola PlayStation 4 con firmware vulnerable y jailbreak activo (ej. GoldHEN en 9.00 o PPPwn en 11.00).
2. **Instalación del paquete:**
   - Copiar `snoot.pkg` a una unidad USB formateada en exFAT.
   - Conectar el USB a la PS4.
   - Ir a **Settings** -> **GoldHEN** -> **Package Installer** e instalar `snoot.pkg`.
   - Alternativamente, enviar el paquete por red usando Remote PKG Installer.
3. **Instalación de datos del disco:**
   - Snoot requiere los datos del disco de PS1 generados por `tools/ctl` (ubicados en `build/ctl/ps1/disc/`).
   - Mediante un cliente FTP (conectando al servidor FTP integrado de GoldHEN en el puerto 2121) o la aplicación PS4-Explorer, crear la carpeta `/data/snoot/` en el disco interno de la PS4 y subir el contenido de `build/ctl/ps1/disc/`.

## Cómo ejecutar en emuladores

### shadPS4 (0.20.0)
1. **Línea de comandos** (opciones de `shadPS4.exe --help`):
   ```bash
   shadps4.exe --game "build/ps4/eboot.bin" -f false
   ```
   - `-g, --game TEXT`: ruta del `eboot.bin` (o ID del juego). Si es una carpeta, usa su `eboot.bin`.
   - `-f, --fullscreen TEXT`: `true|false`.
   - `--override-root DIR`: raíz del juego (`/app0`) alternativa; `--mount origen,destino` monta rutas extra
     y `-e, --env` pasa variables de entorno al guest; `--log-append` acumula el log en vez de truncarlo.
   - `--add-game-folder DIR`: registra una carpeta de juegos (para arrancar por ID).
2. **Dónde busca el juego sus datos:** `/app0` es la carpeta del `eboot.bin` (`src/emulator.cpp`: "Applications
   expect to be run from /app0 so mount the file's parent path as app0") y `/data` es la subcarpeta `data` del
   usuario del emulador (`mnt->Mount(GetUserPath(PathType::GameDataDir), "/data")`), es decir
   `%APPDATA%\shadPS4\data\` en Windows. Los datos del disco van en `%APPDATA%\shadPS4\data\snoot\`.
3. **Dónde queda lo que el juego escribe por `printf`:** stdout/stderr del guest van a
   `Devices::Logger` (`src/core/file_sys/fs.cpp`, `CreateStdHandles`) y se registran con la clase `Tty` y el
   prefijo `[stdout] ` (`src/core/file_sys/devices/logger.cpp`) en `log\shad_log.txt` (el arranque escribe
   primero `log\shadps4.log` y `src/emulator.cpp` hace `Log::Switch` al cargar el juego; con `Log.separate`
   activo en `config.json` sería `log\SNOT00001.log`).
4. **Configuración:** `config.json` en `%APPDATA%\shadPS4\` (`src/core/emulator_settings.cpp`); el
   `config.toml` antiguo se migra automáticamente. La sección `Log` (`enable`, `filter`, `separate`, `sync`,
   `type`) controla el registro.
5. **Cómo cerrar al terminar:** si el juego llama `exit()`, el HLE de `exit`
   (`src/core/libraries/kernel/process.cpp`) termina el proceso con una aserción y vuelca el log; si el juego
   no sale, la ventana queda abierta (`while (window->IsOpen())` en `src/emulator.cpp`) y hay que matar el
   proceso (`taskkill /PID <pid> /T /F`).
6. **Capturas:** `F12` guarda un PNG en `%APPDATA%\shadPS4\screenshots\`
   (`{game_id}_{fecha}_{game|hud}_{seq}.png`); `LAlt+F12` la incluye con los overlays.
7. **Diálogo de migración de partidas:** en el primer arranque shadPS4 muestra el diálogo modal "Save
   Migration" siempre que falte `%APPDATA%\shadPS4\home\1000` (`src/core/user_manager.cpp`,
   `CreateDefaultUsers`/`AskMigrationOption`); crear esa carpeta por adelantado evita que bloquee el arranque.

### fpPS4
1. Ejecución directa:
   ```bash
   fpps4.exe -e "build/ps4/eboot.bin"
   ```

## Integración con Console Test Lab (`tools/ctl`)

```bash
E:/Dev/renpy-console-project/.venv/Scripts/python.exe -m tools.ctl run --target ps4 --scenario tests/scenarios/snoot-route-chapter_x2.yaml
```

El adapter `tools/ctl/ps4.py` copia `build/ctl/ps1/disc/` y el `AUTOTEST.BIN` del escenario en
`%APPDATA%\shadPS4\data\snoot\`, crea `%APPDATA%\shadPS4\home\1000\` (sin diálogo de migración), compila con
`platforms/ps4/build.py --trace`, arranca shadPS4 con `--game build/ps4/eboot.bin -f false`, espera la salida
del juego (o `limits.max_seconds`), mata el proceso si hace falta y extrae de `log\shad_log.txt` las líneas
`T|` de la traza VN_TRACE (`build/ctl/ps4/trace.txt`) para el veredicto contra Ren'Py.

**Bloqueo conocido (T-614):** el `libc.a` de OpenOrbis implementa `malloc`/`realloc` sobre
`sceLibcMspace*` de `libSceLibcInternal` (`malloc.lo`, verificado con `llvm-nm` sobre la imagen
`xfangfang/pacbrew`), pero shadPS4 0.20.0 solo tiene stubs de esos NIDs (`CommonStub` que devuelven 0). El
heap del guest nunca se inicializa: la CRT reserva regiones flexibles de 2.5 GiB ("User Mem") en bucle hasta
que shadPS4 muere con `address_space.cpp:294 MapRegion: Assertion Failed!`, antes de ningún evento TRACE ni
de dibujar la pantalla de título. Ver `reports/T-614.md`.
