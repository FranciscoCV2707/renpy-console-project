# Console Test Lab

`tools.ctl compare` admite tres modos en `compare.mode`:

- `same`: compara los eventos TRACE seleccionados y los cuadros indicados.
- `renpy`: compara hablante y texto en español por cada `SAY`.
- `renpy_full`: compara también el fondo, los sprites visibles y la música activa en cada `SAY`.

`renpy_full` usa el mapa compilado de Snoot PS1 para traducir IDs de imagen, pista y tag a nombres. El hook Ren'Py
reconstruye el estado acumulando `SCENE`, `SHOW`, `HIDE`, `PLAY` y `STOP` hasta el siguiente `SAY`. Los nombres de
música ignoran diferencias de mayúsculas y barras de ruta. Las líneas repetidas consecutivas con el mismo ID de
traducción en Ren'Py cuentan una sola vez, igual que en `renpy`.

En Snoot, `rec`, `viewfinder` y `photoviewfinder` son superposiciones aunque Ren'Py las emita con `attrs=` vacío;
siguen en `sprites` y no reemplazan el fondo. Las imágenes con el tag `bg` o `background`, y las imágenes de
escena como `room anon day alt`, se comparan como fondo. El atributo Ren'Py `flip` se omite de la identidad del
sprite: el compilador lo representa con una bandera de dibujo, que TRACE aún no expone. Por eso `renpy_full`
compara expresión y presencia, pero no certifica la orientación reflejada.

Las diferencias intencionales se declaran por índice de `SAY`, campo y valores exactos de ambas trazas:

```yaml
compare:
  mode: renpy_full
  events: [SAY]
  exceptions:
  - index: 12
    field: bg
    actual: classroom-demake
    reference: classroom
```

Los campos permitidos son `bg`, `sprites` y `music`. La excepción solo permite el par de valores escrito; otros
cambios en esa línea siguen produciendo `FAIL`. Sin una excepción coincidente, el reporte señala el primer `SAY` y
campo divergente.
