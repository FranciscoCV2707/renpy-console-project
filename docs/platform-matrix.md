# Matriz de plataformas

> Niveles (A SDL, B nativo, C demake, D demake extremo, R investigación) y fases: `PLAN.md` secciones 5 y 6.
> `(verificar)` = confirmar etiqueta de imagen o flags con `--help` o la doc oficial antes de usarlo.

## Hardware, toolchain y pruebas

| Plataforma | Nivel | Fase | Resolución | RAM / VRAM | SDK | Toolchain | Emulador de prueba | Salida de traza | Estado |
|---|---|---|---|---|---|---|---|---|---|
| PC | A | 4 | 320×240 escalable | — | SDL2 2.32 | MSYS2 ucrt64 (instalado) | — | stdout | Backend sin ventana para pruebas |
| **PS1** | B | 1 | 320×240 | 2 MB / 1 MB (+512 KB SPU) | PSn00bSDK | MSYS2 (instalado) | PCSX-Redux (`-stdout`, sin interfaz), DuckStation | TTY | v1.0 publicada; núcleo nuevo compila |
| PSP / PSP Go | A | 5 | 480×272 | 32/64 MB / 2 MB | pspsdk | pspdev/pspdev@sha256:54895e6f5afb71b8f4f6915ee6d5023e1e087ca7afdf2dcb1d7a694a5233e45f | PPSSPP / PPSSPPHeadless | stdout en headless | Compila (uild/psp/EBOOT.PBP) |
| PS2 | A | 5 | 640×448 | 32 MB / 4 MB GS | ps2sdk + gsKit | `ps2dev/ps2dev` (verificar) | PCSX2 (flags batch: verificar) | log de EE | Pendiente (reemplaza a `snoot-ps2`) |
| PS Vita | A | 6 | 960×544 | 512 MB / 128 MB | VitaSDK | `vitasdk/vitasdk@sha256:8227da1b596d981f4513cd9b36bda1e43857f6dae5bcf4312c1cd40167f7d9bb` | Vita3K | log de Vita3K | Compila con backend SDL (T-601); paquete `build/vita/snoot.vpk` |
| 3DS | A | 6 | 400×240 + 320×240 | 128/256 MB | libctru + SDL2 (compilado desde fuente, tag release-2.32.10) | devkitpro/devkitarm@sha256:116afba8df8453961de2936ffab20dd441edf4d682856c1ec8b0e53d7ed0bbf5 | Azahar | log de debug | Compila (uild/3ds/snoot.3dsx) |
| Wii | A | 6 | 640×480 | 24+64 MB | libogc | devkitpro/devkitppc@sha256:d50f8a886f2ce1d3c22685a774afb0845379876b47d9b41a9b729f4f63a54813 | Dolphin (-b -e <dol>, verificar) | OSReport | Compila (uild/wii/boot.dol) |
| Xbox clásica | A | 6 | 640×480 | 64 MB unificada | nxdk (trae SDL2) | xboxdev/nxdk@sha256:14aeace40a9aa3ffdf14501827459cb2ab04766e836200228d87bfeb52f7f6ed | xemu | DbgPrint (verificar) | Compila (uild/xbox/default.xbe) |
| Switch 1 | A | 6 | 1280×720 | 4 GB | libnx + SDL2 (switch-sdl2) | devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282 | hardware propio | nxlink | Compila (uild/switch/snoot.nro) |
| GBA | C | 7 | 240×160 | 32 KB IWRAM + 256 KB EWRAM / 96 KB; ROM ≤ 32 MB | Butano | `devkitpro/devkitarm` | mGBA (Lua) | registros de debug de mGBA | Pendiente |
| DS | C | 7 | 2× 256×192 | 4 MB / 656 KB | BlocksDS | imagen de BlocksDS (verificar) | melonDS | consola de debug | Pendiente |
| GB / GBC | D | 7 | 160×144 | 8/32 KB WRAM; ROM ≤ 8 MB (MBC5) | GBDK-2020 | release Windows | SameBoy / BizHawk / Mesen 2 | debug del emulador | Pendiente |
| PS3 | R | 6 | 1280×720 | 256 MB / 256 MB | PSL1GHT v2 | `hldtux/ps3dev-sdl2@sha256:2b6154588148336d559fbd37f4f52a3418fa96a86906b5019160baef22c75e55` | RPCS3 | stdout/RPCS3.log | Compila con backend SDL (T-607); `build/ps3/snoot.self` y `build/ps3/snoot.pkg` |
| PS4 | R | — | — | — | OpenOrbis | — | shadPS4 | — | Investigación |
| PS5 | R | — | — | — | PS5SDK experimental | — | sin emulador general | — | Investigación |
| Xbox 360 | R | — | — | — | libxenon (bare-metal) | — | Xenia | — | Investigación |
| Xbox One / Series S/X | R | — | — | — | UWP / GDK autorizado | Visual Studio | Developer Mode | — | Investigación |

## Recursos por plataforma (perfiles de `tools/assetpipe`)

Snoot va solo en español (`PLAN.md` D16): `--language es` toma las imágenes con texto traducido de `game/tl/es/`.

| Plataforma | Fondos / CG | Sprites | Música | Efectos / voz | Video |
|---|---|---|---|---|---|
| PC | Original | Original | Original | Original | Original |
| PS1 | 4/8 bpp + CLUT, 320×180 en 320×240 (como hoy) | 4/8 bpp + CLUT | XA-ADPCM (`psxavenc`) | SPU-ADPCM (`psxavenc`) | STR/MDEC (`psxavenc`) |
| PS2 | 8/32 bpp | 8 bpp | ADPCM o PCM en streaming | ADPCM SPU2 | Decidir (IPU/MPEG o cuadros) |
| PSP | 8/16 bpp, 480×272 | 8 bpp | MP3/AT3 o PCM | PCM | Decidir (verificar decodificador) |
| Vita / 3DS / Wii / Xbox / Switch | Según VRAM; potencia de 2 si aplica | — | Ogg/Opus vía SDL_mixer o equivalente | WAV/ADPCM | Decidir por plataforma |
| GBA | Modo 4 (8 bpp, 240×160) + LZ77 | 4 bpp | PCM 8 bits o tracker | PCM corto | Escenas fijas |
| DS | 8/16 bpp por pantalla, comprimido | 4/8 bpp | IMA-ADPCM en streaming | ADPCM | Opcional, cuadros a baja tasa |
| GB / GBC | ≤ 360 tiles por pantalla, tramado, 4 tonos / paletas GBC | Tiles 2 bpp | hUGETracker | — | Escenas fijas |

Reglas: conversión determinista, `manifest.json` con hash por recurso, reporte de presupuesto por escena (pico de
RAM/VRAM) y vista previa HTML para revisión humana.
