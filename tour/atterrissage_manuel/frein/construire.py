#!/usr/bin/env python3
"""Etape 3 : compile dinput8.dll (SDK CC2X, commit fige) et cc2x_frein.dll dans un dossier de travail.

    python -I construire.py                  compile + controle des DLL + compile le test
    python -I construire.py --lancer-tests   ... et lance le test (programme 32 bits ecrit par nous, sans le jeu)

N'ecrit RIEN dans le dossier du jeu, ni dans le clone du SDK, ni dans le depot (hors le rapport texte).
Ne charge ni ne lance aucune des deux DLL. Le compilateur est Zig 0.15.2 (pip install ziglang==0.15.2).
"""
import hashlib
import os
import re
import struct
import subprocess
import sys
from pathlib import Path

FREIN = Path(__file__).resolve().parent
DEPOT = FREIN.parents[2]
CLONE = Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-tiers\Carrier-Command-2-extender')
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-travail')
COMMIT = '7ab05c79357e0cdb5bfaa2866bd3a81a101a09da'
EMPREINTES = FREIN.parent / 'SDK_empreintes_7ab05c7.txt'
RAPPORT = FREIN / 'RAPPORT_compilation.md'
FICHIERS_SDK = ['include/cc2x.h', 'src/cc2x.c', 'src/world.c', 'src/lua_world.c', 'src/internal.h', 'src/dinput8.def']
# memes options que build.py du SDK (ligne 23-24)
CFLAGS = ['-target', 'x86-windows-gnu', '-std=c11', '-O2', '-Wall', '-Wextra', '-Wno-unused-parameter',
          '-Werror=implicit-function-declaration', '-fno-strict-aliasing']
INTERDITES = {'ws2_32.dll', 'wsock32.dll', 'wininet.dll', 'winhttp.dll', 'urlmon.dll', 'advapi32.dll', 'user32.dll',
              'shell32.dll', 'ole32.dll', 'oleaut32.dll', 'crypt32.dll', 'iphlpapi.dll', 'netapi32.dll', 'dnsapi.dll',
              'secur32.dll', 'mswsock.dll', 'rasapi32.dll', 'gdi32.dll', 'comdlg32.dll', 'shlwapi.dll', 'psapi.dll', 'wtsapi32.dll'}
MOTS_SUSPECTS = [b'http', b'://', b'socket', b'WSA', b'cmd.exe', b'powershell', b'RegOpen', b'RegSet', b'RegCreate',
                 b'RegDelete', b'RegQuery', b'CreateProcess', b'ShellExecute', b'WinExec', b'URLDownload', b'InternetOpen',
                 b'keybd', b'Clipboard', b'SetWindowsHook', b'WriteProcessMemory']
