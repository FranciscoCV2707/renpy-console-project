# Qué descargar e instalar

> Por fase de `PLAN.md`. Descargas de más de 1 GB, con aprobación del usuario. Las toolchains de consola (salvo
> PS1) van en Docker: no se instalan en Windows.

## Ya instalado (2026-10-26)

- Python 3.12 (`.venv` de cada repo), Git, CMake, Ninja, ffmpeg, Graphviz, Node/npm, uv, gh.
- PSn00bSDK en `C:\msys64\usr\local\psn00bsdk` (PS1), gcc de host y **SDL2 2.32.10** en `C:\msys64\ucrt64`.
- DuckStation, PCSX-Redux y BIOS de PS1 en `E:\snoot`; SDKs de Ren'Py en `E:\snoot\renpy-sdks` y
  `E:\snoot\renpy-8.3.7-sdk`.
- Docker Desktop y WSL2 (Docker Desktop no estaba abierto: hay que iniciarlo).
- CLIs de agentes: `codex`, `opencode`, `kilo`, `vibe`, `agy`.

## Pista de agentes `[HUMANO]`

| Qué | Cómo |
|---|---|
| Logins | `codex login`, `opencode auth login`, `kilo`, `vibe --setup`, `agy` |
| Beam | `opencode run -m opencode-go/beam-free "Responde solo: OK"` (verificar) |
| Orca | Instalador de Windows de `stablyai/orca` (verificar); activar "Orca CLI"; `orca status --json` |

## Fases 1–4 — PS1 y PC

Nada nuevo. SDL2 ya está en MSYS2.

## Fase 5 — PSP y PS2

| Qué | Cómo |
|---|---|
| Toolchain PSP | `docker pull pspdev/pspdev:latest` (verificar etiqueta) |
| Toolchain PS2 | `docker pull ps2dev/ps2dev:latest` (verificar etiqueta) |
| PPSSPP | https://www.ppsspp.org/ → `E:\snoot` (usar PPSSPPHeadless para pruebas) |
| PCSX2 | https://pcsx2.net/ → `E:\snoot` (requiere BIOS de PS2 propia) |

## Fase 6 — Vita, 3DS, Wii, Xbox clásica, Switch

| Qué | Cómo |
|---|---|
| VitaSDK | `vitasdk/vitasdk` (verificar) |
| devkitPro (3DS, Wii, Switch, GBA) | `devkitpro/devkitarm`, `devkitpro/devkitppc`, `devkitpro/devkita64` |
| nxdk (Xbox clásica) | https://github.com/XboxDev/nxdk en WSL2 |
| Emuladores | Vita3K (https://vita3k.org/), Azahar (https://github.com/azahar-emu/azahar), Dolphin (https://dolphin-emu.org/), xemu (https://xemu.app/) |

## Fase 7 — GBA, DS, GB/GBC

| Qué | Cómo |
|---|---|
| Butano (GBA) | https://github.com/GValiente/butano sobre `devkitpro/devkitarm` |
| BlocksDS (DS) | https://github.com/blocksds (imagen Docker: verificar nombre) |
| GBDK-2020 (GB/GBC) | https://github.com/gbdk-2020/gbdk-2020 (release de Windows) |
| Emuladores | mGBA (https://mgba.io/), melonDS (https://melonds.kuribo64.net/), SameBoy, BizHawk, Mesen 2 |

## Investigación

PSL1GHT (https://github.com/ps3dev/PSL1GHT) + RPCS3, OpenOrbis (https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain)
+ shadPS4, PS5SDK (experimental), libxenon (https://github.com/Free60Project/libxenon) + Xenia, GDK (requiere
aprobación de Microsoft).
