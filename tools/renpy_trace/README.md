# renpy_trace — hook de traza para Ren'Py

Archivo `trace_hook.rpy`: se copia **solo** en una copia de trabajo del juego (nunca en el original) y emite
líneas del protocolo TRACE (C3) de `PLAN.md` sección 4.1.

## Uso

1. Copiar `trace_hook.rpy` a `game/` de la copia del juego (o añadirlo al `PYTHONPATH` de Ren'Py).
2. Definir la variable de entorno `RCP_TRACE_OUT` con la ruta del archivo de salida. Sin ella el hook no hace nada.
3. Ejecutar con el SDK 8.3.7:

```
set RCP_TRACE_OUT=C:\ruta\trace.txt
E:\snoot\renpy-8.3.7-sdk\renpy.exe E:\ruta\copia-del-juego
```

Variables opcionales (compatibles con `kit_capture.rpy` del port-kit, si se usa a la vez): `KIT_CAPTURE_ROUTE`,
`KIT_CAPTURE_MANUAL_INTERACTIONS`, etc.

## Eventos emitidos

- `LABEL` — desde `config.label_callbacks` (`name`).
- `SAY` — en cada interacción de diálogo (`who`, `loc=archivo:línea`). Se emite desde la interacción, después de
  incrementar `frame`, a partir de los datos capturados en el callback de personaje.
- `SHOW` / `HIDE` / `SCENE` — comparando los tags visibles de la capa `master` con la interacción anterior
  (`SHOW` incluye `attrs` con `renpy.get_attributes(tag)` cuando existe).
- `PLAY` / `STOP` — comparando lo que suena en el canal `music`.
- `MENU` y `CHOICE` — al mostrar y elegir una opción. `CHOICE` emite el índice real entre las opciones elegibles
  (los items con valor `None` son títulos y no cuentan); si no se puede determinar, no se emite.
- `ERROR` — cuando falla alguna operación interna, con `msg=...`.
- `frame` = interacciones contadas desde el inicio; `seq` = secuencia global de líneas.

Los valores escapan `|`, `;`, `=` y saltos de línea con barra invertida.

## Formato provisional

Los campos `tag` y `music` usan nombres (no los ids numéricos del compilador VNB). Los ids numéricos quedan
pendientes hasta que el compilador los exponga.

## Limitaciones

- `SCENE` se detecta con la heurística actual: se emite cuando todos los tags previos de `master` desaparecen en
  la interacción. Puede no coincidir con un `scene` explícito en todos los casos.
- Faltan los eventos `END` y `FBHASH` (pendientes).

## Pendiente

- Los ids de texto que usa el compilador VNB todavía no se emiten en `SAY` (campo `text=`); por ahora solo
  `who` y `loc`. Se anota como pendiente para cuando el compilador exponga esos ids.
- La autoselección de opciones para recorrer rutas de forma determinista se delega a `kit_capture.rpy`
  (`SNOOT_CHOICES`); este hook solo registra lo que ocurre.