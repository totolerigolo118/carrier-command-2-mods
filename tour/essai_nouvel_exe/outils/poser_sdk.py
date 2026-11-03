#!/usr/bin/env python3
"""Pose / retour arriere du SDK CC2X A DEUX PROFILS (dinput8.dll) dans le dossier du jeu.

  python -I -B poser_sdk.py etat    --jeu DOSSIER_DU_JEU
  python -I -B poser_sdk.py poser   --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]    (184B144D... -> E1DE25D5...)
  python -I -B poser_sdk.py revenir --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]    (E1DE25D5... -> 184B144D...)

Pourquoi : le SDK pose le 27/10 (184B144D..., un profil) ne connait que l'ancien exe ; sur le build de Steam du 28/10 (0x6ae228f3) il
reste inactif. La DLL a deux profils (E1DE25D5..., compilee par la conversation « port-nouvel-exe ») reconnait les deux exe et a ete
relue par une autre conversation : tour/revue_sdk_deux_profils/VERDICT.md (worktree quirky-wright), pose acceptable 🟡.

Securites (meme esprit que poser.py, dont on reprend les fonctions et les empreintes) :
  - les deux DLL sources ont un sha256 EPINGLE ci-dessous ; la DLL du jeu doit etre EXACTEMENT celle qu'on remplace (sinon refus) ;
  - le jeu doit etre FERME (tout processus carrier_command* lance depuis ce dossier) ; sur un chemin « steamapps » il faut
    --cest-le-vrai-jeu ;
  - `poser` refait d'abord la condition 2 du verdict : il liste ce que le SDK chargera et REFUSE s'il trouve autre chose que nos
    compilations connues (cc2x_frein.dll du jeu, plugins des mods de poser.MODS_PLUGINS_CONNUS), un dossier cc2x\\plugins ou un cc2x.ini ;
  - ecriture dans un fichier temporaire, relecture du sha256, puis renommage ; relecture finale ; une seule ecriture : <jeu>\\dinput8.dll ;
  - rien d'autre n'est touche (exe, plugins, mods.xml, .ini). Python standard seulement, aucun reseau.
"""
import argparse
import importlib.util
import os
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('poser', ICI / 'poser.py')
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)                    # sha, refus, ecrire, jeu_ouvert, mods_avec_cc2x, mods_cc2x_inconnus, empreintes

NOUVELLE = (Path(r'C:\Users\UTILISATEUR\Documents\cc2-port-travail\sdk\dist\dinput8.dll'),
            'E1DE25D53A5588BDA62269D6D93335ACB9F32EA555AC9274FE7973C19D6225D7')      # deux profils (relue le 31/10)
ANCIENNE = (Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\dist\dinput8.dll'),
            '184B144D6E2BB868FFEB7D45ECD463F8919E64732E3B5681A16165363EBA0982')      # un profil (posee le 27/10, relue le 27/10)
NOMS = {NOUVELLE[1]: 'SDK a DEUX profils (E1DE25D5...)', ANCIENNE[1]: 'SDK a UN profil, ancien exe seulement (184B144D...)'}


def preparer(args):
    jeu = Path(args.jeu)
    if not jeu.is_dir():
        P.refus(f"{jeu} n'est pas un dossier")
    if 'steamapps' in os.path.abspath(jeu).lower() and not args.cest_le_vrai_jeu:
        P.refus("ce chemin ressemble au VRAI jeu (steamapps). Ajouter --cest-le-vrai-jeu pour confirmer que c'est voulu.")
    appdata = args.appdata or os.environ.get('APPDATA')
    if not appdata:
        P.refus('%APPDATA% introuvable : donner --appdata')
    return jeu, appdata


def source_ok(source):
    chemin, attendu = source
    if not chemin.is_file():
        P.refus(f'DLL source introuvable : {chemin}')
    octets = chemin.read_bytes()
    if P.sha(octets) != attendu:
        P.refus(f"{chemin} n'a pas le sha256 epingle ({attendu[:8]}...) : rien n'est fait")
    return octets


def sha_du_jeu(jeu):
    f = Path(jeu) / 'dinput8.dll'
    return P.sha(f.read_bytes()) if f.is_file() else None


