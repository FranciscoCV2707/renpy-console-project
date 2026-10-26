# Qué descargar e instalar (SDKs y herramientas)

> Ordenado por prioridad. No instalar todo de golpe: ir fase por fase.
> Regla: instalar con aprobación; verificar con `tools/check_env.py` (cuando exista).

## Ya tienes (no reinstalar)

- Python 3.12 + venv (`.venv`)
- Git, CMake, Ninja, ffmpeg, Graphviz
- PSn00bSDK (MSYS2) en `C:\msys64\usr\local\psn00bsdk`
- DuckStation, PCSX-Redux, BizHawk (emuladores PS1)
- BIOS reales de PS1
- SDKs de Ren'Py (8.3.7, etc.)

## Fase 1 — PC (para pruebas rápidas) [AHORA]

| Herramienta | Para qué | Descarga |
|---|---|---|
| SDL2 (dev) | Backend PC del núcleo | https://github.com/libsdl-org/SDL/releases (Windows dev) |
| MinGW/MSVC | Compilar C en Windows | Ya tienes (MSYS2) |

Verificación: compilar `platforms/pc/backend.c` con SDL2.

## Fase 2 — PS2 y PSP [SIGUIENTE]

| SDK | Para qué | Descarga / Instalación |
|---|---|---|
| PS2SDK | Compilar para PS2 | `git clone https://github.com/ps2dev/ps2sdk` (requiere ps2dev toolchain) |
| ps2dev toolchain | Compilador mips64r5900el | https://github.com/ps2dev/ps2toolchain |
| PCSX2 | Emulador PS2 | https://pcsx2.net/ |
| PSPSDK | Compilar para PSP | https://github.com/pspdev/pspsdk |
| PSP toolchain | Compilador psp-gcc | https://github.com/pspdev/pspdev |
| PPSSPP | Emulador PSP | https://www.ppsspp.org/ |

Verificación: compilar un ELF/EBOOT mínimo y ejecutar en el emulador.

## Fase 3 — PS Vita, 3DS, Wii, Xbox Classic

| SDK | Para qué | Descarga |
|---|---|---|
| VitaSDK | PS Vita | https://github.com/vitasdk |
| devkitPro | 3DS, Wii, GBA, DS, Switch | https://devkitpro.org/ (instalador Windows) |
| NXDK | Xbox Classic | https://github.com/XboxDev/nxdk |
| xemu | Emulador Xbox Classic | https://xemu.app/ |
| Vita3K | Emulador Vita | https://vita3k.org/ |
| Azahar | Emulador 3DS | https://github.com/azahar-emu/azahar |
| Dolphin | Emulador Wii | https://dolphin-emu.org/ |

## Fase 4 — DS, GBA, Switch

Ya incluidos en devkitPro (Fase 3). Emuladores:
- melonDS (DS): https://melonds.kuribo64.net/
- mGBA (GBA): https://mgba.io/
- Switch: hardware o emuladores compatibles (Ryujinx/Yuzu forks).

## Fase 5 — PS3, PS4, Xbox One / Series

| SDK | Para qué | Descarga |
|---|---|---|
| PSL1GHT | PS3 | https://github.com/ps3dev/PSL1GHT |
| OpenOrbis | PS4 | https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain |
| shadPS4 | Emulador PS4 | https://github.com/shadps4-emu/shadPS4 |
| GDK (autorizado) | Xbox One/Series | Microsoft (requiere aprobación) |
| RPCS3 | Emulador PS3 | https://rpcs3.net/ |

## Fase 6 — GB, GBC, Xbox 360, PS5 (especializados)

| SDK | Para qué | Descarga |
|---|---|---|
| GBDK-2020 | GB/GBC | https://github.com/gbdk-2020/gbdk-2020 |
| Mesen 2 / BizHawk | Emuladores GB/GBC | https://mesen.ca/ / https://tasvideos.org/Bizhawk |
| LibXenon | Xbox 360 | https://github.com/Free60Project/libxenon |
| Xenia | Emulador Xbox 360 | https://xenia.jp/ |
| PS5SDK (experimental) | PS5 | https://github.com/PS5Dev/PS5SDK (investigación) |

## Herramientas de automatización (instalar cuando haga falta)

| Herramienta | Para qué |
|---|---|
| PyAutoGUI | Control de emuladores sin API |
| OpenCV | Comparación de capturas |
| Pillow | Procesamiento de imágenes |
| pytest | Pruebas |

## Notas importantes

- **No instalar todo de golpe.** Ir fase por fase según el roadmap.
- **Windows first:** usar MSYS2 para toolchains Unix-like.
- **PS5 y Xbox 360** son proyectos especializados: dejar para el final.
- **PS5SDK experimental** no genera aplicaciones completas; requiere acceso oficial.
- **Xbox One/Series**: UWP nuevos no se aceptan en Store; distribución comercial sigue otra ruta.

## Verificación rápida (cuando exista check_env.py)

```powershell
.\.venv\Scripts\python.exe tools\check_env.py
```

Por ahora, verificar manualmente que los compiladores estén en PATH:
```powershell
mipsel-none-elf-gcc --version   # PS1
mips64r5900el-ps2-elf-gcc --version  # PS2 (cuando se instale)
arm-none-eabi-gcc --version     # GBA/DS/Switch
```
