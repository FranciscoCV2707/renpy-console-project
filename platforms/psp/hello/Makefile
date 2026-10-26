TARGET = hello
OBJS = main.o

PSPSDK := $(shell psp-config --pspsdk-path)
PSPDEV := $(shell psp-config --pspdev-path)

PSP_EBOOT_TITLE = Hello SDL2

CFLAGS += $(shell psp-pkg-config --cflags sdl2)
LIBS += $(shell psp-pkg-config --libs sdl2)

# `all` se define después del include porque $(PSP_EBOOT) se define dentro de
# build.mak (líneas 134-138); definirlo antes dejaría el prerequisito vacío.
include $(PSPSDK)/lib/build.mak

all: $(PSP_EBOOT)
