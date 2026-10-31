#!/usr/bin/env python3
"""Installe / retire le mod local `cc2_mesures` (horloge de jeu + journal des atterrissages).

Le mod est range comme tes autres mods locaux : <racine>\\mods\\cc2_mesures\\ avec mod.xml,
thumbnail.png et content\\scripts\\library_custom_1.lua (horloge) et library_custom_4.lua (journal).
Il est active par UNE ligne ajoutee dans <racine>\\mods.xml, apres une sauvegarde datee
(mods.xml.bak_AAAA-MM-JJ, comme tes sauvegardes habituelles). Le dossier du JEU n'est jamais touche.

  python mod_mesures.py etat      [--racine DOSSIER]
  python mod_mesures.py installer [--racine DOSSIER] [--date AAAA-MM-JJ]
  python mod_mesures.py retirer   [--racine DOSSIER]

--racine vaut par defaut %APPDATA%\\Carrier Command 2 (le vrai dossier) ; donne un autre dossier pour essayer.
Securites : refuse si le jeu tourne (avec le vrai dossier) ; ne remplace jamais un dossier existant ;
verifie le sha256 des scripts avant et apres copie ; ecrit mods.xml via un fichier temporaire puis
relit et valide le XML ; retirer ne supprime que ce que l'installation a cree.
"""
import argparse
import datetime
import hashlib
import os
import shutil
import struct
import subprocess
import sys
import xml.dom.minidom
import zlib

