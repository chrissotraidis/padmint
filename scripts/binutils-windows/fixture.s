# Synthetic MIPS fixture: the assembler features an N64 decompilation build uses.
        .set noreorder
        .set noat
        .section .text
        .globl entry
entry:
        lui     $t0, %hi(data_word)
        addiu   $t0, $t0, %lo(data_word)
        lw      $t1, 0($t0)
        jal     helper
        nop
        beq     $t1, $zero, done
        addiu   $t1, $t1, -1
        sw      $t1, 4($t0)
done:
        jr      $ra
        nop
        .globl helper
helper:
        lwc1    $f0, 8($t0)
        mul.s   $f2, $f0, $f0
        swc1    $f2, 12($t0)
        mfc0    $k0, $12
        jr      $ra
        nop
        .section .data
        .align 4
        .globl data_word
data_word:
        .word   0x80000400, 3, 0x3fc00000, 0
        .asciz  "PadMint MIPS fixture"
        .section .rodata
        .align 3
        .double 1.5
