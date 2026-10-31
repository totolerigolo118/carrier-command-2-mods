#!/usr/bin/env python3
"""Pilote de reessais pour essai_auto.py : le jeu plante de facon intermittente au demarrage d'une partie (course interne, voir le journal).
Relance essai_auto.py (etat entierement restaure entre deux passes) jusqu'a ce qu'une passe se deroule SANS rapport de plantage Windows.

  python -I essai_auto_reessais.py ETIQUETTE [--max-passes N] -- <arguments passes tels quels a essai_auto.py 'lancer'>

Exemple :
  python -I essai_auto_reessais.py mesure --max-passes 5 -- --rom0 5 --accord-dossier-jeu --attente-menu 100000 --rouvrir --entrees "..."
Chaque passe s'appelle ETIQUETTE_p1, ETIQUETTE_p2... ; la derniere passe (sans plantage) est celle a lire."""
import datetime
import os
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
ESSAI = os.path.join(ICI, 'essai_auto.py')


def rapport_de(etiquette):
    base = os.environ.get('LOCALAPPDATA') or ICI
    return os.path.join(base, 'cc2_essais_auto', '%s_%s' % (datetime.date.today().isoformat(), etiquette), 'rapport.txt')


def sans_plantage(chemin):
    if not os.path.isfile(chemin):
        return False
    texte = open(chemin, encoding='utf-8', errors='replace').read()
    if 'tout est remis en etat' not in texte:
        return False                      # passe pas terminee proprement : on ne conclut pas
    for ligne in texte.splitlines():
        if 'rapports de plantage Windows pendant l' in ligne:
            return ligne.rstrip().endswith('aucun')
    return False


def main():
    if '--' not in sys.argv[1:] or len(sys.argv) < 3:
        sys.exit(__doc__)
    i = sys.argv.index('--')
    avant, apres = sys.argv[1:i], sys.argv[i + 1:]
    etiquette = avant[0]
    maxi = 5
    if '--max-passes' in avant:
        maxi = int(avant[avant.index('--max-passes') + 1])
    for n in range(1, maxi + 1):
        nom = '%s_p%d' % (etiquette, n)
        print('=== passe %d/%d : %s' % (n, maxi, nom), flush=True)
        r = subprocess.run([sys.executable, '-I', ESSAI, 'lancer', nom] + apres)
        chemin = rapport_de(nom)
        if sans_plantage(chemin):
            print('=== passe %s : SANS plantage, rapport %s' % (nom, chemin), flush=True)
            return 0
        print('=== passe %s : plantage ou passe incomplete (code %s) : on recommence' % (nom, r.returncode), flush=True)
    print('=== %d passes, toutes avec plantage' % maxi, flush=True)
    return 1


if __name__ == '__main__':
    sys.exit(main())
