# renpy-console-project

Ecosistema de portabilidad de Ren'Py a consolas, asistido por IA: un núcleo C99 compartido, un backend por
plataforma y un laboratorio de pruebas automático. Primero Snoot Game; después Wani y otros juegos Ren'Py.

## Primera meta

Snoot Game en **PS1, PC, PSP y PS2** desde el mismo núcleo y los mismos datos.

## Estructura

- `engine/core/` — núcleo C99 portable (VM, escena, texto, capítulos) y contrato con las plataformas.
- `platforms/` — backends: `ps1/` (PSn00bSDK), `pc/` (pruebas de host); `sdl/` y el resto según el plan.
- `tools/` — Test Lab (`ctl`), recursos (`assetpipe`), agentes.
- `tests/` — pruebas de host, escenarios y trazas de referencia.
- `docs/` — API del núcleo, matriz de plataformas, descargas, bitácora.

## Documentos

- `PLAN.md` — plan, decisiones, contratos y fases con compuertas.
- `STATUS.md` — en qué va el proyecto.
- `AGENTS.md` — reglas para todos los agentes IA.

## Licencia

Motor: MIT. Cada port publicado es obra derivada del juego original y respeta sus licencias (Snoot y Wani:
AGPL-3.0 para el código, CC-BY-SA 4.0 para arte y audio). Ver `PLAN.md` sección 10.
