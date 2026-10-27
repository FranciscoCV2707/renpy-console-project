# Empaquetado del demake de Nintendo DS

El comando empaqueta los recursos de Snoot en español para copiarlos a NitroFS:

```powershell
E:/Dev/renpy-console-project/.venv/Scripts/python.exe -m tools.demake.ds_pack `
  --game E:/snoot/snootgame/game --out build/demake/ds/nitrofs
```

El inventario y la resolución de imágenes con texto traducido reutilizan `tools.assetpipe.manifest`.
Se procesan imágenes de `images/`, audio de los directorios conocidos y texto de `tl/es`; video y fuentes
se omiten según D19. La salida incluye un `manifest.json` ordenado y reproducible, categorías con bytes,
total, límite de ROM de 512 MiB y los cinco recursos mayores.

## Formatos

- **Fondos:** imagen LANCZOS a 256×192; cada píxel se guarda como palabra little-endian
  `1BBBBBGGGGGRRRRR` (BGR555 con bit 15 opaco), y el flujo de píxeles se comprime con LZ77 tipo `0x10`.
  La disposición de color y el bit de opacidad siguen GBATEK, *LCD VRAM Bitmap BG Modes*, modo bitmap
  de 16 bits para NDS. [GBATEK](https://mgba-emu.github.io/gbatek/#lcd-vram-bitmap-bg-modes)
- **Sprites:** los directorios de personajes se reducen a la mitad en cada dimensión, se convierten a
  índices de 8 bits (índice 0 transparente) y se almacenan como tiles de 8×8 en orden por filas; los tiles
  se comprimen con LZ77 `0x10`. Cada archivo lleva ancho y alto de 16 bits, datos comprimidos y paleta de
  256 entradas BGR555 little-endian. GBATEK describe los tiles OBJ de 8×8 y la profundidad de color de
  256 colores en *NDS OBJ*. [GBATEK](https://mgba-emu.github.io/gbatek/#nds-obj)
- **Audio:** ffmpeg convierte a PCM signed 16-bit, 22050 Hz y mono; `tools.demake.ima_adpcm` genera
  nibbles IMA-ADPCM en orden bajo y alto, precedidos por predictor signed 16-bit little-endian, índice
  inicial y byte reservado. El flujo se alinea a 4 bytes. El manifiesto conserva la cantidad original de
  muestras para configurar la longitud del canal. GBATEK documenta el formato IMA-ADPCM del canal DS,
  el header de 32 bits y el conteo en palabras en *DS Sound Channels 0..15*.
  [GBATEK](https://mgba-emu.github.io/gbatek/#ds-sound-channels-015)
- **Texto:** `text.bin` contiene la tabla little-endian de offsets a cada id de traducción y su texto UTF-8
  terminado en NUL, igual que el empaquetador de GBA.

LZ77 `0x10` reutiliza `tools.demake.lz77.bios_lz77`; su compresor y descompresor se mantienen en un único
módulo común.
