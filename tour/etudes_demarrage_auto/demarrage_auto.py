#!/usr/bin/env python3
"""Installateur du DEMARRAGE AUTOMATIQUE de Carrier Command 2 (voir ETUDE.md).  AUCUNE commande ne lance le jeu.

  python -I demarrage_auto.py etat                      lecture seule : que est en place ?
  python -I demarrage_auto.py installer [options]       pose le script de menu + le mod interrupteur (mods.xml N'EST PAS touche)
  python -I demarrage_auto.py armer                     ajoute la ligne du mod dans mods.xml (= coche l'interrupteur ; on peut aussi le cocher dans le menu MODS du jeu)
  python -I demarrage_auto.py desarmer                  retire cette ligne (= decoche)
  python -I demarrage_auto.py desinstaller              desarme, remet le fichier de rom_0 a 0 octet, supprime le mod

Options de « installer » : --rom N (fichier library_custom_N.lua de rom_0\\scripts, 0 par defaut), --mode nouvelle|charger,
--partie N (slot a charger si --mode charger, 19 par defaut), --attente S (secondes de menu avant la demande, 30), --attendre-touche
(le compte a rebours ne demarre qu'une fois l'ecran-titre « PRESS ANY KEY » passe), --date AAAA-MM-JJ (nom des sauvegardes de mods.xml).
Autres : --racine DOSSIER (donnees du jeu, %APPDATA%\\Carrier Command 2), --dossier-jeu DOSSIER (Steam) ; servent aux essais sur un FAUX dossier.

Ce que « installer » ecrit, et rien d'autre :
  - <jeu>\\rom_0\\scripts\\library_custom_N.lua : ne le touche QUE s'il est le fichier VIDE d'origine (0 octet) ; ecrit le script (verifie par relecture) ;
  - <racine>\\mods\\cc2_demarrage_auto\\ : mod.xml, thumbnail.png, content\\scripts\\library_custom_N.lua (un commentaire) ; refuse si le dossier existe deja.
Garde-fous : refuse si un exe du jeu tourne (carrier_command*.exe, y compris les exe d'essai) ; refuse si un mod installe utilise deja le meme numero
de library_custom ; en cas d'erreur, remet le fichier de rom_0 a 0 octet et retire le dossier cree. Retour arriere complet : « desinstaller »,
ou vider le fichier de rom_0 (sha256 de 0 octet E3B0C442...B855) ; Steam > Proprietes > Fichiers installes > Verifier l'integrite le remet aussi a zero."""
import argparse
import datetime
import glob
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
SRC_LUA = os.path.join(ICI, 'demarrage_auto.lua')
NOM_MOD = 'Demarrage auto'               # attribut name de mod.xml ; DOIT etre le NOM_MOD de demarrage_auto.lua
DOSSIER_MOD = 'cc2_demarrage_auto'
MARQUE = '-- DEMARRAGE AUTO (cc2_demarrage_auto)'
VIDE = 'E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855'
JEU_DEFAUT = r'C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2'
MARQUE_MODS_XML = '\t</active_mod_folders>'
MOD_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<data name="%s" author="Yolo" description="Interrupteur du demarrage automatique. Tant que ce mod est COCHE, le script de menu '
           '(library_custom_N.lua de rom_0, pose par demarrage_auto.py) lance tout seul une partie quelques secondes apres l ouverture du menu. '
           'Decoche = menu normal. Ne modifie aucun fichier ni reglage. Pour le retirer : python demarrage_auto.py desinstaller.">\n</data>\n' % NOM_MOD)


