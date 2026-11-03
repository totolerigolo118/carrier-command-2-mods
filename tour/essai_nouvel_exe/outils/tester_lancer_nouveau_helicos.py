#!/usr/bin/env python3
"""Essais de lancer_nouveau_helicos.py sur des FAUX dossiers (C:\\Users\\UTILISATEUR\\Documents\\cc2-port-travail\\faux_nouveau_h_*).

Ne touche ni au vrai jeu ni a Steam et ne lance AUCUN jeu (seulement `--a-blanc` et des refus). Lancer : python -I -B tester_lancer_nouveau_helicos.py
"""
import contextlib
import hashlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
LANCER = ICI / 'lancer_nouveau_helicos.py'
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-port-travail')
SDK_TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-travail')
NEUF = TRAVAIL / 'carrier_command_nouveau_steam_461E1262.exe'
TROIS = TRAVAIL / 'carrier_command_nouveau_patche_ascenseur_temps_pont.exe'
NOM = 'carrier_command_nouveau_2C9F8E47.exe'
SHA_COPIE = '2C9F8E47FD494BD3EF04038910C6E2A086742BCDA6AF71CACE2E1B69EA766F06'
pass_, fail = 0, 0

spec = importlib.util.spec_from_file_location('lancer_nouveau_helicos_sous_test', LANCER)
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
L = H.L


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
    assert d.parent == TRAVAIL and nom.startswith('faux_nouveau_h_'), d      # on ne supprime que nos faux dossiers
    if d.exists():
        shutil.rmtree(d)
    jeu = d / sous / 'jeu' if sous else d / 'jeu'
    jeu.mkdir(parents=True)
    shutil.copyfile(NEUF, jeu / 'carrier_command.exe')
    return jeu


def dll(jeu):
    shutil.copyfile(TRAVAIL / 'sdk' / 'dist' / 'dinput8.dll', jeu / 'dinput8.dll')
    shutil.copyfile(SDK_TRAVAIL.parent / 'cc2-sdk-travail-v15' / 'dist' / 'cc2x_frein.dll', jeu / 'cc2x_frein.dll')


