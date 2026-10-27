# Demake de GBA — presupuesto del cartucho (T-701, PLAN.md D19)

Dice si Snoot Game (solo español, D16) cabe en un cartucho de GBA de 32 MB con la fidelidad
de D19, y cuánto ocupa cada parte.

```
E:/Dev/renpy-console-project/.venv/Scripts/python.exe -m tools.demake.gba_budget --game E:/snoot/snootgame/game
```

## Resultado (medido sobre el juego real)

| Categoría | Archivos | Bytes LZ77 | Parte del total | Método |
|---|---|---|---|---|
| Fondos | 322 | 4.436.339 | 18,0 % | muestra de 20, media ≈ 13,3 KB por fotograma, extrapolada |
| Sprites | 265 | 646.136 | 2,6 % | muestra de 20, media ≈ 2,4 KB por sprite, extrapolada |
| Música | 105 | 16.074.132 | 65,3 % | bucle de 20 s × 8000 Hz × 1 byte por pista |
| Efectos | 81 | 2.102.595 | 8,5 % | duración completa × 8000 Hz × 1 byte |
| Texto | 46 | 1.338.679 | 5,4 % | 3.358.817 bytes UTF-8 de `tl/es` comprimidos |
| **Total** | | **24.597.881** | **73,3 %** | de 33.554.432 bytes (32 MB) |

**Veredicto: CABE.** Sobran **8.956.551 bytes (8,5 MB)** para el motor VNB,
las fuentes, los menús y los datos de guardado. Los PNG convertidos de muestra quedan en
`build/demake/gba/` (por ejemplo `backgrounds_aquarium.png`).

## Método por categoría

