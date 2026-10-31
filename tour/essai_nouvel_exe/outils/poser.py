#!/usr/bin/env python3
"""Pose / retrait de dinput8.dll (SDK CC2X compile par nous) et de cc2x_frein.dll dans le dossier du jeu.

  python -I poser.py etat      --jeu DOSSIER_DU_JEU
  python -I poser.py installer --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]
  python -I poser.py maj       --jeu DOSSIER_DU_JEU [--a-blanc] [--cest-le-vrai-jeu]    (remplace cc2x_frein.dll v1 par la v2)
  python -I poser.py retirer   --jeu DOSSIER_DU_JEU [--a-blanc] [--tout] [--cest-le-vrai-jeu]

Aucun dossier par defaut : --jeu est toujours donne. Python standard seulement, aucun reseau.

31/10 : COPIE pour l'essai du nouvel exe (tour/essai_nouvel_exe/outils), faite depuis la worktree manual-landings (v12). Seuls changements :
le SDK epingle est la DLL a deux profils E1DE25D5... (184B144D... devient notre compilation precedente), les deux builds sont
reconnus (PE_RECONNUS), le plugin du bouton Hold (EE9043DA...) est connu dans son mod. La pose du SDK lui-meme : poser_sdk.py.

Securites (meme esprit que patch_exe.py) :
  - les deux DLL doivent avoir EXACTEMENT les sha256 epingles ci-dessous (ceux du rapport de compilation) ;
  - le jeu doit etre FERME (processus carrier_command.exe lance depuis CE dossier) ; sur un chemin « steamapps »
    il faut --cest-le-vrai-jeu ;
  - l'executable du dossier doit etre la version que le SDK attend (horodatage PE + taille d'image) ;
  - refus s'il existe deja une dinput8.dll, un cc2x_*.dll, un dossier cc2x\\plugins, un cc2x.ini dans le dossier du jeu
    (le SDK les lirait / les chargerait), ou un mod actif qui contient un dossier cc2x (sa DLL serait executee) ;
  - ne remplace JAMAIS un fichier existant, sauf `maj` : uniquement cc2x_frein.dll, uniquement si son sha256 est celui de notre
    version PRECEDENTE ; ecriture dans un fichier temporaire, relecture du sha256, puis renommage ;
  - `retirer` ne supprime un fichier que si son sha256 est exactement le notre ; jamais l'executable ;
  - ecrit seulement : <jeu>\\dinput8.dll, <jeu>\\cc2x_frein.dll et, s'il manque, %APPDATA%\\Carrier Command 2\\cc2x\\frein.ini
    (copie de frein.ini.example : TOUT ETEINT). `retirer --tout` supprime aussi cc2x.log, frein.ini (s'il est inchange)
    et le dossier cc2x s'il est vide.
"""
import argparse
import hashlib
import os
import re
import struct
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-travail')
SOURCE_DEFAUT = TRAVAIL / 'dist'
SOURCES_DEFAUT = {'dinput8.dll': Path(r'C:\Users\UTILISATEUR\Documents\cc2-port-travail\sdk\dist'),     # la DLL a deux profils (E1DE25D5...)
                  'cc2x_frein.dll': SOURCE_DEFAUT}
EXEMPLE_INI = ICI / 'frein.ini.example'
# 31/10 (copie de l'essai du nouvel exe, tour/essai_nouvel_exe) : le SDK epingle est la DLL A DEUX PROFILS (ancien exe + build de Steam
# du 28/10), relue par une autre conversation (tour/revue_sdk_deux_profils/VERDICT.md, worktree quirky-wright) ; posee par poser_sdk.py.
# L'ancienne DLL a un profil (184B144D...) reste reconnue comme notre compilation PRECEDENTE (retour arriere).
SHA = {'dinput8.dll': 'E1DE25D53A5588BDA62269D6D93335ACB9F32EA555AC9274FE7973C19D6225D7',
       'cc2x_frein.dll': '941DFFB9F1671CB351A69B826B14E62AB9978390C888257DA699E8584ADC59B3'}     # v12 : H5 (0x6fe470) envoie l'avion pose au test de toucher du jeu (chemin des helicos), sonde de prise en charge, suivi, table par build
