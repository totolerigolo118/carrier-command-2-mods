#!/usr/bin/env python3
"""Copie le NOUVEL executable de Steam PATCHE (ascenseur_x2 + temps_x2 + pont_retour_x2) a cote du vrai et le lance directement.

  python -I -B lancer_nouveau.py etat    --jeu DOSSIER_DU_JEU
  python -I -B lancer_nouveau.py copier  --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]
  python -I -B lancer_nouveau.py lancer  --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]
  python -I -B lancer_nouveau.py retirer --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]

Pourquoi : la mise a jour Steam du 28/10/2026 a remplace carrier_command.exe (horodatage PE 0x6ae228f3, sha256 461E1262...). On
ne le patche JAMAIS en place (Steam le reecrit) : on copie, a cote, une copie patchee sous un NOUVEAU nom, et on la lance
directement. Fait sur le modele de tour/atterrissage_manuel/frein/lancer_ancien.py (memes garde-fous). Voir
tour/etude_port_nouvel_exe/RAPPORT.md et premier_essai/PROCEDURE_premier_essai_nouvel_exe.md (worktree port-nouvel-exe).
31/10 : COPIE adaptee pour l'essai avec le SDK a deux profils (tour/essai_nouvel_exe) : poser.py est celui de ce dossier.

Securites :
  - la copie source (C:\\Users\\UTILISATEUR\\Documents\\cc2-port-travail\\carrier_command_nouveau_patche_ascenseur_temps_pont.exe) est
    verifiee par son sha256 epingle (5AF41B4D...), par son horodatage PE ET par patch_exe.py : profil « build de Steam »,
    exactement les modules ascenseur_x2, temps_x2 et pont_retour_x2 actifs, aucun autre octet different de 461E1262... ;
  - elle est ecrite sous un NOUVEAU nom (carrier_command_nouveau_5AF41B4D.exe), jamais par-dessus un autre fichier ;
  - carrier_command.exe (celui de Steam) n'est JAMAIS ouvert en ecriture ni supprime ; il doit etre exactement 461E1262... ;
  - rien n'est copie ni supprime ni lance si un processus carrier_command* tourne depuis ce dossier (ou si on ne sait pas) ;
  - `lancer` refuse si Steam n'est pas ouvert, si steam_appid.txt manque, si dinput8.dll ou cc2x_frein.dll n'ont pas
    EXACTEMENT les sha256 epingles par poser.py (31/10 : le SDK A DEUX PROFILS E1DE25D5... et le frein v15 238B0456...), ou si la
    copie a ete changee ; il lance l'exe directement (pas par Steam), puis lit cc2x.log (bilan_journal) : le SDK doit etre ACTIF
    (« ready for ... 1.5.18-win32-6ae228f3 ») et charger modes, Hold et frein v15 avec ses 9 crochets du nouvel exe (10 avec heli_recall=1) ;
  - `retirer` ne supprime la copie que si son sha256 est exactement le bon ;
  - sur un chemin « steamapps » il faut --cest-le-vrai-jeu. Python standard seulement, aucun reseau. Aucune DLL n'est posee ici.
"""
import argparse
import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

ICI = Path(__file__).resolve().parent
TOUR = ICI.parents[1]
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-port-travail')          # ici seulement : copie source, faux dossiers d'essai
SOURCE = TRAVAIL / 'carrier_command_nouveau_patche_ascenseur_temps_pont.exe'
NOM = 'carrier_command_nouveau_5AF41B4D.exe'
SHA_COPIE = '5AF41B4D78CF18EB25C2F227397EAAA2F0E6443E65D2E9A142CC5043F45CC345'
SHA_STEAM = '461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A'
PE_NOUVEAU = (0x6ae228f3, 0x00af7000)
MODULES_ATTENDUS = {'ascenseur_x2', 'temps_x2', 'pont_retour_x2'}


def _charger(nom, chemin):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


P = _charger('poser', ICI / 'poser.py')                                       # copie du 31/10 : SDK a deux profils E1DE25D5..., frein v15
PE = _charger('patch_exe', TOUR / 'outils' / 'patch_exe.py')                  # profils, modules, coherence : une seule source de verite


