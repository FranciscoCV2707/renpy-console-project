cmake_minimum_required(VERSION 3.21)

project(
	vnengine
	LANGUAGES    C ASM
	VERSION      0.1.0
	DESCRIPTION  "Motor de novelas visuales para PlayStation 1"
)

# Un ejecutable por juego: games/<GAME>/ trae sus reglas (game.c), sus textos (text.c) y su tabla de pantallas
# especiales (specials.c). El ejecutable se llama como el juego (GAME=snoot -> snoot.exe).
set(GAME "snoot" CACHE STRING "juego: carpeta de games/")
if(NOT EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/games/${GAME})
	message(FATAL_ERROR "no existe games/${GAME}")
endif()

set(VN_SEEN_BYTES 2048)
set(VN_SAVE_TITLE "SNOOT GAME")
set(VN_SAVE_PREFIX "BASLUS-99999SNOOT")
set(VN_SAVE_MAGIC "SNS1")
include(${CMAKE_CURRENT_SOURCE_DIR}/games/${GAME}/config.cmake OPTIONAL)
configure_file(app/game_config.h.in generated/game_config.h @ONLY)

# core/: núcleo general; app/: bucle principal e interfaz; modules/: pantallas especiales
file(GLOB _sources CONFIGURE_DEPENDS core/*.c app/*.c modules/*.c games/${GAME}/*.c)
psn00bsdk_add_executable(${GAME} GPREL ${_sources})
target_include_directories(${GAME} PRIVATE core app modules ${CMAKE_CURRENT_BINARY_DIR}/generated)
