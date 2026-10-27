# Plan maestro — renpy-console-project

> **Versión:** 0.2 (integrada) · **Fecha:** 2026-10-26 · **Autor:** Pako Tako + agentes IA
> **Une:** el `PLAN.md` v0.1 de este repo y `PLAN_MAESTRO_SNOOT_PORTS.md` v2.0 (copia sin cambios en
> `docs/plan-maestro-agentes.md`, de donde salen las plantillas de agentes de su Parte D).
> **Regla de lectura:** este archivo manda. Si algo choca con el plan maestro v2.0, vale lo de aquí; la tabla de la
> sección 2 dice qué se tomó de cada uno y por qué.
> **Marcadores:** `[HUMANO]` lo haces tú · `[GATE]` compuerta, no se avanza sin cumplirla · `(verificar)` dato
> que cambia entre versiones: confirmarlo con `--help` o la doc oficial antes de usarlo.

---

## 0. Resumen

**Objetivo:** llevar Snoot Game (y después Wani y otros juegos Ren'Py) a todas las consolas posibles con **un
núcleo C99 compartido + un backend por plataforma + un laboratorio de pruebas automático**, partiendo de lo que ya
funciona en PS1.

**Primera meta medible:** Snoot en **PS1, PC, PSP y PS2** desde el mismo núcleo y los mismos datos.

**Lo más importante que cambió en esta versión:** casi la mitad de lo que el plan maestro v2.0 pedía construir
ya existe en los repos hermanos (fuente oficial, línea base PS1 congelada, modo prueba con botones guionados,
captura dentro de Ren'Py, simulador de rutas). El camino rápido es **envolver y reutilizar**, no reescribir:

| Lo que v2.0 pedía construir | Ya existe en | Se usa así |
|---|---|---|
| Fuente oficial como `upstream/` | `snoot-ps1/original/` (con AGPL y CC-BY-SA) y `E:\snoot\snootgame` | Solo lectura; sin submódulo |
| Línea base PS1 congelada (G4) | Tag `v1.0` de `snoot-ps1` | Referencia de regresión |
| Goldens de regresión PS1 | `vn-engine-ps1/tests/emu/snoot.py` (captura píxel a píxel contra v1.0) | Prueba de "cero regresiones" |
| Build "test mode" con entradas guionadas | `AUTOTEST.BIN` + `input_set_script` + `autotest_autoplay` (motor) y `emutest.py` | Base del adapter PS1 del Test Lab |
| Exportador/hook dentro de Ren'Py | `renpy-port-kit/renpykit/compare/kit_capture.rpy` | Se le agrega la salida TRACE |
| Recorrido determinista de rutas | Simulador del kit (`renpykit/simulate`, `rutas.json`) | Elige las opciones de cada ruta |
| Formato intermedio (SnootIR) | Bytecode VNB v3 + compilador `vncompiler/` + simulador | VNB **es** el formato intermedio |
| Core portable + PAL | `engine/core/` + `VnPlatformOps` (este repo, sesión 2026-10-26) | Se completa en la Fase 1 |
| SDL2 dev | MSYS2 ucrt64 trae SDL2 2.32.10 | Sin descarga |
| CLIs de agentes | Instalados: codex, opencode, kilo, vibe, agy, docker, wsl, uv, gh | Falta Orca |

---

## 1. Inventario

### 1.1 Repos en `E:\Dev`

| Repo | Rol | Estado (2026-10-26) |
|---|---|---|
| `renpy-console-project` | **Este repo.** Núcleo multiplataforma, backends, Test Lab, coordinación | Fase 1 en curso |
| `vn-engine-ps1` | Motor PS1 compartido (Snoot, Wani); fuente del núcleo | Bytecode v3 (giro de sprites), 112 pruebas |
| `snoot-ps1` | Port PS1 de Snoot, v1.0 publicada (tag `v1.0`) | Congelado; motor v1.0 en `engine/` |
| `wani-ps1` | Port PS1 de I Wani Hug that Gator! | En desarrollo; 147 pruebas (1 falla por `psxavenc`, ver riesgos) |
| `renpy-port-kit` | Kit genérico Ren'Py: RPA/RPYC, AST, simulador, captura, comparación | 404 pruebas |
| `snoot-ps2` | Intento de port nativo a PS2 | Solo docs; **lo reemplaza la Fase 5** de este plan |

Regla: los repos hermanos no se modifican desde aquí sin permiso; los cambios se proponen con copias o PR. Las
correcciones de rutas viejas sí están autorizadas.

### 1.2 `E:\snoot` (material local, no versionado)

Fuentes Ren'Py (`snootgame`, `I Wani Hug that Gator!`), SDKs de Ren'Py (8.3.7 y otros en `renpy-sdks`),
DuckStation, PCSX-Redux, BIOS de PS1, auditorías visuales y `PLAN_PORT_SNOOTGAME_PS1 d.md` (diseño v4 del port PS1:
menús, 3 ranuras, galería; es la referencia de UI para todos los ports).

---

## 2. Decisiones

| # | Decisión | Origen | Por qué |
|---|---|---|---|
| D1 | **Un núcleo C99 + backends**, nada de 20 motores | v0.1 y v2.0 | Las dos lo dicen |
| D2 | **Este repo es el repo del proyecto** (no se crea `snoot-ports/`) | Ajuste a v2.0 | Ya tiene el núcleo extraído, git y pruebas |
| D3 | **VNB es el formato intermedio** (se descartan SnootIR y VNSCENE) | Ajuste a v2.0 | Ya hay compilador, simulador y motor probados con dos juegos; un IR nuevo duplicaría todo. La forma legible es el guion JSON del kit |
| D4 | **Backend SDL2 compartido** para PC, PSP, PS2, Vita, 3DS, Wii, Xbox clásica, Switch | v2.0 | Un backend cubre 8 plataformas; nativo solo PS1, GBA, DS, GB/GBC |
| D5 | **Toolchains de consola en Docker**; PS1 sigue con PSn00bSDK en MSYS2 | v2.0 + realidad | Los SDK homebrew son Unix-first; PS1 ya funciona nativo |
| D6 | **Backend PC primero** tras consolidar PS1; los bugs de lógica se arreglan en PC | v2.0 | Iterar en PC es mucho más rápido que en emulador |
| D7 | **Modo prueba + protocolo TRACE único** en todas las plataformas | v2.0 + motor actual | El motor ya se autojuega (`AUTOTEST.BIN`); falta que emita trazas comparables |
| D8 | **Test Lab CLI primero** (`tools/ctl`); MCP propio después, opcional | v2.0 sobre v0.1 | Todos los agentes usan una CLI; el MCP no bloquea nada |
| D9 | **Comunicación de agentes por archivos** (`.agents/tasks`, `.agents/reports`) | v2.0 | Ahorra cuota de Claude: lee reportes cortos |
| D10 | **Enjambre de 5 Beam desde ya** en las tareas que no dependen de la pista principal; los demás agentes entran por tarea | Usuario (2026-10-26) | Beam en OpenCode Go no gasta cuota: 5 en paralelo adelantan el Test Lab, las trazas y los recursos mientras Claude lleva la Fase 1 |
| D11 | **Motor MIT; ports AGPL-3.0 + CC-BY-SA 4.0** | Ajuste a v2.0 | El motor no lleva código del juego; el disco/ROM de cada port sí (ver sección 10) |
| D12 | **Coordenadas por perfil**: el compilador VNB genera posiciones por plataforma | Ajuste a v2.0 (pedía 1920x1080 virtual) | Así ya funciona con los perfiles `snoot` y `wani` del compilador |
| D13 | **Solo Snoot, a todas las consolas**; Wani y la Fase 8 quedan en pausa. El núcleo sigue sin nada fijo de un juego | Usuario, 2026-10-26 (antes: Snoot primero, Wani detrás) | La meta es Snoot; Wani se retoma después, ya con el núcleo probado en varias consolas |
| D15 | **API de plataforma por enlace**: `video`, `img`, `res`, `audio`, `input`, `save`, `cd` son funciones C que cada backend implementa (el linker elige); `VnPlatformOps` queda solo para archivos y fuente | Usuario (2026-10-26) | Cada consola compila un solo backend: una tabla de ~60 punteros no aporta y obliga a reescribir ~290 llamadas de `main.c` y arriesga G1 |
| D14 | **Commits:** conventional commits en inglés, sin coautor; la tarea va en el cuerpo (`Refs: T-041`) | Reglas del repo sobre v2.0 | v2.0 pedía `T-xxx: resumen`; se conserva la convención existente |
| D16 | **Snoot solo en español** (traducción oficial `game/tl/es`), en todas las consolas: texto, imágenes con texto traducido (`tl/es/images`) y trazas de referencia | Usuario, 2026-10-26 | Igual que el port de PS1 v1.0; sin selector de idioma. `tools/assetpipe --language es`; `tools/renpy_trace/record.py` graba en `es` |

Descartado de v2.0: el submódulo `upstream/` (D2/inventario), la rama `integration` mientras trabaje un solo agente
(se crea en la Fase 4), y las tablas de cronograma por meses de v0.1 (no eran verificables).

---

## 3. Arquitectura

```
Juego Ren'Py (.rpy oficial)                      Ren'Py SDK (referencia, solo lectura)
        │                                                   │
        ▼                                                   ▼
renpy-port-kit: AST, análisis, simulador ──► rutas ──► kit_capture.rpy ──► trazas de referencia
        │
        ▼
vncompiler (perfil por plataforma) ──► VNB + T##.TXT + recursos por perfil
        │
        ▼
engine/core (C99): vm, scene, text, chapter, lz4, str [+ app/main en Fase 1]
        │  vn_ops (VnPlatformOps)
        ▼
platforms/ps1 (PSn00bSDK) · platforms/sdl (PC, PSP, PS2, Vita, 3DS, Wii, Xbox, Switch) · gba · nds · gb
        │
        ▼
tools/ctl: build · run · trace · compare · report   ◄── agentes (Claude orquesta, el resto implementa)
```

**Reglas de dependencias:** el núcleo no incluye nada de una consola (solo `vn_platform.h`); los backends no tienen
lógica de juego; el conversor no genera C, genera datos.

### 3.1 Estructura del repo (real + lo que se agrega)

```
renpy-console-project/
├─ PLAN.md  STATUS.md  CLAUDE.md  AGENTS.md  README.md
├─ engine/
│  ├─ core/            # C99 portable + vn_platform.h (contrato con los backends)
│  └─ ps1-base/        # copia de referencia de vn-engine-ps1 947cb3b (no se edita)
├─ platforms/
│  ├─ pc/              # backend sin ventana para pruebas de host
│  ├─ ps1/             # backend PSn00bSDK + módulos de hardware
│  ├─ sdl/             # (Fase 4) backend SDL2 compartido
│  └─ psp/ ps2/ ...    # ajustes por plataforma sobre sdl/ (Docker, empaquetado)
├─ tools/
│  ├─ ctl/             # (Fase 2) Console Test Lab
│  ├─ assetpipe/       # (Fase 4) perfiles de recursos por plataforma
│  ├─ agents/          # (Fase 4) dispatch.py, agents.toml, sync_skills.py
│  └─ doctor.py        # (Fase 2) diagnóstico del entorno
├─ tests/
│  ├─ core/            # pruebas C de host
│  ├─ scenarios/       # escenarios del Test Lab (YAML)
│  └─ reference/       # trazas de Ren'Py y goldens por plataforma
├─ docs/               # core-api.md, platform-matrix.md, what-to-download.md, bitacora.md, platforms/<x>.md
└─ .agents/            # (Fase 4) tasks/ reports/ templates/ JOURNAL.md
```

Las carpetas vacías de v0.1 (`engine/audio`, `engine/graphics`, `engine/save-system`, `engine/script-vm`,
`tools/renpy-importer`, `tools/asset-converter`, `tools/compatibility-analyzer`, `tools/console-test-lab`,
`tests/golden-traces`, `tests/visual-regression`) se eliminan: lo que iban a contener vive en las rutas de arriba.

---

## 4. Contratos

| Contrato | Archivo | Dueño | Estado |
|---|---|---|---|
| C1 — Bytecode VNB v3 | `vn-engine-ps1/docs/bytecode.md` | Claude | Vigente; cambiarlo actualiza spec, compilador, simulador y motor juntos |
| C2 — Plataforma | `engine/core/vn_platform.h` (archivos y fuente), headers de la API por enlace (D15), `docs/core-api.md` | Claude | PS1 implementa todo; quitar lo de PS1 de los headers que ve el núcleo (T-102) |
| C3 — TRACE | sección 4.1 | Claude | Nuevo (Fase 2); reemplaza los logs `[ENGINE]` de v0.1 |
| C4 — Escenarios | sección 4.2 | Claude | Nuevo (Fase 2); reemplaza el formato `steps:` de v0.1 |

Solo Claude edita los contratos; los demás agentes proponen cambios en su reporte.

### 4.1 Protocolo TRACE (una línea por evento, igual en todas las plataformas)

```
T|<seq>|<frame>|<EV>|k=v;k=v
T|17|1042|SAY|who=3;text=3121
T|18|1043|SHOW|tag=2;img=140;x=160;y=240
T|19|1100|CHOICE|i=2
T|20|1101|LABEL|name=route_a_intro
T|21|1101|FBHASH|crc=9a3f12c0
```

- Eventos: `LABEL, SAY, SHOW, HIDE, SCENE, PLAY, STOP, MENU, CHOICE, END, ERROR` y `FBHASH` (CRC del cuadro en
  puntos marcados, para regresión por plataforma).
- En el motor sale por `vn_ops->log` desde el `notify` de la VM; solo en builds de prueba.
- En Ren'Py sale de `kit_capture.rpy` (`config.label_callbacks` y la interacción de cada línea) con los mismos
  ids de texto que usa el compilador, así se compara sin depender del texto.

### 4.2 Escenario del Test Lab

```yaml
id: snoot-smoke
reference: tests/reference/traces/snoot/ruta-a.trace
inputs:            # se compila a AUTOTEST.BIN (PS1) o equivalente
  - advance: 12
  - choose: 2
  - advance: 30
expect:
  - {ev: LABEL, name: start}
compare:
  events: [LABEL, SAY, SHOW, HIDE, SCENE, PLAY, STOP, MENU, CHOICE]
  tolerance: {frames: 2}
limits:
  max_seconds: 300
```

`ctl compare` alinea los eventos con la referencia y reporta el **primer evento divergente**.

---

## 5. Plataformas por nivel

| Nivel | Plataformas | Backend | Fidelidad objetivo |
|---|---|---|---|
| **A — SDL** | PC, PSP (PSP Go), PS2, Vita, 3DS, Wii, Xbox clásica, Switch | `platforms/sdl` + ajustes | Todo el juego; video según plataforma |
| **B — Nativo** | PS1 | `platforms/ps1` | Completa con recursos reducidos (ya demostrado) |
| **C — Demake** | GBA, DS | nativo (Butano / BlocksDS) | Texto completo, arte reducido, audio simple, sin video |
| **D — Demake extremo** | GB, GBC | nativo (GBDK-2020) | Texto completo, tiles con tramado, música tracker |
| **R — Investigación** | PS3, PS4, PS5, Xbox 360, Xbox One/Series | — | Documento de factibilidad antes de asignar trabajo |

Detalle por consola (resolución, RAM/VRAM, SDK, imagen Docker, emulador, salida de traza): `docs/platform-matrix.md`.

---

## 6. Roadmap con compuertas

Dos pistas: la **pista principal** es serial y la lleva Claude; la **pista de agentes** se prepara en paralelo y
entra en juego en la Fase 4.

### Fase 0 — Base `[hecha]`
Repo con git, núcleo sin hardware en `engine/core/`, contrato de plataforma con archivos y fuente, backend PS1
que compila, backend PC sin ventana, `pytest` con la prueba de host (VM hasta el primer diálogo de Wani).

### Fase 1 — PS1 sobre el núcleo nuevo
1. Extraer `vn-engine-ps1/app/main.c` (bucle, menús, guardado, galería) y `modules/` al núcleo, separando lo de
   PS1 (botones `psxpad`, VRAM) detrás de `vn_ops`.
2. Sacar lo de PS1 (`psxgpu.h`, VRAM, CLUT) de los headers de la API por enlace que ven `engine/core`, `engine/app` y
   `engine/modules` (D15); lo propio de PS1 queda en `platforms/ps1/`.
3. CMake para armar el ejecutable PS1 desde este repo con los datos de `snoot-ps1`.
4. Correr `vn-engine-ps1/tests/emu/snoot.py check` contra el ejecutable nuevo.

**[GATE G1]** `[cumplida 2026-10-26]` Snoot PS1 armado desde este repo pasa los escenarios de `tests/emu/snoot.py` (título, menús, partida,
cargar, teclado, chat, créditos) **idéntico píxel a píxel** a la referencia v1.0; Wani compila con el mismo núcleo.

### Fase 2 — TRACE y Test Lab v1 sobre PS1
1. TRACE en el motor (C3) y `pal_trace` → `vn_ops->log`.
2. `tools/ctl`: `build`, `run`, `compare`, `report`; primer adapter PS1/PCSX-Redux envolviendo `emutest.py`
   (sin interfaz; la TTY sale con `-logfile <archivo>`: `-stdout` no sirve porque `pcsx-redux.exe` es un
   lanzador que no pasa la salida de `pcsx-redux.main`).
3. Escenarios (C4) que se compilan a `AUTOTEST.BIN`.
4. `tools/doctor.py`: une los `check_env.py` de los repos y el `--smoke` de los CLIs de agentes.

**[GATE G2]** `[cumplida 2026-10-26: PASS en 47 s]` `python -m tools.ctl run --target ps1 --scenario snoot-smoke` da veredicto automático en < 5 min.

### Fase 3 — Referencia Ren'Py
1. `kit_capture.rpy` emite TRACE (C3) además de capturas.
2. Trazas de todas las rutas y finales de Snoot, en español (D16), con el juego publicado → `tests/reference/traces/snoot/`.
3. `ctl compare` de PS1 contra la referencia; las diferencias aceptadas se documentan.

**[GATE G3]** Trazas de referencia de todas las rutas; PS1 coincide en eventos o cada diferencia está explicada.

### Fase 4 — Backend SDL2 en PC (y arranque de la pista de agentes)
1. `platforms/sdl` con SDL2 2.32 de MSYS2; perfil de recursos PC en `tools/assetpipe`.
2. Escenarios de todas las rutas en PC contra la referencia.
3. Desde aquí, todo bug de lógica se reproduce y arregla en PC primero.

**[GATE G4]** PC pasa el 100 % de los escenarios con las tolerancias definidas.

### Fase 5 — PSP y PS2 en paralelo (primera meta)
SDL2 + ajustes por plataforma; toolchains `pspdev/pspdev` y `ps2dev/ps2dev` en Docker (verificar etiquetas);
adapters PPSSPP y PCSX2; perfiles de recursos con los presupuestos de `docs/platform-matrix.md`.

**[GATE G5]** Cada port completa una ruta entera en emulador y pasa ≥ 90 % de escenarios; el resto documentado.

### Fase 6 — Resto del nivel A
Orden por reutilización: **Vita → 3DS → Wii → Xbox clásica → Switch**. Cada una con `docs/platforms/<x>.md`,
imagen Docker, adapter `ctl` y compuerta igual a G5.

### Fase 7 — Demakes (niveles C y D)
**GBA → DS → GB/GBC.** `[HUMANO]` define la fidelidad aceptable **antes** de empezar.

### Fase 8 — Industrializar (Ren'Py → consolas para otros juegos)
`renpy-port-kit` + compilador VNB para juegos sin fuente (descompilador propio, unrpyc, rpycdec) y
`analyze` con reporte de compatibilidad por consola. Wani es el segundo juego de prueba.

### Investigación (no bloquea nada)
PS3 (PSL1GHT), PS4 (OpenOrbis), Xbox 360 (libxenon), PS5, Xbox One/Series: un documento de factibilidad cada una.

### Pista de agentes (en paralelo a las Fases 1–3, lista antes de la Fase 4)

| Paso | Quién | Qué |
|---|---|---|
| A1 | `[HUMANO]` | Logins de los CLIs, Orca instalado `[hecho 2026-10-26]`; abrir Docker Desktop |
| A2 | `[HUMANO]` | Beam responde `[hecho]` |
| A3 | Claude | `AGENTS.md`, skills propias en `.agents/skills/` (+ copia en `.claude/skills/`), subagentes en `.claude/agents/`, plantillas en `.agents/templates/`, `tools/agents/agents.toml`, `dispatch.py`, `sync_skills.py`; skills `orca-cli` y `orchestration` de Orca `[hecho]` |
| A4 | Claude | Prueba de humo `[hecha 2026-10-26]`: 10 agentes en verde, 5 Beam en paralelo sin límites de tasa |

Skills por agente (probado el 2026-10-26): Codex, OpenCode/Beam, Kilo, Vibe y Antigravity leen `.agents/skills/` del
proyecto y `~/.agents/skills/`; Claude lee `.claude/skills/` (las propias se editan en `.agents/skills/` y se copian
con `python tools/agents/sync_skills.py`). Los trabajadores llevan solo las 5 skills propias, `AGENTS.md` y las de
Orca; Superpowers es opcional y solo para Claude.

**[GATE GA]** ≥ 5 agentes entregan reporte y commit en su rama sin escribir fuera de su worktree.

---

## 7. Agentes

| Agente | Asignar | No asignar |
|---|---|---|
| **Claude Code** (jefe) | Contratos, división de tareas, revisión, integración, Fases 1–3 | Trabajo masivo o repetitivo |
| **Codex** | C difícil: núcleo, backend SDL, PS2, bugs de memoria | Conversión masiva de recursos |
| **Kilo + MiMo** | PSP, Vita, empaquetado | Cambios de contratos |
| **Antigravity** | Adapters del Test Lab, reportes HTML, comparador visual (`agy -p` ya funciona sin terminal en 1.4.7) | Código crítico del núcleo |
| **Mistral Vibe** | Revisión de solo lectura, documentación, auditoría de licencias | Código crítico del núcleo |
| **Beam ×5** (OpenCode Go, sin costo) | Volumen: herramientas Python, Test Lab, conversores, pruebas, escenarios, inventarios, análisis de código (contexto de 1M) | Contratos, merges |

- Una tarea = un worktree = una rama `agent/<agente>/<T-xxx>`. Merge a `integration` solo con build OK + `ctl` en
  verde + revisión; `integration` → `main` con todos los escenarios en verde.
- Escalamiento tras dos fallos: Beam → Kilo → Codex → Claude.
- Tareas de ≤ ~400 líneas de cambio; si no, se dividen.
- Reglas comunes de todos los agentes: `AGENTS.md`.

---

## 8. Backlog inicial

| ID | Fase | Agente | Tarea | Depende |
|---|---|---|---|---|
| T-101 | 1 | beam | Mapear `main.c` y `modules/`: qué es lógica y qué es PS1 → `docs/analysis/main-c.md` (Claude lo revisa) | — |
| T-102 | 1 | claude | Headers de la API por enlace sin nada de PS1 (D15) | T-101 |
| T-103 | 1 | claude | `main.c` y `modules/` en `engine/app` y `engine/modules` (`fmv.c` en `platforms/ps1`) `[hecho]` | T-101 |
| T-104 | 1 | claude | CMake PS1 en este repo (Snoot y Wani compilan) `[hecho]` | T-103 |
| T-105 | 1 | claude | `tests/emu/snoot.py check` contra el build nuevo (G1) | T-104 |
| T-201 | 2 | claude | TRACE en el motor | G1 |
| T-202 | 2 | beam | Esqueleto `tools/ctl` (CLI, config, reporte MD) | — |
| T-203 | 2 | beam | Adapter PS1/PCSX-Redux sobre `emutest.py` + parser TRACE | T-201, T-202 |
| T-204 | 2 | beam | Escenarios YAML → `AUTOTEST.BIN` | T-202 |
| T-205 | 2 | beam | `tools/doctor.py` | — |
| T-206 | 5 | beam | Investigar y fijar imágenes Docker de PSP y PS2 → `docs/platforms/psp.md`, `ps2.md` | — |
| T-301 | 3 | beam | TRACE en `kit_capture.rpy` (propuesta para renpy-port-kit; formato de la sección 4.1) | — |
| T-302 | 3 | beam | Trazas de referencia de todas las rutas de Snoot | T-301 |
| T-303 | 3 | beam | `ctl compare` (primer evento divergente) | T-203, T-302 |
| T-401 | 4 | codex | `platforms/sdl` para PC | G3 |
| T-402 | 4 | beam | `tools/assetpipe` perfil PC | — |
| T-501 | 5 | kilo | Port PSP + `docs/platforms/psp.md` | G4 |
| T-502 | 5 | codex | Port PS2 + `docs/platforms/ps2.md` | G4 |
| T-503 | 5 | antigravity | Adapters `ctl` PPSSPP y PCSX2 | T-202 |
| T-504 | 5 | beam | Perfiles de recursos PSP y PS2 | T-402 |
| T-901 | — | vibe | Auditoría de licencias y `CREDITS.md` (antes de cada publicación) | G3 |

**Primera oleada de Beam (5 en paralelo, tras la prueba de humo):** T-101, T-202, T-205, T-301, T-402; T-206 entra
en cuanto se libere uno. Claude sigue con T-102..T-105 en cuanto llegue T-101. Si aparecen errores 429 o
timeouts, se baja `max_parallel` en `agents.toml`.

Dos formas de lanzarlos (mismas tareas, mismos worktrees):
- Sin ventanas: `python tools/agents/dispatch.py batch --agent beam --tasks T-101 T-202 T-205 T-301 T-402 --parallel 5`.
- Para verlos trabajar: una pestaña de Orca por tarea (`orca agent launch --agent opencode --model opencode-go/beam-free`
  en el worktree de cada una).

---

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| Extraer `main.c` rompe Snoot o Wani | G1 exige igualdad píxel a píxel con v1.0; Wani compila con el mismo núcleo |
| `psxavenc.exe` falla con 0xC0000139 (DLL de entrada no encontrada) | Hoy rompe 1 prueba de wani-ps1 (`test_programa.py`); revisar el PATH de MSYS2 antes de la Fase 2 |
| Beam Free termina o no está en tu región | Otro modelo de OpenCode Go en `agents.toml` |
| Cuota de Claude agotada | Reportes cortos; el trabajo masivo a Beam/Codex/Kilo desde la Fase 4 |
| Agentes editan lo mismo | Archivos permitidos por tarea, contratos solo de Claude, worktrees |
| "Compila = terminado" | Compuertas con `ctl` obligatorias |
| Python o pantallas propias del juego | Módulos especiales (`modules/`) y reporte del kit con archivo y línea; no adivinar |
| Memoria en PS1/GBA/GB | Presupuestos por escena en el perfil de recursos |
| CRLF en scripts que van a Docker | `.gitattributes` con `eol=lf` (Fase 4) |

No hacer: mover el port PS1 de `snoot-ps1`; convertir recursos a mano; tener agentes ocupados sin tareas
independientes; dejar que un agente "mejore" la arquitectura sin tarea.

---

## 10. Licencias y publicación

- Snoot Game y Wani: código **AGPL-3.0**, arte y audio **CC-BY-SA 4.0** (las licencias vienen en
  `snoot-ps1/original/`). Ren'Py: MIT.
- El **motor es MIT** (no incluye código de los juegos). Cada **port publicado** (disco, ROM, ejecutable con datos)
  es obra derivada: se publica con el código fuente del port (AGPL) y los recursos convertidos con atribución y
  share-alike (CC-BY-SA).

Antes de publicar cualquier build:
- [ ] Código del port público y enlazado junto al build.
- [ ] Atribución a Cavemanon y autores del juego; `CREDITS.md` en el repo y en el build.
- [ ] Recursos nuevos con licencia compatible con CC-BY-SA 4.0.
- [ ] Avisos de licencias de SDKs y bibliotecas (SDL, PSn00bSDK, Butano...).
- [ ] Sin BIOS, firmware ni claves de consolas.
- [ ] Queda claro que es un port no oficial.
- [ ] T-901 en verde.

---

## 11. Rutas y comandos

| Ruta | Contenido |
|---|---|
| `E:\Dev\renpy-console-project` | Este repo |
| `E:\Dev\vn-engine-ps1` | Motor PS1 compartido (fuente del núcleo) |
| `E:\Dev\snoot-ps1` | Port PS1 v1.0 (tag `v1.0`, no modificar) |
| `E:\Dev\wani-ps1` | Port PS1 de Wani |
| `E:\Dev\renpy-port-kit` | Kit Ren'Py |
| `E:\snoot` | Fuentes, SDKs de Ren'Py, emuladores, BIOS |
| `C:\msys64\usr\local\psn00bsdk` | PSn00bSDK |
| `C:\msys64\ucrt64` | gcc y SDL2 2.32 de host |

```powershell
# Pruebas de este repo
.\.venv\Scripts\python.exe -m pytest

# Regresión PS1 contra v1.0 (en vn-engine-ps1)
.\.venv\Scripts\python.exe tests\emu\snoot.py check

# Entorno de los ports PS1
.\.venv\Scripts\python.exe tools\check_env.py
```
