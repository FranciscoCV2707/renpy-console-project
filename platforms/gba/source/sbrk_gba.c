#include <stdint.h>

/* El sbrk de la libc de devkitARM corta el heap de EWRAM unos KB antes del final (reserva que
 * aquí no aplica: la pila del GBA vive en IWRAM). Las texturas residentes de una escena (fondo
 * 28,8 KB más personajes y capas) no caben sin ese tramo, así que el heap debe llegar de verdad
 * hasta __eheap_end. newlib llama a _sbrk_r (débil en la biblioteca), que es el símbolo que se
 * redefine aquí. */

struct _reent;

extern char __eheap_start[];
extern char __eheap_end[];

/* retain: --gc-sections la soltaría porque solo la biblioteca (malloc) la referencia. */
__attribute__((used, retain)) void *_sbrk_r(struct _reent *reent, int incr)
{
	static char *heap_brk = 0;

	(void)reent;
	if (!heap_brk)
		heap_brk = __eheap_start;
	if (incr < 0 || heap_brk + incr > __eheap_end)
		return (void *)-1;
	char *prev = heap_brk;
	heap_brk += incr;
	return prev;
}