# nos compilations PRECEDENTES, reconnues par `retirer` et remplacables par `maj` (jamais d'autre fichier)
SHA_ANCIENNES = {'dinput8.dll': {'184B144D6E2BB868FFEB7D45ECD463F8919E64732E3B5681A16165363EBA0982'},       # SDK 0.5.0 a un profil (pose le 27/10 ; copie dans cc2-sdk-travail\dist\)
                 'cc2x_frein.dll': {'E50634F4E6A39B647E586124DBBC2B7F9E329CD91802DA3D25BE22622D521D40',     # v1 (posee a 09:21)
                                    'F42433D1724E7D143370942696CE2DBD442C61D058E7265CBEDF8E7435A2A117',     # v2 (posee a 14:59)
                                    '72CE4E29377D2A63D6990DB46FD153A41254F93A98F389F25ECC2BFC2976272A',    # v3 (posee a 15:29)
                                    'BBE281EE2DC82A73017FCCE54DA0C8BE28A163269A0484002DBBA9818AC878A7',    # v4 (posee a 15:52)
                                    '4B70F03194B99BCCD506EACC5331D1E7906ADC23B567B8FB24AFD04898526F29',    # v5 (posee a 08:14)
                                    '9A082FBB677D7DE6A4CAD2091060B6C604B349F2EEB429322ABA3B8F619E5E8A',    # v6 (posee a 09:50)
                                    'A3D785206B55FA69B8AF30FDBDC724C85E8246816E7E87A24853B3238C0546C5',    # v7 (posee a 15:46 le 29/10)
                                    '0C8D68ADCD6794C8B73610FB6EA759A04626D8F97FEC088EDA7C6F628B1B731E',    # v8 (posee a 08:00 le 30/10, essai)
                                    'DEA9295AF0E08C19042B1C9DE5C61D7CB64E7915999C4E52BE35A3187F20DDDA',    # v9 (posee a 08:30 le 30/10, essai)
                                    '66731A35ED5C7148019A8B6E31D234A3C0844AE7FF014C7E65320D06B9E60A25',    # v10 (posee a 09:25 le 30/10, grand essai ; sauvegardee dans cc2-sdk-travail\dist_v10\)
                                    '3CD7225D1BCE332B4DBDFFCC292C4834E2CB30D2552E9799194DD8A70C0F210F'}}    # v11 (jamais posee, abandonnee le 31/10 ; sauvegardee dans cc2-sdk-travail\dist_v11\)
# 28/10 : plugin d'observation de la session « modes carburant », pose dans son mod avec l'accord du moddeur (il lit les gaz, n'ecrit rien dans le jeu).
# Reconnu par son sha256 exact pour `maj` SEULEMENT (nous ne l'avons pas relu) ; tout autre fichier dans un dossier cc2x de mod reste un refus.
MODS_PLUGINS_CONNUS = {'cc2x_modes.dll': {'AB2D5343C983C97784616A3965CA26BD1072B99DE82E92A474F9814A993A46E4',     # v1 (28/10)
                                          '331581C64CB880AB0BC8CBC3258414F55C41723FB8DA7042CFDABE08CABC8729',      # v3 (pose par la conversation « modes carburant » le 30/10 a 07:38, non relu par nous)
                                          '4B2EBC04D772D7EFB2F21E70AA17CB7FE26CF7A044FDFE3B97F07FDCD1FE1D51'},     # v3.1 (pose par « modes carburant » le 30/10 a 08:21 ; meme empreinte que son rapport de compilation plugin/v3_1/RAPPORT_compilation.md ; non relu par nous)
                       'cc2x_hold.dll': {'EE9043DA4773F8360C18BCFE2FF2554FA6A2ECE5D8DA675B96B0E98F2C7F3793',      # v1 du bouton Hold (mod cc2_hold_copies, pose le 31/10 a 11:36 avec l'accord du moddeur ; non relu par nous)
                                         'DDB0AB76ED2C8A20CA72E3609DFD61843D9FDA16ADE07B8A7064F54402D9DDA5',      # v2 « synchronise » (posee le 31/10 a 13:13 par la conversation Hold avec l'accord du moddeur ; empreinte relue par nous, code non relu)
                                         '4837B1B9FC26C3AA236A28564785BF6F74F2BC97D4C3150B54355AD90D89DF17'}}     # v2.1 (posee le 31/10 vers 13:22 a la place de la v2, accord du moddeur ; empreinte relue par nous, code non relu)
