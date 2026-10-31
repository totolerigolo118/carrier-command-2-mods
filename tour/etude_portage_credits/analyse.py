"""Fonctions d'analyse (lecture seule) : retrouver un site dans le nouvel exe par desassemblage."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portlib as P

old = P.Exe(P.F_ORIG)
new = P.Exe(P.F_NEW)

def relocs(e):
    s = set()
    for nm, vs, sva, rs, ro, ch in e.secs:
        if nm != '.reloc':
            continue
        d = e.b[ro:ro + rs]
        p = 0
        while p + 8 <= len(d):
            page, size = struct.unpack_from('<II', d, p)
            if size < 8:
                break
            for i in range((size - 8) // 2):
                w = struct.unpack_from('<H', d, p + 8 + 2 * i)[0]
                if w >> 12 == 3:
                    s.add(page + (w & 0xfff))
            p += size
    return s

RO = relocs(old)
RN = relocs(new)

def fmt(ins):
    return '%08x  %-7s %s' % (ins.address, ins.mnemonic, ins.op_str)

def sig(ins):
    return ins.mnemonic + ' ' + P.norm_ops(ins.op_str)

def same_chain(a, b):
    return a is not None and b is not None and len(a) == len(b) and all(sig(x) == sig(y) and x.size == y.size for x, y in zip(a, b))

def match_at(va_old, va_new):
    co, io = P.chain(old, va_old)
    cn, inn = P.chain(new, va_new)
    if co is None or cn is None or io != inn or not same_chain(co, cn):
        return None
    if (va_old - co[io].address) != (va_new - cn[inn].address):
        return None
    return co, cn, io

def find_new(va):
    hits = []
    oo = old.va2off(va)
    for d in range(-0x80, 0x400):
        on = new.va2off(va + d)
        if on is None or new.b[on - 3:on] != old.b[oo - 3:oo]:
            continue
        r = match_at(va, va + d)
        if r:
            hits.append((d, r))
    return hits

def classify(ins, va):
    d = ins.address
    if ins.mnemonic.startswith('j') and ins.size - 4 == va - d:
        return 'saut_relatif'
    if ins.disp_offset and d + ins.disp_offset == va:
        for op in ins.operands:
            if op.type == P.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                return 'pointeur'
    if ins.imm_offset and d + ins.imm_offset == va:
        return 'immediat'
    if ins.mnemonic.startswith('j') and ins.size - 4 == va - d:
        return 'saut_relatif'
    return 'autre'

def ctx_find(vaold):
    """Retrouve une constante de donnees : memes octets voisins. Renvoie (decalage, taille_contexte, nb_candidats)."""
    oo = old.va2off(vaold)
    n = 0
    for L in (16, 12, 8, 4):
        pre = old.b[oo - L:oo + 4 + L]
        res = []
        for d in range(-0x600, 0x600, 4):
            on = new.va2off(vaold + d)
            if on is None or on - L < 0 or on + 4 + L > len(new.b):
                continue
            if new.b[on - L:on + 4 + L] == pre:
                res.append(d)
        n = len(res)
        if n == 1:
            return res[0], L, 1
    return None, 4, n

def desasm(e, va, n=5):
    o = e.va2off(va)
    return list(P._md.disasm(e.b[o:o + 40], va))[:n]
