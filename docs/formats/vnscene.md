# Formato intermedio común: VNSCENE

> Contrato 1 del ecosistema. Independiente de consola. Versionado.

## 1. Estructura general

```json
{
  "game": "nombre_del_juego",
  "format_version": 1,
  "engine_min_version": "1.0",
  "entry": "start",
  "scenes": [ ... ],
  "assets": { ... },
  "audio": { ... },
  "variables": { ... }
}
```

## 2. Escena

```json
{
  "id": "start",
  "operations": [
    { "op": "background", "asset": "school" },
    { "op": "show", "asset": "character_neutral", "at": "center" },
    { "op": "dialogue", "speaker": "character", "text": "Hola, ¿cómo estás?" },
    { "op": "choice", "options": [
        { "text": "Bien", "target": "answer_good" },
        { "text": "Mal", "target": "answer_bad" }
    ]}
  ]
}
```

## 3. Lista de ops (basada en bytecode VNB v2)

### Control de flujo
- `label`, `jump`, `call`, `return`, `if`, `else`, `endif`, `choice`

### Escena y visuales
- `background`, `show`, `hide`, `scene`, `camera`, `transition`

### Diálogo y texto
- `dialogue`, `narrator`, `text_tag`, `window`

### Audio
- `music`, `ambient`, `sfx`, `voice`

### Variables y estado
- `set`, `add`, `sub`, `mul`, `div`, `persistent`

### Guardado
- `save`, `load`, `checkpoint`

### Especiales
- `special`, `video`, `input`, `imagemap`

### Animación (ATL)
- `anim`, `anim_event`, `loop`

## 4. Validación

El conversor debe validar el VNSCENE contra un schema JSON antes de generarlo.
Los backends deben rechazar formatos con `format_version` no soportada.

## 5. Generación de bytecode

El compilador VNB lee VNSCENE y genera VNB (bytecode) para el motor.
Backends que no usan VNB (PC, herramientas) pueden consumir VNSCENE directamente.

## 6. Notas

- Este formato es el contrato entre el conversor y el motor.
- Cambiarlo implica actualizar compilador, simulador y motor juntos.
- Versión actual: 1 (borrador).