def composition_ok(octets):
    """Refuse (sortie) sauf si `octets` = exe de Steam 461E1262... + EXACTEMENT ascenseur_x2, temps_x2 et pont_retour_x2."""
    prof = PE.profil_de(octets)
    if prof is None or prof['sha256_origine'] != SHA_STEAM:
        P.refus("patch_exe.py ne reconnait pas ce fichier comme le build de Steam du 28/10 (461E1262...)")
    mods, sha_o = PE.charger_tous(prof)
    PE.PROFIL_COURANT[0] = prof
    ok, msg = PE.coherence_globale(octets, mods, sha_o)
    if not ok:
        P.refus('la copie differe du build de Steam ailleurs que sur nos modules : ' + msg)
    etats = {n: PE.etat_module(octets, m, mods, sha_o)[0] for n, m in mods.items()}
    actifs = {n for n, e in etats.items() if e == 'patche'}
    autres = {n: e for n, e in etats.items() if n not in actifs and e != 'original'}
    if actifs != MODULES_ATTENDUS or autres:
        P.refus(f'modules actifs {sorted(actifs)} au lieu de {sorted(MODULES_ATTENDUS)} (etats : {etats})')


def source_ok():
    if not SOURCE.is_file():
        P.refus(f'copie patchee introuvable : {SOURCE}')
    octets = SOURCE.read_bytes()
    if P.sha(octets) != SHA_COPIE:
        P.refus(f'la copie patchee ne porte pas le sha256 attendu ({SHA_COPIE[:8]}...) : on ne copie pas')
    if P.pe_de(SOURCE) != PE_NOUVEAU:
        P.refus("la copie patchee n'a pas l'horodatage PE du build de Steam (0x6ae228f3)")
    composition_ok(octets)
    return octets


def preparer(args):
    jeu = Path(args.jeu)
    if not jeu.is_dir():
        P.refus(f"{jeu} n'est pas un dossier")
    if 'steamapps' in os.path.abspath(jeu).lower() and not args.cest_le_vrai_jeu:
        P.refus("ce chemin ressemble au VRAI jeu (steamapps). Ajouter --cest-le-vrai-jeu pour confirmer que c'est voulu.")
    return jeu


def jeu_ouvert(jeu):
    """True / False ; None si on ne sait pas (a traiter comme « ouvert »). Simulation reservee aux faux dossiers de cc2-port-travail."""
    sim = os.environ.get('POSER_SIMULER_JEU_OUVERT')
    if sim and P.dans(jeu, TRAVAIL):
        return sim == '1'
    cmd = ('Get-Process -Name carrier_command* -ErrorAction SilentlyContinue | '
           'ForEach-Object { if ($_.Path) { $_.Path } else { "?" } }')
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', cmd],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None
    chemins = [l.strip() for l in out.splitlines() if l.strip()]
    return any(c == '?' or P.dans(c, jeu) for c in chemins)


def jeu_ferme(jeu):
    o = jeu_ouvert(jeu)
    if o is None:
        P.refus("impossible de savoir si le jeu tourne : par prudence, rien n'est fait")
    if o:
        P.refus("un processus carrier_command* tourne depuis ce dossier : le fermer d'abord")


def steam_tourne(jeu):
    sim = os.environ.get('LANCER_SIMULER_STEAM')
    if sim and P.dans(jeu, TRAVAIL):
        return sim == '1'
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command',
                              'Get-Process -Name steam -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Id'],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None
    return bool(out.strip())


def pid_de_la_copie():
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command',
                              f'Get-Process -Name {Path(NOM).stem} -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Id'],
                             capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return None
    return out or None


def exe_steam_ok(jeu):
    exe = Path(jeu) / 'carrier_command.exe'
    if not exe.is_file():
        P.refus('carrier_command.exe absent du dossier')
    if P.sha(exe.read_bytes()) != SHA_STEAM:
        P.refus("carrier_command.exe n'est plus le build de Steam attendu (461E1262...) : Steam a-t-il fait une mise a jour ? "
                "La copie patchee ne correspond peut-etre plus. Rien n'est fait.")


