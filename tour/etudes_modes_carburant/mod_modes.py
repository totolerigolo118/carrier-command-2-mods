#!/usr/bin/env python3
"""Installe / retire le mod local `cc2_modes` (etude des modes ECO / NORMAL / FLANK).

Meme outil et memes securites que tour/outils/mod_mesures.py (qu'il reutilise sans le modifier) :
sauvegarde datee de mods.xml, UNE ligne ajoutee, sha256 des scripts verifie avant et apres copie,
refuse si le jeu tourne, ne remplace jamais un dossier existant, ne touche jamais au dossier du jeu.

Le mod a deux scripts, installables separement (etapes du plan) :
  --etape mesure     library_custom_3.lua : telemetrie en LECTURE SEULE (ecrit dans cc2x.log)      [etape 0b]
  --etape interface  library_custom_5.lua : onglet SPEED, maquette SANS EFFET                       [etape 2]
  --etape interface2 library_custom_5.lua v2 : le meme onglet branche sur le plugin cc2x_modes v3 (sans plugin : maquette)
  --etape interface2_1 library_custom_5.lua v2.1 : v2 + garde-fou pilotage pose sans condition et avant/apres update, « PLUGIN PLEIN »
  --etape tout       mesure + interface (v1)      --etape tout2   mesure + interface2 (v2)      --etape tout2_1   mesure + v2.1

  python mod_modes.py etat          [--racine DOSSIER]
  python mod_modes.py installer     --etape mesure|interface|interface2|interface2_1|tout|tout2|tout2_1 [--racine DOSSIER] [--date AAAA-MM-JJ]
  python mod_modes.py mettre-a-jour --etape mesure|interface|interface2|interface2_1|tout|tout2|tout2_1 [--racine DOSSIER]   (ajoute / remplace un script, mods.xml intact)
  python mod_modes.py retirer       [--racine DOSSIER]                 (retire aussi le plugin s'il est pose)

Plugin ECO / FLANK (etape 3c ; plugin/cc2x_modes.c = v3, plugin/v3_1/cc2x_modes.c = v3.1, construits dans des dossiers de travail separes) :
  python mod_modes.py poser-plugin   [--racine DOSSIER]   copie cc2x_modes.dll (la v3.1, sha256 verifie) dans mods\\cc2_modes\\content\\cc2x\\
  python mod_modes.py retirer-plugin [--racine DOSSIER]   supprime ce fichier seulement
  python mod_modes.py mettre-a-jour-plugin [--version 3|3.1] [--racine DOSSIER]   remplace la version posee (une version CONNUE) par la v3.1 (defaut)
                                                          ou par la v3 (--version 3 : retour arriere) ; toujours sha256 verifie, jeu ferme
  Le dossier du jeu n'est jamais touche ; le SDK charge ce plugin au prochain lancement parce que cc2_modes est actif ; sans
  modes.ini il OBSERVE seulement. Toutes les commandes qui ecrivent REFUSENT si le jeu tourne (copies d'essai comprises :
  carrier_command*.exe, donc aussi l'ancien exe de la voie A) ; l'option --jeu-ouvert-ok de l'outil de base est refusee ici.

--racine vaut par defaut %APPDATA%\\Carrier Command 2 (le vrai dossier) ; donne un autre dossier pour essayer.
"""
import argparse
import hashlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ICI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ICI, 'lua')
MESURE = ('library_custom_3.lua', (SRC, '283C0EC24B242F9DDFB0CAA6EAEEE1E15E88F9B8CB400E5CCAF93EEC73766DB0'))
UI_V1 = ('library_custom_5.lua', (SRC, 'F0DF2F5B160EEE961E96870DADAB00E937306976FEC283AC6C5FC660A1095EE3'))      # maquette sans effet (posee le 27/10)
UI_V2 = ('library_custom_5.lua', (os.path.join(SRC, 'v2'), '0A402A3E7865B9840D0EFE04874F6E3634E81EF74C4905428918686BB83D779F'))   # branchee sur le plugin v3 (posee le 30/10)
UI_V2_1 = ('library_custom_5.lua', (os.path.join(SRC, 'v2_1'), 'C91FFDEBE7CBE08DFD27EB83F492BB261686B0C4CEE084F482BE05D578E197A2'))   # v2 + corrections ONG-R1 / R2 / 1 (PAS posee)
ETAPES = {'mesure': dict([MESURE]), 'interface': dict([UI_V1]), 'interface2': dict([UI_V2]), 'interface2_1': dict([UI_V2_1]),
          'tout': dict([MESURE, UI_V1]), 'tout2': dict([MESURE, UI_V2]), 'tout2_1': dict([MESURE, UI_V2_1])}
