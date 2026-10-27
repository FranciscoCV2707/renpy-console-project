#include <stdint.h>

/* El sbrk de la libc de devkitARM corta el heap de EWRAM unos KB antes del final (reserva que
 * aquí no aplica: la pila del GBA vive en IWRAM). El motor necesita decodificar imágenes de
 * 320x180 (57,6 KB) con el capítulo descomprimido (18 KB) ya residente, así que el heap debe
 * llegar de verdad hasta __eheap_end. newlib llama a _sbrk_r (débil en la biblioteca), que es
 * el símbolo que se redefine aquí. */

struct _reent;

extern char __eheap_start[];
extern char __eheap_end[];

/* retain: --gc-sections la soltaría porque solo la biblioteca (malloc) la referencia. */
__attribute__((used, retain)) void *_sbrk_r(struct _reent *reent, int incr)
{
	static char *heap_brk = 0;
	char *prev;

	(void)reent;
	if (!heap_brk)
		heap_brk = __eheap_start;
	if (incr < 0 || heap_brk + incr > __eheap_end)
		return (void *)-1;
	prev = heap_brk;
	heap_brk += incr;
	{
		extern void mgba_log(const char *msg);
		static char msg[64];
		int n = 0;
		unsigned v = (unsigned)incr;
		msg[n++] = 'S'; msg[n++] = 'B'; msg[n++] = 'R'; msg[n++] = 'K'; msg[n++] = ' ';
		if (v >= 100000) { msg[n++] = '0' + v / 100000; }
		if (v >= 10000) { msg[n++] = '0' + v / 10000 % 10; }
		if (v >= 1000) { msg[n++] = '0' + v / 1000 % 10; }
		if (v >= 100) { msg[n++] = '0' + v / 100 % 10; }
		if (v >= 10) { msg[n++] = '0' + v / 10 % 10; }
		msg[n++] = '0' + v % 10;
		msg[n] = 0;
		mgba_log(msg);
	}
	return prev;
}
