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

## Pista de agentes
- [x] Logins, Orca y Beam (usuario). Skills de Orca `orca-cli` y `orchestration` instaladas para todos.
- [x] Skills propias, subagentes, plantillas, `agents.toml`, `dispatch.py`, `sync_skills.py` (9 pruebas pasan).
- [ ] `[HUMANO]` Abrir Docker Desktop (Orca CLI ya está en el PATH; las terminales nuevas lo ven).
- [ ] `[HUMANO]` Opcional: Superpowers para Claude (`/plugin install superpowers@claude-plugins-official`).
- [ ] A4: prueba de humo. Pasaron Claude, Antigravity y Codex; faltan 5 Beam, Kilo y Vibe (lanzarlos desde tu terminal).
- [ ] Primera oleada de 5 Beam: T-101, T-202, T-205, T-301, T-402 (PLAN.md sección 8).

## Avisos
- `psxavenc.exe` termina con 0xC0000139 al convertir audio: rompe 1 prueba de wani-ps1
  (`tests/test_programa.py::test_real_chapter_graphics_preserve_branches_and_disc_resources`). No lo causaron los
  cambios de rutas (falla igual sin ellos).
