# renpy_trace — hook de traza para Ren'Py

Archivo `trace_hook.rpy`: se copia **solo** en una copia de trabajo del juego (nunca en el original) y emite
líneas del protocolo TRACE (C3) de `PLAN.md` sección 4.1.

## Uso

1. Copiar `trace_hook.rpy` a `game/` de la copia del juego (o añadirlo al `PYTHONPATH` de Ren'Py).
2. Definir la variable de entorno `RCP_TRACE_OUT` con la ruta del archivo de salida. Sin ella el hook no hace nada.
3. Ejecutar el juego con el SDK de Ren'Py (8.3.7). Las líneas se escriben en `RCP_TRACE_OUT`.

Variables opcionales (compatibles con `kit_capture.rpy` del port-kit, si se usa a la vez): `KIT_CAPTURE_ROUTE`,
`KIT_CAPTURE_MANUAL_INTERACTIONS`, etc.

## Eventos emitidos

- `LABEL` — desde `config.label_callbacks` (`name`).
- `SAY` — en cada interacción de diálogo (`who`, `loc=archivo:línea`).
- `SHOW` / `HIDE` / `SCENE` — comparando los tags visibles de la capa `master` con la interacción anterior.
- `PLAY` / `STOP` — comparando lo que suena en el canal `music`.
- `MENU` y `CHOICE` — al mostrar y elegir una opción.
- `frame` = interacciones contadas desde el inicio; `seq` = secuencia global de líneas.

Los valores escapan `|`, `;`, `=` y saltos de línea con barra invertida.

## Pendiente

- Los ids de texto que usa el compilador VNB todavía no se emiten en `SAY` (campo `text=`); por ahora solo
  `who` y `loc`. Se anota como pendiente para cuando el compilador exponga esos ids.
- La autoselección de opciones para recorrer rutas de forma determinista se delega a `kit_capture.rpy`
  (`SNOOT_CHOICES`); este hook solo registra lo que ocurre.