# Investigación de Plataforma: PlayStation 4 (PS4)

> **Estado:** Fase de Investigación (PLAN.md sección 5, Nivel R)  
> **Fecha de verificación:** 2026-10-27  
> **Factibilidad general:** Altamente Viable (Esfuerzo M) con backend SDL2 sobre OpenOrbis PS4 Toolchain.

---

## 1. Resumen de Factibilidad

Portar Snoot Game a PS4 es una opción sólida gracias a la arquitectura x86_64 compartida con PC y a la existencia del **OpenOrbis PS4 Toolchain**, un SDK homebrew abierto basado en LLVM/Clang. El ecosistema cuenta con un puerto maduro de **SDL2** y herramientas comunitarias para empaquetar paquetes instalables Fake PKG (`.pkg`). Para pruebas automáticas, emuladores emergentes de código abierto como **shadPS4** y **fpPS4** proporcionan soporte para ejecución por terminal y salida de trazas.

---

## 2. SDK y Toolchain

* **SDK Homebrew:** **OpenOrbis PS4 Toolchain** (OoSDK).
  * Repositorio: [github.com/OpenOrbis/OpenOrbis-PS4-Toolchain](https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain) (verificado: 2026-10-27).
  * Licencia: BSD de 3 cláusulas.
  * Base técnica: LLVM/Clang configurado para el sistema operativo Orbis OS (derivado de FreeBSD 9).
  * Generación de stubs: Herramienta `orbis-lib-gen` para enlazar con bibliotecas del sistema (`libkernel`, `libScePad`, `libSceVideoOut`, `libSceAudioOut`).
  * Empaquetado: Incluye `create-eboot` y `create-pkg` para generar `eboot.bin`, `param.sfo` y archivos `.pkg` finales.
* **SDK Oficial (PlayStation 4 SDK):** Prohibido por infringir acuerdos de confidencialidad (NDA) y leyes de propiedad intelectual.

---

## 3. Estado de SDL2

* **Disponibilidad:** Excelente. OpenOrbis cuenta con integración nativa de **SDL2** dentro de su árbol de ejemplos y paquetes de puertos comunitarios.
  * Puerto inicial integrado por `znullptr` dentro de `/samples/sdl2/` en el repositorio oficial de OpenOrbis.
  * Paquete administrado en repositorios comunitarios como Pacbrew (`ps4-openorbis-portlibs` con SDL2, SDL2_image, SDL2_mixer, SDL2_ttf).
* **Subsistemas implementados:**
  * **Video:** Renderizado 2D/3D acelerado utilizando `libSceVideoOut` directamente o capa intermedia OpenGL ES (Piglet / Mesa wrapper). El renderizado por software (`SDL_RENDERER_SOFTWARE`) es directamente soportado.
  * **Audio:** Soporte completo mediante `libSceAudioOut`.
  * **Entrada:** Soporte para el mando DualShock 4 mediante la biblioteca nativa `libScePad`.
* **Compatibilidad con Snoot:** El código del backend `platforms/sdl` compila de manera casi directa dada la coincidencia de arquitectura (x86_64, enteros de 64 bits, endianness little-endian).

---

## 4. Entorno de Compilación en Docker

* **Soporte Docker oficial:** El repositorio de OpenOrbis contiene un `Dockerfile` en su raíz y documentación dedicada (`DOCKER.md`):
  * [github.com/OpenOrbis/OpenOrbis-PS4-Toolchain/blob/master/DOCKER.md](https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain/blob/master/DOCKER.md).
