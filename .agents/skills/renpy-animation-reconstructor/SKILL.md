---
name: renpy-animation-reconstructor
description: Traduce transforms ATL, transiciones y movimientos de sprites de Ren'Py a las tablas ANIM del bytecode VNB (tiempo, posición, zoom, alpha, giro) y valida el resultado contra la traza de referencia. Úsala al implementar o depurar animaciones en el compilador o en cualquier backend.
---
# Reconstructor de animaciones ATL

## Dónde vive hoy
- Formato: `E:\Dev\vn-engine-ps1\docs\bytecode.md` (v3: ANIM con giro en el bit 7 de flags).
- Compilador: `E:\Dev\vn-engine-ps1\vncompiler\` (`temporal.py`, `formatos.py`); bloques con cámara en
  `E:\Dev\wani-ps1\tools\script_compiler\camera_blocks.py`.
- Lectura de ATL en el kit: `E:\Dev\renpy-port-kit\renpykit\temporal.py`.
- Interpolación en el motor: `engine/core/scene.c` (`scene_look`).

## Modelo
Cada ATL es una lista de claves por sprite: tiempo, posición, zoom, alpha, color, giro, con interpolación.
`parallel` → pistas simultáneas; `repeat` → bucle; `pause` → avanza el tiempo; `function` → no soportado
(reportar con archivo:línea).

## Procedimiento
1. Leer el ATL con la skill `renpy-source-analyzer` (archivo:línea).
2. Traducir a claves ANIM. Las posiciones se calculan por perfil de plataforma al compilar, nunca en el runtime
   de PS1/GBA/GB.
3. Validar: eventos SHOW de la traza del port contra la referencia de Ren'Py (tolerancia por defecto ±2 cuadros).
4. Cambiar el formato ANIM es cambiar el contrato C1: spec, compilador, simulador y motor en el mismo cambio.
   Si hace falta, propónlo en el reporte; no lo cambies tú.

## Errores comunes
- Olvidar `xanchor/yanchor` (0.0 en posiciones absolutas, 0.5 en `center`).
- Tratar `zoom` y `xzoom/yzoom` como acumulativos.
- Tiempos ATL en segundos (float): pasar a cuadros enteros.
