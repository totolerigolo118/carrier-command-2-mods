#!/usr/bin/env python3
"""PARTIE 2 : fabrique, HORS DU JEU, une COPIE du SDK CC2X (commit fige 7ab05c7, version 0.5.0) avec un 2e profil pour le
nouvel exe de Steam, la compile avec la MEME chaine que construire.py (Zig 0.15.2, memes options que build.py du SDK), et controle.

  - le clone du SDK (cc2-sdk-tiers) est seulement LU : commit et empreintes verifies (fonctions de construire.py) ;
  - on compile d'abord les sources INCHANGEES et on compare au dinput8.dll du jeu (184B144D...) : si elles sont identiques
    hors horodatage et identifiant de build, la chaine est la meme que celle de nos compilations existantes ;
  - on ajoute le 2e profil (cc2x.c : Profile ; world.c : Layout) avec les valeurs de analyse/profil_sdk_valeurs.json ;
    le profil de l'ancien exe reste TEL QUEL ;
  - on compile deux fois (determinisme) et on controle les imports / chaines suspectes comme construire.py ;
  - RIEN n'est ecrit dans le dossier du jeu, dans le clone du SDK, ni dans le depot (hors le diff et le rapport).
  - AUCUNE DLL n'est chargee ni posee.

Usage : python -I -B fabriquer_sdk_nouvel_exe.py <valeurs.json> <dossier_de_travail_hors_depot> <sortie.diff> <rapport.md>
"""
import difflib
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
CONSTRUIRE = ICI.parents[1] / 'atterrissage_manuel' / 'frein' / 'construire.py'
BUILD_NOUVEAU = '1.5.18-win32-6ae228f3'
TIMESTAMP_NOUVEAU = 0x6ae228f3
DLL_DU_JEU = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2\dinput8.dll')
SHA_DLL_DU_JEU = '184B144D6E2BB868FFEB7D45ECD463F8919E64732E3B5681A16165363EBA0982'


def charger_construire(travail):
    spec = importlib.util.spec_from_file_location('construire_ref', CONSTRUIRE)
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    c.TRAVAIL = travail          # les fonctions de construire.py lisent ce nom global : elles travaillent chez nous
    return c


