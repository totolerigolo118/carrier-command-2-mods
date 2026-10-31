"""Outils communs de l'etude de portage (lecture seule des exe ; aucun ecrit dans le jeu)."""
import struct, hashlib, os, re, json, glob
B = os.path.dirname(os.path.abspath(__file__))
COPIES = B + '/copies/'
F_ORIG = COPIES + 'carrier_command_ORIGINAL_1C9A01C3.exe'
F_PATCH = COPIES + 'carrier_command_PATCHE_8E7FCBB6.exe'
F_NEW = COPIES + 'carrier_command_NOUVEAU_461E1262.exe'
SHA_ORIG = '1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026'
SHA_PATCH = '8E7FCBB6CE27BD3D8FEB02BF7F3DBBA646CCE6D4944360570F082972E8DFE8BE'
SHA_NEW = '461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A'
BASE = 0x400000
MODDIR = B + '/../outils/modules_exe/'
NOUVEAU_DIR = B + '/modules_exe_nouvel_exe/'
TRAVAIL = B + '/travail/'

def sha(b): return hashlib.sha256(b).hexdigest().upper()
def lire(p):
    with open(p, 'rb') as f: return f.read()

def pe_info(b):
    e = struct.unpack_from('<I', b, 0x3c)[0]
    assert b[e:e+4] == b'PE\0\0'
    mach, nsec, ts, symp, nsym, optsz, chars = struct.unpack_from('<HHIIIHH', b, e+4)
    o = e + 24
    magic = struct.unpack_from('<H', b, o)[0]
    imgbase = struct.unpack_from('<I', b, o+28)[0]
    secalign, filealign = struct.unpack_from('<II', b, o+32)
    imgsize, hdrsize, csum = struct.unpack_from('<III', b, o+56)
    secs = []
    for i in range(nsec):
        nm, vs, sva, rs, ro = struct.unpack_from('<8sIIII', b, o+optsz+40*i)
        ch = struct.unpack_from('<I', b, o+optsz+40*i+36)[0]
        secs.append((nm.rstrip(b'\0').decode(), vs, sva, rs, ro, ch))
    return dict(e_lfanew=e, machine=mach, nsec=nsec, ts=ts, optsz=optsz, chars=chars, magic=magic,
                imgbase=imgbase, secalign=secalign, filealign=filealign, imgsize=imgsize, hdrsize=hdrsize,
                checksum=csum, secs=secs, opt_off=o, sec_table_off=o+optsz, sec_table_end=o+optsz+40*nsec)

class Exe:
    def __init__(self, path):
        self.path = path; self.b = lire(path); self.pe = pe_info(self.b); self.secs = self.pe['secs']
    def off2va(self, off):
        if off < self.pe['hdrsize']: return BASE + off
        for nm, vs, sva, rs, ro, ch in self.secs:
            if ro <= off < ro + rs: return BASE + sva + off - ro
        return None
    def va2off(self, va):
        r = va - BASE
        if 0 <= r < self.pe['hdrsize']: return r
        for nm, vs, sva, rs, ro, ch in self.secs:
            if sva <= r < sva + min(vs, rs) if False else (sva <= r < sva + rs): return ro + r - sva
        return None
    def sec_of_va(self, va):
        r = va - BASE
        if 0 <= r < self.pe['hdrsize']: return 'EN-TETE'
        for nm, vs, sva, rs, ro, ch in self.secs:
            if sva <= r < sva + max(vs, rs): return nm
        return None
    def u32(self, va): o = self.va2off(va); return struct.unpack_from('<I', self.b, o)[0]
    def f32(self, va): o = self.va2off(va); return struct.unpack_from('<f', self.b, o)[0]

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM
_md = Cs(CS_ARCH_X86, CS_MODE_32); _md.detail = True
HEX = re.compile(r'0x[0-9a-fA-F]+')

def norm_ops(s):
    def f(m):
        v = int(m.group(0), 16)
        return 'ADDR' if 0x400000 <= v < 0xEF7000 else m.group(0)
    return HEX.sub(f, s)

_cache = {}

def _decode_from(exe, start, n):
    o = exe.va2off(start)
    code = exe.b[o:o + n]
    ins = []
    pos = 0
    while pos < len(code):
        got = list(_md.disasm(code[pos:pos + 16], start + pos, count=1))
        if not got:
            pos += 1
            continue
        ins.append(got[0])
        pos += got[0].size
    return ins

def chain(exe, va_field, nbefore=4, nafter=6):
    """Desassemble autour du champ de 4 octets a va_field. Synchronisation par vote : on desassemble depuis ~100 points de
    depart ; une adresse est un vrai debut d'instruction si elle est retrouvee par une forte majorite des departs.
    Renvoie (liste d'instructions, index de celle qui contient le champ) ou (None, None)."""
    key = (exe.path, va_field, nbefore, nafter)
    if key in _cache:
        return _cache[key]
    votes = {}
    insn = {}
    nstart = 0
    for back in range(8, 112):
        nstart += 1
        for x in _decode_from(exe, va_field - back, back + 100):
            if va_field - 40 <= x.address <= va_field + 40:
                votes[x.address] = votes.get(x.address, 0) + 1
                insn[x.address] = x
    cand = [a for a in votes if votes[a] >= 0.5 * max(votes.values())]
    cand.sort()
    seq = []
    for a in cand:
        x = insn[a]
        if seq and seq[-1].address + seq[-1].size > a:
            if votes[a] > votes[seq[-1].address]:
                seq[-1] = x
            continue
        seq.append(x)
    k = None
    for j, x in enumerate(seq):
        if x.address <= va_field < x.address + x.size:
            k = j
    if k is None:
        _cache[key] = (None, None)
        return _cache[key]
    lo = max(0, k - nbefore)
    hi = min(len(seq), k + nafter + 1)
    _cache[key] = (seq[lo:hi], k - lo)
    return _cache[key]
