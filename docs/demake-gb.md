# Demake de GB/GBC — presupuesto de la ROM (T-703, PLAN.md D19)

Dice si Snoot Game (solo español, D16) cabe en una ROM dual GB/GBC con MBC5 de 8 MB con la
fidelidad de D19 (fondos en tiles con tramado de 4 colores, retratos en vez de sprites
completos, efectos simples y sin música original), y cuánto ocupa cada parte.

```
E:/Dev/renpy-console-project/.venv/Scripts/python.exe -m tools.demake.gb_budget --game E:/snoot/snootgame/game
```

## Resultado (medido sobre el juego real)

| Categoría | Archivos | Bytes | Parte del total | Método |
|---|---|---|---|---|
| Fondos | 322 | 1.107.422 | 42,8 % | muestra de 20, media ≈ 3,4 KB por fondo (tiles únicos + mapa + atributos + paleta), extrapolada |
| Retratos | 265 | 146.280 | 5,7 % | muestra de 20, media ≈ 552 B por busto de 48×48, extrapolada |
| Glifos | 256 | 4.096 | 0,2 % | tabla de 256 glifos de 8×8 a 2 bpp (123 caracteres distintos en `tl/es`) |
| Efectos | 186 | 2.976 | 0,1 % | estimado: zumbidos de onda cuadrada generados por registros, 16 B por efecto |
| Texto | 46 | 1.326.422 | 51,3 % | 3.329.911 caracteres a 1 byte por glifo, comprimidos con LZ77 propio |
| **Total** | | **2.587.196** | **30,8 %** | de 8.388.608 bytes (8 MB, MBC5) |

**Veredicto: CABE.** Sobran **5.801.412 bytes (5,5 MB)** para el motor VNB, los menús, los
datos de guardado y música tracker propia. Los PNG convertidos de muestra quedan en
`build/demake/gb/` (3 fondos a 480×432 y 2 retratos a 144×144, escalados ×3).

## Hardware (Pan Docs, gbdev.io/pandocs)

- Pantalla de 160×144: "an area of 160x144 pixels of this picture can be displayed on the
  LCD screen" (Tile Maps). Un fondo completo son 20×18 = 360 tiles de 8×8.
- Tiles: "Tile data is stored in VRAM in the memory area at $8000-$97FF; with each tile
  taking 16 bytes, this area defines data for 384 tiles" (Tile Data); cada tile es de 8×8
  a 2 bits, con el pixel izquierdo en el bit 7 y el primer byte de cada fila en el bit 0
  del color.
- Mapa de fondo: 32×32 tiles (256×256 px); un mapa indexa 256 tiles sin signo con
  direccionamiento $8000 (Tile Data).
- GBC: el mapa de atributos vive en el banco 1 de VRAM y su bit 3 elige el banco de
  tiles (Tile Maps), lo que deja los 384 tiles de la VRAM al alcance del fondo; 8 paletas
  de fondo de 4 colores RGB555 (FF68/FF69, Palettes).
- MBC5: ROM de hasta 8 MB (MBC5).

## Método por categoría

- **Fondos**: todo lo de `images/` que no sea pose de personaje (misma clasificación que
  el presupuesto de GBA). Cada imagen se recorta centrada al aspecto 10:9 de la pantalla
  (de un 16:9 queda la franja central), se escala a 160×144 y se cuantiza la luminancia a
  4 tonos con tramado ordenado Bayer 4×4 (D19). Se parte en tiles de 8×8, se deduplican y
  se mide tiles×16 + 360 bytes de mapa + 360 bytes de mapa de atributos de GBC + 64 bytes
  de paletas. Muestra determinista de 20 espaciada uniformemente (la misma que la de
  GBA), media extrapolada al total.
- **Retratos** (D19: retratos en vez de sprites completos): un busto de 48×48 por cada
  pose distinta de personaje (265 archivos en las carpetas `anon`, `fang`, …, `trishfam`).
  Cada sprite se recorta al rectángulo opaco, se toma el cuadrado superior centrado del
  lado mínimo y se trama igual que los fondos: 36 tiles de 8×8 a 2 bits, mapa de 36 bytes
  y paleta. Muestra de 20, media extrapolada.
- **Glifos**: tabla de 256 glifos de 8×8 a 2 bits = 4.096 bytes. Los 46 `.rpy` de
  `tl/es` usan 123 caracteres distintos; el español (á é í ó ú ñ ü ¡ ¿ …) entra de sobra.
- **Efectos** (D19: efectos simples y sin música original): cada uno de los 186 audios se
  sustituye por un zumbido de onda cuadrada; sin muestras, se estiman 16 bytes de pares
  tono/duración por efecto.
- **Texto**: los `.rpy` de `tl/es` (3.358.817 bytes UTF-8 = 3.329.911 caracteres) a
  1 byte por glifo, comprimidos con un LZ77 de software propio (la GB no trae
  descompresión por hardware): cabecera de tamaño en 32 bits little-endian y bloques de
  flags con literales y pares (longitud-3, desplazamiento-1) sobre ventana de 4096, el
  mismo bitstream que el LZ77 de la BIOS de GBA pero con cabecera propia. Es una cota
  superior: el VNB solo llevaría las cadenas traducidas.

## Tiles por fondo: el límite real es 256, no 384

