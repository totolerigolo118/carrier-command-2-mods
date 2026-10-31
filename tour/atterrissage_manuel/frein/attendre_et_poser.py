#!/usr/bin/env python3
"""Attend que le jeu soit ferme, puis pose les deux DLL avec poser.py (phase 1 : tout eteint), puis verifie.

    python -I attendre_et_poser.py --jeu DOSSIER_DU_JEU --cest-le-vrai-jeu [--delai-max-h 8]

Ne lance et ne ferme JAMAIS le jeu. S'arrete sans rien faire apres --delai-max-h heures.
Rien n'est pose si le jeu est ouvert, si l'etat est inconnu, ou si poser.py refuse (il refait toutes ses verifications).
"""
import argparse
import hashlib
import subprocess
import sys
import time
from pathlib import Path

ICI = Path(__file__).resolve().parent
POSER = ICI / 'poser.py'


def poser(*args):
    r = subprocess.run([sys.executable, '-I', str(POSER), *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jeu', required=True)
    ap.add_argument('--cest-le-vrai-jeu', action='store_true')
    ap.add_argument('--delai-max-h', type=float, default=8)
    ap.add_argument('--appdata', help='pour les essais sur un faux dossier')
    args = ap.parse_args()
    jeu = Path(args.jeu)
    exe = jeu / 'carrier_command.exe'
    exe_avant = sha(exe)
    extra = ['--cest-le-vrai-jeu'] if args.cest_le_vrai_jeu else []
    if args.appdata:
        extra += ['--appdata', args.appdata]
    fin = time.time() + args.delai_max_h * 3600
    print(time.strftime('%H:%M:%S'), 'surveillance armee ; exe', exe_avant[:8], '; jeu a fermer par le moddeur', flush=True)
    fermes = 0
    while time.time() < fin:
        _, out = poser('etat', '--jeu', str(jeu), *extra)
        if 'jeu lance : non' in out:
            fermes += 1
        else:
            fermes = 0
        if fermes >= 3:                                  # ferme depuis ~15 s : la fermeture (sauvegarde cloud, etc.) est finie
            break
        time.sleep(5)
    else:
        print(time.strftime('%H:%M:%S'), 'delai depasse : RIEN n\'a ete pose.')
        sys.exit(2)
    print(time.strftime('%H:%M:%S'), 'jeu ferme : pose', flush=True)
    code, out = poser('installer', '--jeu', str(jeu), *extra)
    print(out)
    if code:
        print('POSE REFUSEE par poser.py : rien n\'a ete ecrit.')
        sys.exit(1)
    code, out = poser('etat', '--jeu', str(jeu), *extra)
    print(out)
    ok = (sha(jeu / 'dinput8.dll') == '184B144D6E2BB868FFEB7D45ECD463F8919E64732E3B5681A16165363EBA0982'
          and sha(jeu / 'cc2x_frein.dll') == '941DFFB9F1671CB351A69B826B14E62AB9978390C888257DA699E8584ADC59B3'
          and sha(exe) == exe_avant)
    print('VERIFICATION FINALE :', 'DLL conformes, executable inchange' if ok else 'ECART : a examiner')
    sys.exit(0 if ok else 3)


if __name__ == '__main__':
    main()
