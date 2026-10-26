# STATUS

## Cierre vigente: 2026-10-24 - Giro de sprites en ANIM (PAKO-17)
- Bytecode v3: flags de ANIM bit 7 = las claves traen angulo `s16` (1/4096 de vuelta) en los bytes 9-10; pivote en
  el centro de la imagen. Sin el bit todo igual (Snoot y capitulos ya compilados). VNB1 y guardado sin cambios.
- Archivos: vncompiler/formatos.py, vncompiler/temporal.py (`rotated_center`), core/scene.c/.h, core/vm.h
  (`VmLook.angle`), core/img.c/.h (`img_draw_ex_rot`), app/main.c, docs/bytecode.md.
- Consumidor: wani-ps1 (`camera_blocks.project` conserva el pivote del giro bajo la camara), rama
  agent/claude-lead/pako-17 de wani-ps1. Capitulo 1: 236 -> 239 dialogos con movimiento real; capitulo 2: 399.
- Pruebas: motor 112 pasan (incluye PAKO-14 mezclado y tests/compiler/test_rotation.py con scene.c nativo);
  perfiles wani y snoot compilan sin avisos; wani-ps1 147 pasan / 2 omitidas (contra esta rama del motor).
  `tests/emu/snoot.py check`: PCSX-Redux no dio cuadros sin ventana (parado a los ~25 min); sin validacion visual.
- Preview con el giro: `E:/Dev/wani-ps1/build/probar-main/wani_preview.cue` (sin probar en emulador; checklist en
  el comentario de PAKO-17). Tambien es la primera con capitulos en el heap (PAKO-14).
- Siguiente: camara durante una salida animada en wani (corta el gimnasio tras `rotate_funny`).
- Mezclado en main (43ce99e); wani-ps1 main 26b506a. Motor 112 pasan en main.

## Cierre anterior: 2026-10-24 - Capitulos grandes en el heap (PAKO-14)
- `chapter_buf`/`text_buf` fijos reemplazados por `core/chapter.c`: un bloque del heap por capitulo a su tamano
  real, con NULL revisado. Limites en `core/vn_limits.h` (96 KiB VNB, 96 KiB texto), leidos tambien por
  `vncompiler/formatos.py`: `compile_program` falla con capitulo, tamano y limite. Sin cambio de VNB1.
- Heap libre al arrancar (wani): 385.936 -> 516.168 bytes. Eleccion heap vs LOAD_PACK en docs/presupuesto-memoria.md.
- Pruebas: motor 100 pasan (5 nuevas en tests/compiler/test_chapter_limits.py); perfiles wani y snoot compilan;
  wani-ps1 145 pasan / 2 omitidas (contra el checkout de E:/Dev, sin esta rama).
- Sin nueva preview. Validacion pendiente: cargar en emulador un capitulo de mas de 48 KiB y la fuente.
- wani-ps1 ya quito sus topes propios de 48/80 KiB (main 6e7ca05).
- Mezclado en main (3c45554).

## Cierre anterior: 2026-10-24 - ORDER desde el compilador y espejo que cambia dentro de ANIM
- Nodo `ps1_order` emite el opcode ORDER que el motor ya tenia (wani lo usa para `behind`). Sin cambio de formato.
- `xzoom` que salta entre 1 y -1 dentro de una animacion se escribe como eventos de imagen con el bit de espejo.
- Pruebas: compilador 95 pasan. Mezclado en main (4a4950f). Sin emulador.

## Cierre anterior: 2026-10-23 - ANIM con cambios de imagen, color, espejo e introduccion de bucle
- vncompiler escribe eventos de imagen (formato de 7 bytes que el motor ya leia), modulacion r/g/b desde
  matrixcolor multiplicable, flip desde `xzoom -1` y la clave de inicio de bucle (flags bits 1-6, leida en
  core/scene.c). Las propiedades que ANIM no dibuja fallan con su nombre. Detalle en docs/bytecode.md.
- Con el kit nuevo, el motor acepta 4577 de 5224 eventos de Wani (antes 4237).
- Pruebas: compilador 93 pasan (incluye scene.c nativo); perfil wani compila. Sin emulador.
- Ramas: feat/anim-child-frames (bdba056) y feat/anim-color-props (encima, 67dcb6c), sin mezclar.

