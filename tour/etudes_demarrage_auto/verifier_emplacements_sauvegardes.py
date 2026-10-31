#!/usr/bin/env python3
"""LECTURE SEULE (n'ecrit rien, ne lance rien) : prevoit si le CHARGEMENT d'une sauvegarde risque de faire planter le jeu.

Pourquoi (voir ETUDE.md, section 4) : au chargement, le jeu recree chaque vehicule d'apres sa definition (nombre d'emplacements
d'equipement), puis relit les equipements enregistres dans la sauvegarde SANS verifier qu'il y a assez d'emplacements
(fonction 0x5EF2D0 de carrier_command.exe 1.5.18). Une sauvegarde faite avec un mod qui AJOUTE des emplacements (Revolution)
et rechargee sans ce mod depasse donc les tableaux : plantage 0xC0000005 en 0x1EF518 / 0x1EF525.

  python -I verifier_emplacements_sauvegardes.py                       # mods actifs = ceux de mods.xml
  python -I verifier_emplacements_sauvegardes.py --ajouter-mod "C:\\...\\workshop\\content\\1489630\\3460002110"   # "et si Revolution etait actif ?"
  python -I verifier_emplacements_sauvegardes.py --mods-xml AUTRE.xml --sauvegardes DOSSIER --jeu DOSSIER

Pour chaque slot : "tient" (le plus grand nombre d'equipements enregistres par modele de vehicule <= emplacements definis) ou
"DEPASSE" (chargement probablement fatal). Correspondance indice de definition -> fichier : deduite des noms (library_enum.lua),
sure pour le porte-avions (0), supposee pour les autres.
"""
import argparse
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

APPDATA = os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2')
JEU = r'C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2'
FICHIERS = {0: 'carrier', 2: 'wheel_small', 4: 'wheel_medium', 6: 'wheel_heavy', 8: 'wing_small', 10: 'wing_heavy',
            12: 'rotor_small', 14: 'rotor_heavy', 16: 'barge'}


def emplacements(dossiers, nom):
    """Nombre d'equipements definis pour le modele : le DERNIER dossier de la liste qui fournit le fichier l'emporte (comme les mods)."""
    compte = None
    for d in dossiers:
        p = os.path.join(d, 'vehicle_chassis_%s.xml' % nom)
        if os.path.isfile(p):
            t = open(p, encoding='utf-8', errors='replace').read()
            m = re.search(r'<attachments>(.*?)</attachments>', t, re.S)
            compte = len(re.findall(r'<(?:a|attachment)[ />]', m.group(1))) if m else 0
    return compte


def maxima_sauvegarde(chemin):
    t = open(chemin, encoding='utf-8', errors='replace').read()
    t = re.sub(r'^<\?xml[^>]*\?>', '', t.strip())
    racine = ET.fromstring('<racine>' + t + '</racine>')          # le fichier a deux elements racine (meta, scene)
    mx = defaultdict(int)
    for el in racine.iter():
        atts = el.find('attachments')
        if atts is None or el.find('bodies') is None:               # seuls les vehicules "vivants" ont des corps
            continue
        di = el.get('definition_index')
        if di is not None and int(di) in FICHIERS:
            mx[int(di)] = max(mx[int(di)], len(atts.findall('a')))
    return mx


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--mods-xml', default=os.path.join(APPDATA, 'mods.xml'))
    ap.add_argument('--sauvegardes', default=os.path.join(APPDATA, 'saved_games'))
    ap.add_argument('--jeu', default=JEU)
    ap.add_argument('--ajouter-mod', action='append', default=[], help='dossier d\'un mod a ajouter en fin de liste (simulation)')
    a = ap.parse_args()
    mods = []
    if os.path.isfile(a.mods_xml):
        mods = re.findall(r'<path value="([^"]*)"', open(a.mods_xml, encoding='utf-8', errors='replace').read())
    mods += a.ajouter_mod
    dossiers = [os.path.join(a.jeu, 'rom_0', 'game_objects')] + [os.path.join(m, 'content', 'game_objects') for m in mods]
    print('mods pris en compte :', ', '.join(os.path.basename(m.rstrip('\\/')) for m in mods) or '(aucun)')
    defs = {di: emplacements(dossiers, nom) for di, nom in FICHIERS.items()}
    print('emplacements d\'equipement par modele :', ', '.join('%s=%s' % (FICHIERS[di], n) for di, n in defs.items()))
    fichiers = sorted(glob.glob(os.path.join(a.sauvegardes, 'slot_*', 'save.xml')), key=lambda x: int(re.search(r'slot_(\d+)', x).group(1)))
    if not fichiers:
        sys.exit('aucune sauvegarde trouvee dans %s' % a.sauvegardes)
    mauvais = 0
    for p in fichiers:
        mx = maxima_sauvegarde(p)
        trop = ['%s : %d enregistres > %d definis' % (FICHIERS[d], m, defs[d]) for d, m in sorted(mx.items()) if defs[d] is not None and m > defs[d]]
        mauvais += bool(trop)
        print('%-8s %s' % (re.search(r'(slot_\d+)', p).group(1), ('DEPASSE (chargement probablement fatal) : ' + '; '.join(trop)) if trop else 'tient'))
    print('%d sauvegarde(s) sur %d depassent les emplacements definis.' % (mauvais, len(fichiers)))
    return 1 if mauvais else 0


if __name__ == '__main__':
    sys.exit(main())
