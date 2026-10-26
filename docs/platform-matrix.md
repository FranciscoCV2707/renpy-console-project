# Matriz de plataformas (detalle)

> Resumen por consola: SDK, emulador, dificultad, nivel de motor, estado.

## PlayStation

| Consola | SDK / toolchain | Emulador | Dificultad | Nivel motor | Estado |
|---|---|---|---|---|---|
| PS1 | PSn00bSDK | PCSX-Redux / BizHawk / DuckStation | Ya logrado | Standard | ✅ v1.0 |
| PS2 | PS2SDK (ps2dev) | PCSX2 | Media | Standard | 🔴 pendiente |
| PS3 | PSL1GHT | RPCS3 | Alta | Full | 🔴 pendiente |
| PS4 | OpenOrbis | shadPS4 / hardware | Alta | Full | 🔴 pendiente |
| PS5 | PS5SDK experimental | Hardware | Muy alta | Full | 🔴 investigación |
| PSP | PSPSDK | PPSSPP | Media | Standard | 🔴 pendiente |
| PSP Go | PSPSDK (compartido) | PPSSPP + hardware | Media | Standard | 🔴 pendiente |
| PS Vita | VitaSDK | Vita3K | Media | Standard | 🔴 pendiente |

## Nintendo

| Consola | SDK / toolchain | Emulador | Dificultad | Nivel motor | Estado |
|---|---|---|---|---|---|
| Game Boy | GBDK-2020 | BizHawk / Mesen 2 | Muy alta | Minimal | 🔴 pendiente |
| Game Boy Color | GBDK-2020 | BizHawk / Mesen 2 | Alta | Minimal | 🔴 pendiente |
| Game Boy Advance | Butano / devkitARM | mGBA | Media-alta | Lite | 🔴 pendiente |
| Nintendo DS | BlocksDS / libnds | melonDS / DeSmuME | Media-alta | Standard | 🔴 pendiente |
| Nintendo 3DS | devkitARM + libctru + citro2d | Azahar | Media | Standard | 🔴 pendiente |
| Wii | devkitPPC + libogc | Dolphin | Media | Full | 🔴 pendiente |
| Switch 1 | devkitA64 + libnx | Hardware / emuladores | Media-alta | Full | 🔴 pendiente |

## Xbox

| Consola | SDK / toolchain | Emulador / pruebas | Dificultad | Nivel motor | Estado |
|---|---|---|---|---|---|
| Xbox Classic | NXDK (SDL2) | xemu | Media | Standard | 🔴 pendiente |
| Xbox 360 | LibXenon | Hardware / Xenia | Muy alta | Full | 🔴 pendiente |
| Xbox One | UWP + GDK | Developer Mode | Media-alta | Full | 🔴 pendiente |
| Xbox Series S | UWP / GDK | Developer Mode | Media-alta | Full | 🔴 pendiente |
| Xbox Series X | UWP / GDK | Developer Mode | Media-alta | Full | 🔴 pendiente |

## Niveles de motor

| Nivel | Consolas | Capacidades |
|---|---|---|
| Full | PS2, PS3, PS4, PS5, Wii, Switch, Xbox One/Series, PC | Todo: video, audio XA, 16+ sprites, cámara, transiciones |
| Standard | PS1, PSP, Vita, DS, 3DS, Xbox Classic | Sprites 8–16, audio VAG/XA, imágenes 8-bit, video reducido |
| Lite | GBA | Paletas 4/8-bit, tiles, sprites hardware, audio PCM/PSG |
| Minimal | GB, GBC | 4 tonos, fondos de tiles, texto, audio reducido |

## Automatización de pruebas

| Plataforma | Emulador | Estrategia |
|---|---|---|
| PS1 | PCSX-Redux / BizHawk | Lua, debugger, capturas |
| PS2 | PCSX2 | CLI, logs, controlador externo |
| PS3 | RPCS3 | Arranque automatizado, logs, capturas |
| PS4 | shadPS4 | CLI, diagnóstico, hardware |
| PS5 | Sin emulador general | Hardware + pruebas del núcleo en PC |
| PSP / PSP Go | PPSSPP | CLI, debugger, entradas automatizadas |
| PS Vita | Vita3K | CLI, logs, automatización externa |
| GB / GBC | BizHawk / Mesen 2 | Lua, estados, capturas |
| GBA | mGBA | Lua nativo |
| DS | DeSmuME / BizHawk | Lua |
| 3DS | Azahar | Control externo, logs, capturas |
| Wii | Dolphin | CLI, playback de entradas, debugger |
| Switch | Emulador compatible / hardware | Automatización externa, logs |
| Xbox Classic | xemu | Control externo, logs |
| Xbox 360 | Hardware / Xenia | Validación específica, debugger |
| Xbox One / Series | Consola en modo desarrollo | Despliegue y depuración con VS |
