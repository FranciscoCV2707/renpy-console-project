# Reproductor de STR sin callbacks (ver main.c). El demultiplexor es el del motor (core/str.c).
cmake_minimum_required(VERSION 3.21)

project(strplayer LANGUAGES C ASM)

set(REPO ${CMAKE_CURRENT_SOURCE_DIR}/../../..)
psn00bsdk_add_executable(player GPREL main.c ${REPO}/core/str.c)
target_include_directories(player PRIVATE ${REPO}/core)
