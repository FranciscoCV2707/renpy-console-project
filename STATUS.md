# STATUS — renpy-console-project

## Fecha: 2026-10-25

## Estado actual
- Repositorio creado en `E:\Dev\renpy-console-project`.
- Plan maestro escrito (`PLAN.md`, v0.1 extendido).
- CLAUDE.md y reglas de agentes creadas.
- Estructura de directorios creada (tools/, engine/, platforms/, tests/, docs/).
- Contratos iniciales: `engine/core/vn_core.h` (Contrato 2), `platforms/pc/backend.h/.c` (Contrato 3 parcial), `tests/scenarios/snoot_intro.yaml` (Contrato 4), `docs/formats/vnscene.md` (Contrato 1).
- Console Test Lab: esqueleto CLI en `tools/console-test-lab/cli.py`.
- Motor base copiado en `engine/ps1-base/` (copia de `vn-engine-ps1`, solo lectura de referencia).
- Documentación adicional: `docs/what-to-download.md`, `docs/core-api.md`, `docs/platform-matrix.md`.
- Lista de descargas por fase documentada en `docs/what-to-download.md`.

## Fase actual
Fase 1 — Consolidar PS1 y crear referencia para PC (en progreso).

## Hecho
- [x] Análisis de `E:\Dev` y `E:\snoot`.
- [x] Plan maestro con arquitectura, matriz de plataformas, contratos, roadmap, tareas.
- [x] Estructura de directorios creada.
- [x] Contratos iniciales escritos (headers + esqueletos).
- [x] Motor base copiado (`engine/ps1-base/`).
- [x] Lista de descargas y matriz de plataformas documentadas.

## Siguiente
- [x] Crear `docs/core-api.md` (borrador).
- [x] Extraer a `engine/core/` los módulos sin hardware: `vm`, `scene`, `str`, `lz4`, `opcodes.h`, `vn_limits.h`.
  Copia exacta de `ps1-base`; compilan en host con `gcc -std=c99 -Wall -Wextra -pedantic` sin avisos.
- [x] `VnPlatformOps` ampliado con archivos y fuente (`engine/core/vn_platform.h`); `chapter` y `text` en el
  núcleo sobre `vn_ops`.
- [x] Backend PS1 (`platforms/ps1/backend_ps1.c`) con los módulos de hardware copiados; compila con PSn00bSDK.
- [x] Backend PC sin ventana (archivos desde carpeta, cuenta glifos) y prueba `tests/core/test_core_host.c`:
  pasa con los datos de Wani (`E:\Dev\wani-ps1\build\fase0`).
- [ ] Extraer `app/main.c` (bucle, menús, guardado) y enlazar un ejecutable PS1 con este núcleo.
- [ ] Ops de imágenes y audio cuando el núcleo las necesite (al extraer `main.c`).
- [ ] Backend PC con SDL2 (falta descargar SDL2 dev).
- [ ] Crear backend PC con SDL2 para pruebas rápidas.
- [ ] No tocar repos hermanos.
