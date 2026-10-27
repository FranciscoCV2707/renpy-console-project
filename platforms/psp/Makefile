TARGET = snoot
SRC = /src
OUT = /src/build/psp

PSPSDK := $(shell psp-config --pspsdk-path)
PSPDEV := $(shell psp-config --pspdev-path)

PSP_EBOOT_TITLE = Snoot Game

SRCS = $(wildcard $(SRC)/engine/core/*.c) \
       $(wildcard $(SRC)/engine/app/*.c) \
       $(wildcard $(SRC)/engine/modules/*.c) \
       $(wildcard $(SRC)/games/snoot/*.c) \
       $(wildcard $(SRC)/platforms/sdl/*.c)
OBJS = $(patsubst $(SRC)/%.c,$(OUT)/obj/%.o,$(SRCS))

CFLAGS += -std=c99 -Wall -Wextra -Wno-unused-parameter -pedantic -O2
CFLAGS += -I$(SRC)/engine/core -I$(SRC)/engine/platform -I$(SRC)/engine/app \
          -I$(SRC)/engine/modules -I$(SRC)/games/snoot -I$(SRC)/platforms/sdl \
          -I$(OUT)/generated
CFLAGS += $(shell psp-pkg-config --cflags sdl2)
LIBS += $(filter-out -lSDL2main,$(shell psp-pkg-config --libs sdl2))

ifeq ($(VN_TRACE),1)
CFLAGS += -DVN_TRACE
endif

include $(PSPSDK)/lib/build.mak

all: $(PSP_EBOOT)

$(OUT)/obj/%.o: $(SRC)/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c -o $@ $<