PE_ATTENDU = (0x6a36c177, 0x00af7000)           # horodatage PE, taille d'image : l'ancien exe 1.5.18 Windows
PE_NOUVEAU = (0x6ae228f3, 0x00af7000)           # le build de Steam du 28/10 (461E1262...)
PE_RECONNUS = (PE_ATTENDU, PE_NOUVEAU)          # ce que le SDK epingle (deux profils) reconnait
# 29/10 : depuis la mise a jour Steam, carrier_command.exe n'est plus ce build ; l'ancien exe est copie a cote du jeu par lancer_ancien.py
# (sha256 exact). `maj` SEULEMENT accepte ce fichier-la comme exe que le SDK reconnait ; `installer` reste strict.
EXE_ANCIEN = ('carrier_command_ancien_8E7FCBB6.exe', '8E7FCBB6CE27BD3D8FEB02BF7F3DBBA646CCE6D4944360570F082972E8DFE8BE')


def sha(octets):
    return hashlib.sha256(octets).hexdigest().upper()


def refus(msg):
    print('REFUS :', msg)
    sys.exit(1)


def dans(chemin, dossier):
    a, b = os.path.normcase(os.path.abspath(chemin)), os.path.normcase(os.path.abspath(dossier))
    return a == b or a.startswith(b + os.sep)


def jeu_ouvert(jeu):
    """True / False ; None si on ne sait pas (a traiter comme « ouvert »)."""
    sim = os.environ.get('POSER_SIMULER_JEU_OUVERT')
    if sim and dans(jeu, TRAVAIL):                      # simulation reservee aux faux dossiers de nos essais
        return sim == '1'
    # carrier_command* : aussi les copies d'essai posees a cote du jeu (carrier_command_test_*.exe, carrier_command_ancien_*.exe)
    cmd = ('Get-Process -Name carrier_command* -ErrorAction SilentlyContinue | '
           'ForEach-Object { if ($_.Path) { $_.Path } else { "?" } }')
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', cmd],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None
    chemins = [l.strip() for l in out.splitlines() if l.strip()]
    return any(c == '?' or dans(c, jeu) for c in chemins)


def pe_de(exe):
    d = Path(exe).read_bytes()[:4096]
    nt = struct.unpack_from('<I', d, 0x3c)[0]
    ts = struct.unpack_from('<I', d, nt + 8)[0]
    taille = struct.unpack_from('<I', d, nt + 24 + 56)[0]
    return ts, taille


def mods_avec_cc2x(appdata):
    """Dossiers cc2x des mods actifs (mods.xml) : le SDK y chargerait des DLL."""
    mx = Path(appdata) / 'Carrier Command 2' / 'mods.xml'
    if not mx.is_file():
        return []
    trouves = []
    for m in re.finditer(r'<path value="([^"]+)"', mx.read_text(encoding='utf-8', errors='replace')):
        d = Path(m.group(1).replace('/', '\\'))
        for sous in (d / 'content' / 'cc2x', d / 'cc2x'):
            if sous.exists():
                trouves.append(str(sous))
    return trouves


def mods_cc2x_inconnus(dossiers):
    """Fichiers des dossiers cc2x de mods autres que les plugins de MODS_PLUGINS_CONNUS (sha256 exact)."""
    inconnus = []
    for d in dossiers:
        for f in Path(d).iterdir():
            if not (f.is_file() and sha(f.read_bytes()) in MODS_PLUGINS_CONNUS.get(f.name.lower(), ())):
                inconnus.append(str(f))
    return inconnus


