# Plan Maestro: Ecosistema de Portabilidad de Ren'Py a Consolas (asistido por IA)

> **Documento:** `E:\Dev\renpy-console-project\PLAN.md`  
> **Versión:** 0.1 (borrador inicial)  
> **Fecha:** 2026-10-25  
> **Autor:** Pako Tako + agentes IA (Claude, Codex, OpenCode, Antigravity)  
> **Idioma:** español para documentación; código y nombres en inglés.  
> **Alcance:** llevar Snoot Game y otros juegos Ren'Py a 20 variantes de hardware
> (PS1, PS2, PS3, PS4, PS5, PSP, PSP Go, PS Vita, GB, GBC, GBA, NDS, 3DS, Wii,
> Switch 1, Xbox Classic, Xbox 360, Xbox One, Xbox Series S/X), con un núcleo compartido,
> un conversor Ren'Py y un laboratorio de pruebas automatizado.

---

## 0. Resumen ejecutivo

Ya existen, funcionando, cuatro piezas:

1. **`E:\Dev\snoot-ps1`** — port completo de Snoot Game a PS1 (v1.0 publicada),
   con motor en C (PSn00bSDK), compilador Ren'Py → bytecode VNB, simulador, pipeline
   de imágenes/audio y pruebas automatizadas en PCSX-Redux.
2. **`E:\Dev\vn-engine-ps1`** — motor compartido que nació de `snoot-ps1` y hoy
   sirve a `wani-ps1` (port de *I Wani Hug that Gator!*). Ya incluye Fases A–D
   (separación general/Snoot, capacidades Wani, bytecode v2 + compilador común).
3. **`E:\Dev\renpy-port-kit`** — kit genérico para descompilar, analizar, simular y
   preparar recursos de cualquier juego Ren'Py (RPA/RPYC propios, AST, guion JSON,
   recursos renderizados, comparación con el original).
4. **`E:\Dev\wani-ps1`** — port en curso de *I Wani Hug that Gator!* a PS1, con
   bloques temporales, cámara horneada, audio de historia, videos STR, etc.

El siguiente salto no es “hacer otro port aislado”, sino convertir esos avances en un
**ecosistema reutilizable**: un juego Ren'Py compatible se importa una sola vez y se
generan versiones para varias consolas desde el mismo núcleo y los mismos datos de
escena, con ayuda de agentes IA que programan, compilan, prueban y diagnostican.

**Decisión clave (no negociable):** no se construyen 20 motores independientes.
Se construye **un núcleo compartido en C/C++** + **backends por plataforma** +
**un conversor Ren'Py → formato intermedio** + **un laboratorio de pruebas (Console
Test Lab)** que automatiza compiladores y emuladores. Las consolas más limitadas
(GB, GBC, GBA, DS) reciben versiones reducidas del motor.

**Primera meta concreta y medible:** Snoot Game ejecutándose en **PS1, PS2 y PSP**
desde el **mismo código de lógica** y los **mismos datos de escena**. Si se logra,
la arquitectura queda demostrada.

**Regla de oro:** no modificar `snoot-ps1`, `wani-ps1`, `vn-engine-ps1` ni
`renpy-port-kit` desde este proyecto sin pedir permiso. Todo lo nuevo vive en
`renpy-console-project/` y se propone a los repos hermanos mediante pull requests
o copias explícitas.

---

## 1. Inventario real de lo que ya existe

### 1.1 Proyectos en `E:\Dev`

| Proyecto | Rol | Estado | Licencia |
|---|---|---|---|
| `snoot-ps1` | Port de Snoot Game a PS1 (v1.0) | Publicado; referencia estable | AGPL-3.0 (juego) + MIT (motor) |
| `vn-engine-ps1` | Motor compartido de VN para PS1 | Fases A–D en curso; sirve a wani | MIT |
| `wani-ps1` | Port de *I Wani Hug that Gator!* a PS1 | En desarrollo activo (bloques temporales, cámara, audio, video STR) | AGPL-3.0 + CC-BY-SA-4.0 |
| `renpy-port-kit` | Kit genérico Ren'Py → datos neutros | Fases 0–5; 400+ tests | (definir) |
| `snoot-ps2` | Port nativo PS2 (preparación) | Solo docs/plan/status | — |
| `hello-ps1` | Ejemplo mínimo PS1 | Referencia de build | — |
| `NeoCab` | (otro proyecto) | No relacionado | — |

### 1.2 Proyectos en `E:\snoot`

