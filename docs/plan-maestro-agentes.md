# PLAN MAESTRO — Snoot Game en todas las consolas posibles, con un equipo de 10 agentes orquestado por Claude Code

> **Versión:** 2.0 · **Fecha:** 26-oct-2026 · **Plataforma de trabajo:** Windows 10/11 (+ WSL2 + Docker para toolchains)
> **Para quién es este documento:**
> 1. **Tú** → solo la Parte A (≈30–60 min, cosas que requieren tus cuentas o permisos de administrador).
> 2. **Claude Code** → todo lo demás. Pégale el prompt de la Parte B y él ejecuta el runbook.
> 3. **Los agentes trabajadores** → leen `AGENTS.md` (Parte D4), que Claude Code genera desde aquí.
>
> **Marcadores usados:**
> `[HUMANO]` = lo haces tú · `[CLAUDE]` = lo hace Claude Code · `[GATE]` = compuerta: no se avanza sin cumplirla · `(verificar)` = dato que cambia entre versiones; el agente debe confirmarlo con `--help` o la doc oficial antes de usarlo.

---

## Índice

0. [Resumen ejecutivo](#0-resumen-ejecutivo)
1. [Qué mejoré respecto al plan anterior](#1-qué-mejoré-respecto-al-plan-anterior)
2. [Arquitectura del equipo de agentes](#2-arquitectura-del-equipo-de-agentes)
3. [Parte A — Preparación (HUMANO)](#3-parte-a--preparación-humano)
4. [Parte B — Prompt de arranque para Claude Code](#4-parte-b--prompt-de-arranque-para-claude-code)
5. [Parte C — Runbook por fases con compuertas](#5-parte-c--runbook-por-fases-con-compuertas)
6. [Parte D — Archivos que Claude Code debe crear (plantillas completas)](#6-parte-d--archivos-que-claude-code-debe-crear)
7. [Parte E — Referencia técnica del port](#7-parte-e--referencia-técnica-del-port)
8. [Parte F — Backlog inicial de tareas](#8-parte-f--backlog-inicial-de-tareas)
9. [Parte G — Riesgos, límites y solución de problemas](#9-parte-g--riesgos-límites-y-solución-de-problemas)
10. [Parte H — Checklist de publicación y licencias](#10-parte-h--checklist-de-publicación-y-licencias)
11. [Fuentes](#11-fuentes)

---

## 0. Resumen ejecutivo

**Objetivo:** terminar y multiplicar los ports de *Snoot Game* (visual novel de Ren'Py) partiendo del port de PS1 que ya funciona, con un pipeline reutilizable: **Ren'Py → formato intermedio (SnootIR) → motor C portable → backends por consola → pruebas automáticas en emuladores**.

**Equipo (10 agentes):** Claude Code (jefe) + Codex + KiloCode/MiMo + Antigravity + Mistral Vibe + 5× OpenCode con Beam Free.

**Decisiones clave (las 8 que más aceleran):**

| # | Decisión | Por qué |
|---|----------|---------|
| 1 | **Usar el código fuente oficial de Snoot Game** (repositorio de Cavemanon) en lugar de descompilar `.rpyc` | El juego es libre: código AGPL-3 y assets CC-BY-SA 4.0. Tener los `.rpy` originales elimina toda la incertidumbre de la descompilación. Tu descompilador queda para *otros* juegos y para validar. |
| 2 | **Orca** como cabina (cockpit) y orquestación | Repo verificado: ~100k estrellas, MIT, instalador oficial de Windows, soporta Claude Code, Codex, OpenCode, Kilocode, MiMo Code, Antigravity y Mistral Vibe. |
| 3 | **Despachador headless propio** (`tools/agents/dispatch.py`) como segunda vía | Para lanzar enjambres de Beam en lote sin abrir terminales, con worktree, timeout y log por tarea. Si Orca cambia o falla, el proyecto no se detiene. |
| 4 | **Toolchains de consola en Docker/WSL2** | Los SDK homebrew son Unix-first. Con imágenes Docker oficiales (ps2dev, pspdev, vitasdk, devkitpro) los agentes compilan igual en cualquier worktree. |
| 5 | **Backend SDL compartido** para PC, PSP, PS2, Vita, 3DS, Switch, Wii y Xbox | SDL tiene ports para esas plataformas. Un solo backend bien abstraído cubre 8 plataformas; solo PS1, GBA, DS y GB/GBC necesitan backend nativo. |
| 6 | **Backend PC de referencia** + **Console Test Lab** CLI-first | Iterar en PC es 10–50× más rápido que en emulador. Los ports se validan comparando trazas contra el Ren'Py original. |
| 7 | **Builds en "modo prueba"** que reproducen entradas y emiten trazas `TRACE` por consola | No hace falta inyectar botones en cada emulador: el propio motor se autojuega y reporta. El emulador solo arranca y captura el log. |
| 8 | **Comunicación por archivos** (tareas y reportes en `.agents/`) | Ahorra cuota de Claude: él lee reportes cortos, no salidas gigantes de terminal. Beam (gratis) hace el trabajo pesado. |

---

## 1. Qué mejoré respecto al plan anterior

| Plan anterior | Problema | Plan 2.0 |
|---|---|---|
| "Mejorar el descompilador" como pilar | Snoot Game publica su código fuente bajo AGPL-3 + CC-BY-SA 4.0 | Fuente oficial como `upstream/` de solo lectura. Descompilador = herramienta genérica para otros juegos (Fase 12). |
| Advertencia vaga sobre licencias | No decía qué obligaciones hay | Obligaciones concretas: publicar código de cada port (AGPL), atribución y share-alike de assets (CC-BY-SA). Ver Parte H. |
| Orca "≈104 000 estrellas" sin verificar | Dato no comprobado | Verificado: ~100.6k estrellas, MIT, `.exe` oficial, lista de agentes soportados que incluye los 6 tuyos. |
| hcom / Ruflo / Superset como alternativas | Más piezas, más conflictos | Orca + despachador propio. Nada más. |
| `codex exec --full-auto` | Codex lo marca como obsoleto | `codex exec --sandbox workspace-write`. |
| Antigravity tratado como agente headless más | `agy -p` tiene bugs documentados sin TTY en Windows (salida perdida o cuelgue) | Antigravity trabaja **interactivo dentro de una terminal de Orca**, no por subprocess. |
| Compilar en Windows nativo | SDKs homebrew pensados para Linux | Docker Desktop + WSL2 con imágenes oficiales por consola. |
| Un backend por consola | 13+ backends = 13+ proyectos | SDL para 8 plataformas; nativo solo para 4. |
| Pruebas inyectando entradas por emulador | Cada emulador tiene API distinta | Build "test-mode": guion de entradas embebido + traza por TTY/log. |
| Traza de referencia "a mano" | Sin método concreto | Hook `.rpy` con `config.label_callbacks`, `config.start_interact_callbacks` y `renpy.get_filename_line()` + autoselección de opciones. |
| Sin presupuestos de hardware | Expectativas irreales en GB/GBA | Tabla de RAM/VRAM/resolución y "tiers" de fidelidad por consola. |
| Prompt maestro genérico | Sin compuertas ni definiciones de terminado | Runbook por fases con `[GATE]`, DoD por tipo de tarea y escalera de escalamiento. |

---

## 2. Arquitectura del equipo de agentes

### 2.1 Diagrama

```
                         ┌──────────────────────────────────────┐
                         │  TÚ  (decisiones irreversibles,       │
                         │       logins, aprobaciones)           │
                         └──────────────────┬───────────────────┘
                                            │
                    ┌───────────────────────▼────────────────────────┐
                    │  CLAUDE CODE — Arquitecto / Orquestador / QA     │
                    │  • escribe specs y tareas (.agents/tasks)        │
                    │  • dueño de interfaces (engine/pal, SnootIR)     │
                    │  • revisa (subagente port-reviewer) y fusiona    │
                    └───────┬───────────────────────────┬─────────────┘
                            │                           │
          ┌─────────────────▼──────────┐   ┌────────────▼─────────────────┐
          │ ORCA (cockpit + orquest.)  │   │ dispatch.py (lotes headless)  │
          │ terminales interactivas,   │   │ worktree + timeout + log      │
          │ worktrees, diffs, móvil    │   │ por (tarea, agente)           │
          └───┬─────────┬─────────┬────┘   └───┬───────────┬──────────────┘
              │         │         │            │           │
        ┌─────▼───┐ ┌───▼────┐ ┌──▼──────┐ ┌───▼────┐ ┌────▼──────────────┐
        │ Codex   │ │Antigrav│ │ Vibe    │ │ Kilo   │ │ Beam ×5 (OpenCode)│
        │ C duro, │ │Test Lab│ │revisor, │ │ + MiMo │ │ assets, tests,    │
        │ PS2/SDL │ │adapters│ │docs,    │ │ PSP /  │ │ converters, IR,   │
        │         │ │ Vita   │ │licencias│ │ Vita   │ │ escenarios        │
        └─────────┘ └────────┘ └─────────┘ └────────┘ └───────────────────┘
              │         │         │            │           │
              └─────────┴─────────┴─────┬──────┴───────────┘
                                        ▼
                 git worktrees  agent/<agente>/<T-xxx>  →  integration  →  main
                                        ▼
                 Console Test Lab (ctl): build · run · trace · compare · report
```

### 2.2 Roles y enrutamiento

| Agente | Modelo | Fortalezas | Asignar | NO asignar |
|---|---|---|---|---|
| **Claude Code (jefe)** | Opus/Sonnet según tarea | Arquitectura, specs, revisión, integración | Interfaces (`engine/pal/*.h`, esquema SnootIR), revisión de PRs, desbloqueos | Trabajo masivo o repetitivo (gasta tu cuota) |
| **Codex** | El de tu plan | C/C++ difícil, depuración profunda | Core del motor, backend SDL, PS2, bugs de memoria | Conversión masiva de assets |
| **KiloCode + MiMo** | MiMo (token plan) | Implementación media, refactor | Backend PSP, Vita, empaquetado | Cambios de interfaces |
| **Antigravity** | El de tu plan | Navegador/UI, herramientas visuales | Adapters del Test Lab, reportes HTML, comparador visual | Tareas headless (usa siempre su terminal en Orca) |
| **Mistral Vibe** | Mistral | Segunda opinión independiente | Revisión de solo lectura, documentación, auditoría de licencias/créditos | Código crítico del core |
| **Beam 1–5** | `opencode-go/beam-free` | Rápido, gratis, contexto 1M | Conversores de assets, pruebas, escenarios, exportador IR, scripts, inventarios | Arquitectura, decisiones de interfaz, merges |

### 2.3 Escalera de escalamiento

Si una tarea falla **dos veces** con el mismo agente: `Beam → Kilo/MiMo → Codex → Claude Code`. El siguiente recibe el reporte del intento previo.

### 2.4 Límites de concurrencia (iniciales)

| Recurso | Inicio | Máximo | Subir cuando |
|---|---|---|---|
| Beam en paralelo | 3 | 5 | 1 día sin errores 429/timeouts |
| Agentes escribiendo código a la vez | 4 | 6 | Los merges no generan conflictos |
| Builds Docker simultáneos | 2 | nº núcleos ÷ 4 | CPU < 80 % sostenido |
| Revisores de solo lectura | ilimitado | — | — |

### 2.5 Flujo de vida de una tarea

```
backlog (.agents/tasks/T-xxx.md, estado: todo)
  → Claude asigna agente y la marca "assigned"
  → dispatch.py / Orca crea worktree  ../snoot-wt/T-xxx-<agente>  rama agent/<agente>/T-xxx
  → el agente trabaja, hace commit, escribe .agents/reports/T-xxx.md
  → Claude: build + ctl + subagente port-reviewer
       ├─ OK      → git merge --no-ff a integration → estado "done"
       └─ Falla   → feedback en la tarea → reintento o escalamiento
  → periódicamente: integration → main (solo con todos los escenarios en verde)
```

---

## 3. Parte A — Preparación (HUMANO)

> Todo lo de esta sección requiere tus cuentas, ventanas de login o permisos de administrador. Lo demás lo hace Claude Code.

### A1. Software base (PowerShell como **administrador**)

```powershell
# Base
winget install --id Git.Git -e
winget install --id GitHub.GitLFS -e
winget install --id GitHub.cli -e
winget install --id Python.Python.3.12 -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id astral-sh.uv -e
winget install --id Gyan.FFmpeg -e
winget install --id Kitware.CMake -e
winget install --id Microsoft.PowerShell -e
winget install --id Microsoft.WindowsTerminal -e
winget install --id 7zip.7zip -e

# WSL2 + Docker (requiere reinicio)
wsl --install -d Ubuntu
winget install --id Docker.DockerDesktop -e
```

Después del reinicio: abre Docker Desktop → *Settings → General → Use the WSL 2 based engine* (activado) → *Resources → WSL integration → Ubuntu* (activado).

Configuración de Git (en PowerShell normal):

```powershell
git config --global core.longpaths true
git config --global core.autocrlf false
git config --global init.defaultBranch main
git config --global user.name  "TU_NOMBRE"
git config --global user.email "TU_CORREO"
```

> `core.autocrlf false` + el `.gitattributes` de la Parte D evitan que los Makefiles y scripts lleguen con CRLF a los contenedores Linux (causa nº 1 de builds rotos en Windows).

### A2. Los 6 CLIs de IA

```powershell
# Claude Code (instalador nativo oficial)
irm https://claude.ai/install.ps1 | iex

# Codex
npm install -g @openai/codex

# OpenCode (para Beam)
npm install -g opencode-ai

# Kilo Code CLI (fork de OpenCode)
npm install -g @kilocode/cli

# Mistral Vibe
uv tool install mistral-vibe
```

**Antigravity CLI (`agy`)**: instálalo siguiendo la guía oficial (antigravity.google/docs/cli-overview). Tener la app gráfica no garantiza tener `agy` en el PATH.

Cierra y vuelve a abrir la terminal para que se actualice el PATH.

### A3. Logins (solo tú puedes hacerlos)

```powershell
claude                    # inicia sesión con tu cuenta Claude y sal con /exit
codex login
opencode auth login       # elige OpenCode Go / OpenCode Zen y pega tu clave
kilo                      # configura tu proveedor Xiaomi MiMo (token plan) y sal
vibe --setup              # o simplemente `vibe` la primera vez; pide tu API key
agy                       # login OAuth de Google
```

### A4. Prueba crítica: ¿Beam funciona desde México?

Beam Free está marcado por OpenCode como **"regiones limitadas"** y **tiempo limitado**. Pruébalo antes de diseñar nada alrededor de él:

```powershell
opencode models opencode-go          # debe aparecer opencode-go/beam-free
opencode run -m opencode-go/beam-free "Responde solo: OK"
```

- Si responde `OK` → perfecto.
- Si falla por región → usa otro modelo de tu plan Go para los 5 "Beam" (cambia una línea en `agents.toml`, Parte D8). Todo el plan sigue igual.

### A5. Orca

1. Descarga e instala `orca-windows-setup.exe` desde los releases oficiales de `stablyai/orca` (o desde onorca.dev/download).
2. Abre Orca → agrega la carpeta de tu proyecto.
3. En *Settings*, activa **Orca CLI** (la ubicación del interruptor cambia entre versiones; búscalo como "Orca CLI").
4. Si tu versión tiene la orquestación detrás de una opción experimental, actívala.
5. Abre una terminal nueva y verifica: `orca status --json`.
6. (Opcional) instala la app móvil de Orca para recibir avisos cuando un agente termine.

### A6. Tu repositorio actual

- Ten a mano la ruta de tu proyecto actual (engine PS1 + descompilador), por ejemplo `D:\snoot-ports`.
- **Haz un respaldo completo** (zip) antes de entregárselo a los agentes.
- Si todavía no es repo Git, Claude Code lo inicializará en la Fase 2.

### A7. Lo que Claude Code te pedirá confirmar durante el proceso

- Instalar emuladores y SDKs (descargas grandes).
- Cualquier `git push` a un remoto.
- Borrar worktrees o ramas.
- Publicar builds.

---

## 4. Parte B — Prompt de arranque para Claude Code

Abre una terminal en la carpeta del proyecto (o la terminal de Claude dentro de Orca), ejecuta `claude` y pega esto:

````text
Eres el arquitecto y orquestador del proyecto "Snoot Ports". Lee COMPLETO el archivo
PLAN_MAESTRO_SNOOT_PORTS.md que está en la raíz y trátalo como tu especificación.

Reglas de ejecución:
1. Sigue el runbook de la Parte C en orden, fase por fase. No te saltes ningún [GATE].
2. Lo marcado [HUMANO] ya lo hice o te lo haré cuando me lo pidas; si algo falta,
   detente y dime exactamente qué comando debo correr.
3. Antes de usar cualquier comando marcado (verificar), confírmalo con --help
   o la documentación oficial y corrige el plan si cambió.
4. No modifiques el port de PS1 existente hasta completar la Fase 4 (línea base
   congelada y reproducible).
5. Tú diseñas, divides, revisas e integras. El trabajo masivo lo delegas a los
   agentes según la tabla de enrutamiento (sección 2.2). Cuida mi cuota de Claude.
6. Pide mi confirmación antes de: descargas mayores a 1 GB, git push, borrar
   ramas/worktrees, o cualquier acción irreversible.
7. Al terminar cada fase, escribe un resumen de máximo 15 líneas en
   .agents/JOURNAL.md y dime: qué se hizo, qué compuerta se cumplió, qué sigue.

Empieza por la Fase 1 (diagnóstico del entorno).
````

---

## 5. Parte C — Runbook por fases con compuertas

> Cada fase indica: **objetivo · pasos · quién · compuerta**. Las tareas `T-xxx` están detalladas en la Parte F.

### Fase 1 — Diagnóstico del entorno `[CLAUDE]`

1. Crear `tools/doctor.py` (Parte D10) y ejecutarlo:
   ```powershell
   python tools/doctor.py
   python tools/doctor.py --smoke    # prueba real de cada CLI con un prompt mínimo
   ```
2. Si falta algo instalable sin admin, instalarlo; si requiere admin o login, pedírmelo con el comando exacto.
3. Comprobar Docker: `docker run --rm hello-world`.

**[GATE G1]** Todos los obligatorios en verde. `agy` puede quedar como opcional. Beam responde, o hay modelo sustituto definido.

### Fase 2 — Esqueleto del repositorio y configuración de agentes `[CLAUDE]`

1. Si no es repo: `git init`, primer commit con TODO lo existente **sin mover nada**.
2. Crear ramas: `integration` desde `main`.
3. Crear la estructura de la Parte D1 **solo para carpetas nuevas** (no reorganizar el código existente todavía).
4. Crear archivos: `.gitattributes`, `.gitignore` (D2), `CLAUDE.md` (D3), `AGENTS.md` (D4), `.claude/settings.json` (D5), subagentes (D6), `opencode.json` (D7), `tools/agents/agents.toml` (D8), `dispatch.py` (D9), `sync_skills.py` (D11), plantillas `.agents/templates/` (D12), skills propias en `skills/` (D13).
5. Instalar skills de terceros (sección E11) y sincronizar las propias:
   ```powershell
   python tools/agents/sync_skills.py
   ```
6. Agregar el upstream de Snoot Game como submódulo de solo lectura (ver E1):
   ```powershell
   git submodule add https://git.snootgame.xyz/Cavemanon/SnootGame.git upstream/snootgame
   ```
   (verificar) la URL de clonado exacta en la página del repo; si el host no responde, pedirme una copia.
7. Commit: `chore: bootstrap multi-agent workspace`.

**[GATE G2]** `python tools/agents/dispatch.py list-agents` lista los agentes; `git worktree list` funciona; `upstream/snootgame` contiene `game/*.rpy`.

### Fase 3 — Prueba de humo del equipo `[CLAUDE]`

1. Crear tareas `T-001` a `T-006` (Parte F): cada agente escribe `docs/smoke/<agente>.md` con su versión, modelo y un resumen de 10 líneas de `AGENTS.md`.
2. Lanzar Beam ×3 en lote:
   ```powershell
   python tools/agents/dispatch.py batch --agent beam --tasks T-001 T-002 T-003 --parallel 3
   ```
3. Lanzar Codex, Kilo y Vibe con `dispatch.py run`.
4. Antigravity: abrir una terminal en Orca dentro de su worktree y darle la tarea interactiva (o con `orca orchestration dispatch ... --inject`, ver E10).
5. Revisar reportes en `.agents/reports/` y estados en `.agents/status/`.
6. Probar subir a 5 Beam simultáneos con tareas triviales y observar errores 429/timeouts.

**[GATE G3]** ≥ 5 agentes entregan reporte y commit en su rama; ningún agente escribió fuera de su worktree; concurrencia máxima de Beam medida y anotada en `agents.toml`.

### Fase 4 — Congelar y medir el port de PS1 `[CLAUDE + Codex]`

1. Auditoría de solo lectura del código existente (subagente `renpy-analyst` + Beam): inventario de módulos, dependencias, formato de datos actual, scripts de build, cómo se generó cada asset.
2. Escribir `docs/platforms/ps1.md` y `docs/CONTEXT.md` (vocabulario del proyecto).
3. Hacer el build reproducible: documentar toolchain (PSn00bSDK + GCC mipsel), scripts, versión exacta. Si el build actual depende de pasos manuales, convertirlos en script.
4. Generar `.iso/.bin+.cue` y registrar hash SHA-256.
5. Etiquetar: `git tag ps1-baseline-v1`.
6. Correr el port en PCSX-Redux y DuckStation; capturar log (`-stdout`) y screenshots de 5 escenas clave como *golden* de regresión.

**[GATE G4]** Build de PS1 reproducible desde cero con un solo comando; hash registrado; tag creado; goldens guardados.

### Fase 5 — Referencia Ren'Py (la "verdad") `[Beam + Claude]`

1. Identificar la versión de Ren'Py que usa el upstream y descargar ese SDK a `tools/sdk/renpy-<ver>/`.
2. Ejecutar el juego original desde el SDK (sin modificar `upstream/`, trabajando en una copia `build/renpy-ref/`).
3. Implementar el **exportador IR** (E3): corre *dentro* del runtime de Ren'Py y vuelca el AST a `build/ir/snoot.ir.json`.
4. Implementar el **hook de traza** (E4) y la **autoselección de opciones** para recorrer rutas de forma determinista.
5. Generar trazas de referencia por ruta: `tests/reference/traces/<ruta>.jsonl` + capturas en puntos clave.
6. Inventario de assets: imágenes, audio, video, fuentes, con tamaños y uso por escena (`build/ir/assets.json`).

**[GATE G5]** IR que cubre el 100 % de labels del juego o lista explícita de nodos no soportados; trazas de referencia de todas las rutas/finales; inventario de assets completo.

### Fase 6 — Console Test Lab v1 sobre PS1 `[Antigravity + Beam + Codex]`

1. Crear `tools/ctl` (E9) con: `ctl build`, `ctl run`, `ctl trace`, `ctl compare`, `ctl report`.
2. Primer adapter: **PS1 / PCSX-Redux** (el port ya funciona, así que valida el laboratorio y no el port).
3. Añadir al motor PS1 el **modo prueba**: guion de entradas embebido + líneas `TRACE` por `printf` (salen por `-stdout` en PCSX-Redux).
4. Escenario 1 de punta a punta: arrancar → avanzar N diálogos → elegir opción → comparar traza con la referencia.

**[GATE G6]** `ctl run --target ps1 --scenario smoke` produce un reporte con veredicto automático en < 5 minutos.

### Fase 7 — Core portable + PAL `[Claude (interfaces) + Codex (implementación)]`

1. Claude escribe `engine/pal/*.h` (E5) y el esquema `SnootIR` v1 (E2) como contratos. **Solo Claude los edita.**
2. Codex extrae del port PS1 la lógica independiente de plataforma hacia `engine/core/` (VM de escenas, estado, variables, texto, guardado lógico).
3. El backend PS1 pasa a implementar la PAL. Requisito: **cero regresiones** frente a los goldens de G4.

**[GATE G7]** PS1 compila con la nueva arquitectura y pasa los mismos escenarios que en G6.

### Fase 8 — Backend PC de referencia (SDL) `[Codex + Beam]`

1. `engine/backends/sdl/` sobre SDL (2 o 3, según disponibilidad en consolas destino; ver E6).
2. Pipeline de assets "PC" (alta calidad) en `tools/assetpipe/`.
3. Todos los escenarios contra las trazas de referencia de Ren'Py.

**[GATE G8]** PC pasa 100 % de escenarios con tolerancias definidas. **Desde aquí, cualquier bug lógico se reproduce y arregla en PC primero.**

### Fase 9 — PSP y PS2 en paralelo `[Kilo/MiMo → PSP, Codex → PS2, Beam → assets]`

1. Ambos sobre el backend SDL + ajustes por plataforma (memoria, formatos de textura y audio).
2. Toolchains en Docker: `pspdev/pspdev`, `ps2dev/ps2dev`.
3. Adapters ctl: PPSSPP (PSP) y PCSX2 (PS2).
4. Pipelines de assets con presupuestos de la tabla E7.

**[GATE G9]** Cada port arranca, completa al menos una ruta completa en emulador y pasa ≥ 90 % de escenarios; los fallos restantes documentados.

### Fase 10 — Plataformas SDL restantes `[reparto según carga]`

Orden sugerido por reutilización: **PS Vita → 3DS → Wii → Xbox clásica → Switch**. Cada una con su `docs/platforms/<x>.md`, imagen Docker, adapter ctl y gate igual a G9.

### Fase 11 — Demakes nativos `[Codex + Beam]`

**GBA (Butano/devkitARM) → DS (BlocksDS) → GB/GBC (GBDK-2020)**. Requieren pipelines de assets agresivos (E8). Definir con el usuario el nivel de fidelidad aceptable **antes** de empezar (`[HUMANO]` decide).

### Fase 12 — Industrializar `rp2c` (Ren'Py → consolas) `[Claude + Beam]`

1. Generalizar exportador + pipeline para otros juegos Ren'Py.
2. Integrar tu descompilador / `unrpyc` / `rpycdec` para juegos sin fuente.
3. `rp2c analyze <juego>` → reporte de compatibilidad por consola (qué nodos, ATL, Python y assets no se soportan).

### Investigación aparte (no bloquea nada)

PS3 (PSL1GHT), PS4 (OpenOrbis), Xbox 360 (libxenon), PS5: cada una con un documento de factibilidad antes de asignar trabajo.

---

## 6. Parte D — Archivos que Claude Code debe crear

### D1. Estructura del repositorio

> Adaptar a lo existente: **no mover el código del port PS1 antes del GATE G4**.

```
snoot-ports/
├─ PLAN_MAESTRO_SNOOT_PORTS.md
├─ CLAUDE.md                     # instrucciones del orquestador
├─ AGENTS.md                     # reglas comunes a todos los agentes
├─ LICENSE                       # AGPL-3.0 (código)
├─ LICENSES/CC-BY-SA-4.0.txt     # assets
├─ CREDITS.md                    # atribuciones (Cavemanon + contribuyentes)
├─ upstream/snootgame/           # submódulo, SOLO LECTURA
├─ engine/
│  ├─ core/                      # C99 portable: VM, estado, texto, saves lógicos
│  ├─ pal/                       # contratos de plataforma (*.h) — dueño: Claude
│  └─ backends/
│     ├─ sdl/                    # PC, PSP, PS2, Vita, 3DS, Wii, Xbox, Switch
│     ├─ ps1/  gba/  nds/  gb/   # nativos
├─ ports/<plataforma>/           # build, empaquetado, Dockerfile de referencia
├─ tools/
│  ├─ doctor.py
│  ├─ agents/  dispatch.py  agents.toml  sync_skills.py
│  ├─ renpy_export/              # exportador IR + hook de traza
│  ├─ assetpipe/                 # conversores por plataforma
│  ├─ ctl/                       # Console Test Lab
│  ├─ decompiler/                # tu descompilador existente
│  ├─ sdk/  emulators/           # descargas locales (ignoradas por git)
├─ tests/
│  ├─ scenarios/*.yaml
│  └─ reference/{traces,frames}/
├─ skills/                       # 5 skills propias (fuente de verdad)
├─ docs/ CONTEXT.md  adr/  platforms/<plataforma>.md  smoke/
├─ .claude/ settings.json  agents/  skills/
└─ .agents/ tasks/ reports/ status/ logs/ inbox/ templates/ JOURNAL.md
```

### D2. `.gitattributes` y `.gitignore`

```gitattributes
* text=auto eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf
*.png binary
*.jpg binary
*.ogg binary
*.opus binary
*.wav binary
*.webm binary
*.iso binary
*.bin binary
```

```gitignore
build/
dist/
tools/sdk/
tools/emulators/
.agents/inbox/
.agents/logs/
.agents/status/
*.iso
*.chd
*.elf
*.pbp
*.vpk
*.3dsx
*.nds
*.gba
*.gb
*.gbc
__pycache__/
.venv/
.env
```

### D3. `CLAUDE.md`

````markdown
# CLAUDE.md — Orquestador de Snoot Ports

Lee primero PLAN_MAESTRO_SNOOT_PORTS.md (especificación completa) y docs/CONTEXT.md.

## Tu rol
Arquitecto, orquestador e integrador. Diseñas, divides, revisas y fusionas.
No implementas trabajo masivo: lo delegas (tabla 2.2 del plan).

## Reglas de oro
1. Una tarea = un worktree = una rama `agent/<agente>/<T-xxx>` = un agente.
2. Eres el ÚNICO que edita `engine/pal/*.h`, `docs/ir/SnootIR.md` y `tools/agents/agents.toml`.
3. Nadie toca `upstream/` ni el tag `ps1-baseline-v1`.
4. Merge a `integration` solo si: build OK + `ctl` en verde + subagente `port-reviewer` aprueba.
5. Lees reportes (`.agents/reports/`), no logs completos. Logs solo si el reporte no basta.
6. Falla dos veces → escala (Beam → Kilo → Codex → tú).
7. Beam empieza con 3 en paralelo; ver `max_parallel` en agents.toml.
8. Pide confirmación al usuario para: push, borrar ramas/worktrees, descargas > 1 GB, publicar.
9. Al cerrar cada fase: resumen ≤ 15 líneas en `.agents/JOURNAL.md`.

## Herramientas
- Lotes headless: `python tools/agents/dispatch.py run|batch|status|remove`
- Orca: skills `orca-cli` y `orchestration`. Antes de mutar estado de orquestación,
  ejecuta `orca skills get orchestration --full` (los comandos cambian entre versiones).
- Pruebas: `python -m tools.ctl ...`
- Diagnóstico: `python tools/doctor.py`

## Cómo escribir una tarea
Usa `.agents/templates/TASK.md`. Toda tarea tiene: objetivo, contexto mínimo (rutas exactas),
archivos permitidos, archivos prohibidos, pasos de verificación ejecutables y DoD.
Si una tarea necesita más de ~400 líneas de cambio, divídela.

## Definición de terminado (DoD) por tipo
- Código del motor: compila en PC y en la plataforma afectada; escenarios ctl en verde; sin warnings nuevos.
- Conversor de assets: determinista (mismo input → mismo hash); respeta presupuesto de memoria; tests.
- Adapter ctl: escenario `smoke` pasa en esa plataforma; documentado en docs/platforms.
- Documentación: rutas y comandos verificados ejecutándolos.
````

### D4. `AGENTS.md` (lo leen Codex, OpenCode/Beam y Kilo de forma nativa; a Vibe y Antigravity se lo indica el prompt)

````markdown
# AGENTS.md — Reglas para TODOS los agentes de Snoot Ports

## Antes de empezar
1. Tu tarea está en `.agents/inbox/<T-xxx>.md`. Léela completa.
2. Trabajas SOLO dentro de este directorio (tu worktree). Nunca escribas fuera.
3. Lee `docs/CONTEXT.md` para el vocabulario del proyecto.

## Prohibido
- Editar `engine/pal/*.h`, `docs/ir/SnootIR.md`, `tools/agents/agents.toml`, `upstream/**`.
  Si crees que deben cambiar, propónlo en tu reporte.
- `git push`, `git merge`, `git rebase`, `git reset --hard`, borrar ramas.
- Tocar archivos fuera de la lista "Archivos permitidos" de tu tarea.
- Inventar resultados: pega la salida REAL de los comandos de verificación.
- Descargar SDKs o emuladores (ya están en tools/ o en Docker).

## Cómo compilar
- Toolchains de consola: SIEMPRE vía Docker con la imagen indicada en docs/platforms/<x>.md.
  Ejemplo: `docker run --rm -v "${PWD}:/src" -w /src pspdev/pspdev:latest make -C ports/psp`
- PC: `cmake -S . -B build/pc && cmake --build build/pc`

## Al terminar
1. Ejecuta los pasos de verificación de tu tarea.
2. `git add` solo de archivos permitidos y `git commit -m "<T-xxx>: <resumen>"`.
3. Escribe `.agents/reports/<T-xxx>.md` con la plantilla `.agents/templates/REPORT.md`
   (máximo 60 líneas). Inclúyelo en el commit.
4. Si te bloqueas: documenta el bloqueo en el reporte, haz commit de lo útil y termina.

## Estilo de código
- C99 en engine/core y backends nativos; nada de asignación dinámica en el bucle de juego de PS1/GBA/GB.
- Python 3.11+ en tools/, con tipado y tests (pytest).
- Conversores deterministas: misma entrada → mismo hash de salida.
````

### D5. `.claude/settings.json`

> Permisos del proyecto. Con Git for Windows instalado, Claude Code usa Git Bash para su herramienta Bash y estas reglas aplican. (verificar) la sintaxis vigente de reglas con `/permissions`.

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git show:*)",
      "Bash(git branch:*)",
      "Bash(git worktree:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git merge:*)",
      "Bash(git tag:*)",
      "Bash(python tools/doctor.py:*)",
      "Bash(python tools/agents/dispatch.py:*)",
      "Bash(python tools/agents/sync_skills.py:*)",
      "Bash(python -m tools.ctl:*)",
      "Bash(python -m pytest:*)",
      "Bash(docker run:*)",
      "Bash(docker images:*)",
      "Bash(cmake:*)",
      "Bash(ffmpeg:*)",
      "Bash(orca:*)"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git reset --hard:*)",
      "Bash(git clean -fdx:*)",
      "Bash(rm -rf:*)",
      "Read(./.env)",
      "Edit(./upstream/**)"
    ]
  }
}
```

**Agent teams de Claude Code** (opcional): función experimental que se activa con `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` y usa *bastante más* cuota. En este plan **no se usa por defecto**: los trabajadores son los otros CLIs. Úsala solo si quieres que varias instancias de Claude debatan una decisión de arquitectura.

### D6. Subagentes de Claude Code (`.claude/agents/`)

`.claude/agents/port-reviewer.md`

````markdown
---
name: port-reviewer
description: Revisa la rama de un agente antes de fusionarla en integration. Úsalo SIEMPRE antes de cada merge. Verifica diff, archivos permitidos, build, escenarios ctl y reglas de AGENTS.md.
tools: Read, Grep, Glob, Bash
model: sonnet
---
Eres el revisor de integración de Snoot Ports. Recibes: ID de tarea y rama.

1. Lee `.agents/tasks/<T>.md` (archivos permitidos, DoD) y el reporte del agente.
2. `git diff integration...<rama> --stat` y luego el diff completo.
   - Rechaza si toca archivos no permitidos, `engine/pal/*.h`, `upstream/` o agents.toml.
3. Reproduce los pasos de verificación de la tarea. No confíes en la salida pegada.
4. Corre `python -m tools.ctl run --target pc --suite smoke` y, si la tarea afecta
   una consola, el mismo suite en esa consola.
5. Busca: memoria dinámica en bucles de PS1/GBA/GB, rutas absolutas de Windows,
   CRLF en scripts, secretos, assets sin licencia compatible.
6. Veredicto: APROBADO / CAMBIOS (lista numerada y concreta) / RECHAZADO (motivo).
Máximo 40 líneas.
````

`.claude/agents/renpy-analyst.md`

````markdown
---
name: renpy-analyst
description: Analiza scripts Ren'Py (.rpy), ATL, screens y Python del juego en modo solo lectura. Úsalo para responder preguntas sobre cómo se comporta el original o para auditar el IR.
tools: Read, Grep, Glob
model: sonnet
---
Analista de Ren'Py. Nunca editas archivos. Respondes con rutas y números de línea
exactos (`upstream/snootgame/game/<archivo>.rpy:<línea>`). Cuando describas ATL,
lista las propiedades (xpos, ypos, zoom, alpha, rotate...), tiempos e interpolación.
Señala cualquier construcción que el IR v1 no soporte.
````

`.claude/agents/ctl-runner.md`

````markdown
---
name: ctl-runner
description: Ejecuta el Console Test Lab para una plataforma y resume resultados. Úsalo para correr suites y diagnosticar diferencias de traza.
tools: Read, Grep, Glob, Bash
model: sonnet
---
Ejecuta `python -m tools.ctl run --target <x> --suite <s>`, lee el reporte en
build/ctl/<x>/report.md y resume: escenarios OK/fallidos, primer evento divergente
de cada fallo (esperado vs obtenido) y la hipótesis más probable. Máximo 30 líneas.
````

### D7. `opencode.json` (raíz del proyecto)

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "opencode-go/beam-free",
  "permission": {
    "edit": "allow",
    "bash": "allow",
    "webfetch": "deny"
  }
}
```

> Permisos amplios porque cada Beam trabaja aislado en su worktree. Si un Beam se sale de su carpeta, baja `bash` a `"ask"` y usa Orca para supervisarlo. (verificar) claves de permisos con la doc de OpenCode.

### D8. `tools/agents/agents.toml`

```toml
# Configuración de agentes para dispatch.py y sync_skills.py
# Solo Claude Code edita este archivo.

[settings]
base_branch = "integration"
worktree_root = "../snoot-wt"
default_timeout_min = 45
# Sin acentos ni caracteres & | < > ^ % " (los CLIs instalados por npm son .cmd en Windows)
prompt_template = "Eres el agente {agent} del proyecto Snoot Ports. Primero lee AGENTS.md. Luego lee tu tarea en .agents/inbox/{task}.md y ejecutala. Trabaja solo dentro de este directorio. Al terminar corre las verificaciones que pide la tarea, haz commit en tu rama actual y escribe tu reporte en .agents/reports/{task}.md usando la plantilla .agents/templates/REPORT.md. No hagas push, merge ni rebase. Si te bloqueas, describe el bloqueo en el reporte y termina."

[skills]
# Carpetas donde se copian las skills de ./skills (verificar cuál lee cada agente)
targets = [".claude/skills", ".agents/skills", ".opencode/skills"]

[agents.beam]
cmd = ["opencode", "run", "-m", "opencode-go/beam-free", "{prompt}"]
max_parallel = 3          # medir en Fase 3; subir a 5 si no hay 429
timeout_min = 40

[agents.codex]
cmd = ["codex", "exec", "--sandbox", "workspace-write", "-C", "{worktree}", "{prompt}"]
max_parallel = 1
timeout_min = 60

[agents.kilo]
# Tras verificar `kilo run --help` y `kilo models`, agrega por ejemplo: "-m", "<proveedor/modelo-mimo>"
cmd = ["kilo", "run", "--auto", "{prompt}"]
max_parallel = 1
timeout_min = 60

[agents.vibe]
cmd = ["vibe", "--prompt", "{prompt}", "--max-turns", "40", "--output", "json", "--trust"]
max_parallel = 1
timeout_min = 45

[agents.claude]
# Consume tu cuota de Claude: solo revisiones puntuales o desbloqueos
cmd = ["claude", "-p", "{prompt}", "--permission-mode", "acceptEdits"]
max_parallel = 1
timeout_min = 45

[agents.agy]
# agy -p pierde la salida o se cuelga sin TTY en Windows (issues #76 y #318 del repo antigravity-cli).
# Usa Antigravity interactivo dentro de una terminal de Orca.
cmd = ["agy", "-p", "{prompt}"]
enabled = false

# Sustituto si Beam no está disponible en tu región o termina la promoción:
# [agents.gomodel]
# cmd = ["opencode", "run", "-m", "opencode-go/<modelo>", "{prompt}"]   # ver `opencode models opencode-go`
# max_parallel = 2
```

### D9. `tools/agents/dispatch.py`

```python
#!/usr/bin/env python3
"""
dispatch.py - Despachador headless de agentes para Snoot Ports.

Crea un git worktree por (tarea, agente), copia la tarea a .agents/inbox/,
lanza el CLI del agente en modo no interactivo con timeout, guarda el log
y recoge el reporte en .agents/reports/ del repo principal.

Uso:
  python tools/agents/dispatch.py list-agents
  python tools/agents/dispatch.py run    --agent beam --task T-012
  python tools/agents/dispatch.py batch  --agent beam --tasks T-012 T-013 T-014 --parallel 3
  python tools/agents/dispatch.py status
  python tools/agents/dispatch.py remove --agent beam --task T-012 --yes

Requiere Python 3.11+ (tomllib) y git en el PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CFG_PATH = ROOT / "tools" / "agents" / "agents.toml"
AG = ROOT / ".agents"
CMD_UNSAFE = set('&|<>^%"')
RATE_LIMIT_HINTS = ("429", "rate limit", "rate_limit", "too many requests")


class DispatchError(Exception):
    pass


def load_cfg() -> dict:
    with CFG_PATH.open("rb") as f:
        return tomllib.load(f)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git(*args: str, cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=check, text=True,
        capture_output=True, encoding="utf-8", errors="replace",
    )


def worktree_path(cfg: dict, task: str, agent: str) -> Path:
    base = Path(cfg["settings"]["worktree_root"])
    if not base.is_absolute():
        base = (ROOT / base).resolve()
    return base / f"{task}-{agent}"


def ensure_worktree(cfg: dict, task: str, agent: str) -> tuple[Path, str]:
    wt = worktree_path(cfg, task, agent)
    branch = f"agent/{agent}/{task}"
    if wt.exists():
        return wt, branch
    wt.parent.mkdir(parents=True, exist_ok=True)
    base_branch = cfg["settings"].get("base_branch", "integration")
    has_branch = git("rev-parse", "--verify", "--quiet", branch, check=False).returncode == 0
    if has_branch:
        git("worktree", "add", str(wt), branch)
    else:
        git("worktree", "add", "-b", branch, str(wt), base_branch)
    return wt, branch


def resolve_exe(name: str) -> str:
    exe = shutil.which(name)
    if not exe:
        raise DispatchError(f"No encuentro '{name}' en el PATH. Ejecuta: python tools/doctor.py")
    return exe


def build_cmd(agent_cfg: dict, prompt: str, wt: Path) -> list[str]:
    cmd = [p.replace("{prompt}", prompt).replace("{worktree}", str(wt)) for p in agent_cfg["cmd"]]
    cmd[0] = resolve_exe(cmd[0])
    if os.name == "nt" and cmd[0].lower().endswith((".cmd", ".bat")):
        bad = CMD_UNSAFE.intersection(prompt)
        if bad:
            raise DispatchError(f"El prompt contiene caracteres peligrosos para .cmd: {sorted(bad)}")
    return cmd


def agent_cfg_or_fail(cfg: dict, agent: str) -> dict:
    agents = cfg.get("agents", {})
    if agent not in agents:
        raise DispatchError(f"Agente desconocido: {agent}. Opciones: {', '.join(agents)}")
    acfg = agents[agent]
    if not acfg.get("enabled", True):
        raise DispatchError(f"El agente '{agent}' está deshabilitado en agents.toml")
    return acfg


def run_one(cfg: dict, agent: str, task: str) -> dict:
    acfg = agent_cfg_or_fail(cfg, agent)
    task_file = AG / "tasks" / f"{task}.md"
    if not task_file.exists():
        raise DispatchError(f"No existe {task_file}")

    wt, branch = ensure_worktree(cfg, task, agent)
    inbox = wt / ".agents" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    shutil.copy2(task_file, inbox / f"{task}.md")
    (wt / ".agents" / "reports").mkdir(parents=True, exist_ok=True)

    prompt = cfg["settings"]["prompt_template"].format(task=task, agent=agent)
    cmd = build_cmd(acfg, prompt, wt)

    for d in ("logs", "status", "reports"):
        (AG / d).mkdir(parents=True, exist_ok=True)
    log_path = AG / "logs" / f"{task}-{agent}.log"
    timeout_min = int(acfg.get("timeout_min", cfg["settings"].get("default_timeout_min", 45)))
    env = os.environ.copy()
    env.update({k: str(v) for k, v in acfg.get("env", {}).items()})

    status: dict = {
        "task": task, "agent": agent, "branch": branch, "worktree": str(wt),
        "started": now(), "cmd": [Path(cmd[0]).name, *cmd[1:]],
    }
    print(f"[dispatch] -> {agent} {task}  ({wt})", flush=True)

    timed_out = False
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(f"# {status['started']} agent={agent} task={task}\n# cwd={wt}\n\n")
        log.flush()
        try:
            proc = subprocess.run(
                cmd, cwd=wt, env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, timeout=timeout_min * 60,
            )
            code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out, code = True, -1

    # La copia de la tarea ya no se necesita: así el worktree queda limpio
    (inbox / f"{task}.md").unlink(missing_ok=True)
    if inbox.exists() and not any(inbox.iterdir()):
        inbox.rmdir()

    report_src = wt / ".agents" / "reports" / f"{task}.md"
    report_found = report_src.exists()
    if report_found:
        shutil.copy2(report_src, AG / "reports" / f"{task}-{agent}.md")

    base_branch = cfg["settings"].get("base_branch", "integration")
    commits = git("rev-list", "--count", f"{base_branch}..{branch}", check=False).stdout.strip()
    dirty = bool(git("status", "--porcelain", cwd=wt, check=False).stdout.strip())
    log_text = log_path.read_text(encoding="utf-8", errors="replace").lower()

    status.update({
        "finished": now(),
        "exit_code": code,
        "timed_out": timed_out,
        "report_found": report_found,
        "commits_ahead": int(commits) if commits.isdigit() else None,
        "uncommitted_changes": dirty,
        "possible_rate_limit": any(h in log_text for h in RATE_LIMIT_HINTS),
        "log": str(log_path),
    })
    (AG / "status" / f"{task}-{agent}.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

    verdict = "OK" if (code == 0 and report_found and not timed_out) else "REVISAR"
    print(f"[dispatch] <- {agent} {task}: {verdict} exit={code} commits={status['commits_ahead']} "
          f"reporte={'si' if report_found else 'NO'}{' TIMEOUT' if timed_out else ''}", flush=True)
    return status


def cmd_batch(cfg: dict, agent: str, tasks: list[str], parallel: int) -> list[dict]:
    acfg = agent_cfg_or_fail(cfg, agent)
    workers = max(1, min(parallel, int(acfg.get("max_parallel", 1))))
    for t in tasks:  # crear worktrees en serie evita bloqueos de git
        ensure_worktree(cfg, t, agent)
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(run_one, cfg, agent, t): t for t in tasks}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except DispatchError as e:
                results.append({"task": futures[fut], "agent": agent, "error": str(e)})
                print(f"[dispatch] ERROR {futures[fut]}: {e}", flush=True)
    if any(r.get("possible_rate_limit") for r in results):
        print("[dispatch] Aviso: posibles limites de tasa. Baja --parallel o max_parallel.")
    return results


def cmd_status() -> None:
    files = sorted((AG / "status").glob("*.json")) if (AG / "status").exists() else []
    if not files:
        print("Sin ejecuciones registradas.")
        return
    print(f"{'TAREA':<10} {'AGENTE':<8} {'EXIT':>5} {'COMMITS':>7} {'REPORTE':>8} {'TIMEOUT':>8}  FIN")
    for f in files:
        s = json.loads(f.read_text(encoding="utf-8"))
        print(f"{s['task']:<10} {s['agent']:<8} {s.get('exit_code', ''):>5} "
              f"{str(s.get('commits_ahead', '')):>7} {('si' if s.get('report_found') else 'NO'):>8} "
              f"{('SI' if s.get('timed_out') else 'no'):>8}  {s.get('finished', '')}")


def cmd_remove(cfg: dict, agent: str, task: str, yes: bool, force: bool) -> None:
    wt = worktree_path(cfg, task, agent)
    if not wt.exists():
        print(f"No existe el worktree {wt}")
        return
    if not yes:
        raise DispatchError("Borrar un worktree requiere --yes (la rama se conserva).")
    args = ["worktree", "remove", str(wt)] + (["--force"] if force else [])
    git(*args)
    print(f"Worktree eliminado: {wt} (rama agent/{agent}/{task} conservada)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Despachador headless de agentes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list-agents")
    p_run = sub.add_parser("run")
    p_run.add_argument("--agent", required=True)
    p_run.add_argument("--task", required=True)
    p_batch = sub.add_parser("batch")
    p_batch.add_argument("--agent", required=True)
    p_batch.add_argument("--tasks", nargs="+", required=True)
    p_batch.add_argument("--parallel", type=int, default=3)
    sub.add_parser("status")
    p_rm = sub.add_parser("remove")
    p_rm.add_argument("--agent", required=True)
    p_rm.add_argument("--task", required=True)
    p_rm.add_argument("--yes", action="store_true")
    p_rm.add_argument("--force", action="store_true")
    args = ap.parse_args()

    try:
        cfg = load_cfg()
        if args.cmd == "list-agents":
            for name, a in cfg.get("agents", {}).items():
                state = "on " if a.get("enabled", True) else "off"
                print(f"{name:<8} [{state}] max_parallel={a.get('max_parallel', 1)}  {' '.join(a['cmd'][:3])} ...")
        elif args.cmd == "run":
            s = run_one(cfg, args.agent, args.task)
            return 0 if s.get("exit_code") == 0 and s.get("report_found") else 1
        elif args.cmd == "batch":
            res = cmd_batch(cfg, args.agent, args.tasks, args.parallel)
            return 0 if all(r.get("exit_code") == 0 and r.get("report_found") for r in res) else 1
        elif args.cmd == "status":
            cmd_status()
        elif args.cmd == "remove":
            cmd_remove(cfg, args.agent, args.task, args.yes, args.force)
    except (DispatchError, subprocess.CalledProcessError) as e:
        msg = e.stderr if isinstance(e, subprocess.CalledProcessError) and e.stderr else str(e)
        print(f"[dispatch] ERROR: {msg}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### D10. `tools/doctor.py`

```python
#!/usr/bin/env python3
"""
doctor.py - Verifica el entorno de Snoot Ports.
Uso:
  python tools/doctor.py           # existencia y versiones
  python tools/doctor.py --smoke   # ademas, un prompt minimo a cada CLI de IA (usa cuota)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

# (nombre, ejecutable, args, obligatorio)
CHECKS = [
    ("Git", "git", ["--version"], True),
    ("Python", "python", ["--version"], True),
    ("Node.js", "node", ["--version"], True),
    ("npm", "npm", ["--version"], True),
    ("uv", "uv", ["--version"], True),
    ("Docker", "docker", ["--version"], True),
    ("FFmpeg", "ffmpeg", ["-version"], True),
    ("CMake", "cmake", ["--version"], False),
    ("GitHub CLI", "gh", ["--version"], False),
    ("Claude Code", "claude", ["--version"], True),
    ("Codex", "codex", ["--version"], True),
    ("OpenCode", "opencode", ["--version"], True),
    ("Kilo CLI", "kilo", ["--version"], True),
    ("Mistral Vibe", "vibe", ["--version"], True),
    ("Antigravity CLI", "agy", ["--version"], False),
    ("Orca CLI", "orca", ["status", "--json"], False),
]

SMOKE = [
    ("Beam", ["opencode", "run", "-m", "opencode-go/beam-free", "Responde solo: OK"]),
    ("Codex", ["codex", "exec", "Responde solo: OK"]),
    ("Kilo", ["kilo", "run", "--auto", "Responde solo: OK"]),
    ("Vibe", ["vibe", "--prompt", "Responde solo: OK", "--max-turns", "1"]),
    ("Claude", ["claude", "-p", "Responde solo: OK"]),
]


def run(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    exe = shutil.which(cmd[0])
    if not exe:
        return 127, "no encontrado en PATH"
    try:
        p = subprocess.run([exe, *cmd[1:]], capture_output=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
        out = (p.stdout or b"") + (p.stderr or b"")
        text = out.decode("utf-8", errors="replace").replace("\x00", "").strip()
        return p.returncode, text
    except subprocess.TimeoutExpired:
        return 124, f"timeout tras {timeout}s"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    missing_required = []
    print("== Herramientas ==")
    for name, exe, vargs, required in CHECKS:
        code, out = run([exe, *vargs])
        ok = code == 0
        first = out.splitlines()[0][:70] if out else ""
        mark = "OK " if ok else ("FALTA" if required else "opc ")
        print(f"[{mark}] {name:<16} {first}")
        if not ok and required:
            missing_required.append(name)

    print("\n== Comprobaciones extra ==")
    code, _ = run(["docker", "info"], timeout=20)
    print(f"[{'OK ' if code == 0 else 'FALTA'}] Docker daemon en marcha")
    if code != 0:
        missing_required.append("Docker daemon")

    code, out = run(["git", "config", "--global", "core.longpaths"])
    print(f"[{'OK ' if out.strip() == 'true' else 'aviso'}] git core.longpaths = {out.strip() or '(sin definir)'}")

    if sys.version_info < (3, 11):
        print("[FALTA] Python >= 3.11 (tomllib)")
        missing_required.append("Python 3.11+")

    code, out = run(["opencode", "models", "opencode-go"], timeout=60)
    has_beam = "beam-free" in out
    print(f"[{'OK ' if has_beam else 'aviso'}] Beam listado en opencode-go: {'si' if has_beam else 'no'}")

    if args.smoke:
        print("\n== Smoke test de agentes (usa un poco de cuota) ==")
        for name, cmd in SMOKE:
            code, out = run(cmd, timeout=180)
            ok = code == 0 and "ok" in out.lower()
            print(f"[{'OK ' if ok else 'FALLA'}] {name:<8} exit={code} {out.splitlines()[-1][:60] if out else ''}")

    if missing_required:
        print(f"\nFaltan obligatorios: {', '.join(missing_required)}")
        return 1
    print("\nEntorno listo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### D11. `tools/agents/sync_skills.py`

```python
#!/usr/bin/env python3
"""Copia cada skills/<nombre>/ (con SKILL.md) a las carpetas de skills de cada agente."""
from __future__ import annotations

import shutil
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    cfg = tomllib.loads((ROOT / "tools" / "agents" / "agents.toml").read_text(encoding="utf-8"))
    targets = cfg.get("skills", {}).get("targets", [".claude/skills"])
    src_root = ROOT / "skills"
    skills = sorted(p for p in src_root.iterdir() if (p / "SKILL.md").exists())
    for target in targets:
        dst_root = ROOT / target
        dst_root.mkdir(parents=True, exist_ok=True)
        for skill in skills:
            dst = dst_root / skill.name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(skill, dst)
            print(f"[sync] {skill.name} -> {target}")


if __name__ == "__main__":
    main()
```

### D12. Plantillas de tarea y reporte

`.agents/templates/TASK.md`

```markdown
# T-xxx — <título imperativo>

- **Estado:** todo | assigned | review | done | blocked
- **Agente:** beam | codex | kilo | vibe | agy | claude
- **Fase:** <n>
- **Depende de:** T-yyy, T-zzz

## Objetivo
<una o dos frases, resultado observable>

## Contexto mínimo
- Lee: <rutas exactas>
- Contrato a respetar: <engine/pal/xxx.h, docs/ir/SnootIR.md §n>

## Archivos permitidos
- <rutas o globs>

## Archivos prohibidos
- engine/pal/**, upstream/**, tools/agents/agents.toml, <otros>

## Pasos sugeridos
1. ...

## Verificación (comandos ejecutables)
```
<comando 1>
<comando 2>
```

## Definición de terminado
- [ ] ...
```

`.agents/templates/REPORT.md`

```markdown
# Reporte T-xxx — <agente>

**Resultado:** COMPLETO | PARCIAL | BLOQUEADO

## Qué hice (≤ 8 líneas)

## Archivos cambiados
- ruta — motivo

## Verificación (salida REAL, recortada a lo relevante)
```
$ comando
salida
```

## Decisiones y supuestos

## Propuestas de cambio a contratos (si aplica)

## Bloqueos / siguiente paso sugerido
```

### D13. Las 5 skills propias (`skills/<nombre>/SKILL.md`)

`skills/renpy-source-analyzer/SKILL.md`

```markdown
---
name: renpy-source-analyzer
description: Analiza scripts Ren'Py (.rpy) de Snoot Game u otro juego para inventariar labels, menús, variables, ATL, screens, audio e imágenes, y detectar construcciones no soportadas por SnootIR. Úsala antes de tocar el exportador IR o al investigar cómo se comporta una escena original.
---
# Analizador de fuentes Ren'Py

## Entradas
- Fuente: `upstream/snootgame/game/**/*.rpy` (solo lectura)
- IR actual: `build/ir/snoot.ir.json` (si existe)

## Procedimiento
1. Inventario rápido: `rg -n "^\s*label\s" upstream/snootgame/game` y análogos para
   `menu:`, `jump`, `call`, `show`, `scene`, `hide`, `play`, `stop`, `queue`, `with`, `transform`, `screen`, `python`, `$`.
2. Para cada `python`/`$`: clasificar en (a) asignación simple, (b) expresión soportada,
   (c) lógica que requiere port manual. Listar archivo:línea.
3. Para cada `transform`/ATL: propiedades, duraciones, interpolaciones (linear/ease/...), repeat/parallel/block.
4. Para screens personalizados: qué hacen y si afectan el flujo narrativo.
5. Salida: `docs/analysis/<tema>.md` con tablas y referencias archivo:línea.

## Reglas
- Nunca modificar `upstream/`.
- Citar siempre archivo:línea.
- Marcar explícitamente lo que el IR v1 no cubre.
```

`skills/renpy-animation-reconstructor/SKILL.md`

```markdown
---
name: renpy-animation-reconstructor
description: Convierte transforms ATL, transiciones y animaciones de sprites de Ren'Py en keyframes del IR (tiempo, posición, zoom, alpha, rotación, easing) y valida la reconstrucción contra la traza de referencia. Úsala al implementar o depurar animaciones en cualquier backend.
---
# Reconstructor de animaciones ATL

## Modelo
Cada ATL se convierte en una lista de pistas por propiedad:
`{prop, keyframes:[{t_ms, value, ease}], loop}`. Bloques `parallel` → pistas simultáneas;
`repeat` → `loop`; `pause` → avance de tiempo; `function` → NO soportado (reportar).

## Procedimiento
1. Leer el ATL con la skill renpy-source-analyzer (archivo:línea).
2. Traducir a pistas; normalizar posiciones a coordenadas virtuales 1920x1080.
3. Escalar a la resolución del backend en tiempo de build, nunca en runtime de PS1/GBA/GB.
4. Validar: comparar eventos SHOW/MOVE de la traza del port contra la referencia
   (tolerancia por defecto: ±2 frames, ±1 % de posición, ±0.02 alpha).
5. Easings: implementar en `engine/core/ease.c` con tablas precalculadas en plataformas sin FPU.

## Errores comunes
- Olvidar `xanchor/yanchor` (por defecto 0.0 para posiciones absolutas, 0.5 en `center`).
- Interpretar `zoom` y `xzoom/yzoom` como acumulativos.
- Tiempos ATL en segundos (float) → convertir a ms enteros.
```

`skills/console-port-builder/SKILL.md`

```markdown
---
name: console-port-builder
description: Compila el motor y los datos de Snoot Ports para una consola concreta usando la imagen Docker y el perfil documentados en docs/platforms/<plataforma>.md. Úsala para cualquier build de consola, diagnóstico de errores de compilación o empaquetado.
---
# Constructor de ports

## Reglas
- Toolchains SIEMPRE en Docker (o WSL2 si la plataforma lo indica). Nunca instalar SDKs en Windows.
- El comando oficial de cada plataforma vive en `docs/platforms/<plataforma>.md`. Si no existe, créalo.
- Builds reproducibles: fijar la etiqueta/digest de la imagen Docker en el doc de plataforma.

## Patrón
```
docker run --rm -v "${PWD}:/src" -w /src <imagen> make -C ports/<plataforma> [TESTMODE=1]
```

## Perfiles
- `release`: sin trazas, optimizado.
- `testmode`: `-DSNOOT_TESTMODE=1`, guion de entradas embebido, salida TRACE por TTY/log.

## Diagnóstico
1. Leer el primer error, no el último.
2. Si es de enlazado: revisar orden de libs y símbolos de la PAL no implementados.
3. Si es memoria (sección desbordada): revisar presupuesto en docs/platforms y el reporte del assetpipe.
```

`skills/console-emulator-testing/SKILL.md`

```markdown
---
name: console-emulator-testing
description: Ejecuta builds testmode en emuladores mediante el Console Test Lab (python -m tools.ctl), recoge trazas y capturas, y compara con la referencia Ren'Py. Úsala para validar cualquier cambio que afecte a una plataforma o para diagnosticar divergencias.
---
# Pruebas en emulador

## Comandos
- `python -m tools.ctl run --target <plataforma> --suite smoke`
- `python -m tools.ctl run --target <plataforma> --scenario <id>`
- `python -m tools.ctl compare --target <plataforma> --scenario <id>`
- `python -m tools.ctl report --target <plataforma>`

## Interpretación
- El reporte marca el PRIMER evento divergente. Diagnostica ese, no los siguientes.
- Divergencia en LABEL/JUMP → lógica (reproducir en PC primero).
- Divergencia en SHOW/MOVE → ATL o escalado.
- Divergencia en AUDIO → pipeline de audio o canal.
- Sin traza → crash temprano: revisar log del emulador y el arranque del backend.

## Reglas
- Nunca dar una plataforma por buena solo porque compila o arranca.
- Adjuntar al reporte la línea de veredicto de ctl y la ruta del reporte completo.
```

`skills/console-asset-optimizer/SKILL.md`

```markdown
---
name: console-asset-optimizer
description: Convierte imágenes, audio, video y fuentes de Snoot Game a los formatos y presupuestos de memoria de cada consola mediante tools/assetpipe, de forma determinista. Úsala al añadir una plataforma, al cambiar calidad o al investigar desbordes de memoria.
---
# Optimizador de assets por consola

## Principios
- Entrada única: inventario `build/ir/assets.json`. Salida: `build/assets/<plataforma>/` + `manifest.json` con hashes.
- Deterministas: fijar semillas de dithering/cuantización; mismo input → mismo hash.
- Presupuestos por plataforma en docs/platforms/<plataforma>.md (RAM, VRAM, tamaño de medio).

## Recetas base
- Imágenes: redimensionar a la resolución destino (Lanczos), cuantizar a la profundidad del hardware
  (4/8/16 bpp), paleta por imagen o compartida por escena, dithering ordenado para GB/GBA.
- Audio música: streaming en el formato nativo (XA en PS1, ADPCM, etc.); SFX cortos en memoria.
- Video: decidir por plataforma (STR en PS1, decodificador nativo donde exista, o secuencia
  de cuadros a baja tasa; en GB/GBA reemplazar por escenas fijas).
- Fuentes: atlas de bitmap pre-renderizado por tamaño y resolución.

## Verificación
- `python -m pytest tools/assetpipe -q`
- Reporte de presupuesto: ninguna escena excede RAM/VRAM de la plataforma.
```

---

## 7. Parte E — Referencia técnica del port

### E1. Snoot Game: fuente oficial y licencias

- Repositorio oficial (Gitea de Cavemanon): `https://git.snootgame.xyz/Cavemanon/SnootGame` (verificar disponibilidad; si no responde, usa la descarga oficial del juego, que incluye los `.rpy`/`.rpyc`, y el README con la licencia).
- **Licencias:** código bajo **AGPL-3.0**; assets bajo **CC-BY-SA 4.0** (las distribuciones empaquetadas lo declaran así y el README exige que cualquier asset añadido sea compatible con CC-BY-SA 4.0).
- Ramas: el README pide contribuciones a la rama `patch`; `master` se mantiene estable. Para tu port usa la **última versión estable** como base y anota el commit en `docs/upstream.md`.
- Consecuencia práctica: tu motor, conversores y ports que incorporen código del juego deben publicarse bajo AGPL-3.0 con su código fuente; los assets convertidos siguen siendo CC-BY-SA 4.0 con atribución. Ver Parte H.

### E2. SnootIR v1 (formato intermedio)

**Archivo:** `build/ir/snoot.ir.json` (legible) → compilado a binario por plataforma `snoot.sirb`.

```text
Programa  = { version, labels{nombre→pc}, code[instr], strings[lang][id], assets{id→meta}, transforms[id] }

Instrucciones v1 (op args):
  LABEL      name                       ; marcador (también genera TRACE LABEL)
  SCENE      bg_asset  transition?      ; limpia capa master
  SHOW       tag attrs  at=transform_id? zorder? transition?
  HIDE       tag  transition?
  WITH       transition_id
  SAY        who_id  text_id  voice_asset?
  MENU       [ {text_id, cond_expr?, target_pc} ... ]
  JUMP       target_pc
  CALL       target_pc
  RETURN
  IF         cond_expr  else_pc
  SET        var_id  expr
  PLAY       channel  asset_id  loop  fadein_ms
  QUEUE      channel  asset_id
  STOP       channel  fadeout_ms
  PAUSE      ms | until_input
  MOVIE      asset_id  skippable
  NATIVE     hook_id                    ; lógica portada a mano (minijuegos, screens especiales)
  END

Expresiones (expr): bytecode de pila restringido
  CONST int|bool|str_id · LOAD var · STORE var · ADD SUB MUL DIV MOD · NEG NOT
  EQ NE LT LE GT GE · AND OR (cortocircuito)
  Cualquier otra construcción Python → error de exportación con archivo:línea.

Transforms: pistas por propiedad (ver skill renpy-animation-reconstructor).
Coordenadas virtuales: 1920x1080; el escalado ocurre en build por plataforma.
```

Reglas del IR: enteros de 32 bits; strings fuera del código (tabla por idioma); IDs de assets lógicos (el mismo ID en todas las plataformas, distinto archivo físico).

### E3. Exportador IR (corre *dentro* de Ren'Py)

Por qué dentro del runtime: el propio Ren'Py parsea el juego exactamente como lo ejecuta, incluido ATL y statements de usuario (`play`, `stop`, `queue` son *user statements*). Es la misma estrategia que usan los descompiladores serios cuando corren dentro del runtime.

Diseño:
1. Copia de trabajo: `build/renpy-ref/` = copia de `upstream/snootgame` + `tools/renpy_export/export_ir.rpy`.
2. `export_ir.rpy` en `init 999 python:` registra una acción que, al arrancar con una variable de entorno `SNOOT_EXPORT=1`, recorre `renpy.game.script.namemap` (o la estructura equivalente de tu versión) y serializa cada nodo de `renpy.ast` (Label, Say, Show, Scene, Hide, With, Menu, If, Jump, Call, Return, Python, UserStatement, Transform/ATL) a JSON con `filename` y `linenumber`.
3. Un compilador en Python (`tools/renpy_export/compile_ir.py`) transforma ese JSON en SnootIR v1, convierte expresiones con el módulo `ast` de Python y rechaza lo no soportado con un reporte.
4. Herramientas de apoyo: `renpy <proyecto> lint` (verificar) y la opción de volcado JSON del lanzador (`--json-dump`, verificar) para cruzar labels y screens.

Resultado esperado: `build/ir/snoot.ir.json`, `build/ir/unsupported.md`, `build/ir/assets.json`.

### E4. Traza de referencia del Ren'Py original

**Hook de traza** (boceto; Claude debe validarlo contra la versión exacta del SDK) — `tools/renpy_export/trace_hook.rpy`, copiado solo a `build/renpy-ref/game/`:

```python
init -999 python:
    import json, os

    _snoot_trace_path = os.path.join(config.basedir, "snoot_trace.jsonl")
    _snoot_seq = [0]

    def _snoot_emit(ev, **kw):
        _snoot_seq[0] += 1
        kw["seq"] = _snoot_seq[0]
        kw["ev"] = ev
        try:
            kw["loc"] = "%s:%d" % renpy.get_filename_line()
        except Exception:
            pass
        with open(_snoot_trace_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(kw, ensure_ascii=False) + "\n")

    def _snoot_on_label(name, abnormal):
        _snoot_emit("LABEL", name=name)

    def _snoot_on_interact():
        try:
            showing = sorted(renpy.get_showing_tags("master"))
        except Exception:
            showing = []
        try:
            music = renpy.music.get_playing("music")
        except Exception:
            music = None
        _snoot_emit("INTERACT", showing=showing, music=music)

    config.label_callbacks.append(_snoot_on_label)
    config.start_interact_callbacks.append(_snoot_on_interact)
```

- `loc` (archivo:línea) permite mapear cada interacción al nodo del IR sin depender del texto.
- Posiciones de sprites: añadir `renpy.get_image_bounds(tag)` por cada tag visible (verificar firma en tu versión).
- **Recorrer rutas de forma determinista:** en la copia de trabajo, modificar el screen `choice` para que elija automáticamente según una lista en la variable de entorno `SNOOT_CHOICES` (p. ej. `2,1,3`), y activar avance automático. Alternativa: el sistema de *testcases* de Ren'Py (`testcase`, comando `test` del lanzador; verificar sintaxis en la doc de tu versión).
- Salida: `tests/reference/traces/<ruta>.jsonl` + capturas (`renpy.screenshot`) en interacciones marcadas.

### E5. Core portable y PAL (Platform Abstraction Layer)

Contratos (los escribe Claude; ejemplos de forma, no definitivos):

```c
/* engine/pal/pal_video.h */
typedef struct { int16_t x, y; uint16_t w, h; } pal_rect;
int  pal_video_init(void);
int  pal_tex_load(uint16_t asset_id);            /* devuelve handle o -1 */
void pal_tex_free(int handle);
void pal_draw(int handle, const pal_rect *dst, uint8_t alpha, int16_t zoom_q8, int16_t rot_q8);
void pal_frame_begin(void);
void pal_frame_end(void);                        /* incluye vsync */

/* engine/pal/pal_audio.h */
int  pal_music_play(uint16_t asset_id, int loop, int fadein_ms);
void pal_music_stop(int fadeout_ms);
int  pal_sfx_play(uint16_t asset_id);

/* engine/pal/pal_input.h */
enum { PAL_BTN_A=1, PAL_BTN_B=2, PAL_BTN_UP=4, PAL_BTN_DOWN=8, PAL_BTN_START=16, PAL_BTN_SKIP=32 };
uint32_t pal_input_poll(void);                   /* en TESTMODE lee del guion embebido */

/* engine/pal/pal_storage.h */
int pal_data_open(const char *logical_name);     /* CD, ROM, NitroFS, SD... */
int pal_data_read(int fd, void *dst, uint32_t off, uint32_t len);
int pal_save_write(int slot, const void *buf, uint32_t len);
int pal_save_read(int slot, void *buf, uint32_t len);

/* engine/pal/pal_debug.h */
void pal_trace(const char *line);                /* TTY/log del emulador; no-op en release */
uint32_t pal_ticks_ms(void);
```

El core (`engine/core/`) contiene: VM del IR, estado y variables, rollback opcional, sistema de texto (ajuste de línea precalculado en build), animaciones (pistas ATL), guardado lógico y el emisor de trazas.

### E6. Backends y "tiers" de fidelidad

| Tier | Plataformas | Backend | Fidelidad objetivo |
|---|---|---|---|
| **A — SDL** | PC (Win/Linux), PS Vita, PSP, PS2, 3DS, Wii, Xbox clásica, Switch | `engine/backends/sdl` + ajustes por plataforma | Casi completa: todas las escenas, música, ATL; video según plataforma |
| **B — Nativo** | PS1 (existente) | `engine/backends/ps1` (PSn00bSDK) | Completa con assets reducidos (ya demostrado) |
| **C — Demake** | GBA, DS | nativo (Butano / BlocksDS) | Texto completo, arte reducido y comprimido, audio simplificado, sin video |
| **D — Demake extremo** | GB / GBC | nativo (GBDK-2020) | Texto completo, arte en tiles con dithering, música en tracker, sin video |

Notas:
- SDL tiene ports para PSP, PS2, Vita, 3DS, Switch, Wii y Xbox (vía nxdk); confirmar en cada plataforma si conviene SDL2 o SDL3 según el port más maduro (verificar).
- La PAL hace que "SDL o nativo" sea un detalle del backend: el core no cambia.

### E7. Tabla de plataformas (hardware, toolchain, emulador)

| Plataforma | Resolución | RAM / VRAM | SDK | Imagen Docker / instalación | Emulador de prueba | Salida de traza |
|---|---|---|---|---|---|---|
| PC | 1920×1080 (escalable) | — | SDL + CMake | nativo | — | stdout |
| **PS1** | 320×240 | 2 MB / 1 MB (+512 KB SPU) | PSn00bSDK | toolchain mipsel (script `mips.ps1` de PCSX-Redux en Windows, o paquetes mipsel en WSL) | PCSX-Redux (`-stdout -run -loadexe <exe>`, `-iso <img>`, `-dofile <lua>`), DuckStation (`-fastboot`, ruta absoluta) | TTY por `-stdout` |
| **PS2** | 640×448 | 32 MB / 4 MB GS | ps2sdk + gsKit | `ps2dev/ps2dev:latest` | PCSX2 (flags de batch/ELF: verificar `--help`) | log de consola EE |
| **PSP** | 480×272 | 32/64 MB / 2 MB | pspsdk | `pspdev/pspdev:latest` | PPSSPP / PPSSPPHeadless | stdout en headless |
| **PS Vita** | 960×544 | 512 MB / 128 MB | VitaSDK | `vitasdk/vitasdk:latest` | Vita3K | log de Vita3K |
| **3DS** | 400×240 + 320×240 | 128/256 MB | libctru + citro2d (devkitARM) | `devkitpro/devkitarm` | Azahar | log de debug |
| **Wii** | 640×480 | 24+64 MB | libogc (devkitPPC) | `devkitpro/devkitppc` | Dolphin (`-b -e <dol>`) | OSReport en log |
| **Switch** | 1280×720 | 4 GB | libnx (devkitA64) | `devkitpro/devkita64` | validar en hardware propio | nxlink / log |
| **Xbox clásica** | 640×480 | 64 MB unificada | nxdk | WSL2 (verificar imagen) | xemu | DbgPrint (verificar) |
| **GBA** | 240×160 | 32 KB IWRAM + 256 KB EWRAM / 96 KB; ROM ≤ 32 MB | Butano (devkitARM) | `devkitpro/devkitarm` | mGBA (Lua, GDB) | registros de debug de mGBA |
| **DS** | 2× 256×192 | 4 MB / 656 KB | BlocksDS | imagen de BlocksDS (verificar nombre) | melonDS | consola de debug |
| **GB / GBC** | 160×144 | 8/32 KB WRAM; ROM ≤ 8 MB (MBC5) | GBDK-2020 | release Windows de GBDK | SameBoy / BizHawk | registro de debug del emulador |

Investigación (sin compromiso): PS3 (PSL1GHT, RPCS3), PS4 (OpenOrbis, shadPS4), Xbox 360 (libxenon, Xenia).

### E8. Pipeline de assets por plataforma (`tools/assetpipe/`)

| Plataforma | Fondos/CG | Sprites | Música | SFX/voz | Video |
|---|---|---|---|---|---|
| PC | PNG/WebP original | igual | OGG/Opus original | igual | original |
| PS1 | 16 bpp o 8 bpp+CLUT, 320×240, streaming desde CD | 4/8 bpp + CLUT | XA-ADPCM (psxavenc) | SPU-ADPCM/VAG (psxavenc) | STR/MDEC (psxavenc) |
| PS2 | 8/32 bpp | 8 bpp | ADPCM o PCM en streaming | ADPCM SPU2 | decidir (IPU/MPEG o cuadros) |
| PSP | 8/16 bpp, 480×272 | 8 bpp | MP3/AT3 o PCM | PCM | H.264 nativo (verificar) |
| Vita/3DS/Wii/Xbox/Switch | según VRAM; texturas potencia de 2 si aplica | — | Ogg/Opus vía SDL_mixer o equivalente | WAV/ADPCM | decidir por plataforma |
| GBA | modo 4 (8 bpp, 240×160) + LZ77 | 4 bpp | PCM 8-bit baja tasa o remakes tracker | PCM corto | se reemplaza por escenas fijas |
| DS | 8/16 bpp por pantalla, comprimido | 4/8 bpp | IMA-ADPCM en streaming | ADPCM | opcional, cuadros a baja tasa |
| GB/GBC | ≤ 360 tiles únicos por pantalla, dithering ordenado, 4 tonos / paletas GBC | tiles 2 bpp | hUGETracker | — | se reemplaza por escenas fijas |

Reglas: conversión determinista, `manifest.json` con hash por asset, reporte de presupuesto por escena (pico de RAM/VRAM), y "modo vista previa" que genera un HTML con todas las imágenes convertidas para revisión humana rápida.

### E9. Console Test Lab (`tools/ctl/`)

**Principio:** CLI primero (todos los agentes saben usar una CLI). Un servidor MCP es opcional después.

```
python -m tools.ctl build   --target <plataforma> [--testmode]
python -m tools.ctl run     --target <plataforma> --suite smoke|full | --scenario <id>
python -m tools.ctl compare --target <plataforma> --scenario <id>
python -m tools.ctl report  --target <plataforma>          # build/ctl/<plataforma>/report.md (+ .html)
python -m tools.ctl golden  --target <plataforma> --scenario <id>   # actualizar goldens (requiere aprobación de Claude)
```

**Configuración** `testlab.toml` (rutas a emuladores portables en `tools/emulators/`):

```toml
[pc]
runner = "build/pc/snoot"
[ps1]
emulator = "tools/emulators/pcsx-redux/pcsx-redux.exe"
args = ["-stdout", "-run", "-loadexe", "{exe}"]
[psp]
emulator = "tools/emulators/ppsspp/PPSSPPHeadless.exe"
args = ["{exe}"]
```

**Escenario** `tests/scenarios/route-a-smoke.yaml`:

```yaml
id: route-a-smoke
reference: tests/reference/traces/route-a.jsonl
inputs:            # se compila dentro del build testmode
  - advance: 12
  - choose: 2
  - advance: 30
expect:
  - {ev: LABEL, name: start}
  - {ev: LABEL, name: route_a_intro}
compare:
  events: [LABEL, SAY, SHOW, HIDE, SCENE, PLAY, STOP, MENU, CHOICE]
  tolerance: {frames: 2, pos_pct: 1.0, alpha: 0.02}
limits:
  max_seconds: 300
```

**Protocolo TRACE** (una línea por evento, idéntico en todas las plataformas):

```
T|<seq>|<frame>|<EV>|k=v;k=v
T|17|1042|SAY|who=nm;text=3121;loc=script.rpy:880
T|18|1043|SHOW|tag=anon;attrs=happy;x=960;y=1080;a=255
T|19|1100|CHOICE|i=2
T|20|1101|LABEL|name=route_a_intro
T|21|1101|FBHASH|crc=9a3f12c0
```

- El build **testmode** lee entradas del guion embebido en lugar del mando, imprime TRACE por `pal_trace()` y, en puntos marcados, el CRC del framebuffer (`FBHASH`) para regresión por plataforma.
- `ctl compare` alinea la secuencia de eventos con la referencia Ren'Py (ignorando tiempos dentro de tolerancia) y reporta el **primer evento divergente**.
- Capturas del emulador (cuando el adapter lo permita) para revisión visual y SSIM contra la referencia en escenas seleccionadas.

**Interfaz de adapter** (forma sugerida):

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class RunResult:
    exit_code: int
    trace_lines: list[str]
    log_path: Path
    screenshots: list[Path]
    timed_out: bool


class EmulatorAdapter(Protocol):
    name: str

    def build(self, testmode: bool) -> Path: ...
    def run(self, artifact: Path, timeout_s: int) -> RunResult: ...
```

### E10. Orca: orquestación desde Claude Code

1. Instalar skills (una vez):
   ```powershell
   npx skills add https://github.com/stablyai/orca --skill orca-cli --global
   npx skills add https://github.com/stablyai/orca --skill orchestration --global
   # o con el CLI de Orca:
   orca skills install --skill orca-cli --skill orchestration --agent claude-code,codex
   ```
2. **Siempre** antes de mutar estado: `orca skills get orchestration --full` (guía acorde a tu versión; comandos antiguos se retiran).
3. Comprobar la app: `orca status --json`.
4. Ejemplos de comandos de orquestación (fuente: la propia skill; verificar):
   ```text
   orca orchestration task-create --spec "<texto>" --deps '["<id>"]' --json
   orca orchestration task-list --ready --json
   orca orchestration dispatch --task <id> --to <handle> --inject --json
   orca orchestration inbox --json
   orca orchestration gate-list --json
   orca orchestration gate-resolve --id <gate> --resolution "<texto>" --json
   orca orchestration run-stop --json
   ```
   `--inject` envía al trabajador un preámbulo que le enseña a reportar `worker_done`.
5. **Cuándo usar qué:**
   - Orca → agentes interactivos (Antigravity siempre), tareas largas que quieras ver en vivo, revisión de diffs, seguimiento desde el móvil.
   - `dispatch.py` → lotes headless (Beam ×N, Codex/Kilo/Vibe en tareas acotadas).

### E11. Skills y plugins de terceros (instalación por agente)

| Paquete | Qué aporta | Claude Code | Codex | OpenCode / Kilo | Antigravity |
|---|---|---|---|---|---|
| **Superpowers** (obra) | TDD, systematic-debugging, worktrees, dispatching-parallel-agents, verification-before-completion, code review | `/plugin install superpowers@claude-plugins-official` | `/plugins` → buscar *superpowers* | seguir `.opencode/INSTALL.md` del repo | `agy plugin install https://github.com/obra/superpowers` |
| **mattpocock/skills** (selección) | `codebase-design`, `improve-codebase-architecture`, `diagnosing-bugs`, `handoff`, `to-issues` | `/plugin marketplace add mattpocock/skills` → `/plugin install mattpocock-skills@mattpocock` | `npx skills@latest add mattpocock/skills` | ídem | ídem |
| **Orca** | `orca-cli`, `orchestration` | ver E10 | ver E10 | — | — |
| **anthropics/skills** | Referencia oficial para escribir skills | solo como ejemplo | — | — | — |

Recomendación para evitar conflictos de reglas duplicadas:
- **Claude Code:** Superpowers completo + de mattpocock solo `codebase-design` e `improve-codebase-architecture`.
- **Workers:** solo las 5 skills propias + `AGENTS.md` (más instrucciones = más confusión en modelos medianos como Beam).
- No instalar dos paquetes que definan flujos de planificación distintos en el mismo agente.

---

## 8. Parte F — Backlog inicial de tareas

> Claude Code convierte cada fila en `.agents/tasks/T-xxx.md` con la plantilla D12 y completa rutas exactas tras la auditoría de la Fase 4.

| ID | Fase | Agente | Tarea | Depende |
|---|---|---|---|---|
| T-001 | 3 | beam | Smoke: `docs/smoke/beam-1.md` (versión, modelo, resumen de AGENTS.md) | — |
| T-002 | 3 | beam | Smoke: `docs/smoke/beam-2.md` | — |
| T-003 | 3 | beam | Smoke: `docs/smoke/beam-3.md` | — |
| T-004 | 3 | codex | Smoke: `docs/smoke/codex.md` | — |
| T-005 | 3 | kilo | Smoke: `docs/smoke/kilo.md` (confirmar id del modelo MiMo) | — |
| T-006 | 3 | vibe | Smoke: `docs/smoke/vibe.md` | — |
| T-007 | 3 | agy (Orca) | Smoke: `docs/smoke/antigravity.md` | — |
| T-010 | 4 | beam | Inventario del repo existente: módulos, build, formatos → `docs/analysis/inventory.md` | G3 |
| T-011 | 4 | codex | Build reproducible de PS1 con un comando + hash | T-010 |
| T-012 | 4 | beam | Capturar goldens de 5 escenas en PCSX-Redux | T-011 |
| T-013 | 4 | vibe | `docs/CONTEXT.md` (vocabulario) y `docs/platforms/ps1.md` | T-010 |
| T-020 | 5 | beam | Detectar versión Ren'Py del upstream y preparar `build/renpy-ref` | G4 |
| T-021 | 5 | beam | `export_ir.rpy`: volcado del AST a JSON con archivo:línea | T-020 |
| T-022 | 5 | codex | `compile_ir.py`: JSON → SnootIR v1 + compilador de expresiones + `unsupported.md` | T-021 |
| T-023 | 5 | beam | `trace_hook.rpy` + autoselección de opciones por `SNOOT_CHOICES` | T-020 |
| T-024 | 5 | beam | Generar trazas de referencia de todas las rutas/finales | T-023 |
| T-025 | 5 | beam | Inventario de assets con uso por escena → `assets.json` | T-021 |
| T-026 | 5 | claude | Redactar `docs/ir/SnootIR.md` v1 (contrato) | T-022 |
| T-030 | 6 | agy (Orca) | Esqueleto `tools/ctl` (CLI, config, reporte MD/HTML) | G5 |
| T-031 | 6 | codex | Modo testmode + `pal_trace` en el port PS1 | T-030 |
| T-032 | 6 | beam | Adapter PS1/PCSX-Redux + parser TRACE | T-030 |
| T-033 | 6 | beam | `ctl compare`: alineación de eventos y primer divergente | T-024, T-032 |
| T-040 | 7 | claude | Escribir `engine/pal/*.h` v1 | G6 |
| T-041 | 7 | codex | Extraer core portable desde PS1 a `engine/core` | T-040 |
| T-042 | 7 | codex | Backend PS1 sobre la PAL, cero regresiones | T-041 |
| T-050 | 8 | codex | Backend SDL para PC | G7 |
| T-051 | 8 | beam | Assetpipe perfil PC | T-025 |
| T-052 | 8 | beam | Escenarios para todas las rutas | T-033 |
| T-060 | 9 | kilo | Port PSP (SDL + ajustes) + `docs/platforms/psp.md` | G8 |
| T-061 | 9 | codex | Port PS2 (SDL + ajustes) + `docs/platforms/ps2.md` | G8 |
| T-062 | 9 | beam | Assetpipe PSP | T-051 |
| T-063 | 9 | beam | Assetpipe PS2 | T-051 |
| T-064 | 9 | agy (Orca) | Adapters ctl PPSSPP y PCSX2 | T-030 |
| T-070 | 10 | kilo | Port Vita | G9 |
| T-071 | 10 | codex | Port 3DS | G9 |
| T-072 | 10 | beam | Assetpipes Vita/3DS | T-051 |
| T-080 | 11 | claude + humano | Definir fidelidad aceptable GBA/DS/GB | G9 |
| T-081 | 11 | codex | Backend GBA (Butano) | T-080 |
| T-082 | 11 | beam | Assetpipe GBA (modo 4 + LZ77 + audio) | T-080 |
| T-090 | 12 | claude | Diseño de `rp2c analyze` | G9 |
| T-091 | 12 | beam | Integrar descompilador propio / unrpyc / rpycdec | T-090 |
| T-099 | — | vibe | Auditoría de licencias y `CREDITS.md` (repetir antes de cada release) | G5 |

---

## 9. Parte G — Riesgos, límites y solución de problemas

### G1. Riesgos principales

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Beam Free termina o no está disponible en tu región | Pierdes 5 trabajadores gratis | Sustituto en `agents.toml` con otro modelo de OpenCode Go; nada más cambia |
| Beam retiene prompts 30 días (no entrena con ellos) | Privacidad | No pongas claves ni datos personales en tareas; el código es AGPL de todos modos |
| Límites de concurrencia no publicados | 429 / timeouts | Empezar con 3, medir, `possible_rate_limit` en status |
| Cuota de Claude agotada | Orquestación se detiene | Reportes cortos, subagentes con Sonnet, trabajo masivo a Beam/Codex/Kilo |
| Agentes editan lo mismo | Conflictos de merge | Archivos permitidos por tarea, contratos solo de Claude, worktrees |
| "Compila = terminado" | Ports rotos | Gates con ctl obligatorios |
| Python/lógica custom del juego | Escenas no portables | `NATIVE hook_id` + port manual, listado en `unsupported.md` |
| Memoria en PS1/GBA/GB | Crashes | Presupuestos en build, reporte por escena |
| Upstream no disponible | Sin fuente | Usar la distribución oficial descargable (incluye licencia y scripts) |

### G2. Problemas típicos

| Síntoma | Causa probable | Solución |
|---|---|---|
| `claude` no se reconoce tras instalar | PATH sin refrescar | Cerrar y abrir terminal |
| `agy -p` no imprime nada o se cuelga | Bug sin TTY en Windows | Usar Antigravity dentro de terminal de Orca |
| Build Docker falla con `\r: command not found` | CRLF | `.gitattributes` con `eol=lf`, `git add --renormalize .` |
| `git worktree add` falla por ruta larga | Límite de rutas | `git config --global core.longpaths true` y worktrees en ruta corta (`D:\wt`) |
| Docker muy lento con el repo en `D:\` | Montajes NTFS→Linux | Aceptable al principio; si molesta, mover builds pesados a un clon dentro de WSL |
| Vibe pide confiar en la carpeta | Sistema de trust | `--trust` en modo programático (ya en agents.toml) |
| Kilo usa un modelo equivocado | Falta `-m` | Ver `kilo models` y fijar `-m` en agents.toml |
| `dispatch.py` aborta por "caracteres peligrosos" | Prompt con `& | < > ^ % "` | Mantener el template sin esos caracteres |
| Un agente no escribe reporte | Se quedó sin turnos o se desvió | Revisar log; dividir la tarea; escalar |

### G3. Qué NO hacer

- No dejar 10 agentes "ocupados" si solo hay 4 tareas independientes.
- No dejar que un agente "mejore" la arquitectura sin tarea explícita.
- No convertir assets a mano: todo por `assetpipe` para que sea reproducible.
- No mover el port PS1 antes de G4.

---

## 10. Parte H — Checklist de publicación y licencias

Antes de publicar cualquier build:

- [ ] El código del port (motor, backends, herramientas que se distribuyan) está publicado bajo **AGPL-3.0** con su código fuente accesible (repositorio público o enlace junto al build).
- [ ] Los assets convertidos se distribuyen bajo **CC-BY-SA 4.0** con atribución a Cavemanon y a los autores indicados en el upstream.
- [ ] `CREDITS.md` incluido en el build (pantalla de créditos o archivo) y en el repo.
- [ ] Cualquier asset nuevo (fuentes, música de demakes) tiene licencia compatible con CC-BY-SA 4.0.
- [ ] Licencias de SDKs y librerías respetadas (p. ej., avisos de SDL, PSn00bSDK, Butano, etc.).
- [ ] No se incluyen BIOS, firmware ni claves de consolas.
- [ ] Queda claro que es un port no oficial del juego de Cavemanon.
- [ ] `T-099` (auditoría con Vibe) en verde.

---

## 11. Fuentes

Agentes y orquestación
- Orca (repo, instalador Windows, agentes soportados): https://github.com/stablyai/orca
- Orca skills (orca-cli, orchestration): https://www.onorca.dev/docs/cli/skills
- Skill de orquestación de Orca (comandos): https://skills.sh/stablyai/orca/orchestration
- Claude Code — instalación: https://code.claude.com/docs/en/setup
- Claude Code — agent teams: https://code.claude.com/docs/en/agent-teams
- OpenCode CLI (`run`, `-m`, `models`, `serve`/`--attach`): https://opencode.ai/docs/cli/
- Beam Free en OpenCode (id `beam-free`, tiempo y regiones limitadas, retención 30 días): https://www.orcarouter.ai/es/blog/beam-1-0-free-opencode-1m-context
- Codex modo no interactivo (`codex exec`, `--sandbox workspace-write`): https://developers.openai.com/de-DE/docs/non-interactive-mode
- Kilo Code CLI (`kilo run --auto`, fork de OpenCode): https://github.com/Kilo-Org/kilocode/
- Mistral Vibe (instalación, modo programático): https://github.com/MistralAI/mistral-vibe · https://docs.mistral.ai/vibe/code/cli/work-with-cli
- Antigravity CLI — problemas de `-p` sin TTY: https://github.com/google-antigravity/antigravity-cli/issues/76 · https://github.com/google-antigravity/antigravity-cli/issues/318

Skills
- Superpowers (instalación por agente): https://github.com/obra/superpowers · guía: https://www.developersdigest.tech/blog/claude-code-superpowers-plugin-guide
- Skills for Real Engineers (mattpocock): https://github.com/mattpocock/skills

Snoot Game y Ren'Py
- Licencia AGPL-3 + CC-BY-SA-4.0 (paquete de distribución): https://gpo.zugaina.org/AJAX/Ebuild/56102818/View
- Repositorio oficial referenciado (git.snootgame.xyz): https://archives-cdn-origin.gentoo.org/gentoo-commits/1669670075.832f08ebb66611d3f06ce61b1f6be92053032aad.sprice623@gentoo/t
- README del juego (contribuciones AGPL, assets compatibles CC-BY-SA 4.0): https://gooberparty.duckdns.org/Boots%20Archive/Games/Native/Indies/Snoot%20Game/SnootGame-Patch8_NewYears-win/README.md
- rpycdec 0.2.0 (Ren'Py 7/8, probado hasta 8.5.3): https://pypi.org/project/rpycdec/0.2.0/
- unrpyc: https://github.com/CensoredUsername/unrpyc

Toolchains y emuladores
- ps2dev (imagen `ps2dev/ps2dev:latest`): https://github.com/ps2dev/ps2dev
- pspdev (imagen `pspdev/pspdev:latest`): https://github.com/pspdev/pspdev
- devkitPro (imágenes Docker oficiales): https://devkitpro.org/wiki/About
- Ejemplo de CI con SDL para vita/3DS/PS2/PSP en Docker: https://github.com/madebr/setup-sdl-test
- PCSX-Redux (flags `-stdout -run -loadexe`, `-iso`, `-dofile`): https://github.com/grumpycoders/pcsx-redux · https://docs.rs/psx
