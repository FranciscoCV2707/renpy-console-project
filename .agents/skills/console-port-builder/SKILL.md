---
name: console-port-builder
description: Compila el núcleo y los datos de un juego para una consola concreta (PS1 con PSn00bSDK; el resto con la imagen Docker documentada en docs/platforms/<plataforma>.md). Úsala para cualquier build de consola, error de compilación o empaquetado.
---
# Constructor de ports

## PS1 (nativo, MSYS2)
- Compilador: `C:\msys64\usr\local\psn00bsdk\bin\mipsel-none-elf-gcc.exe`; flags en `docs/core-api.md`.
- Hasta que este repo tenga su CMake (Fase 1, T-104), el build completo es el de `E:\Dev\vn-engine-ps1`:
  `cmake --preset default` y `cmake --build build` (Snoot), `cmake --preset wani` y `cmake --build build/wani`.

## Otras consolas (Docker)
- Siempre en Docker (o WSL2 si el doc de la plataforma lo dice). Nunca instalar SDKs en Windows.
- El comando oficial de cada plataforma está en `docs/platforms/<plataforma>.md`; si no existe, créalo.
- Fijar la etiqueta o el digest de la imagen en ese doc.
- Patrón: `docker run --rm -v "${PWD}:/src" -w /src <imagen> make -C platforms/<plataforma> [TESTMODE=1]`.
- Docker Desktop tiene que estar abierto (`docker info` responde).

## Perfiles
- `release`: sin trazas.
- `testmode`: entradas guionadas (como `AUTOTEST.BIN` en PS1) y salida TRACE (`PLAN.md` sección 4.1).

## Diagnóstico
1. Leer el primer error, no el último.
2. Enlazado: orden de bibliotecas y operaciones de `vn_platform.h` sin implementar.
3. Memoria (sección desbordada): presupuesto en `docs/platform-matrix.md` y el reporte de recursos.
