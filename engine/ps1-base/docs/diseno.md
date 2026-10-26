# Diseño de la Fase B: separar lo general de lo de Snoot

Estado: **propuesta, espera aprobación** antes de cambiar código.

## 1. Lo que hay hoy (motor de snoot-ps1, `ae2f4f0`)
| Archivo | Líneas | Qué es |
|---|---|---|
| `vm.c`, `audio.c`, `cd.c`, `res.c`, `img.c`, `video.c`, `video_clip.c`, `text.c`, `save.c`, `input.c`, `lz4.c`, `scene.c` | ~3 700 | Núcleo. Ya es general: no nombra nada de Snoot |
| `main.c` | 2 392 | Todo lo demás: bucle principal, escena y transiciones, caja de texto, menús, título, pausa, ranuras, opciones, galería, extras, teclado, chat por tiras, créditos, menú de desarrollo, prueba automática |

Buena parte de lo de Snoot **ya viene de datos** (`DATA\GAME.BIN`): hablantes, posiciones, galería,
nombres de capítulos, capítulos extra, tiras del chat y texto de los créditos. Lo que sigue fijo en
el código:

| Fijo en el código | Dónde | Cómo queda |
|---|---|---|
| Regla de desbloqueo de los extras (Snoot D1: según finales vistos, series de Trish y Naomi, x10) | `extra_unlocked()` | función del juego (sección 3) |
| Exactamente 4 finales y sus 4 imágenes | `ending_image[4]`, `endings_mask & 15` | N finales (hasta 32) leídos de `GAME.BIN` |
| Textos de la interfaz en español ("Comenzar", "Guardar", errores de la memory card...) | `title_items`, `pause_items`, `card_error()`, etc. | tabla de textos en `GAME.BIN`, con estos mismos como valor por defecto |
| Entradas del menú de título (Comenzar, Continuar, Extras, Galería, Opciones) | `update_title()` | lista de entradas en `GAME.BIN`; cada una es una acción del motor |
| Pantallas especiales 1 = chat por tiras, 2 = créditos, 3 = teclado | `begin_special()` | módulos generales (sección 4) |
| Nombre del ejecutable, del proyecto y del archivo de la memory card | CMake, `save.c` | por juego (sección 5) |

## 2. Estructura propuesta
```
vn-engine-ps1/
  core/      núcleo (los ~3 700 líneas de hoy, sin cambios de comportamiento)
  ui/        título, pausa, ranuras, opciones, galería, extras, avisos, menú de desarrollo
  modules/   pantallas especiales: tiras (chat), créditos, teclado; más adelante video STR,
             chat de teléfono, lienzo, elección con imágenes
  app/       bucle principal, escena, transiciones, caja de texto, menús de decisión
  games/
    snoot/   game.c: la regla de extras de Snoot; game.cmake: nombre, módulos, archivo de la card
    wani/    (Fase C)
  tools/     compilador guion.json -> VNB y simulador del bytecode (Fase D)
  tests/     pruebas en emulador y de las herramientas
```
`main.c` se parte en `app/` y `ui/` sin cambiar lo que hace; cada paso compila y se prueba.

## 3. Lo propio de cada juego: datos primero, código solo si hace falta
1. **Datos en `GAME.BIN`** (lo que se pueda describir): cantidad de finales y sus imágenes, textos
   de la interfaz, entradas del título, galería, capítulos, extras, ranuras.
   - Se agrega una sección nueva al final (`PRF1`). Si no está, se usan los valores de Snoot: el
     `GAME.BIN` de snoot-ps1 v1.0 sigue funcionando sin cambios.
2. **Funciones del juego** (`games/<juego>/game.c`) solo para reglas que no son datos simples. Hoy
   es una sola: `game_extra_unlocked(i, progreso)` de Snoot. Cada juego trae su `game.c`; uno que no
   necesite reglas propias usa el de por defecto (todo desbloqueado al verlo).

## 4. Pantallas especiales como módulos
- La instrucción `SPECIAL id` sigue igual. Cada módulo se registra con su id y sus funciones
  `begin`, `update` y `draw`.
- Los de Snoot pasan a ser generales: **tiras** (cualquier pantalla de imágenes que se desplazan,
  no solo el chat del capítulo 4), **créditos** (texto con estilos, de `GAME.BIN`) y **teclado**
  (entrada de texto).
- Cada juego elige en su `game.cmake` qué módulos lleva, así no ocupan memoria en juegos que no
  los usan.

## 5. Un ejecutable por juego
- `cmake --preset snoot` y `cmake --preset wani` (o `-DGAME=...`) arman `snoot.exe` o `wani.exe`
  con el núcleo, la interfaz, los módulos elegidos y el `game.c` del juego.
- El archivo de la memory card conserva su nombre y formato por juego: una partida de Snoot v1.0 se
  carga igual con el motor nuevo.

## 6. Cómo se comprueba que Snoot no cambia
- **Paso 0 (antes de tocar nada):** con el sistema de pruebas de snoot-ps1 (`tools/engine/emutest.py`,
  PCSX-Redux sin ventana, guiones de botones y capturas), se graban capturas de referencia del disco
  de snoot-ps1 v1.0: título, menús, guardar y cargar, extras, galería, el chat del capítulo 4, el
  teclado del 13D, créditos y una partida automática (`autoplay`). Las herramientas y los datos de
  snoot-ps1 se leen; nada se escribe allá.
- **En cada paso:** se arma un disco de prueba de Snoot con el motor compartido y los datos de
  snoot-ps1 (`build/data`, solo lectura), se corren los mismos guiones y las capturas deben salir
  **idénticas píxel a píxel**. La partida automática debe terminar igual.
- Estas pruebas quedan en `tests/` de este repo y se corren en cada cambio futuro del motor.

## 7. Orden de trabajo
1. Pruebas de referencia de Snoot (sección 6).
2. Mover archivos a `core/`, `ui/`, `modules/`, `app/` (solo mover; el ejecutable puede seguir
   saliendo idéntico).
3. Sacar la regla de extras a `games/snoot/game.c`.
4. N finales y textos de la interfaz desde `GAME.BIN` (sección `PRF1` opcional).
5. Pantallas especiales como módulos registrados.
6. Presets de CMake por juego.
Después de cada paso: compilar, correr las pruebas de la sección 6 y hacer commit.

## 8. Fuera de esta fase
- Todo lo nuevo de Wani (video STR, chat de teléfono, lienzo, cámara, texto animado): Fase C.
- Bytecode v2 y compilador desde `guion.json`: Fase D.
- Cambiar snoot-ps1: Fase E, solo si se pide.