def h(n):
    return '0x%08x' % n


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    val = json.load(open(sys.argv[1], encoding='utf-8'))['valeurs']
    travail = Path(sys.argv[2]).resolve()
    p_diff, p_md = Path(sys.argv[3]), Path(sys.argv[4])
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'      # `git status` sur le clone ne doit rien ecrire (pas de rafraichissement de l'index)
    C = charger_construire(travail)
    for interdit in (Path(r'C:\Program Files (x86)\Steam').resolve(), C.CLONE.resolve(), C.DEPOT.resolve()):
        if travail == interdit or interdit in travail.parents:
            sys.exit('ARRET : le dossier de travail est dans %s' % interdit)
    C.verifier_entrees()
    for sous in ('sources_ref', 'sources_nouveau', 'dist_ref', 'dist', 'dist_verif', 'cache', 'cache_local', 'control'):
        (travail / sous).mkdir(parents=True, exist_ok=True)
    for f in C.FICHIERS_SDK:
        for dossier in ('sources_ref', 'sources_nouveau'):
            dest = travail / dossier / f
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((C.CLONE / f).read_bytes())
    print('sources copiees (deux jeux identiques, empreintes du clone verifiees)')

    # ------------------------------------------------------------ le 2e profil
    p_c = travail / 'sources_nouveau' / 'src' / 'cc2x.c'
    p_w = travail / 'sources_nouveau' / 'src' / 'world.c'
    c_txt = p_c.read_bytes().decode('utf-8')
    w_txt = p_w.read_bytes().decode('utf-8')
    nl = '\r\n' if '\r\n' in c_txt else '\n'
    c_txt, w_txt = c_txt.replace('\r\n', '\n'), w_txt.replace('\r\n', '\n')
    c_orig, w_orig = c_txt, w_txt

    v = {k: d['nouveau'] for k, d in val.items()}
    ancien_bloc = '''    "1.5.18-win32", 0x6a36c177, 0x00af7000,
    0x00d34bc4, 0x00772fd0, 0x0077ee10, 0x0077eea0,
    0x004465ec, {0x6a, 0x20, 0x89, 0x85, 0x64, 0xff, 0xff, 0xff},
    0x008cda70, 0x008ce200, 0x008ff6b0, 0x00908220, 0x00904a50, 0x00904050, 0x00d03518,
}};
'''
    assert c_txt.count(ancien_bloc) == 1, 'bloc Profile inattendu dans cc2x.c'
    nouveau_bloc = '''    "1.5.18-win32", 0x6a36c177, 0x00af7000,
    0x00d34bc4, 0x00772fd0, 0x0077ee10, 0x0077eea0,
    0x004465ec, {0x6a, 0x20, 0x89, 0x85, 0x64, 0xff, 0xff, 0xff},
    0x008cda70, 0x008ce200, 0x008ff6b0, 0x00908220, 0x00904a50, 0x00904050, 0x00d03518,
}, {
    /* Steam build of 2026-10-28 (build 26277078; the game still says v1.5.18; PE timestamp 0x6ae228f3, same SizeOfImage).
     * Every address found again by its disassembled context and checked against LUA_SIGS / lua_site_bytes;
     * the build string differs on purpose: plugins that only know "1.5.18-win32" refuse to load on this build. */
    "%s", 0x6ae228f3, 0x00af7000,
    %s, %s, %s, %s,
    %s, {0x6a, 0x20, 0x89, 0x85, 0x64, 0xff, 0xff, 0xff},
    %s, %s, %s, %s, %s, %s, %s,
}};
''' % (BUILD_NOUVEAU, h(v['server_vtable']), h(v['server_init']), h(v['server_tick']), h(v['server_end']), h(v['lua_site']),
       h(v['f_index2addr']), h(v['f_auxsetstr']), h(v['f_finishset']), h(v['f_luaS_new']), h(v['f_luaH_new']), h(v['f_luaC_step']),
       h(v['nilobject']))
    c_txt = c_txt.replace(ancien_bloc, nouveau_bloc)

    # world.c : un 2e Layout = copie du 1er avec les adresses du jeu remplacees (les decalages d'objets restent ceux du source)
    a = w_txt.index('static const Layout LAYOUTS[] = {{')
    b = w_txt.index('}};', a)
    corps = w_txt[a + len('static const Layout LAYOUTS[] = {{'):b]
    copie = corps
    remplacements = [
        ('.build = "1.5.18-win32"', '.build = "%s"' % BUILD_NOUVEAU),
        ('.f_vehicle_by_id = 0x005ee6a0', '.f_vehicle_by_id = ' + h(v['f_vehicle_by_id'])),
        ('.f_tile_by_id = 0x00631240', '.f_tile_by_id = ' + h(v['f_tile_by_id'])),
        ('.f_tile_at = 0x00631040', '.f_tile_at = ' + h(v['f_tile_at'])),
        ('.f_request_landing = 0x0062b4a0', '.f_request_landing = ' + h(v['f_request_landing'])),
        ('.f_waypoints_clear = 0x00854870', '.f_waypoints_clear = ' + h(v['f_waypoints_clear'])),
        ('.f_deque_grow = 0x00860c90', '.f_deque_grow = ' + h(v['f_deque_grow'])),
        ('.vt_rigid_dynamic = 0x00cdd478', '.vt_rigid_dynamic = ' + h(v['vt_rigid_dynamic'])),
        ('.h_waypoints = 0x007781d4', '.h_waypoints = ' + h(v['h_waypoints'])),
        ('.h_hangar = 0x0062ae8d', '.h_hangar = ' + h(v['h_hangar'])),
        ('.h_hangar_found = 0x0062aefc', '.h_hangar_found = ' + h(v['h_hangar_found'])),
        ('.h_hangar_none = 0x0062aead', '.h_hangar_none = ' + h(v['h_hangar_none'])),
        ('.h_controller = {0x0063014f, 0x00634981}', '.h_controller = {%s, %s}' % (h(v['h_controller[0]']), h(v['h_controller[1]']))),
        ('.h_spawn = 0x00634f3d', '.h_spawn = ' + h(v['h_spawn'])),
        ('.f_spawn = 0x0062ca30', '.f_spawn = ' + h(v['f_spawn'])),
        ('.h_af_tick = 0x0062b8f3', '.h_af_tick = ' + h(v['h_af_tick'])),
        ('.f_af_tick = 0x00628600', '.f_af_tick = ' + h(v['f_af_tick'])),
    ]
    for ancien, nouveau in remplacements:
        assert corps.count(ancien) == 1, 'motif attendu une fois dans world.c : ' + ancien
        copie = copie.replace(ancien, nouveau)
    w_txt = w_txt[:b] + '}, {' + copie + w_txt[b:]
    # les decalages de champs ne sont PAS modifies : memes valeurs dans les deux Layout (controle)
    assert w_txt.count('.v_dock_state = 0x174') == 2 and w_txt.count('.v_flight_state = 0x170') == 2

    p_c.write_bytes(c_txt.replace('\n', nl).encode('utf-8'))
    p_w.write_bytes(w_txt.replace('\n', nl).encode('utf-8'))

    # le diff (seule chose copiee dans le depot)
    diff = []
    for nom, avant, apres in (('src/cc2x.c', c_orig, c_txt), ('src/world.c', w_orig, w_txt)):
        diff += list(difflib.unified_diff(avant.splitlines(True), apres.splitlines(True), 'a/' + nom, 'b/' + nom, n=3))
    p_diff.write_text(''.join(diff), encoding='utf-8')
    print('diff ecrit :', p_diff, '(%d lignes)' % len(diff))

    # ------------------------------------------------------------ compilation
    zv = subprocess.run([sys.executable, '-m', 'ziglang', 'version'], capture_output=True, text=True).stdout.strip()
    print('compilation (Zig %s)' % zv)
    (travail / 'control' / 'control.c').write_text('int cc2x_control(void) { return 0; }\n', encoding='ascii')
    C.zig(['-shared', travail / 'control' / 'control.c', '-o', travail / 'control' / 'control.dll'])
    C.nettoyer(travail / 'control')

    def compiler(src, out):
        C.zig(['-shared', '-I', src / 'include', src / 'src' / 'cc2x.c', src / 'src' / 'world.c', src / 'src' / 'lua_world.c',
               src / 'src' / 'dinput8.def', '-o', out / 'dinput8.dll'])
        C.nettoyer(out)

    compiler(travail / 'sources_ref', travail / 'dist_ref')
    compiler(travail / 'sources_nouveau', travail / 'dist')
    compiler(travail / 'sources_nouveau', travail / 'dist_verif')

    # ------------------------------------------------------------ controles
    L = ['# Rapport de compilation du SDK avec le 2e profil (partie 2) — genere par `fabriquer_sdk_nouvel_exe.py`', '',
         'Commit du SDK : `%s` (CC2X 0.5.0). Compilateur : Zig %s, memes options que `build.py` du SDK et que `construire.py`. '
         'Dossier de travail (hors depot, hors jeu) : `%s`. **Aucune DLL chargee, lancee ni posee.**' % (C.COMMIT, zv, travail), '']
    ok_total = True
    # 1. la chaine : sources inchangees -> meme DLL que celle du jeu ?
    ref = travail / 'dist_ref' / 'dinput8.dll'
    sha_ref = hashlib.sha256(ref.read_bytes()).hexdigest().upper()
    dll_jeu_ok = DLL_DU_JEU.is_file() and hashlib.sha256(DLL_DU_JEU.read_bytes()).hexdigest().upper() == SHA_DLL_DU_JEU
    egal_jeu = dll_jeu_ok and C.egal_hors_horodatage(ref, DLL_DU_JEU)
    L += ['## 1. La chaine de compilation est-elle la meme ?', '',
          '- sources INCHANGEES recompilees ici : `%s` (%d octets)' % (sha_ref, ref.stat().st_size),
          '- `dinput8.dll` du jeu (LECTURE seule) : %s' % ('`%s` (somme attendue)' % SHA_DLL_DU_JEU if dll_jeu_ok else 'ABSENTE ou somme differente'),
          '- identiques hors horodatage PE et identifiant de build : **%s**' % ('OUI' if egal_jeu else 'NON'), '']
    print('chaine : sources inchangees == dinput8.dll du jeu hors horodatage/build-id :', egal_jeu)
    ok_total = ok_total and egal_jeu

    # 2. la DLL avec le 2e profil
    a, s, ok = C.controler(travail / 'dist' / 'dinput8.dll', 'dinput8.dll')
    det = C.egal_hors_horodatage(travail / 'dist' / 'dinput8.dll', travail / 'dist_verif' / 'dinput8.dll')
    print('deuxieme compilation identique (hors horodatage PE et identifiant de build) :', det)
    ok_total = ok_total and ok and det
    L += ['## 2. DLL avec les deux profils', '', '- taille %d octets, sha256 `%s`' % (a['taille'], a['sha'].upper()),
          '- deuxieme compilation identique hors horodatage PE et identifiant de build : **%s**' % ('oui' if det else 'NON'),
          '- PE32 i386 DLL : %s ; TLS : %s ; imports retardes : %s ; exports : %s' % (
              a['machine'] == 0x14c and a['pe32'] and a['dll'], 'present' if a['tls'] else 'absent', 'presents' if a['delay'] else 'absents',
              ', '.join(a['exports'])),
          '- chaines suspectes : %s' % ('aucune' if not s else s), '- verdict automatique : **%s**' % ('OK' if ok else 'A EXAMINER'), '',
          '| DLL importee | fonctions |', '|---|---|']
    ref_imp = C.analyser(DLL_DU_JEU)['imports'] if dll_jeu_ok else {}
    for dll, fns in a['imports'].items():
        L.append('| %s | %s |' % (dll, ', '.join(fns)))
    memes_imports = ref_imp == a['imports']
    L += ['', '- imports identiques a ceux de la DLL du jeu (184B144D...) : **%s**' % ('OUI' if memes_imports else 'NON : A EXAMINER'), '']
    ok_total = ok_total and memes_imports
    p_md.write_text('\n'.join(L), encoding='utf-8')
    print('rapport ecrit :', p_md)
    print('RESULTAT :', 'tout est conforme' if ok_total else 'A EXAMINER')
    return 0 if ok_total else 1


if __name__ == '__main__':
    sys.exit(main())