def charger_mod_mesures():
    """Reutilise png_uni / valider_xml du programme d'installation du mod de mesures."""
    spec = importlib.util.spec_from_file_location('mod_mesures', os.path.join(ICI, '..', 'outils', 'mod_mesures.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sha(octets):
    return hashlib.sha256(octets).hexdigest().upper()


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


def processus_jeu():
    """PID de TOUT exe du jeu (carrier_command*.exe : l'original et les exe d'essai), [] si aucun, None si je ne peux pas le verifier."""
    try:
        out = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None
    if not out.strip():
        return None
    pids = []
    for ligne in out.splitlines():
        champs = [c.strip('"') for c in ligne.split('","')]
        if len(champs) > 1 and champs[0].strip('"').lower().startswith('carrier_command'):
            pids.append(champs[1].strip('"'))
    return pids


def racine_defaut():
    return os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2')


def est_vrai(a):
    """Vrai si on travaille sur les VRAIS dossiers (les garde-fous « jeu ferme » ne s'appliquent pas aux faux dossiers d'essai)."""
    n = lambda p: os.path.normcase(os.path.abspath(p))
    return n(a.racine) == n(racine_defaut()) or n(a.dossier_jeu) == n(JEU_DEFAUT)


def exiger_jeu_ferme(a):
    if est_vrai(a):
        p = processus_jeu()
        if p is None or p:
            sys.exit('REFUS : le jeu tourne (ou je ne peux pas le verifier). Ferme-le puis recommence. Rien n\'est ecrit.')


def chemins(a):
    return dict(mods_xml=os.path.join(a.racine, 'mods.xml'),
                dossier_mod=os.path.join(a.racine, 'mods', DOSSIER_MOD),
                scripts_rom=os.path.join(a.dossier_jeu, 'rom_0', 'scripts'),
                rom=os.path.join(a.dossier_jeu, 'rom_0', 'scripts', 'library_custom_%d.lua' % a.rom))


def ligne_mods_xml(c):
    return '\t\t<path value="%s"/>\n' % c['dossier_mod']


def contenu_mod(a):
    mm = charger_mod_mesures()
    return {
        'mod.xml': MOD_XML.encode('utf-8'),
        'thumbnail.png': mm.png_uni(128, (30, 90, 50)),
        os.path.join('content', 'scripts', 'library_custom_%d.lua' % a.rom):
            b'-- Demarrage auto : fichier volontairement sans code (il laisse le script de menu de rom_0 hors jeu).\n',
    }


def fichiers_du_dossier(dossier):
    res = {}
    for rep, _, fichiers in os.walk(dossier):
        for f in fichiers:
            p = os.path.join(rep, f)
            res[os.path.relpath(p, dossier)] = lire(p)
    return res


def etat_rom(chemin):
    """('absent'|'vide'|'notre script'|'AUTRE CONTENU', taille)"""
    if not os.path.isfile(chemin):
        return 'absent', 0
    n = os.path.getsize(chemin)
    if n == 0:
        return 'vide', 0
    debut = lire(chemin)[:200].decode('utf-8', 'replace')
    return ('notre script' if debut.startswith(MARQUE) else 'AUTRE CONTENU'), n


def slots_pris(a, n):
    """Mods (hors le notre) qui fournissent deja library_custom_n.lua : dans <racine>\\mods et dans les mods Workshop."""
    motifs = [os.path.join(a.racine, 'mods', '*', 'content', 'scripts', 'library_custom_%d.lua' % n),
              os.path.join(a.dossier_jeu, '..', '..', 'workshop', 'content', '1489630', '*', 'content', 'scripts', 'library_custom_%d.lua' % n)]
    pris = []
    for m in motifs:
        for p in glob.glob(m):
            nom = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(p))))
            if nom != DOSSIER_MOD:
                pris.append(nom)
    return sorted(pris)


def entete(a):
    return ('%s : pose par demarrage_auto.py le %s ; retrait : python -I demarrage_auto.py desinstaller\n'
            'g_da_mode = "%s"\ng_da_slot = %d\ng_da_attente = %d\ng_da_attendre_menu = %s\n'
            % (MARQUE, datetime.date.today().isoformat(), a.mode, a.partie, a.attente, 'true' if a.attendre_touche else 'false'))


def vider(chemin):
    with open(chemin, 'wb'):
        pass
    return os.path.getsize(chemin) == 0


def lire_mods_xml(c):
    if not os.path.isfile(c['mods_xml']):
        sys.exit('REFUS : mods.xml introuvable (%s).' % c['mods_xml'])
    brut = lire(c['mods_xml'])
    try:
        txt = brut.decode('utf-8')
    except UnicodeDecodeError:
        sys.exit('REFUS : mods.xml n\'est pas de l\'UTF-8. Rien n\'est ecrit.')
    charger_mod_mesures().valider_xml(brut)
    if '\r\n' in txt or txt.count(MARQUE_MODS_XML) != 1:
        sys.exit('REFUS : mods.xml n\'a pas la forme attendue (un seul </active_mod_folders>, fins de ligne simples). Rien n\'est ecrit.')
    return brut, txt


