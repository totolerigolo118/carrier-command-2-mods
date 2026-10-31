#!/usr/bin/env python3
"""Compile et teste le plugin cc2x_modes v3.1 (dossier plugin/v3_1), dans un dossier de travail A PART. Rien n'est copie dans le jeu.

    python -I construire_v3_1.py                    compile deux fois + controle des imports + compile le banc de la v3.1
    python -I construire_v3_1.py --lancer-tests     ... et lance le banc (programme 32 bits ecrit par nous, sans le jeu)
    python -I construire_v3_1.py --ancien-banc      ... et lance AUSSI le banc de la v3 (inchange) contre la source v3.1,
                                                    pour savoir lesquels des 130 controles de la v3 ne passent plus

Reutilise `plugin/construire_modes.py` (donc les controles de tour/atterrissage_manuel/frein/construire.py) SANS le modifier :
seuls le dossier source, le dossier de travail et le rapport sont changes. Le dossier de travail de la v3 (cc2-modes-travail, dont
dist\\cc2x_modes.dll = la v3 posee) n'est jamais touche ; le rapport de la v3 (plugin/RAPPORT_compilation.md) non plus.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
BASE = ICI.parent / 'construire_modes.py'
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-modes-travail-v3_1')
RAPPORT = ICI / 'RAPPORT_compilation.md'


def charger(chemin, nom):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def banc_de_la_v3():
    """Compile le banc de la v3 (tests/test_modes.c de plugin/, inchange) contre la source v3.1 et le lance."""
    m = charger(BASE, 'construire_modes_v31_ancien')
    c = m.charger()
    c.TRAVAIL = TRAVAIL
    src = TRAVAIL / 'ancien_banc'
    (src / 'plugin' / 'tests').mkdir(parents=True, exist_ok=True)
    (src / 'plugin' / 'cc2x_modes.c').write_bytes((ICI / 'cc2x_modes.c').read_bytes())
    (src / 'plugin' / 'tests' / 'test_modes.c').write_bytes((ICI.parent / 'tests' / 'test_modes.c').read_bytes())
    (TRAVAIL / 'reglages_ancien').mkdir(exist_ok=True)
    exe = TRAVAIL / 'test' / 'test_modes_v3_contre_v3_1.exe'
    print('\nbanc de la v3 (inchange) contre la source v3.1 (UBSan, -Werror)')
    c.zig(['-fsanitize=undefined', '-Werror', '-I', TRAVAIL / 'sources' / 'include', src / 'plugin' / 'tests' / 'test_modes.c', '-o', exe])
    c.nettoyer(TRAVAIL / 'test')
    r = subprocess.run([str(exe), str(TRAVAIL / 'reglages_ancien')], cwd=TRAVAIL / 'test')
    print('(code de sortie du banc de la v3 contre la v3.1 : %d)' % r.returncode)
    return r.returncode


def banc_avec_exemple():
    """Relance le banc de la v3.1 en lui donnant modes.ini.example : il doit se lire sans aucun avertissement."""
    (TRAVAIL / 'reglages_exemple').mkdir(exist_ok=True)
    exe = TRAVAIL / 'test' / 'test_modes.exe'
    print('\nbanc de la v3.1 + lecture de modes.ini.example')
    r = subprocess.run([str(exe), str(TRAVAIL / 'reglages_exemple'), str(ICI / 'modes.ini.example')], cwd=TRAVAIL / 'test')
    print('(code de sortie : %d)' % r.returncode)
    return r.returncode


def main():
    ancien = '--ancien-banc' in sys.argv
    if ancien:
        sys.argv.remove('--ancien-banc')
    avec_tests = '--lancer-tests' in sys.argv
    m = charger(BASE, 'construire_modes_v31')
    m.ICI = ICI                    # sources : plugin/v3_1/cc2x_modes.c et plugin/v3_1/tests/test_modes.c
    m.TRAVAIL = TRAVAIL
    m.RAPPORT = RAPPORT
    code = 0
    try:
        m.main()
    except SystemExit as e:
        code = e.code or 0
    if avec_tests:
        code = code or banc_avec_exemple()
    if ancien:
        banc_de_la_v3()
    sys.exit(code)


if __name__ == '__main__':
    main()
