# Backend SDL2 para PC

## Compilar y ejecutar

Requiere SDL2 2.32 en MSYS2 ucrt64. `python platforms/sdl/build.py --trace` compila Snoot a
`build/pc/snoot.exe` y copia `SDL2.dll`. Para la prueba automática, prepara primero el disco con
`python -m tools.ctl run --target ps1 --scenario tests/scenarios/snoot-smoke.yaml`; después ejecuta
`python -m tools.ctl run --target pc --scenario tests/scenarios/snoot-smoke.yaml`.

El backend lee el directorio plano `build/ctl/ps1/disc`, con los mismos archivos del disco PS1. El adapter
reemplaza `AUTOTEST.BIN` por las entradas del escenario. Con `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy` y
`VN_FAST=1` ejecuta sin ventana ni pausas de 60 Hz. La traza va a stdout y a `build/ctl/pc/trace.txt`.
Cada paso `shot` crea un BMP con el nombre indicado en `build/ctl/pc/`.

## Entrada

| Acción | Teclas |
|---|---|
| Cruz / confirmar | Enter o Espacio |
| Círculo / volver | Escape |
| Cuadrado | Retroceso |
| Triángulo | Tab |
| Cruceta | Flechas o WASD |
| L1 / R1 | Q / E |
| L2 / R2 | Shift izquierdo / derecho |
| Start / Select | F1 / F2 |

En un mando SDL estándar, A/B/X/Y corresponden a Cruz/Círculo/Cuadrado/Triángulo; cruceta, hombros, gatillos,
Start y Back se asignan a los mismos botones.

La entrada automática conserva el formato `AUTOTEST.BIN`: botones, decisiones por índice, autoplay, captura y salida.

## Implementación

La ventana usa el espacio lógico 320×240 a escala 3×. El render procesa las capas del 20 al 0. IMG1 se
descomprime con el LZ4 del núcleo y se expande desde su paleta a textura RGBA; las coordenadas de VRAM/CLUT no
se usan. Los recursos se guardan en RAM. El guardado alterna dos archivos en `build/ctl/pc/save/` con número,
magic y checksum.

SDL mantiene la API de audio y sus niveles/colas de estado; la salida queda en silencio hasta integrar el
decodificador de T-403. FMV no se reproduce en este backend todavía.