def sauvegarder_mods_xml(c, brut, a, suffixe):
    date = a.date or datetime.date.today().isoformat()
    base = c['mods_xml'] + '.bak_%s_%s' % (date, suffixe)
    bak, k = base, 2
    while os.path.exists(bak):                       # une sauvegarde existante n'est JAMAIS ecrasee
        bak = '%s_%d' % (base, k)
        k += 1
    shutil.copyfile(c['mods_xml'], bak)
    if lire(bak) != brut:
        os.remove(bak)
        sys.exit('ERREUR : la sauvegarde n\'est pas identique a mods.xml. Rien d\'autre n\'est ecrit.')
    print('Sauvegarde de mods.xml : %s (sha256 %s)' % (bak, sha(brut)))


# ----------------------------------------------------------------------------- commandes
def cmd_etat(a, c):
    mm = charger_mod_mesures()
    p = processus_jeu()
    print('Jeu en cours      : %s' % ('non verifiable' if p is None else ('OUI (pid %s)' % ', '.join(p) if p else 'non')))
    print('Dossier du jeu    : %s' % a.dossier_jeu)
    for n in range(10):
        f = os.path.join(c['scripts_rom'], 'library_custom_%d.lua' % n)
        e, t = etat_rom(f)
        extra = ''
        if e == 'notre script':
            txt = lire(f).decode('utf-8', 'replace')
            params = re.findall(r'^(g_da_\w+) = (.+)$', txt, re.M)
            extra = ' ; ' + ', '.join('%s=%s' % (k[5:], v.strip('"')) for k, v in params)
        print('  rom_0 library_custom_%d.lua : %s (%d octets)%s' % (n, e, t, extra))
    attendu = contenu_mod(a)
    if os.path.isdir(c['dossier_mod']):
        presents = fichiers_du_dossier(c['dossier_mod'])
        print('Mod interrupteur  : present (%s)%s' % (c['dossier_mod'], '' if presents == attendu else ' ; DIFFERENT de ce que l\'outil poserait'))
    else:
        print('Mod interrupteur  : absent (%s)' % c['dossier_mod'])
    if os.path.isfile(c['mods_xml']):
        txt = lire(c['mods_xml']).decode('utf-8', 'replace').replace('\r\n', '\n')
        print('Interrupteur      : %s' % ('COCHE (mods.xml cite le mod)' if ligne_mods_xml(c) in txt else 'decoche'))
    else:
        print('Interrupteur      : mods.xml introuvable')
    return 0


