# Cómo instalar y jugar — Snoot Game en consolas

Guía para jugar sin programar nada. Snoot Game es una novela visual de **Cavemanon**; esto es un
**port no oficial** hecho por fans, sin relación con Cavemanon ni con Sony, Nintendo o Microsoft.
El juego va **solo en español** (la traducción oficial del juego): no hay selector de idioma.

Cómo leer esta guía: cada consola tiene su sección con **qué archivo se descarga**, **dónde se copia**,
**qué necesita la consola** y **cómo se guarda la partida**. Solo PlayStation 1 tiene versión publicada
(v1.0); el resto está **en preparación** y su sección describe lo que habrá cuando salga, para que sepas
qué te hará falta por adelantado.

Reglas comunes a todas las plataformas:

- El port **no incluye BIOS, firmware ni claves** de ninguna consola: si algo las necesita, las pone
  cada cual desde su propia consola (o desde el emulador, si es legal en tu país).
- Junto al juego se entregan los **créditos** (`CREDITS.md`) y un directorio `LICENSES/` con los textos
  de licencia; el juego es AGPL-3.0 (código) y CC-BY-SA 4.0 (arte y audio), y el código fuente del port
  se publica en un enlace junto a cada descarga. No los borres al copiar el juego.
- Requisitos tipo "homebrew" o "CFW" (consola modificada) se indican con un **enlace a la guía
  comunitaria de referencia**: aquí no hay pasos de hackeo y cada quien decide qué hace con su consola.

## PlayStation 1 — Disponible (v1.0)

- **Qué se descarga:** un `.zip` con la imagen del CD: `snoot_game.cue` + `snoot_game.bin`
  (el disco completo del juego, 213 MB).
