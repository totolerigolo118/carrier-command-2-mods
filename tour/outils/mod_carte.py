#!/usr/bin/env python3
"""Installe / retire le mod local `cc2_carte` (enregistreur de positions pour le timelapse de la carte).

Le mod est range comme tes autres mods locaux : <racine>\\mods\\cc2_carte\\ avec mod.xml,
thumbnail.png et content\\scripts\\library_custom_6.lua (= passation_windows/enregistreur_carte/cc2map_enregistreur.lua).
Il est active par UNE ligne ajoutee dans <racine>\\mods.xml, apres une sauvegarde datee
(mods.xml.bak_AAAA-MM-JJ_carte, jamais ecrasee). Le dossier du JEU n'est jamais touche.

  python mod_carte.py etat          [--racine DOSSIER]
  python mod_carte.py installer     [--racine DOSSIER] [--date AAAA-MM-JJ] [--variante origine|diag] [--a-blanc]
  python mod_carte.py mettre-a-jour [--racine DOSSIER] [--variante origine|diag] [--a-blanc]
  python mod_carte.py retirer       [--racine DOSSIER]

--racine vaut par defaut %APPDATA%\\Carrier Command 2 (le vrai dossier) ; donne un autre dossier pour essayer.
--variante : quel script poser. `origine` = celui du Mac (par defaut) ; `diag` = le meme plus des lignes CC2DIAG de diagnostic
(tour/carte/cc2map_enregistreur_diag.lua). Les deux sont epingles par leur sha256 ci-dessous.
mettre-a-jour : remplace SEULEMENT library_custom_6.lua du mod deja installe par la variante demandee (mods.xml n'est pas
touche) ; refuse si le script en place n'est pas l'une des deux variantes connues (jamais d'ecrasement d'une modification inconnue).
--a-blanc : fait toutes les verifications de `installer` / `mettre-a-jour` et affiche ce qui serait fait, sans rien ecrire.
Securites : refuse si le jeu tourne (avec le vrai dossier) ; ne remplace jamais un dossier existant ;
refuse si un mod actif fournit deja library_custom_6.lua ; verifie le sha256 du script avant et apres copie ;
ecrit mods.xml via un fichier temporaire puis relit et valide le XML ; si l'installation echoue en route,
le dossier cree est supprime et mods.xml est laisse (ou remis) tel quel ; retirer ne supprime que ce que
l'installation a cree.

Si le script change (par exemple la liste SCREENS), mettre a jour le sha256 ci-dessous apres l'avoir relu.
"""
import argparse
import datetime
import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys
import xml.dom.minidom
import zlib

ICI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(ICI, '..', '..', 'passation_windows', 'enregistreur_carte'))
SRC_DIAG = os.path.normpath(os.path.join(ICI, '..', 'carte'))
NOM = 'cc2_carte'
SCRIPT_MOD = 'library_custom_6.lua'
VARIANTES = {   # variante -> (fichier source, sha256 attendu de la source ; relus le 27/10/2026)
    'origine': (os.path.join(SRC, 'cc2map_enregistreur.lua'),
                '9CC21F1D3ABD417FF368E0B904450033C4A3164E243E01BA68AD64D5FFF1DA4C'),
    'diag': (os.path.join(SRC_DIAG, 'cc2map_enregistreur_diag.lua'),
             '0AE7302E6553964E87602130A275848A32C7C95D711DB8498C28B3B848E0EEF6'),
}
SCRIPTS = {SCRIPT_MOD: VARIANTES['origine']}   # nom dans le mod -> (fichier source, sha256) ; change avec --variante
MOD_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<data name="Carte CC2" author="Yolo" description="Enregistreur de positions pour le timelapse de la carte. '
           'ENREGISTREUR (library_custom_6.lua) : note dans le journal du SDK CC2X (cc2x.log) des lignes CC2MAP avec la '
           'position des unites de toutes les equipes, des iles et des missiles. Ne change aucune donnee du jeu : il ne '
           'fait que lire des etats et ecrire dans ce journal (aucun autre fichier, aucun reseau). Demande CC2X 0.5.0 ; '
           'sans lui il ne fait rien. Pour le retirer : enlever la ligne cc2_carte de mods.xml.">\n</data>\n')
