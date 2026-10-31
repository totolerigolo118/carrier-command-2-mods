#!/usr/bin/env python3
"""Active / desactive des mods dans mods.xml, de facon reversible et sauvegardee.

  python mods_actifs.py etat       [--racine DOSSIER]
  python mods_actifs.py desactiver --nom pack_moddeur --nom boite_noire [--suffixe b] [--jeu-ouvert-ok]
  python mods_actifs.py restaurer  --depuis mods.xml.bak_2026-10-27b [--jeu-ouvert-ok]

--racine vaut par defaut %APPDATA%\\Carrier Command 2. `desactiver` retire de la liste active_mod_folders
les lignes dont le dossier se termine par --nom (les deux ecritures du chemin, avec \\ ou /), apres une
sauvegarde datee (mods.xml.bak_AAAA-MM-JJ + suffixe). Les DOSSIERS des mods ne sont jamais touches ni
supprimes : on peut tout reactiver avec `restaurer`. Refuse si le jeu tourne (sauf --jeu-ouvert-ok :
dans ce cas le changement ne compte qu'au prochain lancement).
"""
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import xml.dom.minidom


def jeu_ouvert():
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq carrier_command.exe', '/NH'],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return None
    return 'carrier_command.exe' in out.lower()


def lire(p):
    with open(p, 'rb') as f:
        return f.read()


def ecrire_atomique(p, octets):
    tmp = p + '.cc2_tmp'
    try:
        with open(tmp, 'wb') as f:
            f.write(octets)
            f.flush()
            os.fsync(f.fileno())
        if lire(tmp) != octets:
            raise RuntimeError('relecture du fichier temporaire differente')
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


RE_PATH = re.compile(r'^[ \t]*<path value="([^"]*)"/>[ \t]*$')


def chemins_actifs(txt):
    return [m.group(1) for ln in txt.split('\n') for m in [RE_PATH.match(ln)] if m]


def nom_dossier(chemin):
    return re.split(r'[\\/]', chemin.rstrip('\\/'))[-1]


def garde_jeu(args):
    ouvert = jeu_ouvert()
    if ouvert is None or ouvert:
        if not args.jeu_ouvert_ok:
            sys.exit("REFUS : le jeu tourne (ou je ne peux pas le verifier). Ferme-le, ou ajoute --jeu-ouvert-ok "
                     "(le changement ne comptera alors qu'au prochain lancement). Rien n'est ecrit.")
        print("Attention : le jeu tourne ; le changement ne comptera qu'au prochain lancement.")


def cmd_etat(a, mods_xml):
    txt = lire(mods_xml).decode('utf-8')
    print('mods.xml : %s' % mods_xml)
    for c in chemins_actifs(txt):
        print('  actif : %-22s %s%s' % (nom_dossier(c), c, '' if os.path.isdir(c) else '   (DOSSIER ABSENT)'))
    return 0


def cmd_desactiver(a, mods_xml):
    garde_jeu(a)
    if not a.nom:
        sys.exit('REFUS : donne au moins un --nom.')
    avant = lire(mods_xml)
    txt = avant.decode('utf-8')
    if '\r\n' in txt:
        sys.exit('REFUS : fins de ligne inattendues dans mods.xml. Rien n\'est ecrit.')
    xml.dom.minidom.parseString(avant)
    lignes = txt.split('\n')
    gardees, retirees = [], []
    for ln in lignes:
        m = RE_PATH.match(ln)
        if m and nom_dossier(m.group(1)) in a.nom:
            retirees.append(m.group(1))
        else:
            gardees.append(ln)
    if not retirees:
        print('Rien a retirer : aucun de %s n\'est actif.' % ', '.join(a.nom))
        return 0
    date = (a.date or datetime.date.today().isoformat()) + (a.suffixe or '')
    bak = mods_xml + '.bak_' + date
    if os.path.exists(bak):
        sys.exit('REFUS : la sauvegarde %s existe deja (je ne l\'ecrase pas). Change --suffixe. Rien n\'est ecrit.' % bak)
    shutil.copyfile(mods_xml, bak)
    if lire(bak) != avant:
        os.remove(bak)
        sys.exit('ERREUR : la sauvegarde n\'est pas identique. Rien n\'est modifie.')
    nouveau = '\n'.join(gardees).encode('utf-8')
    xml.dom.minidom.parseString(nouveau)
    ecrire_atomique(mods_xml, nouveau)
    xml.dom.minidom.parseString(lire(mods_xml))
    print('Sauvegarde : %s' % bak)
    for c in retirees:
        print('  retire de la liste active : %s' % c)
    print('FAIT. Les dossiers des mods n\'ont pas ete touches. Pour tout remettre : python mods_actifs.py restaurer --depuis %s' % os.path.basename(bak))
    return 0


def cmd_restaurer(a, mods_xml):
    garde_jeu(a)
    src = a.depuis if os.path.isabs(a.depuis) else os.path.join(os.path.dirname(mods_xml), a.depuis)
    if not os.path.isfile(src):
        sys.exit('REFUS : sauvegarde introuvable : %s' % src)
    octets = lire(src)
    xml.dom.minidom.parseString(octets)
    ecrire_atomique(mods_xml, octets)
    print('mods.xml remplace par %s.' % src)
    return 0


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument('commande', choices=['etat', 'desactiver', 'restaurer'])
    ap.add_argument('--racine', default=os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2'))
    ap.add_argument('--nom', action='append')
    ap.add_argument('--suffixe')
    ap.add_argument('--date')
    ap.add_argument('--depuis')
    ap.add_argument('--jeu-ouvert-ok', action='store_true', dest='jeu_ouvert_ok')
    a = ap.parse_args()
    mods_xml = os.path.join(a.racine, 'mods.xml')
    if not os.path.isfile(mods_xml):
        sys.exit('REFUS : mods.xml introuvable : %s' % mods_xml)
    return {'etat': cmd_etat, 'desactiver': cmd_desactiver, 'restaurer': cmd_restaurer}[a.commande](a, mods_xml)


if __name__ == '__main__':
    sys.exit(main())
