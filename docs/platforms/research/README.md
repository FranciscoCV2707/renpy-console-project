# Investigación de Plataformas (Nivel R) — Snoot Game

> **Documento:** Informe de Factibilidad y Recomendación Estratégica  
> **Fase del Plan:** Fase de Investigación (PLAN.md sección 5, Nivel R)  
> **Fecha de verificación:** 2026-10-27  
> **Consolas evaluadas:** PlayStation 3, PlayStation 4, PlayStation 5, Xbox 360, Xbox One / Xbox Series X|S  

---

## 1. Objetivo y Contexto

El objetivo de esta investigación es determinar la viabilidad técnica, legal y operativa de portar **Snoot Game** a cinco plataformas de sobremesa utilizando el **backend SDL2 compartido** (`platforms/sdl`), así como definir los requisitos de toolchains, emuladores para pruebas automatizadas (`tools/ctl`) y experiencia para el usuario final.

---

## 2. Matriz Comparativa de Factibilidad

| Plataforma | SDK Recomendado | Estado de SDL2 | Toolchain / Docker | Emulador para CI (`tools/ctl`) | Requisitos Usuario | Riesgo Legal | Estimación de Esfuerzo |
|---|---|---|---|---|---|---|---|
| **Xbox One / Series X\|S** | UWP / WinRT (Microsoft) | **Excelente** (Upstream en `libsdl-org/SDL`, D3D11) | Local MSBuild o Docker Windows | Ejecución nativa en PC UWP + WDP en consola | Consola estándar de tienda + Dev Mode ($19) | Cero (Canal oficial) | **S (Pequeño)** |
| **PlayStation 4** | OpenOrbis Toolchain | **Bueno** (Integrado en muestras y `pacbrew`, video/audio OK) | Dockerfile oficial / `xfangfang/pacbrew` | **shadPS4** (`--game`, modo CLI) / fpPS4 | Consola con jailbreak (FW <= 11.00) + GoldHEN | Muy bajo (Clean-room) | **M (Mediano)** |
| **PlayStation 3** | PSL1GHT v2 | **Bueno** (Adaptado en `SDL2_PSL1GHT`, Tiny3D/RSX) | Docker `psl1ght/psl1ght` o `wargio/ps3sdk-docker` | **RPCS3** (`--headless`, logs en TTY) | Consola con CFW (Evilnat) o PS3HEN | Muy bajo (Clean-room) | **M (Mediano)** |
| **PlayStation 5** | `ps5-payload-sdk` | **Experimental** (Bifurcación en `ps5-payload-dev/SDL`) | Dockerfile comunitario (`Dockerfile.sdk`) | **Sin confirmar / Ninguno** (No hay emulador funcional) | Consola con exploit (FW <= 4.51 / 5.50) + red | Moderado (Consola en activo) | **L (Grande)** |
| **Xbox 360** | `libxenon` (bare-metal) | **Inexistente** (Solo SDL 1.2 `libSDLXenon`) | Docker `free60/libxenon` | **Incompatible** (Xenia solo ejecuta XEX retail, no ELF bare-metal) | Consola con chip físico (RGH / JTAG) + XeLL | Alto si se usa XDK / Bajo en libxenon | **L (Desaconsejado)** |

---

## 3. Recomendación Final Ordenada por Costo

Orden de menor a mayor costo de desarrollo e integración con el ecosistema de `renpy-console-project`:

### 1. Xbox One y Xbox Series X|S — Esfuerzo S (Máxima Recomendación)
* **Por qué es la primera opción:**
  * **Soporte oficial y legal sin fisuras:** No requiere vulnerar la consola ni perder la garantía. Cualquier usuario puede activar el modo desarrollador en su consola habitual por una tarifa de registro accesible (o gratis si es estudiante).
  * **SDL2 nativo y maduro:** SDL2 cuenta con soporte upstream oficial de WinRT / UWP con aceleración por Direct3D 11 y audio nativo.
  * **Pruebas automáticas sin emulador:** El paquete UWP se compila para arquitectura x64 y corre directamente en la PC del desarrollador con idéntica API. Además, Windows Device Portal permite automatizar la instalación y recogida de trazas TRACE por red.
