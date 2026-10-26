# Bitácora

## 2026-10-24 - Giro de sprites en las claves ANIM (PAKO-17)
- Formato aprobado: bit 7 de los flags de ANIM; con el bit, bytes 9-10 de cada clave = angulo `s16` en 1/4096 de
  vuelta, horario, pivote en el centro de la imagen. Sin el bit los bytes se ignoran (Snoot escribe ahi un giro
  que su v1.0 nunca dibujo). El compilador solo pone el bit si algun angulo no es 0. Detalle en docs/bytecode.md.
- Compilador: `temporal.rotated_center` lleva `rotate` de Ren'Py (transform_anchor, rotate_pad) al centro de la
  imagen; la tolerancia de claves suma el giro en pixeles. Motor: `scene_look` interpola el angulo, la captura de
  `VM_SHOW_FROM_CURRENT` lo incluye y `img_draw_ex_rot` gira las esquinas de cada POLY_FT4 con `isin`/`icos`.
- Comprobado: los capitulos de Wani sin giro salen identicos byte a byte (solo C00 cambia: +1 ANIM girada y +1 del
  bloque que ahora sigue). Wani capitulo 1: 236 -> 239 dialogos con movimiento real; capitulo 2 sigue en 399.
- El bloque del gimnasio ya pasa `rotate_funny`; ahora lo corta la `camera` durante la salida animada de Solly
  (wani `characters_motion.py`, "camara durante una salida animada"). Ese es el siguiente cuello.
- Pendiente: ver el giro en DuckStation (PCSX-Redux sin ventana no dio cuadros en esta sesion).

## 2026-10-24 - Capitulos grandes en el heap (PAKO-14)
- Problema: con escenas, los capitulos 6, 7, 18A y 18D de Wani (~54-57 KB de VNB) no cabian en `chapter_buf`
  (48 KiB) y el disco solo fallaba al cargarlos en la consola.
- Arreglo: `core/chapter.c` reserva VNB + texto en un bloque del heap a su tamano real (NULL revisado) y lo libera
  en cada carga; limites unicos en `core/vn_limits.h` (96 KiB cada uno), que el compilador lee para fallar con
  capitulo, tamano y limite. Heap libre al arrancar en wani: 385.936 -> 516.168 bytes. Sin cambio de VNB1.
- Eleccion y cuentas: docs/presupuesto-memoria.md. Pendiente: cargar un capitulo grande en emulador.

## 2026-10-23 - ANIM con cambios de imagen, color, espejo e introduccion
- El compilador escribe los eventos de imagen de 7 bytes que `scene_look` ya leia (antes siempre 0 eventos).
- Matrices de color multiplicables a r/g/b de las claves; `xzoom -1` constante a flip; cualquier propiedad no
  dibujable falla con su nombre en vez de perderse.
- Clave de inicio de bucle en los bits 1-6 de los flags de ANIM (`core/scene.c`); 0 conserva el comportamiento
  anterior. Probado con scene.c nativo; el perfil wani compila. Falta verlo en emulador.
- Motor acepta 4237 -> 4577 de 5224 eventos de Wani (renpy-port-kit docs/lectura-movimientos.md).

## 2026-10-22 - SHOW desde el aspecto actual (PAKO-6)
- Problema: tras un SAY, un `show x at t` nuevo se horneaba desde el estado asentado del movimiento anterior;
  con lectura rapida el sprite saltaba a ese punto antes de animar.
- Arreglo: flag SHOW 0x08. `scene_show` pide a `VmHost.capture` el aspecto actual antes de reiniciar;
  `scene_look` lo usa como clave 0 hasta la clave 1 del primer pase. Sin cambio de registro ni de guardado.
- Pendiente: lectura rapida y guardar/cargar a mitad de movimiento en emulador.

## 2026-10-18 - Audio de historia de Wani
- ps1_audio valida y emite los opcodes de audio existentes (0x20..0x27); sin cambio VNB/AIX1.
- VOLUME sin fundido es inmediato. SFX_STOP aplica el tiempo de fundido y apaga voces al llegar a cero; VOLUME afecta voces SPU activas.
- 70 pruebas del compilador pasan, incluidas dos pruebas C de las rutinas de volumen/fundido. Perfil wani compilado.
- Consumidor Wani: build/jugar-audio, 95 sentencias de audio de capitulos 1 y 2. Recorrido/escucha en emulador pendientes; continuidad temporal/guardado no resuelta.
- Sin commits ni ramas; preservar cambios locales.

