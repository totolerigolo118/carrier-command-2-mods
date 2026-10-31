#!/usr/bin/env python3
"""Desassemble une plage de carrier_command.exe (32 bits). LECTURE SEULE.

Usage : python -I desasm.py <exe> <debut_hex> <fin_hex>
Adresses d'image, base 0x400000 (comme Ghidra). Les lectures de constantes flottantes par
adresse absolue sont annotees avec la valeur lue : `; [0x00db7a70] = 600`.
"""
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

exe, start, end = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
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
    secs.append((base + va, min(vsize, rawsz), rawptr))


def off(va):
    for sva, n, rp in secs:
        if sva <= va < sva + n:
            return rp + va - sva
    return None


def flt(va):
    o = off(va)
    if o is None:
        return None
    return struct.unpack_from('<f', data, o)[0]


o1 = off(end)
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True


def sync_start(start):
    """Debut de fonction (16 octets alignes, precede de int3) tel que le desassemblage
    lineaire tombe pile sur `start` : evite d'afficher des instructions decalees."""
    s = start & ~0xF
    for _ in range(0x600):
        so = off(s)
        if so is not None and data[so - 1] == 0xCC and data[so] != 0xCC:
            addrs = set()
            for ins in md.disasm(data[so:off(start) + 16], s):
                addrs.add(ins.address)
            if start in addrs:
                return s
        s -= 16
    return start


s0 = sync_start(start)
for ins in md.disasm(data[off(s0):o1], s0):
    if ins.address < start:
        continue
    note = ''
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp:
            d = op.mem.disp & 0xFFFFFFFF
            f = flt(d)
            if f is not None and base <= d < base + 0xC00000:
                note = '; [0x%08x] = %.8g' % (d, f)
    print('%08x  %-26s %-7s %s %s' % (ins.address, ins.bytes.hex(' '), ins.mnemonic, ins.op_str, note))
