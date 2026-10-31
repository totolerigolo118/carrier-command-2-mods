# -*- coding: utf-8 -*-
"""Releve des performances : note pendant la partie (toutes les 5 et 10 s) la vitesse du jeu, les unites par
equipe et par type, les missiles et obus en vol, les ecrans qui tournent et ce que fait le joueur (pont,
carte, pilotage). N'affiche rien et ne change rien au jeu. Demande du moddeur le 24/10/2026 (courbes du lag,
regardees apres la partie : outil/courbes/faire_courbes.py).

Remplace rom_0/scripts/library_custom_5.lua, un fichier VIDE prevu par le jeu pour les ajouts
(0 = fumee tricolore, 1 = horloge, 4 = journal ; 2 et 3 = mods Workshop inactifs).
Les lignes sont ecrites avec print() : il faut aussi le module « ecriture_releve » (sinon elles sont perdues).
Source : fichiers/releve/library_custom_5.lua ; test hors jeu : tests/test_releve.py.
"""
NOM = "releve"
TITRE = "Releve des performances (pour les courbes du lag)"
TYPE = "fichier"
CIBLE = "scripts/library_custom_5.lua"            # dans rom_0
SOURCE = "releve/library_custom_5.lua"            # dans fichiers/
ORIGINE_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"   # fichier vide