UI_CONNUES = {UI_V1[1][1]: 'v1 (maquette sans effet)', UI_V2[1][1]: 'v2 (branchee sur le plugin v3)',
              UI_V2_1[1][1]: 'v2.1 (v2 + garde-fou pilotage corrige + PLUGIN PLEIN)'}
MOD_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<data name="Modes CC2" author="Yolo" description="Etude des modes de vitesse ECO / NORMAL / FLANK par avion. '
           'MESURE (library_custom_3.lua) : en lecture seule, ecrit dans le journal du SDK CC2X (cc2x.log) la vitesse, '
           'les gaz et le carburant de tes avions en l air, toutes les 5 s ; sans CC2X il ne fait rien. '
           'ONGLET (library_custom_5.lua) : une fenetre SPEED sous LOADOUT quand tu cliques sur un avion, avec trois '
           'boutons ECO / NORMAL / FLANK. Sans le plugin cc2x_modes.dll c est une MAQUETTE SANS EFFET ; avec le plugin il regle le '
           'mode de l avion (le plugin n agit que si modes.ini a enabled=1) et previent le plugin quand tu pilotes un avion. '
           'Aucun fichier ecrit hors cc2x.log, aucun reseau. '
           'Pour le retirer : enlever la ligne cc2_modes de mods.xml.">\n</data>\n')


# Les DLL de reference, une par version, chacune dans son dossier de travail (hors depot) ; le sha256 est verifie avant toute copie.
PLUGINS = {
    '3.1': (Path(r'C:\Users\UTILISATEUR\Documents\cc2-modes-travail-v3_1\dist\cc2x_modes.dll'),     # construit par plugin/v3_1/construire_v3_1.py (PAS posee)
            '4B2EBC04D772D7EFB2F21E70AA17CB7FE26CF7A044FDFE3B97F07FDCD1FE1D51'),             # v3 + lecture stricte de modes.ini + lignes de journal reservees
    '3': (Path(r'C:\Users\UTILISATEUR\Documents\cc2-modes-travail\dist\cc2x_modes.dll'),            # construit par plugin/construire_modes.py (posee le 30/10)
          '331581C64CB880AB0BC8CBC3258414F55C41723FB8DA7042CFDABE08CABC8729'),                # v2 + pont Lua cc2x.modes.* + garde-fou pilotage + 2 builds du jeu
}
PLUGIN_COURANT = '3.1'                                   # la version que poser-plugin / mettre-a-jour-plugin installent par defaut
PLUGIN_SRC, PLUGIN_SHA = PLUGINS[PLUGIN_COURANT]
PLUGIN_ANCIENS = {'AB2D5343C983C97784616A3965CA26BD1072B99DE82E92A474F9814A993A46E4': 'v1 (ECO seul)',      # posee le 28/10, plus de DLL de reference
                  '8B3A5A874599BD9FE8D84C51632A2FBE6F7AE829CCF5B8C5CB0BB70A576CDB35': 'v2 (ECO par type + FLANK, sans Lua)'}
PLUGIN_NOMS = {sha: 'v' + v for v, (_, sha) in PLUGINS.items()}           # sha256 -> « v3.1 », « v3 »
PLUGIN_CONNUS = dict(PLUGIN_ANCIENS, **PLUGIN_NOMS)                       # toutes les versions que cet outil reconnait (et peut donc retirer / remplacer)
PLUGIN_REL = os.path.join('content', 'cc2x', 'cc2x_modes.dll')     # le SDK charge content\\cc2x\\*.dll des mods actifs


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def _jeu_ouvert():
    """True / False ; None si on ne peut pas le savoir. Voit aussi les copies d'essai (carrier_command_test_*.exe)."""
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq carrier_command*', '/NH'],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return None
    return 'carrier_command' in out.lower()


def _racine_vraie(racine):
    vrai = os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2')
    return os.path.normcase(os.path.abspath(racine)) == os.path.normcase(os.path.abspath(vrai))


def plugin_chemin(racine):
    return os.path.join(racine, 'mods', 'cc2_modes', PLUGIN_REL)


