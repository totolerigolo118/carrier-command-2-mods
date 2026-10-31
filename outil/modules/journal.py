# -*- coding: utf-8 -*-
"""Journal des atterrissages : chronometre tout seul les retours d'avions et d'helicos sur le
porte-avions (entree dans la file, piste donnee, toucher du pont, rangement au hangar, approches
ratees) et affiche le resultat en temps de jeu au-dessus de l'horloge, sur les ecrans de controle des
vehicules (screen_veh_l/m/r). Sert a mesurer les modules d'atterrissage. Ne change rien au jeu.

Remplace rom_0/scripts/library_custom_4.lua, un fichier VIDE prevu par le jeu pour les ajouts
(0 = fumee tricolore, 1 = horloge, 2 et 3 = mods Workshop inactifs 3398249587 et 3225306468).
Source : fichiers/journal/library_custom_4.lua ; test hors jeu : tests/test_journal.py.
"""
NOM = "journal"
TITRE = "Journal des atterrissages (chronometre automatique)"
TYPE = "fichier"
CIBLE = "scripts/library_custom_4.lua"            # dans rom_0
SOURCE = "journal/library_custom_4.lua"           # dans fichiers/
ORIGINE_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"   # fichier vide
