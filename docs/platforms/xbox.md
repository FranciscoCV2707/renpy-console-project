# Xbox clásica — Toolchain Docker (nxdk)

## Imagen Docker

- Imagen: `xboxdev/nxdk@sha256:14aeace40a9aa3ffdf14501827459cb2ab04766e836200228d87bfeb52f7f6ed`
- Etiqueta de origen: `xboxdev/nxdk:latest`
- Digest: `sha256:14aeace40a9aa3ffdf14501827459cb2ab04766e836200228d87bfeb52f7f6ed`
- Tamaño: ~301 MB
- Fuente: https://hub.docker.com/r/xboxdev/nxdk y https://github.com/XboxDev/nxdk (Dockerfile en el repositorio).
- Comprobar localmente:

```sh
docker pull xboxdev/nxdk@sha256:14aeace40a9aa3ffdf14501827459cb2ab04766e836200228d87bfeb52f7f6ed
docker inspect --format "{{index .RepoDigests 0}}" xboxdev/nxdk:latest
```

## Toolchain incluido

- Compilador: `nxdk-cc` (clang 20.1.6, objetivo i386-pc-windows-msvc) y `nxdk-cxx`.
- Enlazador: `nxdk-link` (lld con `-merge:.edata=.edataxb`).
- SDL2 propio de nxdk en `/usr/src/nxdk/lib/sdl/SDL2` (cabeceras directamente en `include/`, sin prefijo `SDL2/`).
- Empaquetado: `cxbe` genera `default.xbe`; `extract-xiso` puede generar una ISO XISO desde la carpeta de salida.
- Macro del SDK disponible en el código: `NXDK` (definida por `nxdk-cc`; se usa `#ifdef NXDK` en `platforms/sdl`).
- `make` incluido.

## Compilación

```sh
python platforms/xbox/build.py --trace
```

La salida es `build/xbox/default.xbe` (y la carpeta `build/xbox/` sirve para generar una ISO XISO).

Los datos del disco de PS1 se leen desde `D:\data\` (variable de entorno `VN_DATA_DIR` para otra ruta).

## Instalación en la consola o en xemu

- Emulador de prueba: xemu (https://xemu.app). xemu necesita la BIOS y el disco duro del usuario; no se descargan
  ni se redistribuyen aquí, solo documenta qué hace falta.
- Copiar `build/xbox/default.xbe` (o la ISO generada) a la ubicación que use xemu y arrancarlo.
- Salida de traza: `DbgPrint` (por verificar en hardware/emulador); el motor emite `T|...` por `vn_ops->log` en
  builds de prueba (`VN_TRACE`).

## Lo que falta para correrlo con `tools/ctl`

- Adapter `ctl` para Xbox/xemu no implementado en esta tarea (igual que el resto del nivel A).
- No hay extracción automática de traza desde xemu ni comparación contra la referencia.<|end|><|start|>write to=assistant<|channel|>analysis<|message|>Now update platform-matrix row for Xbox clásica. Task says "solo la fila de Xbox clásica". Update estado maybe "Compila con nxdk (Docker), pendiente de xemu". Let's edit row.<|end|><|start|>assist<|channel|>analysis <|constrain|>xml<|message|><rfl:parameter name="path">
E:\Dev\renpy-console-wt\T-604-beam\docs\platform-matrix.md
