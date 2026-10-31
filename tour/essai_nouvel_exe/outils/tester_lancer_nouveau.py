#!/usr/bin/env python3
"""Essais de lancer_nouveau.py sur des FAUX dossiers de jeu (C:\\Users\\UTILISATEUR\\Documents\\cc2-port-travail\\faux_nouveau_*).

Ne touche ni au vrai jeu, ni a Steam, et ne LANCE AUCUN jeu : la ligne de commande n'est utilisee qu'avec `--a-blanc` ou pour des
refus ; le chemin « lancer pour de vrai » est teste en memoire avec subprocess.Popen REMPLACE par un faux qui n'ouvre aucun programme.
Lancer : python -I -B tester_lancer_nouveau.py
"""
import contextlib
import hashlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

ICI = Path(__file__).resolve().parent
LANCER = ICI / 'lancer_nouveau.py'
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-port-travail')
SDK_TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-travail')
NEUF = TRAVAIL / 'carrier_command_nouveau_steam_461E1262.exe'
ANCIEN = TRAVAIL / 'carrier_command_ancien_original_1C9A01C3.exe'
DEUX_MODULES = TRAVAIL / 'carrier_command_nouveau_patche_ascenseur_temps.exe'
NOM = 'carrier_command_nouveau_5AF41B4D.exe'
SHA_COPIE = '5AF41B4D78CF18EB25C2F227397EAAA2F0E6443E65D2E9A142CC5043F45CC345'
pass_, fail = 0, 0

spec = importlib.util.spec_from_file_location('lancer_nouveau_sous_test', LANCER)
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def check(cond, msg):
    global pass_, fail
    if cond:
        pass_ += 1
    else:
        fail += 1
        print('  ECHEC :', msg)


def faux(nom, sous='', exe=NEUF):
    d = TRAVAIL / nom
    assert d.parent == TRAVAIL and nom.startswith('faux_nouveau_'), d      # on ne supprime que nos faux dossiers
    if d.exists():
        shutil.rmtree(d)
    jeu = d / sous / 'jeu' if sous else d / 'jeu'
    jeu.mkdir(parents=True)
    shutil.copyfile(exe, jeu / 'carrier_command.exe')               # le faux « exe de Steam » : le vrai build 461E1262...
    return jeu


def dll(jeu):
    """31/10 : les versions epinglees : le SDK a DEUX profils (E1DE25D5...) et le frein v12 (941DFFB9...)."""
    shutil.copyfile(TRAVAIL / 'sdk' / 'dist' / 'dinput8.dll', jeu / 'dinput8.dll')
    shutil.copyfile(SDK_TRAVAIL / 'dist' / 'cc2x_frein.dll', jeu / 'cc2x_frein.dll')


