#!/usr/bin/env python3
"""Liste les lectures d'une constante flottante dans une plage d'adresses de carrier_command.exe.
LECTURE SEULE. Donne pour chaque lecture : adresse de l'instruction, longueur, decalage du
disp32, octets d'origine (tels qu'ils sont dans le FICHIER), mnemonique, valeur lue.

Usage : python -I lister_lectures.py <exe> <debut_hex> <fin_hex> <valeur> [<valeur> ...]
<valeur> = nombre decimal ou fraction (0.05, -0.025, 2.5, 1/6, -1/30 ...) : comparee sur les 32 bits.
"""
import struct
import sys
from fractions import Fraction

exe, lo, hi = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
wanted = {}
for a in sys.argv[4:]:
    f = float(Fraction(a)) if '/' in a else float(a)
    wanted[struct.unpack('<I', struct.pack('<f', f))[0]] = a

data = open(exe, 'rb').read()
pe = struct.unpack_from('<I', data, 0x3C)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
optsz = struct.unpack_from('<H', data, pe + 20)[0]
opt = pe + 24
base = struct.unpack_from('<I', data, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + optsz + 40 * i
    vsize, va, rawsz, rawptr = struct.unpack_from('<IIII', data, o + 8)
    fl = struct.unpack_from('<I', data, o + 36)[0]
    secs.append((base + va, min(vsize, rawsz), rawptr, bool(fl & 0x20000000)))


def off(va):
    for sva, n, rp, _ in secs:
        if sva <= va < sva + n:
            return rp + va - sva
    return None


# copies des constantes en donnees
locs = {}
for sva, n, rp, ex in secs:
    if ex:
        continue
    blob = data[rp:rp + n]
    for bits, name in wanted.items():
        pat = struct.pack('<I', bits)
        i = blob.find(pat)
        while i != -1:
            if i % 4 == 0:
                locs[sva + i] = (name, bits)
            i = blob.find(pat, i + 1)

SS = {0x10: 'movss', 0x58: 'addss', 0x59: 'mulss', 0x5C: 'subss', 0x5E: 'divss', 0x5D: 'minss',
      0x5F: 'maxss', 0x5A: 'cvtss2sd', 0x51: 'sqrtss'}
PS = {0x28: 'movaps', 0x10: 'movups', 0x54: 'andps', 0x57: 'xorps', 0x58: 'addps', 0x59: 'mulps',
      0x5C: 'subps', 0x5E: 'divps', 0x2F: 'comiss', 0x2E: 'ucomiss', 0x5D: 'minps', 0x5F: 'maxps'}
X87 = {(0xD9, 0x05): 'fld', (0xD8, 0x0D): 'fmul', (0xD8, 0x05): 'fadd', (0xD8, 0x25): 'fsub',
       (0xD8, 0x35): 'fdiv', (0xD8, 0x15): 'fcom', (0xD8, 0x1D): 'fcomp'}

rows = []
for sva, n, rp, ex in secs:
    if not ex:
        continue
    blob = data[rp:rp + n]
    for cva, (name, bits) in locs.items():
        pat = struct.pack('<I', cva)
        i = blob.find(pat)
        while i != -1:
            d = sva + i                      # adresse du disp32
            if lo <= d < hi:
                m = blob[i - 1]
                start = mn = None
                if (blob[i - 2], m) in X87:
                    start, mn = d - 2, X87[(blob[i - 2], m)]
                elif (m & 0xC7) == 0x05 and blob[i - 3] == 0x0F and blob[i - 4] in (0xF3, 0x66, 0xF2):
                    start = d - 4
                    mn = SS.get(blob[i - 2], 'op%02x' % blob[i - 2]) if blob[i - 4] == 0xF3 else '?(%02x 0f)' % blob[i - 4]
                elif (m & 0xC7) == 0x05 and blob[i - 3] == 0x0F:
                    start, mn = d - 3, PS.get(blob[i - 2], 'op%02x' % blob[i - 2])
                if start is None:
                    rows.append((d, d, 0, '?', name, ''))
                else:
                    s_off = i - (d - start)
                    rows.append((start, d, d + 4 - start, mn, name, blob[s_off:i + 4].hex(' ')))
            i = blob.find(pat, i + 1)

rows.sort()
print('# %d lectures entre 0x%08x et 0x%08x' % (len(rows), lo, hi))
print('# adresse   long  disp  mnemonique valeur   octets du fichier')
for start, d, ln, mn, name, hx in rows:
    print('0x%08x  %2d    +%d    %-9s  %-7s  %s' % (start, ln, d - start, mn, name, hx))
