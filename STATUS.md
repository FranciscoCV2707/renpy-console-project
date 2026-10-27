# STATUS — renpy-console-project

## Fecha: 2026-10-26

## Fase actual
Fases 4-7 en paralelo (D20): PC, PSP y PS2 juegan rutas completas; Vita, 3DS, Wii, Xbox, Switch y PS4 compilan; demakes de GBA y GB en marcha. G1, G2 y G3 cumplidas.

## Hecho
- [x] Repo con git; rutas a `E:\snoot` en este repo y en los hermanos.
- [x] Núcleo en `engine/core/`: `vm`, `scene`, `str`, `lz4` (copia exacta) y `chapter`, `text` sobre `vn_ops`.
- [x] Contrato de plataforma `engine/core/vn_platform.h` con archivos y fuente.
- [x] Backend PS1 (`platforms/ps1/`, compila con PSn00bSDK) y backend PC sin ventana (`platforms/pc/`).
- [x] `pytest`: la prueba de host lleva la VM hasta el primer diálogo de Wani y lo dibuja (1 pasa).
- [x] Plan integrado v0.2: `PLAN.md` une el v0.1 con `PLAN_MAESTRO_SNOOT_PORTS.md` (copia en
  `docs/plan-maestro-agentes.md`); `AGENTS.md` reemplaza a `docs/ai-agent-rules.md`.

## Siguiente (pista principal)
- [x] T-101..T-105: mapa de `main.c`, API de plataforma por enlace sin PS1 (`engine/platform/`), app y módulos en
  `engine/app` y `engine/modules`, CMake PS1 (Snoot y Wani compilan).
- [x] G1: `tests/emu/snoot_check.py` (los 7 escenarios) con capturas idénticas a la v1.0; el contador final de cuadros
  varía ±2, igual que con el motor de vn-engine-ps1 sin cambios (tiempos del CD en el emulador).
- [x] T-202 Test Lab (`python -m tools.ctl`): esqueleto con compare y reporte.
- [x] Fase 2: T-201 TRACE en el motor (`VN_TRACE`), T-203 adapter PS1, T-204 escenarios a `AUTOTEST.BIN`.
  G2: `python -m tools.ctl run --target ps1 --scenario tests/scenarios/snoot-smoke.yaml` → PASS en 47 s (la
  referencia es una traza del propio motor en PS1).
- [x] T-302: trazas de Ren'Py de las 14 rutas en `tests/reference/traces/snoot/`, en español (D16: Snoot solo se
  porta en español), con `python -m tools.renpy_trace.record`. Rutas 1-4: 11-15 min cada una; capítulos extra:
  menos de 1 min. En la copia de captura se saltan el teléfono de `textscroll` y el `renpy.input` del anuario.
- [x] T-303/T-304 (D17): comparación entre motores por id de traducción y hablante (`compare.mode: renpy`, tabla
  armada con el compilador de snoot-ps1 en `build/`); 14 escenarios de ruta (`tests/scenarios/snoot-route-*.yaml`,
  autoplay + `choices`). chapter_x2 coincide 97/97 en PS1 y en PC.
- [x] G3 (2026-10-27): las 14 rutas en PS1 y en PC contra Ren'Py: 13 PASS (las 4 principales completas, 7-9 min
  cada una en PS1, segundos en PC). chapter_x6 difiere por "Trevor & Tana" sin traducir: corregido en el
  compilador de snoot-ps1 (bd822da); falta regenerar sus guiones. Regresión G1 contra la v1.0 repetida: 25 de 25
  capturas idénticas (contador final ±2 en los 3 escenarios largos, como el motor original).
- [ ] Fase 4 (D20, D21, D22): backend SDL en PC con los datos del disco de PS1: título, texto, audio XA/SPU; humo
  propio (`snoot-smoke-pc`). Falta: oír el audio contra los OGG originales.
- [ ] Fase 5: PSP hecha (T-501: chapter_x2 PASS en PPSSPP en 8 s). PS2 (T-502: compila; se cuelga al arrancar en
  PCSX2; segunda ronda con Kilo).
- [ ] Fase 6: Vita fusionada (T-601). 3DS, Wii, Xbox clásica y Switch compilan (T-602..T-605) y entran con T-407
  (`sdl_target.h`, en curso). PS4 compila (T-606, `snoot.pkg`) y entra después de T-407. Adaptador de Vita3K
  (T-608) en curso. Perfiles de recursos de las cinco (T-506).
- [ ] Fase 7: GBA cabe en 32 MB (T-701) y su empaquetador está hecho (T-702, 24,8 MB); GB/GBC cabe en 8 MB (T-703);
  empaquetador de GB/GBC en curso (T-704).
- [x] Licencias y `CREDITS.md` (T-901), guía para jugadores `docs/instalar.md` (T-902), factibilidad del nivel R
  (T-R01, D23: Xbox One/Series, PS4 y PS3 entran; PS5 y Xbox 360 fuera por ahora).
- Emuladores en `E:\snoot` (ver `CLAUDE.md`); faltan MCPX y BIOS de Xbox y claves de Switch (del usuario).

## Pista de agentes
- [x] Logins, Orca y Beam (usuario). Skills de Orca `orca-cli` y `orchestration` instaladas para todos.
- [x] Skills propias, subagentes, plantillas, `agents.toml`, `dispatch.py`, `sync_skills.py` (9 pruebas pasan).
- [x] Docker Desktop 28.5.1 en marcha.
- [x] Plugins de Claude: `clangd-lsp` y `pyright-lsp` (con clangd y pyright instalados). Superpowers descartado.
- [x] A4 / GA: prueba de humo de los 10 agentes en verde (ramas `agent/*/T-001..T-010`).
- [x] Primera oleada: T-101, T-202, T-205, T-206, T-301, T-402 fusionadas (T-301 escaló a Kilo; T-202 lo terminó Claude).
- [x] Chequeo de calidad en `dispatch.py` antes de la revisión, con una ronda de corrección: archivos fuera de la
  tarea, ruff, vulture, alias y `__all__`, salto de línea final, pytest.
- [x] Segunda oleada: T-203, T-204, T-504 fusionadas (las cuatro ramas necesitaron retoques de Claude).
- [x] Tercera oleada: T-303, T-304, T-403, T-505 (Beam) y T-401 (Codex, dos intentos) fusionadas. El chequeo ahora
  también exige `.clang-format` en C nuevo y compara contra el merge-base de la rama.
- [x] Audio por duración (D18): PSP 108 MB y PS2 159 MB (antes 364 MB y 1.35 GB), deterministas.

## Pendientes
- Regenerar los guiones de snoot-ps1 (`build.py --solo-scripts`) cuando terminen las rutas de PS1: trae el arreglo de
  "Trevor & Tana" (commit `bd822da` en snoot-ps1); luego chapter_x6 debería pasar en PS1 y PC.
- Xbox One/Series al final (Visual Studio con UWP, más de 10 GB, y modo desarrollador: con permiso del usuario).
- El repo mezcla CRLF (lo copiado de `ps1-base`) y LF. Propuesta: `.gitattributes` con `eol=lf` y renormalizar.
- Agentes que lanzan PCSX-Redux para probar opciones dejan procesos colgados: revisar `tasklist` al terminar.

## Avisos
- `psxavenc.exe` termina con 0xC0000139 al convertir audio: rompe 1 prueba de wani-ps1
  (`tests/test_programa.py::test_real_chapter_graphics_preserve_branches_and_disc_resources`). No lo causaron los
  cambios de rutas (falla igual sin ellos).
