# Bitácora — renpy-console-project

## 2026-10-26
- `git init` y commit inicial; rutas de `C:\Users\Pako\Desktop\snoot` cambiadas a `E:\snoot`.
- Extraídos a `engine/core/` los módulos sin hardware de `ps1-base` (`vm`, `scene`, `str`, `lz4`,
  `opcodes.h`, `vn_limits.h`). Compilan en host con `C:\msys64\ucrt64\bin\gcc.exe -std=c99 -Wall -Wextra -pedantic`.
- Pendiente: no hay `.venv` ni pytest (resuelto más abajo).
- Commit inicial reescrito sin línea de coautor (regla del proyecto).
- Contrato `VnPlatformOps` movido a `engine/core/vn_platform.h` y ampliado con archivos y fuente. `chapter.c` y
  `text.c` ya no incluyen nada de PS1. Hardware (`audio`, `cd`, `img`, `input`, `res`, `save`, `video`,
  `video_clip`) copiado a `platforms/ps1/` con `backend_ps1.c`.
- Cambio de conducta: `font_load` ahora rechaza un `FONT.BIN` más corto que su atlas (antes leía de más).
- Prueba host `tests/core/test_core_host.c` pasa con los datos de Wani; el núcleo y el backend PS1 compilan con
  `mipsel-none-elf-gcc`. No hay ejecutable PS1 todavía (falta `main.c`), así que no se probó en emulador.
- Referencias: base = `vn-engine-ps1` (`947cb3b`); `snoot-ps1/engine` = motor v1.0, solo referencia.
- Rutas `C:\Users\Pako\Desktop\snoot` cambiadas a `E:\snoot` en los repos hermanos, con permiso del usuario:
  `vn-engine-ps1` f63d4a6, `snoot-ps1` 2b22e15, `wani-ps1` 3810b25, `renpy-port-kit` 59fc01d, `snoot-ps2` ce0eccd.
  `check_env.py` de snoot-ps1 y wani-ps1 en verde; renpy-port-kit 404 pruebas pasan. `engine/ps1-base` no se tocó
  (copia de 947cb3b).
- `.venv` con Python 3.12 y pytest; `pytest.ini` limita las pruebas a `tests/`. `tests/test_core_host.py` compila
  y corre la prueba de host: 1 pasa.
- Plan integrado v0.2: `PLAN.md` reescrito uniendo el v0.1 y `E:\Dev\PLAN_MAESTRO_SNOOT_PORTS.md` v2.0 (copiado
  sin cambios a `docs/plan-maestro-agentes.md`). Decisiones clave: este repo es el del proyecto, VNB es el formato
  intermedio (se descartan SnootIR y VNSCENE), backend SDL2 compartido, Docker para toolchains, TRACE + Test Lab
  CLI, agentes en paralelo desde la Fase 4. `AGENTS.md` reemplaza a `docs/ai-agent-rules.md`; se borraron
  `docs/formats/vnscene.md`, el stub `tools/console-test-lab` y las carpetas vacías.
- Rutas `Path.home() / "Desktop" / "snoot"` (no las tomó el script anterior) cambiadas a `E:\snoot`:
  snoot-ps1 4385f4c (`emutest.py`, `audit/capture.py`), wani-ps1 81c56d8 (`playtest.py`), renpy-port-kit d395512
  (`paths.py`). Kit 404 pasan; snoot-ps1 59 pasan; wani-ps1 146 pasan y 1 falla por `psxavenc.exe` 0xC0000139
  (falla igual antes del cambio).
- Pista de agentes A3: skills de Orca (`orca-cli` ya estaba, `orchestration` instalada con el CLI de Orca) en
  `~/.agents`, `~/.claude` y `~/.gemini`. Probado con una skill falsa: OpenCode/Beam, Kilo y Antigravity leen
  `.agents/skills` (OpenCode y Kilo también `.claude/skills`); Codex y Vibe leen `.agents/skills` (código fuente).
  `agy -p` 1.4.7 responde sin terminal. 5 skills propias en `.agents/skills/` adaptadas a VNB y a las rutas reales,
  3 subagentes en `.claude/agents/`, plantillas, `agents.toml` con flags verificados con `--help`, `dispatch.py` y
  `sync_skills.py` con 8 pruebas. `npx skills` no se pudo correr (código externo bloqueado por permisos).