def lire_etat(jeu, appdata):
    jeu = Path(jeu)
    e = {'exe': (jeu / 'carrier_command.exe').is_file(), 'pe': None, 'dll': {}, 'autres_dll': [], 'ini_jeu': (jeu / 'cc2x.ini').exists(),
         'plugins_dir': [str(p) for p in (jeu / 'cc2x' / 'plugins').glob('*.dll')] if (jeu / 'cc2x' / 'plugins').is_dir() else [],
         'log': (jeu / 'cc2x.log').exists(), 'mods_cc2x': mods_avec_cc2x(appdata),
         'frein_ini': (Path(appdata) / 'Carrier Command 2' / 'cc2x' / 'frein.ini').exists()}
    if e['exe']:
        e['pe'] = pe_de(jeu / 'carrier_command.exe')
    for nom, attendu in SHA.items():
        p = jeu / nom
        if not p.is_file():
            e['dll'][nom] = None
        else:
            s = sha(p.read_bytes())
            e['dll'][nom] = 'nous' if s == attendu else ('ancienne' if s in SHA_ANCIENNES.get(nom, ()) else 'AUTRE')
    e['autres_dll'] = [p.name for p in jeu.glob('cc2x_*.dll') if p.name not in SHA]
    return e


def afficher(e, jeu, appdata):
    print('Dossier du jeu :', os.path.abspath(jeu))
    if not e['exe']:
        print('  carrier_command.exe : ABSENT')
    else:
        ok = e['pe'] in PE_RECONNUS
        print(f'  carrier_command.exe : horodatage PE {e["pe"][0]:#010x}, taille d\'image {e["pe"][1]:#010x} -> '
              f'{"version attendue par le SDK a deux profils" if ok else "AUTRE VERSION : le SDK resterait inactif"}')
    for nom, v in e['dll'].items():
        print(f'  {nom} : ' + {None: 'absent', 'nous': 'present, notre compilation (sha256 conforme)',
                              'ancienne': 'present, notre compilation PRECEDENTE (a mettre a jour avec `maj`)',
                              'AUTRE': 'PRESENT MAIS DIFFERENT de notre compilation'}[v])
    if e['autres_dll']:
        print('  autres cc2x_*.dll dans le dossier du jeu :', ', '.join(e['autres_dll']))
    if e['plugins_dir']:
        print('  DLL dans cc2x\\plugins :', ', '.join(e['plugins_dir']))
    print('  cc2x.ini dans le dossier du jeu :', 'PRESENT (option developpeur lue par le SDK)' if e['ini_jeu'] else 'absent')
    print('  cc2x.log :', 'present' if e['log'] else 'absent')
    print('  mods actifs avec un dossier cc2x :', ', '.join(e['mods_cc2x']) if e['mods_cc2x'] else 'aucun')
    print('  frein.ini (%APPDATA%\\Carrier Command 2\\cc2x) :', 'present' if e['frein_ini'] else 'absent')


def ecrire(chemin, octets, sha_attendu):
    tmp = Path(str(chemin) + '.cc2_tmp')
    try:
        tmp.write_bytes(octets)
        if sha(tmp.read_bytes()) != sha_attendu:
            raise RuntimeError('relecture du fichier temporaire : sha256 different')
        os.replace(tmp, chemin)
    finally:
        if tmp.exists():
            tmp.unlink()
    if sha(Path(chemin).read_bytes()) != sha_attendu:
        raise RuntimeError('le fichier final n\'a pas le sha256 attendu')


def preparer(args):
    jeu = Path(args.jeu)
    if not jeu.is_dir():
        refus(f'{jeu} n\'est pas un dossier')
    if 'steamapps' in os.path.abspath(jeu).lower() and not args.cest_le_vrai_jeu:
        refus("ce chemin ressemble au VRAI jeu (steamapps). Ajouter --cest-le-vrai-jeu pour confirmer que c'est voulu.")
    appdata = args.appdata or os.environ.get('APPDATA')
    if not appdata:
        refus('%APPDATA% introuvable : donner --appdata')
    return jeu, appdata


