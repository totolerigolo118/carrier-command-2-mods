#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build cc2x_cc2_patchs.dll (32-bit Windows plugin for CC2X) with Zig used as a C compiler.

    python build.py                     -> dist/cc2x_cc2_patchs.dll
    python build.py --zig PATH          use this zig executable (or set CC2X_ZIG)
    python build.py --sdk DIR           folder that holds cc2x.h (default: auto-detected)

Compiler lookup, first hit wins: --zig, $CC2X_ZIG, `zig` on the PATH, `python -m ziglang`
(pip install ziglang==0.15.2). Same flags as the SDK's own build.py. The output is checked afterwards
(PE32 / i386 / DLL, export cc2x_plugin_load, imported DLLs are listed). The .dll is ignored by git.
"""
import argparse
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ['cc2_patchs.c', 'cp_config.c', 'cp_groups.c', 'cp_hook.c', 'cp_hooks.c', 'cp_ini.c',
           'cp_patch.c', 'cp_pe.c', 'cp_speed.c', 'cp_tunables.c', 'cp_win.c']
CFLAGS = ['-target', 'x86-windows-gnu', '-std=c11', '-O2', '-Wall', '-Wextra', '-Wno-unused-parameter',
          '-Werror=implicit-function-declaration', '-fno-strict-aliasing']
OUT_NAME = 'cc2x_cc2_patchs.dll'


def find_sdk(arg):
    candidates = [Path(arg)] if arg else [ROOT / 'include', ROOT.parent / 'passation_windows' / 'sdk_public_cc2x']
    for c in candidates:
        if (c / 'cc2x.h').is_file():
            return c
    sys.exit('cc2x.h not found: pass --sdk DIR (the folder that contains cc2x.h)')


def find_zig(arg):
    path = arg or os.environ.get('CC2X_ZIG')
    if path:
        return [str(Path(path).resolve())]
    exe = shutil.which('zig')
    if exe:
        return [exe]
    try:
        subprocess.run([sys.executable, '-m', 'ziglang', 'version'], check=True, capture_output=True)
        return [sys.executable, '-m', 'ziglang']
    except (subprocess.CalledProcessError, OSError):
        sys.exit('No Zig found. Use: pip install ziglang==0.15.2   (or pass --zig PATH / set CC2X_ZIG)')


def check_dll(path):
    """Minimal PE reader: machine, DLL flag, exports, imported DLL names."""
    data = path.read_bytes()
    nt = struct.unpack_from('<I', data, 0x3c)[0]
    assert data[nt:nt + 4] == b'PE\0\0', 'not a PE file'
    machine, nsec, _ts, _p, _n, opt_size, chars = struct.unpack_from('<HHIIIHH', data, nt + 4)
    opt = nt + 24
    magic = struct.unpack_from('<H', data, opt)[0]
    sections = []
    sec = opt + opt_size
    for i in range(nsec):
        name, vsize, va, rsize, rptr = struct.unpack_from('<8sIIII', data, sec + 40 * i)
        sections.append((va, max(vsize, rsize), rptr))

    def rva(r):
        for va, size, ptr in sections:
            if va <= r < va + size:
                return ptr + (r - va)
        raise ValueError('rva outside sections')

    def cstr(off):
        return data[off:data.index(b'\0', off)].decode('ascii', 'replace')

    dd = opt + 96  # data directories of a PE32 optional header
    exp_rva, exp_size = struct.unpack_from('<II', data, dd)
    imp_rva, _ = struct.unpack_from('<II', data, dd + 8)
    exports, imports = [], []
    if exp_rva:
        e = rva(exp_rva)
        n_names = struct.unpack_from('<I', data, e + 24)[0]
        names_rva = struct.unpack_from('<I', data, e + 32)[0]
        for i in range(n_names):
            exports.append(cstr(rva(struct.unpack_from('<I', data, rva(names_rva) + 4 * i)[0])))
    if imp_rva:
        p = rva(imp_rva)
        while True:
            fields = struct.unpack_from('<IIIII', data, p)
            if not any(fields):
                break
            imports.append(cstr(rva(fields[3])))
            p += 20
    return {'machine': machine, 'pe32': magic == 0x10b, 'dll': bool(chars & 0x2000), 'exports': exports,
            'imports': imports, 'size': len(data)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zig')
    ap.add_argument('--sdk')
    args = ap.parse_args()
    sdk = find_sdk(args.sdk)
    zig = find_zig(args.zig)
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    out = dist / OUT_NAME
    env = dict(os.environ)
    env.setdefault('ZIG_GLOBAL_CACHE_DIR', str(ROOT / '.cache' / 'zig'))
    cmd = zig + ['cc', *CFLAGS, '-shared', '-I', str(sdk), '-I', str(ROOT / 'src'),
                 *[str(ROOT / 'src' / s) for s in SOURCES], '-o', str(out)]
    print(' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True, env=env)
    for junk in list(dist.glob('*.lib')) + list(dist.glob('*.pdb')):
        junk.unlink()
    info = check_dll(out)
    print('built %s (%d bytes)' % (out, info['size']))
    print('  machine 0x%04x (0x014c = i386), PE32: %s, DLL: %s' % (info['machine'], info['pe32'], info['dll']))
    print('  exports:', ', '.join(info['exports']) or '(none)')
    print('  imports:', ', '.join(info['imports']))
    if info['machine'] != 0x14c or not info['pe32'] or not info['dll'] or 'cc2x_plugin_load' not in info['exports']:
        sys.exit('CHECK FAILED: not a 32-bit DLL that exports cc2x_plugin_load')
    print('check OK')


if __name__ == '__main__':
    main()