## Cierre anterior: 2026-10-22 - Reproductor STR en streaming con XA y 339 KiB de RAM liberados (PAKO-12)
- modules/fmv.c reescrito sobre examples/mdec/strvideo: CdlReadS con CdlModeRT, sectores por CdReadyCallback,
  doble buffer de cuadros, VLC con tabla en el scratchpad, MDEC en franjas por DMA al framebuffer oculto, XA
  intercalado reproducido por la lectora. Cuadros de hasta 320x240; X corta. Misma interfaz (fmv_select, special_fmv).
- Los buffers del video salen de la cache de precarga de res (res_borrow_cache) mientras la escena no se dibuja: la
  BSS baja de 1.886.800 a 1.539.876 bytes y el heap libre al arrancar pasa de ~40 KiB a ~377 KiB.
- audio_video_begin/end: la musica se pausa durante el video y vuelve donde habria llegado (fundidos avanzados; una
  pista sin bucle que termino no vuelve).
- Pruebas: compilador 83 pasan; perfil wani compila sin avisos. Medido con Wani en DuckStation (2 MB): 24 cuadros/s
  sostenidos con audio; PCSX-Redux muestra el cuadro completo. Consola real pendiente.
- Rama: video-streaming.

## Cierre anterior: 2026-10-22 - Guard de CdSearchFile y presupuesto de heap (PAKO-9)
- El motor ya no llama a CdSearchFile: core/cd.c implementa iso_search, que baja del descriptor de
  volumen y recorre los directorios sector a sector usando la tabla FTB1 de borrador (cero heap;
  antes un DATA de 48 KB agotaba el heap y la DMA del CD sobrescribia la RAM desde 0x80000000).
  Las ausencias fallan con el error visible "cd: no se encuentra ...".
- Prueba nativa nueva tests/compiler/test_cd_guard.py: walker contra un disco sintetico con un DATA
  de 25 sectores, malloc envenenado y chequeo de que ningun .c del motor llame CdSearchFile.
- Presupuesto medido en docs/presupuesto-memoria.md: wani BSS 1.886.800 bytes (_end 0x801f5fa4),
  heap libre en el arranque 41.044 bytes (tope 0x801ffff8, compartido con la pila). Quedan dos
  llamadas root-only en tests/str (discos de prueba chicos); una es el ejemplo MPL-2.0 sin cambios.
- Pruebas: compilador 76 pasan (74 anteriores + 2 nuevas); cmake --preset wani y default (snoot)
  compilan; wani-ps1 118 pasan / 2 omitidas (corrio contra los checkouts de E:/Dev, no contra esta
  rama) con 1 error preexistente de overlap_host.c contra el VmHost nuevo del motor original,
  ajeno a PAKO-9 y a cd.c.
- Sin nueva preview. Sin cambio de VNB1 ni de bytecode.
- Validacion pendiente: arranque en emulador o consola real del disco actual y del disco antiguo
  con DATA grande (aqui no se corren emuladores).
- Siguiente: validar en emulador que el arranque via iso_search carga la tabla igual que antes.
- Rama: agent/opencode/pako-9.

## Cierre anterior: 2026-10-22 - SHOW desde el aspecto actual (PAKO-6)
- SHOW flags bit3 (`VM_SHOW_FROM_CURRENT`): al reiniciar la animacion de un sprite existente, el motor captura
  su aspecto actual y lo usa como clave 0 del primer tramo (primer pase). Doc: docs/bytecode.md.
- Registro SHOW y encabezado VNB1 sin cambios (bit antes reservado); tamano de guardado sin cambios
  (`Vm.from` no se guarda; al cargar se asienta como antes). Al saltar no se captura.
- `VmHost` tiene un cuarto campo opcional `capture`; main.c usa `scene_capture`. Hosts de prueba actualizados.
- Pruebas: 81 pasan (7 nuevas en tests/compiler/test_show_from_current.py con vm.c + scene.c nativos).
  Perfil wani compilado sin avisos. Sin emulador ni consola real.