def verifier_jeu_ferme(jeu):
    o = jeu_ouvert(jeu)
    if o is None:
        refus('impossible de savoir si le jeu tourne : par prudence, rien n\'est fait')
    if o:
        refus('le jeu tourne (carrier_command.exe de ce dossier) : le fermer d\'abord')


def cmd_etat(args):
    jeu, appdata = preparer(args)
    afficher(lire_etat(jeu, appdata), jeu, appdata)
    o = jeu_ouvert(jeu)
    print('  jeu lance :', 'OUI' if o else ('inconnu' if o is None else 'non'))


def cmd_installer(args):
    jeu, appdata = preparer(args)
    srcs = {nom: Path(args.source) if args.source else SOURCES_DEFAUT[nom] for nom in SHA}
    e = lire_etat(jeu, appdata)
    afficher(e, jeu, appdata)
    print()
    for nom, attendu in SHA.items():
        p = srcs[nom] / nom
        if not p.is_file():
            refus(f'{p} introuvable')
        if sha(p.read_bytes()) != attendu:
            refus(f'{p} n\'a pas le sha256 epingle (recompilee ? relancer construire.py et mettre a jour poser.py apres relecture du rapport)')
    if not e['exe']:
        refus('carrier_command.exe absent de ce dossier')
    if e['pe'] not in PE_RECONNUS:
        refus('executable d\'une autre version que celle que le SDK reconnait')
    if any(v is not None for v in e['dll'].values()):
        refus('une de nos DLL (ou une dinput8.dll) est deja la : on ne remplace rien')
    if e['autres_dll'] or e['plugins_dir'] or e['ini_jeu']:
        refus('le dossier contient deja des fichiers que le SDK chargerait ou lirait (autres cc2x_*.dll, cc2x\\plugins, cc2x.ini)')
    if e['mods_cc2x']:
        refus('un mod actif contient un dossier cc2x : sa DLL serait executee par le SDK')
    verifier_jeu_ferme(jeu)
    ini_dir = Path(appdata) / 'Carrier Command 2' / 'cc2x'
    ini = ini_dir / 'frein.ini'
    actions = [f'copier dinput8.dll -> {jeu / "dinput8.dll"}', f'copier cc2x_frein.dll -> {jeu / "cc2x_frein.dll"}']
    if not ini.exists():
        actions.append(f'creer {ini} (copie de frein.ini.example, TOUT ETEINT)')
    print('Actions :\n  ' + '\n  '.join(actions))
    if args.a_blanc:
        print('\n(a blanc : rien n\'a ete ecrit)')
        return
    for nom, attendu in SHA.items():
        ecrire(jeu / nom, (srcs[nom] / nom).read_bytes(), attendu)
    if not ini.exists():
        ini_dir.mkdir(parents=True, exist_ok=True)
        octets = EXEMPLE_INI.read_bytes()
        ecrire(ini, octets, sha(octets))
    print('\nPOSE TERMINEE. Retour arriere : poser.py retirer --jeu ... (jeu ferme).')


