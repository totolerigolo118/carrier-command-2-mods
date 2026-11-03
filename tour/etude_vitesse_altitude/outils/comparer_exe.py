"""Cherche dans l'ancien exe les memes octets que dans le nouveau (sites utiles). LECTURE SEULE."""
import struct, sys
def load(p):
    d = open(p, 'rb').read()
    pe = struct.unpack_from('<I', d, 0x3C)[0]; n = struct.unpack_from('<H', d, pe + 6)[0]; osz = struct.unpack_from('<H', d, pe + 20)[0]
    base = struct.unpack_from('<I', d, pe + 24 + 28)[0]
    secs = []
    for i in range(n):
        o = pe + 24 + osz + 40 * i
        vs, va, rs, rp = struct.unpack_from('<IIII', d, o + 8)
        secs.append((base + va, rs, rp))
    return d, secs
def off(secs, va):
    for s, n, rp in secs:
        if s <= va < s + n: return rp + va - s
def va_of(secs, o):
    for s, n, rp in secs:
        if rp <= o < rp + n: return s + o - rp
new, ns = load(sys.argv[1]); old, os_ = load(sys.argv[2])
# site, longueur de contexte avant/apres (motif sans adresses absolues de preference)
for name, site, before, after in [
    ("setLinearDamping call", 0x5d0e64, 8, 6),
    ("air damping read", 0x5d0bb1, 0, 8),
    ("AI cruise 120 load", 0x71decc, 8, 16),
    ("AI after load (hook)", 0x71ded4, 0, 8),
    ("thrust ceiling", 0x5d377a, 0, 8),
    ("ceiling sub/div", 0x5d3795, 0, 24),
]:
    o = off(ns, site)
    pat = new[o - before:o + after]
    hits = []
    i = old.find(pat)
    while i >= 0 and len(hits) < 5:
        hits.append(hex(va_of(os_, i + before)))
        i = old.find(pat, i + 1)
    print(f"{name:24s} new {site:#x}  bytes {new[o:o+after].hex(' ')}  old hits {hits}")
