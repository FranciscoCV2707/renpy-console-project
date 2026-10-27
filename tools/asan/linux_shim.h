/* Shim para compilar el backend SDL en Linux (solo lo usa tools/asan): el branch PC de
 * sdl_target.h llama `mkdir(path)` (1 argumento, el de MinGW); en glibc mkdir lleva modo.
 * Se incluye con `-include` antes de cada .c; el macro solo afecta a las llamadas de 1
 * argumento, que en este codigo son las de make_dir. */
#pragma once

#include <sys/stat.h>

static inline int linux_shim_mkdir(const char *path)
{
	return mkdir(path, 0777);
}

#define mkdir(path) linux_shim_mkdir(path)
