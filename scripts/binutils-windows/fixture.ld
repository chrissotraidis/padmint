OUTPUT_ARCH(mips)
ENTRY(entry)
SECTIONS
{
  . = 0x80000400;
  .text : { *(.text) }
  .rodata : { *(.rodata) }
  .data : { *(.data) }
  /DISCARD/ : { *(.MIPS.abiflags) *(.reginfo) *(.pdr) *(.gnu.attributes) *(.comment) }
}
