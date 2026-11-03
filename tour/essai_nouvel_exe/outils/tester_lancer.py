#!/usr/bin/env python3
"""Essais de lancer_ancien.py sur des FAUX dossiers de jeu (dans C:\\Users\\UTILISATEUR\\Documents\\cc2-sdk-travail\\faux_*).

Ne touche ni au vrai jeu, ni a Steam, et ne LANCE aucun jeu (seulement des `--a-blanc` et des refus). Lancer : python -I tester_lancer.py
"""
import hashlib
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-travail')
LANCER = ICI / 'lancer_ancien.py'
SAUV = Path(r'C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\sauvegardes')      # 31/10 copie : les exe ne sont que dans le dossier principal
ORIGINAL = SAUV / 'carrier_command_1.5.18_original.exe'
NOM = 'carrier_command_ancien_8E7FCBB6.exe'
DIST = TRAVAIL / 'dist'
SDK2 = Path(r'C:\Users\UTILISATEUR\Documents\cc2-port-travail\sdk\dist')          # la DLL du SDK a deux profils (E1DE25D5...)
V13 = Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-travail-v15\dist')            # 02/11 : le frein epingle (v15), compile a part
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


def faux(nom, sous=''):
    d = TRAVAIL / nom
    assert d.parent == TRAVAIL and nom.startswith('faux_'), d      # on ne supprime que nos faux dossiers
    if d.exists():
        shutil.rmtree(d)
    jeu = d / sous / 'jeu' if sous else d / 'jeu'
    jeu.mkdir(parents=True)
    # faux « exe de Steam » : l'original avec un horodatage PE de nouveau build (0x6ae228f3)
    b = bytearray(ORIGINAL.read_bytes())
    nt = struct.unpack_from('<I', b, 0x3c)[0]
    struct.pack_into('<I', b, nt + 8, 0x6ae228f3)
    (jeu / 'carrier_command.exe').write_bytes(bytes(b))
    return jeu


def dll(jeu):
    shutil.copyfile(SDK2 / 'dinput8.dll', jeu / 'dinput8.dll')
    shutil.copyfile(V13 / 'cc2x_frein.dll', jeu / 'cc2x_frein.dll')


