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

### shadPS4
1. **Línea de comandos:**
   ```bash
   shadps4.exe --game="build/ps4/eboot.bin" --log-level=info
   ```
2. **Instalación de PKG:**
   ```bash
   shadps4.exe --install-pkg="build/ps4/snoot.pkg"
   ```
3. Ubicar los datos del disco en la carpeta de datos simulada del emulador: `<directorio_usuario>/user/data/snoot/`.

### fpPS4
1. Ejecución directa:
   ```bash
   fpps4.exe -e "build/ps4/eboot.bin"
   ```

## Integración futura con Console Test Lab (`tools/ctl`)

Para permitir la ejecución automatizada de pruebas y captura de trazas TRACE con `python -m tools.ctl run --target ps4 --scenario ...`, faltaría implementar en una tarea posterior:
1. **Módulo adapter `tools/ctl/ps4.py`:**
   - Orquestar la preparación de la carpeta de trabajo del emulador (`shadPS4` o `fpPS4`).
   - Copiar `eboot.bin` y los datos del disco (`build/ctl/ps1/disc/`) junto con el `AUTOTEST.BIN` generado para el escenario en la ruta mapeada a `/data/snoot/`.
2. **Ejecución y recolección de trazas:**
   - Lanzar shadPS4 en modo headless (`--game=...`) redirigiendo la salida estándar a un archivo de registro.
   - Extraer las líneas de traza con prefijo `T|` generadas por `VN_TRACE`.
   - Monitorear la finalización del autotest y matar el proceso del emulador al concluir el escenario.