Un fondo de 160×144 usa como mucho 360 tiles distintos, por debajo de los 384 que caben
en la VRAM (Pan Docs, Tile Data): **ningún fondo pasa de 384** (0 de 20 en la muestra, e
imposible por construcción). El límite que sí se pisa es el del mapa: **9 de los 20
fondos de la muestra superan los 256 tiles únicos** que un mapa de fondo indexa en DMG
(Pan Docs, Tile Data), por ejemplo `images/backgrounds/aquarium.webp` o
`images/cgs/wounds1.webp`. En GBC esos fondos funcionan igual (el atributo elige el banco
1 de VRAM), pero en DMG hay que reconvertirlos. Qué se hace, por orden:

1. **Más tramado**: bajar de 4 tonos a 3 en esos fondos reduce los tiles únicos (los
   bloques de Bayer uniformizan el patrón y colapsan tiles).
2. **Recorte**: menos detalle en la conversión (menos niveles de detalle en la
   reducción) también reduce tiles únicos.
3. **Solo GBC**: dejar los fondos complejos con atributos y aceptar que la ROM dual
   muestre en DMG una variante más simple de esos fondos.

## Qué recortar si no cupiese (con números)

No hace falta hoy, pero por orden de ahorro:

1. **Texto como cadenas en vez de `.rpy` completos**: los literales de cadena de
   `tl/es` son 1.638.018 bytes UTF-8 (medidos extrayendo los literales con una
   expresión regular); a 1 byte por glifo comprimidos con el mismo LZ77 son 869.873
   bytes, 456.549 menos que la cota superior actual.
2. **Fondos con tiles compartidos entre fondos**: deduplicar también entre fondos (una
   tileoteca global) en vez de por fondo; ahorro real solo medible convirtiendo de
   verdad.
3. **Bajar a 3 tonos** reduce los tiles únicos y por tanto los bytes de fondo.

## Supuestos y exclusiones

- Las imágenes con texto traducido (`tl/es/images`) sustituyen a las originales vía
  `source_file` de assetpipe; no se cuentan dos veces.
- Los fondos guardan siempre su mapa de atributos de GBC (360 bytes) porque los que
  pasan de 256 tiles lo necesitan; en DMG esos bytes sobran.
- La música original no se incluye (D19); si se quisiera música tracker propia
  (hUGETracker, ver `docs/platform-matrix.md`), cada pista ocupa unos pocos KB, y sobran
  5,5 MB.
- El LZ77 del texto es un formato propio de software: la ROM lo descomprime con código
  del motor, no hay que citarlo como hardware.

## Empaquetado binario (T-704)

`python -m tools.demake.gb_pack --game <game> --out <directorio>` escribe:

- `bg/<sha16>.bin`: cabecera y flujo LZ77 tipo 0x10 de los tiles 2bpp únicos, mapa de
  20×18 índices, mapa de atributos de 20×18 bytes y ocho paletas de cuatro colores.
  Los índices 0–255 usan el banco 0; los 256–383 se guardan módulo 256 y el atributo
  selecciona el banco 1 (bit 3). La paleta elegida es la 0.
- `face/<sha16>.bin`: tiles 2bpp únicos del busto de 48×48 comprimidos con el mismo LZ77,
  mapa de 6×6 índices, atributos del banco 0 y las ocho paletas.
- `font.bin`: exactamente 256 glifos de 8×8 a 2bpp (16 bytes cada uno). El ID de cada
  glifo es el orden Unicode ascendente que comparte `gb_budget.glyph_table`; los no
  usados quedan en blanco. Los glifos se rasterizan desde la primera fuente del juego
  en orden de ruta, a 8 px.
- `text.bin`: cantidad u16 little-endian; por entrada, dos offsets u32 little-endian
  (ID UTF-8 NUL y texto como índices de glifo NUL), seguidos del pool. Las entradas
  siguen el orden por ID de traducción.
- `manifest.json`: IDs y rutas originales, tipo, archivo de salida, tamaño y SHA-256;
  además total binario y bytes libres contra 8 MiB. El manifiesto se serializa en JSON
  ordenado y UTF-8 para que la misma fuente dé el mismo hash.

Los campos gráficos siguen [Tile Data](https://gbdev.io/pandocs/Tile_Data.html),
[Tile Maps](https://gbdev.io/pandocs/Tile_Maps.html) y
[Palettes](https://gbdev.io/pandocs/Palettes.html) de Pan Docs; el límite del cartucho
usa [MBC5](https://gbdev.io/pandocs/MBC5.html). Una pantalla de 160×144 contiene 360
celdas, por lo que una imagen no puede producir más de 360 tiles únicos. El empaquetador
registra el conteo de imágenes que excedan los 384 tiles de VRAM; el layout deja el error
explícito si en el futuro cambia la resolución o el cuantizador y se supera ese límite.

El empaquetador guarda únicamente texto extraído por ID de traducción; el presupuesto
T-703 cuenta los `.rpy` completos como cota superior. También mide tiles sin comprimir,
mientras el paquete guarda el flujo comprimido. Por eso ambos totales son medidas
distintas y el resultado empaquetado debe compararse con el límite físico de 8 MiB.

Corrida sobre `E:/snoot/snootgame/game`: el paquete ocupa **1.877.453 bytes**. El
presupuesto T-703 estima 2.587.196 bytes, diferencia de −27,4% (texto: 697.403 frente a
1.326.422 bytes; fondos: 1.039.085 frente a 1.107.422; retratos: 136.869 frente a
146.280; glifos: 4.096 en ambos; no se emiten efectos originales). No se cumple el
margen de ±5% solicitado para comparar esos totales: las dos mediciones tienen distinta
compresión y cobertura. La ROM sí queda bajo el límite de 8.388.608 bytes.
