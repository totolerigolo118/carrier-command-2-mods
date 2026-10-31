#!/usr/bin/env python3
"""Compile cc2x_hold.dll v2 (plugin CC2X du bouton Hold copie et synchronise) dans un dossier de travail neuf, controle la DLL,
compare ses imports a ceux de la v1, compile et lance le test.

    python -I construire_hold.py                  compile + controles de la DLL + compile le test
    python -I construire_hold.py --lancer-tests   ... et lance le test (programme 32 bits ecrit par nous, sans le jeu)

N'ecrit RIEN dans le dossier du jeu, ni dans %APPDATA%, ni dans le clone du SDK, ni dans plugin_v1 (seulement lu) ;
dans le depot, seulement RAPPORT_compilation.md.
Ne charge ni ne lance la DLL. Compilateur : Zig 0.15.2 (deja installe), memes options que build.py du SDK et que le frein.
Sous-processus : git (lecture du clone), zig, le test. Aucun reseau.
"""
import hashlib
import os
import re
import struct
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
DEPOT = ICI.parents[2]
CLONE = Path(r'C:\Users\UTILISATEUR\Documents\cc2-sdk-tiers\Carrier-Command-2-extender')
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v2')
V1 = Path(r'C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v1\dist\cc2x_hold.dll')   # lue seulement, pour comparer les imports
V1_SHA = 'EE9043DA4773F8360C18BCFE2FF2554FA6A2ECE5D8DA675B96B0E98F2C7F3793'
COMMIT = '7ab05c79357e0cdb5bfaa2866bd3a81a101a09da'
EMPREINTES = DEPOT / 'tour' / 'atterrissage_manuel' / 'SDK_empreintes_7ab05c7.txt'
RAPPORT = ICI / 'RAPPORT_compilation.md'
CFLAGS = ['-target', 'x86-windows-gnu', '-std=c11', '-O2', '-Wall', '-Wextra', '-Wno-unused-parameter',
          '-Werror=implicit-function-declaration', '-fno-strict-aliasing']
INTERDITES = {'ws2_32.dll', 'wsock32.dll', 'wininet.dll', 'winhttp.dll', 'urlmon.dll', 'advapi32.dll', 'user32.dll',
              'shell32.dll', 'ole32.dll', 'oleaut32.dll', 'crypt32.dll', 'iphlpapi.dll', 'netapi32.dll', 'dnsapi.dll',
              'secur32.dll', 'mswsock.dll', 'rasapi32.dll', 'gdi32.dll', 'comdlg32.dll', 'shlwapi.dll', 'psapi.dll', 'wtsapi32.dll'}
MOTS_SUSPECTS = [b'http', b'://', b'socket', b'WSA', b'cmd.exe', b'powershell', b'RegOpen', b'RegSet', b'RegCreate',
                 b'RegDelete', b'RegQuery', b'CreateProcess', b'ShellExecute', b'WinExec', b'URLDownload', b'InternetOpen',
                 b'keybd', b'Clipboard', b'SetWindowsHook', b'WriteProcessMemory', b'CreateFile', b'DeleteFile']
# le code C du plugin ne doit appeler aucune de ces fonctions (VirtualProtect est importe par le code de demarrage du compilateur, comme pour le frein)
INTERDITS_SOURCE = ['VirtualProtect', 'VirtualAlloc', 'WriteProcessMemory', 'CreateFile', 'fopen', 'LoadLibrary', 'GetProcAddress',
                    'CreateThread', 'GetPrivateProfile', 'WritePrivateProfile', 'system(', 'Sleep(']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def arret(msg):
    print('ARRET :', msg)
    sys.exit(1)