- Rama: agent/claude-lead/pako-6.

## Cierre anterior: 2026-10-21 - Primer pase / ciclo / fase (PAKO-4)
- Diseno: docs/ciclo-fase.md. VNB1 y nucleo C sin cambios.
- Casos ahora soportados por vncompiler/temporal.py (loop_start=0): clock_offset sin cycle_tracks
  (bucle rotado a la fase heredada); cycle_tracks con clock_offset >= duration; cycle_tracks cuyo
  resto del primer pase coincide con el ciclo estable dentro de la tolerancia.
- Siguen rechazados: primer pase distinto visible (SHOW nuevo, clock_offset=0), fase sin bucle o negativa,
  bucles con introduccion. Soportarlos requiere cambio de formato (recomendado: clave de reinicio, VNB2).
- 74 pruebas del compilador pasan. Cobertura real de los 70 eventos de Wani sin medir: queda para PAKO-6.

## 2026-10-18 - Audio de historia
- ps1_audio valida y emite los opcodes de audio existentes (0x20..0x27); sin cambio VNB/AIX1.
- VOLUME sin fundido es inmediato. SFX_STOP aplica el tiempo de fundido y apaga voces al llegar a cero; VOLUME afecta voces SPU activas.
- 70 pruebas del compilador pasan, incluidas dos pruebas C de las rutinas de volumen/fundido. Perfil wani compilado.
- Consumidor Wani: build/jugar-audio, 95 sentencias de audio de capitulos 1 y 2. Recorrido/escucha en emulador pendientes; continuidad temporal/guardado no resuelta.
- Sin commits ni ramas; preservar cambios locales.

## 2026-10-18 - Capitulo 2 de Wani
- Wani integra el capitulo 2 con ANIM/TRANSITION existentes e ids globales de imagen. Sin cambios al nucleo C ni al formato de bytecode en este incremento. Perfil wani compilado; 58 pruebas del compilador pasan. Cuatro secuencias de flujo grafico de Wani coinciden con core/vm.c nativo. PCSX-Redux sin cuadros en este entorno: validacion visual pendiente.
- Preview y limites: E:/Dev/wani-ps1/docs/capitulo2.md. Sin commits/ramas; preservar cambios locales.

## Cierre anterior: 2026-10-17
- Reanudar con E:/Dev/wani-ps1/docs/retomar-sesion.md. Motor: 55 pruebas pasan.
- Disenar consumo de introduccion/primer pase/ciclo/fase y continuidad/guardado antes de retirar rechazos.
- Sin cambios C ni VNB1 esta sesion; si hace falta cambiar bytecode, aplicar versionado y actualizar todos los consumidores.
- Cifras posteriores en secciones historicas no sustituyen este cierre. Sin commits ni ramas.

## 2026-10-17 - Contrato de ciclo estable
- Adaptador rechaza cycle_tracks no nulo: ANIM no representa primer pase distinto del ciclo estable.
- 55 pruebas pasan. No cambia nucleo C ni VNB1. Plan en kit/docs/plan-calidad-port.md.

## 2026-10-17 - Contrato de fase ciclica del kit
- Adaptador rechaza clock_offset no nulo para no perder fase heredada silenciosamente.
- 54 pruebas pasan. Sin cambios a C ni VNB1; soporte de fase/bucles con introduccion en PS1 pendiente.

Punto de reanudacion actualizado al cierre del 2026-10-17: `E:\Dev\wani-ps1\docs\retomar-sesion.md`.
Proximo soporte compartido: bucles con introduccion, orden/salidas y transiciones; no cambiar VNB1 sin su proceso de versionado.

## 2026-10-16 - Consumidor temporal por lotes
Wani agrega cinco bloques compatibles, 66 dialogos y 24 movimientos originales usando ANIM existente.
Uso y limites actualizados en docs/temporal-kit.md; no hay cambio del nucleo ni de VNB1.

Última actualización: 2026-10-17