ICI = os.path.dirname(os.path.abspath(__file__))
SRC_PASSATION = os.path.normpath(os.path.join(ICI, '..', '..', 'passation_windows', 'lua_a_installer'))
SRC_TOUR = os.path.normpath(os.path.join(ICI, '..', 'lua'))
NOM = 'cc2_mesures'
SCRIPTS = {   # nom dans le mod -> (dossier de la source, sha256 attendu de la source ; relus le 27/10/2026)
    'library_custom_1.lua': (SRC_PASSATION, 'D0344F948732B30035AB043E5356221B6FB19471B44C78C981F10ED849B8E5FA'),
    'library_custom_4.lua': (SRC_PASSATION, 'B0CEDB8C686DA0B079696D7E989421B29B0EB22BCA5F7F0DFD73A4605FC54F21'),
    'library_custom_7.lua': (SRC_TOUR, 'E7C30BF6013DFC607801AD4C4FC7CB34B257774D8CAB8B6BAFCAB01E509920FB'),
    'library_custom_9.lua': (SRC_TOUR, '061A37805D53B5B204BE4E20A25EB9D83E33CC88ACA77D3CE04A2CD38D43E728'),
}
MOD_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<data name="Mesures CC2" author="Yolo" description="Mesures en temps de jeu pour comparer les patchs. '
           'HORLOGE (library_custom_1.lua) : le temps de jeu en bas a gauche des ecrans de controle des vehicules '
           '(screen_veh_l / m / r). JOURNAL (library_custom_4.lua) : chronometre tout seul les retours d avions et '
           'd helicos et l affiche juste au-dessus de l horloge. SIM (library_custom_7.lua) : a droite de l horloge, '
           'la vitesse reelle de la simulation (x1.00 = normale, x2.00 = 2 fois plus vite, moins que voulu = la '
           'machine ne suit pas). SORTIES (library_custom_9.lua) : en haut a droite, chronometre les decollages '
           'et affiche 4/4 EN L AIR : FINI en m:ss quand tous les appareils sont decolles. Ne change rien au jeu : il ne fait que lire des etats et afficher du texte '
           '(aucun fichier, aucun reseau). Pour le retirer : enlever la ligne cc2_mesures de mods.xml.">\n</data>\n')


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def png_uni(taille=128, rvb=(40, 60, 90)):
    """Petit PNG valide, une seule couleur (vignette du mod)."""
    def bloc(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    ligne = b'\x00' + bytes(rvb) * taille
    return (b'\x89PNG\r\n\x1a\n' + bloc(b'IHDR', struct.pack('>IIBBBBB', taille, taille, 8, 2, 0, 0, 0))
            + bloc(b'IDAT', zlib.compress(ligne * taille, 9)) + bloc(b'IEND', b''))


def jeu_ouvert():
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq carrier_command.exe', '/NH'],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return None
    return 'carrier_command.exe' in out.lower()


def chemins(racine):
    mods = os.path.join(racine, 'mods')
    dossier = os.path.join(mods, NOM)
    return dict(mods_xml=os.path.join(racine, 'mods.xml'), mods=mods, dossier=dossier,
                ligne_chemin=dossier)   # la valeur du path dans mods.xml est le chemin du dossier


def ligne_xml(dossier):
    return '\t\t<path value="%s"/>\n' % dossier


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


def valider_xml(octets):
    xml.dom.minidom.parseString(octets)


def active_dans(mods_xml_txt, dossier):
    return ligne_xml(dossier) in mods_xml_txt.replace('\r\n', '\n')


def cmd_etat(a, c):
    txt = lire(c['mods_xml']).decode('utf-8') if os.path.isfile(c['mods_xml']) else ''
    print('Racine           : %s' % a.racine)
    print('Dossier du mod   : %s (%s)' % (c['dossier'], 'present' if os.path.isdir(c['dossier']) else 'absent'))
    print('Active (mods.xml): %s' % ('oui' if active_dans(txt, c['dossier']) else 'non'))
    if os.path.isdir(c['dossier']):
        for n, (_, attendu) in SCRIPTS.items():
            p = os.path.join(c['dossier'], 'content', 'scripts', n)
            etat = 'absent' if not os.path.isfile(p) else ('conforme' if sha(lire(p)) == attendu else 'DIFFERENT')
            print('  %-22s %s' % (n, etat))
    return 0


def sources_verifiees():
    """Lit les scripts sources et refuse si l'un n'est pas celui qui a ete relu (sha256)."""
    sources = {}
    for n, (dossier, attendu) in SCRIPTS.items():
        p = os.path.join(dossier, n)
        if not os.path.isfile(p) or sha(lire(p)) != attendu:
            sys.exit('REFUS : la source %s n\'est pas celle relue (sha256 different). Rien n\'est ecrit.' % p)
        sources[n] = lire(p)
    return sources


def cmd_mettre_a_jour(a, c):
    """Ajoute / remet les scripts du mod et son mod.xml a l'etat voulu. mods.xml n'est PAS touche."""
    vrai = os.path.normcase(os.path.abspath(a.racine)) == os.path.normcase(os.path.abspath(os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2')))
    if vrai and jeu_ouvert() is not False and not a.jeu_ouvert_ok:
        sys.exit("REFUS : le jeu tourne (ou je ne peux pas le verifier). Ferme-le, ou ajoute --jeu-ouvert-ok. Rien n'est ecrit.")
    if not os.path.isdir(c['dossier']):
        sys.exit('REFUS : le mod %s n\'est pas installe (utilise `installer`). Rien n\'est ecrit.' % NOM)
    sources = sources_verifiees()
    scripts = os.path.join(c['dossier'], 'content', 'scripts')
    os.makedirs(scripts, exist_ok=True)
    for n, octets in sources.items():
        p = os.path.join(scripts, n)
        if os.path.isfile(p) and lire(p) == octets:
            print('  %-22s deja a jour' % n)
            continue
        ecrire_atomique(p, octets)
        if sha(lire(p)) != SCRIPTS[n][1]:
            sys.exit('ERREUR : copie de %s differente de la source.' % n)
        print('  %-22s ecrit' % n)
    valider_xml(MOD_XML.encode('utf-8'))
    p = os.path.join(c['dossier'], 'mod.xml')
    if not os.path.isfile(p) or lire(p) != MOD_XML.encode('utf-8'):
        ecrire_atomique(p, MOD_XML.encode('utf-8'))
        print('  mod.xml                mis a jour')
    print('FAIT : mod %s a jour (mods.xml non touche).' % NOM)
    return 0


def cmd_installer(a, c):
    vrai = os.path.normcase(os.path.abspath(a.racine)) == os.path.normcase(os.path.abspath(os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2')))
    if vrai and jeu_ouvert() is not False:
        sys.exit('REFUS : le jeu tourne (ou je ne peux pas le verifier). Ferme-le puis recommence. Rien n\'est ecrit.')
    if not os.path.isfile(c['mods_xml']):
        sys.exit('REFUS : mods.xml introuvable dans %s' % a.racine)
    if os.path.exists(c['dossier']):
        sys.exit('REFUS : %s existe deja (je ne remplace jamais un dossier). Rien n\'est ecrit.' % c['dossier'])
    sources = sources_verifiees()
    avant = lire(c['mods_xml'])
    txt = avant.decode('utf-8')
    if active_dans(txt, c['dossier']):
        sys.exit('REFUS : mods.xml cite deja %s. Rien n\'est ecrit.' % NOM)
    valider_xml(avant)
    marque = '\t</active_mod_folders>'
    if txt.replace('\r\n', '\n').count(marque) != 1 or '\r\n' in txt:
        sys.exit('REFUS : mods.xml n\'a pas la forme attendue (un seul </active_mod_folders>, fins de ligne simples). Rien n\'est ecrit.')
    # 1. sauvegarde datee de mods.xml
    date = a.date or datetime.date.today().isoformat()
    bak = c['mods_xml'] + '.bak_' + date
    if os.path.exists(bak):
        sys.exit('REFUS : la sauvegarde %s existe deja (je ne l\'ecrase pas). Donne --date AAAA-MM-JJ avec une autre date.' % bak)
    shutil.copyfile(c['mods_xml'], bak)
    if lire(bak) != avant:
        os.remove(bak)
        sys.exit('ERREUR : la sauvegarde n\'est pas identique a mods.xml. Rien d\'autre n\'est ecrit.')
    print('Sauvegarde : %s (sha256 %s)' % (bak, sha(avant)))
    # 2. le dossier du mod
    scripts = os.path.join(c['dossier'], 'content', 'scripts')
    os.makedirs(scripts)
    for n, octets in sources.items():
        with open(os.path.join(scripts, n), 'wb') as f:
            f.write(octets)
        if sha(lire(os.path.join(scripts, n))) != SCRIPTS[n][1]:
            sys.exit('ERREUR : copie de %s differente de la source. mods.xml n\'est PAS modifie.' % n)
    with open(os.path.join(c['dossier'], 'mod.xml'), 'wb') as f:
        f.write(MOD_XML.encode('utf-8'))
    valider_xml(lire(os.path.join(c['dossier'], 'mod.xml')))
    with open(os.path.join(c['dossier'], 'thumbnail.png'), 'wb') as f:
        f.write(png_uni())
    print('Dossier cree : %s' % c['dossier'])
    # 3. activation : UNE ligne ajoutee a la fin de la liste
    nouveau = txt.replace(marque, ligne_xml(c['dossier']).rstrip('\n') + '\n' + marque).encode('utf-8')
    valider_xml(nouveau)
    ecrire_atomique(c['mods_xml'], nouveau)
    apres = lire(c['mods_xml'])
    valider_xml(apres)
    print('mods.xml : une ligne ajoutee (sha256 %s -> %s)' % (sha(avant), sha(apres)))
    print('FAIT : mod %s installe et active. Retour arriere : python mod_mesures.py retirer, ou recopier %s sur mods.xml.' % (NOM, os.path.basename(bak)))
    return 0


def cmd_retirer(a, c):
    vrai = os.path.normcase(os.path.abspath(a.racine)) == os.path.normcase(os.path.abspath(os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2')))
    if vrai and jeu_ouvert() is not False:
        sys.exit('REFUS : le jeu tourne (ou je ne peux pas le verifier). Ferme-le puis recommence.')
    txt = lire(c['mods_xml']).decode('utf-8')
    ligne = ligne_xml(c['dossier'])
    if txt.count(ligne) == 1:
        nouveau = txt.replace(ligne, '').encode('utf-8')
        valider_xml(nouveau)
        ecrire_atomique(c['mods_xml'], nouveau)
        print('mods.xml : la ligne %s est retiree.' % NOM)
    else:
        print('mods.xml : %s n\'y figure pas (rien a retirer).' % NOM)
    if os.path.isdir(c['dossier']):
        attendus = {os.path.join('content', 'scripts', n) for n in SCRIPTS} | {'mod.xml', 'thumbnail.png'}
        presents = set()
        for rep, _, fichiers in os.walk(c['dossier']):
            for f in fichiers:
                presents.add(os.path.relpath(os.path.join(rep, f), c['dossier']))
        if presents <= attendus:
            shutil.rmtree(c['dossier'])
            print('Dossier supprime : %s' % c['dossier'])
        else:
            print('Dossier GARDE : il contient des fichiers que je n\'ai pas crees : %s' % sorted(presents - attendus))
    return 0


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument('commande', choices=['etat', 'installer', 'retirer', 'mettre-a-jour'])
    ap.add_argument('--racine', default=os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2'))
    ap.add_argument('--date')
    ap.add_argument('--jeu-ouvert-ok', action='store_true', dest='jeu_ouvert_ok')
    a = ap.parse_args()
    c = chemins(a.racine)
    return {'etat': cmd_etat, 'installer': cmd_installer, 'retirer': cmd_retirer,
            'mettre-a-jour': cmd_mettre_a_jour}[a.commande](a, c)


if __name__ == '__main__':
    sys.exit(main())