## 2026-10-18 - Capitulo 2 de Wani
- Wani integra el capitulo 2 con ANIM/TRANSITION existentes e ids globales de imagen. Sin cambios al nucleo C ni al formato de bytecode en este incremento. Perfil wani compilado; 58 pruebas del compilador pasan. Cuatro secuencias de flujo grafico de Wani coinciden con core/vm.c nativo. PCSX-Redux sin cuadros en este entorno: validacion visual pendiente.
- Preview y limites: E:/Dev/wani-ps1/docs/capitulo2.md. Sin commits/ramas; preservar cambios locales.

## Cierre de sesion 2026-10-17
- Punto consolidado en E:/Dev/wani-ps1/docs/retomar-sesion.md; motor 55 pruebas pasan.
- Contrato actual rechaza clock_offset/cycle_tracks no representables. Consumo destino y continuidad/guardado pendientes.
- Cierre solo documental; sin repetir pruebas, cambiar C/VNB1, hacer commits o ramas.

## 2026-10-17 - Primer pase distinto del ciclo estable
- El kit agrega cycle_initial/cycle_tracks para ciclos que heredan el final de la vuelta previa.
- ANIM actual no conserva esos dos recorridos: rechazo explicito y prueba de regresion; 55 pruebas pasan.
- Pendiente disenar ejecucion de introduccion/primer pase/ciclo sin cortar el flujo del dialogo.
  No quitar el rechazo sin implementar el consumidor. Sin cambios a C ni VNB1.

## 2026-10-17 - Rechazo explicito de fase heredada no representable
- El kit permite after(t) ciclico con clock_offset; ANIM actual no tiene ese contrato.
- animation_from_timeline rechaza offsets no nulos; prueba de regresion, 54 pruebas pasan.
- Sin cambios a nucleo C o VNB1. No presentar continuidad durante lectura o guardado como implementada.

## 2026-10-16 - Uso de cronologias en conversion por lotes
- Documentado consumidor Wani con prefijos transaccionales y fallback explicito.
- El kit conserva fase no lineal antes del muestreo ANIM; no cambia el formato ni el motor C.
- Pendientes compartidos: alfa gradual de bitmaps, disolvencias no lineales/multicapa y bucles con introduccion.

## 2026-10-16 - Herencia de cronologia al cambiar expresiones
- El consumidor Wani conserva claves activas en cambios de expresion inmediatos; el salto de Ben ya no se corta.
- El kit proporciona after(0)/recorte lineal con rechazo explicito de fases no lineales parciales.
- Prueba nativa scene.c incluye apice/regreso del salto. 53 pruebas del motor pasan.
- Sin cambios al formato VNB1 ni al nucleo C; limites y uso actualizados en docs/temporal-kit.md.

## 2026-10-15 - Validacion de personajes y limite del alfa en bitmaps
- Wani conecta cuatro movimientos de Ben/Inco con el adaptador temporal existente.
- scene.c nativo confirma posiciones de la entrada de Ben en 0/15/30/60 cuadros.
- Se documenta que alpha se calcula en SpriteLook pero solo se mezcla gradualmente para solidos;
  bitmaps requieren TRANSITION para un fundido visible. No se cambia el nucleo C ni VNB1 en esta ampliacion.

## 2026-10-15 - Adaptador temporal neutral del kit
- animation_from_timeline muestrea curvas/posiciones a claves ANIM existentes, con presupuesto y rechazo de estados
  no representables. transition_from_spec traduce corte/dissolve/Fade. Se emiten ps1_transition/ps1_camera validados.
- El motor no importa el kit: el port inyecta un objeto Timeline y resuelve recursos/estado/ramas.
- Wani conecta el pasillo original; pruebas contra core/scene.c en inicio, mitad y final de ambas panoramicas.
- Limites de fondos panoramicos, cuantizacion, profundidad y bucles documentados en docs/temporal-kit.md.

## 2026-10-15 - Correccion de texto y enlace de introducciones
- Nuevo TextLayout optativo: metricas exactas FNT1, ajuste por palabras, corte de palabras demasiado largas,
  paginas limitadas por altura y reapertura de estilo. Argumentos de controles no se confunden con espacios.
- Menus: renglones sin paginas ni controles que font_draw no interpreta. Compilacion anterior sin callback no cambia.
- Nodo ps1_special con id u8 validado, usa SPECIAL existente. Perfil Wani registra Inco V05 y Olivia V02.
- 44 pruebas pasan; motor Wani compilado. No hay cambio de formato de bytecode.
- Validacion PCSX-Redux separada confirma video visible y dialogo con renglones/paginas.
- Sigue pendiente traducir la puesta en escena temporal original; no se agregaron movimientos inventados.

