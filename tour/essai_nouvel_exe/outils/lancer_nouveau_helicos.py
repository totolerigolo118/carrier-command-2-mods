#!/usr/bin/env python3
"""Comme lancer_nouveau.py, mais pour la copie a QUATRE reglages : ascenseur_x2 + temps_x2 + pont_retour_x2 + helicos_approche_x2.

  python -I -B lancer_nouveau_helicos.py etat    --jeu DOSSIER_DU_JEU
  python -I -B lancer_nouveau_helicos.py copier  --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]
  python -I -B lancer_nouveau_helicos.py lancer  --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]
  python -I -B lancer_nouveau_helicos.py retirer --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]

Une seule nouveaute par rapport a la copie lancee le 31/10 (5AF41B4D...) : l'approche des helicos x2 (le point vise est 100 m
devant l'helico au lieu de 50 m ; valide sur le Mac le 24/10, jamais vu sur Windows). Copie fabriquee hors du jeu par patch_exe.py
et relue par verifier_copie_helicos.py. Memes garde-fous que lancer_nouveau.py (dont on reprend tout le code) ; seuls changent la
copie source, son nom dans le dossier du jeu, son sha256 et la liste exacte des modules exiges.
31/10 (frein v13 pose par la session « helicos + retour au hangar ») : `lancer` refuse si frein.ini active heli_recall (crochet H6
des helicos) : ce serait une deuxieme nouveaute dans cet essai ; la ligne « hook H6 » dans cc2x.log compte aussi comme un probleme.
02/11 (frein v14, pose par la session de coordination) : meme refus pour auto_recall (retour automatique au hangar) ; « auto_recall=1 »
(ligne des reglages) et « AUTO RECALL » dans cc2x.log comptent aussi comme un probleme. Les lanceurs multijoueur heritent de tout ceci.
"""
import importlib.util
import os
from pathlib import Path

ICI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('lancer_nouveau', ICI / 'lancer_nouveau.py')
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)

L.SOURCE = L.TRAVAIL / 'carrier_command_nouveau_patche_ascenseur_temps_pont_helicos.exe'
L.NOM = 'carrier_command_nouveau_2C9F8E47.exe'
L.SHA_COPIE = '2C9F8E47FD494BD3EF04038910C6E2A086742BCDA6AF71CACE2E1B69EA766F06'
L.MODULES_ATTENDUS = {'ascenseur_x2', 'temps_x2', 'pont_retour_x2', 'helicos_approche_x2'}
L.MAUVAISES = L.MAUVAISES + ('hook H6', 'auto_recall=1', 'AUTO RECALL')
_lancer_commun = L.cmd_lancer
# options du frein qui seraient une deuxieme nouveaute dans ces essais
OPTIONS_REFUSEES = {'heli_recall': 'helicos poses a la main : crochet H6 (v13) et helico tenu au sol (v15)', 'auto_recall': 'retour automatique au hangar, frein v14'}


def option_active(ini, nom):
    """Une ligne `nom` dont la valeur n'est pas exactement 0 (le frein lit toute valeur non nulle comme 1)."""
    if not ini.is_file():
        return False
    for ligne in ini.read_text(errors='replace').splitlines():
        cle, egal, valeur = ligne.split(';')[0].partition('=')
        if egal and cle.strip().lower() == nom and valeur.strip() != '0':
            return True
    return False


def cmd_lancer_sans_options(args):
    ini = Path(os.environ.get('APPDATA', '')) / 'Carrier Command 2' / 'cc2x' / 'frein.ini'
    for nom, quoi in OPTIONS_REFUSEES.items():
        if option_active(ini, nom):
            L.P.refus(f"{ini} active {nom} ({quoi}) : ce serait une deuxieme nouveaute dans cet essai ; rien n'est lance")
    _lancer_commun(args)


L.cmd_lancer = cmd_lancer_sans_options

if __name__ == '__main__':
    L.main()
