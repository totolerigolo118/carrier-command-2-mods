#!/usr/bin/env python3
"""Compile cc2x_modes.dll (plugin ECO) dans un dossier de travail et controle la DLL. Rien n'est copie dans le jeu.

    python -I construire_modes.py                  compile deux fois + controle des imports + compile le banc d'essai
    python -I construire_modes.py --lancer-tests   ... et lance le banc d'essai (programme 32 bits ecrit par nous, sans le jeu)

Reutilise, sans les modifier, les fonctions de controle de tour/atterrissage_manuel/frein/construire.py (analyse PE,
imports interdits, chaines suspectes, determinisme) et le SDK CC2X fige (commit 7ab05c7, empreintes de cc2x.h verifiees).
Le dossier de travail est a part (pas le cc2-sdk-travail de l'etude d'atterrissage, pas le depot, pas le jeu).
Compilateur : Zig 0.15.2 (pip install ziglang==0.15.2), memes options que build.py du SDK.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
DEPOT = ICI.parents[2]
BASE = DEPOT / 'tour' / 'atterrissage_manuel' / 'frein' / 'construire.py'
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-modes-travail')
RAPPORT = ICI / 'RAPPORT_compilation.md'


def charger():
    spec = importlib.util.spec_from_file_location('construire_base', BASE)
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    return c


def main():
    lancer = '--lancer-tests' in sys.argv
    c = charger()
    c.TRAVAIL = TRAVAIL
    c.EXPORTS_ATTENDUS['cc2x_modes.dll'] = {'cc2x_plugin_load'}
    # entrees : le dossier de travail est a part, le SDK est au bon commit, cc2x.h est conforme a l'empreinte figee
    t = TRAVAIL.resolve()
    for interdit in (DEPOT.resolve(), c.CLONE.resolve(), Path(r'C:\Program Files (x86)\Steam'), Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-travail')):
        if t == interdit or interdit in t.parents:
            c.arret(f'le dossier de travail {t} est dans {interdit}')
    head = subprocess.run(['git', '-C', str(c.CLONE), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    if head != c.COMMIT:
        c.arret(f'le clone est au commit {head}, pas {c.COMMIT}')
    figees = {}
    for ligne in c.EMPREINTES.read_text(encoding='utf-8').splitlines():
        h, _, nom = ligne.partition('  ')
        figees[nom.strip()] = h.strip()
    if figees.get('include/cc2x.h') != c.sha(c.CLONE / 'include' / 'cc2x.h'):
        c.arret('cc2x.h ne correspond pas a l\'empreinte figee')
    print(f'commit {c.COMMIT[:7]} et cc2x.h conformes aux empreintes figees')
    for sous in ('sources', 'dist', 'dist_verif', 'test', 'cache', 'cache_local', 'reglages', 'control'):
        (TRAVAIL / sous).mkdir(parents=True, exist_ok=True)
    src = TRAVAIL / 'sources'
    (src / 'include').mkdir(exist_ok=True)
    (src / 'include' / 'cc2x.h').write_bytes((c.CLONE / 'include' / 'cc2x.h').read_bytes())
    (src / 'plugin' / 'tests').mkdir(parents=True, exist_ok=True)
    (src / 'plugin' / 'cc2x_modes.c').write_bytes((ICI / 'cc2x_modes.c').read_bytes())
    (src / 'plugin' / 'tests' / 'test_modes.c').write_bytes((ICI / 'tests' / 'test_modes.c').read_bytes())
    (TRAVAIL / 'control' / 'control.c').write_text('int cc2x_control(void) { return 0; }\n', encoding='ascii')
    version = subprocess.run([sys.executable, '-m', 'ziglang', 'version'], capture_output=True, text=True).stdout.strip()
    print('\ncompilation (Zig', version + ')')
    c.zig(['-shared', TRAVAIL / 'control' / 'control.c', '-o', TRAVAIL / 'control' / 'control.dll'])
    c.nettoyer(TRAVAIL / 'control')
    for sortie in ('dist', 'dist_verif'):
        out = TRAVAIL / sortie
        c.zig(['-shared', '-I', src / 'include', src / 'plugin' / 'cc2x_modes.c', '-o', out / 'cc2x_modes.dll'])
        c.nettoyer(out)
    a, s, ok = c.controler(TRAVAIL / 'dist' / 'cc2x_modes.dll', 'cc2x_modes.dll')
    det = c.egal_hors_horodatage(TRAVAIL / 'dist' / 'cc2x_modes.dll', TRAVAIL / 'dist_verif' / 'cc2x_modes.dll')
    print(f'  deuxieme compilation identique (hors horodatage PE et identifiant de build) : {"oui" if det else "NON"}')
    tout_ok = ok and det
    L = ['# Rapport de compilation du plugin cc2x_modes.dll — genere par `construire_modes.py`', '',
         f'Commit du SDK : `{c.COMMIT}`. Compilateur : Zig {version}. Dossier de travail (hors depot, hors jeu) : `{TRAVAIL}`. '
         '**La DLL n\'a pas ete chargee ni lancee, rien n\'a ete copie dans le jeu.**', '',
         f'- taille {a["taille"]} octets, sha256 `{a["sha"].upper()}`',
         f'- deuxieme compilation identique, hors horodatage PE et identifiant de build : {"oui" if det else "NON"}',
         f'- PE32 i386 DLL : {a["machine"] == 0x14c and a["pe32"] and a["dll"]} ; TLS : '
         f'{"present, callbacks identiques a ceux d une DLL vide (code du compilateur)" if a.get("tls_ok") else ("present, A EXAMINER" if a["tls"] else "absent")} ; '
         f'imports retardes : {"presents" if a["delay"] else "absents"} ; exports : {", ".join(a["exports"])}',
         f'- chaines suspectes : {"aucune" if not s else s}', f'- verdict automatique : {"OK" if ok else "A EXAMINER"}', '',
         '| DLL importee | fonctions |', '|---|---|']
    for dll, fns in a['imports'].items():
        L.append(f'| {dll} | {", ".join(fns)} |')
    RAPPORT.write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('\nrapport ecrit :', RAPPORT)
    print('\ncompilation du banc d\'essai (UBSan, -Werror)')
    test = TRAVAIL / 'test' / 'test_modes.exe'
    c.zig(['-fsanitize=undefined', '-Werror', '-I', src / 'include', src / 'plugin' / 'tests' / 'test_modes.c', '-o', test])
    c.nettoyer(TRAVAIL / 'test')
    if lancer:
        print('\nlancement du banc d\'essai (programme 32 bits ecrit par nous ; il ne charge aucune DLL du SDK ; ecrit seulement dans', TRAVAIL / 'reglages', ')')
        r = subprocess.run([str(test), str(TRAVAIL / 'reglages')], cwd=TRAVAIL / 'test')
        tout_ok = tout_ok and r.returncode == 0
    print('\nRESULTAT :', 'tout est conforme' if tout_ok else 'A EXAMINER (voir ci-dessus)')
    sys.exit(0 if tout_ok else 1)


if __name__ == '__main__':
    main()
