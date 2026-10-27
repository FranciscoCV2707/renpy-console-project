# Qué respaldar y qué reinstalar

Lista para formatear la PC sin perder nada. Después de reinstalar, seguir `CONTINUAR.md`.

## Antes de formatear: respaldar (no está en git)

| Qué | Dónde está | Por qué |
|---|---|---|
| Carpeta de emuladores, BIOS, firmware y el juego | `E:\snoot\` (todo) | Los emuladores se pueden volver a bajar, pero BIOS y firmware de tus consolas no. Si `E:` es otro disco y no se formatea, no hace falta copiarla |
| BIOS de PS1 | `E:\snoot\ps1 bios\` | Vienen de tu consola |
| BIOS de PS2 | `E:\snoot\ps2 bios\` y `E:\snoot\pcsx2-2.8.2\bios\scph39001.bin` | Vienen de tu consola |
| Firmware de PS3 y Vita | `E:\snoot\ps3 firmware\`, `E:\snoot\vita firmware\` | Oficiales de Sony; se pueden volver a bajar, pero ahorra tiempo |
| Snoot Game | `E:\snoot\snootgame\`, `E:\snoot\SnootGame-Patch14-MunichAgreement-win\` | Fuente de todo el port (guion, imágenes, `tl/es`) |
| SDK de Ren'Py | `E:\snoot\renpy-8.3.7-sdk\`, `E:\snoot\renpy-sdks\` | Graban las trazas de referencia |
| Repos hermanos sin remoto | `E:\Dev\vn-engine-ps1`, `E:\Dev\wani-ps1`, `E:\Dev\renpy-port-kit`, `E:\Dev\snoot-ps2` | No tienen repositorio en GitHub: se pierden si no se copian |
| Llave SSH de GitHub | `C:\Users\Pako\.ssh\` | Sin ella no se puede hacer `git push`; o generar otra y darla de alta en GitHub |
| Configuración de OpenCode | `C:\Users\Pako\.config\opencode\` | Modelo predeterminado y proveedores |
| Memoria de Claude (opcional) | `C:\Users\Pako\.claude\projects\E--Dev\memory\` | Preferencias guardadas; lo importante ya está en `PLAN.md` y `CLAUDE.md` |

Ya están en GitHub: `renpy-console-project` (main y todas las ramas `agent/*`) y `snoot-ps1` (`snoot-game-ps1`).

## Después de formatear: instalar

### Base
- Git (con Git Bash) y la llave SSH de GitHub.
- Python 3.12 (64 bits). Cada repo usa su `.venv`.
- MSYS2 en `C:\msys64`. En la terminal UCRT64:
  `pacman -S mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-SDL2 mingw-w64-ucrt-x86_64-clang-tools-extra mingw-w64-ucrt-x86_64-cmake mingw-w64-ucrt-x86_64-ninja`
  (SDL2 2.32.x; `clang-format` y `clangd` vienen en `clang-tools-extra`).
- PSn00bSDK (PS1) en `C:\msys64\usr\local\psn00bsdk`: release oficial de GitHub `Lameguy64/PSn00bSDK`.
- ffmpeg (en el PATH).
- Docker Desktop con WSL2. Las imágenes de las toolchains (PSP, PS2, Vita, 3DS, Wii, Xbox, Switch, PS4, PS3, DS, GBA)
  se descargan solas al compilar: van fijadas por digest en cada `platforms/<consola>/build.py`. Son varios GB.
- Node.js (para los CLIs de agentes).

### Agentes
- Claude Code.
- `codex`, `opencode`, `kilo`, `vibe`, `agy` (Antigravity) y Orca; luego iniciar sesión en cada uno
  (`codex login`, `opencode auth login`, `kilo`, `vibe --setup`, `agy`). Detalle en `docs/what-to-download.md`.
- OpenCode: el modelo que usan los agentes es `opencode-go/iceman-contributor-free` (en `tools/agents/agents.toml`).

### Emuladores (en `E:\snoot`, versiones probadas)

| Consola | Emulador | Carpeta |
|---|---|---|
| PS1 | PCSX-Redux (nightly) y DuckStation | `pcsx-redux-nightly-...`, `duckstation-windows-x64-release` |
| PSP | PPSSPP 1.20.4 | `ppsspp-1.20.4` |
| PS2 | PCSX2 2.8.2 portable | `pcsx2-2.8.2` (con `inis\PCSX2.ini` ajustado: ver `docs/platforms/ps2.md`) |
| PS Vita | Vita3K (continuous) | `vita3k-continuous` |
| 3DS | Azahar 2126.2 | `azahar-2126.2` |
| Wii | Dolphin 2609a | `dolphin-2609a` |
| Xbox clásica | xemu 0.8.139 | `xemu-0.8.139` |
| PS3 | RPCS3 0.0.43 | `rpcs3-c365ea76a552961ff078` (firmware 4.93 instalado con `--installfw`) |
| PS4 | shadPS4 0.20.0 | `shadps4-.0.20.0` |
| DS | melonDS 1.1 | `melonds-1.1` |
| GBA | mGBA 0.10.5 | `mgba-0.10.5` |
| GB/GBC | SameBoy 1.0.4 | `sameboy-1.0.4` |

Después de instalarlos: en Windows, Configuración → Pantalla → Gráficos, poner cada emulador en "Alto rendimiento"
(NVIDIA). En esta PC se hizo con el registro (`HKCU\Software\Microsoft\DirectX\UserGpuPreferences`).

### Lo que todavía falta y solo puedes dar tú
- Xbox clásica: tu MCPX (`mcpx_1.0.bin`) y tu BIOS (por ejemplo `Complex_4627.bin`), sacados de tu Xbox, en
  `E:\snoot\xbox bios\`.
- Switch: tus `prod.keys` y el firmware de tu Switch, en `E:\snoot\switch keys\`.
- Xbox One/Series (al final): permiso para bajar Visual Studio con UWP (más de 10 GB) y el modo desarrollador en la
  consola.
