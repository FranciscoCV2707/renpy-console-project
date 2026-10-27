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
siguen en `sprites` y no reemplazan el fondo. Para Ren'Py, la imagen que sigue a `scene` llega al hook como `SHOW`
con el tag y atributos de la imagen; se compara como fondo. En el motor se usa el estado de `SCENE`, sin dejar que
un `SHOW` de overlay cambie ese fondo. El tag de fondo `room` también es una imagen de escena.

El atributo `flip` se quita del nombre de sprite en ambos lados. Snoot define las imágenes `flip` como envolturas
espejadas y el compilador las reduce a la imagen base más una bandera; el motor dibuja esa bandera, pero TRACE no la
expone. Por tanto, `renpy_full` compara expresión y presencia, pero no certifica la orientación reflejada.

La captura Ren'Py de Snoot no registra el `show black` temporal que aparece en algunos guiones. El normalizador
ignora ese tag del motor para no convertirlo en fondo y conservar la misma cobertura que la traza de referencia;
esto no valida la presencia de esa capa negra. `tools.ctl.full_diff` agrupa las diferencias por campo y par de
valores para revisar una traza completa, por ejemplo `python -m tools.ctl.full_diff tests/reference/traces/ps4/chapter_x2.trace`.

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

### Normalización verificada en T-628

Un `SHOW` sin atributos no cambia el fondo: guiones como X3 muestran personajes de imagen única y capas `dimmer_*`. El fondo se reconoce por el estado `SCENE` del motor y por tags de escena conocidos; `room` también se trata como fondo. Para `fangphonevideocall` y `layeredanonphone` se quitan del nombre compilado solo los atributos `default` comprobados en `src/image_definitions.rpy`; los atributos del teléfono se ordenan porque sus grupos son independientes. La música se normaliza como conjunto ordenado con prefijo `mix:` y se quitan prefijos `<sync ...>`. Esta forma común no recupera canales que el hook no registró; véase la revisión de 14 rutas en `docs/fidelidad.md`.
