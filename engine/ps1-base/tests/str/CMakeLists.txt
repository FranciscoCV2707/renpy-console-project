# Prueba aislada del video STR (MDEC + XA) con el ejemplo strvideo de PSn00bSDK (main.c, MPL-2.0 sin cambios)
cmake_minimum_required(VERSION 3.21)

project(strvideo_test LANGUAGES C ASM)

psn00bsdk_add_executable(strvideo GPREL main.c)
