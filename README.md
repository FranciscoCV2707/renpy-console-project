# renpy-console-project

Ecosistema de portabilidad de Ren'Py a consolas, asistido por IA: un núcleo C99 compartido, un backend por
plataforma y un laboratorio de pruebas automático. Primero Snoot Game; después Wani y otros juegos Ren'Py.

## Meta actual

Snoot Game, en español, en todas las consolas del plan desde el mismo núcleo. Hoy coincide con Ren'Py en PS1, PC, PSP,
PS2, Vita, 3DS, Wii, PS4, DS y GBA (ruta `chapter_x2`); el estado por consola está en `STATUS.md`.

## Estructura

- `engine/core/` — núcleo C99 portable (VM, escena, texto, capítulos) y contrato con las plataformas.
- `platforms/` — backends: `ps1/` (PSn00bSDK), `sdl/` (PC, PSP, PS2, Vita, 3DS, Wii, Xbox, Switch, PS4, PS3; un bloque
  por consola en `sdl_target.h`), `ds/`, `gba/`; cada carpeta de consola trae su `build.py` en Docker.
- `tools/` — Test Lab (`ctl`), recursos (`assetpipe`), agentes.
- `tests/` — pruebas de host, escenarios y trazas de referencia.
- `docs/` — API del núcleo, matriz de plataformas, descargas, bitácora.

## Documentos

- `PLAN.md` — plan, decisiones, contratos y fases con compuertas.
- `STATUS.md` — en qué va el proyecto.
- `CONTINUAR.md` — cómo retomar el trabajo (otra PC o sesión nueva).
- `REINSTALAR.md` — qué respaldar e instalar.
- `AGENTS.md` — reglas para todos los agentes IA.

## Licencia

Motor: MIT. Cada port publicado es obra derivada del juego original y respeta sus licencias (Snoot y Wani:
AGPL-3.0 para el código, CC-BY-SA 4.0 para arte y audio). Ver `PLAN.md` sección 10.
