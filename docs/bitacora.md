# Bitácora — renpy-console-project

## 2026-10-26
- `git init` y commit inicial; rutas de `C:\Users\Pako\Desktop\snoot` cambiadas a `E:\snoot`.
- Extraídos a `engine/core/` los módulos sin hardware de `ps1-base` (`vm`, `scene`, `str`, `lz4`,
  `opcodes.h`, `vn_limits.h`). Compilan en host con `C:\msys64\ucrt64\bin\gcc.exe -std=c99 -Wall -Wextra -pedantic`.
- Pendiente: no hay `.venv` ni pytest (el Python del sistema es 3.14, el proyecto pide 3.12).
