#!/usr/bin/env python3
"""Comme lancer_nouveau_helicos.py, mais pour la copie MULTIJOUEUR a 3 reglages (la prudente) : ascenseur_x2 + pont_retour_x2 +
helicos_approche_x2, SANS temps_x2 (SIM x1, comme le jeu de l'ami) et sans cercle ni creneau.

  python -I -B lancer_multi_3.py etat|copier|lancer|retirer --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]

Copie fabriquee hors du jeu le 31/10 par patch_exe.py, relue par verifier_copies_multi.py (= la copie helicos 2C9F8E47... sans
temps_x2). Memes garde-fous que lancer_nouveau_helicos.py (dont le refus si frein.ini active heli_recall) ; seuls changent la copie
source, son nom dans le dossier du jeu, son sha256 et la liste exacte des modules exiges.
"""
import importlib.util
from pathlib import Path

ICI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('lancer_nouveau_helicos', ICI / 'lancer_nouveau_helicos.py')
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)
L = H.L

L.SOURCE = L.TRAVAIL / 'carrier_command_nouveau_multi_ascenseur_pont_helicos.exe'
L.NOM = 'carrier_command_nouveau_795CD61D.exe'
L.SHA_COPIE = '795CD61DE271F8DA4B97F499491DD3CBCCED1A1433EBEBFCB63A182AF4AA1A0E'
L.MODULES_ATTENDUS = {'ascenseur_x2', 'pont_retour_x2', 'helicos_approche_x2'}

if __name__ == '__main__':
    L.main()
