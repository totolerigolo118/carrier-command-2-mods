# -*- coding: utf-8 -*-
"""Vitesse de l'escadrille : barre ECO / NORMAL / FLANK en bas a droite des ecrans de controle des
vehicules (screen_veh_l/m/r/ll et tacops_*_control du porte-avions de Revolution). Un clic choisit la
vitesse de croisiere de tous les avions de l'equipe pilotes par l'IA. Premiere fois : NORMAL ; ensuite le
dernier mode est repris d'une partie a l'autre.

A utiliser AVEC le module programme « vitesse_escadrille » (qui ajoute la fonction Lua cc2_vitesse) :
sans lui, la barre ne s'affiche pas et rien ne change.
Remplace rom_0/scripts/library_custom_6.lua, un fichier VIDE prevu par le jeu pour les ajouts.
Source : fichiers/vitesse_boutons/library_custom_6.lua ; test hors jeu : tests/test_vitesse_boutons.py.
Etude : etudes/ia_vitesse.md (demande du moddeur le 25/10/2026, variante 1 de etudes/maquette_vitesse_ia.html).
"""
NOM = "vitesse_boutons"
TITRE = "Vitesse de l'escadrille (ECO / NORMAL / FLANK) : boutons"
TYPE = "fichier"
CIBLE = "scripts/library_custom_6.lua"              # dans rom_0
SOURCE = "vitesse_boutons/library_custom_6.lua"     # dans fichiers/
ORIGINE_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"   # fichier vide