## 2026-10-15 - Tablas ANIM compartidas y validación visual de Wani
- El compilador serializa claves y offsets de ANIM existentes; deduplica por paquete y valida campos/tiempos.
- core/scene.c nativo lee las claves generadas: comprobados inicio, mitad y estado final de posición/escala.
- PCSX-Redux completó la prueba sintética de animación de Wani y su recorrido visual lineal de 600 diálogos.
- 34 pruebas del motor pasan. No se modifica el formato VNB1 ni el código de producción en C.
- Pendiente traducir ATL general y probar guardado durante animaciones; el recorrido lineal no sustituye el port completo.

## 2026-10-15 - Compilación de instrucciones visuales resueltas
- Se agregan nodos intermedios ps1_scene/ps1_show/ps1_hide, genéricos y con campos validados.
- Emiten SCENE/SHOW/HIDE del VNB1 existente: no se modifica el formato ni el motor C.
- Suite del motor: 26 pruebas pasan. La suite de Wani sigue comparando flujo contra la VM C nativa.
- Prueba en PCSX-Redux con fondo y sprites reales de Wani: HIDE retira cada capa y SCENE limpia sprites.
- Artefactos en `E:/Dev/wani-ps1/build/validacion/imagenes`; no acredita fidelidad al encuadre original.

## 2026-10-12 - Inicio: motor de snoot-ps1 copiado
- Pedido del usuario: que el motor mejore con cada port y sirva para juegos futuros, en una
  carpeta propia.
- Se copió el motor de `snoot-ps1` en su commit `ae2f4f0` (`src/`, `include/`, CMake) y sus
  documentos de formato a `docs/snoot-ps1/`. snoot-ps1 no se modificó.
- Compila a un `snoot.exe` byte a byte idéntico al de snoot-ps1 (94 208 bytes).
- Se escribieron `CLAUDE.md`, `PLAN.md` (fases A a E) y `STATUS.md`.

Pendiente: Fase B (diseño de la separación entre núcleo, perfil del juego y módulos).

## 2026-10-12 - Licencia, compilador y diseño de la Fase B
- Decisiones del usuario: licencia MIT (`LICENSE`); el compilador `guion.json` -> VNB vive aquí.
- `docs/diseno.md`: cómo separar el núcleo, la interfaz, los módulos de pantallas especiales y lo
  propio de cada juego (datos en `GAME.BIN` primero, `games/<juego>/game.c` solo para reglas), y cómo
  comprobar que Snoot no cambia (capturas en PCSX-Redux idénticas píxel a píxel). Espera aprobación.

## 2026-10-12 - Fase B: separación hecha, Snoot igual
- **Pruebas en emulador** (`tests/emu/snoot.py`): arman discos de Snoot con un motor y los datos de
  snoot-ps1 (solo lectura; sus herramientas se importan sin dejar caché y sus carpetas de trabajo se
  redirigen a `build/emu/`), corren guiones de botones en PCSX-Redux sin ventana y comparan las
  capturas píxel a píxel con las del motor de referencia (`f770b2e`, igual a la v1.0).
  - El ejecutable se rellena a 256 KB en el disco de prueba: así los datos quedan en los mismos
    sectores aunque el motor cambie de tamaño, y los tiempos de carga no cambian.
  - Escenarios: título, menús (continuar, extras, galería, opciones), partida (líneas, pausa,
    guardar), cargar (con la memory card de la partida), teclado del 13D, chat del capítulo 4 y
    créditos. Dos corridas del mismo motor dan capturas idénticas.
  - Límite: una partida desde el menú de desarrollo no guarda el progreso, así que la regla de
    extras con finales vistos no se ejercita en emulador (se movió textual).
- **Pasos** (cada uno compilado y probado, con su commit):
  1. pruebas de referencia;
  2. `core/` y `app/`;
  3. regla de extras de Snoot en `games/snoot/game.c` (`games/default`: extras al ver un final);
  4. textos de la interfaz por juego (`games/<juego>/text.c`, `app/ui_text.h`) y hasta 8 finales;
  5. pantallas especiales como módulos (`modules/`: tiras, créditos, teclado) con banderas para el
     bucle principal y gancho de prueba automática; cada juego las asigna a ids en
     `games/<juego>/specials.c` (el orden da el estado del motor, así Snoot conserva 16-18);
  6. un ejecutable por juego (`GAME`, presets `default`/`snoot`/`generic`).