def etat_copie(jeu):
    c = Path(jeu) / NOM
    if not c.is_file():
        return 'absente'
    return 'bonne' if P.sha(c.read_bytes()) == SHA_COPIE else 'AUTRE'


def cmd_etat(args):
    jeu = preparer(args)
    exe = jeu / 'carrier_command.exe'
    print('Dossier du jeu :', os.path.abspath(jeu))
    if exe.is_file():
        s, pe = P.sha(exe.read_bytes()), P.pe_de(exe)
        print(f'  carrier_command.exe : sha256 {s[:12]}..., horodatage PE {pe[0]:#x}',
              '(= build de Steam attendu 461E1262...)' if s == SHA_STEAM else '(AUTRE exe que le build de Steam attendu)')
    print(f'  {NOM} :', etat_copie(jeu))
    print(f'  copie source ({SOURCE.name}) :', 'presente' if SOURCE.is_file() else 'ABSENTE')
    for nom, attendu in P.SHA.items():
        f = jeu / nom
        s = P.sha(f.read_bytes()) if f.is_file() else None
        print(f'  {nom} :', 'absent' if s is None else ('version attendue' if s == attendu else (
            'ancienne version de chez nous' if s in P.SHA_ANCIENNES.get(nom, ()) else 'AUTRE version')))
    print('  steam_appid.txt :', 'present' if (jeu / 'steam_appid.txt').is_file() else 'ABSENT')
    print('  jeu lance :', {True: 'OUI', False: 'non', None: 'inconnu'}[jeu_ouvert(jeu)])
    print('  Steam ouvert :', {True: 'oui', False: 'NON', None: 'inconnu'}[steam_tourne(jeu)])


def cmd_copier(args):
    jeu = preparer(args)
    octets = source_ok()
    exe_steam_ok(jeu)
    jeu_ferme(jeu)
    cible = jeu / NOM
    if cible.exists():
        if cible.is_file() and P.sha(cible.read_bytes()) == SHA_COPIE:
            print('Deja en place, rien a faire :', cible)
            return
        P.refus(f'{cible} existe deja avec un autre contenu : on ne remplace jamais un fichier existant')
    print(f'Copie : {SOURCE.name} -> {cible} ({len(octets)} octets, sha256 verifie avant et apres)')
    if args.a_blanc:
        print('A BLANC : rien ecrit.')
        return
    P.ecrire(cible, octets, SHA_COPIE)
    print("COPIE TERMINEE. carrier_command.exe (Steam) n'a pas ete touche.")


