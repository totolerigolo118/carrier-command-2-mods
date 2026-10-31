# Patches "sharper CCTV screen" for Carrier Command 2 (build_mac of 2026-01-05, md5 b0107170...).
#
# The image of a bridge screen serves both as the background (the camera view) and as the Lua script's interface.
# Its size comes from a per-screen-type table (type 0 = 128 x 128, 35 screens). Here, only the screen whose script
# is "scripts/screen_cctv.lua" gets a TAILLE x TAILLE image; the interface keeps its 128 units.
#   A  create_lite 0x1000ad74f  : image size at creation (tables 0x1028b1470 / 0x1028b1488)
#   B  render_screen 0x10021ce70 : interface camera = 128 x 128 if the image is TAILLE x TAILLE,
#                                  and scale = TAILLE / 128 in g_echelle (0 = no scale)
#   C  element_clip 0x10015e662  : glScissor(x, y, w, h) multiplied by the scale
#   D  render_screen 0x10021cf13 : scale reset to 0 after the interface (piloting, pause, overlay underneath)
# g_echelle: ShowExampleAppSimpleOverlay()::corner (0x102a2a864, __bss, 4 bytes), read only by the dead code.
# Registers: only those that the original code overwrites right after (A: rax rcx rdx r8 r9 ; B: rcx xmm0 xmm2 ;
# C: xmm0-xmm3 ecx edx esi edi ; D: edi).
# TAILLE and ECHELLE (bits of the float TAILLE / 128) are defined by the generator.

.text
.globl _cctv_a
_cctv_a:                                # rax = screen definitions, rcx = index x 0x78
    leaq (%rax,%rcx), %rdx
    movslq 0x60(%rdx), %rax             # screen type (original instruction)
    cmpl $23, 0x20(%rdx)                # length of script_file_name (mm_string: text 0x18, length 0x20)
    jne 1f
    movq 0x18(%rdx), %rcx
    testq %rcx, %rcx
    je 1f
    movq (%rcx), %r8
    cmpq L_script(%rip), %r8
    jne 1f
    movq 8(%rcx), %r8
    cmpq L_script+8(%rip), %r8
    jne 1f
    movq 15(%rcx), %r8
    cmpq L_script+15(%rip), %r8
    jne 1f
    movl $TAILLE, %r9d
    movl $TAILLE, %r8d
    jmp g_ret_a
1:                                      # original code
    movl $0x80, %r9d
    movl $0x80, %r8d
    cmpq $5, %rax
    ja 2f
    leaq g_tab_haut(%rip), %rcx
    movl (%rcx,%rax,4), %r9d
    leaq g_tab_larg(%rip), %rcx
    movl (%rcx,%rax,4), %r8d
2:
    jmp g_ret_a

.globl _cctv_b
_cctv_b:                                # r14 = screen image (width 0x20, height 0x24)
    movl 0x20(%r14), %ecx
    cmpl $TAILLE, %ecx
    jne 1f
    cmpl $TAILLE, 0x24(%r14)
    jne 1f
    movss g_128(%rip), %xmm0
    movss g_128(%rip), %xmm2
    movl $ECHELLE, g_echelle(%rip)
    jmp g_ret_b
1:                                      # original code
    xorps %xmm0, %xmm0
    cvtsi2ss %rcx, %xmm0
    movl 0x24(%r14), %ecx
    cvtsi2ss %rcx, %xmm2
    movl $0, g_echelle(%rip)
    jmp g_ret_b

.globl _cctv_c
_cctv_c:                                # rdi = element : x 0x8, y 0xc, w 0x10, h 0x14
    movss g_echelle(%rip), %xmm2
    xorps %xmm3, %xmm3
    ucomiss %xmm3, %xmm2
    jne 1f
    movss g_demi(%rip), %xmm0           # original code
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
1:                                      # same computation, interface units x scale
    movss 0x14(%rdi), %xmm1
    mulss %xmm2, %xmm1
    addss g_demi(%rip), %xmm1
    roundss $9, %xmm1, %xmm1
    cvttss2si %xmm1, %ecx
    movss 0x10(%rdi), %xmm0
    mulss %xmm2, %xmm0
    addss g_demi(%rip), %xmm0
    roundss $9, %xmm0, %xmm0
    cvttss2si %xmm0, %edx
    movss 0xc(%rdi), %xmm0
    mulss %xmm2, %xmm0
    roundss $9, %xmm0, %xmm0
    cvttss2si %xmm0, %esi
    movss 0x8(%rdi), %xmm0
    mulss %xmm2, %xmm0
    roundss $9, %xmm0, %xmm0
    cvttss2si %xmm0, %edi
    jmp g_ret_c

.globl _cctv_d
_cctv_d:
    movl $0, g_echelle(%rip)
    movl $0xb44, %edi                   # original instruction
    jmp g_ret_d

L_script:
    .ascii "scripts/screen_cctv.lua"