- Título, menús, partida, cargar y teclado: idénticos píxel a píxel después de cada paso.

## 2026-10-12 - Fase B confirmada en emulador
- El escenario `creditos` y el `chat` ahora recorren el juego con salto de texto (`skipping` en
  `tests/emu/snoot.py`) para llegar al capítulo 4 y a los créditos.
- PCSX-Redux no sale tras `PCSX.quit()`: el runner esperaba indefinidamente. Ahora cierra el proceso
  30 s después de que el guion escribe `final.txt`.
- `python tests\emu\snoot.py check`: los 7 escenarios idénticos a la referencia (`OK`).

Pendiente: Fase C, paso 2 (cámara). `CAMERA` (0x16) no tiene efecto en Snoot; hay que definir
`xpunch`/`ypunch` en el bytecode antes de implementarlo.

## 2026-10-12 - Fase C, paso 2: cámara (CAMERA) en el motor
- `app/main.c`: `OP_CAMERA` anima zoom y desplazamiento de toda la escena (`pantalla = zoom x punto -
  (tx, ty)`, tx/ty en 1920x1080 como en `docs/snoot-ps1/bytecode.md`). Se aplica a sprites y al fondo.
- Límites: el fondo grande (`big`) se desplaza pero no hace zoom; la cámara no se guarda en la partida
  ni se reinicia al volver al título; el compilador de Ren'Py aún no emite `CAMERA` (Fase D).
- Snoot no emite `CAMERA`: `snoot.py check` da los 7 escenarios idénticos, así que el cambio no lo altera.
- Sin prueba visual todavía: falta una escena con `CAMERA` (Wani o una escena de prueba).

## 2026-10-12 - Prueba visual de la cámara
- `tests/emu/snoot.py camara`: escena de Snoot con la cámara forzada desde el arnés (escribe `cam_*` en
  memoria en cuadros fijos y toma capturas 30 cuadros después). Muestras cada 1500 cuadros desde que el
  juego entra en `state=1`, con cámara normal, zoom 2x y zoom 0.5x con desplazamiento.
- Resultado: el zoom y el desplazamiento se ven en el fondo y en la escena; la interfaz no se mueve.
  Capturas en `build/emu/cur/camara/`.
- No es una prueba píxel a píxel (cada muestra cae en otro momento del guion). Falta comprobar que el
  teléfono también se escale en las versiones con zoom.

## 2026-10-12 - Fase C, paso 3: texto animado ({sh}, {sc})
- `core/text.h`: códigos 0x07/0x08 (`{sh}`/`{/sh}`) y 0x0E/0x0F (`{sc}`/`{/sc}`).
- `core/text.c`: `step()` los consume sin revelar carácter; `text_draw()` aplica el temblor: `{sh}` un
  desplazamiento por cuadro para todo el tramo, `{sc}` uno por letra. Amplitud de 1 px de PS1.
- Formato en `docs/bytecode.md` (v2 en curso). El compilador que los genera llega en la Fase D.
- `snoot.py check`: los 7 escenarios idénticos a la referencia (`OK`). Snoot no usa estos códigos.
- Sin prueba visual: no hay escena con temblor todavía.

## 2026-10-12 - Fase C, paso 4 (parte 1): 16 capas de sprites
- `core/video.h`: sprites en las capas 4 a 19 (un sprite por capa, 16 como `VM_MAX_SPRITES`); fondo en la 20.
  Antes había 6 capas y los sprites de la séptima en adelante se aplanaban a la misma capa.
- `snoot.py check`: los 7 escenarios idénticos a la referencia (`OK`).
- Pendiente del paso: revisar el asignador de VRAM para 12 sprites con los tamaños reales de Wani
  (presupuesto de la Fase 2 de wani-ps1). El motor ya desaloja lo que no está en la escena.

## 2026-10-12 - Corrección
- La línea "Pendiente: Fase C, paso 2 (cámara)... hay que definir `xpunch`/`ypunch`" de la entrada de la fase B
  ya no aplica: la cámara quedó en el paso 2 (ver entrada de la cámara). `xpunch`/`ypunch` siguen pendientes
  como instrucción propia.

## 2026-10-12 - Fase C, paso 6: menú de imágenes (IMGMENU) y corrección de la cámara
- `core/opcodes.h`, `core/vm.h`, `core/vm.c`: `OP_IMGMENU` (0x19) con fondo y botones (imagen, posición,
  visto, destino). Reutiliza `menu_target` y el camino de `MENU` para reanudar.