RE_PATH = re.compile(r'^[ \t]*<path value="([^"]*)"/>[ \t]*$')
RE_LIB = re.compile(r'^library_custom_\d+\.lua$')
RE_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def png_uni(taille=128, rvb=(40, 90, 60)):
    """Petit PNG valide, une seule couleur (vignette du mod)."""
    def bloc(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    ligne = b'\x00' + bytes(rvb) * taille
    return (b'\x89PNG\r\n\x1a\n' + bloc(b'IHDR', struct.pack('>IIBBBBB', taille, taille, 8, 2, 0, 0, 0))
            + bloc(b'IDAT', zlib.compress(ligne * taille, 9)) + bloc(b'IEND', b''))


def jeu_ouvert():
    """True / False, ou None si je ne peux pas le savoir."""
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq carrier_command.exe', '/NH'],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return None
    return 'carrier_command.exe' in out.lower()


def est_le_vrai(racine):
    vrai = os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2')
    return os.path.normcase(os.path.abspath(racine)) == os.path.normcase(os.path.abspath(vrai))


def chemins(racine):
    mods = os.path.join(racine, 'mods')
    dossier = os.path.join(mods, NOM)
    return dict(mods_xml=os.path.join(racine, 'mods.xml'), mods=mods, dossier=dossier)


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


def chemins_actifs(txt):
    return [m.group(1) for ln in txt.replace('\r\n', '\n').split('\n') for m in [RE_PATH.match(ln)] if m]


def nom_dossier(chemin):
    return re.split(r'[\\/]', chemin.rstrip('\\/'))[-1]


def numeros_pris(txt, dossier_a_ignorer):
    """{chemin d'un mod actif: [library_custom_*.lua qu'il fournit]} (lecture seule ; ignore notre propre dossier)."""
    ignore = os.path.normcase(os.path.abspath(dossier_a_ignorer))
    res = {}
    for p in chemins_actifs(txt):
        if os.path.normcase(os.path.abspath(p)) == ignore:
            continue
        try:
            noms = sorted(n for n in os.listdir(os.path.join(p, 'content', 'scripts')) if RE_LIB.match(n))
        except OSError:
            noms = []
        res[p] = noms
    return res


def en_conflit(pris):
    return [p for p, noms in pris.items() if set(noms) & set(SCRIPTS)]


def sources_verifiees():
    """Lit les scripts sources et refuse si l'un n'est pas celui qui a ete relu (sha256)."""
    sources = {}
    for n, (chemin, attendu) in SCRIPTS.items():
        if not os.path.isfile(chemin) or sha(lire(chemin)) != attendu:
            sys.exit('REFUS : la source %s n\'est pas celle relue (sha256 different ou fichier absent). Rien n\'est ecrit.' % chemin)
        sources[n] = lire(chemin)
    return sources


def cmd_etat(a, c):
    txt = lire(c['mods_xml']).decode('utf-8') if os.path.isfile(c['mods_xml']) else ''
    print('Racine           : %s' % a.racine)
    print('Dossier du mod   : %s (%s)' % (c['dossier'], 'present' if os.path.isdir(c['dossier']) else 'absent'))
    print('Active (mods.xml): %s' % ('oui' if active_dans(txt, c['dossier']) else 'non'))
    if os.path.isdir(c['dossier']):
        for n, (_, attendu) in SCRIPTS.items():
            p = os.path.join(c['dossier'], 'content', 'scripts', n)
            if not os.path.isfile(p):
                etat = 'absent'
            else:
                connues = [v for v, (_, h) in VARIANTES.items() if h == sha(lire(p))]
                etat = ('conforme (variante %s)' % '/'.join(connues)) if connues else 'DIFFERENT (ni origine ni diag)'
            print('  %-22s %s' % (n, etat))
    pris = numeros_pris(txt, c['dossier'])
    print('Emplacements library_custom fournis par les autres mods actifs :')
    for p, noms in pris.items():
        print('  %-22s %s' % (nom_dossier(p), ', '.join(noms) if noms else '(aucun)'))
    conflits = en_conflit(pris)
    print('library_custom_6.lua : %s' % ('LIBRE' if not conflits else 'DEJA FOURNI PAR ' + ', '.join(nom_dossier(p) for p in conflits)))
    print('(Les scripts du jeu lui-meme ne sont pas verifies par cet outil.)')
    return 0


def cmd_installer(a, c):
    vrai = est_le_vrai(a.racine)
    ouvert = jeu_ouvert() if vrai else False
    if vrai and ouvert is not False and not a.a_blanc:
        sys.exit('REFUS : le jeu tourne (ou je ne peux pas le verifier). Ferme-le puis recommence. Rien n\'est ecrit.')
    if a.date is not None and not RE_DATE.match(a.date):
        sys.exit('REFUS : --date doit avoir la forme AAAA-MM-JJ. Rien n\'est ecrit.')
    if not os.path.isfile(c['mods_xml']):
        sys.exit('REFUS : mods.xml introuvable dans %s' % a.racine)
    if os.path.lexists(c['dossier']):
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
    conflits = en_conflit(numeros_pris(txt, c['dossier']))
    if conflits:
        sys.exit('REFUS : library_custom_6.lua est deja fourni par un mod actif (%s). Rien n\'est ecrit.' % ', '.join(conflits))
    date = a.date or datetime.date.today().isoformat()
    bak = c['mods_xml'] + '.bak_' + date + '_carte'
    if os.path.lexists(bak):
        sys.exit('REFUS : la sauvegarde %s existe deja (je ne l\'ecrase pas). Donne --date AAAA-MM-JJ avec une autre date. Rien n\'est ecrit.' % bak)
    if a.a_blanc:
        print('A BLANC (rien n\'est ecrit). Jeu : %s.' % {True: 'ouvert (l\'installation reelle refuserait)', False: 'ferme', None: 'inconnu (l\'installation reelle refuserait)'}[ouvert])
        print('Sauvegarde qui serait faite : %s (copie de mods.xml, sha256 %s)' % (bak, sha(avant)))
        print('Dossier qui serait cree     : %s' % c['dossier'])
        for n in SCRIPTS:
            print('  content\\scripts\\%s  (source relue, sha256 %s)' % (n, SCRIPTS[n][1]))
        print('  mod.xml, thumbnail.png')
        print('Ligne qui serait ajoutee a mods.xml, avant </active_mod_folders> :%s' % ('\n' + ligne_xml(c['dossier']).rstrip('\n')))
        print('library_custom_6.lua : libre (aucun mod actif ne le fournit).')
        return 0
    # 1. sauvegarde datee de mods.xml
    shutil.copyfile(c['mods_xml'], bak)
    if lire(bak) != avant:
        os.remove(bak)
        sys.exit('ERREUR : la sauvegarde n\'est pas identique a mods.xml. Rien d\'autre n\'est ecrit.')
    print('Sauvegarde : %s (sha256 %s)' % (bak, sha(avant)))
    # 2. le dossier du mod (supprime si quelque chose echoue avant l'activation)
    cree = False
    try:
        scripts = os.path.join(c['dossier'], 'content', 'scripts')
        os.makedirs(scripts)
        cree = True
        for n, octets in sources.items():
            with open(os.path.join(scripts, n), 'wb') as f:
                f.write(octets)
            if sha(lire(os.path.join(scripts, n))) != SCRIPTS[n][1]:
                raise RuntimeError('copie de %s differente de la source' % n)
        with open(os.path.join(c['dossier'], 'mod.xml'), 'wb') as f:
            f.write(MOD_XML.encode('utf-8'))
        valider_xml(lire(os.path.join(c['dossier'], 'mod.xml')))
        with open(os.path.join(c['dossier'], 'thumbnail.png'), 'wb') as f:
            f.write(png_uni())
        print('Dossier cree : %s' % c['dossier'])
        # 3. activation : UNE ligne ajoutee a la fin de la liste
        nouveau = txt.replace(marque, ligne_xml(c['dossier']).rstrip('\n') + '\n' + marque).encode('utf-8')
        valider_xml(nouveau)
    except BaseException as e:
        if cree:
            shutil.rmtree(c['dossier'], ignore_errors=True)
        sys.exit('ERREUR : %s. Le dossier cree a ete supprime, mods.xml n\'est PAS modifie.' % e)
    ecrire_atomique(c['mods_xml'], nouveau)
    apres = lire(c['mods_xml'])
    try:
        valider_xml(apres)
    except Exception as e:
        ecrire_atomique(c['mods_xml'], avant)
        shutil.rmtree(c['dossier'], ignore_errors=True)
        sys.exit('ERREUR : mods.xml invalide apres ecriture (%s). Remis tel quel, dossier supprime.' % e)
    print('mods.xml : une ligne ajoutee (sha256 %s -> %s)' % (sha(avant), sha(apres)))
    print('FAIT : mod %s installe et active. Retour arriere : python mod_carte.py retirer, ou recopier %s sur mods.xml.' % (NOM, os.path.basename(bak)))
    return 0


def cmd_mettre_a_jour(a, c):
    """Remplace library_custom_6.lua du mod deja installe par la variante demandee. mods.xml n'est PAS touche."""
    vrai = est_le_vrai(a.racine)
    ouvert = jeu_ouvert() if vrai else False
    if vrai and ouvert is not False and not a.a_blanc:
        sys.exit('REFUS : le jeu tourne (ou je ne peux pas le verifier). Ferme-le puis recommence. Rien n\'est ecrit.')
    if not os.path.isfile(c['mods_xml']):
        sys.exit('REFUS : mods.xml introuvable dans %s' % a.racine)
    txt = lire(c['mods_xml']).decode('utf-8')
    if not os.path.isdir(c['dossier']) or os.path.islink(c['dossier']) or not active_dans(txt, c['dossier']):
        sys.exit('REFUS : le mod %s n\'est pas installe et actif (utilise `installer`). Rien n\'est ecrit.' % NOM)
    sources = sources_verifiees()
    scripts = os.path.join(c['dossier'], 'content', 'scripts')
    connus = {h: v for v, (_, h) in VARIANTES.items()}
    plan = []
    for n, octets in sources.items():
        p = os.path.join(scripts, n)
        if os.path.islink(p) or not os.path.isfile(p):
            sys.exit('REFUS : %s est absent ou n\'est pas un fichier ordinaire (utilise `retirer` puis `installer`). Rien n\'est ecrit.' % p)
        actuel = lire(p)
        if actuel == octets:
            plan.append((n, p, octets, 'deja a jour (variante %s)' % a.variante))
        elif sha(actuel) in connus:
            plan.append((n, p, octets, 'variante %s -> %s' % (connus[sha(actuel)], a.variante)))
        else:
            sys.exit('REFUS : %s n\'est ni la variante origine ni la variante diag (sha256 %s) : je ne l\'ecrase pas. Rien n\'est ecrit.' % (p, sha(actuel)))
    for n, p, octets, quoi in plan:
        print('  %-22s %s' % (n, quoi))
    if a.a_blanc:
        print('A BLANC (rien n\'est ecrit). Jeu : %s. mods.xml ne serait pas touche.' % {True: 'ouvert (la mise a jour reelle refuserait)', False: 'ferme', None: 'inconnu (la mise a jour reelle refuserait)'}[ouvert])
        return 0
    for n, p, octets, quoi in plan:
        if quoi.startswith('deja a jour'):
            continue
        ecrire_atomique(p, octets)
        if sha(lire(p)) != SCRIPTS[n][1]:
            sys.exit('ERREUR : copie de %s differente de la source.' % n)
        print('  %-22s ecrit' % n)
    print('FAIT : mod %s a jour, variante %s (mods.xml non touche). Retour arriere : mettre-a-jour --variante origine.' % (NOM, a.variante))
    return 0


def cmd_retirer(a, c):
    if est_le_vrai(a.racine) and jeu_ouvert() is not False:
        sys.exit('REFUS : le jeu tourne (ou je ne peux pas le verifier). Ferme-le puis recommence. Rien n\'est ecrit.')
    if not os.path.isfile(c['mods_xml']):
        sys.exit('REFUS : mods.xml introuvable dans %s' % a.racine)
    if os.path.islink(c['dossier']):
        sys.exit('REFUS : %s est un lien, je n\'y touche pas. Rien n\'est ecrit.' % c['dossier'])
    txt = lire(c['mods_xml']).decode('utf-8')
    if '\r\n' in txt:
        sys.exit('REFUS : fins de ligne inattendues dans mods.xml. Rien n\'est ecrit.')
    ligne = ligne_xml(c['dossier'])
    n = txt.count(ligne)
    if n:
        nouveau = txt.replace(ligne, '').encode('utf-8')
        valider_xml(nouveau)
        ecrire_atomique(c['mods_xml'], nouveau)
        valider_xml(lire(c['mods_xml']))
        print('mods.xml : %d ligne(s) %s retiree(s).' % (n, NOM))
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
    global SCRIPTS
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument('commande', choices=['etat', 'installer', 'mettre-a-jour', 'retirer'])
    ap.add_argument('--racine', default=os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2'))
    ap.add_argument('--date')
    ap.add_argument('--variante', choices=sorted(VARIANTES), default='origine')
    ap.add_argument('--a-blanc', action='store_true', dest='a_blanc')
    a = ap.parse_args()
    if a.a_blanc and a.commande not in ('installer', 'mettre-a-jour'):
        ap.error('--a-blanc ne va qu\'avec `installer` ou `mettre-a-jour`')
    if a.variante != 'origine' and a.commande not in ('installer', 'mettre-a-jour'):
        ap.error('--variante ne va qu\'avec `installer` ou `mettre-a-jour`')
    if a.date is not None and a.commande != 'installer':
        ap.error('--date ne va qu\'avec `installer`')
    SCRIPTS = {SCRIPT_MOD: VARIANTES[a.variante]}
    c = chemins(a.racine)
    return {'etat': cmd_etat, 'installer': cmd_installer, 'mettre-a-jour': cmd_mettre_a_jour,
            'retirer': cmd_retirer}[a.commande](a, c)


if __name__ == '__main__':
    sys.exit(main())