def cmd_lancer(args):
    jeu = preparer(args)
    cible = jeu / NOM
    if etat_copie(jeu) != 'bonne':
        P.refus(f"{NOM} absent ou modifie : faire `copier` d'abord")
    if P.pe_de(cible) != PE_NOUVEAU:
        P.refus("la copie n'a pas l'horodatage PE du build de Steam")
    composition_ok(cible.read_bytes())
    exe_steam_ok(jeu)
    for nom, attendu in P.SHA.items():
        f = jeu / nom
        if not f.is_file() or P.sha(f.read_bytes()) != attendu:       # 31/10 : EXACTEMENT le SDK a deux profils et le frein v15 (les seuls qui
            P.refus(f"{nom} absent ou pas la version epinglee par poser.py ({attendu[:8]}...) : rien n'est lance"   # connaissent ce build)
                    + (" (le SDK a un profil resterait inactif : poser_sdk.py poser d'abord)" if nom == 'dinput8.dll' else ''))
    if not (jeu / 'steam_appid.txt').is_file():
        P.refus('steam_appid.txt absent : un lancement direct echouerait')
    # 02/11 : le SDK charge toute DLL cc2x du jeu et des mods actifs ; on ne lance que si ce sont exactement nos plugins connus
    appdata = os.environ.get('APPDATA')
    etrangers = [str(f) for f in jeu.glob('cc2x_*.dll') if f.name.lower() != 'cc2x_frein.dll']
    etrangers += [str(p) for p in (jeu / 'cc2x' / 'plugins', jeu / 'cc2x.ini') if p.exists()]
    etrangers += P.mods_cc2x_inconnus(P.mods_avec_cc2x(appdata)) if appdata else ['%APPDATA% introuvable : mods non verifies']
    if etrangers:
        P.refus('le SDK chargerait du code que nous ne connaissons pas : ' + ' ; '.join(etrangers) + " : rien n'est lance")
    jeu_ferme(jeu)
    if not steam_tourne(jeu):
        P.refus("Steam ne semble pas ouvert (ou on ne sait pas) : l'ouvrir d'abord")
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
            if any('stays inactive' in l or 'plugin cc2x_frein.dll' in l for l in lignes):     # le frein (dossier du jeu) est charge en dernier
                break
    for l in [l for l in lignes if any(k in l for k in CLES_A_MONTRER)][:16]:
        print('  cc2x.log :', l)
    pid = pid_de_la_copie()
    print('  processus de la copie :', f'PID {pid}' if pid else "ABSENT (le jeu s'est-il ferme tout seul ? plantage au demarrage ?)")
    ok, manque, mauvais = bilan_journal(lignes)
    for m in manque:
        print('  MANQUE  :', m)
    for m in mauvais:
        print('  PROBLEME:', m)
    if ok:
        print('OK : SDK actif sur le nouvel exe ; modes, Hold et frein v15 (9 crochets, + H6 si heli_recall=1) charges ; aucune ligne de refus.')
    else:
        print("PAS OK : relire cc2x.log avant tout essai (ne pas jouer tant que ce n'est pas compris).")


# Lignes de demarrage attendues avec le SDK a deux profils, la copie patchee du nouvel exe et frein.ini a recall_force=1 (31/10).
ATTENDUES = (
    ('SDK actif sur le nouvel exe', 'CC2X 0.5.0 ready for Carrier Command 2 1.5.18-win32-6ae228f3'),
    ('plugin modes charge', 'plugin cc2x_modes.dll loaded'),
    ('Hold : crochets du nouvel exe', 'nouvel exe Steam 461E1262 (jamais essaye) : crochets poses en 0x6fce72 et 0x6fda4c'),
    ('Hold v2 : synchronisation du nouvel exe', 'nouvel exe Steam 461E1262 (jamais essaye) : synchronisation posee en 0x7061f0'),
    ('plugin Hold charge', 'plugin cc2x_hold.dll loaded'),
    ('frein : 9 crochets du nouvel exe', 'recall_force=1: hooks H1 (0x7019de), H2 (0x701b4d), H3 (0x6ff20b, read only), 4 commit-gate probes '
     '(read only), H5 (0x6fe580, sends the aircraft to the touch test 0x6ff31a) and the take-over probe (0x6ff489, read only) installed'),
    ('frein v15 sur le nouvel exe', 'loaded (frein v15, build 1.5.18-win32-6ae228f3, exe 0x6ae228f3)'),
    ('plugin frein charge', 'plugin cc2x_frein.dll loaded'),
)
# Tout ce qui dit « refus » ou « erreur » au demarrage (SDK : cc2x.c ; frein ; Hold).
MAUVAISES = ('unexpected original bytes', 'already changed', 'core hooks failed', 'stays inactive', 'unsupported game build',
             'no Lua bridge', 'not registered', 'cannot load plugin', 'could NOT', 'not loaded', 'verification ratee',
             "rien n'est installe", 'exe inconnu', 'synchronisation NON installee', 'synchronisation arretee', '] error:')
CLES_A_MONTRER = ('ready for', 'plugin', 'inactive', 'unsupported', 'loaded', 'installed', 'crochets', 'could NOT', 'unexpected',
                  'error:', 'warn:')


def bilan_journal(lignes):
    """-> (ok, attendues manquantes, lignes mauvaises). ok = toutes les attendues et aucune mauvaise."""
    texte = '\n'.join(lignes)
    manque = [nom for nom, motif in ATTENDUES if motif not in texte]
    mauvais = [l for l in lignes if any(m in l for m in MAUVAISES)]
    return not manque and not mauvais, manque, mauvais


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
