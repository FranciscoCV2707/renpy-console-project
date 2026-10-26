# STATUS — renpy-console-project

## Fecha: 2026-10-26

## Fase actual
Fase 3 — Referencia Ren'Py. Fases 1 y 2 terminadas: G1 y G2 cumplidas el 2026-10-26.

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
- [ ] T-302: trazas de Ren'Py de las 14 rutas (11 grabadas; rutas 1-3 grabándose tras saltar el teléfono de
  `textscroll`). Rama `agent/beam/T-302` sin fusionar.
- [ ] Fase 3 (T-303): comparar PS1 contra Ren'Py. Falta un id común en las dos trazas: Ren'Py da `who=nombre;
  loc=archivo:línea` y el motor `who=id;text=id`; LABEL solo sale de Ren'Py (el VNB no guarda nombres).

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

## Pendientes
- Audio de los perfiles PSP/PS2 en WAV: PSP pesa 364 MB contra 191 MB de PC. Elegir formato comprimido por consola.
- El repo mezcla CRLF (lo copiado de `ps1-base`) y LF. Propuesta: `.gitattributes` con `eol=lf` y renormalizar.
- Agentes que lanzan PCSX-Redux para probar opciones dejan procesos colgados: revisar `tasklist` al terminar.

## Avisos
- `psxavenc.exe` termina con 0xC0000139 al convertir audio: rompe 1 prueba de wani-ps1
  (`tests/test_programa.py::test_real_chapter_graphics_preserve_branches_and_disc_resources`). No lo causaron los
  cambios de rutas (falla igual sin ellos).