- `app/main.c`: `menu_img` cambia el dibujo y la navegación de `ST_MENU` (izquierda/arriba, derecha/abajo,
  X elige). No se agregó estado nuevo: `ST_SPECIAL` tiene que quedar al final y sus números se usan en las
  pruebas.
- Corrección: la cámara se reinicia al volver al título y al cargar una partida (`camera_reset()`).
- `snoot.py check`: 5 escenarios idénticos y 2 (chat, créditos) con capturas idénticas pero el contador de
  cuadros del final distinto (27984 contra 27985 y 51527 contra 51528). El contador ya varió entre corridas
  del mismo código (chat dio 28801 y 27985 en corridas distintas), así que es el momento del corte del
  arnés, no una regresión. No se cambió la comparación.
- Sin probar: ninguna escena de Snoot usa `IMGMENU`; falta una escena de Wani o de prueba.

## 2026-10-13 - Fase C, paso 7: chat de teléfono (OP_PHONE + módulo phone)
- `core/opcodes.h`, `core/vm.h`, `core/vm.c`: `OP_PHONE` (0x1A) deja hasta 32 mensajes (lado, texto, foto) y
  valida el id de texto. `app/main.c` los pasa al módulo con `phone_add`.
- `modules/phone.c`: burbujas a la izquierda (lado 0) y a la derecha (lado 1), fotos, recorrido con arriba/abajo
  y X para salir. `special_phone` se abre con la instrucción SPECIAL del id que asigne cada juego.
- Compila sin advertencias. Sin probar: ninguna escena de Snoot usa el chat; falta una escena de Wani.
- Regresión de Snoot: 5 escenarios idénticos. `chat` y `creditos` tienen capturas idénticas, pero el contador
  de cuadros del final es uno menor (27984 contra 27985, 51527 contra 51528). Se repite en `chat` solo, y
  también en el commit 17e3f3d (menú de imágenes, sin el teléfono), así que viene del código comprometido
  desde ese commit y no del chat nuevo. Las capturas y el estado son iguales: es un efecto de tiempo en el
  arnés, no un cambio visual. No se cambió la comparación; hace falta decidir si el arnés debe ignorar ese
  contador. Pendiente de decidir, no de código.

## 2026-10-13 - Fase C, paso 8: lienzo de dibujo y guardado en la memory card
- `modules/canvas.c`: lienzo de 128x72 con cursor de la cruceta, trazo con X, deshacer con O, grosor con L1.
  Mapa de 1 bit (1152 bytes) como fuente de verdad; deshacer guarda una copia al empezar cada trazo.
- `app/main.c`: el dibujo va al final del progreso (`OFS_CANVAS`); progress_to_buf/progress_from_buf lo guardan y
  cargan. No mueve ningún desplazamiento existente.
- Compila sin advertencias. Pendiente: que Wani lo abra en el capítulo 3 (SPECIAL) y que los créditos lo
  muestren desde el mapa de bits (hoy no hay función de dibujar el mapa en pantalla fuera del lienzo).
- Regresión de Snoot tras el lienzo: 5 escenarios idénticos; `chat` y `creditos` con capturas idénticas y el
  contador de cuadros final una unidad menor, igual que en el commit 17e3f3d (ver entrada del paso 7).

## 2026-10-13 - Fase C, paso 9 (parte 1): video STR probado aparte
- `tests/str`: el ejemplo `strvideo` de PSn00bSDK (MPL-2.0, sin cambios) con un `video.str` generado con
  `psxavenc` (5 s, 320x176, 15 cuadros/s, XA 37800 Hz).
- Resultado en PCSX-Redux: el video se reproduce (contador 2.867 s en el cuadro 600, 4.467 s en el 1200),
  0 errores de lectura y 0 de decodificación. El audio no se comprueba con capturas.
- Pendiente: integrarlo al motor. El ejemplo maneja el CD con su propio manejador de sectores; el motor ya
  tiene su lectura en segundo plano (`core/cd.c`, `core/res.c`) para las imágenes. Hay que unirlos sin
  romper a Snoot.
- Paso 9 (parte 2): `core/str.c` demultiplexa el STR en cuadros con dos buffers (uno se llena mientras el otro
  espera al consumidor; un cuadro viejo sin consumir se cuenta como perdido). Prueba en el PC con el video
  generado: 71 cuadros, 0 perdidos, 0 huecos (`tests/str/test_demux.c`).
