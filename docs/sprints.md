# Sprints por plataforma (PLAN.md D26)

Una consola a la vez, con varios agentes a la vez sobre ella, hasta dejarla terminada. Así no se pisan los emuladores
(cada uno usa la GPU, puertos y carpetas propias) y cada consola queda pulida antes de pasar a la siguiente.

## Equipo por sprint

| Rol | Qué hace | Usa el emulador |
|---|---|---|
| Rutas | Las 14 rutas en `renpy` y `renpy_full` en el emulador; arregla lo que sea del port | Sí (el único) |
| Fidelidad | Diferencias de `renpy_full` de esa consola (fondo, personajes, música) contra PC y Ren'Py | No (trazas) |
| Fluidez | Cuadros por segundo, eventos por segundo en rutas largas, memoria viva (D25) | Solo cuando Rutas no lo usa |
| Escenas y controles | Chat del teléfono, teclado del anuario, botones y táctil de esa consola | Solo cuando Rutas no lo usa |
| Imagen | Capturas del título, un diálogo con fondo, el chat y el teclado, medidas contra PC | Solo cuando Rutas no lo usa |

El líder (Claude) escribe las tareas del sprint, coordina el turno del emulador, revisa a ojo cada captura y fusiona.

## "Terminado" de una consola
- [ ] Las 14 rutas en PASS con `renpy` (texto) y con `renpy_full` (fondo, personajes y música por línea), o cada
      diferencia que quede explicada en `docs/fidelidad.md` como decisión del demake.
- [ ] Ritmo: las rutas largas a la velocidad normal de la consola (sin cuadros de más de 100 ms salvo cargas).
- [ ] Memoria: solo lo que está en pantalla y la precarga (D25), medido en una ruta larga.
- [ ] Chat del teléfono y teclado del anuario jugables con los controles de esa consola (y táctil si tiene).
- [ ] Capturas de título, diálogo, chat y teclado revisadas a ojo y medidas contra PC.
- [ ] Audio: música y efectos suenan donde suenan en Ren'Py.
- [ ] `docs/platforms/<consola>.md` al día; build reproducible con su `build.py`.

## Orden
PSP → Vita → 3DS → Wii → PS4 → PS2 → DS → GBA → PS3. Xbox clásica y Switch cuando lleguen los archivos del usuario;
GB/GBC después de su motor; Xbox One/Series al final. Se pueden llevar dos sprints a la vez si sus emuladores son
distintos (por ejemplo PSP y Wii).

## Registro

| Consola | Inicio | Fin | Notas |
|---|---|---|---|
| — | — | — | — |
