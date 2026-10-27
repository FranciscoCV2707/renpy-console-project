PS3DEV ?= /usr/local/ps3dev
PSL1GHT ?= $(PS3DEV)
LD = ppu-gcc

TITLE = Snoot Game
APPID = SNOT00001
CONTENTID = UP0001-$(APPID)_00-0000000000000000

TARGET = snoot
BUILDDIR = /src/build/ps3

SRCS = $(wildcard /src/engine/core/*.c) \
       $(wildcard /src/engine/app/*.c) \
       $(wildcard /src/engine/modules/*.c) \
       $(wildcard /src/games/snoot/*.c) \
       $(wildcard /src/platforms/sdl/*.c)

OBJS = $(SRCS:.c=.o)
OFILES = $(OBJS)

include $(PSL1GHT)/ppu_rules

PORTLIBS ?= $(PS3DEV)/portlibs/ppu

INCLUDES = -I/src/engine/core -I/src/engine/platform -I/src/engine/app \
           -I/src/engine/modules -I/src/games/snoot -I/src/platforms/sdl \
           -I$(BUILDDIR)/generated $(LIBPSL1GHT_INC) \
           -I$(PORTLIBS)/include -I$(PORTLIBS)/include/SDL2

CFLAGS = $(MACHDEP) -std=c99 -Wall -Wextra -Wno-unused-parameter -pedantic -O2 \
         -D__PSL1GHT__ $(INCLUDES)
LDFLAGS = $(MACHDEP) -Wl,-q
LIBS = -L$(PORTLIBS)/lib -lSDL2 -lm -lgcm_sys -lrsx -lsysutil -lio -laudio \
       -lrt -llv2 $(LIBPSL1GHT_LIB)

all: snoot.self snoot.pkg
