#!/usr/bin/env python3
"""Essais de poser.py sur des FAUX dossiers de jeu (dans C:\\Users\\UTILISATEUR\\Documents\\cc2-sdk-travail\\faux_*).

Ne touche ni au vrai jeu, ni au vrai %APPDATA%. Lancer : python -I tester_poser.py
Le faux exe est une copie de la sauvegarde de l'original (tour/sauvegardes/), jamais lancee.
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
POSER = ICI / 'poser.py'
ORIGINAL = ICI.parents[1] / 'sauvegardes' / 'carrier_command_1.5.18_original.exe'
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


def faux(nom):
    d = TRAVAIL / nom
    assert d.parent == TRAVAIL and nom.startswith('faux_'), d      # on ne supprime que nos faux dossiers
    if d.exists():
        shutil.rmtree(d)
    (d / 'jeu').mkdir(parents=True)
    (d / 'appdata' / 'Carrier Command 2').mkdir(parents=True)
    shutil.copyfile(ORIGINAL, d / 'jeu' / 'carrier_command.exe')
    return d / 'jeu', d / 'appdata'


def poser(cmd, jeu, appdata, *extra, ouvert=None):
    env = dict(os.environ)
    env.pop('POSER_SIMULER_JEU_OUVERT', None)
    if ouvert is not None:
        env['POSER_SIMULER_JEU_OUVERT'] = '1' if ouvert else '0'
    r = subprocess.run([sys.executable, '-I', str(POSER), cmd, '--jeu', str(jeu), '--appdata', str(appdata), *extra],
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def main():
    ini_rel = Path('Carrier Command 2') / 'cc2x' / 'frein.ini'
    print('1. etat d\'un dossier vide, a blanc, pose')
    jeu, ad = faux('faux_1')
    c, o = poser('etat', jeu, ad, ouvert=False); check(c == 0 and 'absent' in o and 'version attendue' in o, 'etat initial\n' + o)
    c, o = poser('installer', jeu, ad, '--a-blanc', ouvert=False)
    check(c == 0 and not (jeu / 'dinput8.dll').exists() and not (ad / ini_rel).exists(), 'a blanc ne doit rien ecrire\n' + o)
    c, o = poser('installer', jeu, ad, ouvert=False)
    check(c == 0 and 'POSE TERMINEE' in o, 'pose\n' + o)
    exe_avant = sha(jeu / 'carrier_command.exe')
    check(sha(jeu / 'dinput8.dll') == '184B144D6E2BB868FFEB7D45ECD463F8919E64732E3B5681A16165363EBA0982', 'sha dinput8')
    check(sha(jeu / 'cc2x_frein.dll') == '941DFFB9F1671CB351A69B826B14E62AB9978390C888257DA699E8584ADC59B3', 'sha plugin')
    check((ad / ini_rel).read_bytes() == (ICI / 'frein.ini.example').read_bytes() and b'brake_enabled=0' in (ad / ini_rel).read_bytes(),
          'frein.ini = exemple, tout eteint')
    check(sorted(p.name for p in jeu.iterdir()) == ['carrier_command.exe', 'cc2x_frein.dll', 'dinput8.dll'], 'seuls 2 fichiers ajoutes dans le jeu')
    check(not list(jeu.glob('*.cc2_tmp')), 'pas de fichier temporaire')
    c, o = poser('etat', jeu, ad, ouvert=False); check(c == 0 and o.count('notre compilation') == 2, 'etat apres pose\n' + o)

    print('2. deuxieme pose refusee, rien ne change')
    c, o = poser('installer', jeu, ad, ouvert=False); check(c == 1 and 'REFUS' in o, 'double pose\n' + o)
    check(sha(jeu / 'dinput8.dll') == '184B144D6E2BB868FFEB7D45ECD463F8919E64732E3B5681A16165363EBA0982', 'dinput8 inchangee')

    print('3. jeu ouvert : pose et retrait refuses')
    c, o = poser('retirer', jeu, ad, ouvert=True); check(c == 1 and 'le jeu tourne' in o and (jeu / 'dinput8.dll').exists(), 'retrait refuse jeu ouvert\n' + o)
    jeu2, ad2 = faux('faux_2')
    c, o = poser('installer', jeu2, ad2, ouvert=True); check(c == 1 and not (jeu2 / 'dinput8.dll').exists(), 'pose refusee jeu ouvert\n' + o)

    print('4. retrait : a blanc, normal, --tout')
    c, o = poser('retirer', jeu, ad, '--a-blanc', ouvert=False); check(c == 0 and (jeu / 'dinput8.dll').exists(), 'retrait a blanc\n' + o)
    (jeu / 'cc2x.log').write_text('journal de test')
    c, o = poser('retirer', jeu, ad, ouvert=False)
    check(c == 0 and not (jeu / 'dinput8.dll').exists() and not (jeu / 'cc2x_frein.dll').exists() and (jeu / 'cc2x.log').exists()
          and (ad / ini_rel).exists(), 'retrait simple garde le journal et les reglages\n' + o)
    check(sha(jeu / 'carrier_command.exe') == exe_avant, 'exe jamais touche')
    c, o = poser('installer', jeu, ad, ouvert=False); check(c == 0, 'repose possible apres retrait\n' + o)
    c, o = poser('retirer', jeu, ad, '--tout', ouvert=False)
    check(c == 0 and not (jeu / 'cc2x.log').exists() and not (ad / ini_rel).exists() and not (ad / 'Carrier Command 2' / 'cc2x').exists(),
          '--tout retire journal, reglages inchanges et dossier vide\n' + o)
    c, o = poser('retirer', jeu, ad, ouvert=False); check(c == 0 and 'Rien a retirer' in o, 'retrait a vide\n' + o)

    print('5. reglages modifies conserves ; fichier modifie jamais supprime')
    jeu, ad = faux('faux_3')
    poser('installer', jeu, ad, ouvert=False)
    (ad / ini_rel).write_text('[frein]\nbrake_enabled=1\n')
    c, o = poser('retirer', jeu, ad, '--tout', ouvert=False); check(c == 0 and (ad / ini_rel).exists() and 'conserve' in o, 'frein.ini modifie conserve\n' + o)
    poser('installer', jeu, ad, ouvert=False)
    with open(jeu / 'dinput8.dll', 'r+b') as f:
        f.seek(100); b = f.read(1); f.seek(100); f.write(bytes([b[0] ^ 1]))
    c, o = poser('retirer', jeu, ad, ouvert=False); check(c == 1 and (jeu / 'dinput8.dll').exists() and 'DIFFERENT' in o, 'dinput8 modifiee : refus\n' + o)

    print('6. refus : autre dinput8.dll, cc2x.ini, autre plugin, autre version de l\'exe, mod avec dossier cc2x, dossier steamapps')
    jeu, ad = faux('faux_4'); (jeu / 'dinput8.dll').write_bytes(b'MZ autre')
    c, o = poser('installer', jeu, ad, ouvert=False); check(c == 1 and (jeu / 'dinput8.dll').read_bytes() == b'MZ autre' and not (jeu / 'cc2x_frein.dll').exists(), 'autre dinput8.dll\n' + o)
    jeu, ad = faux('faux_5'); (jeu / 'cc2x.ini').write_text('[cc2x]\ntime_scale=4\n')
    c, o = poser('installer', jeu, ad, ouvert=False); check(c == 1 and not (jeu / 'dinput8.dll').exists(), 'cc2x.ini present\n' + o)
    jeu, ad = faux('faux_6'); (jeu / 'cc2x_autre.dll').write_bytes(b'x')
    c, o = poser('installer', jeu, ad, ouvert=False); check(c == 1 and not (jeu / 'dinput8.dll').exists(), 'autre plugin present\n' + o)
    jeu, ad = faux('faux_7')
    with open(jeu / 'carrier_command.exe', 'r+b') as f:
        f.seek(0x3c); nt = int.from_bytes(f.read(4), 'little'); f.seek(nt + 8); f.write(b'\x01\x00\x00\x00')
    c, o = poser('installer', jeu, ad, ouvert=False); check(c == 1 and 'autre version' in o.lower() and not (jeu / 'dinput8.dll').exists(), 'autre version de l\'exe\n' + o)
    jeu, ad = faux('faux_8')
    mod = TRAVAIL / 'faux_8' / 'mod_avec_cc2x'; (mod / 'content' / 'cc2x').mkdir(parents=True)
    (ad / 'Carrier Command 2' / 'mods.xml').write_text(f'<data><active_mod_folders><path value="{mod}"/></active_mod_folders></data>')
    c, o = poser('installer', jeu, ad, ouvert=False); check(c == 1 and 'mod actif' in o and not (jeu / 'dinput8.dll').exists(), 'mod actif avec cc2x\n' + o)
    jeu, ad = faux('faux_9')
    sa = TRAVAIL / 'faux_9' / 'steamapps' / 'common' / 'CC2'; sa.mkdir(parents=True); shutil.copyfile(jeu / 'carrier_command.exe', sa / 'carrier_command.exe')
    c, o = poser('installer', sa, ad, ouvert=False); check(c == 1 and 'cest-le-vrai-jeu' in o and not (sa / 'dinput8.dll').exists(), 'steamapps sans confirmation\n' + o)
    c, o = poser('installer', sa, ad, '--cest-le-vrai-jeu', ouvert=False); check(c == 0 and (sa / 'dinput8.dll').exists(), 'steamapps avec confirmation (faux dossier)\n' + o)

    print('7. DLL source modifiee : refus')
    jeu, ad = faux('faux_10')
    src = TRAVAIL / 'faux_10' / 'dist'; src.mkdir()
    for n in ('dinput8.dll', 'cc2x_frein.dll'):
        shutil.copyfile(TRAVAIL / 'dist' / n, src / n)
    with open(src / 'cc2x_frein.dll', 'r+b') as f:
        f.seek(200); b = f.read(1); f.seek(200); f.write(bytes([b[0] ^ 1]))
    c, o = poser('installer', jeu, ad, '--source', str(src), ouvert=False); check(c == 1 and 'sha256' in o and not (jeu / 'dinput8.dll').exists(), 'source alteree\n' + o)

    print('8. maj : remplace SEULEMENT notre version precedente de cc2x_frein.dll')
    v1 = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2\cc2x_frein.dll')   # lecture seule : copie de la v1 posee
    SHA_V1 = sha(v1) if v1.is_file() else ''
    if v1.is_file() and sha(v1) in ('E50634F4E6A39B647E586124DBBC2B7F9E329CD91802DA3D25BE22622D521D40', 'F42433D1724E7D143370942696CE2DBD442C61D058E7265CBEDF8E7435A2A117', '72CE4E29377D2A63D6990DB46FD153A41254F93A98F389F25ECC2BFC2976272A', 'BBE281EE2DC82A73017FCCE54DA0C8BE28A163269A0484002DBBA9818AC878A7', '4B70F03194B99BCCD506EACC5331D1E7906ADC23B567B8FB24AFD04898526F29', '9A082FBB677D7DE6A4CAD2091060B6C604B349F2EEB429322ABA3B8F619E5E8A', 'A3D785206B55FA69B8AF30FDBDC724C85E8246816E7E87A24853B3238C0546C5', '0C8D68ADCD6794C8B73610FB6EA759A04626D8F97FEC088EDA7C6F628B1B731E', 'DEA9295AF0E08C19042B1C9DE5C61D7CB64E7915999C4E52BE35A3187F20DDDA', '66731A35ED5C7148019A8B6E31D234A3C0844AE7FF014C7E65320D06B9E60A25', '3CD7225D1BCE332B4DBDFFCC292C4834E2CB30D2552E9799194DD8A70C0F210F'):
        jeu, ad = faux('faux_11'); poser('installer', jeu, ad, ouvert=False)
        exe_avant = sha(jeu / 'carrier_command.exe'); din = sha(jeu / 'dinput8.dll')
        c, o = poser('maj', jeu, ad, ouvert=False); check(c == 0 and 'Deja a jour' in o, 'maj sur la v2 : rien a faire\n' + o)
        shutil.copyfile(v1, jeu / 'cc2x_frein.dll')
        c, o = poser('etat', jeu, ad, ouvert=False); check(c == 0 and 'PRECEDENTE' in o, 'etat reconnait la v1\n' + o)
        c, o = poser('maj', jeu, ad, '--a-blanc', ouvert=False); check(c == 0 and sha(jeu / 'cc2x_frein.dll') == SHA_V1, 'maj a blanc ne change rien\n' + o)
        c, o = poser('maj', jeu, ad, ouvert=True); check(c == 1 and sha(jeu / 'cc2x_frein.dll') == SHA_V1, 'maj refusee jeu ouvert\n' + o)
        c, o = poser('maj', jeu, ad, ouvert=False)
        check(c == 0 and 'MISE A JOUR TERMINEE' in o and sha(jeu / 'cc2x_frein.dll') == '941DFFB9F1671CB351A69B826B14E62AB9978390C888257DA699E8584ADC59B3'
              and sha(jeu / 'dinput8.dll') == din and sha(jeu / 'carrier_command.exe') == exe_avant, 'maj v1 -> v2\n' + o)
        check(not list(jeu.glob('*.cc2_tmp')), 'pas de fichier temporaire apres maj')
        shutil.copyfile(v1, jeu / 'cc2x_frein.dll')
        c, o = poser('retirer', jeu, ad, ouvert=False)
        check(c == 0 and not (jeu / 'cc2x_frein.dll').exists() and not (jeu / 'dinput8.dll').exists(), 'retirer supprime aussi la v1\n' + o)
        jeu, ad = faux('faux_12'); poser('installer', jeu, ad, ouvert=False)
        with open(jeu / 'cc2x_frein.dll', 'r+b') as f:
            f.seek(300); b = f.read(1); f.seek(300); f.write(bytes([b[0] ^ 1]))
        c, o = poser('maj', jeu, ad, ouvert=False); check(c == 1 and 'pas une de nos compilations' in o, 'maj refusee sur un fichier inconnu\n' + o)
        jeu, ad = faux('faux_13'); shutil.copyfile(v1, jeu / 'cc2x_frein.dll')
        c, o = poser('maj', jeu, ad, ouvert=False); check(c == 1 and sha(jeu / 'cc2x_frein.dll') == SHA_V1, 'maj refusee sans dinput8.dll de chez nous\n' + o)
        # 29/10 : sur le nouveau build de Steam, `maj` n'est permise que s'il y a la copie exacte de l'ancien exe a cote
        jeu, ad = faux('faux_14'); poser('installer', jeu, ad, ouvert=False)
        b = bytearray((jeu / 'carrier_command.exe').read_bytes())
        nt = struct.unpack_from('<I', b, 0x3c)[0]
        struct.pack_into('<I', b, nt + 8, 0x6ae228f3)                       # exe « de Steam » du nouveau build
        (jeu / 'carrier_command.exe').write_bytes(bytes(b))
        shutil.copyfile(v1, jeu / 'cc2x_frein.dll')
        c, o = poser('maj', jeu, ad, ouvert=False); check(c == 1 and sha(jeu / 'cc2x_frein.dll') == SHA_V1, 'maj refusee : nouveau build et pas de copie de l ancien exe\n' + o)
        shutil.copyfile(ORIGINAL.parent / 'carrier_command_1.5.18_patche_8E7FCBB6.exe', jeu / 'carrier_command_ancien_8E7FCBB6.exe')
        c, o = poser('maj', jeu, ad, '--a-blanc', ouvert=False); check(c == 0 and sha(jeu / 'cc2x_frein.dll') == SHA_V1, 'maj a blanc avec la copie de l ancien exe\n' + o)
        c, o = poser('maj', jeu, ad, ouvert=False)
        check(c == 0 and 'MISE A JOUR TERMINEE' in o and sha(jeu / 'cc2x_frein.dll') == '941DFFB9F1671CB351A69B826B14E62AB9978390C888257DA699E8584ADC59B3', 'maj avec la copie exacte de l ancien exe\n' + o)
        with open(jeu / 'carrier_command_ancien_8E7FCBB6.exe', 'ab') as f:
            f.write(b'\0')
        shutil.copyfile(v1, jeu / 'cc2x_frein.dll')
        c, o = poser('maj', jeu, ad, ouvert=False); check(c == 1 and sha(jeu / 'cc2x_frein.dll') == SHA_V1, 'maj refusee : copie de l ancien exe modifiee\n' + o)
        c, o = poser('installer', jeu, ad, ouvert=False); check(c == 1, 'installer reste strict sur le nouveau build\n' + o)
    else:
        print('  (v1 absente du jeu : essais de maj sautes)')

    for d in TRAVAIL.glob('faux_*'):
        shutil.rmtree(d)
    print(f'\n{pass_} controles reussis, {fail} echec(s)')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