- Pendiente de la integración: leer los sectores del CD en trozos (`core/cd.c`), alimentar el demux, decodificar
  con el MDEC y mostrar el cuadro. La lectura actual del motor es por consultas (`CdRead` + `CdReadSync`), sin
  callbacks; el ejemplo de PSn00bSDK usa callbacks. Hay que decidir cómo se comparte.
- Clip de Wani para probar: `anim_tragedy1` (1920x1080 en el original) escalado a 320x176, 15 cuadros/s, 6 s,
  generado en `build/str/wani/tragedy.str` (87 cuadros, 870 sectores de video, sin audio: la fuente no trae
  pista de audio en ese tramo).
- **Hallazgo de rendimiento:** el ejemplo oficial decodifica unos 4 cuadros por segundo en PCSX-Redux (frame
  42 en la captura a los 10 s de emulación, contador de tiempo 2.867 s). Para 15 cuadros/s hace falta unas 3.5
  veces más rápido. Es el bloqueo principal de la integración: el ejemplo tiene texto de depuración y decodifica
  sin optimizar. Antes de integrar hay que medir el MDEC solo y decidir (resolución, cuadros por segundo u
  optimización).
- **Medición del MDEC (paso 9, integración): no concluyente, y lo que sí es válido.**
  - Válido: el ejemplo oficial (`tests/str`) con el clip de Wani a 320x176 llega al cuadro 42-47 a los 10 s de
    emulación: unos 4-5 cuadros/s. Para 15 cuadros/s hacen falta unas 3 veces más.
  - No válido: un banco propio (`tests/str/bench`) que mide la VLC y el MDEC por separado. Errores que
    encontré y no terminé de resolver: (1) primero llamaba a `DecDCTinSync` antes de `DecDCTout`, con lo que
    cada espera vencía por tiempo; (2) al recompilar cambia la dirección de la variable de resultados y el
    script Lua la leía mal; (3) con el orden corregido las esperas siguen venciendo y el banco no termina.
    Queda sin usar.
  - Las resoluciones menores (256x144, 160x96, 128x80) con el ejemplo oficial se quedan en negro tras los
    primeros cuadros (`FRAME: 2`): no se reprodujeron, así que no dicen nada sobre velocidad. Falta investigar
    por qué el ejemplo no decodifica esos tamaños.
- Pendiente: decidir la resolución o la cadencia del video de Wani a partir de una medida válida. Para la
  integración hay que decodificar en segundo plano (como el ejemplo, con callbacks de DMA) y no con esperas.
- **Investigación de las resoluciones menores (opción 2):** los archivos STR son correctos (mismos 10 sectores
  por cuadro, dimensiones bien puestas). Con una copia instrumentada del ejemplo (contadores en memoria):
  - 320x176: ninguna espera vence, los 87 cuadros se decodifican.
  - 256x144: el bucle principal da una sola vuelta y se queda en `get_next_frame()`: el segundo cuadro nunca
    se completa. No es el MDEC: las esperas no vencen. Es el manejo de sectores: un sector que llega mientras el
    MDEC escribe queda pendiente y solo se procesa en `mdec_dma_handler`, y con cuadros más chicos el orden
    entre CD y DMA del MDEC se atora. Causa exacta pendiente de confirmar.
- **Opción 3 (decodificación en segundo plano con callbacks):** es la forma de resolver el punto anterior, porque
  requiere planificar los sectores y las transferencias del MDEC a la vez, no solo acelerar. Es el trabajo grande.
- **Causa de las resoluciones menores (cerrada):** el ejemplo oficial calcula el límite de las porciones del
  MDEC sin el desplazamiento del cuadro centrado. Con una línea de corrección (ver `tests/str/README.md`),
  256x144, 160x96 y 128x80 decodifican los 87 cuadros con 0 errores.
- **Velocidad (lo que cambia el plan):** con esa corrección, a los 10 s de emulación todas las resoluciones
  dan 46-48 cuadros (unos 4.7 cuadros/s), desde 320x176 hasta 128x80. Como no depende del tamaño, el cuello
  de botella no es el MDEC ni el CD (el ejemplo lee a 2x con modo de tiempo real, que sí alcanza 15 cuadros/s).
  Bajar la resolución no llega a 15 cuadros/s. Lo que limita es un costo fijo por cuadro en el bucle: el orden
  entre sectores del CD, las porciones del MDEC y la subida a VRAM. Eso es el trabajo de la opción 3
  (decodificación en segundo plano con callbacks de DMA).
