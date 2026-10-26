# AGENTS.md — Reglas para todos los agentes de renpy-console-project

Lo leen solos Codex, OpenCode (Beam) y Kilo; a Claude, Vibe y Antigravity se lo indica su prompt.

## Antes de empezar
1. Tu tarea está en `.agents/inbox/<T-xxx>.md` (o te la dan en el prompt). Léela completa.
2. Trabajas solo dentro de tu worktree. Nunca escribas fuera.
3. Lee `PLAN.md` (secciones 2 a 4) y, si tocas el motor, `docs/core-api.md`.

## Prohibido
- Editar contratos: `engine/core/vn_platform.h`, el formato VNB, el protocolo TRACE y el formato de escenarios
  (`PLAN.md` sección 4), `tools/agents/agents.toml`. Si crees que deben cambiar, propónlo en tu reporte.
- Editar `engine/ps1-base/` (copia de referencia) o cualquier repo hermano (`vn-engine-ps1`, `snoot-ps1`,
  `wani-ps1`, `renpy-port-kit`).
- `git push`, `git merge`, `git rebase`, `git reset --hard`, borrar ramas.
- Tocar archivos fuera de la lista "Archivos permitidos" de tu tarea.
- Inventar resultados: pega la salida real de los comandos de verificación.
- Adivinar: si algo del juego o del hardware no se entiende, repórtalo con archivo y línea. Para PS1, basarse en
  los ejemplos de PSn00bSDK y en psx-spx; no inventar registros ni funciones.
- Descargar SDKs o emuladores.

## Cómo compilar y probar
- Pruebas: `E:\Dev\renpy-console-project\.venv\Scripts\python.exe -m pytest` (incluye la prueba C de host del
  núcleo). En un worktree no hay `.venv`: usa siempre el del repo principal, con esa ruta completa.
- Host: `C:\msys64\ucrt64\bin\gcc.exe` (C99, `-Wall -Wextra -pedantic`).
- PS1: `C:\msys64\usr\local\psn00bsdk\bin\mipsel-none-elf-gcc.exe` con los flags de `docs/core-api.md`.
- Otras consolas: siempre por Docker con la imagen de `docs/platforms/<x>.md`.

## Estilo
- C99 en `engine/core` y backends; compatible con PSn00bSDK. Sin memoria dinámica en el bucle de juego de
  PS1/GBA/GB. El núcleo no incluye nada de una consola: solo `vn_platform.h`.
- Nada fijo de un juego en el núcleo: lo propio de cada juego va en datos o en su módulo.
- Python 3.12 en `tools/`, con tests en `tests/`. Windows first: `encoding="utf-8"`, `pathlib.Path`,
  `subprocess.run([...], check=True)` sin `shell=True`. Scripts en Python, no `.sh` ni `.bat`.
- Conversores deterministas: misma entrada → mismo hash.
- Documentación en español; código y nombres en inglés.

## Al terminar
1. Corre los pasos de verificación de tu tarea.
2. `git add` solo de archivos permitidos y commit en conventional commits en inglés, sin línea de coautor ni
   mención a la IA; la tarea va en el cuerpo: `Refs: T-xxx`.
3. Escribe `.agents/reports/<T-xxx>.md` con `.agents/templates/REPORT.md` (máximo 60 líneas) e inclúyelo en el
   commit.
4. Si te bloqueas: documenta el bloqueo en el reporte, haz commit de lo útil y termina.
5. Fuera de una tarea de agente (sesión directa con el usuario): actualiza `docs/bitacora.md` y `STATUS.md`, di
   cómo probar el cambio y haz commit. Antes de cambios grandes, propón un plan y espera aprobación.