- **Fondos**: todo lo de `images/` que no sea sprite de personaje (escenas, CG, overlays,
  VFX). Cada imagen se encaja en un fotograma de modo 4 (GBATEK: "Video Mode 4 - 240x160,
  8bit (256 colors)"), 240×160 a 8 bpp = 38.400 bytes sin comprimir, cuantizado a 256 colores
  con tramado Floyd-Steinberg (Pillow `quantize`), comprimido con el LZ77 de la BIOS de GBA
  (GBATEK: "LZ77 Decompression (SWI 11h)", tipo 0x10, ventana de 4096, coincidencias de 3 a
  18). Se mide una muestra determinista de 20 (espaciada uniformemente sobre la lista
  ordenada), media ≈ 13,3 KB por fotograma (66 % de los 38,4 KB sin comprimir), y se
  extrapola al total, más 512 bytes de paleta BGR555 por fotograma (GBATEK: paleta de 256
  colores de 2 bytes).
- **Sprites**: carpetas de personaje de Snoot (`anon`, `fang`, `fangparents`, `highres`,
  `moe`, `naomi`, `naser`, `reed`, `rosa`, `spears`, `stella`, `tracy`, `trish`, `trishfam`).
  Cada sprite se recorta al rectángulo opaco del personaje, se escala a 160 px de alto y se
  cuantiza a 16 colores con tramado (D19); los índices se almacenan a 4 bpp como los tiles de
  GBA (GBATEK: "OBJ Tiles 4bit"), más 32 bytes de paleta. Misma medición por muestra de 20:
  media ≈ 2,4 KB por sprite.
- **Música**: audio de más de 10 s (mismo umbral música/efecto que los perfiles de assetpipe,
  D18). D19 fija PCM de 8 bits mono a 8 kHz en bucles de 20 s: 20 × 8000 = 160.000 bytes por
  pista; las pistas más cortas que 20 s cuentan su duración real.
- **Efectos**: audio de 10 s o menos, completo: duración × 8000 bytes.
- **Texto**: los 46 `.rpy` de `tl/es` (3.358.817 bytes UTF-8) comprimidos con el LZ77 de la
  BIOS. Es una cota superior: el VNB solo llevaría las cadenas traducidas, no el script
  completo (ver el recorte 3).

El cartucho máximo de GBA son 32 MB (GBATEK: "GBA Cartridges ... max 32MB"). El compresor LZ77
produce el formato exacto de la BIOS y `tests/test_gba_budget.py` verifica el ida y vuelta con
un decodificador de referencia.

## Qué recortar si no cupiese (con números)

No hace falta hoy, pero por orden de ahorro:

1. **Bucles de música de 10 s en vez de 20**: 105 pistas × 80.000 = 8.400.000 bytes; el total
   bajaría a 16.197.881 (48,3 %). Es el único recorte grande sin tocar la fidelidad de D19.
2. **Menos pistas de música**: cada pista eliminada ahorra 160.000 bytes (20 s de bucle).
3. **Texto como cadenas en vez de `.rpy` completos**: los literales de cadena de `tl/es` son
   1.714.923 bytes UTF-8, 904.087 comprimidos (medidos extrayendo los literales con una
   expresión regular); frente a 1.338.679 ahorra ~435 KB de la cota superior actual.
4. **Fondos en tiles de 4 bpp en vez de modo 4**: los índices pasan de 8 a 4 bpp (la mitad de
   bytes sin comprimir); ahorro real solo medible convirtiendo de verdad a tiles, no estimado
   aquí.

## Supuestos y exclusiones

- Las imágenes con texto traducido (`tl/es/images`, 39 archivos) sustituyen a las originales
  vía `source_file` de assetpipe; no se cuentan dos veces.
- Dos PNG de portada que viven dentro de `audio/OST/` quedan fuera del inventario de imágenes
  (la tarea define fondos como `images/`): ~197 KB originales, ~27 KB convertidas; margen de
  sobra de sobra.
- El tramado Floyd-Steinberg sobre ruido fino reduce la compresión LZ77 (~66 % del original);
  sin tramado los fotogramas comprimirían mejor, pero D19 lo exige.

## Formato del paquete (T-702)

`python -m tools.demake.gba_pack --game <game> --out <directorio>` genera un archivo por
imagen o pista, `text.bin` y `manifest.json`. Los nombres de salida se derivan del SHA-256
del id de origen para evitar colisiones y no dependen de la ruta absoluta del juego.

- `bg/<hash>.bin`: flujo LZ77 tipo 0x10 con fotograma de modo 4 (240×160, un índice de 8
  bits por píxel), alineado con ceros a 4 bytes, seguido de 256 colores BGR555 little-endian.
  El destino de `LZ77UnCompVram` debe estar alineado a media palabra y la fuente a 4 bytes;
  por eso se conserva ese relleno. [GBATEK, compresión BIOS](https://mgba-emu.github.io/gbatek/#bios-decompression-functions),
  [modo 4](https://mgba-emu.github.io/gbatek/#lcd-vram-bitmap-bg-modes),
  [paletas](https://mgba-emu.github.io/gbatek/#lcd-color-palettes).
- `spr/<hash>.bin`: ancho y alto visibles como `u16` little-endian, datos de tiles 8×8 a
  4 bpp comprimidos con LZ77 y alineados a 4 bytes, y 16 colores BGR555. Las filas se
  rellenan con índice 0 hasta completar el tile. [GBATEK, tiles de caracteres](https://mgba-emu.github.io/gbatek/#lcd-vram-character-data).
- `snd/<hash>.bin`: PCM con signo de 8 bits, mono, 8000 Hz, sin cabecera; las pistas de más
  de 10 s se limitan a 20 s y los efectos se convierten completos. La frecuencia y el corte
  siguen D19; la GBA reproduce muestras PCM mediante FIFO de sonido. [GBATEK, sonido](https://mgba-emu.github.io/gbatek/#sound).
- `text.bin`: `u32` little-endian con el número de entradas, seguido por pares de `u32`
  (offset del id, offset del texto), relativos al comienzo del archivo; el pool UTF-8 NUL
  terminado sigue a la tabla. Se incluyen los ids `translate es` y las cadenas Ren'Py
  `old`/`new`, con ids estables derivados de la ruta y el texto original.
- `manifest.json`: lista ordenada por id con ruta original, tipo, bytes y SHA-256 del
  contenido convertido. `categories` y `text_bin` informan el tamaño de los archivos
  generados; el JSON usa claves ordenadas, UTF-8 y salto final de línea.

El compresor aplica el formato BIOS LZ77 0x10: referencias de distancia 1–4096 y longitud
3–18. El descodificador valida cabecera, truncamientos y referencias que apunten antes del
inicio. Sus vectores de ida y vuelta están en `tests/test_gba_pack.py`.