def plugin_etat(racine):
    p = plugin_chemin(racine)
    if not os.path.isfile(p):
        return 'absent'
    s = _sha(p)
    if s == PLUGIN_SHA:
        return '%s conforme (sha256 %s...)' % (PLUGIN_NOMS[s], PLUGIN_SHA[:8])
    if s in PLUGIN_CONNUS:
        return '%s (sha256 %s...) : mettre-a-jour-plugin le remplacera par la v%s' % (PLUGIN_CONNUS[s], s[:8], PLUGIN_COURANT)
    return 'DIFFERENT de tout ce que cet outil connait'


def plugin_mettre_a_jour(racine, version=None):
    """Remplace une version CONNUE du plugin par la version voulue (par defaut la courante), dans le mod cc2_modes seulement."""
    version = version or PLUGIN_COURANT
    if version not in PLUGINS:
        sys.exit("REFUS : version de plugin inconnue (%s) ; versions connues : %s. Rien n'est ecrit." % (version, ', '.join(sorted(PLUGINS))))
    source, voulu = PLUGINS[version]
    if _racine_vraie(racine) and _jeu_ouvert() is not False:
        sys.exit("REFUS : le jeu tourne (ou je ne peux pas le verifier ; copies d'essai comprises). Ferme-le. Rien n'est ecrit.")
    dest = plugin_chemin(racine)
    if not os.path.isfile(dest):
        sys.exit("REFUS : aucun plugin pose (utilise poser-plugin). Rien n'est ecrit.")
    actuel = _sha(dest)
    if actuel == voulu:
        print('plugin : deja a jour (v%s).' % version)
        return 0
    if actuel not in PLUGIN_CONNUS:
        sys.exit("REFUS : le plugin pose n'est aucune version connue (sha256 %s). Rien n'est ecrit." % actuel)
    if not source.is_file() or _sha(source) != voulu:
        sys.exit("REFUS : la DLL de reference de la v%s n'est pas celle controlee (sha256 different ou absente : %s). Rien n'est ecrit." % (version, source))
    tmp = dest + '.cc2_tmp'
    try:
        Path(tmp).write_bytes(source.read_bytes())
        if _sha(tmp) != voulu:
            sys.exit("ERREUR : copie differente de la source. L'ancien plugin reste en place.")
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    print('FAIT : plugin %s remplace par la v%s (sha256 %s). Sans modes.ini ou avec enabled=0 il OBSERVE seulement.'
          % (PLUGIN_CONNUS[actuel], version, _sha(dest)))
    autre = [v for v in sorted(PLUGINS) if v != version]
    print('Retour arriere (jeu ferme) : %s ; ou retirer-plugin.' % (
        ' / '.join('mettre-a-jour-plugin --version %s' % v for v in autre) if autre else 'retirer-plugin'))
    return 0


def plugin_poser(racine):
    """Copie cc2x_modes.dll dans le mod cc2_modes (jamais dans le dossier du jeu). mods.xml n'est PAS touche."""
    if _racine_vraie(racine) and _jeu_ouvert() is not False:
        sys.exit("REFUS : le jeu tourne (ou je ne peux pas le verifier ; copies d'essai comprises). Ferme-le. Rien n'est ecrit.")
    mod = os.path.join(racine, 'mods', 'cc2_modes')
    if not os.path.isdir(mod):
        sys.exit("REFUS : le mod cc2_modes n'est pas installe (utilise `installer`). Rien n'est ecrit.")
    xml = os.path.join(racine, 'mods.xml')
    if not os.path.isfile(xml) or ('<path value="%s"/>' % mod) not in open(xml, encoding='utf-8').read():
        sys.exit("REFUS : cc2_modes n'est pas actif dans mods.xml : le plugin ne serait pas charge. Rien n'est ecrit.")
    if not PLUGIN_SRC.is_file() or _sha(PLUGIN_SRC) != PLUGIN_SHA:
        sys.exit("REFUS : la DLL construite n'est pas celle controlee (sha256 different ou absente : %s). Rien n'est ecrit." % PLUGIN_SRC)
    dest = plugin_chemin(racine)
    if os.path.exists(dest):
        sys.exit('REFUS : %s existe deja (je ne remplace jamais un fichier). Utilise retirer-plugin d\'abord. Rien n\'est ecrit.' % dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + '.cc2_tmp'
    try:
        Path(tmp).write_bytes(PLUGIN_SRC.read_bytes())
        if _sha(tmp) != PLUGIN_SHA:
            sys.exit('ERREUR : copie differente de la source. Rien n\'est laisse en place.')
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    print('FAIT : plugin pose : %s (sha256 %s). Sans modes.ini il OBSERVE seulement (rien n\'est ecrit dans le jeu).' % (dest, _sha(dest)))
    print('Retour arriere : python mod_modes.py retirer-plugin (jeu ferme), ou supprimer ce fichier.')
    return 0


def plugin_retirer(racine, silencieux=False):
    if _racine_vraie(racine) and _jeu_ouvert() is not False:
        sys.exit("REFUS : le jeu tourne (ou je ne peux pas le verifier). Ferme-le puis recommence. Rien n'est supprime.")
    dest = plugin_chemin(racine)
    if not os.path.isfile(dest):
        if not silencieux:
            print('plugin : rien a retirer.')
        return 0
    if _sha(dest) not in PLUGIN_CONNUS:
        print('plugin GARDE : %s n\'est pas une version que j\'ai posee (sha256 inconnu).' % dest)
        return 1
    os.remove(dest)
    d = os.path.dirname(dest)
    if not os.listdir(d):
        os.rmdir(d)
    print('plugin retire : %s' % dest)
    return 0


def charger_outil():
    p = os.path.normpath(os.path.join(ICI, '..', 'outils', 'mod_mesures.py'))
    spec = importlib.util.spec_from_file_location('mod_mesures_base', p)
    mm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mm)
    # I2 (revue du 29/10) : l'outil de base ne cherche que « carrier_command.exe » et rate l'ancien exe de la voie A
    # (carrier_command_ancien_*.exe). Ses fonctions cherchent jeu_ouvert dans leur module a chaque appel : on y met la verification large.
    mm.jeu_ouvert = _jeu_ouvert
    return mm