- **En emulador (lo más fácil):** abre `snoot_game.cue` —no el `.bin`— en
  [DuckStation](https://www.duckstation.org/) con una BIOS de PlayStation y listo.
- **En consola real:** graba el `.cue`/`.bin` en un CD-R en modo Disc-at-Once y a velocidad baja (4x u
  8x). La consola necesita un chip o un método para arrancar copias; no se incluye nada de eso.
- **Guardado:** en la **memory card de la ranura 1**; el juego gestiona 3 ranuras de guardado y el
  progreso (texto leído, finales, galería). Sin memory card puedes jugar con **Select** presionado
  durante el arranque, pero no se guarda. El emulador crea la memory card solo.
- **En PS2 con POPStarter (`.VCD`) no funciona** de momento: se queda en la pantalla de inicio. Hay un
  port nativo para PS2 en camino (ver abajo).

## PC (Windows) — En preparación

- **Qué se descargará:** un `.zip` con `snoot.exe`, `SDL2.dll` y la carpeta de datos del juego.
- **Dónde:** se descomprime en cualquier carpeta y se ejecuta `snoot.exe`. No hay instalador.
- **Qué necesita:** Windows 10/11; nada más (SDL2 va incluida).
- **Guardado:** archivos de partida en la carpeta `save/` junto al ejecutable; sin límite de ranuras
  impuesto por el sistema.

## PSP / PSP Go — En preparación

- **Qué se descargará:** el `EBOOT.PBP` del juego.
- **Dónde se copia:** en la Memory Stick (o en la memoria interna del PSP Go), en la carpeta
  `PSP/GAME/SNOOT/`, con los datos del juego en `PSP/GAME/SNOOT/DATA/` y las partidas en
  `PSP/GAME/SNOOT/SAVE/`.
- **Qué necesita:** una PSP con **custom firmware** para ejecutar homebrew desde la Memory Stick
  (guía comunitaria de referencia:
  [GBAtemp — Install PSP 6.61 Pro-C / Infinity Custom Firmware](https://gbatemp.net/threads/install-psp-6-61-pro-c-infinity-custom-firmware.468844/))
  o bien el emulador [PPSSPP](https://www.ppsspp.org/) en PC o móvil, que no modifica nada.
- **Guardado:** en la propia Memory Stick (`PSP/GAME/SNOOT/SAVE/`), como archivos del juego; no usa
  los datos de guardado de PSP.

## PlayStation 2 — En preparación

- **Qué se descargará:** el ejecutable `.elf` del juego junto a sus datos.
- **Dónde se copia:** a una memoria USB o memory card; se arranca desde un explorador de homebrew
  (p. ej. el que instala FreeMcBoot).
- **Qué necesita:** una PS2 con **FreeMcBoot** en la memory card
  (guía comunitaria de referencia:
  [PS2-HOME — Free McBoot Installation Guide](https://www.ps2-home.com/forum/viewtopic.php?t=1248))
  o el emulador [PCSX2](https://pcsx2.net/) en PC.
- **Guardado:** por definir con el paquete (memoria USB o memory card); se indicará aquí al publicar.

## PS Vita — En preparación

- **Qué se descargará:** el paquete `snoot.vpk`.
- **Dónde se copia:** se instala con **VitaShell** (o con el emulador Vita3K, que abre el `.vpk`
  directamente). Los datos del juego van en `ux0:data/snoot/` y las partidas en `ux0:data/snoot/save/`
  (la tarjeta de memoria o el almacenamiento de la consola).
- **Qué necesita:** una Vita con **HENkaku/ensō** (guía comunitaria de referencia:
  [vita.hacks.guide](https://vita.hacks.guide/)) o el emulador [Vita3K](https://vita3k.org/) en PC.
- **Guardado:** archivos en `ux0:data/snoot/save/`; se pueden copiar a PC para hacer copia de seguridad.

## Nintendo 3DS — En preparación

- **Qué se descargará:** el paquete del juego (formato `.cia` o `.3dsx` por decidir) y sus datos en la
  tarjeta SD.
- **Qué necesita:** una 3DS con **custom firmware** (guía comunitaria de referencia:
  [3ds.hacks.guide](https://3ds.hacks.guide/)) o el emulador
  [Azahar](https://github.com/azahar-emu/azahar) en PC.
- **Guardado:** en la tarjeta SD de la consola; se indicará la carpeta al publicar.

## Wii — En preparación

- **Qué se descargará:** la aplicación del juego (`.dol`/`.elf`) y sus datos.
- **Dónde se copia:** a la tarjeta SD en la carpeta de aplicaciones del **Homebrew Channel**.
- **Qué necesita:** una Wii con el **Homebrew Channel**
  (guía comunitaria de referencia: [wii.hacks.guide](https://wii.hacks.guide/)) o el emulador
  [Dolphin](https://dolphin-emu.org/) en PC.
- **Guardado:** en la tarjeta SD; carpeta por definir al publicar.

## Xbox clásica — En preparación

- **Qué se descargará:** el ejecutable del juego y sus datos.
- **Qué necesita:** una Xbox con **softmod o chip** (wiki comunitaria de referencia:
  [ConsoleMods — Original Xbox Mods Wiki](https://consolemods.org/wiki/Xbox:Original_Xbox_Mods_Wiki))
  o el emulador [xemu](https://xemu.app/) en PC, que usa la BIOS de tu propia consola.
- **Guardado:** en el disco duro de la consola o la memory card de Xbox; por definir al publicar.

## Nintendo Switch — En preparación

- **Qué se descargará:** el paquete del juego y sus datos en la microSD.
- **Qué necesita:** una Switch con **custom firmware** (Atmosphère; guía comunitaria de referencia:
  [switch.hacks.guide](https://switch.hacks.guide/)). No hay emulador de Switch que usar en PC.
- **Guardado:** en la microSD; carpeta por definir al publicar.

## Game Boy Advance — En preparación (demake)

Adaptación reducida del juego (fase de demake): cabe en un cartucho de 32 MB.

- **Qué se descargará:** la ROM `.gba`.
- **Qué necesita:** un **flashcart** de GBA (p. ej.
  [EverDrive GBA (krikzz.com)](https://krikzz.com/our-products/cartridges/everdrive-gba-pro.html) o
  [EZ-Flash Omega (ezflash.cn)](https://www.ezflash.cn/product/omega/)) o el emulador
  [mGBA](https://mgba.io/) en PC.
- **Guardado:** en la SRAM del flashcart (se copia a la SD al salir); en emulador, en el directorio de
  guardados del emulador.

## Nintendo DS — En preparación (demake)

- **Qué se descargará:** la ROM `.nds`.
- **Qué necesita:** un **flashcart** de DS
  (wiki comunitaria de referencia: [ConsoleMods — NDS Flash Cards](https://consolemods.org/wiki/NDS:Flash_Cards))
  o el emulador [melonDS](https://melonds.kuribo64.net/) en PC.
- **Guardado:** en el flashcart o en los directorios del emulador; por definir al publicar.

## Game Boy / Game Boy Color — En preparación (demake)

Adaptación extrema del juego a los 4 tonos del GB; cabe en un cartucho de 8 MB.

- **Qué se descargará:** la ROM `.gb` / `.gbc`.
- **Qué necesita:** un **flashcart** de GB/GBC (p. ej.
  [EverDrive GB X7 (krikzz.com)](https://krikzz.com/our-products/cartridges/edgbx7.html)) o el emulador
  [SameBoy](https://sameboy.github.io/) en PC.
- **Guardado:** en la SRAM del flashcart; en emulador, en su directorio de guardados.

## Otras consolas (PS3, PS4, PS5, Xbox 360, Xbox One/Series) — Investigación

No hay versión en desarrollo con fecha: están en fase de investigación del proyecto. Cuando alguna
pase a desarrollo tendrá su sección aquí con los mismos cuatro puntos.
