# STATUS — renpy-console-project

## Fecha: 2026-10-26

## Fase actual
Fase 1 — PS1 sobre el núcleo nuevo (`PLAN.md` sección 6). Fase 0 terminada.

## Hecho
- [x] Repo con git; rutas a `E:\snoot` en este repo y en los hermanos.
- [x] Núcleo en `engine/core/`: `vm`, `scene`, `str`, `lz4` (copia exacta) y `chapter`, `text` sobre `vn_ops`.
- [x] Contrato de plataforma `engine/core/vn_platform.h` con archivos y fuente.
- [x] Backend PS1 (`platforms/ps1/`, compila con PSn00bSDK) y backend PC sin ventana (`platforms/pc/`).
- [x] `pytest`: la prueba de host lleva la VM hasta el primer diálogo de Wani y lo dibuja (1 pasa).
- [x] Plan integrado v0.2: `PLAN.md` une el v0.1 con `PLAN_MAESTRO_SNOOT_PORTS.md` (copia en
  `docs/plan-maestro-agentes.md`); `AGENTS.md` reemplaza a `docs/ai-agent-rules.md`.

## Siguiente (pista principal)
- [ ] T-101: mapear `vn-engine-ps1/app/main.c` y `modules/` (lógica vs PS1).
- [ ] T-102..T-104: ampliar `VnPlatformOps`, mover `main.c` al núcleo, CMake PS1 en este repo.
- [ ] T-105 / G1: `tests/emu/snoot.py check` idéntico a v1.0.

## Siguiente (pista de agentes, `[HUMANO]`)
- [ ] Logins de codex, opencode, kilo, vibe y agy; abrir Docker Desktop; instalar Orca.
- [ ] Probar Beam desde México (`PLAN.md` paso A2).

## Avisos
- `psxavenc.exe` termina con 0xC0000139 al convertir audio: rompe 1 prueba de wani-ps1
  (`tests/test_programa.py::test_real_chapter_graphics_preserve_branches_and_disc_resources`). No lo causaron los
  cambios de rutas (falla igual sin ellos).
