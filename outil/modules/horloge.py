# -*- coding: utf-8 -*-
"""Horloge de jeu : affiche « TEMPS DE JEU h:mm:ss.s » (update_get_logic_tick()/30) en bas a gauche
des ecrans de controle des vehicules (screen_veh_l/m/r). Sert a mesurer en temps de jeu, sans que
le lag du Mac fausse la mesure. Ne change rien au jeu.

Remplace rom_0/scripts/library_custom_1.lua, un fichier VIDE prevu par le jeu pour les ajouts.
Source : fichiers/horloge/library_custom_1.lua ; test hors jeu : tests/test_horloge.py.
"""
NOM = "horloge"
TITRE = "Horloge de jeu sur les ecrans de controle des vehicules"
TYPE = "fichier"
CIBLE = "scripts/library_custom_1.lua"            # dans rom_0
SOURCE = "horloge/library_custom_1.lua"           # dans fichiers/
ORIGINE_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"   # fichier vide
