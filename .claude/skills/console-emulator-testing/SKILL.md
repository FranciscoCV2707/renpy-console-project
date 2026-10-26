---
name: console-emulator-testing
description: Corre builds de prueba en emuladores sin interfaz, recoge trazas y capturas, y las compara con la referencia (Ren'Py o la v1.0 de PS1). Úsala para validar cualquier cambio que afecte a una plataforma o para diagnosticar diferencias.
---
# Pruebas en emulador

## Comandos
- Test Lab (desde la Fase 2): `python -m tools.ctl run --target <plataforma> --scenario <id>`,
  `python -m tools.ctl compare ...`, `python -m tools.ctl report --target <plataforma>`.
- Hoy, PS1 contra la v1.0 (en `E:\Dev\vn-engine-ps1`): `.\.venv\Scripts\python.exe tests\emu\snoot.py check`
  (escenarios: titulo, menus, partida, cargar, teclado, chat, creditos).
- Hoy, guiones de botones sueltos (en `E:\Dev\snoot-ps1`): `python -m tools.engine.emutest --steps "..."`.
- Núcleo en host: `.\.venv\Scripts\python.exe -m pytest` en este repo.

## Interpretación
- Diagnostica el PRIMER evento divergente, no los siguientes.
- LABEL/JUMP distinto → lógica: reprodúcelo en PC primero.
- SHOW distinto → ATL o escalado (skill `renpy-animation-reconstructor`).
- PLAY/STOP distinto → pipeline de audio o canal.
- Sin traza → falla al arrancar: log del emulador y arranque del backend.

## Reglas
- Una plataforma no está bien solo porque compila o arranca.
- Pega en el reporte la línea de veredicto y la ruta del reporte completo.
- Emuladores y BIOS en `E:\snoot`; no los muevas ni los descargues.
