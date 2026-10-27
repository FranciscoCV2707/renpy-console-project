# Nintendo DS - Demake Snoot Game (Fase 7, T-708)
NAME            := snoot
GAME_TITLE      := Snoot Game
GAME_SUBTITLE   := Demake DS
GAME_AUTHOR     := renpy-console-project
ARM7ELF         := $(BLOCKSDS)/sys/arm7/main_core/arm7_minimal.elf
NITROFSDIR      := nitrofs

SOURCEDIRS      := source engine_core engine_app engine_modules games_snoot
INCLUDEDIRS     := source engine_core include engine_app engine_modules games_snoot generated

DEFINES         += -DARM9

ifeq ($(VN_TRACE),1)
DEFINES         += -DVN_TRACE
endif

include $(BLOCKSDS)/sys/default_makefiles/rom_arm9/Makefile
