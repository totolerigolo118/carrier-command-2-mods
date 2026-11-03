#!/usr/bin/env python3
"""Comme lancer_nouveau_helicos.py, mais pour la copie MULTIJOUEUR a 5 reglages : ascenseur_x2 + pont_retour_x2 + helicos_approche_x2
+ atterrissage_cercle + atterrissage_creneau, SANS temps_x2 (SIM x1, comme le jeu de l'ami).

  python -I -B lancer_multi_5.py etat|copier|lancer|retirer --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]

ATTENTION : cercle et creneau n'ont jamais tourne sur le nouvel exe, ni avec le frein (le creneau envoie des avions du virage arriere
vers le bloc qui mene au crochet H2 du frein, 19 octets avant lui). Copie fabriquee hors du jeu le 31/10 par patch_exe.py, relue par
verifier_copies_multi.py (= la copie multi a 3 reglages + cercle + creneau). Memes garde-fous que lancer_nouveau_helicos.py.
"""
import importlib.util
from pathlib import Path

ICI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('lancer_nouveau_helicos', ICI / 'lancer_nouveau_helicos.py')
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)
L = H.L

L.SOURCE = L.TRAVAIL / 'carrier_command_nouveau_multi_ascenseur_pont_helicos_cercle_creneau.exe'
L.NOM = 'carrier_command_nouveau_FCB3CDE1.exe'
L.SHA_COPIE = 'FCB3CDE18346DACE6D86D217733F1E617AE1DD88BBE033A4AC8F6FDBE3313CFC'
L.MODULES_ATTENDUS = {'ascenseur_x2', 'pont_retour_x2', 'helicos_approche_x2', 'atterrissage_cercle', 'atterrissage_creneau'}

if __name__ == '__main__':
    L.main()