- **Video visible (paso 9):** `tests/str/player` reproduce el clip de Wani en PCSX-Redux: 184 cuadros en 30 s
  (unos 6 por segundo), sin errores. Errores que encontré y corregí en el camino: (1) `CdRead` no avanza sola, hay
  que reposicionar con `CdlSetloc` en cada bloque; (2) el MDEC necesita `DMACallback(1, ...)` para que sus
  esperas funcionen; (3) la salida del MDEC va en franjas verticales de 16 columnas, no en filas; (4) el
  demultiplexor guarda un solo cuadro listo, así que hay que decodificar cada cuadro antes de alimentar el
  siguiente sector; (5) el límite del ejemplo oficial con cuadros angostos (ver `tests/str/README.md`).
- Medido: el cuello de botella es la lectura del CD (unos 60 sectores/s), no la decodificación. Próximo paso:
  lectura en streaming sin reposicionar y solapamiento con la VLC.
- Todavía no está integrado en el motor (no hay módulo de video en el juego).
- **Lectura en paralelo con la decodificación (probado, descartado):** dos buffers de CD, pidiendo el bloque
  siguiente mientras se decodifica el actual. Resultado: 92 cuadros en 30 s, la mitad de la versión con un
  buffer (184). La causa es el conflicto de DMA que describe el ejemplo oficial: la lectura del CD y la salida del
  MDEC no pueden correr a la vez, así que se estorban. La versión comprometida (un buffer) se restauró.
- Consecuencia: la velocidad de reproducción está acotada por (tiempo de lectura del CD por cuadro) +
  (tiempo del MDEC por cuadro), sin solaparse. Para 15 cuadros/s a 320x176 hay que bajar uno de los dos.
- **Decisión de video (por ahora):** el video de Wani se codifica a 160x96 y 12 cuadros por segundo, con
  `psxavenc -t strv -v v2 -s 160x96 -r 12 -x 1`. Motivo: es la combinación que mejor aguanta el límite de
  lectura del CD (unos 10,7 cuadros por segundo medidos en el reproductor de prueba). Optimizar el decodificador
  apenas mejoraría la velocidad: la espera del CD domina. Pendiente de integración y de revisar la calidad con las
  escenas importantes en el port.
- **Módulo de video en el motor (paso 9, integración):** `modules/fmv.c` (`special_fmv`): lee `\VIDEO.STR` con
  `cd_read_sectors` (sin callbacks de CD), decodifica un cuadro por actualización, lo sube a VRAM (640,256) y lo
  dibuja a doble tamaño en tiras de página, con las barras del cuadro. X sale. Cuadros de hasta 160x96.
  Compila sin advertencias. Regresión de Snoot: 5 escenarios idénticos; `chat` y `creditos` con capturas
  idénticas y el contador de cuadros una unidad menor (mismo caso documentado). Pendiente: que un script lo abra
  con `SPECIAL` (se asigna en la tabla del juego, con el port de Wani) y verlo dentro del juego.

## 2026-10-13 - Fase 0 de Wani con el motor compartido
- Perfil `generic` (`games/default`, sin reglas de juego) compilado: `build/default/default.exe` y `default.elf`.
- Wani arma su disco de prueba con este motor (`E:\Dev\wani-ps1\tools\engine\disco.py`): `GAME.BIN` mínimo,
  un capítulo (`C00.VNB`), sus textos (`T00.TXT`), un fondo (`I0001.IMG`, 8 bits y LZ4) y la fuente de Snoot
  (temporal). Probado en PCSX-Redux con el mismo arnés de Lua de `snoot.py`: captura del título (el menú de
  siempre) y del fondo con la línea "4 de Septiembre." del guion de Wani.
- Sin cambios en el código del motor. Para Wani hizo falta: `GAME.BIN` con cero hablantes, posiciones ni galería
  (el motor sale antes de leer lo que falta), y `FILES.BIN` con la raíz del disco (SYSTEM.CNF y el ejecutable).
- **Video, pregunta abierta:** 320x176 a 15 cuadros/s no está demostrado. El ejemplo oficial de PSn00bSDK lee
  con `CdlReadS` en modo tiempo real y callbacks; el reproductor de prueba lee con reposicionamiento y da unos
  6 cuadros/s. Pasar a streaming cambia el diseño de `modules/fmv.c` (hoy sin callbacks). Mientras el usuario
  decide, el video de Wani sigue a 160x96 y 12 cuadros/s.