def lancer(cmd, jeu, *extra, ouvert=False, steam=True):
    env = dict(os.environ)
    env['POSER_SIMULER_JEU_OUVERT'] = '1' if ouvert else '0'
    env['LANCER_SIMULER_STEAM'] = '1' if steam else '0'
    r = subprocess.run([sys.executable, '-I', str(LANCER), cmd, '--jeu', str(jeu), *extra], capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def main():
    print('1. etat, copie a blanc, copie, copie redondante')
    jeu = faux('faux_lancer_1')
    main_avant = sha(jeu / 'carrier_command.exe')
    c, o = lancer('etat', jeu)
    check(c == 0 and "pas l'ancien exe" in o and 'absente' in o, 'etat initial\n' + o)
    c, o = lancer('copier', jeu, '--a-blanc')
    check(c == 0 and 'A BLANC' in o and not (jeu / NOM).exists(), 'a blanc ne doit rien ecrire\n' + o)
    c, o = lancer('copier', jeu)
    check(c == 0 and 'COPIE TERMINEE' in o, 'copie\n' + o)
    check(sha(jeu / NOM) == '8E7FCBB6CE27BD3D8FEB02BF7F3DBBA646CCE6D4944360570F082972E8DFE8BE', 'sha de la copie')
    check(sha(jeu / 'carrier_command.exe') == main_avant, "l'exe de Steam n'est pas touche")
    check(sorted(p.name for p in jeu.iterdir()) == sorted(['carrier_command.exe', NOM]), 'un seul fichier ajoute, pas de temporaire')
    c, o = lancer('copier', jeu)
    check(c == 0 and 'Deja en place' in o, 'copie redondante\n' + o)
    c, o = lancer('etat', jeu)
    check(c == 0 and f'{NOM} : bonne' in o, 'etat apres copie\n' + o)

    print('2. refus : jeu ouvert, fichier existant different')
    jeu = faux('faux_lancer_2')
    c, o = lancer('copier', jeu, ouvert=True)
    check(c == 1 and 'REFUS' in o and not (jeu / NOM).exists(), 'jeu ouvert : rien copie\n' + o)
    (jeu / NOM).write_bytes(b'autre chose')
    c, o = lancer('copier', jeu)
    check(c == 1 and 'REFUS' in o and (jeu / NOM).read_bytes() == b'autre chose', 'fichier existant different : jamais remplace\n' + o)
    c, o = lancer('retirer', jeu)
    check(c == 1 and 'REFUS' in o and (jeu / NOM).exists(), 'retirer refuse un fichier qui n\'est pas la bonne copie\n' + o)

    print('3. lancer (a blanc) : chaque garde-fou')
    jeu = faux('faux_lancer_3')
    c, o = lancer('lancer', jeu, '--a-blanc')
    check(c == 1 and 'faire `copier`' in o, 'copie absente\n' + o)
    lancer('copier', jeu)
    c, o = lancer('lancer', jeu, '--a-blanc')
    check(c == 1 and 'dinput8.dll absent' in o, 'sans SDK\n' + o)
    dll(jeu)
    c, o = lancer('lancer', jeu, '--a-blanc')
    check(c == 1 and 'steam_appid.txt' in o, 'sans steam_appid.txt\n' + o)
    (jeu / 'steam_appid.txt').write_text('1489630')
    c, o = lancer('lancer', jeu, '--a-blanc', ouvert=True)
    check(c == 1 and 'tourne' in o, 'jeu ouvert\n' + o)
    c, o = lancer('lancer', jeu, '--a-blanc', steam=False)
    check(c == 1 and 'Steam' in o, 'Steam ferme\n' + o)
    c, o = lancer('lancer', jeu, '--a-blanc')
    check(c == 0 and 'A BLANC : rien lance' in o, 'tout en regle : a blanc\n' + o)
    check(not (jeu / 'cc2x.log').exists(), 'a blanc : aucun jeu lance (pas de journal)')
    shutil.copyfile(DIST / 'dinput8.dll', jeu / 'cc2x_frein.dll')
    c, o = lancer('lancer', jeu, '--a-blanc')
    check(c == 1 and 'cc2x_frein.dll' in o, 'plugin pas dans la version epinglee\n' + o)
    dll(jeu)
    shutil.copyfile(TRAVAIL / 'dist_v6' / 'cc2x_frein.dll', jeu / 'cc2x_frein.dll')                 # la v6 (posee dans le vrai jeu) reste acceptee
    c, o = lancer('lancer', jeu, '--a-blanc')
    check(c == 0 and 'A BLANC : rien lance' in o, 'une ancienne compilation de chez nous (v6) est acceptee\n' + o)
    c, o = lancer('etat', jeu)
    check(c == 0 and 'ancienne version de chez nous' in o, 'etat : la v6 est signalee comme ancienne\n' + o)
    dll(jeu)
    shutil.copyfile(DIST / 'dinput8.dll', jeu / 'dinput8.dll')                                       # 31/10 : le SDK a un profil (184B144D...) reste accepte
    c, o = lancer('lancer', jeu, '--a-blanc')
    check(c == 0 and 'A BLANC : rien lance' in o, 'le SDK a un profil (notre compilation precedente) est accepte' + chr(10) + o)
    (jeu / 'dinput8.dll').write_bytes(b'MZ autre')
    c, o = lancer('lancer', jeu, '--a-blanc')
    check(c == 1 and 'dinput8.dll' in o, 'une autre dinput8.dll est refusee' + chr(10) + o)
    dll(jeu)
    c, o = lancer('etat', jeu)
    check(c == 0 and o.count('version attendue') == 2, 'etat : le SDK a deux profils et la v15 sont les versions attendues' + chr(10) + o)
    with open(jeu / NOM, 'ab') as f:
        f.write(b'\0')
    c, o = lancer('lancer', jeu, '--a-blanc')
    check(c == 1 and 'modifie' in o, 'copie modifiee\n' + o)

    print('4. retirer')
    jeu = faux('faux_lancer_4')
    main_avant = sha(jeu / 'carrier_command.exe')
    c, o = lancer('retirer', jeu)
    check(c == 0 and 'Rien a retirer' in o, 'rien a retirer\n' + o)
    lancer('copier', jeu)
    c, o = lancer('retirer', jeu, ouvert=True)
    check(c == 1 and (jeu / NOM).exists(), 'jeu ouvert : pas de suppression\n' + o)
    c, o = lancer('retirer', jeu, '--a-blanc')
    check(c == 0 and (jeu / NOM).exists(), 'a blanc : pas de suppression\n' + o)
    c, o = lancer('retirer', jeu)
    check(c == 0 and 'RETRAIT TERMINE' in o and not (jeu / NOM).exists(), 'retrait\n' + o)
    check(sha(jeu / 'carrier_command.exe') == main_avant, "l'exe de Steam n'est pas touche")

    print('5. chemin « steamapps » : --cest-le-vrai-jeu obligatoire')
    jeu = faux('faux_lancer_5', 'steamapps')
    c, o = lancer('copier', jeu)
    check(c == 1 and 'VRAI jeu' in o and not (jeu / NOM).exists(), 'refus sans le drapeau\n' + o)
    c, o = lancer('copier', jeu, '--cest-le-vrai-jeu')
    check(c == 0 and (jeu / NOM).exists(), 'ok avec le drapeau\n' + o)

    for n in range(1, 6):
        shutil.rmtree(TRAVAIL / f'faux_lancer_{n}', ignore_errors=True)
    print(f'\n{pass_} controles reussis, {fail} echec(s)')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
