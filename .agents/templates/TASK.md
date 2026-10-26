# T-xxx — <título imperativo>

- **Estado:** todo | assigned | review | done | blocked
- **Agente:** beam | codex | kilo | vibe | agy | claude
- **Fase:** <n> (PLAN.md sección 6)
- **Depende de:** T-yyy, T-zzz

## Objetivo
<una o dos frases, resultado observable>

## Contexto mínimo
- Lee: <rutas exactas>
- Contrato a respetar: <engine/core/vn_platform.h, PLAN.md §4.1 TRACE, §4.2 escenarios, VNB>

## Archivos permitidos
- <rutas o globs>

## Archivos prohibidos
- engine/core/vn_platform.h, engine/ps1-base/**, tools/agents/agents.toml, repos hermanos, <otros>

## Pasos sugeridos
1. ...

## Verificación (comandos ejecutables)
```
.\.venv\Scripts\python.exe -m pytest
<comando 2>
```

## Definición de terminado
- [ ] ...
