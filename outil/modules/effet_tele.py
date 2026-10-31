# -*- coding: utf-8 -*-
"""Effet tele : retire l'effet « vieille tele » de l'interface de pilotage et de la camera gimbal
(grain, lignes, bavure des couleurs, bords assombris). Choix du moddeur le 23/10/2026 (variante 2 de
maquette_camera_cc2.html) : memes tailles qu'aujourd'hui, image propre.

Remplace rom_0/shaders/screen_crt_hud.glsl (utilise par c_frontend_renderer::pass_hud_ui, l'interface
de pilotage dessinee en 256 px de haut, et pass_overlay_ui, le calque des ecrans de chargement).
Le calcul d'origine reste dans le fichier avec un poids nul, pour que le moteur retrouve tous ses
uniforms. Compile verifie par tests/test_effet_tele_web.html (WebGL 2).
"""
NOM = "effet_tele"
TITRE = "Vue de pilotage sans effet vieille tele"
TYPE = "fichier"
CIBLE = "shaders/screen_crt_hud.glsl"             # dans rom_0
SOURCE = "effet_tele/screen_crt_hud.glsl"         # dans fichiers/
ORIGINE_SHA256 = "ceadab0a21459350b0e75a3467fafd98ab7efb8eade5aaa1eec1458db83775f8"
