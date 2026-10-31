# -*- coding: utf-8 -*-
"""Ecriture du releve : le print() de Lua ecrit dans un fichier au lieu de la sortie standard.

FICHIER GENERE par outil/generateurs/generer_ecriture_releve.py a partir de ecriture_releve.s
(ne pas modifier a la main). Demande du moddeur le 24/10/2026 (courbes du lag, regardees apres la partie).
Quand Steam lance le jeu, ce que les scripts Lua ecrivent avec print() est perdu. Ici, au premier print(),
le jeu ouvre (en ajout) /Users/UTILISATEUR/Library/Application Support/Carrier Command 2/releve_cc2.txt
et y ecrit tout ce que print() ecrit (si l'ouverture echoue : sortie standard, comme avant).
Deux instructions de luaB_print (0x10283aed0 et 0x10283af78) appellent du code ajoute (une soixantaine d'octets,
plus le chemin du fichier) dans le code mort de ImGui::ShowDemoWindow ; le FILE* est garde dans une case que seul
ce code mort utilisait.
Sans le module « releve » (library_custom_5.lua), seuls les print() des mods arrivent dans le fichier.
"""
NOM = 'ecriture_releve'
TITRE = 'Releve : print() ecrit dans un fichier (courbes du lag)'
TYPE = "programme"
# md5 du programme avec ce module seul : 8655d7175105c0fe4e488f4e36b0075f

RETOUCHES = [
    # code ajoute (165 octets, dont le chemin du fichier) dans le code mort de ImGui::ShowDemoWindow
    ("imm", 0x100061a00, "8d35e28c9c02488d15f3e5f9ffe80a638002488d3d0f8e9c02e822638002e953a2ffff488d3da68e9c02e80b63800285c00f84fb9bffff660fefc0f30f7f057d8e9c02488d35768e9c02488d3df74c0400488d15a8e5f9ffe8bf628002488d3d6c8e9c02e8d7628002e9c49bffff488d3ddb8d9c02e8c062800285c00f845ba8ffff660fefc0f30f7f05b28d9c02488d35ab8d9c02488d3dc2db0300488d155de5f9ffe874", "e8150000004c8d251c8e9c02c3e808000000488d1d0f8e9c02c3488b05078e9c024885c07529488d3d23000000488d356f000000e83f6480024885c0750a488b05abc59302488b00488905d98d9c02c32f55736572732f74686f6d617373616e63656e6f742f4c6962726172792f4170706c69636174696f6e20537570706f72742f4361727269657220436f6d6d616e6420322f72656c6576655f6363322e747874006100"),
    # movq GOT(__stdoutp), %r12 (luaB_print, avant les arguments) -> call _rv_r12 (0x100061a00)
    ("imm", 0x10283aed0, "4c8b2519311600", "e82b6b82fd6690"),
    # movq GOT(__stdoutp), %rbx (luaB_print, "\n" final et fflush) -> call _rv_rbx (0x100061a0d)
    ("imm", 0x10283af78, "488b1d71301600", "e8906a82fd6690"),
]
