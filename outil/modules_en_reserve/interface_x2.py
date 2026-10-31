# -*- coding: utf-8 -*-
"""Interface x2 : l'interface de pilotage et de la camera gimbal (viseur, echelles, textes) dessinee
en 512 pixels de haut au lieu de 256, donc deux fois plus nette. Contrepartie : le jeu la place en
pixels fixes, ses elements sont deux fois plus petits a l'ecran (le moddeur : « ca ne me derange pas »).
Demande le 23/10/2026, variante 5 de maquette_camera_cc2.html (avec effet_tele = sans effet).

Cible `hud_ui_target`, creee dans c_frontend_renderer::update :
  hauteur  : movl $0x100, %r9d          -> $0x200          (256 -> 512 px)
  largeur  : (largeur/hauteur ecran) x [256.0] -> x [512.0] (constante existante 0x102869b58)
Le monde 3D n'est pas concerne (deja en pleine resolution). Cout en performances quasi nul (2D).
"""
NOM = "interface_x2"
TITRE = "Interface de pilotage 2x plus fine (elements 2x plus petits)"
TYPE = "programme"

RETOUCHES = [
    ("imm", 0x1001ed3f4, "41b900010000", "41b900020000"),               # hauteur 256 -> 512
    ("rip", 0x1001ed3b7, "f30f590585c56702", 0x102869944, 0x102869b58, 2),  # mulss 256.0 -> 512.0
]
