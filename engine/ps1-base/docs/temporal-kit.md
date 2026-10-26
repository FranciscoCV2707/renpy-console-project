# Consumir cronologias de renpy-port-kit

cycle_tracks/cycle_initial describen vueltas posteriores diferentes del primer pase.
El adaptador rechaza cycle_tracks no nulo incluso con loop_start=0 y clock_offset=0;
muestrear solo una vuelta y marcar loop perderia el estado original. Soporte destino pendiente.

Actualizacion 2026-10-17: el kit serializa clock_offset para vistas ciclicas heredadas.
El adaptador rechaza valores no nulos: no puede descartarlos ni reiniciar el ciclo.
Bucles con introduccion siguen sin representarse en ANIM. No cambia C ni VNB1.

Actualizacion 2026-10-21 (docs/ciclo-fase.md): con loop_start=0 el adaptador rota el ciclo
estable a la fase heredada. Acepta clock_offset sin cycle_tracks, cycle_tracks con
clock_offset >= duration, y cycle_tracks cuyo resto del primer pase ya coincide con el ciclo.
Primer pase distinto visible, fase sin bucle y bucles con introduccion siguen rechazados.

El kit interpreta ATL como datos seguros. El compilador del motor adapta esos datos al
formato PS1. Ninguno debe depender de rutas o nombres de imagen de un juego concreto.

## Ejemplo

```python
from renpykit.temporal import TemporalCompiler, transition_spec
from vncompiler.temporal import animation_from_timeline, transition_from_spec
from vncompiler.programa import compile_program

timeline = TemporalCompiler(script).compile(
    node.get("atl"), node.get("at") or [], initial=previous_state,
    image_size=(6000, 1080), where=node.get("where", ""))
resolved = animation_from_timeline(timeline, (1920, 1080), (6000, 1080), tolerance=6)
show = {"op": "ps1_show", "tag": 1, "image": image_id,
        "keyframes": resolved["keyframes"], "loop": resolved["loop"]}
transition = transition_from_spec(transition_spec({"py": "Dissolve(1.0)"}, script))
```

Insertar `show` y `transition` en el lugar de los eventos originales antes de llamar a
`compile_program`. Un panorama opaco que funciona como fondo puede usar `ps1_scene`;
no debe convertirse indiscriminadamente todo SHOW en SCENE porque borraria los otros tags.
El port prepara los recursos IMG y sus ids; nunca se deducen del nombre dentro del motor.

## Contrato y restricciones

- `animation_from_timeline` acepta un objeto con sample(t), duration, loop_start y diagnostics;
  no importa el kit ni ejecuta codigo del juego. El port proporciona ambos paquetes en su entorno.
- Las dimensiones son originales, antes de reducir imagen/pantalla por el mismo factor.
  Posicion final: xpos - xanchor * zoom + xoffset. Se calcula la alineacion 8.8 equivalente.
- Se muestrea a 60 cuadros/s y se reducen adaptativamente las claves hasta un maximo de 64.
  La tolerancia controla el error de interpolacion de los valores cuantizados, en pixeles originales;
  no elimina el error propio de 8.8/zoom 1/64 ni garantiza tiempo de pared si caen cuadros.
- Se rechazan diagnosticos del kit, bucles con introduccion, rotacion/escala por eje/profundidad,
  zoom/alfa fuera de rango y alineaciones imposibles. Si imagen y viewport tienen igual medida,
  un desplazamiento en ese eje necesita padding o un camino de renderizado distinto.
- ANIM calcula posicion, escala uniforme y alfa; el alfa gradual solo se aplica a colores solidos.
  El dibujado de bitmaps no lo mezcla gradualmente: usar TRANSITION para fundidos de personajes,
  no presentar una clave alpha como fundido visible ya implementado. El camino de fondos panoramicos
  solo consume x/y. No usar animaciones de alfa/zoom como si ese camino las soportara.
- `transition_from_spec` admite corte, disolvencia lineal y Fade por negro/blanco; los demas
  casos fallan explicitamente. `ps1_camera` recibe CAMERA 2D ya resuelta, no traduce perspectiva 3D.
- El formato VNB1 no cambia. El adaptador no cubre aun cambios de imagen/sonido dentro de ATL.
- Herencia de tags, ramas, orden/behind, recursos y camara son responsabilidades del lowering del port;
  no se pueden reemplazar por un snapshot ni por el estado final de otra ruta.

## Validacion con Wani

Actualizacion por lotes 2026-10-16: Wani conecta cinco bloques adicionales (66 dialogos/24 movimientos).
El consumidor descubre recursos y confirma prefijos compatibles de forma transaccional; los eventos
no representables vuelven a snapshots con diagnosticos. La API ANIM/VNB1 y el nucleo C no cambian.
Timeline.after del kit ya conserva fase no lineal en tiempos conocidos, incluyendo tracks con inicio negativo.
El adaptador debe muestrearlos, no truncarlos ni reiniciar easing. after(0) admite bucles; otros recortes no.
Transiciones layer=master se aproximan explicitamente por pantalla en Wani: no afirmar soporte multicapa.

Ampliacion 2026-10-16: la conversacion con Ben cubre 37 dialogos y diez movimientos.
Antes de cambiar la imagen de un SHOW inmediato, el port conserva la Timeline activa con after(0),
en lugar de compilar otra desde el estado final. Solo se recortan lineales en tiempos conocidos;
curvas no lineales en curso y tiempos desconocidos de lectura siguen requiriendo herencia de fase.
La tabla ANIM y el nucleo C no cambian. scene.c nativo tambien valida el salto de Ben.

`wani-ps1/tools/script_compiler/motion.py` conecta los movimientos originales del pasillo:
centro a izquierda en 72 cuadros y luego derecha en 90 cuadros, con sus curvas ease_quad
muestreadas. No se agregan movimientos arbitrarios. La prueba nativa usa core/scene.c;
`python -m tools.engine.motion_test` en el port valida posiciones en PCSX-Redux con Lua.
El resto de Wani sigue parcial: esta integracion no representa ATL general de todo el juego.
Tambien se conectan cuatro movimientos de Inco/Ben en su primera conversacion. Las disolvencias
del motor conservan duracion pero siguen lineales; el kit conserva la curva original para su implementacion futura.
