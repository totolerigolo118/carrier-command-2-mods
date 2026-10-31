#!/usr/bin/env python3
"""Copie l'ANCIEN executable du jeu a cote du vrai (build 1.5.18 du 20/06/2026, celui de tous nos essais) et le lance directement.

  python -I lancer_ancien.py etat    --jeu DOSSIER_DU_JEU
  python -I lancer_ancien.py copier  --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]
  python -I lancer_ancien.py lancer  --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]
  python -I lancer_ancien.py retirer --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]

Pourquoi : la mise a jour Steam du 28/10/2026 a remplace carrier_command.exe (horodatage PE 0x6ae228f3). Le SDK dinput8.dll ne
s'active que pour l'horodatage 0x6a36c177 : sur le nouvel exe nos plugins ne sont pas charges. Voir tour/etude_mise_a_jour/ETUDE.md.

Securites :
  - l'exe copie est tour/sauvegardes/carrier_command_1.5.18_patche_8E7FCBB6.exe, verifie par son sha256 epingle ET par son
    horodatage PE ; il est ecrit sous un NOUVEAU nom (carrier_command_ancien_8E7FCBB6.exe), jamais par-dessus un autre fichier ;
  - carrier_command.exe (celui de Steam) n'est JAMAIS lu en ecriture, ni supprime ;
  - rien n'est copie ni supprime ni lance si un processus carrier_command* tourne depuis ce dossier (ou si on ne sait pas) ;
  - `lancer` refuse si Steam n'est pas ouvert, si dinput8.dll ou cc2x_frein.dll n'ont pas EXACTEMENT les sha256 epingles par poser.py,
    ou si la copie a ete changee ; il lance l'exe directement (pas par Steam), puis lit cc2x.log pour dire si le SDK s'est active ;
  - `retirer` ne supprime la copie que si son sha256 est exactement le bon ;
  - sur un chemin « steamapps » il faut --cest-le-vrai-jeu. Python standard seulement, aucun reseau.
"""
import argparse
import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

ICI = Path(__file__).resolve().parent
SOURCE = ICI.parents[1] / 'sauvegardes' / 'carrier_command_1.5.18_patche_8E7FCBB6.exe'
NOM = 'carrier_command_ancien_8E7FCBB6.exe'
SHA_ANCIEN = '8E7FCBB6CE27BD3D8FEB02BF7F3DBBA646CCE6D4944360570F082972E8DFE8BE'
PE_ANCIEN = (0x6a36c177, 0x00af7000)

_spec = importlib.util.spec_from_file_location('poser', ICI / 'poser.py')
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)                    # reprend les sha256 epingles, jeu_ouvert, ecrire, refus (une seule source de verite)


def preparer(args):
    jeu = Path(args.jeu)
    if not jeu.is_dir():
        P.refus(f"{jeu} n'est pas un dossier")
    if 'steamapps' in os.path.abspath(jeu).lower() and not args.cest_le_vrai_jeu:
        P.refus("ce chemin ressemble au VRAI jeu (steamapps). Ajouter --cest-le-vrai-jeu pour confirmer que c'est voulu.")
    return jeu


def source_ok():
    if not SOURCE.is_file():
        P.refus(f'sauvegarde introuvable : {SOURCE}')
    octets = SOURCE.read_bytes()
    if P.sha(octets) != SHA_ANCIEN:
        P.refus('la sauvegarde ne porte pas le sha256 attendu (8E7FCBB6...) : on ne copie pas')
    if P.pe_de(SOURCE) != PE_ANCIEN:
        P.refus("la sauvegarde n'a pas l'horodatage PE que le SDK reconnait")
    return octets


def jeu_ferme(jeu):
    o = P.jeu_ouvert(jeu)
    if o is None:
        P.refus("impossible de savoir si le jeu tourne : par prudence, rien n'est fait")
    if o:
        P.refus('un processus carrier_command* tourne depuis ce dossier : le fermer d\'abord')


def steam_tourne(jeu):
    sim = os.environ.get('LANCER_SIMULER_STEAM')
    if sim and P.dans(jeu, P.TRAVAIL):                  # simulation reservee aux faux dossiers de nos essais
        return sim == '1'
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command',
                              'Get-Process -Name steam -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Id'],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None
    return bool(out.strip())


def etat_copie(jeu):
    c = Path(jeu) / NOM
    if not c.is_file():
        return 'absente'
    return 'bonne' if P.sha(c.read_bytes()) == SHA_ANCIEN else 'AUTRE'


def cmd_etat(args):
    jeu = preparer(args)
    exe = jeu / 'carrier_command.exe'
    print('Dossier du jeu :', os.path.abspath(jeu))
    if exe.is_file():
        pe = P.pe_de(exe)
        print(f'  carrier_command.exe : sha256 {P.sha(exe.read_bytes())[:12]}..., horodatage PE {pe[0]:#x}',
              '(le SDK reconnait)' if pe == PE_ANCIEN else '(le SDK reste INACTIF sur cet exe)')
    print(f'  {NOM} :', etat_copie(jeu))
    for nom, attendu in P.SHA.items():
        f = jeu / nom
        s = P.sha(f.read_bytes()) if f.is_file() else None
        print(f'  {nom} :', 'absent' if s is None else ('version attendue' if s == attendu else ('ancienne version de chez nous' if s in P.SHA_ANCIENNES.get(nom, ()) else 'AUTRE version')))
    print('  jeu lance :', {True: 'OUI', False: 'non', None: 'inconnu'}[P.jeu_ouvert(jeu)])
    print('  Steam ouvert :', {True: 'oui', False: 'NON', None: 'inconnu'}[steam_tourne(jeu)])