* **Imágenes comunitarias en Docker Hub:**
  * `xfangfang/pacbrew`: Imagen que incluye la cadena de herramientas `ps4-openorbis` y los `portlibs` de SDL2 precompilados vía gestor `pacman` ([hub.docker.com/r/xfangfang/pacbrew](https://hub.docker.com/r/xfangfang/pacbrew), verificado: 2026-10-27).
* **Flujo de compilación:**
  * Montaje de volumen local → compilación con `clang` objetivo `x86_64-scei-ps4` → generación de ELF → firma con `create-eboot` → empaquetado en `.pkg` mediante `create-pkg`.

---

## 5. Emulación y Pruebas Automatizadas (Test Lab / TRACE)

* **Emulador principal 1 (Recomendado):** **shadPS4** ([github.com/shadps4-emu/shadPS4](https://github.com/shadps4-emu/shadPS4) y [shadps4.net](https://shadps4.net), verificado: 2026-10-27).
  * Emulador de PS4 de rápido avance compatible con ejecución CLI:
    ```bash
    shadps4.exe --game="build/ps4/disc/eboot.bin" --log-level=info
    ```
  * Dispone de compilaciones basadas en terminal/SDL aptas para integración continua.
* **Emulador complementario 2:** **fpPS4** ([github.com/red-prig/fpPS4](https://github.com/red-prig/fpPS4), verificado: 2026-10-27).
  * Emulador escrito en Free Pascal, altamente compatible con juegos 2D, títulos indie y homebrew de OpenOrbis con salida directa a consola.
* **Captura de trazas TRACE:** Tanto shadPS4 como fpPS4 redirigen la salida de consola de `eboot.bin` a registros de texto locales o `stdout`, permitiendo recolectar trazas con el protocolo TRACE del proyecto.

---

## 6. Requisitos para el Usuario / Hardware Real

* **Consola con Jailbreak / Exploit:**
  * Requiere una PS4 (Fat, Slim o Pro) en una versión de firmware vulnerable:
    * Firmware <= 9.00: Exploit pOOBs4 (vía WebKit + USB exFAT) o GoldHEN.
    * Firmware <= 11.00: Exploit PPPwn (ejecutable mediante conexión Ethernet).
* **Carga de software:**
  * Se empaqueta como Fake PKG (FPKG). Se copia a un disco USB o se transfiere vía red (Remote PKG Installer) y se instala mediante el instalador de paquetes de GoldHEN.
  * No requiere cuentas de desarrollador de Sony ni modificación física de hardware.

---

## 7. Riesgos Legales

* **Bajo riesgo:**
  * OpenOrbis Toolchain ha sido desarrollado mediante técnicas de ingeniería inversa en sala limpia ("clean-room"), sin utilizar código fuente protegido de Sony.
  * La herramienta `create-pkg` firma paquetes con claves públicas o "passcode fake" compatibles con cargadores homebrew como GoldHEN, sin descifrar ni distribuir claves propietarias ilegales.
  * Los activos del juego permanecen bajo las licencias AGPL-3.0 y CC-BY-SA 4.0 acordadas en el proyecto.

---

## 8. Estimación de Esfuerzo

* **Estimación:** **M (Mediano)**
* **Justificación:**
  * **Puntos a favor:** SDL2 totalmente funcional en OpenOrbis; arquitectura x86_64 idéntica a PC; memoria de 8 GB GDDR5 elimina cualquier limitación presupuestaria; emulación factible en shadPS4/fpPS4 para CI.
  * **Trabajo necesario:** Poner a punto el pipeline de empaquetado FPKG (`create-pkg`) y adaptar el lanzador en `tools/ctl` para coordinar la ejecución headless en shadPS4 y la recolección de trazas.

---

## 9. Fuentes Citadas

1. Repositorio OpenOrbis PS4 Toolchain: `https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain` (2026-10-27).
2. Guía de integración Docker de OpenOrbis: `https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain/blob/master/DOCKER.md` (2026-10-27).
3. Repositorio de pacbrew (imágenes y portlibs): `https://hub.docker.com/r/xfangfang/pacbrew` (2026-10-27).
4. Emulador shadPS4 (releases y documentación CLI): `https://github.com/shadps4-emu/shadPS4` y `https://shadps4.net` (2026-10-27).
5. Emulador fpPS4: `https://github.com/red-prig/fpPS4` (2026-10-27).