def cmd_installer(a, c):
    exiger_jeu_ferme(a)
    e, t = etat_rom(c['rom'])
    if e == 'notre script':
        sys.exit('REFUS : %s contient deja le script du demarrage auto. Fais d\'abord « desinstaller ». Rien n\'est ecrit.' % c['rom'])
    if e != 'vide':
        sys.exit('REFUS : %s n\'est pas le fichier VIDE d\'origine (%s, %d octets) : je n\'y touche pas. Rien n\'est ecrit.' % (c['rom'], e, t))
    if os.path.exists(c['dossier_mod']):
        sys.exit('REFUS : %s existe deja (je ne remplace jamais un dossier). Rien n\'est ecrit.' % c['dossier_mod'])
    pris = slots_pris(a, a.rom)
    if pris:
        sys.exit('REFUS : library_custom_%d.lua est deja fourni par le(s) mod(s) %s : choisis un autre --rom. Rien n\'est ecrit.' % (a.rom, ', '.join(pris)))
    source = lire(SRC_LUA)
    if ('local NOM_MOD = "%s"' % NOM_MOD).encode() not in source:
        sys.exit('ERREUR : NOM_MOD de demarrage_auto.lua ne correspond pas au nom du mod (%s). Rien n\'est ecrit.' % NOM_MOD)
    octets = entete(a).encode('utf-8') + source
    mod_cree = rom_ecrit = False
    try:
        # 1. le mod (zone utilisateur d'abord : si ca echoue, le dossier du jeu n'a pas ete touche)
        mm = charger_mod_mesures()
        os.makedirs(os.path.join(c['dossier_mod'], 'content', 'scripts'))
        mod_cree = True
        for rel, contenu in contenu_mod(a).items():
            with open(os.path.join(c['dossier_mod'], rel), 'wb') as f:
                f.write(contenu)
        mm.valider_xml(lire(os.path.join(c['dossier_mod'], 'mod.xml')))
        if fichiers_du_dossier(c['dossier_mod']) != contenu_mod(a):
            raise RuntimeError('le dossier du mod n\'est pas conforme a ce qui a ete ecrit')
        print('Mod cree           : %s' % c['dossier_mod'])
        # 2. le script, dans le fichier vide du dossier du jeu (ecriture en place, relue)
        rom_ecrit = True
        with open(c['rom'], 'wb') as f:
            f.write(octets)
            f.flush()
            os.fsync(f.fileno())
        if lire(c['rom']) != octets:
            raise RuntimeError('relecture de %s differente de ce qui a ete ecrit' % c['rom'])
        print('Script pose        : %s (%d octets, sha256 %s)' % (c['rom'], len(octets), sha(octets)))
    except BaseException as ex:
        print('ERREUR : %r : je remets tout comme avant.' % (ex,))
        if rom_ecrit and os.path.isfile(c['rom']):
            print('  fichier de rom_0 remis a 0 octet : %s' % ('oui' if vider(c['rom']) else 'NON, A VERIFIER A LA MAIN'))
        if mod_cree and os.path.isdir(c['dossier_mod']):
            shutil.rmtree(c['dossier_mod'], ignore_errors=True)
            print('  dossier du mod retire')
        sys.exit(1)
    print('mods.xml           : NON touche.')
    print('Reglages           : mode %s%s, attente %d s%s.' % (a.mode, (' (slot %d)' % a.partie) if a.mode == 'charger' else '', a.attente,
                                                              ', apres l\'ecran-titre' if a.attendre_touche else ''))
    print('FAIT. Pour que le jeu demarre tout seul : coche « %s » dans le menu MODS du jeu, ou fais « armer » (jeu ferme).' % NOM_MOD)
    print('Retour arriere : python -I demarrage_auto.py desinstaller')
    return 0


def cmd_armer(a, c):
    exiger_jeu_ferme(a)
    if not os.path.isdir(c['dossier_mod']):
        sys.exit('REFUS : le mod n\'est pas installe (%s). Fais d\'abord « installer ».' % c['dossier_mod'])
    brut, txt = lire_mods_xml(c)
    ligne = ligne_mods_xml(c)
    if txt.count(ligne) >= 1:
        print('Deja arme : mods.xml cite deja le mod. Rien a faire.')
        return 0
    sauvegarder_mods_xml(c, brut, a, 'demarrage_arme')
    nouveau = txt.replace(MARQUE_MODS_XML, ligne + MARQUE_MODS_XML).encode('utf-8')
    charger_mod_mesures().valider_xml(nouveau)
    ecrire_atomique(c['mods_xml'], nouveau)
    charger_mod_mesures().valider_xml(lire(c['mods_xml']))
    print('mods.xml : une ligne ajoutee (sha256 %s -> %s). Le demarrage automatique est ARME.' % (sha(brut), sha(lire(c['mods_xml']))))
    return 0


def cmd_desarmer(a, c, silencieux=False):
    exiger_jeu_ferme(a)
    if not os.path.isfile(c['mods_xml']):
        if not silencieux:
            print('mods.xml introuvable : rien a decocher.')
        return 0
    brut, txt = lire_mods_xml(c)
    ligne = ligne_mods_xml(c)
    n = txt.count(ligne)
    if n == 0:
        print('Deja desarme : mods.xml ne cite pas le mod.')
        return 0
    if n > 1:
        sys.exit('REFUS : mods.xml cite le mod %d fois ; je ne choisis pas a ta place. Rien n\'est ecrit.' % n)
    sauvegarder_mods_xml(c, brut, a, 'demarrage_desarme')
    nouveau = txt.replace(ligne, '').encode('utf-8')
    charger_mod_mesures().valider_xml(nouveau)
    ecrire_atomique(c['mods_xml'], nouveau)
    print('mods.xml : la ligne du mod est retiree. Le demarrage automatique est DESARME.')
    return 0