def main():
    pre = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    pre.add_argument('--etape', choices=sorted(ETAPES))
    a, reste = pre.parse_known_args()
    commande = next((x for x in reste if not x.startswith('-')), None)
    if '--jeu-ouvert-ok' in reste:                  # l'outil de base permet de passer outre le refus ; ici non (revue du 29/10, I2)
        sys.exit("REFUS : --jeu-ouvert-ok n'est pas accepte par mod_modes.py : ferme le jeu (ancien exe compris). Rien n'est ecrit.")
    if commande in ('poser-plugin', 'retirer-plugin', 'mettre-a-jour-plugin'):
        rac = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
        rac.add_argument('commande')
        rac.add_argument('--racine', default=os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2'))
        rac.add_argument('--version', default=None)
        r, _ = rac.parse_known_args(reste)
        if commande == 'poser-plugin':
            return plugin_poser(r.racine)
        return plugin_mettre_a_jour(r.racine, r.version) if commande == 'mettre-a-jour-plugin' else plugin_retirer(r.racine)
    if commande == 'retirer':           # le plugin d'abord (il est dans le dossier du mod), puis le mod
        rac = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
        rac.add_argument('commande')
        rac.add_argument('--racine', default=os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2'))
        r, _ = rac.parse_known_args(reste)
        if plugin_retirer(r.racine, silencieux=True) != 0:
            sys.exit('REFUS : le plugin present n\'est pas celui pose par cet outil ; rien d\'autre n\'est retire.')
    if commande in ('installer', 'mettre-a-jour') and not a.etape:
        sys.exit('REFUS : donne --etape %s.' % ', '.join(sorted(ETAPES)))
    if a.etape and commande in ('installer', 'mettre-a-jour'):
        scripts = dict(ETAPES[a.etape])
    elif commande == 'etat':
        scripts = dict([MESURE])                    # l'onglet est decrit a part (v1 ou v2)
    else:
        scripts = dict(ETAPES['tout'])
    mm = charger_outil()
    mm.NOM = 'cc2_modes'
    mm.MOD_XML = MOD_XML
    mm.SCRIPTS = scripts
    sys.argv = [sys.argv[0]] + reste
    code = mm.main()
    if commande == 'etat':
        rac = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
        rac.add_argument('commande')
        rac.add_argument('--racine', default=os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2'))
        r, _ = rac.parse_known_args(reste)
        ui = os.path.join(r.racine, 'mods', 'cc2_modes', 'content', 'scripts', 'library_custom_5.lua')
        if os.path.isfile(ui):
            print('  %-22s onglet %s' % ('library_custom_5.lua', UI_CONNUES.get(_sha(ui), 'DIFFERENT de toutes les versions connues')))
        else:
            print('  %-22s absent' % 'library_custom_5.lua')
        print('  %-22s %s' % ('plugin cc2x_modes.dll', plugin_etat(r.racine)))
    return code


if __name__ == '__main__':
    sys.exit(main())
