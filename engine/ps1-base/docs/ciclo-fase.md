# Primer pase, ciclo estable y fase heredada en ANIM

Diseño para consumir `cycle_tracks`/`cycle_initial` (primer pase distinto de las vueltas
siguientes) y `clock_offset` (fase heredada por `Timeline.after`) del kit en el motor PS1.

## Semántica de partida

Kit (`renpykit/temporal.py`, `Timeline.sample(t)`): `s = t + clock_offset`. Si hay bucle y
`s >= duration`, `s` se envuelve en `[loop_start, duration)` y se usan `cycle_tracks`; si no,
se usan los tracks del primer pase. Con `loop_start = 0` (único bucle que ANIM admite) la
función visible es: el resto del primer pase en `[clock_offset, D)` y después el ciclo
estable `C` de periodo `D`, repetido.

Motor (`core/scene.c`, `scene_look`): con el bit 0 de flags, `t %= end` y la tabla se repite
desde la clave 0. No hay clave de reinicio ni desfase por sprite. `shown_at` marca el
cuadro 0; al cargar partida o saltar, la animación queda asentada (`SCENE_SETTLED`).

## Opciones

| Opción | Qué representa | ¿Cabe en ANIM actual? | RAM / CPU |
|---|---|---|---|
| A. Rotar el ciclo estable a la fase heredada | `C((t + φ) mod D)` | Sí: se muestrea `C` desde `φ` durante `D` cuadros y se marca bucle | Igual que hoy (mismas claves, mismo `t %= end`) |
| B. A + comprobar que el resto del primer pase ya coincide con el ciclo | primer pase que converge al ciclo antes de `φ`, o cuyo tramo restante es idéntico | Sí: es A con una verificación en el compilador | Solo coste en PC |
| C. Desenrollar primer pase + N vueltas sin bucle | primer pase distinto con lectura acotada | Sí, pero se congela al terminar las N vueltas; 64 claves limitan N | Más claves (hasta 64 × 15 bytes) |
| D. Índice de clave de reinicio del bucle (bits libres de flags o un u16 nuevo) | primer pase distinto + ciclo, y bucles con introducción (`loop_start > 0`) | No: cambia la interpretación de ANIM | 0–2 bytes por animación; una resta y un módulo más por sprite y cuadro |
| E. Dos animaciones encadenadas (al terminar A, pasar a B) | lo mismo que D | No: necesita un campo de enlace o un evento nuevo | Un índice por sprite; cambio de animación en la VM |
| F. Desfase inicial por SHOW (`shown_at = now - φ`) | fase heredada sin rotar la tabla | No: argumento nuevo de SHOW | 2 bytes por SHOW; no aporta nada que A no cubra |

C se descarta: el tiempo de lectura no se conoce y el sprite se quedaría quieto, lo que es
un cambio visible silencioso. F queda cubierta por A. D es la opción recomendada cuando se
autorice un cambio de formato (VNB2): resuelve primer pase distinto y bucles con
introducción con el mismo mecanismo y el coste más bajo; requiere versión nueva,
`docs/bytecode.md`, `scene.c`, compilador y simulador en el mismo cambio.

## Implementado (sin cambio de VNB1)

`vncompiler/temporal.py` aplica A + B cuando `loop_start == 0`:

- `clock_offset > 0` sin `cycle_tracks`: el bucle se rota a la fase heredada.
- `cycle_tracks` con `clock_offset >= duration`: ya se está en el ciclo estable; se rota.
- `cycle_tracks` con `clock_offset < duration`: se acepta solo si cada cuadro restante del
  primer pase coincide con el ciclo estable dentro de la tolerancia en píxeles. Si no,
  sigue el error "ANIM no representa primer pase distinto del ciclo estable".

Siguen rechazados: primer pase distinto visible (el caso típico de un SHOW nuevo, con
`clock_offset = 0`), `clock_offset` sin bucle o negativo, y `loop_start > 0`. La fase se
muestrea exacta en el reloj del kit; el periodo sigue redondeado a cuadros como antes.
Las tablas de animaciones sin fase ni ciclo no cambian.

## Límites conocidos

- La fase la fija el port al compilar (`after(t)` con `t` conocido). Una fase que depende
  del tiempo de lectura del jugador no se puede rotar en la PC; necesita estado en el motor.
- Guardar/cargar asienta las animaciones (`shown_at = 0`) y no conserva la fase.
- No se midió cuántos de los 70 eventos de Wani (45 sin otros diagnósticos) quedan
  cubiertos: la mayoría son SHOW nuevos con `clock_offset = 0`, que siguen rechazados.
  El recuento real corresponde al inventario del port.
