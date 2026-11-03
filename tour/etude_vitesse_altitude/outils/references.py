"""Trouve les instructions qui referencent une adresse (imm32 ou disp32). LECTURE SEULE."""
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
data = open(sys.argv[1], 'rb').read()
targets = [int(a, 16) for a in sys.argv[2:]]
pe = struct.unpack_from('<I', data, 0x3C)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
optsz = struct.unpack_from('<H', data, pe + 20)[0]
opt = pe + 24
base = struct.unpack_from('<I', data, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + optsz + 40 * i
    name = data[o:o+8].rstrip(b'\0')
    vsize, va, rawsz, rawptr = struct.unpack_from('<IIII', data, o + 8)
    chars = struct.unpack_from('<I', data, o + 36)[0]
    secs.append((name, base + va, rawsz, rawptr, chars))
md = Cs(CS_ARCH_X86, CS_MODE_32)
for t in targets:
    pat = struct.pack('<I', t)
    for name, sva, n, rp, ch in secs:
        if not ch & 0x20000000:
            continue
        blob = data[rp:rp+n]
        i = blob.find(pat)
        while i >= 0:
            # try decode starting a few bytes before
            for back in range(1, 8):
                a = sva + i - back
                ins = next(md.disasm(data[rp+i-back:rp+i-back+16], a), None)
                if ins and ins.address + ins.size >= sva + i + 4 and ins.address + ins.size <= sva + i + 4 + 4:
                    print(hex(t), hex(ins.address), ins.mnemonic, ins.op_str)
                    break
            i = blob.find(pat, i + 1)
