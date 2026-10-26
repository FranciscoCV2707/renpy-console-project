# Reproductor de STR (video visible en el PS1)

Reproduce el clip de Wani (`anim_tragedy1`, 320x176, 15 cuadros/s, 6 s, en bucle) en PCSX-Redux. Es un
programa de prueba, no el motor: el video todavía no está integrado en el juego.

Pasos (desde la raíz del repo; el `video.str` se genera como en `tests/str/README.md`):

1. Compilar: `cmake -S tests/str/player -B build/str/player/cmake -G Ninja -DCMAKE_TOOLCHAIN_FILE=$PSN00BSDK_LIBS/cmake/sdk.cmake -DPSN00BSDK_TC= -DPSN00BSDK_TARGET=mipsel-none-elf -DCMAKE_BUILD_TYPE=Release` y luego `cmake --build build/str/player/cmake`.
2. Armar el disco en `build/str/player/disc`: copiar `build/str/player/cmake/player.exe` como `PLAYER.EXE`, `video.str` como `VIDEO.STR`, y `player.xml`, `SYSTEM.CNF` de esta carpeta. Luego `mkpsxiso -y -o player.bin -c player.cue player.xml`.
3. Correr en PCSX-Redux con `player.lua` (ajusta la dirección de `player_out` según `nm`).

Cómo funciona: lee bloques de 40 sectores del CD (cada uno con `CdlSetloc`), alimenta el demultiplexor (`core/str.c`) de a un sector, decodifica cada cuadro con la VLC y el MDEC en franjas de 16 columnas, y espera a cada franja antes de subirla a VRAM. Requiere `DMACallback(1, ...)` para que las esperas del MDEC funcionen.

Resultado (2026-10-13, 30 s de emulación): 184 cuadros mostrados (unos 6 por segundo), sin errores. Las capturas muestran la escena en color y con la proporción correcta.

Límite medido: el CD. Con bloques de 10 o 40 sectores la lectura da unos 60 sectores por segundo; cada cuadro son 10 sectores, así que la velocidad es la del CD. La decodificación (VLC y MDEC) tarda unos 35 ms por cuadro. Próximo paso para acercarse a 15 cuadros/s: lectura en streaming (`CdlReadS`) sin reposicionar en cada bloque, y solapar la lectura con la VLC.
