# Bitácora — renpy-console-project

## 2026-10-26
- `git init` y commit inicial; rutas de `C:\Users\Pako\Desktop\snoot` cambiadas a `E:\snoot`.
- Extraídos a `engine/core/` los módulos sin hardware de `ps1-base` (`vm`, `scene`, `str`, `lz4`,
  `opcodes.h`, `vn_limits.h`). Compilan en host con `C:\msys64\ucrt64\bin\gcc.exe -std=c99 -Wall -Wextra -pedantic`.
- Pendiente: no hay `.venv` ni pytest (el Python del sistema es 3.14, el proyecto pide 3.12).
- Commit inicial reescrito sin línea de coautor (regla del proyecto).
- Contrato `VnPlatformOps` movido a `engine/core/vn_platform.h` y ampliado con archivos y fuente. `chapter.c` y
  `text.c` ya no incluyen nada de PS1. Hardware (`audio`, `cd`, `img`, `input`, `res`, `save`, `video`,
  `video_clip`) copiado a `platforms/ps1/` con `backend_ps1.c`.
- Cambio de conducta: `font_load` ahora rechaza un `FONT.BIN` más corto que su atlas (antes leía de más).
- Prueba host `tests/core/test_core_host.c` pasa con los datos de Wani; el núcleo y el backend PS1 compilan con
  `mipsel-none-elf-gcc`. No hay ejecutable PS1 todavía (falta `main.c`), así que no se probó en emulador.
- Referencias: base = `vn-engine-ps1` (`947cb3b`); `snoot-ps1/engine` = motor v1.0, solo referencia.
