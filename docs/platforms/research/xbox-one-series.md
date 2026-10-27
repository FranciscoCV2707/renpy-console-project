# Investigación de Plataforma: Xbox One y Xbox Series X|S

> **Estado:** Fase de Investigación (PLAN.md sección 5, Nivel R)  
> **Fecha de verificación:** 2026-10-27  
> **Factibilidad general:** Altamente Favorable / Vía Oficial Limpia (Esfuerzo S) mediante UWP en Modo Desarrollador (Developer Mode).

---

## 1. Resumen de Factibilidad

Llevar Snoot Game a la familia Xbox One y Xbox Series (Xbox One, One S, One X, Series S y Series X) es la vía más directa, segura y técnicamente accesible de todas las plataformas analizadas en este ciclo de investigación. Microsoft ofrece de forma oficial el programa **Xbox Developer Mode**, que permite a cualquier usuario transformar una consola comercial ordinaria en un kit de pruebas y desarrollo para ejecutar aplicaciones **UWP (Universal Windows Platform)** sin necesidad de vulnerabilidades, jailbreaks ni modificaciones de hardware. **SDL2 cuenta con soporte completo y maduro para UWP / WinRT en su repositorio oficial upstream**, lo que permite reutilizar el backend existente (`platforms/sdl`) con cambios mínimos.

---

## 2. SDK y Toolchain