* **Documento detallado:** [docs/platforms/research/xbox-one-series.md](file:///E:/Dev/renpy-console-wt/T-R01-agy/docs/platforms/research/xbox-one-series.md).

---

### 2. PlayStation 4 — Esfuerzo M (Segunda Opción)
* **Por qué es viable:**
  * **Arquitectura compartida (x86_64):** El código C99 y el backend de SDL2 compilan prácticamente sin divergencias con PC.
  * **SDK limpio y empaquetado consolidado:** OpenOrbis permite generar paquetes FPKG `.pkg` listos para instalar con GoldHEN.
  * **Emulación moderna:** Emuladores como `shadPS4` avanzan a gran velocidad y permiten invocar juegos por CLI (`--game`) para capturar trazas de regresión en CI.
* **Limitación:** Requiere que los usuarios posean una consola en firmware <= 11.00 (mediante el exploit PPPwn o WebKit).
* **Documento detallado:** [docs/platforms/research/ps4.md](file:///E:/Dev/renpy-console-wt/T-R01-agy/docs/platforms/research/ps4.md).

---

### 3. PlayStation 3 — Esfuerzo M (Tercera Opción)
* **Por qué es viable:**
  * **Emulador RPCS3 maduro:** Es el emulador más avanzado y estable del grupo, con modo `--headless` contrastado para automatizar la ejecución de escenarios de prueba.
  * **SDK y SDL2 disponibles:** PSL1GHT v2 cuenta con imágenes Docker comunitarias y puertos funcionales de SDL2 sobre Tiny3D y RSX.
  * **Accesibilidad para el usuario:** Prácticamente cualquier PS3 (Fat, Slim y SuperSlim) es compatible hoy en día con CFW o PS3HEN de forma sencilla mediante navegador web.
* **Limitación:** El backend SDL2 no está upstreamed y la arquitectura Cell BE (PPU/SPU y memoria dividida 256 MB + 256 MB) añade cierta complejidad en la gestión de buffers de video respecto a sistemas x86_64.
* **Documento detallado:** [docs/platforms/research/ps3.md](file:///E:/Dev/renpy-console-wt/T-R01-agy/docs/platforms/research/ps3.md).

---

### 4. PlayStation 5 — Esfuerzo L (Desaconsejado en el corto plazo)
* **Por qué debe posponerse:**
  * **Falta de emulador para CI:** No existe ningún emulador de PS5 operativo que permita verificar automáticamente las compuertas de calidad (`tools/ctl`).
  * **Método de despliegue fragmentado:** No existe un formato FPKG estandarizado y el software debe inyectarse en memoria vía red en consolas con versiones de firmware muy bajas (<= 4.51).
  * **Recomendación:** Mantener en Nivel R hasta que la comunidad desarrolle herramientas de emulación funcionales en PC.
* **Documento detallado:** [docs/platforms/research/ps5.md](file:///E:/Dev/renpy-console-wt/T-R01-agy/docs/platforms/research/ps5.md).

---

### 5. Xbox 360 — Esfuerzo L (Desaconsejado Indefinidamente)
* **Por qué debe descartarse:**
  * **Incompatibilidad de SDL2:** libxenon carece de un puerto de SDL2 (solo existe SDL 1.2), lo que rompería la regla de backend unificado.
  * **Incompatibilidad de emulador:** Xenia solo emula ejecutables comerciales XEX sobre el kernel retail de Microsoft y es incapaz de arrancar binarios ELF bare-metal de libxenon.
  * **Barrera de hardware extrema:** Exige abrir físicamente la consola para soldar chips de modificación RGH/JTAG, limitando el alcance a un grupo marginal de usuarios.
* **Documento detallado:** [docs/platforms/research/xbox-360.md](file:///E:/Dev/renpy-console-wt/T-R01-agy/docs/platforms/research/xbox-360.md).

---

## 4. Propuestas para el Plan de Trabajo y Contratos

1. **Incorporación a Nivel A (SDL):**
   * Tras la finalización de las plataformas prioritarias de Fase 5 y 6 (PSP, PS2, Vita, 3DS, Wii, Xbox clásica, Switch), se recomienda **añadir Xbox One / Series como plataforma de Nivel A** implementando un perfil UWP en `platforms/sdl`.
2. **Consolas PlayStation de Nivel A Secundario:**
   * Si se decide extender el soporte a consolas de sobremesa de Sony, la **PS4 (OpenOrbis)** debe tener prioridad sobre la PS3 por su afinidad con la arquitectura x86_64 del backend PC, seguida por **PS3 (PSL1GHT)** aprovechando RPCS3.
3. **Plataformas a congelar:**
   * Mantener PS5 y Xbox 360 en el Nivel R sin asignar recursos de desarrollo de motor.
