# Investigación de Plataforma: PlayStation 5 (PS5)

> **Estado:** Fase de Investigación (PLAN.md sección 5, Nivel R)  
> **Fecha de verificación:** 2026-10-27  
> **Factibilidad general:** Difícil / Alto costo (Esfuerzo L) por ausencia de emulador para pruebas automáticas y ecosistema en fase temprana.

---

## 1. Resumen de Factibilidad

Aunque existen avances notables en la escena homebrew de PlayStation 5 —destacando el kit de desarrollo **`ps5-payload-sdk`** de John Törnblom y un puerto experimental de **SDL2**—, la plataforma presenta barreras críticas para el proyecto. La principal de ellas es la **ausencia total de un emulador funcional** que permita ejecutar pruebas automáticas e integración continua (`tools/ctl`). Además, el despliegue en hardware real depende de vulnerabilidades muy específicas de firmware y métodos de carga de payloads en memoria en lugar de paquetes instalables estándar.

---

## 2. SDK y Toolchain

* **SDK Homebrew Experimental:** **`ps5-payload-sdk`** (desarrollado por John Törnblom y la organización `ps5-payload-dev`).
  * Repositorio oficial: [github.com/ps5-payload-dev/sdk](https://github.com/ps5-payload-dev/sdk) (verificado: 2026-10-27).
  * Arquitectura objetivo: Arquitectura x86_64 AMD Zen 2 sobre Prospero OS (núcleo basado en FreeBSD).
  * Características: A diferencia de SDKs estáticos tradicionales, se apoya en enlace dinámico contra bibliotecas del sistema (`.sprx`). Utiliza Clang/LLVM estándar (`clang-18`, `lld-18`) como compilador de C/C++.
* **SDK Oficial (PlayStation 5 SDK / Prospero SDK):** Terminantemente prohibido por violaciones de derechos de autor y acuerdos NDA con Sony.

---

## 3. Estado de SDL2

* **Disponibilidad:** Experimental. Existe una bifurcación de SDL2 específicamente adaptada para interactuar con `ps5-payload-sdk`.
  * Repositorio: [github.com/ps5-payload-dev/SDL](https://github.com/ps5-payload-dev/SDL) (verificado: 2026-10-27).
* **Subsistemas implementados:**
  * **Video:** Ventanas y renderizado gráfico adaptados a las primitivas y superficies nativas de Prospero OS.
  * **Audio:** Salida de sonido básica enlazada dinámicamente con los módulos de audio de la consola.
  * **Entrada:** Mapeo básico de controles DualSense mediante stubs del sistema.
* **Estado:** Es funcional para aplicaciones sencillas y emuladores tipo RetroArch/vkQuake, pero no está consolidado ni disponible en la rama upstream oficial de libsdl-org.

---

## 4. Entorno de Compilación en Docker

* **Estado de la imagen oficial:** No existe una imagen centralizada en Docker Hub publicada oficialmente por el proyecto `ps5-payload-dev` (**sin confirmar** imagen oficial única).
* **Soluciones comunitarias en Docker:**
  * Diversos proyectos comunitarios (como `itsPLK/ps5-payload-manager`, [github.com/itsPLK/ps5-payload-manager](https://github.com/itsPLK/ps5-payload-manager)) implementan recetas `Dockerfile.sdk` basadas en Ubuntu (22.04 / 24.04 LTS), instalando el paquete de LLVM/Clang y compilando el SDK en `/opt/ps5-payload-sdk`.
* **Flujo de compilación:** Compilación de fuentes C99 con `clang` → enlace con `lld` → generación de un archivo binario ELF (`eboot.elf`) preparado para ser cargado por un cargador de payloads en red.

---

## 5. Emulación y Pruebas Automatizadas (Test Lab / TRACE)

* **Disponibilidad de emulador:** **Descartado / Sin confirmar emulador funcional**.
  * No existe a la fecha ningún emulador de PS5 capaz de arrancar y ejecutar aplicaciones gráficas o juegos comerciales/homebrew de forma funcional.
  * Proyectos como *Kyty* (que aspiraba a emular PS4/PS5) quedaron descontinuados y no lograron compatibilidad con la capa gráfica de PS5.
  * Proyectos tempranos como *RPCSX* se encuentran en fases conceptuales o embrionarias.
  * Emuladores como *shadPS4* están diseñados exclusivamente para PS4 y no ejecutan binarios de Prospero/PS5.
* **Impacto en el proyecto:** Al no existir emulador, **no es posible cumplir las compuertas de verificación ni integrar la consola en `tools/ctl`** sin contar con hardware físico dedicado y cableado.

---

## 6. Requisitos para el Usuario / Hardware Real

* **Consola y Firmware Vulnerable:**
  * Requiere una consola PS5 física en versiones de firmware muy restringidas:
    * Firmware 3.00 hasta 4.51: Vulnerabilidad WebKit / BD-JB con `ps5-payload-elfldr`.
    * Firmwares hasta 5.50 / 7.xx: Métodos emergentes tipo etaHEN o exploits de kernel en desarrollo.
  * La inmensa mayoría de las consolas de usuarios finales se encuentran en versiones superiores de firmware, imposibilitando la ejecución de homebrew.
* **Método de Carga:**
  * A diferencia de PS4 (donde existen instaladores FPKG bien establecidos), en PS5 el software se ejecuta típicamente transmitiendo el archivo ELF por red mediante herramientas como `ps5-payload-elfldr` o cargadores experimentales como ItemzFlow PS5.

---

## 7. Riesgos Legales

* **Evaluación de riesgo:** Moderado.
  * El código fuente de `ps5-payload-sdk` es de código abierto y no infringe directamente propiedad intelectual.
  * Sin embargo, debido a que PS5 es una consola comercial en activo y Sony combate activamente las cadenas de exploits y jailbreaks, el soporte y la distribución de payloads experimentales para vulnerabilidades de kernel en curso presenta fricciones adicionales frente a sistemas de generaciones previas.

---

## 8. Estimación de Esfuerzo

* **Estimación:** **L (Grande / Desaconsejado temporalmente)**
* **Justificación:**
  * **Barreras críticas:** Ausencia total de emulador para el Test Lab automático; necesidad de compilar y mantener una imagen Docker propia; ecosistema de carga de binarios en hardware sumamente fragmentado y reservado a una base de usuarios mínima con consolas sin actualizar.
  * **Recomendación:** Mantener la plataforma en estado de investigación pasiva hasta que surja un emulador con soporte headless en PC o se consolide un método de instalación permanente para el usuario final.

---

## 9. Fuentes Citadas

1. Repositorio oficial ps5-payload-sdk: `https://github.com/ps5-payload-dev/sdk` (2026-10-27).
2. Repositorio de SDL adaptado a PS5: `https://github.com/ps5-payload-dev/SDL` (2026-10-27).
3. Ecosistema de herramientas ps5-payload-elfldr y ps5-payload-manager: `https://github.com/itsPLK/ps5-payload-manager` (2026-10-27).
4. Estado de compatibilidad de emuladores de PS5: Estado general verificado en bases de datos comunitarias (sin emulador funcional operativo: 2026-10-27).
