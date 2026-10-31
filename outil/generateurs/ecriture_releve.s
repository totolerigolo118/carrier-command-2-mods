# Greffe « ecriture du releve » pour Carrier Command 2 (build_mac du 05/01/2026, md5 b0107170...).
#
# Le print() de Lua (luaB_print, 0x10283ae97) ecrit sur la sortie standard, que le jeu lance par Steam
# jette. Deux instructions de luaB_print lisent l'adresse de __stdoutp dans la GOT :
#   0x10283aed0  movq GOT(__stdoutp), %r12   (avant la boucle d'ecriture des arguments)
#   0x10283af78  movq GOT(__stdoutp), %rbx   (avant le "\n" final et fflush ; aussi le chemin print() sans argument)
# Elles deviennent « call _rv_r12 » et « call _rv_rbx » : le registre recoit l'adresse d'une case qui contient
# un FILE* ouvert une fois pour toutes (fopen « a » sur le fichier du releve), ou stdout si l'ouverture echoue.
# Case : guard variable de ShowExampleAppLog()::log (0x102a2a828, 8 octets en __bss), que seul le code mort
# de ImGui::ShowDemoWindow utilise.
# Pile : dans luaB_print, rsp = 0 mod 16 ; _rv_xxx entre a 8, _rv_ouvrir a 0 : l'appel a fopen est aligne.
# Seuls des registres libres a cet endroit de luaB_print sont modifies (rax, rcx, rdx, rsi, rdi, r8-r11).
# __CHEMIN__ est remplace par le generateur (le test le remplace par un fichier temporaire).

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