def cli(cmd, jeu, *extra, ouvert=False, steam=True, appdata=None):
    env = dict(os.environ)
    # 02/11 : jamais le vrai %APPDATA% (son frein.ini a auto_recall=1) : un faux dossier vide par defaut
    env['APPDATA'] = str(appdata or (TRAVAIL / 'faux_nouveau_h_appdata'))
    env['POSER_SIMULER_JEU_OUVERT'] = '1' if ouvert else '0'
    env['LANCER_SIMULER_STEAM'] = '1' if steam else '0'
    r = subprocess.run([sys.executable, '-I', '-B', str(LANCER), cmd, '--jeu', str(jeu), *extra], capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def appel(fonction, *a):
    tampon, code = io.StringIO(), 0
    with contextlib.redirect_stdout(tampon):
        try:
            fonction(*a)
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
    return code, tampon.getvalue()


def main():
    print('0. la source et sa composition (en memoire)')
    check(sha(L.SOURCE) == SHA_COPIE and L.NOM == NOM, 'la source et le nom sont ceux de la copie a 4 reglages')
    c, o = appel(L.composition_ok, L.SOURCE.read_bytes())
    check(c == 0, 'la copie a 4 reglages passe\n' + o)
    for nom, chemin in (('la copie a 3 reglages (5AF41B4D...)', TROIS), ('le build de Steam sans patch', NEUF)):
        c, o = appel(L.composition_ok, Path(chemin).read_bytes())
        check(c == 1 and 'REFUS' in o, f'{nom} doit etre refusee\n' + o)

    print('1. copie, copie redondante, lancer a blanc, retirer')
    jeu = faux('faux_nouveau_h_1')
    steam_avant = sha(jeu / 'carrier_command.exe')
    c, o = cli('copier', jeu, '--a-blanc'); check(c == 0 and not (jeu / NOM).exists(), 'a blanc : rien ecrit\n' + o)
    c, o = cli('copier', jeu); check(c == 0 and sha(jeu / NOM) == SHA_COPIE, 'copie\n' + o)
    check(sorted(p.name for p in jeu.iterdir()) == sorted(['carrier_command.exe', NOM]), 'un seul fichier ajoute')
    c, o = cli('copier', jeu); check(c == 0 and 'Deja en place' in o, 'copie redondante\n' + o)
    dll(jeu); (jeu / 'steam_appid.txt').write_text('1489630')
    c, o = cli('lancer', jeu, '--a-blanc'); check(c == 0 and 'A BLANC : rien lance' in o and NOM in o, 'lancer a blanc : la bonne copie\n' + o)
    c, o = cli('lancer', jeu, '--a-blanc', ouvert=True); check(c == 1 and 'tourne' in o, 'jeu ouvert : refus\n' + o)
    c, o = cli('retirer', jeu); check(c == 0 and not (jeu / NOM).exists(), 'retrait\n' + o)
    check(sha(jeu / 'carrier_command.exe') == steam_avant, "l'exe de Steam n'est pas touche")

    print('2. refus : la copie a 3 reglages posee sous le nom de la copie a 4, fichier existant different')
    jeu = faux('faux_nouveau_h_2')
    shutil.copyfile(TROIS, jeu / NOM)
    c, o = cli('copier', jeu); check(c == 1 and sha(jeu / NOM) == sha(TROIS), 'un fichier existant different n\'est jamais remplace\n' + o)
    dll(jeu); (jeu / 'steam_appid.txt').write_text('1489630')
    c, o = cli('lancer', jeu, '--a-blanc'); check(c == 1 and 'modifie' in o, 'lancer refuse un fichier qui n\'est pas la bonne copie\n' + o)
    c, o = cli('retirer', jeu); check(c == 1 and (jeu / NOM).exists(), 'retirer ne supprime pas un fichier qui n\'est pas la bonne copie\n' + o)

    print('3. la copie a 3 reglages, deja dans le dossier, n\'est pas touchee')
    jeu = faux('faux_nouveau_h_3')
    shutil.copyfile(TROIS, jeu / 'carrier_command_nouveau_5AF41B4D.exe')
    cli('copier', jeu); cli('retirer', jeu)
    check(sha(jeu / 'carrier_command_nouveau_5AF41B4D.exe') == sha(TROIS) and not (jeu / NOM).exists(), 'copier puis retirer laissent la copie a 3 reglages intacte')

    print('4. frein v13/v14 : heli_recall (crochet H6) ou auto_recall (retour auto) serait une 2e nouveaute -> refus')
    jeu = faux('faux_nouveau_h_4')
    cli('copier', jeu); dll(jeu); (jeu / 'steam_appid.txt').write_text('1489630')
    ad = TRAVAIL / 'faux_nouveau_h_4' / 'appdata'; (ad / 'Carrier Command 2' / 'cc2x').mkdir(parents=True)
    ini = ad / 'Carrier Command 2' / 'cc2x' / 'frein.ini'
    for texte, refuse in (('[frein]\nrecall_force=1\nheli_recall=1\n', True), ('[frein]\nheli_recall = 2\n', True),
                          ('[frein]\nrecall_force=1\nheli_recall=0\n', False), ('[frein]\n; heli_recall=1\nrecall_force=1\n', False),
                          ('[frein]\nrecall_force=1\n', False), ('[frein]\nrecall_force=1\nauto_recall=1\nauto_recall_s=5\n', 'auto_recall'),
                          ('[frein]\nauto_recall=0\nauto_recall_s=5\n', False)):
        ini.write_text(texte)
        c, o = cli('lancer', jeu, '--a-blanc', appdata=ad)
        if refuse:
            cle = refuse if isinstance(refuse, str) else 'heli_recall'
            check(c == 1 and cle in o and 'A BLANC' not in o, f'refus avec {texte!r}\n' + o)
        else:
            check(c == 0 and 'A BLANC : rien lance' in o, f'accepte avec {texte!r}\n' + o)
    ok, manque, mauvais = L.bilan_journal(['11:00:00.030 [frein] info: heli_recall=1: hook H6 (0x6fdded, gives the runway to the flagged '
                                           'helicopter: continues at 0x6fde02) installed too, inactive until a helicopter is flagged'])
    check(not ok and mauvais, 'la ligne « hook H6 » du journal compte comme un probleme')
    for ligne in ('11:00:00.030 [frein] info: settings: ... hooks=1 heli_recall=0 heli_hook=0 auto_recall=1 auto_recall_s=5',
                  '11:05:00.000 [frein] info: id 17: AUTO RECALL asked'):
        ok, manque, mauvais = L.bilan_journal([ligne])
        check(not ok and mauvais, f'la ligne {ligne!r} compte comme un probleme')
    ok, manque, mauvais = L.bilan_journal(['11:00:00.030 [frein] info: settings: ... hooks=1 heli_recall=0 heli_hook=0 auto_recall=0 auto_recall_s=5'])
    check(not mauvais, 'auto_recall=0 dans la ligne des reglages ne compte pas comme un probleme')

    for p in TRAVAIL.glob('faux_nouveau_h_*'):
        shutil.rmtree(p, ignore_errors=True)
    print(f'\n{pass_} controles reussis, {fail} echec(s)')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