- **Sprites:** Wani necesita 25 a la vez; el motor tiene 16 (capas 4 a 19). Pendiente en el paso 4 de la Fase C.

## 2026-10-13 - Título sin extras, sprites medidos y memory card
- Título: la fila "Capítulos extra" solo existe si el disco trae extras (`title_rows` en `app/main.c`). Wani no
  tiene extras y su menú queda con 4 filas. Snoot sin cambios: `snoot.py check --only titulo menus` da "igual" en
  las 7 capturas.
- Sprites: sin contar multitud ni fondos de pantalla completa, la escena más cargada de Wani tiene 16 capas de
  personaje (cap. 18B). El motor ya tiene 16 capas (4 a 19), así que el paso 4 queda con revisión de VRAM y sin
  ampliación. Las 25 de antes contaban multitud.
- Memory card: el guardado usa la API de la BIOS (`bu00:`), con dos copias alternadas y checksum. Probado solo en
  PCSX-Redux. No probado en PS1 física.

## 2026-10-13 - Videos en la galería (VID1) y pantalla de video por archivo
- `GAME.BIN` puede traer una sección `VID1` (después del menú de desarrollo, antes de `UI01`): videos de la galería con
  su entrada, su archivo `V<nn>.STR` y la imagen que lo desbloquea. Snoot no la tiene y no cambia.
- En la galería, una entrada de video vista muestra "Video / X para ver"; X la reproduce con `special_fmv`
  (`fmv_select(n)` elige `V<nn>.STR`) y al terminar vuelve a la galería (`special_return`).
- `games/default/specials.c` registra el id 250 (`SPECIAL_VIDEO`). Prueba en PCSX-Redux con Wani: galería →
  video → vuelta a la galería (capturas en `wani-ps1\build\fase0\probar`).
- Regresión de Snoot: `snoot.py check --only titulo menus partida` da "igual" en 1, 6 y 7 capturas.
- Estado para Wani (2026-10-13): el capítulo 1 compilado corre en el motor sin cambios (texto, menús, saltos).
  Lo que falta del lado del motor: revisar VRAM con 16 personajes y las pestañas de la galería. Ver `wani-ps1\STATUS.md`.

## 2026-10-15 - Fase D inicial y perfil propio de Wani
- `vncompiler/`: compilador guion.json → VNB1, enlazador y simulador determinista de flujo.
  Se reutilizan CALL/RETURN y LOAD_CHAPTER, sin cambiar el formato; variables e ids de texto comunes.
- El port de Wani usa adaptadores y configura su preview. Las condiciones no soportadas detienen el camino
  con HALT; Python, pantallas y recursos siguen pendientes y se reportan.
- VM: validación de instrucciones truncadas, tablas de menús/teléfono, variables y operadores;
  vm_start limpia el estado de menú pendiente. Hablantes de hasta 63 bytes con validación del límite.
- `games/wani` y preset `wani`: archivos/firma de memory card propios y 3072 bytes de texto leído.
  Configuración generada por perfil y comprobación de que progreso, ranuras y lienzo caben en un bloque.
- 21 tests del compilador/VM contrastan el flujo con `core/vm.c` nativo; Wani agrega cuatro recorridos reales.
- PCSX-Redux ejecutó la preview de capítulos 1 y 2 hasta volver al título. Escritura WNS1 verificada en tarjeta emulada.
- Guardar y cargar tras reiniciar el emulador también recupera la posición y la pila de llamadas de la preview.
- Snoot conserva sus valores originales de guardado. Regresión repetida tras los cambios de perfil:
  título (1), menús (6) y partida (7), las 14 capturas idénticas a las referencias, resultado OK.
- Pendiente: recursos del port, cobertura completa, pruebas de pantallas, VRAM y streaming/audio de video.

## 2026-10-21 - Primer pase, ciclo estable y fase heredada (PAKO-4)
- Diseno en `docs/ciclo-fase.md`: opciones, encaje en ANIM y coste. Recomendado para un futuro VNB2:
  indice de clave de reinicio del bucle (cubre primer pase distinto y bucles con introduccion).
- Sin cambio de VNB1 ni C: `vncompiler/temporal.py` rota el ciclo estable a la fase heredada
  (clock_offset con bucle desde 0) y acepta cycle_tracks solo si el resto del primer pase coincide con el ciclo.
- Primer pase distinto visible, fase sin bucle y loop_start > 0 siguen rechazados. 74 pruebas del compilador pasan.