- Orca: las skills de Codex, OpenCode, Kilo, Vibe y MiMo van a `~/.agents/skills` (carpeta compartida), por eso
  Orca solo mostraba enlaces para Claude y Antigravity. Los 6 agentes arrancan con `orca agent launch`. Codex fallaba
  por `service_tier = "default"` en `~/.codex/config.toml` (se quitó la línea) y Orca usaba Codex 0.128 y OpenCode
  1.14.33 viejos de `AppData\Roaming\npm` (Orca pone esa carpeta antes que `C:\nvm4w\nodejs`); se desinstalaron con
  permiso del usuario. Ahora Orca lanza Codex 0.164 y OpenCode 2.1.4. Repo agregado a Orca.
- Prueba de humo A4 (10 tareas T-001..T-010): Claude (Opus 5.5), Antigravity (Gemini 3.8 Flash) y Codex 0.164
  completas, con commit y reporte; 9 pruebas pasan en cada worktree. Codex necesitó `auto_commit` y `.tmp/` propio
  (su sandbox de Windows no escribe en `.git`, `.agents` ni el temporal global); los reportes pasan a
  `reports/<T>.md`. Los 5 Beam, Kilo y Vibe no se lanzaron: el clasificador de permisos de la sesión de Claude los
  bloqueó por correr con aprobación automática. Faltan por correr desde una terminal del usuario.
- GA cumplida: las 10 tareas de humo en verde (5 Beam en paralelo en ~1,5 min, Codex, Kilo, Vibe, Antigravity,
  Claude), cada rama con solo sus 2 archivos y sin coautor. Kilo se salió del worktree la primera vez (commit en
  `main`): se movió el commit a su rama, se quitó de `main` y ahora recibe `--dir`; `dispatch.py` marca FUGA si un
  agente cambia el repo principal. Detección de límites de tasa solo con frases de error reales.
- Regla de permiso en `.claude/settings.local.json` (personal, ignorada por git) para que Claude lance
  `dispatch.py`. Instalados `clangd` 22.1.4 (MSYS2) y `pyright` 1.1.414 (npm) con los plugins `clangd-lsp` y
  `pyright-lsp`; `compile_flags.txt` para que clangd encuentre los headers. No se instalaron Superpowers ni
  mattpocock (chocan con los comandos propios del usuario).
- Fase 1 cerrada. API de plataforma por enlace (decisión D15 del usuario) en lugar de 60 operaciones en
  `VnPlatformOps`. `main.c`, módulos, juegos y CMake traídos de vn-engine-ps1; Snoot y Wani compilan para PS1 desde
  este repo. T-102: headers neutrales en `engine/platform/`, `BTN_*`, `video_wait_vblank`/`video_vblank_count`,
  `vn_platform_default_ops`; la app compila en PC sin headers de PS1 (prueba nueva).
- G1 con `tests/emu/snoot_check.py` (carga el `snoot.py` de vn-engine-ps1 sin modificarlo): 7 escenarios con
  capturas idénticas a la v1.0. Chat, teclado y créditos terminan con el contador de cuadros ±2; el motor de
  vn-engine-ps1 sin cambios también (teclado 3683 contra 3684): es variación de tiempos del CD, no regresión.
- Oleada 1: T-101, T-205, T-206, T-301 (Kilo, tercer intento), T-402 fusionadas; T-202 en segundo intento. Regla
  nueva en AGENTS.md contra alias y código muerto (todas las ramas de Beam volvieron por eso).
- Chequeo de calidad en `dispatch.py` (ruff, vulture, salto de línea final, pytest) con una ronda de corrección
  del mismo agente antes de la revisión; con el primer intento de Beam en T-402 detecta los alias, las funciones
  muertas y el import sin usar que hubo que pedir a mano. Limpieza de lo que dejó la oleada 1 (`tools/ctl/config.py`
  sin uso, `except Exception`).