def ce_que_le_sdk_chargera(jeu, appdata):
    """-> (liste lisible des plugins, liste des problemes). Condition 2 du verdict du 31/10."""
    jeu = Path(jeu)
    plugins, problemes = [], []
    for f in sorted(jeu.glob('cc2x_*.dll')):
        s = P.sha(f.read_bytes())
        if f.name.lower() == 'cc2x_frein.dll' and s in ({P.SHA['cc2x_frein.dll']} | P.SHA_ANCIENNES['cc2x_frein.dll']):
            plugins.append(f"{f} ({s[:8]}...{', v15' if s == P.SHA['cc2x_frein.dll'] else ', une version precedente'})")
        else:
            problemes.append(f'{f} : pas une de nos compilations connues ({s[:8]}...)')
    if (jeu / 'cc2x' / 'plugins').exists():
        problemes.append(f"{jeu / 'cc2x' / 'plugins'} existe (le SDK y chargerait des DLL)")
    if (jeu / 'cc2x.ini').exists():
        problemes.append(f"{jeu / 'cc2x.ini'} existe (option developpeur lue par le SDK)")
    dossiers = P.mods_avec_cc2x(appdata)
    inconnus = P.mods_cc2x_inconnus(dossiers)
    problemes += [f'{f} : fichier inconnu dans un dossier cc2x de mod actif' for f in inconnus]
    for d in dossiers:
        for f in sorted(Path(d).iterdir()):
            if str(f) not in inconnus:
                plugins.append(f'{f} ({P.sha(f.read_bytes())[:8]}...)')
    return plugins, problemes


def afficher(jeu, appdata):
    print('Dossier du jeu :', os.path.abspath(jeu))
    s = sha_du_jeu(jeu)
    print('  dinput8.dll :', 'absent' if s is None else NOMS.get(s, f'AUTRE DLL ({s[:8]}...)'))
    exe = Path(jeu) / 'carrier_command.exe'
    if exe.is_file():
        print(f'  carrier_command.exe : horodatage PE {P.pe_de(exe)[0]:#010x}')
    plugins, problemes = ce_que_le_sdk_chargera(jeu, appdata)
    print('  plugins que le SDK chargera :' + ''.join('\n    ' + p for p in plugins) if plugins else '  plugins que le SDK chargera : aucun')
    for p in problemes:
        print('  PROBLEME :', p)
    o = P.jeu_ouvert(jeu)
    print('  jeu lance :', {True: 'OUI', False: 'non', None: 'inconnu'}[o])
    return problemes


def jeu_ferme(jeu):
    o = P.jeu_ouvert(jeu)
    if o is None:
        P.refus("impossible de savoir si le jeu tourne : par prudence, rien n'est fait")
    if o:
        P.refus("un processus carrier_command* tourne depuis ce dossier : le fermer d'abord")


def remplacer(args, depart, arrivee, controle_chargeur):
    jeu, appdata = preparer(args)
    problemes = afficher(jeu, appdata)
    print()
    octets = source_ok(arrivee)
    source_ok(depart)                                       # le retour arriere doit exister AVANT qu'on pose quoi que ce soit
    s = sha_du_jeu(jeu)
    if s == arrivee[1]:
        print('Deja en place, rien a faire :', NOMS[arrivee[1]])
        return
    if s != depart[1]:
        P.refus(f"dinput8.dll du jeu n'est pas exactement {NOMS[depart[1]]} : on ne remplace pas un fichier inconnu")
    if controle_chargeur and problemes:
        P.refus('le SDK chargerait ou lirait des fichiers inconnus (voir PROBLEME ci-dessus) : rien n\'est pose')
    jeu_ferme(jeu)
    print(f'Action :\n  remplacer {Path(jeu) / "dinput8.dll"} ({NOMS[depart[1]]})\n  par {arrivee[0]} ({NOMS[arrivee[1]]})')
    if args.a_blanc:
        print('\nA BLANC : rien ecrit.')
        return
    P.ecrire(Path(jeu) / 'dinput8.dll', octets, arrivee[1])
    print(f'\nTERMINE : dinput8.dll = {NOMS[arrivee[1]]} (sha256 relu). Executables, plugins, mods et reglages non touches.')


def cmd_etat(args):
    jeu, appdata = preparer(args)
    afficher(jeu, appdata)


def cmd_poser(args):
    remplacer(args, ANCIENNE, NOUVELLE, controle_chargeur=True)


def cmd_revenir(args):
    remplacer(args, NOUVELLE, ANCIENNE, controle_chargeur=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], allow_abbrev=False)
    ap.add_argument('commande', choices=('etat', 'poser', 'revenir'))
    ap.add_argument('--jeu', required=True)
    ap.add_argument('--appdata', help='racine %%APPDATA%% (pour les essais sur un faux dossier)')
    ap.add_argument('--a-blanc', action='store_true')
    ap.add_argument('--cest-le-vrai-jeu', action='store_true')
    args = ap.parse_args()
    {'etat': cmd_etat, 'poser': cmd_poser, 'revenir': cmd_revenir}[args.commande](args)


if __name__ == '__main__':
    main()