## Estado actual
Wani amplia a diez movimientos de presentacion/saludo; herencia inmediata conservada desde el kit.
Salto y saludo comprobados con scene.c nativo, y salto visible en PCSX-Redux. Nucleo C y VNB1 sin cambios.
Adaptador temporal del kit integrado: vncompiler/temporal.py, documentado en docs/temporal-kit.md.
Curvas muestreadas a ANIM y transiciones neutrales; consumidores iniciales en Wani, sin cambio de VNB1.
53 pruebas del compilador/motor pasan; core/scene.c nativo y panorama Wani en PCSX-Redux comprobados.
Correccion de texto: TextLayout usa metricas FNT1 para ajuste por palabras y paginacion opcional del compilador.
Las opciones se ajustan sin codigos de estilo incompatibles con font_draw. 44 pruebas del motor pasan.
Nodo ps1_special validado; Wani conecta dos introducciones STR mediante su perfil, sin cambiar VNB1.
Fases A y B terminadas. Fases C y D en progreso.
El motor ejecuta la preview enlazada de los capítulos 1 y 2 de Wani.
Prueba visual aislada de Wani ejecutada en PCSX-Redux: SCENE/SHOW/HIDE y dos sprites independientes.
El compilador admite nodos visuales ya resueltos; todavía no interpreta la puesta en escena de Ren'Py.
También serializa y deduplica tablas ANIM del formato VNB1 existente (posición, escala, alfa y color).
Wani completó en PCSX-Redux un recorrido visual lineal de 600 diálogos, separado del port con decisiones.
El juego completo, las imágenes/audio de Wani y la cobertura exhaustiva siguen pendientes.

## Comandos
- Wani: `cmake --preset wani` y `cmake --build build/wani`.
- Snoot: `cmake --preset default` y `cmake --build build`.
- Pruebas del compilador y VM: `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp build\pytest-engine`.
- Regresión en emulador: `.\.venv\Scripts\python.exe tests\emu\snoot.py check --only titulo menus partida`.
- Disco de Wani: ejecutar build.py desde E:\Dev\wani-ps1.

## Hecho
- A: importación del motor de Snoot; B: núcleo, módulos y perfiles separados.
- Cámara de zoom/desplazamiento; texto animado; 16 capas de sprite; módulos teléfono, lienzo y elección con imágenes.
- Video STR a 160x96/12 cuadros por segundo, galería VID1 y título sin extras cuando no hay extras.
- Perfil propio games/wani, con teléfono y lienzo registrados.
- Configuración de progreso y memory card por perfil: Wani usa 3072 bytes de texto leído y archivos WANI A/B.
  Snoot conserva 2048 bytes, sus nombres y su firma originales.
- Comprobación en compilación de que ranuras, progreso y dibujo caben en una copia de memory card.
- Fase D inicial: vncompiler contiene compilador guion.json → VNB1, enlazador y simulador determinista de flujo.
- Variables comunes, CALL/RETURN, LOAD_CHAPTER, _return entero, condiciones y menús condicionados.
- Validación de instrucciones truncadas, índices de variables, operadores y tablas de menú/teléfono en la VM.
- Nombres de hablantes de hasta 63 bytes, con comprobación del límite.
- 21 pruebas del compilador/VM pasan, contrastando con core/vm.c compilado en PC.
- Regresión de Snoot: título, menús y partida conservan las capturas de referencia.

## Pendiente
- D: Python/pantallas, inicialización, cobertura exhaustiva de rutas y comparación contra el kit.
- C: probar VRAM con las 16 capas de Wani; streaming de cuadros de créditos y audio de STR.
- Conectar teléfono, lienzo y menú de imágenes al guion de Wani y verificarlos visualmente.
- Galería con pestañas y desbloqueos del juego completo.
- Cámara: zoom de fondos grandes, persistencia en guardados y perspectiva/sacudidas.
- Hardware real: CD y memory card física.
- E opcional: migrar Snoot al compilador común, solo con autorización.

## Compatibilidad
No hay cambio de formato del bytecode: se usan los operadores VNB1 existentes.
Los archivos antiguos de Wani con el perfil generic no se migran al perfil wani.
El motor y el compilador siguen siendo una base reutilizable; las reglas de Wani permanecen en su perfil/adaptador.