EXPORTS_ATTENDUS = {'dinput8.dll': {'DirectInput8Create', 'DllCanUnloadNow', 'DllGetClassObject', 'DllRegisterServer',
                                    'DllUnregisterServer'},
                    'cc2x_frein.dll': {'cc2x_plugin_load'}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def arret(msg):
    print('ARRET :', msg)
    sys.exit(1)


def verifier_entrees():
    t = TRAVAIL.resolve()
    for interdit in (DEPOT.resolve(), CLONE.resolve(), Path(r'C:\Program Files (x86)\Steam')):
        if t == interdit or interdit in t.parents:
            arret(f'le dossier de travail {t} est dans {interdit}')
    head = subprocess.run(['git', '-C', str(CLONE), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    if head != COMMIT:
        arret(f'le clone est au commit {head}, pas {COMMIT}')
    sale = subprocess.run(['git', '-C', str(CLONE), 'status', '--porcelain'], capture_output=True, text=True).stdout.strip()
    if sale:
        arret('le clone du SDK a des changements locaux :\n' + sale)
    figees = {}
    for ligne in EMPREINTES.read_text(encoding='utf-8').splitlines():
        h, _, nom = ligne.partition('  ')
        figees[nom.strip()] = h.strip()
    for f in FICHIERS_SDK:
        if figees.get(f) != sha(CLONE / f):
            arret(f'{f} ne correspond pas a l\'empreinte figee')
    print(f'commit {COMMIT[:7]} et {len(FICHIERS_SDK)} fichiers du SDK conformes aux empreintes figees')


def copier_sources():
    for f in FICHIERS_SDK:
        dest = TRAVAIL / 'sources' / f
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((CLONE / f).read_bytes())
        if sha(dest) != sha(CLONE / f):
            arret(f'copie de {f} differente')
    (TRAVAIL / 'sources' / 'frein').mkdir(exist_ok=True)
    (TRAVAIL / 'sources' / 'frein' / 'cc2x_frein.c').write_bytes((FREIN / 'cc2x_frein.c').read_bytes())
    (TRAVAIL / 'sources' / 'frein' / 'tests').mkdir(exist_ok=True)
    (TRAVAIL / 'sources' / 'frein' / 'tests' / 'test_frein.c').write_bytes((FREIN / 'tests' / 'test_frein.c').read_bytes())


def zig(args):
    env = dict(os.environ)
    env['ZIG_GLOBAL_CACHE_DIR'] = str(TRAVAIL / 'cache')
    env['ZIG_LOCAL_CACHE_DIR'] = str(TRAVAIL / 'cache_local')
    cmd = [sys.executable, '-m', 'ziglang', 'cc', *CFLAGS, *[str(a) for a in args]]
    print('  zig cc', ' '.join(Path(str(a)).name if ('\\' in str(a) or '/' in str(a)) else str(a) for a in args))
    r = subprocess.run(cmd, cwd=TRAVAIL, env=env, capture_output=True, text=True)
    if r.stdout.strip() or r.stderr.strip():
        print((r.stdout + r.stderr).strip())
    if r.returncode:
        arret('la compilation a echoue')


def nettoyer(dossier):
    for j in list(dossier.glob('*.lib')) + list(dossier.glob('*.pdb')):
        j.unlink()


def analyser(path):
    """PE32 minimal : machine, DLL, point d'entree, TLS, exports, imports PAR FONCTION, sections."""
    d = Path(path).read_bytes()
    nt = struct.unpack_from('<I', d, 0x3c)[0]
    assert d[nt:nt + 4] == b'PE\0\0'
    machine, nsec, _ts, _p, _n, opt_size, chars = struct.unpack_from('<HHIIIHH', d, nt + 4)
    opt = nt + 24
    magic = struct.unpack_from('<H', d, opt)[0]
    entry = struct.unpack_from('<I', d, opt + 16)[0]
    sec0 = opt + opt_size
    sections = []
    for i in range(nsec):
        nom, vs, va, rs, rp = struct.unpack_from('<8sIIII', d, sec0 + 40 * i)
        sections.append((nom.rstrip(b'\0').decode(), va, max(vs, rs), rp))

    def off(r):
        for _, va, size, rp in sections:
            if va <= r < va + size:
                return rp + (r - va)
        raise ValueError(hex(r))

    def cstr(o):
        return d[o:d.index(b'\0', o)].decode('ascii', 'replace')

    dd = opt + 96
    dirs = [struct.unpack_from('<II', d, dd + 8 * i) for i in range(16)]
    exports, imports = [], {}
    if dirs[0][0]:
        e = off(dirs[0][0])
        nn = struct.unpack_from('<I', d, e + 24)[0]
        names = struct.unpack_from('<I', d, e + 32)[0]
        exports = [cstr(off(struct.unpack_from('<I', d, off(names) + 4 * i)[0])) for i in range(nn)]
    if dirs[1][0]:
        p = off(dirs[1][0])
        while True:
            oft, _t, _f, name, ft = struct.unpack_from('<IIIII', d, p)
            if not any((oft, name, ft)):
                break
            fonctions = []
            th = off(oft or ft)
            while True:
                v = struct.unpack_from('<I', d, th)[0]
                if not v:
                    break
                fonctions.append(f'#{v & 0xffff}' if v & 0x80000000 else cstr(off(v) + 2))
                th += 4
            imports[cstr(off(name))] = fonctions
            p += 20
    return {'machine': machine, 'pe32': magic == 0x10b, 'dll': bool(chars & 0x2000), 'entry': entry, 'tls': dirs[9][0] != 0,
            'delay': dirs[13][0] != 0, 'bound': dirs[11][0] != 0, 'exports': exports, 'imports': imports,
            'sections': [s[0] for s in sections], 'taille': len(d), 'sha': sha(path)}


def tls_instructions(path):
    """Instructions (mnemoniques) des callbacks TLS d'une DLL, pour les comparer a celles d'une DLL vide."""
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    d = Path(path).read_bytes()
    nt = struct.unpack_from('<I', d, 0x3c)[0]
    nsec = struct.unpack_from('<H', d, nt + 6)[0]
    opt_size = struct.unpack_from('<H', d, nt + 20)[0]
    opt = nt + 24
    base = struct.unpack_from('<I', d, opt + 28)[0]
    secs = [struct.unpack_from('<8sIIII', d, opt + opt_size + 40 * i) for i in range(nsec)]

    def off(rva):
        for _n, vs, va, rs, rp in secs:
            if va <= rva < va + max(vs, rs):
                return rp + rva - va

    tls_rva = struct.unpack_from('<II', d, opt + 96 + 9 * 8)[0]
    if not tls_rva:
        return []
    cb = struct.unpack_from('<6I', d, off(tls_rva))[3]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    p, out = off(cb - base), []
    while struct.unpack_from('<I', d, p)[0]:
        c = struct.unpack_from('<I', d, p)[0]
        o = off(c - base)
        seq = []
        for ins in md.disasm(d[o:o + 120], c):
            seq.append(ins.mnemonic)
            if ins.mnemonic == 'ret' and len(seq) > 3:
                break
        out.append(seq)
        p += 4
    return out


def egal_hors_horodatage(a, b):
    """Deux DLL identiques sauf l'horodatage PE (4 octets) et l'identifiant de build (section .buildid, 16 octets)."""
    x, y = bytearray(Path(a).read_bytes()), bytearray(Path(b).read_bytes())
    if len(x) != len(y):
        return False
    nt = struct.unpack_from('<I', x, 0x3c)[0]
    x[nt + 8:nt + 12] = y[nt + 8:nt + 12] = b'\0\0\0\0'
    nsec = struct.unpack_from('<H', x, nt + 6)[0]
    opt_size = struct.unpack_from('<H', x, nt + 20)[0]
    for i in range(nsec):
        nom, _vs, _va, rs, rp = struct.unpack_from('<8sIIII', x, nt + 24 + opt_size + 40 * i)
        if nom.rstrip(b'\0') == b'.buildid':
            x[rp:rp + rs] = y[rp:rp + rs] = b'\0' * rs
    return x == y


def mots_suspects(path):
    d = Path(path).read_bytes()
    chaines = re.findall(rb'[\x20-\x7e]{5,}', d)
    trouves = {}
    for m in MOTS_SUSPECTS:
        hits = [c for c in chaines if m in c]
        if hits:
            trouves[m.decode()] = [h.decode()[:80] for h in hits[:4]]
    return trouves


def controler(path, nom):
    a = analyser(path)
    ok = True
    print(f'\n{nom} : {a["taille"]} octets, sha256 {a["sha"].upper()}')
    print(f'  machine {a["machine"]:#06x} (0x014c = i386), PE32 {a["pe32"]}, DLL {a["dll"]}, point d\'entree {a["entry"]:#x}, sections {", ".join(a["sections"])}')
    print(f'  repertoire TLS : {"PRESENT" if a["tls"] else "absent"} ; imports retardes : {"PRESENT" if a["delay"] else "absent"}')
    if a['tls']:
        ref = tls_instructions(TRAVAIL / 'control' / 'control.dll')
        mine = tls_instructions(path)
        a['tls_ok'] = bool(ref) and ref == mine
        print(f'  callbacks TLS : {len(mine)}, {"IDENTIQUES a ceux d une DLL vide compilee pareil (code du compilateur, pas le notre)" if a["tls_ok"] else "DIFFERENTS de ceux d une DLL vide : A EXAMINER"}')
        ok = ok and a['tls_ok']
    print('  exports :', ', '.join(a['exports']))
    if a['machine'] != 0x14c or not a['pe32'] or not a['dll']:
        print('  ECHEC : pas une DLL 32 bits'); ok = False
    if a['delay']:
        print('  A EXAMINER : imports retardes'); ok = False
    if set(a['exports']) != EXPORTS_ATTENDUS[nom]:
        print('  ECHEC : exports differents de', sorted(EXPORTS_ATTENDUS[nom])); ok = False
    for dll, fns in a['imports'].items():
        marque = '  INTERDIT' if dll.lower() in INTERDITES else ''
        if marque:
            ok = False
        print(f'  importe {dll} ({len(fns)}){marque} : {", ".join(fns)}')
    s = mots_suspects(path)
    print('  chaines suspectes :', 'aucune' if not s else s)
    if s:
        ok = False
    return a, s, ok


def rapport(res, flags_zig):
    L = ['# Rapport de compilation (etape 3) — genere par `construire.py`', '',
         f'Commit du SDK : `{COMMIT}`. Compilateur : Zig {flags_zig}. Dossier de travail (hors depot, hors jeu) : `{TRAVAIL}`. '
         'Options = celles de `build.py` du SDK. **Rien n\'a ete charge ni lance (les deux DLL), rien copie dans le jeu.**', '']
    for nom, (a, s, ok, deterministe) in res.items():
        L += [f'## {nom}', '', f'- taille {a["taille"]} octets, sha256 `{a["sha"].upper()}`',
              f'- deuxieme compilation identique, hors horodatage PE et identifiant de build (20 octets) : {"oui" if deterministe else "NON"}',
              f'- PE32 i386 DLL : {a["machine"] == 0x14c and a["pe32"] and a["dll"]} ; TLS : '
              f'{"present, callbacks identiques a ceux d une DLL vide (code du compilateur)" if a.get("tls_ok") else ("present, A EXAMINER" if a["tls"] else "absent")} ; '
              f'imports retardes : {"presents" if a["delay"] else "absents"}; exports : {", ".join(a["exports"])}',
              f'- chaines suspectes : {"aucune" if not s else s}', f'- verdict automatique : {"OK" if ok else "A EXAMINER"}', '',
              '| DLL importee | fonctions |', '|---|---|']
        for dll, fns in a['imports'].items():
            L.append(f'| {dll} | {", ".join(fns)} |')
        L.append('')
    RAPPORT.write_text('\n'.join(L), encoding='utf-8')
    print('\nrapport ecrit :', RAPPORT)


def main():
    lancer = '--lancer-tests' in sys.argv
    verifier_entrees()
    for sous in ('sources', 'dist', 'dist_verif', 'test', 'cache', 'cache_local', 'reglages', 'control'):
        (TRAVAIL / sous).mkdir(parents=True, exist_ok=True)
    copier_sources()
    (TRAVAIL / 'control' / 'control.c').write_text('int cc2x_control(void) { return 0; }\n', encoding='ascii')   # DLL vide : temoin du code du compilateur
    src = TRAVAIL / 'sources'
    version = subprocess.run([sys.executable, '-m', 'ziglang', 'version'], capture_output=True, text=True).stdout.strip()
    print('\ncompilation (Zig', version + ')')
    zig(['-shared', TRAVAIL / 'control' / 'control.c', '-o', TRAVAIL / 'control' / 'control.dll'])
    nettoyer(TRAVAIL / 'control')
    for sortie in ('dist', 'dist_verif'):
        out = TRAVAIL / sortie
        zig(['-shared', '-I', src / 'include', src / 'src' / 'cc2x.c', src / 'src' / 'world.c', src / 'src' / 'lua_world.c',
             src / 'src' / 'dinput8.def', '-o', out / 'dinput8.dll'])
        zig(['-shared', '-I', src / 'include', src / 'frein' / 'cc2x_frein.c', '-o', out / 'cc2x_frein.dll'])
        nettoyer(out)
    res, tout_ok = {}, True
    for nom in ('dinput8.dll', 'cc2x_frein.dll'):
        a, s, ok = controler(TRAVAIL / 'dist' / nom, nom)
        det = egal_hors_horodatage(TRAVAIL / 'dist' / nom, TRAVAIL / 'dist_verif' / nom)
        print(f'  deuxieme compilation identique (hors horodatage PE et identifiant de build, 20 octets) : {"oui" if det else "NON"}')
        tout_ok = tout_ok and det
        res[nom] = (a, s, ok, det)
        tout_ok = tout_ok and ok
    rapport(res, version)
    print('\ncompilation du test (UBSan, -Werror)')
    test = TRAVAIL / 'test' / 'test_frein.exe'
    zig(['-fsanitize=undefined', '-Werror', '-I', src / 'include', src / 'frein' / 'tests' / 'test_frein.c', '-o', test])
    nettoyer(TRAVAIL / 'test')
    if lancer:
        print('\nlancement du test (programme 32 bits ecrit par nous ; il ne charge aucune DLL du SDK ; ecrit seulement dans', TRAVAIL / 'reglages', ')')
        r = subprocess.run([str(test), str(TRAVAIL / 'reglages')], cwd=TRAVAIL / 'test')
        tout_ok = tout_ok and r.returncode == 0
    print('\nRESULTAT :', 'tout est conforme' if tout_ok else 'A EXAMINER (voir ci-dessus)')
    sys.exit(0 if tout_ok else 1)


if __name__ == '__main__':
    main()