def verifier_entrees():
    t = TRAVAIL.resolve()
    for interdit in (DEPOT.resolve(), CLONE.resolve(), Path(r'C:\Program Files (x86)\Steam'), Path(os.environ.get('APPDATA', 'C:\\x'))):
        if t == interdit or interdit in t.parents:
            arret(f'le dossier de travail {t} est dans {interdit}')
    head = subprocess.run(['git', '-C', str(CLONE), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    if head != COMMIT:
        arret(f'le clone est au commit {head}, pas {COMMIT}')
    if subprocess.run(['git', '-C', str(CLONE), 'status', '--porcelain'], capture_output=True, text=True).stdout.strip():
        arret('le clone du SDK a des changements locaux')
    figees = {}
    for ligne in EMPREINTES.read_text(encoding='utf-8').splitlines():
        h, _, nom = ligne.partition('  ')
        figees[nom.strip()] = h.strip()
    if figees.get('include/cc2x.h') != sha(CLONE / 'include' / 'cc2x.h'):
        arret('include/cc2x.h ne correspond pas a l empreinte figee')
    print(f'commit {COMMIT[:7]} et include/cc2x.h conformes aux empreintes figees')


def controler_source():
    texte = (ICI / 'cc2x_hold.c').read_text(encoding='utf-8')
    trouves = [m for m in INTERDITS_SOURCE if m in texte]
    if trouves:
        arret(f'cc2x_hold.c appelle des fonctions interdites : {trouves}')
    print('source : aucune des fonctions interdites (', ', '.join(INTERDITS_SOURCE), ')')


def copier_sources():
    src = TRAVAIL / 'sources'
    for rel, dest in (('include/cc2x.h', src / 'include' / 'cc2x.h'),):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((CLONE / rel).read_bytes())
    (src / 'hold' / 'tests').mkdir(parents=True, exist_ok=True)
    (src / 'hold' / 'cc2x_hold.c').write_bytes((ICI / 'cc2x_hold.c').read_bytes())
    (src / 'hold' / 'tests' / 'test_hold.c').write_bytes((ICI / 'tests' / 'test_hold.c').read_bytes())
    return src


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
    """PE32 minimal : machine, DLL, TLS, exports, imports PAR FONCTION."""
    d = Path(path).read_bytes()
    nt = struct.unpack_from('<I', d, 0x3c)[0]
    assert d[nt:nt + 4] == b'PE\0\0'
    machine, nsec, _ts, _p, _n, opt_size, chars = struct.unpack_from('<HHIIIHH', d, nt + 4)
    opt = nt + 24
    magic = struct.unpack_from('<H', d, opt)[0]
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
    return {'machine': machine, 'pe32': magic == 0x10b, 'dll': bool(chars & 0x2000), 'tls': dirs[9][0] != 0,
            'delay': dirs[13][0] != 0, 'exports': exports, 'imports': imports, 'taille': len(d), 'sha': sha(path)}


def tls_instructions(path):
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
    """Deux DLL identiques sauf l'horodatage PE (4 octets) et la section .buildid."""
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
    chaines = re.findall(rb'[\x20-\x7e]{5,}', Path(path).read_bytes())
    trouves = {}
    for m in MOTS_SUSPECTS:
        hits = [c for c in chaines if m in c]
        if hits:
            trouves[m.decode()] = [h.decode()[:80] for h in hits[:4]]
    return trouves


def controler(path):
    a = analyser(path)
    ok = True
    print(f'\ncc2x_hold.dll : {a["taille"]} octets, sha256 {a["sha"].upper()}')
    print(f'  machine {a["machine"]:#06x} (0x014c = i386), PE32 {a["pe32"]}, DLL {a["dll"]}')
    if a['tls']:
        a['tls_ok'] = tls_instructions(path) == tls_instructions(TRAVAIL / 'control' / 'control.dll') != []
        print('  callbacks TLS :', 'identiques a ceux d une DLL vide (code du compilateur)' if a['tls_ok'] else 'A EXAMINER')
        ok = ok and a['tls_ok']
    print('  exports :', ', '.join(a['exports']))
    if a['machine'] != 0x14c or not a['pe32'] or not a['dll'] or a['delay']:
        print('  ECHEC : pas une DLL 32 bits simple'); ok = False
    if a['exports'] != ['cc2x_plugin_load']:
        print('  ECHEC : exports differents de cc2x_plugin_load'); ok = False
    for dll, fns in a['imports'].items():
        interdit = dll.lower() in INTERDITES
        ok = ok and not interdit
        print(f'  importe {dll} ({len(fns)}){"  INTERDIT" if interdit else ""} : {", ".join(fns)}')
    s = mots_suspects(path)
    print('  chaines suspectes :', 'aucune' if not s else s)
    return a, s, ok and not s


def comparer_v1(a):
    """Imports de la v2 compares a ceux de la v1 (DLL posee le 31/10) : fonctions en plus / en moins, exports identiques ?"""
    if not V1.is_file() or sha(V1).upper() != V1_SHA:
        print('\nv1 introuvable ou differente de EE9043DA... : comparaison impossible')
        return None
    v1 = analyser(V1)
    f1 = {(d.lower(), f) for d, fs in v1['imports'].items() for f in fs}
    f2 = {(d.lower(), f) for d, fs in a['imports'].items() for f in fs}
    plus, moins = sorted(f2 - f1), sorted(f1 - f2)
    print(f'\nimports compares a la v1 (EE9043DA..., {v1["taille"]} octets) :', 'identiques' if not plus and not moins else '')
    for d, f in plus:
        print('  en plus  :', d, f)
    for d, f in moins:
        print('  en moins :', d, f)
    print('  exports :', 'identiques' if v1['exports'] == a['exports'] else 'DIFFERENTS')
    return plus, moins, v1['exports'] == a['exports']


def texte_v1(cmp1):
    if cmp1 is None:
        return 'comparaison impossible (v1 absente)'
    plus, moins, exports = cmp1
    t = 'identiques' if not plus and not moins else 'en plus : %s ; en moins : %s' % (
        ', '.join(f'{d}!{f}' for d, f in plus) or 'rien', ', '.join(f'{d}!{f}' for d, f in moins) or 'rien')
    return t + ('' if exports else ' ; EXPORTS DIFFERENTS')


def rapport(a, s, ok, det, version, test_ok, cmp1):
    L = ['# Rapport de compilation du plugin `cc2x_hold.dll` — genere par `construire_hold.py`', '',
         f'SDK : clone `{COMMIT[:7]}` (seul `include/cc2x.h` est utilise, empreinte figee). Compilateur : Zig {version}. '
         f'Dossier de travail (hors depot, hors jeu) : `{TRAVAIL}`. **Rien n\'a ete charge, lance dans le jeu, ni copie dans le jeu ou %APPDATA%.**', '',
         f'- taille {a["taille"]} octets, sha256 `{a["sha"].upper()}`',
         f'- deuxieme compilation identique (hors horodatage PE et identifiant de build) : {"oui" if det else "NON"}',
         f'- PE32 i386 DLL : {a["machine"] == 0x14c and a["pe32"] and a["dll"]} ; TLS : '
         f'{"present, callbacks identiques a ceux d une DLL vide (code du compilateur)" if a.get("tls_ok") else ("present, A EXAMINER" if a["tls"] else "absent")} ; '
         f'exports : {", ".join(a["exports"])}',
         f'- chaines suspectes : {"aucune" if not s else s}',
         f'- test hors jeu (UBSan, -Werror) : {test_ok}',
         f'- imports compares a la v1 (`EE9043DA…`) : {texte_v1(cmp1)}',
         f'- verdict automatique : {"OK" if ok and det else "A EXAMINER"}', '', '| DLL importee | fonctions |', '|---|---|']
    for dll, fns in a['imports'].items():
        L.append(f'| {dll} | {", ".join(fns)} |')
    RAPPORT.write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('\nrapport ecrit :', RAPPORT)


def main():
    lancer = '--lancer-tests' in sys.argv
    verifier_entrees()
    controler_source()
    for sous in ('sources', 'dist', 'dist_verif', 'test', 'cache', 'cache_local', 'control'):
        (TRAVAIL / sous).mkdir(parents=True, exist_ok=True)
    src = copier_sources()
    (TRAVAIL / 'control' / 'control.c').write_text('int cc2x_control(void) { return 0; }\n', encoding='ascii')
    version = subprocess.run([sys.executable, '-m', 'ziglang', 'version'], capture_output=True, text=True).stdout.strip()
    print('\ncompilation (Zig', version + ')')
    zig(['-shared', TRAVAIL / 'control' / 'control.c', '-o', TRAVAIL / 'control' / 'control.dll'])
    nettoyer(TRAVAIL / 'control')
    for sortie in ('dist', 'dist_verif'):
        zig(['-shared', '-I', src / 'include', src / 'hold' / 'cc2x_hold.c', '-o', TRAVAIL / sortie / 'cc2x_hold.dll'])
        nettoyer(TRAVAIL / sortie)
    a, s, ok = controler(TRAVAIL / 'dist' / 'cc2x_hold.dll')
    cmp1 = comparer_v1(a)
    det = egal_hors_horodatage(TRAVAIL / 'dist' / 'cc2x_hold.dll', TRAVAIL / 'dist_verif' / 'cc2x_hold.dll')
    print('  deuxieme compilation identique (hors horodatage PE et identifiant de build) :', 'oui' if det else 'NON')
    (TRAVAIL / 'dist' / 'SHA256.txt').write_text(f'{a["sha"].upper()}  cc2x_hold.dll\n', encoding='ascii')
    print('\ncompilation du test (UBSan, -Werror)')
    test = TRAVAIL / 'test' / 'test_hold.exe'
    zig(['-fsanitize=undefined', '-Werror', '-I', src / 'include', src / 'hold' / 'tests' / 'test_hold.c', '-o', test])
    nettoyer(TRAVAIL / 'test')
    test_ok = 'compile, non lance'
    tout_ok = ok and det
    if lancer:
        print('\nlancement du test (programme 32 bits ecrit par nous ; il ne charge aucune DLL ; il n ecrit aucun fichier)')
        r = subprocess.run([str(test)], cwd=TRAVAIL / 'test')
        test_ok = 'tous les controles passent' if r.returncode == 0 else f'ECHEC (code {r.returncode})'
        tout_ok = tout_ok and r.returncode == 0
    rapport(a, s, ok, det, version, test_ok, cmp1)
    print('\nRESULTAT :', 'tout est conforme' if tout_ok else 'A EXAMINER (voir ci-dessus)')
    sys.exit(0 if tout_ok else 1)


if __name__ == '__main__':
    main()