* **SDK Autorizado Principal:** **Universal Windows Platform (UWP / WinRT SDK)**.
  * Proveedor: Microsoft Corporation (incluido en Windows SDK y Visual Studio Community, de uso gratuito).
  * Documentación oficial: [learn.microsoft.com/windows/uwp/xbox-apps/](https://learn.microsoft.com/windows/uwp/xbox-apps/) (verificado: 2026-10-27).
  * Lenguaje y runtime: C99 / C++17 compilado mediante MSVC (herramientas `cl.exe` / `link.exe` / `v143`).
* **SDK Alternativo:** **Microsoft Gaming Development Kit (GDK)**.
  * Repositorio de código abierto: [github.com/microsoft/GDK](https://github.com/microsoft/GDK) (verificado: 2026-10-27).
  * Nota de alcance: La versión pública del GDK permite compilar juegos de escritorio para Windows (`__WINGDK__`), mientras que las extensiones específicas de consola (`GDKX`) requieren autorización de Microsoft mediante el programa ID@Xbox. No obstante, **UWP es totalmente abierto y accesible para cualquier desarrollador sin contratos comerciales**.

---

## 3. Estado de SDL2

* **Disponibilidad:** **Excelente (Soporte oficial upstream consolidado)**.
  * SDL2 integra soporte oficial para WinRT / UWP en su rama principal ([github.com/libsdl-org/SDL](https://github.com/libsdl-org/SDL)).
  * Documentación en el árbol de SDL: `docs/README-winrt.md` y proyectos en `VisualC-WinRT/`.
* **Subsistemas implementados:**
  * **Video:** Backend nativo sobre **Direct3D 11** (`src/video/winrt/`) o aceleración mediante ANGLE (OpenGL ES sobre D3D11). El renderizador de SDL gestiona automáticamente las superficies de composición (`CoreWindow` y `SwapChainBackgroundPanel`).
  * **Audio:** Soporte nativo a través de WASAPI y XAudio2.
  * **Entrada:** Soporte completo de mandos inalámbricos Xbox mediante la API `Windows.Gaming.Input`.
  * **Punto de entrada:** Soporte mediante la función adaptadora oficial `SDL_WinRTRunApp`, que encapsula el ciclo de vida de la aplicación UWP y despacha el `main()` estándar del motor C99.
* **Proyectos de referencia:** Plataformas masivas como **RetroArch Xbox** ([github.com/libretro/RetroArch](https://github.com/libretro/RetroArch)) operan exitosamente sobre este mismo esquema UWP en miles de consolas comerciales.

---

## 4. Entorno de Compilación en Docker / Local

* **Compilación en Host Windows:**
  * Se compila mediante MSBuild o la CLI de Visual Studio Build Tools, generando paquetes firmados de prueba en formato `.appx` o `.msix`.
* **Compilación en Docker:**
  * Es posible utilizar imágenes de Windows Containers (como `mcr.microsoft.com/windows/servercore` con Visual Studio Build Tools instalado). No obstante, al trabajar en Windows, la invocación directa de `msbuild.exe` o scripts en Python desde el propio entorno local resulta significativamente más ágil.

---

## 5. Emulación y Pruebas Automatizadas (Test Lab / TRACE)

* **¿Es necesario un emulador?**
  * No existe un emulador público de Xbox One ni de Xbox Series.
  * **Sin embargo, no hace falta un emulador para pruebas automáticas:** Al estar compilado sobre UWP x64, el paquete se ejecuta **de forma nativa en la PC con Windows 10/11**, compartiendo con la consola exactamente las mismas APIs de sistema, la misma pila gráfica Direct3D 11 y el mismo backend de SDL2.
* **Pruebas en Hardware Real mediante Red:**
  * En modo desarrollador, las consolas Xbox exponen el **Windows Device Portal (WDP)** por HTTP/HTTPS.
  * WDP dispone de una completa API REST que permite:
    1. Instalar paquetes `.appx` automáticamente por red (`POST /api/app/packagemanager/package`).
    2. Arrancar el proceso de la aplicación (`POST /api/taskmanager/process`).
    3. Leer la salida de depuración y logs de ETW / stdout en tiempo real.
    4. Detener el proceso tras concluir el escenario de prueba.
  * Esto permite una integración directa y desatendida en `tools/ctl` si se dispone de una consola en la red local.

---

## 6. Requisitos para el Usuario / Hardware Real

* **Activación Oficial sin Modificaciones:**
  * Se realiza en cualquier consola comercial estándar (Xbox One, Xbox One S, Xbox One X, Xbox Series S, Xbox Series X) comprada en tienda.
  * **Cero riesgo para la consola:** No requiere modchips, ni soldaduras, ni exploits, ni hackeo de firmware. La garantía del fabricante permanece intacta.
* **Pasos requeridos:**
  1. Instalar la aplicación gratuita "Xbox Dev Mode" desde la tienda oficial de Microsoft en la consola.
  2. Registrar la consola en el portal de desarrolladores de Microsoft Partner Center (requiere una cuenta Microsoft con pago único de registro de ~$19 USD, o gratuita mediante el programa GitHub Student Developer Pack).
  3. La consola se reinicia en "Developer Mode", con acceso al Device Portal para subir aplicaciones `.appx` / `.msix` arrastrando el archivo en el navegador web o mediante USB.
  4. Para volver a jugar títulos comerciales, el usuario simplemente pulsa "Switch to Retail Mode" y la consola se reinicia de nuevo en su modo comercial habitual.

---

## 7. Riesgos Legales

* **Cero riesgos legales:**
  * Es un cauce de despliegue oficial y expresamente provisto por Microsoft Corporation para desarrolladores independientes y aficionados.
  * El código fuente de SDL2 es zlib, y el motor y los activos de Snoot se distribuyen bajo sus licencias correspondientes (MIT / AGPL-3.0 / CC-BY-SA 4.0), respetando las normas de publicación de la plataforma.

---

## 8. Estimación de Esfuerzo

* **Estimación:** **S (Pequeño / Recomendado)**
* **Justificación:**
  * **Menor costo del grupo:** El backend SDL2 ya está implementado en el upstream oficial; la arquitectura de hardware es x86_64 estándar; el almacenamiento y la memoria RAM (8 GB a 16 GB) exceden con creces los requerimientos; el proceso de compilación y prueba se valida en el propio PC Windows y la instalación en hardware real no requiere jailbreak.
  * **Trabajo necesario:** Crear la solución Visual Studio / plantilla MSBuild que invoque `SDL_WinRTRunApp` enlazando con `platforms/sdl`, generar el manifiesto `AppxManifest.xml` con los iconos de Snoot, y documentar el script de despliegue por red en el Test Lab.

---

## 9. Fuentes Citadas

1. Documentación de activación de Xbox Developer Mode: `https://learn.microsoft.com/windows/uwp/xbox-apps/devkit-activation` (2026-10-27).
2. Soporte oficial de WinRT / UWP en el repositorio upstream de SDL2: `https://github.com/libsdl-org/SDL` (`docs/README-winrt.md` y `src/video/winrt/`) (2026-10-27).
3. Repositorio oficial Microsoft Game Development Kit (GDK): `https://github.com/microsoft/GDK` (2026-10-27).
4. Implementación de RetroArch UWP para Xbox One / Series: `https://github.com/libretro/RetroArch` (2026-10-27).
5. Documentación de Windows Device Portal para Xbox: `https://learn.microsoft.com/windows/uwp/xbox-apps/device-portal-xbox` (2026-10-27).
