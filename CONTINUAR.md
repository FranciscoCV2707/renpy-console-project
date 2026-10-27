# Cómo continuar

Guía para retomar el proyecto después de formatear, en otra PC o en una sesión nueva de Claude Code.
Lo que hay que instalar y respaldar está en `REINSTALAR.md`.

## 1. Recuperar el código

```
cd E:\Dev
git clone git@github.com:FranciscoCV2707/renpy-console-project.git
git clone git@github.com:FranciscoCV2707/snoot-game-ps1.git snoot-ps1
```

Las demás carpetas hermanas (`vn-engine-ps1`, `wani-ps1`, `renpy-port-kit`, `snoot-ps2`) **no tienen repositorio
remoto**: si no se respaldaron a mano antes de formatear, se pierden. `renpy-console-project` ya trae copia de lo que
usa de `vn-engine-ps1` (en `engine/ps1-base/`).

Luego, en `E:\Dev\renpy-console-project`:

```
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q          # deben pasar todas (las de consolas van con -m consoles)
```

## 2. Recuperar los datos que no van en git

- `E:\snoot` completo (emuladores, BIOS, firmware, el juego y los SDK de Ren'Py): ver `REINSTALAR.md`.
- `build/` no se respalda: se regenera. Para los adapters de PSP, Vita, Wii, PS4, PS3, 3DS, DS y GBA primero hay que
  generar el disco de PS1: `python -m tools.ctl run --target ps1 --scenario tests/scenarios/snoot-smoke.yaml`.

## 3. Dónde quedó el trabajo

- Estado por consola y pendientes: `STATUS.md`.
- Plan, decisiones (D1-D25) y tabla de tareas (sección 6): `PLAN.md`.
- Historia de lo hecho y de los errores: `docs/bitacora.md`.
- Plan de trabajo siguiente (sprints por plataforma, D26): `docs/sprints.md`.
- Comparación contra Ren'Py: `docs/test-lab.md`, `docs/fidelidad.md`, `docs/g5.md`.
- Cada consola: `docs/platforms/<consola>.md`.

### Tareas que quedaron corriendo al cerrar (2026-10-27)
Sus ramas se subieron al remoto tal como estaban. Si la tarea no terminó, la rama puede estar vacía o a medias:
relánzala con `python tools/agents/dispatch.py run --agent <agente> --task <T-xxx>` (el texto de la tarea está en
`.agents/tasks/`).

| Tarea | Agente | Qué |
|---|---|---|
| T-625 | beam (OpenCode) | Chat del teléfono del capítulo 4 jugable y legible en cada consola |
| T-626 | beam (OpenCode) | Teclado del anuario del capítulo 13D, táctil en DS/3DS/Vita |
| T-627 | beam (OpenCode) | PS3: por qué el flip del RSX se detiene en RPCS3 |
| T-629 | kilo | Imágenes solo mientras se ven (D25), panorámicas en mosaicos, ruta-1 PASS en PSP |

### Siguientes pasos, en orden
1. Revisar y fusionar T-625, T-626, T-627 y T-629 (abrir las capturas y medirlas: los reportes a veces no coinciden).
2. Arreglar el brillo del backend SDL (tinte 128 → 50 %, `platforms/sdl/video.c:233`) y repetir `chapter_x2` en todas.
3. `renpy_full` en las 14 rutas: tomas de cámara de x10 y las rutas largas (seguir lo de T-628 en `docs/fidelidad.md`);
   después pasar los escenarios de ruta a `compare.mode: renpy_full`.
4. G5: las 14 rutas en PSP, PS2, Vita, Wii y PS4 (`docs/g5.md`).
5. Recursos originales en las consolas con memoria de sobra (D24); motor de GB/GBC; Xbox One/Series al final.

## 4. Cómo trabaja el equipo de agentes

- Claude es el líder: escribe las tareas (`.agents/tasks/T-xxx.md`), las lanza con `tools/agents/dispatch.py`, revisa
  los reportes (`reports/T-xxx.md`) y fusiona. Reglas comunes en `AGENTS.md`; reglas del líder en `CLAUDE.md`.
- Agentes y modelos en `tools/agents/agents.toml`: beam (OpenCode, `opencode-go/iceman-contributor-free`), kilo,
  vibe, agy (Antigravity), codex (sin Docker ni emuladores: solo Python).
- Cada tarea corre en su worktree `E:\Dev\renpy-console-wt\T-xxx-<agente>`, rama `agent/<agente>/T-xxx`.
- Commits en inglés con conventional commits; en main siempre con rutas explícitas (`git commit -m ... -- <rutas>`).

## 5. Para una sesión nueva de Claude Code

Decirle: "lee `CLAUDE.md`, `PLAN.md`, `STATUS.md` y `CONTINUAR.md` y sigue con los siguientes pasos". La memoria de
Claude de esta PC (`C:\Users\Pako\.claude\projects\E--Dev\memory\`) no está en git; lo importante ya quedó en `PLAN.md`
(decisiones D13, D16, D24, D25) y en `CLAUDE.md`.
