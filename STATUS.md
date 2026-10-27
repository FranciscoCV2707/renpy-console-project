# STATUS — renpy-console-project

## Fecha: 2026-10-27

> Para retomar después de formatear o en otra PC: `CONTINUAR.md`. Qué instalar y qué respaldar: `REINSTALAR.md`.
> Repositorio remoto: `git@github.com:FranciscoCV2707/renpy-console-project.git`.

## Fase actual
Fases 4-7 en paralelo (D20). Solo Snoot Game, solo en español (D13, D16). `chapter_x2` PASS contra Ren'Py en PS1, PC,
PSP, PS2, Vita, 3DS, Wii, PS4, DS y GBA. PS3 en pausa. Xbox clásica y Switch compilan y esperan archivos del usuario.
G1, G2 y G3 cumplidas; G5 en medición. Desde D24 un port solo cuenta si es fiel (fondo, personajes y música por línea,
no solo texto) y fluido; desde D25 las imágenes se cargan al mostrarse y se liberan al dejar de verse.

## Tabla por consola

| Consola | Emulador | `chapter_x2` | Notas |
|---|---|---|---|
| PS1 | PCSX-Redux | PASS | 13-14 rutas PASS (G3) |
| PC (banco de pruebas) | — | PASS | Las 14 rutas PASS en texto; `renpy_full` 0 diferencias en x1-x6, x9 |
| PSP | PPSSPP | PASS | 10/11 capítulos; ruta-1 se traba por la panorámica 1328×383 (textura máx. 512): T-629 |
| PS2 | PCSX2 | PASS | 10/11 capítulos; muy lenta (~2 eventos/s) |
| Vita | Vita3K | PASS | Renderer GXM sin `libshacccg.suprx`; la captura interna sale negra |
| 3DS | Azahar | PASS | Traza por `svcOutputDebugString` |
| Wii | Dolphin | PASS | Traza por USB Gecko |
| PS4 | shadPS4 | PASS | dlmalloc propio (`MMAP_CLEARS=0`), traza `[stdin]` |
| DS | melonDS | PASS | Núcleo compartido; traza por la SD (DLDI); escena y diálogo verificados a ojo |
| GBA | mGBA | PASS | Núcleo compartido con datos en el ROM (GBFS); escena y diálogo verificados a ojo |
| PS3 | RPCS3 | — | En pausa: el flip del RSX se detiene (T-627) |
| Xbox clásica | xemu | — | Compila; falta MCPX y BIOS del usuario |
| Switch | — | — | Compila; faltan `prod.keys` y firmware del usuario |
| GB/GBC | SameBoy | — | Presupuesto y empaquetador hechos; falta motor |
| Xbox One/Series | — | — | Al final (Visual Studio UWP > 10 GB, modo desarrollador) |

## Hecho (resumen; detalle en `docs/bitacora.md` y `PLAN.md` sección 6)
- [x] Núcleo C99 compartido (`engine/`), backend PS1 y backend SDL (`platforms/sdl/`, un bloque por consola en
  `sdl_target.h`) usado por PC, PSP, PS2, Vita, 3DS, Wii, Xbox, Switch, PS4 y PS3. Backends propios para DS y GBA.
- [x] Test Lab (`python -m tools.ctl`): adapters para ps1, pc, psp, ps2, vita, 3ds, wii, ps4, ps3, ds y gba.
- [x] Trazas de Ren'Py de las 14 rutas (`tools/renpy_trace`), regrabadas con el hook que registra cambios de expresión,
  música por canal (stems) y `scene` real.
- [x] Comparación `renpy` (texto) y `renpy_full` (fondo, personajes y música por línea, T-623/T-624/T-628).
  Herramienta `python -m tools.ctl.full_diff <traza> --reference <ref>`.
- [x] Demakes: LZ77 de GBA/DS corregido (banderas de GBATEK, distancia ≥ 2 para VRAM); empaquetadores de GBA, GB y DS.
- [x] Backend SDL: sonidos ambientales fuera de la precarga de imágenes, caché negativo, liberación de texturas (T-622).
- [x] Agentes: `dispatch.py` con chequeo de calidad, mata el árbol de procesos al vencer, carpetas permitidas completas.

## En curso al cerrar la sesión (ramas `agent/*`)
- T-625 (OpenCode): chat del teléfono del capítulo 4 en cada consola.
- T-626 (OpenCode): teclado del anuario del capítulo 13D en cada consola, táctil en DS/3DS/Vita.
- T-627 (OpenCode): PS3, por qué el flip del RSX se detiene en RPCS3.
- T-629 (Kilo): imágenes solo mientras se ven (D25) y panorámicas en mosaicos; ruta-1 PASS en PSP.

## Pendientes
- Backend SDL: el tinte neutro 128 de PS1 se aplica como 128/255 en `SDL_SetTextureColorMod`
  (`platforms/sdl/video.c:233`): en todas las consolas SDL la imagen sale a la mitad de brillo. Encontrado en T-712.
- `renpy_full` en las rutas largas: 5.800-8.200 diferencias por ruta sin clasificar; x10 tiene 144 por las tomas de
  cámara que el compilador de PS1 pre-dibuja (`camera shot NNN`); x7: 3; x8: 2.
- PS2 lenta en PCSX2; Vita: captura interna negra; PS3 en pausa.
- Recursos originales (no los del disco de PS1) en las consolas con memoria de sobra (D24, después de G5).
- Motor de GB/GBC; Xbox One/Series al final.
- El repo mezcla CRLF y LF. Propuesta: `.gitattributes` con `eol=lf` y renormalizar.
- Revisar a ojo las capturas que reporten los agentes: Antigravity describió tres veces capturas que no coincidían.

## Avisos
- `psxavenc.exe` termina con 0xC0000139 al convertir audio: rompe 1 prueba de wani-ps1. No lo causaron los cambios de
  rutas.
- Beam con `beam-free` dejó de responder el 2026-10-27; los agentes de OpenCode usan `opencode-go/iceman-contributor-free`.
