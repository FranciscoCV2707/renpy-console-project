# Investigación de Plataforma: Xbox 360

> **Estado:** Fase de Investigación (PLAN.md sección 5, Nivel R)  
> **Fecha de verificación:** 2026-10-27  
> **Factibilidad general:** Desaconsejado / Muy Alto Costo (Esfuerzo L) debido a falta de SDL2 para libxenon e incompatibilidad del emulador Xenia con binarios ELF bare-metal.

---

## 1. Resumen de Factibilidad

Intentar portar Snoot Game a Xbox 360 a través de la vía homebrew libre presenta obstáculos técnicos severos. El único SDK de código abierto sin ataduras legales con Microsoft es **libxenon**, una biblioteca "bare-metal" que se ejecuta directamente sobre el cargador XeLL. Sin embargo, libxenon **carece de un puerto de SDL2** (solo existe una adaptación antigua de SDL 1.2) y, de forma crítica, **el emulador Xenia es incapaz de ejecutar binarios ELF de libxenon**, lo que impide cualquier forma de prueba automatizada en CI.

---

## 2. SDK y Toolchain

* **SDK Homebrew Abierto:** **libxenon** (desarrollado por el proyecto Free60).
  * Repositorio: [github.com/Free60Project/libxenon](https://github.com/Free60Project/libxenon) (verificado: 2026-10-27).
  * Arquitectura objetivo: Procesador triple núcleo Xenon (PowerPC de 64 bits con extensiones AltiVec/VMX128).
  * Naturaleza técnica: Ejecución "bare-metal" (sin sistema operativo ni kernel retail de Xbox 360), arrancado directamente desde la memoria mediante el bootloader XeLL (Xenon Linux Loader).
  * Compilador: Toolchain GCC para PowerPC (`xenon-gcc` / `powerpc-elf-gcc`).
* **SDKs en desarrollo para kernel retail:**
  * Proyectos emergentes como `xsdk` ([github.com/xenosworks/xsdk](https://github.com/xenosworks/xsdk)) intentan crear un SDK limpio que genere ejecutables `.xex` para el kernel oficial, pero se encuentran en fase alfa experimental.
* **SDK Oficial (Microsoft XDK):** Estrictamente prohibido en el proyecto. Su uso infringe los contratos de Microsoft, requiere software confidencial filtrado y acarrea serios riesgos legales de propiedad intelectual.

---

## 3. Estado de SDL2

* **Disponibilidad:** **Inexistente / No disponible para libxenon**.
  * No existe ningún puerto funcional de SDL2 para libxenon ("sin confirmar" cualquier implementación funcional de SDL2 en libxenon).
  * La única biblioteca SDL portada a libxenon es la versión clásica **SDL 1.2** (`lantus/libSDLXenon`, [github.com/lantus/libSDLXenon](https://github.com/lantus/libSDLXenon)).
  * Nota sobre SDL 3: El proyecto experimental `xsdk` incluye un backend preliminar para SDL 3, pero no es compatible con libxenon ni con SDL2, y no se encuentra estabilizado.
* **Impacto en el backend del proyecto:** El backend unificado de Snoot (`platforms/sdl`) está diseñado sobre **SDL2** (`SDL_Renderer`, texturas RGBA, gestión moderna de audio y eventos). Adaptarlo a Xbox 360 obligaría a reescribir un backend específico para SDL 1.2 o desarrollar un controlador de video/audio completo para SDL2 sobre el hardware Xenos/EDRAM de libxenon.

---

## 4. Entorno de Compilación en Docker

* **Imágenes Docker disponibles:**
  * La organización Free60 mantiene imágenes en Docker Hub:
    * `free60/libxenon`: [hub.docker.com/u/free60](https://hub.docker.com/u/free60) (verificado: 2026-10-27).
    * `free60/toolchain`: Entorno base con la cadena de herramientas cruzada para compilación.
* **Flujo de compilación:** Código C → `xenon-gcc` → binario ELF de 32/64 bits para PowerPC (`snoot.elf`).

---

## 5. Emulación y Pruebas Automatizadas (Test Lab / TRACE)

* **Emulador principal de Xbox 360:** **Xenia** ([github.com/xenia-project/xenia](https://github.com/xenia-project/xenia) y [xenia.jp](https://xenia.jp), verificado: 2026-10-27).
* **Incompatibilidad arquitectónica crítica:**
  * Xenia es un emulador de alto nivel (HLE) del **sistema operativo retail de Xbox 360** y está diseñado exclusivamente para cargar ejecutables en formato **XEX** (`default.xex`) e imágenes de disco ISO/GOD.
  * **Xenia NO soporta ni ejecuta binarios ELF de libxenon**. Al intentar abrir un archivo ELF, el emulador se bloquea o arroja errores fatales de inicialización del kernel (ej. `C0000225`), dado que libxenon elude las llamadas de sistema del hipervisor oficial y realiza operaciones bare-metal sobre hardware no emulado por Xenia.
* **Consecuencia para el Test Lab:** Resulta imposible correr escenarios de prueba automatizados (`python -m tools.ctl run --target xbox360`) en entornos de integración continua o en PC sin depender de una consola física conectada por red.

---

## 6. Requisitos para el Usuario / Hardware Real

* **Modificación física de hardware:**
  * A diferencia de PS3 o PS4, una consola Xbox 360 comercial **no puede ejecutar código sin firmar mediante exploits de software**.
  * El usuario requiere obligatoriamente una consola con modificación física permanente: **JTAG** (en consolas muy antiguas con dashboard 7371 o inferior) o **RGH** (Reset Glitch Hack: RGH 1.2, RGH 2.0, RGH 3.0 mediante instalación de modchips o cableado con puente en la placa base).
* **Arranque:** El juego debe cargarse encendiendo la consola mediante el botón de expulsión de bandeja para invocar el bootloader **XeLL**, el cual busca y ejecuta archivos ELF desde una memoria USB formateada en FAT32.

---

## 7. Riesgos Legales

* **Uso de libxenon:** Limpio legalmente. Es código libre bajo licencias GPL/LGPL.
* **Riesgo en alternativas retail:** Para lograr que un juego corra en Xenia o en el dashboard estándar de Xbox 360 (Aurora/FreestyleDash), se requeriría compilar un ejecutable XEX. Históricamente, la inmensa mayoría de herramientas para crear XEX dependen de encabezados y bibliotecas filtradas del Microsoft XDK oficial, lo que constituye una infracción directa de propiedad intelectual inaceptable en este proyecto.

---

## 8. Estimación de Esfuerzo

* **Estimación:** **L (Grande / Desaconsejado)**
* **Justificación:**
  * Falta de puerto SDL2 para libxenon (exige portar SDL2 o retroceder a SDL 1.2).
  * Imposibilidad absoluta de emulación en Xenia con binarios ELF bare-metal, anulando la compuerta de pruebas automáticas del proyecto.
  * Requisito de modificación física por hardware (RGH) para el usuario final, reduciendo la audiencia a un nicho extremadamente técnico.

---

## 9. Fuentes Citadas

1. Repositorio libxenon de Free60Project: `https://github.com/Free60Project/libxenon` (2026-10-27).
2. Repositorio de libSDLXenon (SDL 1.2) por lantus: `https://github.com/lantus/libSDLXenon` (2026-10-27).
3. Imágenes oficiales de Docker Hub de Free60: `https://hub.docker.com/u/free60` (2026-10-27).
4. Proyecto de emulación Xenia y limitaciones de formato XEX vs ELF: `https://github.com/xenia-project/xenia` (2026-10-27).
5. Proyecto emergente xsdk para retail kernel: `https://github.com/xenosworks/xsdk` (2026-10-27).