- T-201: TRACE en `vm.c` con `VN_TRACE`. Probado en PCSX-Redux: 24 eventos en 3000 cuadros de Snoot; el build normal
  sigue idéntico byte a byte. La TTY solo sale con `-logfile`.
- Oleada 2 lanzada: T-203, T-204, T-302, T-504.
- Oleada 2: el chequeo encontró problemas en las cuatro ramas y tres se corrigieron solas en la ronda. Aun así:
  T-203 rehecho (usaba `-stdout`, imports condicionales y reexports), T-302 rehecho (alias, `__all__`), T-504 sin
  las pruebas pedidas. Tres agentes tocaron `dispatch.py` (prohibido) para esquivar un error mío del chequeo (buscaba
  `.venv` dentro del worktree): ahora el chequeo revisa el alcance de cada tarea y detecta alias y `__all__`.
- G2 cumplida: `ctl run --target ps1` → PASS en 47 s contra una traza del propio motor (`tests/reference/traces/ps1`).
- T-302: 11 rutas grabadas en Ren'Py. `trace_hook.rpy` fallaba con personajes escritos como texto (chapter_x6);
  las rutas 1-3 se quedaban en el teléfono de `textscroll` (minijuego de deslizar): `snoot_capture.rpy` lo devuelve
  solo, únicamente en la copia de captura.
- `Path.write_text` en Windows escribe CRLF: lo usé para editar y convertí archivos LF; corregido. Las trazas se
  guardan con LF.

## 2026-10-27

- Fase 6 y 7 en paralelo con Beam, Kilo, Vibe, Antigravity y Codex. `chapter_x2` PASS contra Ren'Py en PSP, PS2,
  Vita (renderer GXM sin `libshacccg.suprx`), 3DS (traza por `svcOutputDebugString`), Wii (crash por el teclado de
  libwiikeyboard sin iniciar y 180 KB en el stack de `res_get`; traza por USB Gecko), PS4 (dlmalloc propio con
  `MMAP_CLEARS=0`; shadPS4 etiqueta el stdout como `[stdin]`; Makefile sin dependencias de headers reusaba objetos
  viejos), DS (núcleo compartido, traza por DLDI) y GBA (núcleo compartido, datos en GBFS).
- PS3 en pausa: SDL2 del port de ps3dev desde la fuente arregla el audio; el Makefile no pasaba `VN_TRACE`; en RPCS3 el
  flip del RSX se detiene (no es la GPU: probado con la Quadro y Vulkan).
- GBA: el LZ77 tenía las banderas al revés (y el decodificador de prueba también, por eso pasaban las pruebas) y usaba
  distancia 1, que la VRAM no acepta. El texto escribía bytes sueltos en VRAM.
- Fidelidad (D24): la comparación solo veía el texto. `renpy_full` compara fondo, personajes y música por línea. El hook
  de Ren'Py perdía los cambios de expresión, tomaba la música del canal (sigue sonando en el fadeout) y no veía las
  capas de música ni el `scene` real; corregido y regrabadas las 14 rutas. Resultado en PC: x1-x6 y x9 sin
  diferencias.
- Memoria (D25): el backend SDL nunca liberaba texturas, buscaba los sonidos ambientales como imágenes (`I32770.IMG`)
  y en PSP la panorámica de 1328×383 bloquea el renderer (textura máxima 512). Arreglos parciales y T-629 en curso.
- G5 medido en capítulos: Vita, Wii y PS4 10/10; PSP y PS2 10/11.
- Agentes: el despachador ahora mata el árbol de procesos al vencer el tiempo (dejaba OpenCode y emuladores vivos) y
  acepta carpetas en "Archivos permitidos". `beam-free` dejó de responder: OpenCode usa `iceman-contributor-free`.
  Antigravity reportó tres veces capturas que no coincidían con la imagen: medir siempre a ojo antes de fusionar.
- Repositorio remoto creado; `CONTINUAR.md` y `REINSTALAR.md` para retomar después de formatear.