def cmd_maj(args):
    """Remplace SEULEMENT cc2x_frein.dll, et seulement si c'est notre compilation precedente (sha256 connu)."""
    jeu, appdata = preparer(args)
    src = Path(args.source) if args.source else SOURCES_DEFAUT['cc2x_frein.dll']
    e = lire_etat(jeu, appdata)
    afficher(e, jeu, appdata)
    print()
    p = src / 'cc2x_frein.dll'
    if not p.is_file():
        refus(f'{p} introuvable')
    if sha(p.read_bytes()) != SHA['cc2x_frein.dll']:
        refus(f'{p} n\'a pas le sha256 epingle (recompilee ? relancer construire.py et mettre a jour poser.py apres relecture du rapport)')
    ancien = Path(jeu) / EXE_ANCIEN[0]
    ancien_ok = ancien.is_file() and sha(ancien.read_bytes()) == EXE_ANCIEN[1] and pe_de(ancien) == PE_ATTENDU
    if not (e['exe'] and e['pe'] in PE_RECONNUS) and not ancien_ok:
        refus('executable absent ou d\'une autre version que celle que le SDK reconnait (et pas de copie exacte de l\'ancien exe a cote)')
    if e['pe'] not in PE_RECONNUS:
        print(f'  (carrier_command.exe est d\'une autre version ; le SDK s\'activera avec {EXE_ANCIEN[0]}, present et conforme)')
    if e['dll']['dinput8.dll'] != 'nous':
        refus('dinput8.dll n\'est pas notre compilation : on ne met rien a jour')
    if e['dll']['cc2x_frein.dll'] == 'nous':
        print('Deja a jour : rien a faire.')
        return
    if e['dll']['cc2x_frein.dll'] != 'ancienne':
        refus('cc2x_frein.dll est absent ou n\'est pas une de nos compilations connues : rien n\'est remplace')
    if e['autres_dll'] or e['plugins_dir'] or e['ini_jeu'] or mods_cc2x_inconnus(e['mods_cc2x']):
        refus('le dossier ou un mod actif contient d\'autres fichiers que le SDK chargerait ou lirait')
    verifier_jeu_ferme(jeu)
    print(f'Action :\n  remplacer {jeu / "cc2x_frein.dll"} (notre version precedente) par la nouvelle ; dinput8.dll, executable et frein.ini inchanges')
    if args.a_blanc:
        print('\n(a blanc : rien n\'a ete ecrit)')
        return
    ecrire(jeu / 'cc2x_frein.dll', p.read_bytes(), SHA['cc2x_frein.dll'])
    print('\nMISE A JOUR TERMINEE. Retour arriere : poser.py retirer --jeu ... (jeu ferme).')


def cmd_retirer(args):
    jeu, appdata = preparer(args)
    e = lire_etat(jeu, appdata)
    afficher(e, jeu, appdata)
    print()
    for nom, v in e['dll'].items():
        if v == 'AUTRE':
            refus(f'{nom} n\'est pas notre compilation : on ne supprime pas un fichier qu\'on n\'a pas pose')
    verifier_jeu_ferme(jeu)
    ini = Path(appdata) / 'Carrier Command 2' / 'cc2x' / 'frein.ini'
    a_supprimer = [jeu / nom for nom, v in e['dll'].items() if v in ('nous', 'ancienne')]
    if args.tout:
        if e['log']:
            a_supprimer.append(jeu / 'cc2x.log')
        if ini.exists() and EXEMPLE_INI.is_file() and ini.read_bytes() == EXEMPLE_INI.read_bytes():
            a_supprimer.append(ini)
        elif ini.exists():
            print('frein.ini a ete modifie : conserve (a supprimer a la main si voulu)')
    if not a_supprimer:
        print('Rien a retirer.')
        return
    print('Suppressions :\n  ' + '\n  '.join(str(p) for p in a_supprimer))
    if args.a_blanc:
        print('\n(a blanc : rien n\'a ete supprime)')
        return
    for p in a_supprimer:
        p.unlink()
    if args.tout:
        d = ini.parent
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    print('\nRETRAIT TERMINE. L\'executable n\'a pas ete touche.')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], allow_abbrev=False)
    ap.add_argument('commande', choices=('etat', 'installer', 'maj', 'retirer'))
    ap.add_argument('--jeu', required=True)
    ap.add_argument('--source', help='dossier des deux DLL (par defaut : SOURCES_DEFAUT, une source par DLL)')
    ap.add_argument('--appdata', help='racine %%APPDATA%% (pour les essais sur un faux dossier)')
    ap.add_argument('--a-blanc', action='store_true')
    ap.add_argument('--tout', action='store_true')
    ap.add_argument('--cest-le-vrai-jeu', action='store_true')
    args = ap.parse_args()
    {'etat': cmd_etat, 'installer': cmd_installer, 'maj': cmd_maj, 'retirer': cmd_retirer}[args.commande](args)


if __name__ == '__main__':
    main()
