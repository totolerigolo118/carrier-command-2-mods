#!/usr/bin/env python3
"""Essais de lancer_multi_3.py et lancer_multi_5.py sur des FAUX dossiers (C:\\Users\\UTILISATEUR\\Documents\\cc2-port-travail\\faux_multi_*).

Ne touche ni au vrai jeu ni a Steam et ne lance AUCUN jeu (seulement `--a-blanc` et des refus). Lancer : python -I -B tester_lancer_multi.py
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
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-port-travail')
SDK_TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-travail')
NEUF = TRAVAIL / 'carrier_command_nouveau_steam_461E1262.exe'
TREIZE_H = TRAVAIL / 'carrier_command_nouveau_patche_ascenseur_temps_pont.exe'            # 5AF41B4D... (avec temps_x2)
HELICOS = TRAVAIL / 'carrier_command_nouveau_patche_ascenseur_temps_pont_helicos.exe'    # 2C9F8E47... (avec temps_x2)
VARIANTES = {
    '3': ('lancer_multi_3.py', 'carrier_command_nouveau_795CD61D.exe', '795CD61DE271F8DA4B97F499491DD3CBCCED1A1433EBEBFCB63A182AF4AA1A0E'),
    '5': ('lancer_multi_5.py', 'carrier_command_nouveau_FCB3CDE1.exe', 'FCB3CDE18346DACE6D86D217733F1E617AE1DD88BBE033A4AC8F6FDBE3313CFC'),
}
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


def charger(fichier):
    spec = importlib.util.spec_from_file_location('sous_test_' + fichier[:-3], ICI / fichier)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.L


def faux(nom):
    d = TRAVAIL / nom
    assert d.parent == TRAVAIL and nom.startswith('faux_multi_'), d       # on ne supprime que nos faux dossiers
    if d.exists():
        shutil.rmtree(d)
    jeu = d / 'jeu'
    jeu.mkdir(parents=True)
    shutil.copyfile(NEUF, jeu / 'carrier_command.exe')
    return jeu


def dll(jeu):
    """Les versions epinglees : le SDK a DEUX profils (E1DE25D5...) et le frein v15 (238B0456...)."""
    shutil.copyfile(TRAVAIL / 'sdk' / 'dist' / 'dinput8.dll', jeu / 'dinput8.dll')
    shutil.copyfile(SDK_TRAVAIL.parent / 'cc2-sdk-travail-v15' / 'dist' / 'cc2x_frein.dll', jeu / 'cc2x_frein.dll')
    (jeu / 'steam_appid.txt').write_text('1489630')


def cli(lanceur, cmd, jeu, *extra, ouvert=False, steam=True, appdata=None):
    env = dict(os.environ)
    env['POSER_SIMULER_JEU_OUVERT'] = '1' if ouvert else '0'
    env['LANCER_SIMULER_STEAM'] = '1' if steam else '0'
    # 02/11 : jamais le vrai %APPDATA% (son frein.ini a auto_recall=1) : un faux dossier vide par defaut
    env['APPDATA'] = str(appdata or (TRAVAIL / 'faux_multi_appdata'))
    r = subprocess.run([sys.executable, '-I', '-B', str(ICI / lanceur), cmd, '--jeu', str(jeu), *extra], capture_output=True, text=True, env=env)
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
    for cle, (lanceur, nom, sha_copie) in VARIANTES.items():
        autre = VARIANTES['5' if cle == '3' else '3']
        L = charger(lanceur)
        print(f'--- {lanceur}')
        print('0. la source et sa composition (en memoire)')
        check(sha(L.SOURCE) == sha_copie and L.NOM == nom and 'temps_x2' not in L.MODULES_ATTENDUS, 'source, nom, pas de temps_x2')
        c, o = appel(L.composition_ok, L.SOURCE.read_bytes())
        check(c == 0, 'sa copie passe\n' + o)
        for quoi, chemin in (("l'autre copie multi", charger(autre[0]).SOURCE), ('la copie de 13:52 (avec temps_x2)', TREIZE_H),
                             ('la copie helicos (avec temps_x2)', HELICOS), ('le build de Steam sans patch', NEUF)):
            c, o = appel(L.composition_ok, Path(chemin).read_bytes())
            check(c == 1 and 'REFUS' in o, f'{quoi} doit etre refusee\n' + o)

        print('1. copie, copie redondante, lancer a blanc, retirer')
        jeu = faux(f'faux_multi_{cle}_1')
        steam_avant = sha(jeu / 'carrier_command.exe')
        c, o = cli(lanceur, 'copier', jeu, '--a-blanc'); check(c == 0 and not (jeu / nom).exists(), 'a blanc : rien ecrit\n' + o)
        c, o = cli(lanceur, 'copier', jeu); check(c == 0 and sha(jeu / nom) == sha_copie, 'copie\n' + o)
        check(sorted(p.name for p in jeu.iterdir()) == sorted(['carrier_command.exe', nom]), 'un seul fichier ajoute')
        c, o = cli(lanceur, 'copier', jeu); check(c == 0 and 'Deja en place' in o, 'copie redondante\n' + o)
        dll(jeu)
        c, o = cli(lanceur, 'lancer', jeu, '--a-blanc'); check(c == 0 and 'A BLANC : rien lance' in o and nom in o, 'lancer a blanc : la bonne copie\n' + o)
        c, o = cli(lanceur, 'lancer', jeu, '--a-blanc', ouvert=True); check(c == 1 and 'tourne' in o, 'jeu ouvert : refus\n' + o)
        c, o = cli(lanceur, 'lancer', jeu, '--a-blanc', steam=False); check(c == 1 and 'Steam' in o, 'Steam ferme : refus\n' + o)

        print('2. frein v13/v14 : heli_recall ou auto_recall actif -> refus')
        ad = TRAVAIL / f'faux_multi_{cle}_1' / 'appdata'; (ad / 'Carrier Command 2' / 'cc2x').mkdir(parents=True)
        ini = ad / 'Carrier Command 2' / 'cc2x' / 'frein.ini'
        ini.write_text('[frein]\nrecall_force=1\nheli_recall=1\n')
        c, o = cli(lanceur, 'lancer', jeu, '--a-blanc', appdata=ad); check(c == 1 and 'heli_recall' in o, 'heli_recall=1 refuse\n' + o)
        ini.write_text('[frein]\nrecall_force=1\nauto_recall=1\nauto_recall_s=5\n')
        c, o = cli(lanceur, 'lancer', jeu, '--a-blanc', appdata=ad); check(c == 1 and 'auto_recall' in o, 'auto_recall=1 refuse\n' + o)
        ini.write_text('[frein]\nrecall_force=1\n')
        c, o = cli(lanceur, 'lancer', jeu, '--a-blanc', appdata=ad); check(c == 0 and 'A BLANC : rien lance' in o, 'sans heli_recall : accepte\n' + o)
        print('2b. code inconnu que le SDK chargerait -> refus')
        mod = ad / 'mods' / 'un_mod'; (mod / 'content' / 'cc2x').mkdir(parents=True)
        (ad / 'Carrier Command 2' / 'mods.xml').write_text(f'<mods>\n<path value="{mod.as_posix()}"/>\n</mods>\n')
        c, o = cli(lanceur, 'lancer', jeu, '--a-blanc', appdata=ad); check(c == 0 and 'A BLANC : rien lance' in o, 'mod actif sans DLL : accepte\n' + o)
        (mod / 'content' / 'cc2x' / 'cc2x_virus.dll').write_bytes(b'MZ pas a nous')
        c, o = cli(lanceur, 'lancer', jeu, '--a-blanc', appdata=ad)
        check(c == 1 and 'cc2x_virus.dll' in o and 'A BLANC' not in o, 'DLL inconnue dans un mod actif : refus\n' + o)
        (mod / 'content' / 'cc2x' / 'cc2x_virus.dll').unlink()
        for etranger in ('cc2x_autre.dll', 'cc2x.ini'):
            (jeu / etranger).write_bytes(b'x')
            c, o = cli(lanceur, 'lancer', jeu, '--a-blanc', appdata=ad)
            check(c == 1 and etranger in o and 'A BLANC' not in o, f'{etranger} dans le dossier du jeu : refus\n' + o)
            (jeu / etranger).unlink()
        (jeu / 'cc2x' / 'plugins').mkdir(parents=True)
        c, o = cli(lanceur, 'lancer', jeu, '--a-blanc', appdata=ad); check(c == 1 and 'plugins' in o, 'dossier cc2x\\plugins : refus\n' + o)
        shutil.rmtree(jeu / 'cc2x')
        c, o = cli(lanceur, 'retirer', jeu); check(c == 0 and not (jeu / nom).exists(), 'retrait\n' + o)
        check(sha(jeu / 'carrier_command.exe') == steam_avant, "l'exe de Steam n'est pas touche")

        print("3. refus : un autre fichier sous ce nom ; les copies deja la ne sont pas touchees")
        jeu = faux(f'faux_multi_{cle}_2')
        shutil.copyfile(HELICOS, jeu / nom)
        c, o = cli(lanceur, 'copier', jeu); check(c == 1 and sha(jeu / nom) == sha(HELICOS), "un fichier existant different n'est jamais remplace\n" + o)
        dll(jeu)
        c, o = cli(lanceur, 'lancer', jeu, '--a-blanc'); check(c == 1 and 'modifie' in o, "lancer refuse un fichier qui n'est pas la bonne copie\n" + o)
        c, o = cli(lanceur, 'retirer', jeu); check(c == 1 and (jeu / nom).exists(), "retirer ne supprime pas un fichier qui n'est pas la bonne copie\n" + o)
        jeu = faux(f'faux_multi_{cle}_3')
        shutil.copyfile(TREIZE_H, jeu / 'carrier_command_nouveau_5AF41B4D.exe')
        cli(lanceur, 'copier', jeu); cli(lanceur, 'retirer', jeu)
        check(sha(jeu / 'carrier_command_nouveau_5AF41B4D.exe') == sha(TREIZE_H) and not (jeu / nom).exists(),
              'copier puis retirer laissent la copie de 13:52 intacte')
        c, o = cli(lanceur, 'copier', Path(r'C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2'), '--a-blanc')
        check(c != 0 and 'cest-le-vrai-jeu' in o, 'chemin steamapps : --cest-le-vrai-jeu obligatoire\n' + o)

    for p in TRAVAIL.glob('faux_multi_*'):
        shutil.rmtree(p, ignore_errors=True)
    print(f'\n{pass_} controles reussis, {fail} echec(s)')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
