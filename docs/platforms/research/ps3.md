# Investigación de Plataforma: PlayStation 3 (PS3)

> **Estado:** Fase de Investigación (PLAN.md sección 5, Nivel R)  
> **Fecha de verificación:** 2026-10-27  
> **Factibilidad general:** Viable (Esfuerzo M) con backend SDL2 sobre PSL1GHT v2.

---

## 1. Resumen de Factibilidad

Portar Snoot Game a PS3 es técnicamente factible utilizando el backend SDL compartido del proyecto (`platforms/sdl`). La consola cuenta con un SDK homebrew maduro y limpio de código propietario (**PSL1GHT v2**) y adaptaciones existentes de **SDL2** para esta plataforma. La verificación automatizada es posible gracias a las capacidades de línea de comandos y ejecución headless del emulador **RPCS3**.

---

## 2. SDK y Toolchain

* **SDK Homebrew:** **PSL1GHT v2** (mantenido por la organización `ps3dev` en GitHub).
  * Repositorio: [github.com/ps3dev/PSL1GHT](https://github.com/ps3dev/PSL1GHT) (verificado: 2026-10-27).
  * Arquitectura objetivo: CPU Cell Broadband Engine (PPU PowerPC 64 bits de dos hilos + 6/7 coprocesadores SPU vectoriales).
  * Compilador: `powerpc64-ps3-elf-gcc` / `ppu-gcc` incluido en el conjunto `ps3toolchain` (`ps3dev/ps3toolchain`).
* **SDK Oficial (Cell OS Lv-2 SDK):** Prohibido por contener código propietario bajo NDA de Sony Interactive Entertainment.

---

## 3. Estado de SDL2

* **Disponibilidad:** SDL2 ha sido adaptado de forma comunitaria a PSL1GHT; no está upstreamed en la rama principal de libsdl-org, pero existen puertos funcionales y estables.
  * Puerto de referencia: [github.com/sergiou87/SDL2_PSL1GHT](https://github.com/sergiou87/SDL2_PSL1GHT) y ramas comunitarias en [github.com/ps3aqua/SDL2_PSL1GHT](https://github.com/ps3aqua/SDL2_PSL1GHT) (verificado: 2026-10-27).
* **Subsistemas implementados:**
  * **Video:** Renderizado acelerado 2D/3D mapeado sobre la GPU RSX mediante bibliotecas como `tiny3D` o llamadas de bajo nivel a la RSX (`librsx` / `rsxgl`). También admite buffer de cuadros por software.
  * **Audio:** Salida directa mediante el subsistema de audio nativo de Cell OS (`sys_audio`).
  * **Entrada:** Soporte para mandos Sixaxis / DualShock 3 a través de `sys/pad` de PSL1GHT.
* **Compatibilidad con Snoot:** El backend SDL2 existente en `platforms/sdl` puede enlazarse contra esta biblioteca sin modificaciones arquitectónicas sustanciales en el bucle principal o en la gestión de eventos.

---

## 4. Entorno de Compilación en Docker

* **Imágenes Docker disponibles:**
  * `psl1ght/psl1ght` y `psl1ght/psl1ght-dev` en Docker Hub: [hub.docker.com/r/psl1ght/psl1ght](https://hub.docker.com/r/psl1ght/psl1ght) (verificado: 2026-10-27).
  * `wargio/ps3sdk-docker`: Contenedor integral preconfigurado con `ps3toolchain`, PSL1GHT v2, `tiny3D` y librerías auxiliares.
* **Ruta de instalación típica en contenedor:** `/usr/local/ps3dev` (`PS3DEV`).
* **Flujo de compilación:** Código C99 del núcleo + backend SDL compilado con `ppu-gcc` → binario ELF PPU (`EBOOT.ELF`) → empaquetado como archivo ejecutable autofirmado (`EBOOT.BIN` vía `make_fself`) → paquete instalable `.pkg`.

---

## 5. Emulación y Pruebas Automatizadas (Test Lab / TRACE)

* **Emulador principal:** **RPCS3** ([github.com/RPCS3/rpcs3](https://github.com/RPCS3/rpcs3) y [rpcs3.net](https://rpcs3.net), verificado: 2026-10-27).
* **Soporte CLI / Headless:**
  * RPCS3 soporta ejecución directa desde terminal mediante `--headless` (o `--no-gui` en versiones legacy) pasando la ruta del ejecutable o carpeta del juego:
    ```bash
    rpcs3.exe --headless "build/ps3/disc/USRDIR/EBOOT.BIN"
    ```
  * Permite configurar salida automática al terminar la ejecución del proceso (`Exit RPCS3 when process finishes`).
* **Captura de trazas TRACE:** RPCS3 vuelca la salida de depuración y `stdout` de la aplicación a su archivo de registro `RPCS3.log` y a la consola TTY, permitiendo la integración directa con `tools/ctl` para comparar trazas de regresión contra Ren'Py y PS1.
* **Firmware requerido:** RPCS3 requiere la instalación del firmware oficial de PS3 (`PS3UPDAT.PUP`), distribuido públicamente y sin coste por Sony en su sitio oficial.

---

## 6. Requisitos para el Usuario / Hardware Real

* **Consola con Jailbreak / Exploit:**
  * Consolas compatibles con Custom Firmware (CFW, ej. Evilnat Cobra 4.91): Modelos Fat y Slim iniciales (CECH-20xx/21xx y parte de 25xx).
  * Consolas incompatibles con CFW permanente (Slim tardías CECH-30xx y SuperSlim CECH-40xx): Requieren **PS3HEN** (Homebrew Enabler), instalable por navegador web sin modificar hardware.
* **Instalación de software:**
  * Paquete `.pkg` firmado con claves públicas homebrew ("fself" / claves libres), instalable directamente desde el menú XMB en la sección *Package Manager* mediante una memoria USB.
  * No se requieren claves privadas filtradas ni cuentas especiales de desarrollador.

---

## 7. Riesgos Legales

* **Bajo riesgo:**
  * PSL1GHT v2 y `ps3toolchain` son implementaciones limpias de ingeniería inversa ("clean-room") con licencia de código abierto (BSD/MIT).
  * Las herramientas de firmado de binarios homebrew (`make_fself_npdrm`, `pkg-maker`) utilizan claves públicas y pseudofirmas aceptadas por CFW y HEN, sin eludir medidas tecnológicas mediante el uso de secretos comerciales bajo litigio.
  * Para emulación en CI/RPCS3, el firmware oficial se descarga directamente desde los servidores de Sony de acuerdo con los términos de RPCS3.

---

## 8. Estimación de Esfuerzo

* **Estimación:** **M (Mediano)**
* **Justificación:**
  * **Puntos a favor:** SDL2 ya fue portado a PSL1GHT; RPCS3 permite automatizar pruebas por CLI; el hardware (256 MB de RAM del sistema + 256 MB de VRAM) supera con holgura los requisitos de Snoot.
  * **Trabajo necesario:** Construir y mantener la imagen Docker con el puerto de SDL2 y `tiny3D` precompilados; escribir el Makefile/script de empaquetado a `.pkg`; configurar el adaptador de RPCS3 en `tools/ctl` para canalizar las trazas TRACE.

---

## 9. Fuentes Citadas

1. Repositorio oficial PSL1GHT v2: `https://github.com/ps3dev/PSL1GHT` (2026-10-27).
2. Adaptación de SDL2 a PSL1GHT por sergiou87: `https://github.com/sergiou87/SDL2_PSL1GHT` (2026-10-27).
3. Repositorio de SDL2_PSL1GHT (ps3aqua): `https://github.com/ps3aqua/SDL2_PSL1GHT` (2026-10-27).
4. Imágenes de Docker Hub para PS3dev: `https://hub.docker.com/r/psl1ght/psl1ght` (2026-10-27).
5. Documentación de CLI y emulador RPCS3: `https://rpcs3.net` y `https://github.com/RPCS3/rpcs3` (2026-10-27).