def cmd_copier(args):
    jeu = preparer(args)
    octets = source_ok()
    jeu_ferme(jeu)
    cible = jeu / NOM
    if cible.exists():
        if cible.is_file() and P.sha(cible.read_bytes()) == SHA_ANCIEN:
            print('Deja en place, rien a faire :', cible)
            return
        P.refus(f'{cible} existe deja avec un autre contenu : on ne remplace jamais un fichier existant')
    print(f'Copie : {SOURCE.name} -> {cible} ({len(octets)} octets, sha256 verifie avant et apres)')
    if args.a_blanc:
        print('A BLANC : rien ecrit.')
        return
    P.ecrire(cible, octets, SHA_ANCIEN)
    print("COPIE TERMINEE. carrier_command.exe (Steam) n'a pas ete touche.")


def cmd_lancer(args):
    jeu = preparer(args)
    cible = jeu / NOM
    if etat_copie(jeu) != 'bonne':
        P.refus(f'{NOM} absent ou modifie : faire `copier` d\'abord')
    if P.pe_de(cible) != PE_ANCIEN:
        P.refus("la copie n'a pas l'horodatage PE que le SDK reconnait")
    for nom, attendu in P.SHA.items():
        f = jeu / nom
        connus = {attendu} | P.SHA_ANCIENNES.get(nom, set())          # nos compilations (la courante ou une precedente), jamais un autre fichier
        if not f.is_file() or P.sha(f.read_bytes()) not in connus:
            P.refus(f'{nom} absent ou pas une de nos compilations epinglees par poser.py : rien n\'est lance')
    if not (jeu / 'steam_appid.txt').is_file():
        P.refus('steam_appid.txt absent : un lancement direct echouerait')
    jeu_ferme(jeu)
    if not steam_tourne(jeu):
        P.refus('Steam ne semble pas ouvert (ou on ne sait pas) : l\'ouvrir d\'abord')
    print(f'Lancement direct (pas par Steam) : {cible}')
    if args.a_blanc:
        print('A BLANC : rien lance.')
        return
    log = jeu / 'cc2x.log'
    avant = log.stat().st_mtime if log.exists() else 0
    DETACHED_PROCESS, NEW_GROUP = 0x00000008, 0x00000200
    subprocess.Popen([str(cible)], cwd=str(jeu), creationflags=DETACHED_PROCESS | NEW_GROUP, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('Lance. Attente du journal du SDK (90 s au plus)...')
    fin = time.time() + 90
    lignes = []
    while time.time() < fin:
        time.sleep(3)
        if log.exists() and log.stat().st_mtime > avant:
            try:
                lignes = log.read_text(encoding='utf-8', errors='replace').splitlines()
            except OSError:
                continue
            if any('loaded' in l or 'stays inactive' in l for l in lignes):
                break
    pertinentes = [l for l in lignes if any(k in l for k in ('ready for', 'plugin', 'inactive', 'unsupported'))][:8]
    for l in pertinentes:
        print('  cc2x.log :', l)
    if any('stays inactive' in l or 'unsupported game build' in l for l in lignes):
        print('ATTENTION : le SDK est INACTIF sur cet exe : l\'essai ne mesurerait rien.')
    elif any('cc2x_frein.dll loaded' in l for l in lignes):
        print('OK : le SDK est actif et le plugin de frein est charge.')
    else:
        print("Pas de confirmation lue dans cc2x.log (le jeu charge encore ?) : relire le journal avant l'essai.")


def cmd_retirer(args):
    jeu = preparer(args)
    cible = jeu / NOM
    if not cible.exists():
        print('Rien a retirer.')
        return
    if etat_copie(jeu) != 'bonne':
        P.refus(f'{cible} ne porte pas le sha256 attendu : on ne supprime que notre copie exacte')
    jeu_ferme(jeu)
    print('Suppression de', cible)
    if args.a_blanc:
        print('A BLANC : rien supprime.')
        return
    cible.unlink()
    print("RETRAIT TERMINE. carrier_command.exe (Steam) n'a pas ete touche.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], allow_abbrev=False)
    ap.add_argument('commande', choices=('etat', 'copier', 'lancer', 'retirer'))
    ap.add_argument('--jeu', required=True)
    ap.add_argument('--a-blanc', action='store_true')
    ap.add_argument('--cest-le-vrai-jeu', action='store_true')
    args = ap.parse_args()
    {'etat': cmd_etat, 'copier': cmd_copier, 'lancer': cmd_lancer, 'retirer': cmd_retirer}[args.commande](args)


if __name__ == '__main__':
    main()
