# Compilador compartido (avance de Fase D)

Cronologias del kit: `temporal.animation_from_timeline` y `transition_from_spec` producen
ANIM/transiciones resueltas; uso, tolerancias y limitaciones en `../docs/temporal-kit.md`.
Nodos `ps1_transition` y `ps1_camera` emiten los opcodes existentes con rangos validados.

`compile_program(guion, roots)` en `programa.py` devuelve los paquetes VNB1, variables,
hablantes y destinos enlazados. `Program.write(Path(...))` escribe Cxx.VNB y Txx.TXT.
Cada capitulo se compara con los limites de `core/vn_limits.h` (los mismos del motor); si no cabe,
falla con el capitulo, su tamano y el limite.

El argumento opcional `text_layout=TextLayout(font_bytes)` de `vncompiler.layout` prepara
dialogos con renglones/paginas y opciones con renglones, usando metricas del FONT.BIN del disco.
Sin este argumento conserva la compilacion anterior. `ps1_special` emite SPECIAL con id u8;
el perfil del juego registra el modulo correspondiente.
No contiene rutas de Wani, reglas de finales ni extracción de recursos.
Para recursos previamente resueltos admite `ps1_scene`, `ps1_show` y `ps1_hide`;
emite SCENE/SHOW/HIDE del formato existente. No resuelve nombres, transforms ni ATL de Ren'Py.
Los nodos resueltos aceptan `keyframes`/`loop`: el compilador valida y deduplica ANIM
(posición 8.8, zoom 1/64, alfa y color) sin modificar el formato VNB1 ni el motor C.

El adaptador de cada port selecciona las entradas, construye GAME.BIN y transforma sus
mecánicas específicas. Wani importa este paquete desde el repositorio hermano del motor.

Se reutilizan los operadores del motor: CALL, RETURN y LOAD_CHAPTER para cambiar de paquete,
con variables enteras de 16 bits y un máximo de 64 slots compartidos. Los parámetros simples
usan slots por etiqueta; no se admite todavía recursión con parámetros ni tipos Python completos.

`simulate({indice: bytes_vnb}, start=..., choices=...)` en `simulador.py` devuelve una traza
determinista de diálogos, menús y estado final. Es un simulador del flujo entero del subconjunto
compilado, no un simulador visual ni una prueba de cobertura completa del juego.

La compilación es parcial: imágenes/audio y Python/pantallas quedan reportados.
Las condiciones y asignaciones no soportadas emiten HALT para detener el camino incorrecto.

Pruebas: `python -m pytest`. Los casos de `tests/compiler` compilan `core/vm.c` con GCC
nativo y comparan las trazas; no necesitan ejecutar un emulador ni modificar juegos originales.
