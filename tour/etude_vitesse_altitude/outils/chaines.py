import re, sys, struct
data = open(sys.argv[1], 'rb').read()
pat = re.compile(sys.argv[2], re.I)
pe = struct.unpack_from('<I', data, 0x3C)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
optsz = struct.unpack_from('<H', data, pe + 20)[0]
opt = pe + 24
base = struct.unpack_from('<I', data, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + optsz + 40 * i
    vsize, va, rawsz, rawptr = struct.unpack_from('<IIII', data, o + 8)
    secs.append((base + va, rawsz, rawptr))
def va(off):
    for sva, n, rp in secs:
        if rp <= off < rp + n:
            return sva + off - rp
for m in re.finditer(rb'[\x20-\x7e]{5,}', data):
    s = m.group().decode()
    if pat.search(s):
        print(hex(va(m.start()) or 0), s)
