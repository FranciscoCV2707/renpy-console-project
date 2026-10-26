---
name: console-asset-optimizer
description: Convierte imágenes, audio, video y fuentes de un juego Ren'Py a los formatos y presupuestos de memoria de cada consola, de forma determinista. Úsala al agregar una plataforma, cambiar la calidad o investigar desbordes de memoria.
---
# Optimizador de recursos por consola

## Dónde vive hoy
- PS1: herramientas de `E:\Dev\snoot-ps1\tools\` y `E:\Dev\wani-ps1\tools\` (imágenes IMG1 con CLUT, XA/SPU y
  STR con `psxavenc`, fuente `build_font.py`). Se reutilizan, no se reescriben.
- Resto de plataformas: `tools/assetpipe/` de este repo (Fase 4), con un perfil por plataforma.

## Principios
- Salida en `build/assets/<plataforma>/` con `manifest.json` y hash por recurso.
- Determinista: semillas fijas de tramado y cuantización; misma entrada → mismo hash.
- Presupuestos por plataforma en `docs/platform-matrix.md` (RAM, VRAM, tamaño del medio).

## Recetas base
- Imágenes: redimensionar a la resolución destino (Lanczos), cuantizar a la profundidad del hardware (4/8/16 bpp),
  paleta por imagen o por escena, tramado ordenado en GB/GBA.
- Música en streaming en el formato nativo (XA en PS1, ADPCM...); efectos cortos en memoria.
- Video según plataforma (STR en PS1, decodificador nativo donde exista, cuadros a baja tasa); en GB/GBA se
  reemplaza por escenas fijas.
- Fuentes: atlas de bitmap por tamaño y resolución (en PS1, `FONT.BIN` de 256x256 a 4 bits).

## Verificación
- Pruebas del pipeline con `pytest`.
- Ninguna escena excede la RAM/VRAM de la plataforma.
- Licencias: los recursos convertidos siguen siendo CC-BY-SA 4.0 con atribución.
