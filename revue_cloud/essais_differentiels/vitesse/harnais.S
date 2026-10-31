    .text
    .globl run_case
    .globl epi_start
    .globl epi_end
    .globl target
    .globl saved_rsp
    .globl rsp_avant_appel
    .globl bad_align
    .globl h_gettop, h_tointegerx, h_pushinteger, h_fopen, h_fgetc, h_fputs, h_fclose
    .globl call_sentinel

# void run_case(struct cpu *in)
run_case:
    pushq %rbp
    pushq %rbx
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15
    movq %rsp, saved_rsp(%rip)
    movq %rdi, %r15
    movups 0x80(%r15), %xmm0
    movups 0x90(%r15), %xmm1
    movups 0xa0(%r15), %xmm2
    movups 0xb0(%r15), %xmm3
    movups 0xc0(%r15), %xmm4
    movups 0xd0(%r15), %xmm5
    movups 0xe0(%r15), %xmm6
    movups 0xf0(%r15), %xmm7
    movups 0x100(%r15), %xmm8
    movups 0x110(%r15), %xmm9
    movups 0x120(%r15), %xmm10
    movups 0x130(%r15), %xmm11
    movups 0x140(%r15), %xmm12
    movups 0x150(%r15), %xmm13
    movups 0x160(%r15), %xmm14
    movups 0x170(%r15), %xmm15
    pushq 0x180(%r15)
    popfq
    movq 0x00(%r15), %rax
    movq 0x08(%r15), %rcx
    movq 0x10(%r15), %rdx
    movq 0x18(%r15), %rbx
    movq 0x28(%r15), %rbp
    movq 0x30(%r15), %rsi
    movq 0x38(%r15), %rdi
    movq 0x40(%r15), %r8
    movq 0x48(%r15), %r9
    movq 0x50(%r15), %r10
    movq 0x58(%r15), %r11
    movq 0x60(%r15), %r12
    movq 0x68(%r15), %r13
    movq 0x70(%r15), %r14
    movq 0x78(%r15), %r15
    movq %rsp, rsp_avant_appel(%rip)
    call *target(%rip)
    movq saved_rsp(%rip), %rsp
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %rbx
    popq %rbp
    ret

# epilogue copie a 0x1001c2b8e : sauvegarde tout a 0x20000000 puis ret
epi_start:
    pushfq
    popq 0x20000180
    movq %rax, 0x20000000
    movq %rcx, 0x20000008
    movq %rdx, 0x20000010
    movq %rbx, 0x20000018
    movq %rsp, 0x20000020
    movq %rbp, 0x20000028
    movq %rsi, 0x20000030
    movq %rdi, 0x20000038
    movq %r8,  0x20000040
    movq %r9,  0x20000048
    movq %r10, 0x20000050
    movq %r11, 0x20000058
    movq %r12, 0x20000060
    movq %r13, 0x20000068
    movq %r14, 0x20000070
    movq %r15, 0x20000078
    movups %xmm0, 0x20000080
    movups %xmm1, 0x20000090
    movups %xmm2, 0x200000a0
    movups %xmm3, 0x200000b0
    movups %xmm4, 0x200000c0
    movups %xmm5, 0x200000d0
    movups %xmm6, 0x200000e0
    movups %xmm7, 0x200000f0
    movups %xmm8, 0x20000100
    movups %xmm9, 0x20000110
    movups %xmm10,0x20000120
    movups %xmm11,0x20000130
    movups %xmm12,0x20000140
    movups %xmm13,0x20000150
    movups %xmm14,0x20000160
    movups %xmm15,0x20000170
    ret
epi_end:

# wrappers verifiant l'alignement de pile a l'entree (rsp % 16 == 8) puis sautant a la fonction C
.macro WRAP name, cfn
\name:
    movq %rsp, %r11
    andq $0xf, %r11
    cmpq $8, %r11
    je 1f
    movq $1, bad_align(%rip)
1:  jmp \cfn
.endm
    WRAP h_gettop, c_gettop
    WRAP h_tointegerx, c_tointegerx
    WRAP h_pushinteger, c_pushinteger
    WRAP h_fopen, c_fopen
    WRAP h_fgetc, c_fgetc
    WRAP h_fputs, c_fputs
    WRAP h_fclose, c_fclose

# long call_sentinel(void *fn, void *arg, uint64_t out[8]) : appelle fn(arg) avec des sentinelles dans les registres callee-saved
call_sentinel:
    pushq %rbp
    pushq %rbx
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15
    pushq %rdx          # out
    movq $0x1111111111111111, %rbx
    movq $0x2222222222222222, %rbp
    movq $0x3333333333333333, %r12
    movq $0x4444444444444444, %r13
    movq $0x5555555555555555, %r14
    movq $0x6666666666666666, %r15
    movq %rdi, %rax
    movq %rsi, %rdi
    movq %rsp, rsp_avant_appel(%rip)
    call *%rax
    movq (%rsp), %rdx
    movq %rbx, 0(%rdx)
    movq %rbp, 8(%rdx)
    movq %r12, 16(%rdx)
    movq %r13, 24(%rdx)
    movq %r14, 32(%rdx)
    movq %r15, 40(%rdx)
    movq %rsp, 48(%rdx)
    popq %rdx
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %rbx
    popq %rbp
    ret

    .data
target: .quad 0
saved_rsp: .quad 0
rsp_avant_appel: .quad 0
bad_align: .quad 0
