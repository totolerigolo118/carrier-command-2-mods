.text
.globl run_regs
run_regs:
    pushq %rbp
    pushq %rbx
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15
    subq $8, %rsp
    movq %rsp, g_rsp(%rip)
    movq %rdi, g_entry(%rip)
    movups g_in+144(%rip), %xmm0
    movups g_in+160(%rip), %xmm1
    movups g_in+176(%rip), %xmm2
    movups g_in+192(%rip), %xmm3
    movups g_in+208(%rip), %xmm4
    movups g_in+224(%rip), %xmm5
    movups g_in+240(%rip), %xmm6
    movups g_in+256(%rip), %xmm7
    movups g_in+272(%rip), %xmm8
    movups g_in+288(%rip), %xmm9
    movups g_in+304(%rip), %xmm10
    movups g_in+320(%rip), %xmm11
    movups g_in+336(%rip), %xmm12
    movups g_in+352(%rip), %xmm13
    movups g_in+368(%rip), %xmm14
    movups g_in+384(%rip), %xmm15
    pushq g_in+0x88(%rip)
    popfq
    movq g_in+0(%rip), %rax
    movq g_in+8(%rip), %rbx
    movq g_in+16(%rip), %rcx
    movq g_in+24(%rip), %rdx
    movq g_in+32(%rip), %rsi
    movq g_in+40(%rip), %rdi
    movq g_in+48(%rip), %rbp
    movq g_in+64(%rip), %r8
    movq g_in+72(%rip), %r9
    movq g_in+80(%rip), %r10
    movq g_in+88(%rip), %r11
    movq g_in+96(%rip), %r12
    movq g_in+104(%rip), %r13
    movq g_in+112(%rip), %r14
    movq g_in+120(%rip), %r15
    jmp *g_entry(%rip)
.globl g_ret_a, g_ret_b, g_ret_c, g_ret_d
g_ret_a:
g_ret_b:
g_ret_c:
g_ret_d:
    pushfq
    popq g_out+0x88(%rip)
    movq %rax, g_out+0(%rip)
    movq %rbx, g_out+8(%rip)
    movq %rcx, g_out+16(%rip)
    movq %rdx, g_out+24(%rip)
    movq %rsi, g_out+32(%rip)
    movq %rdi, g_out+40(%rip)
    movq %rbp, g_out+48(%rip)
    movq %rsp, g_out+56(%rip)
    movq %r8, g_out+64(%rip)
    movq %r9, g_out+72(%rip)
    movq %r10, g_out+80(%rip)
    movq %r11, g_out+88(%rip)
    movq %r12, g_out+96(%rip)
    movq %r13, g_out+104(%rip)
    movq %r14, g_out+112(%rip)
    movq %r15, g_out+120(%rip)
    movups %xmm0, g_out+144(%rip)
    movups %xmm1, g_out+160(%rip)
    movups %xmm2, g_out+176(%rip)
    movups %xmm3, g_out+192(%rip)
    movups %xmm4, g_out+208(%rip)
    movups %xmm5, g_out+224(%rip)
    movups %xmm6, g_out+240(%rip)
    movups %xmm7, g_out+256(%rip)
    movups %xmm8, g_out+272(%rip)
    movups %xmm9, g_out+288(%rip)
    movups %xmm10, g_out+304(%rip)
    movups %xmm11, g_out+320(%rip)
    movups %xmm12, g_out+336(%rip)
    movups %xmm13, g_out+352(%rip)
    movups %xmm14, g_out+368(%rip)
    movups %xmm15, g_out+384(%rip)
    movq g_rsp(%rip), %rsp
    addq $8, %rsp
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %rbx
    popq %rbp
    ret

.globl orig_a, orig_b, orig_c, orig_d, cave_a, cave_b, cave_c, cave_d
cave_a: jmp cctv_a
cave_b: jmp cctv_b
cave_c: jmp cctv_c
cave_d: jmp cctv_d
orig_a:
    movslq 0x60(%rax,%rcx), %rax
    movl $0x80, %r9d
    movl $0x80, %r8d
    cmpq $5, %rax
    ja 2f
    leaq g_tab_haut(%rip), %rcx
    movl (%rcx,%rax,4), %r9d
    leaq g_tab_larg(%rip), %rcx
    movl (%rcx,%rax,4), %r8d
2:  jmp g_ret_a
orig_b:
    movl 0x20(%r14), %ecx
    xorps %xmm0, %xmm0
    cvtsi2ss %rcx, %xmm0
    movl 0x24(%r14), %ecx
    cvtsi2ss %rcx, %xmm2
    jmp g_ret_b
orig_c:
    movss g_demi(%rip), %xmm0
    movss 0x14(%rdi), %xmm1
    addss %xmm0, %xmm1
    roundss $9, %xmm1, %xmm1
    cvttss2si %xmm1, %ecx
    addss 0x10(%rdi), %xmm0
    roundss $9, %xmm0, %xmm0
    cvttss2si %xmm0, %edx
    xorps %xmm0, %xmm0
    roundss $9, 0xc(%rdi), %xmm0
    cvttss2si %xmm0, %esi
    xorps %xmm0, %xmm0
    roundss $9, 0x8(%rdi), %xmm0
    cvttss2si %xmm0, %edi
    jmp g_ret_c
orig_d:
    movl $0xb44, %edi
    jmp g_ret_d
.data
.p2align 4
.globl g_in, g_out, g_rsp, g_entry, g_tab_haut, g_tab_larg, g_128, g_demi, g_echelle
g_in: .space 0x190
g_out: .space 0x190
g_rsp: .quad 0
g_entry: .quad 0
g_tab_haut: .long 128, 128, 256, 256, 192, 32
g_tab_larg: .long 128, 256, 512, 256, 256, 64
g_128: .float 128.0
g_demi: .float 0.5
g_echelle: .long 0
