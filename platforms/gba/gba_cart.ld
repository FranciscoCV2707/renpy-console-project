OUTPUT_FORMAT("elf32-littlearm", "elf32-bigarm", "elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(_start)

MEMORY {
	rom	: ORIGIN = 0x08000000, LENGTH = 32M
	iwram	: ORIGIN = 0x03000000, LENGTH = 32K
	ewram	: ORIGIN = 0x02000000, LENGTH = 256K
}

__text_start	=	ORIGIN(rom);
__eheap_end	=	ORIGIN(ewram) + LENGTH(ewram);
__iwram_start	=	ORIGIN(iwram);
__iwram_top	=	ORIGIN(iwram) + LENGTH(iwram);
__sp_irq	=	__iwram_top - 0x060;
__sp_usr	=	__sp_irq - 0x0a0;
__irq_flags	=	0x03007ff8;

SECTIONS
{
	. = __text_start;
	.crt0 :
	{
		KEEP (*(.crt0))
		. = ALIGN(4);
	} >rom =0xff

	.init :
	{
		KEEP (*(SORT_NONE(.init)))
	} >rom

	.plt :
	{
		*(.plt)
		. = ALIGN(4);
	} >rom

	.text :
	{
		*(EXCLUDE_FILE (*.iwram*) .text*)
		*(.gnu.linkonce.t.*)
		KEEP (*(.text.*personality*))
		*(.gnu.warning)
		*(.glue_7t) *(.glue_7) *(.vfp11_veneer)
		. = ALIGN(4);
	} >rom = 0xff

	__text_end = .;
	.fini :
	{
		KEEP (*(.fini))
		. = ALIGN(4);
	} >rom =0

	.rodata :
	{
		*(.rodata)
		*all.rodata*(*)
		*(.roda)
		*(.rodata.*)
		*(.gnu.linkonce.r*)
		SORT(CONSTRUCTORS)
		. = ALIGN(4);
	} >rom = 0xff

	.ARM.extab : { *(.ARM.extab* .gnu.linkonce.armextab.*) } >rom
	__exidx_start = .;
	.ARM.exidx : { *(.ARM.exidx* .gnu.linkonce.armexidx.*) } >rom
	__exidx_end = .;

	.ctors :
	{
		KEEP (*crtbegin.o(.ctors))
		KEEP (*(EXCLUDE_FILE (*crtend.o) .ctors))
		KEEP (*(SORT(.ctors.*)))
		KEEP (*(.ctors))
		. = ALIGN(4);
	} >rom = 0

	.dtors :
	{
		KEEP (*crtbegin.o(.dtors))
		KEEP (*(EXCLUDE_FILE (*crtend.o) .dtors))
		KEEP (*(SORT(.dtors.*)))
		KEEP (*(.dtors))
		. = ALIGN(4);
	} >rom = 0

	.eh_frame :
	{
		KEEP (*(.eh_frame))
		. = ALIGN(4);
	} >rom = 0

	.gcc_except_table :
	{
		*(.gcc_except_table)
		. = ALIGN(4);
	} >rom = 0

	__iwram_lma = .;

	.iwram __iwram_start : AT (__iwram_lma)
	{
		__iwram_start__ = ABSOLUTE(.);
		*(.iwram .iwram*)
		*iwram.*(.text* .data*)
		. = ALIGN(4);
		__iwram_end__ = ABSOLUTE(.);
	} >iwram = 0xff

	__data_lma = __iwram_lma + SIZEOF(.iwram);

	.data ALIGN(4) : AT (__data_lma)
	{
		__data_start__ = ABSOLUTE(.);
		*(.data*)
		*(.gnu.linkonce.d*)
		CONSTRUCTORS
		. = ALIGN(4);
	} >iwram = 0xff

	__preinit_lma = __data_lma + SIZEOF(.data);

	.preinit_array ALIGN(4) : AT (__preinit_lma)
	{
		__preinit_array_start = ABSOLUTE(.);
		KEEP (*(.preinit_array))
		__preinit_array_end = ABSOLUTE(.);
	} >iwram

	__init_lma = __preinit_lma + SIZEOF(.preinit_array);

	.init_array ALIGN(4) : AT (__init_lma)
	{
		__init_array_start = ABSOLUTE(.);
		KEEP (*(SORT(.init_array.*)))
		KEEP (*(.init_array))
		__init_array_end = ABSOLUTE(.);
	} >iwram

	__fini_lma = __init_lma + SIZEOF(.init_array);

	.fini_array ALIGN(4) : AT (__fini_lma)
	{
		__fini_array_start = ABSOLUTE(.);
		KEEP (*(SORT(.fini_array.*)))
		KEEP (*(.fini_array))
		__fini_array_end = ABSOLUTE(.);
	} >iwram

	__jcr_lma = __fini_lma + SIZEOF(.fini_array);
	.jcr ALIGN(4) : AT (__jcr_lma) { KEEP (*(.jcr)) } >iwram

	__data_end__ = ABSOLUTE(.);
	__iwram_overlay_lma = __jcr_lma + SIZEOF(.jcr);

	__iwram_overlay_start = .;

	OVERLAY ALIGN(4) : NOCROSSREFS AT (__iwram_overlay_lma)
	{
		.iwram0 { *(.iwram0) . = ALIGN(4); }
		.iwram1 { *(.iwram1) . = ALIGN(4); }
		.iwram2 { *(.iwram2) . = ALIGN(4); }
		.iwram3 { *(.iwram3) . = ALIGN(4); }
		.iwram4 { *(.iwram4) . = ALIGN(4); }
		.iwram5 { *(.iwram5) . = ALIGN(4); }
		.iwram6 { *(.iwram6) . = ALIGN(4); }
		.iwram7 { *(.iwram7) . = ALIGN(4); }
		.iwram8 { *(.iwram8) . = ALIGN(4); }
		.iwram9 { *(.iwram9) . = ALIGN(4); }
	} >iwram = 0xff

	__iwram_overlay_end = .;
	__ewram_lma = __iwram_overlay_lma + (__iwram_overlay_end - __iwram_overlay_start);

	__iheap_start = .;

	__ewram_start = ORIGIN(ewram);
	.ewram __ewram_start : AT (__ewram_lma)
	{
		*(.ewram*)
		. = ALIGN(4);
		__ewram_end = ABSOLUTE(.);
	} >ewram = 0xff

	.bss ALIGN(4) (NOLOAD) :
	{
		__bss_start = ABSOLUTE(.);
		__bss_start__ = ABSOLUTE(.);
		*(.dynbss)
		*(.gnu.linkonce.b*)
		*(.bss*)
		*(COMMON)
		. = ALIGN(4);
		__bss_end__ = ABSOLUTE(.);
	} AT>ewram

	__pad_lma = __ewram_lma + SIZEOF(.ewram);

	.sbss ALIGN(4) (NOLOAD) :
	{
		__sbss_start__ = ABSOLUTE(.);
		*(.sbss*)
		. = ALIGN(4);
		__sbss_end__ = ABSOLUTE(.);
		__end__ = ABSOLUTE(.);
		__eheap_start = ABSOLUTE(.);
	} AT>ewram

	.pad ALIGN(4) : AT (__pad_lma)
	{
		LONG(0x52416b64)
		LONG(0x4d)
		. = ALIGN(4);
	} = 0xff
	__rom_end__ = __pad_lma + SIZEOF(.pad);

	/DISCARD/ : { *(.note.GNU-stack) }
}
