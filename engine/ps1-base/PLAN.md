# Plan: vn-engine-ps1

Cierre 2026-10-17: punto consolidado en E:/Dev/wani-ps1/docs/retomar-sesion.md.
El kit ya conserva fase y ciclos con primer pase distinto. Siguiente tarea compartida:
disenar su consumo sin perder continuidad de lectura/guardado; ANIM por ahora los rechaza.
No se cambio C ni VNB1. Cambios futuros del formato deben seguir el proceso de versionado.

> El motor de snoot-ps1 pasa a ser un motor compartido. Se avanza por fases y no se pasa a la
> siguiente sin cumplir sus criterios de "terminado".

## 1. Punto de partida (medido el 2026-10-12)
El motor de Snoot tiene unas 6 000 líneas:

| Parte | Líneas | Estado |
|---|---|---|
| `vm.c` (máquina del guion), `audio.c` (XA y VAG), `cd.c` y `res.c` (carga sin búsquedas), `img.c`, `video.c`, `text.c`, `save.c`, `input.c`, `lz4.c`, `scene.c` | ~3 700 | casi todo general |
| `main.c`: título, menús, galería, pausa, flujo del juego | ~2 400 | mezclado con cosas de Snoot: 4 finales, capítulos extra (regla D1 de Snoot), chat del capítulo 4, créditos, imágenes de los finales |

La copia compila a un ejecutable **byte a byte idéntico** al de snoot-ps1.

## 2. Fases

### Fase A — Importar (hecha)
- Copia del motor de snoot-ps1 (`ae2f4f0`): `src/`, `include/`, CMake y sus documentos de formato en
  `docs/snoot-ps1/`.
- **Terminado:** compila idéntico a snoot-ps1. ✔

### Fase B — Separar lo general de lo de Snoot (hecha, confirmada en emulador)
- Diseño (`docs/diseno.md`, a aprobar antes de tocar código):
  - **Núcleo:** VM, audio, CD, recursos, imágenes, video, texto, guardado, controles, escena.
  - **Perfil del juego en el disco** (`GAME.CFG` o tablas): cantidad de finales, reglas de
    desbloqueo, entradas del menú de título, galería, nombre del juego, ranuras de guardado.
  - **Módulos de pantallas especiales** (la instrucción `SPECIAL`): chat por tiras, créditos,
    teclado en pantalla. Cada uno es un módulo; cada juego elige los suyos al compilar.
  - El ejecutable deja de llamarse `snoot`: un CMake por juego que elige perfil y módulos.
- Sacar de `main.c` lo propio de Snoot sin cambiar su comportamiento.
- **Terminado:** con el perfil de Snoot, el motor compartido corre los datos de snoot-ps1 (se leen
  de su `build/`, solo lectura) y se juega igual: mismo título, menús, extras, galería, chat,
  créditos y guardado. Se compara en el emulador con el disco de snoot-ps1 v1.0.

### Fase C — Lo que pide Wani (y sirve a otros juegos) (en curso)
Cada punto entra como parte general del motor:
- [~] video STR con el MDEC (a partir del ejemplo `examples/mdec/strvideo` de PSn00bSDK) y su audio XA:
  prueba aislada verificada en emulador (`tests/str`); falta integrarlo al motor;
- [~] animaciones por cuadros con transparencia: el formato ya las tiene (eventos de la tabla ANIM que cambian
  la imagen; Snoot usa 36 animaciones con 103 cambios). Falta medir el streaming de cuadros desde el CD para
  los de Wani (créditos: 8 s a 15 cuadros/s de 480x270, no caben en VRAM)
- [~] más sprites a la vez (hasta ~16 de personajes) con el asignador de VRAM revisado: 16 capas
  hechas; falta revisar VRAM para 12 sprites con los tamaños de Wani;
- [x] cámara (zoom, desplazamiento; `CAMERA`), verificada visualmente. Pendiente: sacudidas
  `xpunch`/`ypunch` como instrucción propia (hoy: transiciones `TR_VPUNCH`/`TR_HPUNCH`) y perspectiva;
- [~] texto animado (`{sh}` temblor, `{sc}`): código hecho (`docs/bytecode.md`); falta verlo con una escena;
- [x] pantalla de chat de teléfono con burbujas (`OP_PHONE` + módulo `phone`): código hecho; falta verla con Wani;
- [x] lienzo de dibujo con cursor y guardado del dibujo en la memory card: código hecho; falta abrirlo en Wani;
- [x] pantalla de elección con imágenes (`OP_IMGMENU`, cofre de Wani): código hecho; falta verla
  con una escena de Wani.
- **Terminado:** cada parte tiene una escena de prueba que corre en DuckStation, y Snoot sigue igual.

### Fase D — Bytecode v2 y compilador común
- Avance 2026-10-15: `vncompiler/` compila y enlaza VNB1 con los operadores existentes, y su simulador
  de flujo se contrasta con la VM nativa. Wani usa un adaptador; faltan Python/pantallas, recursos y cobertura completa.
- `docs/bytecode.md` v2: la v1 de Snoot más lo de la Fase C, con el perfil del juego.
- Compilador `guion.json` (del kit) -> VNB v2 en `tools/` de este repo, para que cualquier port lo
  use con su propia configuración. Simulador del bytecode, con su cobertura comparada con la del
  kit.
- **Terminado:** Wani compila completo y el simulador del bytecode da la misma cobertura que el kit.

### Fase E (opcional) — Snoot en el motor compartido
- Pasar snoot-ps1 a este motor y al compilador común (con permiso, porque cambia snoot-ps1).
- **Terminado:** Snoot v1.1 con el motor compartido, igual o mejor que la v1.0.

## 3. Decisiones (2026-10-12, del usuario)
1. **Licencia: MIT** (`LICENSE`), para poder usar el motor en cualquier juego.
   - Las bibliotecas de PSn00bSDK son MPL-2.0: se enlazan sin problema. Un archivo que se copie de
     sus ejemplos (por ejemplo, el reproductor STR) conserva la MPL-2.0 y su aviso.
   - Cada port se publica con la licencia de su juego (Snoot y Wani: AGPL-3.0 y CC-BY-SA-4.0); el
     motor dentro del disco sigue siendo MIT.
2. **El compilador vive aquí**, en `tools/`: el motor define el bytecode, así que el compilador
   `guion.json` -> VNB, el simulador del bytecode y la especificación cambian juntos. El kit sigue
   dando solo `guion.json` y los recursos, y cada port pone su configuración.
