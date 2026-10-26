cmake_minimum_required(VERSION 3.21)

project(
	renpyconsole
	LANGUAGES    C ASM
	VERSION      0.1.0
	DESCRIPTION  "Motor de novelas visuales multiplataforma (build de PS1)"
)

# Un ejecutable por juego: games/<GAME>/ trae sus reglas (game.c), sus textos (text.c) y su tabla de pantallas
# especiales (specials.c). El ejecutable se llama como el juego (GAME=snoot -> snoot.exe). Mismo esquema que
# vn-engine-ps1, para que sus herramientas y pruebas en emulador funcionen con este repo.
set(GAME "snoot" CACHE STRING "juego: carpeta de games/")
if(NOT EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/games/${GAME})
	message(FATAL_ERROR "no existe games/${GAME}")
endif()

set(VN_SEEN_BYTES 2048)
set(VN_SAVE_TITLE "SNOOT GAME")
set(VN_SAVE_PREFIX "BASLUS-99999SNOOT")
set(VN_SAVE_MAGIC "SNS1")
include(${CMAKE_CURRENT_SOURCE_DIR}/games/${GAME}/config.cmake OPTIONAL)
configure_file(engine/app/game_config.h.in generated/game_config.h @ONLY)

# engine/core: nucleo portable; engine/app: bucle e interfaz; engine/modules: pantallas especiales;
# platforms/ps1: hardware de la PS1 (la API que el nucleo y la app llaman se resuelve al enlazar)
file(GLOB _sources CONFIGURE_DEPENDS
	engine/core/*.c engine/app/*.c engine/modules/*.c platforms/ps1/*.c games/${GAME}/*.c)
psn00bsdk_add_executable(${GAME} GPREL ${_sources})
target_include_directories(${GAME} PRIVATE
	engine/core engine/platform engine/app engine/modules platforms/ps1 ${CMAKE_CURRENT_BINARY_DIR}/generated)

# Build de prueba con la traza TRACE (PLAN.md 4.1): VN_TRACE=1 en el entorno al configurar (lo pone tools/ctl).
# Se lee en cada configuracion, asi build/ vuelve al build normal en cuanto falta la variable.
if("$ENV{VN_TRACE}")
	target_compile_definitions(${GAME} PRIVATE VN_TRACE)
endif()