def cmd_desinstaller(a, c):
    exiger_jeu_ferme(a)
    pb = 0
    # 1. le fichier du dossier du jeu d'abord (le plus important a remettre)
    for n in range(10):
        f = os.path.join(c['scripts_rom'], 'library_custom_%d.lua' % n)
        e, t = etat_rom(f)
        if e == 'notre script':
            ok = vider(f) and sha(lire(f)) == VIDE
            print('rom_0 library_custom_%d.lua : remis a 0 octet : %s' % (n, 'oui' if ok else 'NON, A VERIFIER'))
            pb += 0 if ok else 1
        elif e == 'AUTRE CONTENU':
            print('rom_0 library_custom_%d.lua : contenu qui n\'est pas le notre (%d octets) : je n\'y touche pas.' % (n, t))
    # 2. l'interrupteur
    try:
        cmd_desarmer(a, c, silencieux=True)
    except SystemExit as ex:
        print(ex.code)
        pb += 1
    arme_encore = os.path.isfile(c['mods_xml']) and ligne_mods_xml(c) in lire(c['mods_xml']).decode('utf-8', 'replace').replace('\r\n', '\n')
    # 3. le dossier du mod (jamais s'il est encore cite par mods.xml)
    if arme_encore:
        print('Dossier du mod GARDE : mods.xml le cite encore (decoche-le dans le menu MODS ou corrige mods.xml, puis refais « desinstaller »).')
        pb += 1
    elif os.path.isdir(c['dossier_mod']):
        presents = set(fichiers_du_dossier(c['dossier_mod']))
        attendus = set(contenu_mod(a))
        # le numero du fichier library_custom du mod peut avoir ete celui d'une autre installation : on accepte n'importe lequel
        attendus |= {os.path.join('content', 'scripts', 'library_custom_%d.lua' % n) for n in range(10)}
        if presents <= attendus:
            shutil.rmtree(c['dossier_mod'])
            print('Dossier du mod supprime : %s' % c['dossier_mod'])
        else:
            print('Dossier du mod GARDE : il contient des fichiers que je n\'ai pas crees : %s' % sorted(presents - attendus))
            pb += 1
    else:
        print('Dossier du mod : deja absent.')
    print('FAIT.' if pb == 0 else '%d POINT(S) A VERIFIER (voir plus haut).' % pb)
    return 0 if pb == 0 else 1


def analyser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument('commande', choices=['etat', 'installer', 'armer', 'desarmer', 'desinstaller'])
    ap.add_argument('--racine', default=None)
    ap.add_argument('--dossier-jeu', default=JEU_DEFAUT)
    ap.add_argument('--rom', type=int, default=0)
    ap.add_argument('--mode', choices=('nouvelle', 'charger'), default='nouvelle')
    ap.add_argument('--partie', type=int, default=19)
    ap.add_argument('--attente', type=int, default=30)
    ap.add_argument('--attendre-touche', action='store_true')
    ap.add_argument('--date')
    a = ap.parse_args()
    if a.racine is None:
        a.racine = racine_defaut()
    if not 0 <= a.rom <= 9:
        sys.exit('REFUS : --rom : un numero entre 0 et 9')
    if not 0 <= a.partie <= 99:
        sys.exit('REFUS : --partie : un numero de sauvegarde entre 0 et 99')
    if not 3 <= a.attente <= 600:
        sys.exit('REFUS : --attente : entre 3 et 600 secondes')
    return a


def main():
    a = analyser()
    c = chemins(a)
    return {'etat': cmd_etat, 'installer': cmd_installer, 'armer': cmd_armer, 'desarmer': cmd_desarmer,
            'desinstaller': cmd_desinstaller}[a.commande](a, c)


if __name__ == '__main__':
    sys.exit(main())
