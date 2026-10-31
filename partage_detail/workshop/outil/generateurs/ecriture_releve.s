# Patch "writing the log" (releve) for Carrier Command 2 (build_mac of 2026-01-05, md5 b0107170...).
#
# Lua's print() (luaB_print, 0x10283ae97) writes to standard output, which the game, when launched by Steam,
# throws away. Two instructions of luaB_print read the address of __stdoutp from the GOT:
#   0x10283aed0  movq GOT(__stdoutp), %r12   (before the loop that writes the arguments)
#   0x10283af78  movq GOT(__stdoutp), %rbx   (before the final "\n" and fflush; also the print() without arguments path)
# They become "call _rv_r12" and "call _rv_rbx": the register receives the address of a cell that holds
# a FILE* opened once and for all (fopen "a" on the log file), or stdout if the open fails.
# Cell: guard variable of ShowExampleAppLog()::log (0x102a2a828, 8 bytes in __bss), which only the dead code
# of ImGui::ShowDemoWindow uses.
# Stack: in luaB_print, rsp = 0 mod 16; _rv_xxx is entered at 8, _rv_ouvrir at 0: the call to fopen is aligned.
# Only registers that are free at this point of luaB_print are modified (rax, rcx, rdx, rsi, rdi, r8-r11).
# __CHEMIN__ is replaced by the generator (the test replaces it with a temporary file).

.text
.globl _rv_r12
_rv_r12:
    call _rv_ouvrir
    leaq _g_case(%rip), %r12
    ret

.globl _rv_rbx
_rv_rbx:
    call _rv_ouvrir
    leaq _g_case(%rip), %rbx
    ret

_rv_ouvrir:
    movq _g_case(%rip), %rax
    testq %rax, %rax
    jne 1f
    leaq L_chemin(%rip), %rdi
    leaq L_mode(%rip), %rsi
    call _g_fopen
    testq %rax, %rax
    jne 2f
    movq _g_got_stdoutp(%rip), %rax
    movq (%rax), %rax
2:
    movq %rax, _g_case(%rip)
1:
    ret

L_chemin:
    .asciz "__CHEMIN__"
L_mode:
    .asciz "a"
