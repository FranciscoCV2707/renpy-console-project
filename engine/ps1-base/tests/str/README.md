# Prueba del video STR (MDEC + XA)

Prueba aislada, antes de integrarlo al motor: el ejemplo oficial `strvideo` de PSn00bSDK (`main.c` y
`system.cnf`, MPL-2.0, sin cambios) reproduce un `VIDEO.STR` generado con `psxavenc`.

Pasos (PowerShell, en la raíz del repo):

1. Generar el video de prueba (5 s, 15 cuadros/s, 320x176, audio XA 37800 Hz):
   `ffmpeg -f lavfi -i testsrc2=size=320x176:rate=15 -f lavfi -i sine=frequency=440:sample_rate=37800 -t 5 -shortest -c:v libx264 -pix_fmt yuv420p -c:a pcm_s16le in.mkv`
   `psxavenc -t str -f 37800 -c 2 -b 4 -s 320x176 -r 15 -x 2 in.mkv video.str`
2. Compilar el ejemplo: `cmake -S tests/str -B build/str/cmake -G Ninja -DCMAKE_TOOLCHAIN_FILE=$PSN00BSDK_LIBS/cmake/sdk.cmake -DPSN00BSDK_TC= -DPSN00BSDK_TARGET=mipsel-none-elf -DCMAKE_BUILD_TYPE=Release` y luego `cmake --build build/str/cmake`.
3. Armar el disco en `build/str/disc` con `strvideo.xml`, `system.cnf`, `strvideo.exe` y `video.str`, y ejecutar `mkpsxiso -y -o strvideo.bin -c strvideo.cue strvideo.xml`.
4. Correr en PCSX-Redux con `emutest.lua` (capturas en `build/str/shots`, cada 600 cuadros de 60 Hz).

Resultado de la prueba (2026-10-13): el video se reproduce con el contador de tiempo avanzando (2.867 s en el
cuadro 600, 4.467 s en el 1200), 0 errores de lectura y 0 de decodificación. El audio no se verifica con capturas.

## Demultiplexor (en el PC, sin emulador)

`core/str.c` reensambla los cuadros de un `.str` a partir de sus sectores (cabecera de 32 bytes, 2016 de
bitstream). `tests/str/test_demux.c` lo prueba con el `video.str` generado arriba:

   `gcc -std=c99 -Wall -Wextra -Werror -pedantic -I core -o build/str/test_demux.exe tests/str/test_demux.c core/str.c`
   `build/str/test_demux.exe build/str/video.str`

Resultado (2026-10-13): 710 sectores, 621 de video (el resto es audio), 71 cuadros completos, 0 perdidos, 0
huecos. El compilador de la prueba es el de UCRT64 (`/c/msys64/ucrt64/bin/gcc.exe`); el de `/usr/bin` no trae
cabeceras.

## Bug del ejemplo con cuadros más angostos que 320 (2026-10-13)

El ejemplo oficial deja de decodificar cuando el cuadro es más angosto que la pantalla (256x144, 160x96,
128x80). El cuadro se centra con `x_offset`, pero el límite de las porciones (`frame_width`) no suma ese
desplazamiento: se piden menos porciones de las que el MDEC necesita, el MDEC queda ocupado para siempre y
los sectores del CD se acumulan pendientes. A 320 el desplazamiento es 0, así que funciona.

Corrección de una línea (en `main.c`, dentro de `get_next_frame()`/`start_stream` del ejemplo):

    str_ctx.frame_width = str_ctx.slice_pos.x + VRAM_X_COORD(frame->width);

Con ella, 256x144 y 160x96 decodifican los 87 cuadros con 0 errores. El ejemplo original no se modifica en
`tests/str`; la corrección se aplica en la copia de depuración.
