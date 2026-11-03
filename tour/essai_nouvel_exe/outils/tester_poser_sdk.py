#!/usr/bin/env python3
"""Essais de poser_sdk.py sur des FAUX dossiers de jeu (C:\\Users\\UTILISATEUR\\Documents\\cc2-sdk-travail\\faux_sdk_*).

Ne touche ni au vrai jeu, ni au vrai %APPDATA%, et ne lance aucun jeu. Lancer : python -I -B tester_poser_sdk.py
Le faux exe est une copie de la sauvegarde de l'original (hors depot), jamais lancee. Le vrai cc2x_hold.dll est seulement lu.
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
OUTIL = ICI / 'poser_sdk.py'
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-travail')
ORIGINAL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\sauvegardes\carrier_command_1.5.18_original.exe')
UN = TRAVAIL / 'dist' / 'dinput8.dll'
DEUX = Path(r'C:\Users\UTILISATEUR\Documents\cc2-port-travail\sdk\dist\dinput8.dll')
FREIN = TRAVAIL.parent / 'cc2-sdk-travail-v15' / 'dist' / 'cc2x_frein.dll'      # 02/11 : le frein epingle (v15)
SHA_UN = '184B144D6E2BB868FFEB7D45ECD463F8919E64732E3B5681A16165363EBA0982'
SHA_DEUX = 'E1DE25D53A5588BDA62269D6D93335ACB9F32EA555AC9274FE7973C19D6225D7'
VRAI_HOLD = Path(os.environ['APPDATA']) / 'Carrier Command 2' / 'mods' / 'cc2_hold_copies' / 'content' / 'cc2x' / 'cc2x_hold.dll'
VRAI_MODES = Path(os.environ['APPDATA']) / 'Carrier Command 2' / 'mods' / 'cc2_modes' / 'content' / 'cc2x' / 'cc2x_modes.dll'
pass_, fail = 0, 0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def check(cond, msg):
    global pass_, fail
    if cond:
        pass_ += 1
    else:
        fail += 1
        print('  ECHEC :', msg)


def faux(nom, sdk=UN, frein=True):
    d = TRAVAIL / nom
    assert d.parent == TRAVAIL and nom.startswith('faux_sdk_'), d      # on ne supprime que nos faux dossiers
    if d.exists():
        shutil.rmtree(d)
    jeu, ad = d / 'jeu', d / 'appdata'
    jeu.mkdir(parents=True)
    (ad / 'Carrier Command 2').mkdir(parents=True)
    shutil.copyfile(ORIGINAL, jeu / 'carrier_command.exe')
    if sdk:
        shutil.copyfile(sdk, jeu / 'dinput8.dll')
    if frein:
        shutil.copyfile(FREIN, jeu / 'cc2x_frein.dll')
    return jeu, ad


def mod(ad, nom, fichiers):
    """Un faux mod actif avec un dossier content\\cc2x contenant `fichiers` {nom: octets}."""
    m = ad / 'mods' / nom
    (m / 'content' / 'cc2x').mkdir(parents=True)
    for n, o in fichiers.items():
        (m / 'content' / 'cc2x' / n).write_bytes(o)
    mx = ad / 'Carrier Command 2' / 'mods.xml'
    deja = mx.read_text() if mx.exists() else '<data><active_mod_folders></active_mod_folders></data>'
    mx.write_text(deja.replace('</active_mod_folders>', f'<path value="{m}"/></active_mod_folders>'))


def cli(cmd, jeu, ad, *extra, ouvert=False):
    env = dict(os.environ)
    env['POSER_SIMULER_JEU_OUVERT'] = '1' if ouvert else '0'
    r = subprocess.run([sys.executable, '-I', '-B', str(OUTIL), cmd, '--jeu', str(jeu), '--appdata', str(ad), *extra],
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def main():
    check(sha(UN) == SHA_UN and sha(DEUX) == SHA_DEUX, 'les deux DLL sources ont les sha256 attendus')

    print('1. etat, pose a blanc, pose, pose redondante, retour, retour redondant')
    jeu, ad = faux('faux_sdk_1')
    exe_avant, frein_avant = sha(jeu / 'carrier_command.exe'), sha(jeu / 'cc2x_frein.dll')
    c, o = cli('etat', jeu, ad)
    check(c == 0 and 'UN profil' in o and 'cc2x_frein.dll' in o and 'PROBLEME' not in o, 'etat initial\n' + o)
    c, o = cli('poser', jeu, ad, '--a-blanc')
    check(c == 0 and 'A BLANC' in o and sha(jeu / 'dinput8.dll') == SHA_UN, 'a blanc : rien ecrit\n' + o)
    c, o = cli('poser', jeu, ad)
    check(c == 0 and 'TERMINE' in o and sha(jeu / 'dinput8.dll') == SHA_DEUX, 'pose\n' + o)
    check(sha(jeu / 'carrier_command.exe') == exe_avant and sha(jeu / 'cc2x_frein.dll') == frein_avant, 'exe et plugin non touches')
    check(sorted(p.name for p in jeu.iterdir()) == ['carrier_command.exe', 'cc2x_frein.dll', 'dinput8.dll'], 'aucun fichier ajoute, pas de temporaire')
    c, o = cli('poser', jeu, ad)
    check(c == 0 and 'Deja en place' in o and sha(jeu / 'dinput8.dll') == SHA_DEUX, 'pose redondante\n' + o)
    c, o = cli('etat', jeu, ad)
    check(c == 0 and 'DEUX profils' in o, 'etat apres pose\n' + o)
    c, o = cli('revenir', jeu, ad, '--a-blanc')
    check(c == 0 and sha(jeu / 'dinput8.dll') == SHA_DEUX, 'retour a blanc : rien ecrit\n' + o)
    c, o = cli('revenir', jeu, ad)
    check(c == 0 and 'TERMINE' in o and sha(jeu / 'dinput8.dll') == SHA_UN, 'retour\n' + o)
    c, o = cli('revenir', jeu, ad)
    check(c == 0 and 'Deja en place' in o, 'retour redondant\n' + o)
    check(not list(jeu.glob('*.cc2_tmp')), 'pas de fichier temporaire')

    print('2. refus : jeu ouvert, dinput8.dll absente ou inconnue')
    jeu, ad = faux('faux_sdk_2')
    c, o = cli('poser', jeu, ad, ouvert=True)
    check(c == 1 and 'tourne' in o and sha(jeu / 'dinput8.dll') == SHA_UN, 'jeu ouvert : pas de pose\n' + o)
    cli('poser', jeu, ad)
    c, o = cli('revenir', jeu, ad, ouvert=True)
    check(c == 1 and sha(jeu / 'dinput8.dll') == SHA_DEUX, 'jeu ouvert : pas de retour\n' + o)
    jeu, ad = faux('faux_sdk_3', sdk=None)
    c, o = cli('poser', jeu, ad)
    check(c == 1 and 'REFUS' in o and not (jeu / 'dinput8.dll').exists(), 'sans dinput8.dll : rien pose (on ne fait que remplacer)\n' + o)
    (jeu / 'dinput8.dll').write_bytes(b'MZ autre')
    c, o = cli('poser', jeu, ad)
    check(c == 1 and (jeu / 'dinput8.dll').read_bytes() == b'MZ autre', 'dinput8.dll inconnue : jamais remplacee\n' + o)
    c, o = cli('revenir', jeu, ad)
    check(c == 1 and (jeu / 'dinput8.dll').read_bytes() == b'MZ autre', 'dinput8.dll inconnue : pas de retour non plus\n' + o)

    print('3. condition 2 du verdict : ce que le SDK chargerait')
    for nom, preparation, attendu in (
            ('faux_sdk_4', lambda j, a: (j / 'cc2x_autre.dll').write_bytes(b'MZ'), 'cc2x_autre.dll'),
            ('faux_sdk_5', lambda j, a: (j / 'cc2x.ini').write_text('[cc2x]\n'), 'cc2x.ini'),
            ('faux_sdk_6', lambda j, a: (j / 'cc2x' / 'plugins').mkdir(parents=True), 'plugins'),
            ('faux_sdk_7', lambda j, a: (j / 'cc2x_frein.dll').write_bytes(b'MZ frein inconnu'), 'cc2x_frein.dll'),
            ('faux_sdk_8', lambda j, a: mod(a, 'mod_inconnu', {'cc2x_mal.dll': b'MZ'}), 'cc2x_mal.dll'),
            ('faux_sdk_9', lambda j, a: mod(a, 'mod_faux_hold', {'cc2x_hold.dll': b'MZ pas le bon'}), 'cc2x_hold.dll')):
        jeu, ad = faux(nom)
        preparation(jeu, ad)
        c, o = cli('poser', jeu, ad)
        check(c == 1 and 'PROBLEME' in o and attendu in o and sha(jeu / 'dinput8.dll') == SHA_UN, f'{nom} : refus ({attendu})\n' + o)
    jeu, ad = faux('faux_sdk_10')
    if VRAI_HOLD.is_file() and VRAI_MODES.is_file():
        mod(ad, 'cc2_modes', {'cc2x_modes.dll': VRAI_MODES.read_bytes()})          # lecture seule des vrais plugins, copies dans le faux dossier
        mod(ad, 'cc2_hold_copies', {'cc2x_hold.dll': VRAI_HOLD.read_bytes()})
        connus = sha(VRAI_HOLD) in ('EE9043DA4773F8360C18BCFE2FF2554FA6A2ECE5D8DA675B96B0E98F2C7F3793', 'DDB0AB76ED2C8A20CA72E3609DFD61843D9FDA16ADE07B8A7064F54402D9DDA5', '4837B1B9FC26C3AA236A28564785BF6F74F2BC97D4C3150B54355AD90D89DF17')
        c, o = cli('poser', jeu, ad, '--a-blanc')
        if connus:
            check(c == 0 and 'cc2x_modes.dll' in o and 'cc2x_hold.dll' in o and 'PROBLEME' not in o, 'les vrais plugins modes et Hold sont connus et listes\n' + o)
        else:
            check(c == 1 and 'cc2x_hold.dll' in o, 'un cc2x_hold.dll a une autre empreinte (v2 ?) : refus, a relire\n' + o)
    else:
        print('  (vrais plugins absents : essai saute)')
    jeu, ad = faux('faux_sdk_11', frein=False)
    c, o = cli('poser', jeu, ad, '--a-blanc')
    check(c == 0 and 'aucun' in o, 'sans plugin : rien a charger, pose permise\n' + o)
    jeu, ad = faux('faux_sdk_12', sdk=DEUX)
    (jeu / 'cc2x_autre.dll').write_bytes(b'MZ')
    c, o = cli('revenir', jeu, ad)
    check(c == 0 and 'TERMINE' in o and sha(jeu / 'dinput8.dll') == SHA_UN, 'le retour arriere ne depend pas du controle du chargeur\n' + o)

    print('4. sources : modifiees ou absentes (en memoire)')
    spec = importlib.util.spec_from_file_location('poser_sdk_sous_test', OUTIL)
    S = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(S)
    jeu, ad = faux('faux_sdk_13')
    alteree = TRAVAIL / 'faux_sdk_13' / 'dinput8_alteree.dll'
    b = bytearray(DEUX.read_bytes()); b[500] ^= 1; alteree.write_bytes(bytes(b))
    for nom, nouvelle, ancienne in (('source a deux profils alteree', (alteree, SHA_DEUX), S.ANCIENNE),
                                    ('source a deux profils absente', (TRAVAIL / 'faux_sdk_13' / 'rien.dll', SHA_DEUX), S.ANCIENNE),
                                    ('copie de retour absente', S.NOUVELLE, (TRAVAIL / 'faux_sdk_13' / 'rien.dll', SHA_UN))):
        vraie_n, vraie_a, vrai_ouvert = S.NOUVELLE, S.ANCIENNE, S.P.jeu_ouvert
        tampon, code = io.StringIO(), 0
        try:
            S.NOUVELLE, S.ANCIENNE, S.P.jeu_ouvert = nouvelle, ancienne, (lambda j: False)
            with contextlib.redirect_stdout(tampon):
                try:
                    S.cmd_poser(types.SimpleNamespace(jeu=str(jeu), appdata=str(ad), a_blanc=False, cest_le_vrai_jeu=False))
                except SystemExit as e:
                    code = e.code if isinstance(e.code, int) else 1
        finally:
            S.NOUVELLE, S.ANCIENNE, S.P.jeu_ouvert = vraie_n, vraie_a, vrai_ouvert
        check(code == 1 and sha(jeu / 'dinput8.dll') == SHA_UN, f'{nom} : refus, rien ecrit\n' + tampon.getvalue())

    print('5. chemin « steamapps » et options')
    jeu, ad = faux('faux_sdk_14')
    sa = TRAVAIL / 'faux_sdk_14' / 'steamapps' / 'common' / 'CC2'
    sa.mkdir(parents=True)
    for f in jeu.iterdir():
        shutil.copyfile(f, sa / f.name)
    c, o = cli('poser', sa, ad)
    check(c == 1 and 'cest-le-vrai-jeu' in o and sha(sa / 'dinput8.dll') == SHA_UN, 'steamapps sans le drapeau : refus\n' + o)
    c, o = cli('poser', sa, ad, '--cest-le-vrai-jeu')
    check(c == 0 and sha(sa / 'dinput8.dll') == SHA_DEUX, 'steamapps avec le drapeau (faux dossier)\n' + o)
    r = subprocess.run([sys.executable, '-I', '-B', str(OUTIL), 'poser'], capture_output=True, text=True)
    check(r.returncode == 2, 'sans --jeu : refus (aucun dossier par defaut)')
    r = subprocess.run([sys.executable, '-I', '-B', str(OUTIL), 'poser', '--jeu', str(jeu), '--option-inconnue'], capture_output=True, text=True)
    check(r.returncode == 2, 'option inconnue : refus')

    for d in TRAVAIL.glob('faux_sdk_*'):
        shutil.rmtree(d, ignore_errors=True)
    print(f'\n{pass_} controles reussis, {fail} echec(s)')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