| Carpeta | Rol |
|---|---|
| `snootgame` | Código fuente original de Snoot Game (Ren'Py) |
| `I Wani Hug that Gator!` | Código fuente original de Wani (Ren'Py 8.3.7) |
| `SnootGame-Patch14-MunichAgreement-win` | Build publicada de Snoot (Windows) |
| `renpy-8.3.7-sdk` | SDK de Ren'Py (incluye *The Question* y tutorial) |
| `renpy-sdks` / `renpy-sdk-dl` | SDKs adicionales para pruebas de round-trip |
| `duckstation-windows-x64-release` | Emulador PS1 (jugar) |
| `pcsx-redux-nightly-...` | Emulador PS1 (depurar, Lua) |
| `ps1 bios` | BIOS reales (SCPH1001, 5500, 5501, 5502) |
| `audit_out`, `snoot_audit`, `audit_run.log` | Salidas de auditoría visual |
| `export_story.py`, `render_pdf_preview.ps1` | Utilidades sueltas |

### 1.3 Piezas reutilizables que ya existen

- **Motor en C (`vn-engine-ps1/core/`):** VM (`vm.c`), escena (`scene.c`), imágenes (`img.c`),
  audio (`audio.c`), CD (`cd.c`), recursos (`res.c`), texto (`text.c`), guardado (`save.c`),
  entrada (`input.c`), LZ4 (`lz4.c`), video (`video.c`, `video_clip.c`, `str.c`), capítulos
  (`chapter.c`), límites (`vn_limits.h`), opcodes (`opcodes.h`).
- **Bytecode VNB1/VNB2:** especificación en `docs/bytecode.md`; compilador en `vncompiler/`;
  simulador de flujo.
- **Compilador Ren'Py → VNB (adaptadores en `wani-ps1/tools/script_compiler/`):** parser de
  Ren'Py, cámaras, bloques temporales, personajes en movimiento, audio, etc.
- **Kit (`renpy-port-kit/renpykit/`):** RPA (`rpa/`), RPYC (`rpyc/`), AST (`ast/`), análisis
  (`analyze/`), recursos (`resources/`), guion JSON (`script/`), simulación (`simulate/`),
  comparación (`compare/`), guardados (`save/`).
- **Pruebas automatizadas:** `tools/engine/emutest.py`, `playtest.py` (snoot-ps1),
  escenarios PCSX-Redux con Lua, capturas píxel a píxel.
- **Referencias externas clonadas en `renpy-port-kit/referencias/`:** `unrpyc`, `unrparc`,
  `warpa`, `Wani-Translation-Kit` (solo estudio, no se copia código).

### 1.4 Lo que NO existe todavía (y este plan crea)

- Un repositorio unificado `renpy-console-project` con estructura multiplataforma.
- Un formato intermedio de escenas independiente de consola (hoy es VNB + guion JSON).
- Backends para PS2, PSP, Vita, GBA, DS, 3DS, Wii, Switch, Xbox, etc.
- Un Console Test Lab (automatización universal de emuladores).
- Un MCP propio para que los agentes IA controlen todo.
- Perfiles de recursos por plataforma (hoy solo perfil PS1).

---

## 2. Visión y principios de diseño

### 2.1 Visión

> Tomar un proyecto compatible de Ren'Py, importarlo una sola vez y generar versiones
> para distintas consolas sin reescribir el videojuego.

### 2.2 Principios (no negociables)

1. **Un núcleo, muchos backends.** No 20 motores. El núcleo (VM, escena, texto, guardado,
   lógica) es compartido; cada plataforma implementa gráficos, audio, entrada, almacenamiento
   y empaquetado.
2. **Datos, no código, por juego.** El conversor produce datos (escenas, recursos, bytecode)
   que el motor consume. Lo propio de cada juego vive en datos o en módulos aparte.
3. **Versiones reducidas para consolas limitadas.** GB/GBC/GBA/DS no corren el motor completo;
   reciben escenas transformadas (fondos simplificados, audio reducido, sin video).
4. **Detección, no adivinanza.** El conversor detecta construcciones incompatibles (Python
   dinámico, pantallas personalizadas, minijuegos) y las reporta con archivo y línea. La IA
   no debe “adivinar” su funcionamiento; se implementan equivalencias verificables.
5. **Pruebas reproducibles.** Toda capacidad nueva entra con escenario automatizado. Sin prueba,
   no se integra.
6. **No romper lo que funciona.** `snoot-ps1` v1.0 y `wani-ps1` en curso no se tocan desde
   aquí sin permiso. Los cambios al motor compartido (`vn-engine-ps1`) se proponen y se prueban
   con todos los juegos que lo usan.
7. **Formato de bytecode versionado.** Cambiar el bytecode implica actualizar especificación,
   compilador, simulador y motor en el mismo cambio, y subir versión (VNB1 → VNB2 → …).
8. **Licencias.** Ren'Py es MIT, pero los juegos tienen sus propias licencias (AGPL-3.0,
   CC-BY-SA-4.0, etc.). Los ports son obras derivadas y deben respetarlas. El motor es MIT.
9. **Windows first.** Archivos con `encoding="utf-8"`, rutas con `pathlib.Path`, scripts en
   Python, comandos en PowerShell, herramientas externas con `subprocess.run([...], check=True)`.
10. **C99 para el motor.** Compatible con PSn00bSDK; basarse en ejemplos oficiales y psx-spx;
    no inventar registros ni funciones.

### 2.3 Lo que NO se intenta (límites)

- No se portan juegos con Python complejo o minijuegos arbitrarios de forma automática; se
  reportan y se resuelven a mano.
- PS5 no tiene ruta completa de desarrollo homebrew convencional; se deja para fase de
  investigación o acceso oficial.
- Xbox 360 y PS5 se tratan como proyectos especializados (entorno de ejecución incierto).
- No se distribuyen imágenes completas de juegos con licencia restrictiva sin revisar derechos.

---

## 3. Arquitectura objetivo

### 3.1 Vista de alto nivel

```
Juego original Ren'Py
  .rpy · .rpyc · .rpa · imágenes · audio · video
        │
        ▼
┌──────────────────────────────┐
│  Ren'Py Converter (Python)   │  ← renpy-port-kit evolucionado
│  Extracción · Decompilación  │
│  Análisis · Normalización    │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Formato intermedio común    │  ← VNSCENE / scene bundle
│  Escenas · Diálogos · Menús  │
│  Variables · Recursos · Audio │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Universal VN Engine (C/C++) │  ← núcleo compartido
│  VM · Escena · Texto · Audio │
│  Guardado · Lógica · Cámara  │
└──────┬───────┬───────┬───────┘
       │       │       │
       ▼       ▼       ▼
  ┌─────┐ ┌─────┐ ┌─────┐
  │ PS1 │ │ PS2 │ │ PSP │  ... backends por plataforma
  └─────┘ └─────┘ └─────┘
       │
       ▼
  Console Test Lab (Python)
  build · launch · input · capture · compare · report
       │
       ▼
  Agentes IA (Claude/Codex/OpenCode/Antigravity)
  vía MCP propio
```

### 3.2 Separación en tres capas

| Capa | Responsabilidad | Tecnología | Dónde vive |
|---|---|---|---|
| **Conversor Ren'Py** | Interpreta el juego original, recupera estructura, produce datos independientes de consola | Python (renpy-port-kit) | `tools/renpy-importer/` |
| **Motor (núcleo)** | Ejecuta diálogos, decisiones, imágenes, música, animaciones, lógica | C/C++ (C99) | `engine/core/`, `engine/script-vm/`, `engine/graphics/`, `engine/audio/`, `engine/save-system/` |
| **Backends** | Adaptan gráficos, audio, controles, almacenamiento, empaquetado a cada consola | C/C++ por plataforma | `platforms/<consola>/` |

### 3.3 Regla de dependencias

- El núcleo **no conoce** ninguna consola.
- Los backends **no contienen** lógica de juego.
- El conversor **no genera código C** directamente; genera datos + bytecode que el motor consume.
- Los recursos se preparan con **perfiles por plataforma** (resolución, paleta, formato de audio).

### 3.4 Versiones reducidas del motor

Para consolas con memoria muy limitada (GB, GBC, GBA, DS, GBC), el motor completo no cabe.
Se definen **niveles**:

| Nivel | Consolas | Capacidades |
|---|---|---|
| **Full** | PS2, PS3, PS4, PS5, Wii, Switch, Xbox One/Series, PC | Todo: video, audio XA, 16+ sprites, cámara, transiciones |
| **Standard** | PS1, PSP, Vita, DS, 3DS, Xbox Classic | Sprites limitados (8–16), audio VAG/XA, imágenes 8-bit, sin video o video reducido |
| **Lite** | GBA | Paletas 4-bit/8-bit, tiles, sprites hardware, audio PCM/PSG, escenas simplificadas |
| **Minimal** | GB, GBC | 4 tonos, fondos de tiles, texto, sin audio complejo, escenas rediseñadas a mano |

El nivel se declara en `platforms/<consola>/profile.cmake` y el conversor genera recursos
apropiados según el perfil.

---

## 4. Contratos (interfaces) que definen el sistema

Antes de escribir código multiplataforma, se congelan cuatro contratos. Cambiar uno implica
actualizar todos los consumidores.

### 4.1 Contrato 1 — Formato intermedio de escenas (`VNSCENE`)

Hoy existe `guion.json` (del kit) y VNB (bytecode). El formato intermedio común debe:

- Ser **independiente de consola**.
- Representar: escenas, diálogos, menús, variables, saltos, llamadas, returns, condiciones,
  expresiones, audio (música/ambiente/efecto), imágenes (fondo/sprites/CG), animaciones (ATL),
  transiciones, cámara, texto animado, guardado, carga.
- Ser **versionado** (`format_version`).
- Ser **validable** (schema JSON + validador en Python).
- Permitir **generar VNB** (bytecode) para el motor, o consumirse directamente por backends
  que no usen VNB (PC, herramientas).

Ejemplo mínimo (ya propuesto en el análisis previo):

```json
{
  "game": "visual_novel",
  "format_version": 1,
  "entry": "start",
  "scenes": [
    {
      "id": "start",
      "operations": [
        { "op": "background", "asset": "school" },
        { "op": "show", "asset": "character_neutral", "at": "center" },
        { "op": "dialogue", "speaker": "character", "text": "Hola, ¿cómo estás?" },
        { "op": "choice", "options": [
            { "text": "Bien", "target": "answer_good" },
            { "text": "Mal", "target": "answer_bad" }
        ]}
      ]
    }
  ]
}
```

**Tarea:** formalizar este formato en `docs/formats/vnscene.md` con todos los ops necesarios
(listados en `docs/bytecode.md` v2 del motor). Reusar los ops existentes de VNB.

### 4.2 Contrato 2 — Interfaz del núcleo (core API)

El núcleo expone funciones C que los backends llaman. Ejemplo:

```c
/* engine/core/vn_core.h */
typedef struct VnContext VnContext;
VnContext *vn_init(const VnPlatformOps *ops, const VnConfig *cfg);
int  vn_load_scene(VnContext *ctx, const char *scene_id);
int  vn_step(VnContext *ctx);          /* avanza un frame/línea */
void vn_shutdown(VnContext *ctx);

/* Hooks que el backend implementa */
typedef struct VnPlatformOps {
    /* gráficos */
    void (*clear)(void);
    void (*draw_sprite)(int id, int x, int y, int w, int h, const void *tex);
    void (*present)(void);
    /* audio */
    void (*play_music)(int track_id, int loop);
    void (*play_sfx)(int sfx_id);
    /* entrada */
    int  (*poll_input)(void);
    /* almacenamiento */
    int  (*save)(const void *data, size_t size, int slot);
    int  (*load)(void *data, size_t size, int slot);
    /* debug/log */
    void (*log)(const char *msg);
} VnPlatformOps;
```

**Tarea:** extraer esta interfaz de `vn-engine-ps1` (hoy implícita en `core/` + `app/`)
y documentarla en `docs/core-api.md`.

### 4.3 Contrato 3 — Interfaz de plataforma (backend API)

Cada backend implementa `VnPlatformOps` + funciones de empaquetado:

- `platform_init()`, `platform_shutdown()`
- `platform_load_asset(id)` (carga desde CD/ROM/flash)
- `platform_get_time_ms()`
- `platform_sleep_ms(ms)`

Y expone un **manifest** de capacidades:

```c
typedef struct VnPlatformCaps {
    int screen_w, screen_h;
    int max_sprites;
    int vram_bytes;
    int ram_bytes;
    int audio_channels;
    int has_video;       /* 1 si soporta STR/video */
    int has_touch;       /* 1 si tiene táctil */
    int color_depth;     /* 4, 8, 16, 32 */
} VnPlatformCaps;
```

**Tarea:** crear `platforms/<consola>/caps.h` y `platforms/<consola>/backend.c` para cada
plataforma.

### 4.4 Contrato 4 — API de pruebas (escenarios)

Un archivo YAML/JSON por escenario, ejecutable en cualquier plataforma:

```yaml
test: snoot_intro
target: ps2

steps:
  - action: launch
  - action: wait_scene
    scene: start
  - action: screenshot
    name: intro.png
  - action: press
    button: confirm
  - action: wait_dialogue
    id: "000002"
  - action: assert
    condition: dialogue_visible
  - action: screenshot
    name: dialogue.png
```

El Console Test Lab traduce esto a acciones del emulador (Lua/CLI/PyAutoGUI).

---

## 5. Matriz de plataformas, SDKs y emuladores

### 5.1 PlayStation

| Consola | SDK / toolchain | Emulador de pruebas | Dificultad | Estado | Nivel motor |
|---|---|---|---|---|---|
| PS1 | PSn00bSDK (MSYS2) | PCSX-Redux / BizHawk / DuckStation | Ya logrado | ✅ v1.0 | Standard |
| PS2 | PS2SDK (ps2dev) | PCSX2 | Media | 🟡 docs | Standard |
| PS3 | PSL1GHT | RPCS3 | Alta | 🔴 pendiente | Full |
| PS4 | OpenOrbis | shadPS4 / hardware | Alta | 🔴 pendiente | Full |
| PS5 | PS5SDK experimental | Hardware compatible | Muy alta | 🔴 investigación | Full |
| PSP | PSPSDK | PPSSPP | Media | 🔴 pendiente | Standard |
| PSP Go | PSPSDK (compartido) | PPSSPP + hardware | Media | 🔴 pendiente | Standard |
| PS Vita | VitaSDK | Vita3K | Media | 🔴 pendiente | Standard |

Notas:
- PS2SDK, PSL1GHT, PSPSDK, VitaSDK son entornos comunitarios abiertos.
- PS5: el SDK experimental no genera aplicaciones completas; requiere acceso oficial o
  dejar para fase de investigación.
- PSP Go comparte el desarrollo de PSP; no necesita port independiente.

### 5.2 Nintendo

| Consola | SDK / toolchain | Emulador de pruebas | Dificultad | Estado | Nivel motor |
|---|---|---|---|---|---|
| Game Boy | GBDK-2020 | BizHawk / Mesen 2 | Muy alta | 🔴 pendiente | Minimal |
| Game Boy Color | GBDK-2020 | BizHawk / Mesen 2 | Alta | 🔴 pendiente | Minimal |
| Game Boy Advance | Butano / devkitARM | mGBA | Media-alta | 🔴 pendiente | Lite |
| Nintendo DS | BlocksDS / libnds | melonDS / DeSmuME | Media-alta | 🔴 pendiente | Standard |
| Nintendo 3DS | devkitARM + libctru + citro2d | Azahar | Media | 🔴 pendiente | Standard |
| Wii | devkitPPC + libogc | Dolphin | Media | 🔴 pendiente | Full |
| Switch 1 | devkitA64 + libnx | Hardware / emuladores compatibles | Media-alta | 🔴 pendiente | Full |

Notas:
- devkitPro cubre GBA, DS, 3DS, Wii, Switch.
- GBDK-2020 es especializado para GB/GBC.
- GB/GBC requerirán motor Minimal + escenas transformadas (fondos simplificados, audio reducido).

### 5.3 Xbox

| Consola | SDK / toolchain | Emulador / pruebas | Dificultad | Estado | Nivel motor |
|---|---|---|---|---|---|
| Xbox Classic | NXDK (SDL2) | xemu | Media | 🔴 pendiente | Standard |
| Xbox 360 | LibXenon | Hardware / Xenia (según formato) | Muy alta | 🔴 pendiente | Full |
| Xbox One | UWP + Visual Studio / GDK | Developer Mode | Media-alta | 🔴 pendiente | Full |
| Xbox Series S | UWP / GDK | Developer Mode | Media-alta | 🔴 pendiente | Full |
| Xbox Series X | UWP / GDK | Developer Mode | Media-alta | 🔴 pendiente | Full |

Notas:
- NXDK incorpora SDL2 → reduce trabajo en Xbox Classic.
- LibXenon es bare-metal; no es sustituto directo de XEX. Validar cadena de ejecución.
- Xbox One/Series: UWP nuevos no se aceptan en Store; distribución comercial sigue otra ruta.

### 5.4 Automatización de pruebas por plataforma

| Plataforma | Emulador | Mejor estrategia inicial |
|---|---|---|
| PS1 | PCSX-Redux / BizHawk | Lua, debugger, capturas |
| PS2 | PCSX2 | CLI, logs, controlador externo |
| PS3 | RPCS3 | Arranque automatizado, logs, capturas |
| PS4 | shadPS4 | CLI, diagnóstico, hardware |
| PS5 | Sin emulador general | Hardware + pruebas del núcleo en PC |
| PSP / PSP Go | PPSSPP | CLI, debugger, entradas automatizadas |
| PS Vita | Vita3K | CLI, logs, automatización externa |
| GB / GBC | BizHawk / Mesen 2 | Lua, estados, capturas |
| GBA | mGBA | Lua nativo |
| DS | DeSmuME / BizHawk | Lua |
| 3DS | Azahar | Control externo, logs, capturas |
| Wii | Dolphin | CLI, playback de entradas, debugger |
| Switch | Emulador compatible / hardware | Automatización externa, logs |
| Xbox Classic | xemu | Control externo, logs |
| Xbox 360 | Hardware / Xenia | Validación específica, debugger |
| Xbox One / Series | Consola en modo desarrollo | Despliegue y depuración con VS |

**Principio:** no obligar a todas las consolas a usar Lua. Construir un programa central
(Console Test Lab) que use Lua cuando exista y otros mecanismos cuando no.

---

## 6. Conversor Ren'Py → datos neutros (evolución del kit)

### 6.1 Estado actual del kit

El kit ya hace: extracción RPA, descompilación RPYC, AST propio, análisis, guion JSON,
recursos renderizados, simulación de rutas, comparación con el original. Fases 0–5.

### 6.2 Lo que debe agregar para ser “conversor multiplataforma”

1. **Ren'Py Compatibility Analyzer** (prioridad alta):
   - Detección de versión y características de Ren'Py usadas.
   - Inventario de recursos (imágenes, fuentes, música, voces, videos, tamaños).
   - Análisis de scripts: labels, jumps, calls, menús, variables, condiciones.
   - Detección de Python dinámico, pantallas personalizadas, funciones no implementadas.
   - Generación de perfiles de compresión por consola.
   - Validación: comparar comportamiento recuperado contra el juego original.

2. **Formato intermedio común (VNSCENE)** — ver Contrato 4.1.

3. **Generador de bytecode VNB** desde el formato intermedio (hoy el compilador VNB
   lee Ren'Py directamente en wani-ps1; debe migrar a leer VNSCENE).

4. **Estimador de recursos por plataforma**: avisar cuando una escena exceda memoria,
   texturas o características no soportadas.

5. **Reporte de compatibilidad** por juego y por consola.

### 6.3 Herramientas de referencia (no se copia código)

| Herramienta | Uso |
|---|---|
| `unrpyc` | Estudiar decompilación de .rpyc |
| `rpatool` / `rpa-toolkit` | Estudiar extracción de .rpa y AST |
| Ren'Py source | Entender cómo interpreta instrucciones |
| Ghidra | Analizar componentes nativos cuando sea necesario |

El kit ya tiene estas referencias clonadas en `referencias/` y las usa solo para comparar.

### 6.4 Funciones a agregar al kit (con prioridad)

| Función | Prioridad | Descripción |
|---|---|---|
| `analyze_renpy_project` | Alta | Inspeccionar proyecto y detectar incompatibilidades |
| `convert_renpy_project` | Alta | Generar datos del motor (VNSCENE + recursos) |
| `generate_compatibility_report` | Alta | Informe por juego/consola |
| `estimate_resources` | Media | Estimar memoria/disco por escena |
| `validate_against_original` | Media | Comparar comportamiento recuperado vs original |

---

## 7. Console Test Lab (automatización universal)

### 7.1 Qué es

Un programa en Python que coordina compiladores, emuladores, entradas, capturas, logs y
verificaciones desde una sola interfaz (CLI + MCP). Es la pieza que permite a los agentes
IA programar → compilar → probar → diagnosticar → corregir sin intervención manual.

### 7.2 Arquitectura

```
Agente IA
   │
   ▼
Console Test Lab (Python)
   │
   ├── Build adapter     (SDKs, cmake, mkpsxiso, etc.)
   ├── Launch adapter    (emulador CLI/Lua/PyAutoGUI)
   ├── Input adapter     (botones, teclado)
   ├── Capture adapter   (screenshots, video)
   ├── Log adapter       (logs del motor [ENGINE] ...)
   └── Compare adapter   (golden traces, imágenes)
```

### 7.3 Operaciones del Test Lab (y futuras operaciones MCP)

| Operación | Función |
|---|---|
| `build_console_target` | Compilar para una consola |
| `launch_emulator` | Ejecutar el port |
| `run_test_scenario` | Reproducir una prueba |
| `capture_frame` | Capturar pantalla del emulador |
| `read_debug_log` | Recuperar logs |
| `compare_game_states` | Comparar trazas de dos plataformas |
| `generate_compatibility_report` | Crear informe de resultados |

### 7.4 Modo diagnóstico del motor

El motor debe emitir logs estructurados:

```
[ENGINE] scene=start
[ENGINE] dialogue=000001
[ENGINE] asset=school_background
[ENGINE] choice=1
[ENGINE] jump=chapter_01
[ENGINE] frame_ms=16.7
[ENGINE] status=OK
```

Esto permite a la IA saber qué pasó sin depender solo de imágenes.

### 7.5 Herramientas Python a usar

- `subprocess` — controlar procesos (compiladores, emuladores)
- `pytest` — pruebas
- `Pillow` — procesamiento de imágenes
- `OpenCV` — comparación de capturas
- `PyAutoGUI` — cuando un emulador no ofrece interfaz mejor
- `GitHub Actions` — tareas repetitivas

### 7.6 Ejemplo real: PS2 automatizado

```powershell
# Ejemplo con la ruta de tu instalación de PCSX2
$pcsx2 = "C:\Emuladores\PCSX2\pcsx2-qt.exe"
$game  = "D:\Ports\SnootGame\build\ps2\snoot.elf"

& $pcsx2 -batch -nogui -elf $game
```

El Test Lab necesita un adaptador de entradas y otro para recibir registros o comprobar
el estado del juego.

---

## 8. Pipeline de recursos (imágenes, audio, video)

### 8.1 Herramientas

| Herramienta | Uso |
|---|---|
| FFmpeg / FFprobe | Convertir videos y audio, analizar duración/resolución/bitrate |
| ImageMagick | Escalado, cuantización, transformación de imágenes |
| pngquant | Reducir paletas PNG |
| OpenCV | Comparación de capturas, análisis de imágenes |
| Pillow | Procesamiento y generación de recursos desde Python |

### 8.2 Perfiles por plataforma

| Plataforma | Estrategia de recursos |
|---|---|
| PS1 | Texturas adaptadas a VRAM, paletas, video específico (STR/XA) |
| PS2 | Mayor resolución, mejores capacidades de decodificación |
| PSP | Recursos para pantalla 480×272 y memoria disponible |
| GBA | Paletas limitadas, tiles, sprites, recursos convertidos |
| GB / GBC | Rediseño de escenas para pantalla pequeña y pocas tonalidades |
| DS / 3DS | Adaptación a pantallas dobles, tipografía, controles táctiles |
| Wii / Switch | Perfiles de resolución, entrada y audio |
| Xbox / PlayStation posteriores | Activos de mayor calidad según rendimiento y SDK |

### 8.3 Estimador de recursos

Antes de compilar, el conversor debe avisar si:
- Una escena tiene demasiadas texturas.
- Se excede la memoria prevista.
- Se usa una característica no compatible con esa consola.

Esto ahorra compilaciones y pruebas inútiles.

---

## 9. IA y agentes: orquestación, MCP y reglas

### 9.1 Herramientas de coordinación de agentes

| Herramienta | Notas |
|---|---|
| Forge | Ejecuta agentes en ramas/worktrees separados; soporte macOS/Linux (revisar Windows) |
| Conduct (workmux) | Orquestador por terminal compatible con Claude/Codex/OpenCode; worktrees independientes; interesante para Windows |
| Multi-Agent Orchestrator Skill | Divide trabajos, crea worktrees, supervisa ejecuciones |

### 9.2 Reparto recomendado del trabajo

| Agente | Responsabilidad |
|---|---|
| Claude | Arquitectura del motor, análisis de Ren'Py, revisión de decisiones técnicas |
| Codex | Implementación de backends, SDKs, adaptación de APIs |
| OpenCode | Automatización, herramientas auxiliares, pruebas de regresión |
| Antigravity | Interfaz gráfica para importar juegos, configurar plataformas, visualizar resultados |

Son asignaciones recomendadas, no limitaciones. Cada agente trabaja sobre un ticket en su
propio worktree, entrega pruebas y pasa por revisión antes de integrar.

### 9.3 MCP propio (conectado al Test Lab)

En lugar de un MCP por emulador, desarrollar uno propio con estas operaciones:

| Operación MCP | Función |
|---|---|
| `analyze_renpy_project` | Inspeccionar proyecto y detectar incompatibilidades |
| `convert_renpy_project` | Generar datos del motor |
| `build_console_target` | Compilar para una consola |
| `launch_emulator` | Ejecutar el port |
| `run_test_scenario` | Reproducir una prueba |
| `capture_frame` | Capturar pantalla del emulador |
| `read_debug_log` | Recuperar logs |
| `compare_game_states` | Comparar trazas de dos plataformas |
| `generate_compatibility_report` | Crear informe de resultados |

Para acceso inicial a archivos: Filesystem MCP Server, restringiendo directorios.

### 9.4 Ejemplo de tarea ejecutable por un agente

> Trabaja exclusivamente en el backend de PS2 del motor de novelas visuales. Usa los
> contratos del núcleo y no modifiques el conversor Ren'Py. Compila con PS2SDK, ejecuta
> el ELF en PCSX2 mediante Console Test Lab y corre los escenarios automatizados de
> introducción, diálogo, elección y guardado. Revisa los logs, corrige los errores
> reproducibles y entrega un resumen con los cambios, pruebas y limitaciones. No
> integres cambios en main sin revisión.

### 9.5 Reglas para agentes (ai-agent-rules.md)

1. Trabajar solo en la tarea pedida; lo demás se anota como pendiente.
2. No modificar repos hermanos sin permiso.
3. Todo código Python lleva tests y debe pasar `pytest`.
4. Cambiar el bytecode implica actualizar spec, compilador, simulador y motor juntos.
5. Commits: conventional commits en inglés, sin co-autor ni mención a Claude.
6. Documentación en español; código y nombres en inglés.
7. Antes de cambios grandes, proponer plan y esperar aprobación.

---

## 10. Orden de trabajo por fases (roadmap)

No seguir el orden histórico de las consolas. Seguir reutilización de código y
probabilidad de éxito.

### Fase 1 — Consolidar PS1 y crear referencia para PC
- Preservar lo que funciona, documentar el motor actual, construir pruebas reproducibles.
- Implementar el formato intermedio sin romper el port existente.
- **Done:** snoot-ps1 intacto + spec de VNSCENE + tests de round-trip.

### Fase 2 — PS2, PSP y PSP Go
- Primeros backends adicionales; validar la arquitectura.
- **Done:** Snoot Game en PS2 y PSP desde el mismo código de lógica y datos de escena.

### Fase 3 — PS Vita, 3DS, Wii, Xbox Classic
- Adaptadores gráficos y de controles; comprobar qué partes del núcleo se comparten.
- **Done:** al menos 2 de estas 4 plataformas corriendo Snoot.

### Fase 4 — DS, GBA, Switch
- Trabajo especializado en recursos, memoria y representación gráfica.
- **Done:** DS y GBA con versión reducida; Switch con backend propio.

### Fase 5 — PS3, PS4, Xbox One / Series
- SDKs más complejos; validar restricciones de ejecución y distribución.
- **Done:** al menos PS3 y Xbox One corriendo Snoot.

### Fase 6 — GB, GBC, Xbox 360, PS5
- Proyectos especializados: GB/GBC (fidelidad audiovisual), Xbox 360 y PS5 (entorno de ejecución).
- **Done:** GB y GBC con versión Minimal; Xbox 360/PS5 con prototipo documentado.

**Primera meta concreta:** Snoot Game en PS1, PS2 y PSP desde el mismo código de lógica
y los mismos datos de escena.

---

## 11. Tareas detalladas por fase

### 11.0 Preparación del repositorio

- [ ] Crear `E:\Dev\renpy-console-project/` con la estructura propuesta.
- [ ] Inicializar git (repo propio, no tocar los hermanos).
- [ ] Crear `CLAUDE.md`, `PLAN.md` (este doc), `STATUS.md`, `docs/`.
- [ ] Definir `ai-agent-rules.md`.
- [ ] Crear `.gitignore` apropiado.

Estructura propuesta:

```
renpy-console-project/
│
├── tools/
│   ├── renpy-importer/        # evolución del kit (o submódulo)
│   ├── asset-converter/       # perfiles por plataforma
│   ├── compatibility-analyzer/
│   └── console-test-lab/      # automatización universal
│
├── engine/
│   ├── core/                  # VM, escena, texto, guardado, lógica
│   ├── script-vm/             # VNB interpreter
│   ├── graphics/              # abstracción gráfica
│   ├── audio/                 # abstracción de audio
│   └── save-system/           # guardado multiplataforma
│
├── platforms/
│   ├── pc/
│   ├── ps1/
│   ├── ps2/
│   ├── psp/
│   ├── psvita/
│   ├── gba/
│   ├── nds/
│   └── .../
│
├── tests/
│   ├── scenarios/             # escenarios YAML por plataforma
│   ├── golden-traces/         # trazas de referencia
│   └── visual-regression/     # comparación de imágenes
│
└── docs/
    ├── architecture.md
    ├── platform-matrix.md
    ├── ai-agent-rules.md
    ├── formats/
    │   └── vnscene.md
    ├── core-api.md
    └── bitacora.md
```

### 11.1 Fase 1 — Consolidar PS1 y referencia PC

- [ ] Auditar `vn-engine-ps1` y `snoot-ps1`: listar qué es general vs específico.
- [ ] Documentar el motor actual en `docs/motor-actual.md` (basado en `docs/motor.md` de snoot-ps1).
- [ ] Definir Contrato 1 (VNSCENE) formalmente.
- [ ] Definir Contrato 2 (core API) extrayendo de `core/*.h`.
- [ ] Definir Contrato 3 (platform API / caps).
- [ ] Definir Contrato 4 (escenarios de prueba).
- [ ] Crear backend `platforms/pc/` (SDL2 o similar) que corra el núcleo en PC para pruebas rápidas.
- [ ] Migrar el port de snoot-ps1 a consumir VNSCENE sin romper v1.0 (modo compatibilidad).
- [ ] Escribir tests de round-trip: VNSCENE → VNB → ejecución en PC → comparar con snoot-ps1.
- [ ] Documentar en `docs/bitacora.md`.

**Done criteria:**
- `snoot-ps1` v1.0 sigue funcionando sin cambios.
- El núcleo corre en PC con el backend `platforms/pc/`.
- Existe al menos un escenario de prueba que pasa en PC y en PS1 (PCSX-Redux).

### 11.2 Fase 2 — PS2, PSP, PSP Go

- [ ] Instalar y verificar PS2SDK (ps2dev) y PSPSDK.
- [ ] Crear `platforms/ps2/` con backend mínimo (framebuffer, audio, entrada, CD/ISO).
- [ ] Crear `platforms/psp/` (reutilizar PSPSDK).
- [ ] Compilar el núcleo para PS2 (ELF) y PSP (EBOOT).
- [ ] Implementar Console Test Lab adapters para PCSX2 y PPSSPP.
- [ ] Escribir escenarios de prueba para PS2 y PSP.
- [ ] Portar Snoot Game a PS2 y PSP (imágenes, audio, bytecode).
- [ ] Validar en emulador (PCSX2, PPSSPP).
- [ ] Medir memoria y disco; ajustar.

**Done criteria:**
- Snoot Game corre en PCSX2 y PPSSPP con los escenarios de introducción, diálogo, elección y guardado pasando.
- Logs `[ENGINE]` disponibles en ambos.
- Comparación visual contra PS1 dentro de tolerancia.

### 11.3 Fase 3 — PS Vita, 3DS, Wii, Xbox Classic

- [ ] Instalar VitaSDK, devkitPro (3DS, Wii), NXDK.
- [ ] Crear backends para cada plataforma.
- [ ] Implementar adaptadores de Test Lab (Vita3K, Azahar, Dolphin, xemu).
- [ ] Portar Snoot a al menos 2 de estas 4.
- [ ] Documentar lecciones (qué se comparte, qué no).

**Done criteria:**
- Al menos 2 plataformas de esta fase corriendo Snoot con escenarios pasando.

### 11.4 Fase 4 — DS, GBA, Switch

- [ ] Instalar devkitPro (DS, GBA, Switch).
- [ ] Crear backend DS (libnds) y GBA (Butano/devkitARM).
- [ ] Implementar motor Minimal/Lite para GB/GBC/GBA.
- [ ] Transformar escenas de Snoot para pantallas pequeñas (rediseño manual asistido).
- [ ] Crear backend Switch (libnx).
- [ ] Validar en melonDS, mGBA, y hardware/emulador Switch.

**Done criteria:**
- DS y GBA corren una versión reducida de Snoot.
- Switch corre la versión Full.

### 11.5 Fase 5 — PS3, PS4, Xbox One / Series

- [ ] Instalar PSL1GHT, OpenOrbis, GDK (si hay acceso).
- [ ] Crear backends.
- [ ] Validar restricciones de ejecución (firmado, instalación).
- [ ] Portar Snoot a al menos PS3 y Xbox One.

**Done criteria:**
- PS3 y Xbox One corren Snoot con escenarios pasando.

### 11.6 Fase 6 — GB, GBC, Xbox 360, PS5 (especializados)

- [ ] GB/GBC: motor Minimal, escenas rediseñadas, audio reducido.
- [ ] Xbox 360: validar LibXenon + cadena de ejecución.
- [ ] PS5: investigación; prototipo con SDK experimental o acceso oficial.
- [ ] Documentar resultados y límites.

**Done criteria:**
- GB y GBC corren versión Minimal de Snoot.
- Xbox 360 y PS5 tienen prototipo documentado (aunque no completo).

---

## 12. Riesgos, licencias y distribución

### 12.1 Riesgos técnicos

| Riesgo | Mitigación |
|---|---|
| Memoria insuficiente en consolas viejas | Motor reducido por nivel; estimador de recursos |
| Audio/video no soportado | Perfiles por plataforma; alternativas (imágenes en lugar de video) |
| Entorno de ejecución incierto (Xbox 360, PS5) | Fase de investigación; no bloquear otras plataformas |
| Diferencias visuales entre plataformas | Comparación automatizada de capturas; tolerancias |
| Python dinámico en juegos | Detección y reporte; equivalencias manuales |

### 12.2 Licencias

- **Ren'Py:** MIT (código).
- **Snoot Game:** AGPL-3.0 (código/guion) + CC-BY-SA-4.0 (arte/audio).
- **I Wani Hug that Gator!:** AGPL-3.0 + CC-BY-SA-4.0.
- **Motor (vn-engine-ps1):** MIT.
- **Kit:** (definir, probablemente MIT).
- Los ports son obras derivadas: deben publicarse con las licencias del juego original
  y las atribuciones correspondientes.
- Antes de distribuir, revisar derechos de cada juego.

### 12.3 Distribución

- Los discos/ROMs generados contienen material del juego → respetar licencias.
- El código del port y del motor se publica en GitHub.
- Los assets del juego no se redistribuyen sin permiso.

---

## 13. Métricas de éxito

| Métrica | Objetivo |
|---|---|
| Plataformas con Snoot Game funcionando | ≥ 3 (PS1, PS2, PSP) en Fase 2; ≥ 6 en Fase 3; ≥ 10 al final |
| Escenarios de prueba automatizados | ≥ 1 por plataforma |
| Cobertura del conversor (juegos Ren'Py soportados) | Snoot + Wani + The Question + tutorial |
| Tiempo de port de un juego nuevo (con asistencia IA) | < 1 semana para PS1/PS2/PSP |
| Regresiones detectadas automáticamente | ≥ 80% de los bugs de renderizado/audio |
| Documentación | Plan, arquitectura, API, bitácora actualizados |

---

## 14. Apéndices

### 14.1 Rutas clave

| Ruta | Contenido |
|---|---|
| `E:\Dev\snoot-ps1` | Port PS1 de referencia (no modificar) |
| `E:\Dev\vn-engine-ps1` | Motor compartido (proponer cambios) |
| `E:\Dev\wani-ps1` | Port Wani en curso (no modificar) |
| `E:\Dev\renpy-port-kit` | Kit de conversión Ren'Py |
| `E:\Dev\renpy-console-project` | Este proyecto (nuevo) |
| `E:\snoot` | Fuentes de juegos, SDKs, emuladores |

### 14.2 Comandos de referencia (PowerShell)

```powershell
# Verificar entorno (cualquier proyecto)
.\.venv\Scripts\python.exe tools\check_env.py

# Tests
.\.venv\Scripts\python.exe -m pytest

# Build (snoot-ps1)
python build.py

# Build (wani-ps1)
.\.venv\Scripts\python.exe build.py

# Motor compartido
cmake --preset default
cmake --build build

# Kit: analizar un juego
.\.venv\Scripts\python.exe -m renpykit analyze juegos\<juego>

# Kit: generar guion JSON
.\.venv\Scripts\python.exe -m renpykit script juegos\<juego> --pretty
```

### 14.2b Requisitos de instalación (descargas)

Ver `docs/what-to-download.md` para la lista completa por fase.
Prioridad inmediata (Fase 1): SDL2 dev para backend PC.
Siguiente (Fase 2): PS2SDK, PSPSDK, PCSX2, PPSSPP.

### 14.3 Referencias externas

- PSn00bSDK: https://github.com/Lameguy64/PSn00bSDK
- PS2SDK: https://github.com/ps2dev/ps2sdk
- PSL1GHT: https://github.com/ps3dev/PSL1GHT
- OpenOrbis: https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain
- PSPSDK: https://github.com/pspdev/pspsdk
- VitaSDK: https://github.com/vitasdk
- devkitPro: https://devkitpro.org/
- GBDK-2020: https://github.com/gbdk-2020/gbdk-2020
- NXDK: https://github.com/XboxDev/nxdk
- LibXenon: https://github.com/Free60Project/libxenon
- unrpyc: https://github.com/CensoredUsername/unrpyc
- rpatool: https://github.com/Shizmob/rpatool

### 14.4 Documentos internos a leer

- `E:\Dev\snoot-ps1\CLAUDE.md`, `PLAN.md`, `STATUS.md`, `docs/bytecode.md`
- `E:\Dev\vn-engine-ps1\CLAUDE.md`, `PLAN.md`, `STATUS.md`, `docs/bytecode.md`
- `E:\Dev\wani-ps1\CLAUDE.md`, `PLAN.md`, `STATUS.md`
- `E:\Dev\renpy-port-kit\CLAUDE.md`, `PLAN.md`, `STATUS.md`

---

## 15. Próximos pasos inmediatos (siguiente sesión)

1. Crear el repositorio `renpy-console-project` con la estructura propuesta.
2. Copiar este plan como `PLAN.md`.
3. Crear `CLAUDE.md` y `STATUS.md` iniciales.
4. Definir Contrato 1 (VNSCENE) en `docs/formats/vnscene.md` (reusar ops de VNB).
5. Auditar `vn-engine-ps1/core/` para extraer Contrato 2 (core API).
6. Crear backend `platforms/pc/` mínimo (SDL2) para pruebas rápidas.
7. No tocar los repos hermanos; proponer cambios por PR/copia cuando estén listos.

---

*Fin del plan v0.1. Actualizar este documento conforme avance el proyecto.*
## 16. Detalles de instalación y configuración por SDK

### 16.1 PS1 (ya configurado)
- PSn00bSDK vía MSYS2 en `C:\msys64\usr\local\psn00bsdk`.
- Variable `PSN00BSDK_LIBS` definida.
- CMake + Ninja + Python 3.12 + ffmpeg.
- Emuladores: DuckStation (jugar), PCSX-Redux (depurar, Lua), BizHawk (Lua).
- BIOS reales en `E:\snoot\ps1 bios`.

### 16.2 PS2
- Instalar ps2dev toolchain (MSYS2 o Linux/WSL2).
- PS2SDK: `git clone https://github.com/ps2dev/ps2sdk`.
- Compilador: `mips64r5900el-ps2-elf-gcc`.
- Empaquetado: `mkps2iso` o `ps2-packer`.
- Emulador: PCSX2 (CLI: `-batch -nogui -elf <file>`).
- Referencia: https://github.com/ps2dev/ps2sdk

### 16.3 PS3
- PSL1GHT: `git clone https://github.com/ps3dev/PSL1GHT`.
- Compilador: `ppu-gcc`.
- Empaquetado: `make_self` / `make_package`.
- Emulador: RPCS3 (CLI + logs).
- Nota: requiere firmware y claves; solo para desarrollo.

### 16.4 PS4
- OpenOrbis: https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain.
- Compilador: `x86_64-orbis-elf-clang`.
- Pruebas: shadPS4 o hardware con jailbreak/devkit.
- Distribución: requiere acceso oficial o homebrew.

### 16.5 PS5
- PS5SDK experimental: https://github.com/PS5Dev/PS5SDK.
- Estado: no genera aplicaciones completas.
- Acción: fase de investigación; buscar acceso oficial (devkit).

### 16.6 PSP / PSP Go
- PSPSDK: https://github.com/pspdev/pspsdk.
- Compilador: `psp-gcc`.
- Empaquetado: `psp-packer` / `prxtool`.
- Emulador: PPSSPP (CLI + debugger).
- PSP Go comparte el mismo SDK; solo cambia el hardware de salida.

### 16.7 PS Vita
- VitaSDK: https://github.com/vitasdk.
- Compilador: `arm-vita-eabi-gcc`.
- Empaquetado: `vita-make-fself` / `vita-mksfoex`.
- Emulador: Vita3K.

### 16.8 Game Boy / Game Boy Color
- GBDK-2020: https://github.com/gbdk-2020/gbdk-2020.
- Compilador: `lcc` (SDCC-based).
- Emulador: BizHawk / Mesen 2 (Lua).
- Nivel motor: Minimal.

### 16.9 Game Boy Advance
- devkitARM: https://devkitpro.org/.
- Bibliotecas: Butano (https://github.com/GValiente/butano) o libgba.
- Compilador: `arm-none-eabi-gcc`.
- Emulador: mGBA (Lua nativo).
- Nivel motor: Lite.

### 16.10 Nintendo DS
- BlocksDS / libnds: https://github.com/blocksds.
- Compilador: `arm-none-eabi-gcc`.
- Emulador: melonDS / DeSmuME (Lua).
- Nivel motor: Standard.

### 16.11 Nintendo 3DS
- devkitARM + libctru + citro2d.
- Compilador: `arm-none-eabi-gcc`.
- Emulador: Azahar.
- Nivel motor: Standard.

### 16.12 Wii
- devkitPPC + libogc.
- Compilador: `powerpc-eabi-gcc`.
- Emulador: Dolphin (CLI, playback de entradas).
- Nivel motor: Full.

### 16.13 Switch 1
- devkitA64 + libnx.
- Compilador: `aarch64-none-elf-gcc`.
- Pruebas: hardware o emuladores compatibles (Ryujinx/Yuzu forks).
- Nivel motor: Full.

### 16.14 Xbox Classic
- NXDK: https://github.com/XboxDev/nxdk.
- Incluye SDL2 (entrada, audio, gráficos 2D).
- Emulador: xemu.
- Nivel motor: Standard.

### 16.15 Xbox 360
- LibXenon: https://github.com/Free60Project/libxenon.
- Bare-metal; validar cadena de ejecución.
- Emulador: Xenia (según formato).
- Nivel motor: Full (pero entorno incierto).

### 16.16 Xbox One / Series S / Series X
- UWP + Visual Studio / GDK autorizado.
- Pruebas: Developer Mode en consola.
- Distribución comercial: otra ruta (no UWP para juegos nuevos).
- Nivel motor: Full.

---

## 17. Especificación detallada de VNSCENE (ops)

Basado en `docs/bytecode.md` v2 del motor. Ops mínimos requeridos:

### 17.1 Control de flujo
- `label` — define una etiqueta.
- `jump` — salto incondicional.
- `call` — llamada a subrutina.
- `return` — retorno.
- `if` / `else` / `endif` — condicionales.
- `choice` — menú de opciones.

### 17.2 Escena y visuales
- `background` — fondo.
- `show` — mostrar sprite/CG.
- `hide` — ocultar.
- `scene` — limpiar y establecer fondo.
- `camera` — zoom, desplazamiento, sacudidas.
- `transition` — disolver, fundido, sacudida, movimiento.

### 17.3 Diálogo y texto
- `dialogue` — línea de diálogo (speaker, text, tags).
- `narrator` — narración.
- `text_tag` — {sh}, {sc}, {cps}, {w}, {nw}, {i}, {b}.
- `window` — mostrar/ocultar caja de texto.

### 17.4 Audio
- `music` — reproducir/cambiar música.
- `ambient` — ambiente en bucle.
- `sfx` — efecto de sonido.
- `voice` — voz.

### 17.5 Variables y estado
- `set` — asignar variable.
- `add` / `sub` / `mul` / `div` — aritmética.
- `persistent` — variables persistentes (guardado).

### 17.6 Guardado
- `save` — guardar partida.
- `load` — cargar partida.
- `checkpoint` — punto de guardado automático.

### 17.7 Especiales
- `special` — pantallas especiales (chat, teclado, créditos, dibujo).
- `video` — reproducir video (STR o cuadros).
- `input` — entrada de texto.
- `imagemap` — menú con imágenes.

### 17.8 Animación (ATL)
- `anim` — tabla de animación (eventos por tiempo).
- `anim_event` — cambio de imagen en un tiempo.
- `loop` — bucle de animación.

---

## 18. Formato de logs del motor (diagnóstico)

El motor emite líneas con prefijo `[ENGINE]`:

```
[ENGINE] scene=<id>
[ENGINE] dialogue=<id>
[ENGINE] asset=<asset_id>
[ENGINE] choice=<index>
[ENGINE] jump=<label>
[ENGINE] frame_ms=<ms>
[ENGINE] status=OK|ERROR:<code>
[ENGINE] mem_vram_used=<bytes>
[ENGINE] mem_ram_used=<bytes>
```

Estos logs se capturan por el Test Lab y se usan para comparar trazas entre plataformas.

---

## 19. Estrategia de agentes por ticket

Cada ticket sigue este flujo:

1. **Análisis:** el agente lee el ticket + docs relevantes.
2. **Plan:** propone cambios (sin tocar código aún).
3. **Aprobación:** el usuario aprueba.
4. **Implementación:** en worktree propio.
5. **Pruebas:** escribe/actualiza tests; ejecuta `pytest`.
6. **Validación:** compila para la plataforma; ejecuta escenarios del Test Lab.
7. **Reporte:** resumen de cambios, pruebas, limitaciones.
8. **Revisión:** el usuario revisa; si OK, merge.

### 19.1 Plantilla de ticket

```markdown
## Ticket: <título>
**Plataforma:** <consola>
**Prioridad:** alta/media/baja
**Dependencias:** <tickets previos>

### Objetivo
<qué se quiere lograr>

### Criterios de aceptación
- [ ] ...
- [ ] ...

### Archivos a tocar
- platforms/<consola>/...
- tests/...

### Notas
<restricciones, referencias>
```

---

## 20. Cronograma estimado (meses)

| Mes | Fase | Entregable principal |
|---|---|---|
| 1 | Fase 1 | Núcleo en PC + VNSCENE spec + contratos |
| 2 | Fase 2 (inicio) | Backend PS2 mínimo + Test Lab adaptador PCSX2 |
| 3 | Fase 2 (fin) | Snoot en PS2 y PSP |
| 4 | Fase 3 (inicio) | Backends Vita, 3DS, Wii, Xbox Classic |
| 5 | Fase 3 (fin) | Snoot en 2+ de estas plataformas |
| 6 | Fase 4 | DS, GBA, Switch |
| 7 | Fase 5 | PS3, PS4, Xbox One |
| 8 | Fase 6 | GB, GBC, Xbox 360, PS5 (especializados) |
| 9+ | Pulido | Documentación, licencias, distribución |

---

## 21. Checklist de “¿estoy listo para empezar a codear?”

- [ ] Repositorio `renpy-console-project` creado.
- [ ] Plan leído y aprobado.
- [ ] VNSCENE spec escrita (`docs/formats/vnscene.md`).
- [ ] Core API documentada (`docs/core-api.md`).
- [ ] Backend PC mínimo funcionando.
- [ ] Al menos un escenario de prueba pasando en PC.
- [ ] Console Test Lab con adaptador para un emulador (PCSX-Redux o mGBA).
- [ ] Agente IA puede ejecutar un escenario end-to-end.

Si todos los puntos están marcados, el ecosistema está listo para escalar.

---

*Fin del plan v0.1 extendido. Actualizar conforme avance.*
<!-- END -->