def cli(cmd, jeu, *extra, ouvert=False, steam=True):
    env = dict(os.environ)
    env['POSER_SIMULER_JEU_OUVERT'] = '1' if ouvert else '0'
    env['LANCER_SIMULER_STEAM'] = '1' if steam else '0'
    r = subprocess.run([sys.executable, '-I', '-B', str(LANCER), cmd, '--jeu', str(jeu), *extra], capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def appel(fonction, *a, **kw):
    """Appelle une fonction de lancer_nouveau en memoire ; -> (code, sortie). code 1 = refus (SystemExit)."""
    tampon = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(tampon):
        try:
            fonction(*a, **kw)
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
    return code, tampon.getvalue()


def args(jeu, a_blanc=False, vrai=False):
    return types.SimpleNamespace(jeu=str(jeu), a_blanc=a_blanc, cest_le_vrai_jeu=vrai)


def main():
    print('0. la source et ses garde-fous (en memoire)')
    octets = L.SOURCE.read_bytes()
    check(sha(L.SOURCE) == SHA_COPIE, 'la copie source a bien le sha256 5AF41B4D...')
    c, o = appel(L.composition_ok, octets)
    check(c == 0, 'la bonne copie passe la verification de composition\n' + o)
    for nom, chemin in (('le build de Steam sans patch', NEUF), ('la copie a DEUX modules (6072A2FD...)', DEUX_MODULES), ('l\'ANCIEN original', ANCIEN)):
        c, o = appel(L.composition_ok, Path(chemin).read_bytes())
        check(c == 1 and 'REFUS' in o, f'{nom} doit etre refuse\n' + o)
    tous = bytearray(octets)
    import json
    for nom in ('atterrissage_cercle',):                                   # un 4e module actif
        m = json.load(open(L.TOUR / 'outils' / 'modules_exe_461E1262' / f'{nom}.json', encoding='utf-8'))
        for ch in m['changements']:
            tous[ch['offset']:ch['offset'] + 4] = bytes.fromhex(ch['apres'])
    c, o = appel(L.composition_ok, bytes(tous))
    check(c == 1 and 'REFUS' in o, 'un 4e module actif doit etre refuse\n' + o)
    abime = bytearray(octets)
    abime[0x2000] ^= 0xFF
    c, o = appel(L.composition_ok, bytes(abime))
    check(c == 1 and 'REFUS' in o, 'un octet modifie hors des modules doit etre refuse\n' + o)

    print('1. etat, copie a blanc, copie, copie redondante')
    jeu = faux('faux_nouveau_1')
    steam_avant = sha(jeu / 'carrier_command.exe')
    c, o = cli('etat', jeu)
    check(c == 0 and 'build de Steam attendu' in o and 'absente' in o, 'etat initial\n' + o)
    c, o = cli('copier', jeu, '--a-blanc')
    check(c == 0 and 'A BLANC' in o and not (jeu / NOM).exists(), 'a blanc ne doit rien ecrire\n' + o)
    c, o = cli('copier', jeu)
    check(c == 0 and 'COPIE TERMINEE' in o, 'copie\n' + o)
    check(sha(jeu / NOM) == SHA_COPIE, 'sha de la copie')
    check(sha(jeu / 'carrier_command.exe') == steam_avant, "l'exe de Steam n'est pas touche")
    check(sorted(p.name for p in jeu.iterdir()) == sorted(['carrier_command.exe', NOM]), 'un seul fichier ajoute, pas de temporaire')
    c, o = cli('copier', jeu)
    check(c == 0 and 'Deja en place' in o, 'copie redondante\n' + o)
    c, o = cli('etat', jeu)
    check(c == 0 and f'{NOM} : bonne' in o, 'etat apres copie\n' + o)

    print('2. refus : jeu ouvert, fichier existant different, exe de Steam change')
    jeu = faux('faux_nouveau_2')
    c, o = cli('copier', jeu, ouvert=True)
    check(c == 1 and 'REFUS' in o and not (jeu / NOM).exists(), 'jeu ouvert : rien copie\n' + o)
    (jeu / NOM).write_bytes(b'autre chose')
    c, o = cli('copier', jeu)
    check(c == 1 and 'REFUS' in o and (jeu / NOM).read_bytes() == b'autre chose', 'fichier existant different : jamais remplace\n' + o)
    c, o = cli('retirer', jeu)
    check(c == 1 and 'REFUS' in o and (jeu / NOM).exists(), "retirer refuse un fichier qui n'est pas la bonne copie\n" + o)
    jeu = faux('faux_nouveau_2b', exe=ANCIEN)
    c, o = cli('copier', jeu)
    check(c == 1 and '461E1262' in o and not (jeu / NOM).exists(), "carrier_command.exe n'est pas le build de Steam attendu : rien copie\n" + o)

    print('3. lancer (a blanc) : chaque garde-fou')
    jeu = faux('faux_nouveau_3')
    c, o = cli('lancer', jeu, '--a-blanc')
    check(c == 1 and 'faire `copier`' in o, 'copie absente\n' + o)
    cli('copier', jeu)
    c, o = cli('lancer', jeu, '--a-blanc')
    check(c == 1 and 'dinput8.dll absent' in o, 'sans SDK\n' + o)
    dll(jeu)
    c, o = cli('lancer', jeu, '--a-blanc')
    check(c == 1 and 'steam_appid.txt' in o, 'sans steam_appid.txt\n' + o)
    (jeu / 'steam_appid.txt').write_text('1489630')
    c, o = cli('lancer', jeu, '--a-blanc', ouvert=True)
    check(c == 1 and 'tourne' in o, 'jeu ouvert\n' + o)
    c, o = cli('lancer', jeu, '--a-blanc', steam=False)
    check(c == 1 and 'Steam' in o, 'Steam ferme\n' + o)
    c, o = cli('lancer', jeu, '--a-blanc')
    check(c == 0 and 'A BLANC : rien lance' in o, 'tout en regle : a blanc\n' + o)
    check(not (jeu / 'cc2x.log').exists(), 'a blanc : aucun jeu lance (pas de journal)')
    shutil.copyfile(SDK_TRAVAIL / 'dist_v10' / 'dinput8.dll', jeu / 'cc2x_frein.dll')
    c, o = cli('lancer', jeu, '--a-blanc')
    check(c == 1 and 'cc2x_frein.dll' in o, 'plugin pas dans la version epinglee\n' + o)
    dll(jeu)
    shutil.copyfile(SDK_TRAVAIL / 'dist' / 'dinput8.dll', jeu / 'dinput8.dll')                      # 31/10 : le SDK a UN profil (184B144D...) est refuse
    c, o = cli('lancer', jeu, '--a-blanc')
    check(c == 1 and 'dinput8.dll' in o and 'poser_sdk.py' in o, 'le SDK a un profil (resterait inactif) est refuse\n' + o)
    dll(jeu)
    shutil.copyfile(SDK_TRAVAIL / 'dist_v10' / 'cc2x_frein.dll', jeu / 'cc2x_frein.dll')            # 31/10 : seule la v12 connait ce build
    c, o = cli('lancer', jeu, '--a-blanc')
    check(c == 1 and 'cc2x_frein.dll' in o, 'le frein v10 (ne connait pas ce build) est refuse\n' + o)
    dll(jeu)
    with open(jeu / NOM, 'ab') as f:
        f.write(b'\0')
    c, o = cli('lancer', jeu, '--a-blanc')
    check(c == 1 and 'modifie' in o, 'copie modifiee\n' + o)
    (jeu / NOM).unlink()
    cli('copier', jeu)
    b = bytearray((jeu / 'carrier_command.exe').read_bytes())
    b[0x2000] ^= 0xFF
    (jeu / 'carrier_command.exe').write_bytes(bytes(b))
    c, o = cli('lancer', jeu, '--a-blanc')
    check(c == 1 and '461E1262' in o, "l'exe de Steam a change : rien n'est lance\n" + o)

    print('4. lancer « pour de vrai » EN MEMOIRE (Popen remplace : aucun programme n\'est ouvert) et bilan du journal')
    jeu = faux('faux_nouveau_4')
    cli('copier', jeu)
    dll(jeu)
    (jeu / 'steam_appid.txt').write_text('1489630')
    lancements = []

    def ecrire_journal(texte):
        log = jeu / 'cc2x.log'
        avant = log.stat().st_mtime if log.exists() else 0
        log.write_text(texte)
        os.utime(log, (avant + 10, avant + 10))                     # la date doit changer, quelle que soit la finesse de l'horloge

    BON = '\r\n'.join([
        '11:00:00.000 [cc2x] info: CC2X 0.5.0 ready for Carrier Command 2 1.5.18-win32-6ae228f3',
        '11:00:00.010 [modes] info: loaded v3.1; ini x; observe only unless enabled=1',
        '11:00:00.010 [cc2x] info: plugin cc2x_modes.dll loaded (mod "Modes CC2")',
        "11:00:00.020 [hold] info: nouvel exe Steam 461E1262 (jamais essaye) : crochets poses en 0x6fce72 et 0x6fda4c ; une copie enclenchee du bouton Hold retient les avions comme l'original",
        "11:00:00.020 [hold] info: nouvel exe Steam 461E1262 (jamais essaye) : synchronisation posee en 0x7061f0 : l'original et ses copies prennent le meme etat, ecran des joueurs compris",
        '11:00:00.020 [cc2x] info: plugin cc2x_hold.dll loaded (mod "Hold copies")',
        '11:00:00.020 [cc2x] info: 5 enabled mod folder(s) checked for plugins',
        '11:00:00.030 [frein] info: recall_force=1: hooks H1 (0x7019de), H2 (0x701b4d), H3 (0x6ff20b, read only), 4 commit-gate probes (read only), '
        'H5 (0x6fe580, sends the aircraft to the touch test 0x6ff31a) and the take-over probe (0x6ff489, read only) installed, inactive until an aircraft is flagged',
        '11:00:00.030 [frein] info: loaded (frein v12, build 1.5.18-win32-6ae228f3, exe 0x6ae228f3); ini x; brake off unless brake_enabled=1',
        '11:00:00.030 [cc2x] info: plugin cc2x_frein.dll loaded (the game folder)', ''])
    journal = [BON]

    def faux_popen(commande, **kw):
        lancements.append((commande, kw.get('cwd')))
        ecrire_journal(journal[0])
        return types.SimpleNamespace()

    vrai_popen, vrai_sleep, vrai_pid, vrai_ouvert, vrai_steam = subprocess.Popen, L.time.sleep, L.pid_de_la_copie, L.jeu_ouvert, L.steam_tourne
    try:
        subprocess.Popen = faux_popen
        L.time.sleep = lambda s: None
        L.pid_de_la_copie = lambda: '1234'
        L.jeu_ouvert = lambda j: False
        L.steam_tourne = lambda j: True
        c, o = appel(L.cmd_lancer, args(jeu))
        check(c == 0 and len(lancements) == 1 and lancements[0][0] == [str(jeu / NOM)] and lancements[0][1] == str(jeu),
              'lance exactement la copie, depuis le dossier du jeu, jamais carrier_command.exe\n' + o)
        check('OK : SDK actif' in o and 'PAS OK' not in o and 'PID 1234' in o, 'journal complet = OK\n' + o)
        for nom, texte, attendu in (
                ('SDK inactif', '11:00:00.000 [cc2x] warn: unsupported game build (PE timestamp 0x6ae228f3, size 0x00af7000): CC2X stays inactive\r\n', 'PROBLEME'),
                ('octets inattendus', BON.replace('[cc2x] info: plugin cc2x_frein.dll loaded', '[cc2x] error: unexpected original bytes at 0x007019de (game build differs?)\r\n'
                                                  '11:00:00.040 [cc2x] info: plugin cc2x_frein.dll loaded'), 'unexpected original bytes'),
                ('crochets du frein refuses', BON.replace('installed, inactive until', 'X') + '11:00:00.050 [frein] error: recall_force=1 but the hooks could NOT be installed\r\n', 'could NOT'),
                ('Hold absent', BON.replace('plugin cc2x_hold.dll loaded', 'plugin autre'), 'plugin Hold charge'),
                ('frein de l\'ancien build', BON.replace('build 1.5.18-win32-6ae228f3, exe 0x6ae228f3', 'build 1.5.18-win32, exe 0x6a36c177'), 'frein v12 sur le nouvel exe'),
                ('synchronisation du Hold absente', BON.replace('synchronisation posee en 0x7061f0', 'synchronisation NON installee (le code du jeu differe en 0x007061f0)'), 'synchronisation NON installee'),
                ('Lua absent', BON.replace('1.5.18-win32-6ae228f3\r\n', '1.5.18-win32-6ae228f3 (no Lua bridge)\r\n', 1), 'no Lua bridge')):
            journal[0] = texte
            (jeu / 'cc2x.log').write_text('')
            c, o = appel(L.cmd_lancer, args(jeu))
            check('PAS OK' in o and attendu in o, f'journal « {nom} » = PAS OK, avec la raison\n' + o)
        journal[0] = BON
        ok, manque, mauvais = L.bilan_journal(BON.splitlines())
        check(ok and not manque and not mauvais, 'bilan_journal : le journal attendu passe')
        L.pid_de_la_copie = lambda: None
        subprocess.Popen = faux_popen
        c, o = appel(L.cmd_lancer, args(jeu))
        check('ABSENT' in o, 'si le processus n\'existe plus, c\'est dit\n' + o)
    finally:
        subprocess.Popen, L.time.sleep, L.pid_de_la_copie, L.jeu_ouvert, L.steam_tourne = vrai_popen, vrai_sleep, vrai_pid, vrai_ouvert, vrai_steam
    check(subprocess.Popen is vrai_popen, 'Popen est remis en place')

    print('5. retirer')
    jeu = faux('faux_nouveau_5')
    steam_avant = sha(jeu / 'carrier_command.exe')
    c, o = cli('retirer', jeu)
    check(c == 0 and 'Rien a retirer' in o, 'rien a retirer\n' + o)
    cli('copier', jeu)
    c, o = cli('retirer', jeu, ouvert=True)
    check(c == 1 and (jeu / NOM).exists(), 'jeu ouvert : pas de suppression\n' + o)
    c, o = cli('retirer', jeu, '--a-blanc')
    check(c == 0 and (jeu / NOM).exists(), 'a blanc : pas de suppression\n' + o)
    c, o = cli('retirer', jeu)
    check(c == 0 and 'RETRAIT TERMINE' in o and not (jeu / NOM).exists(), 'retrait\n' + o)
    check(sha(jeu / 'carrier_command.exe') == steam_avant, "l'exe de Steam n'est pas touche")

    print('6. chemin « steamapps » : --cest-le-vrai-jeu obligatoire')
    jeu = faux('faux_nouveau_6', 'steamapps')
    c, o = cli('copier', jeu)
    check(c == 1 and 'VRAI jeu' in o and not (jeu / NOM).exists(), 'refus sans le drapeau\n' + o)
    c, o = cli('copier', jeu, '--cest-le-vrai-jeu')
    check(c == 0 and (jeu / NOM).exists(), 'ok avec le drapeau\n' + o)

    print('7. options inconnues et aucun jeu par defaut')
    r = subprocess.run([sys.executable, '-I', '-B', str(LANCER), 'copier'], capture_output=True, text=True)
    check(r.returncode == 2, 'sans --jeu : refus (aucun dossier par defaut)')
    r = subprocess.run([sys.executable, '-I', '-B', str(LANCER), 'copier', '--jeu', str(jeu), '--option-inconnue'], capture_output=True, text=True)
    check(r.returncode == 2, 'option inconnue : refus')

    for p in TRAVAIL.glob('faux_nouveau_*'):
        shutil.rmtree(p, ignore_errors=True)
    print(f'\n{pass_} controles reussis, {fail} echec(s)')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
