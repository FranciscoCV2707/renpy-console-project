TARGET = snoot
SRC = /src
OUT = /src/build/ps4
CONTENT_ID = IV0000-SNOT00001_00-SNOOTGAME0000000
TITLE_ID = SNOT00001
TITLE = Snoot Game
VERSION = 01.00

OPENORBIS ?= /opt/pacbrew/ps4/openorbis
OO_PS4_TOOLCHAIN ?= $(OPENORBIS)
CC = $(OPENORBIS)/bin/clang
LD = $(OPENORBIS)/bin/clang
CREATE_FSELF = $(OPENORBIS)/bin/create-fself
CREATE_GP4 = $(OPENORBIS)/bin/create-gp4
PKGTOOL = $(OPENORBIS)/bin/linux/PkgTool.Core

SRCS = $(wildcard $(SRC)/engine/core/*.c) \
       $(wildcard $(SRC)/engine/app/*.c) \
       $(wildcard $(SRC)/engine/modules/*.c) \
       $(wildcard $(SRC)/games/snoot/*.c) \
       $(wildcard $(SRC)/platforms/ps4/*.c) \
       $(wildcard $(SRC)/platforms/sdl/*.c)
OBJDIR = $(OUT)/obj$(if $(filter 1,$(VN_TRACE)),-trace)
OBJS = $(patsubst $(SRC)/%.c,$(OBJDIR)/%.o,$(SRCS))

# dlmalloc 2.8.6 (dominio publico): en Orbis no hay sbrk, el heap sale de mmap; FOOTERS detecta
# desbordes/doble free al liberar. MMAP_CLEARS=0: shadPS4 no garantiza mmap en ceros y SDL_calloc lo necesita
DLMALLOC_OBJ = $(OBJDIR)/platforms/ps4/dlmalloc-2.8.6.o
$(DLMALLOC_OBJ): CFLAGS += -DHAVE_MORECORE=0 -DUSE_LOCKS=1 -DFOOTERS=1 -DMMAP_CLEARS=0

ARCH = --target=x86_64-pc-freebsd12-elf
CFLAGS += $(ARCH) -std=c99 -Wall -Wextra -Wno-unused-parameter -pedantic -O2 -fPIC -funwind-tables
CFLAGS += -D__PS4__ -D__OPENORBIS__ -D__ORBIS__ -DPS4 -D__BSD_VISIBLE -D_BSD_SOURCE
CFLAGS += -isysroot $(OPENORBIS) -isystem $(OPENORBIS)/include -I$(OPENORBIS)/usr/include -I$(OPENORBIS)/usr/include/SDL2
CFLAGS += -iquote $(SRC)/engine/core -iquote $(SRC)/engine/platform -iquote $(SRC)/engine/app \
          -iquote $(SRC)/engine/modules -iquote $(SRC)/games/snoot -iquote $(SRC)/platforms/sdl \
          -iquote $(OUT)/generated

ifeq ($(VN_TRACE),1)
CFLAGS += -DVN_TRACE
endif

LIBS = -L$(OPENORBIS)/lib -L$(OPENORBIS)/usr/lib -lc -lclang_rt.builtins-x86_64 -lkernel \
       -lpthread -lsamplerate -lm -lSDL2 -lSceSystemService -lSceSysUtil -lSceSysmodule -lSceUserService \
       -lSceAudioOut -lScePad -lScePigletv2VSH
LDFLAGS = $(ARCH) -fuse-ld=lld -Wl,-melf_x86_64 -Wl,-pie -Wl,--script=$(OPENORBIS)/link.x -Wl,--eh-frame-hdr $(LIBS) -nostdlib $(OPENORBIS)/lib/crt1.o

all: $(OUT)/eboot.bin $(OUT)/$(CONTENT_ID).pkg

$(OUT)/eboot.bin: $(OUT)/$(TARGET).elf
	export OO_PS4_TOOLCHAIN=$(OPENORBIS) && $(CREATE_FSELF) -in=$< -out=$(OUT)/$(TARGET).oelf --eboot=$@ --paid 0x3800000000000011

$(OUT)/$(TARGET).elf: $(OBJS)
	@mkdir -p $(dir $@)
	$(LD) $(OBJS) -o $@ $(LDFLAGS)

$(OBJDIR)/%.o: $(SRC)/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -MMD -MP -c -o $@ $<

# Recompila cuando cambia un header (sdl_target.h, vm.h...), no solo el .c
-include $(OBJS:.o=.d)

$(OUT)/sce_sys/param.sfo:
	@mkdir -p $(OUT)/sce_sys
	$(PKGTOOL) sfo_new $@
	$(PKGTOOL) sfo_setentry $@ APP_TYPE --type Integer --maxsize 4 --value 1
	$(PKGTOOL) sfo_setentry $@ APP_VER --type Utf8 --maxsize 8 --value '$(VERSION)'
	$(PKGTOOL) sfo_setentry $@ ATTRIBUTE --type Integer --maxsize 4 --value 0
	$(PKGTOOL) sfo_setentry $@ CATEGORY --type Utf8 --maxsize 4 --value 'gd'
	$(PKGTOOL) sfo_setentry $@ CONTENT_ID --type Utf8 --maxsize 48 --value '$(CONTENT_ID)'
	$(PKGTOOL) sfo_setentry $@ DOWNLOAD_DATA_SIZE --type Integer --maxsize 4 --value 0
	$(PKGTOOL) sfo_setentry $@ SYSTEM_VER --type Integer --maxsize 4 --value 0
	$(PKGTOOL) sfo_setentry $@ TITLE --type Utf8 --maxsize 128 --value '$(TITLE)'
	$(PKGTOOL) sfo_setentry $@ TITLE_ID --type Utf8 --maxsize 12 --value '$(TITLE_ID)'
	$(PKGTOOL) sfo_setentry $@ VERSION --type Utf8 --maxsize 8 --value '$(VERSION)'

$(OUT)/pkg.gp4: $(OUT)/eboot.bin $(OUT)/sce_sys/param.sfo
	cd $(OUT) && $(CREATE_GP4) -out pkg.gp4 --content-id=$(CONTENT_ID) --files 'eboot.bin sce_sys/param.sfo'

$(OUT)/$(CONTENT_ID).pkg: $(OUT)/pkg.gp4
	cd $(OUT) && $(PKGTOOL) pkg_build pkg.gp4 .
	cp $(OUT)/$(CONTENT_ID).pkg $(OUT)/snoot.pkg

clean:
	rm -rf $(OUT)/obj $(OUT)/obj-trace $(OUT)/$(TARGET).elf $(OUT)/$(TARGET).oelf $(OUT)/eboot.bin $(OUT)/pkg.gp4 $(OUT)/$(CONTENT_ID).pkg $(OUT)/snoot.pkg $(OUT)/sce_sys
