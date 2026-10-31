"""Lecture seule : verifie, dans l'ancien et le nouvel exe, les sites des crochets de cc2x_frein v12.

Usage : python -I -B verifier_sites_v12.py <ancien exe 1C9A01C3> <nouvel exe 461E1262> [sortie.txt]

Pour chaque exe et sa table d'adresses (la meme que dans cc2x_frein.c) :
  1. horodatage PE attendu ;
  2. chaque site de crochet : octets attendus, aucune entree de relocation dans les octets deplaces,
     aucun saut ni appel direct de tout le code qui vise l'INTERIEUR des octets deplaces ;
  3. chaque cible de saut (H2, H5) : debut d'instruction et instruction attendue ;
  4. H5 : registres vivants a la cible 0x6ff20a (analyse en arriere sur la grande fonction de la piste,
     appels consideres transparents ; un appel virtuel lit ecx, un appel direct ecx et edx, sauf la racine
     carree du jeu, reconnue a ses octets, qui ne lit que xmm0) ; ce que H5 doit donc fournir ;
  5. H5 : aucun push en attente entre le dernier appel et le site (meme profondeur de pile qu'a la cible).
N'ecrit rien dans les exe. capstone seulement.
"""
import struct
import sys

import capstone
from capstone import x86

# Meme table que BUILDS[] dans cc2x_frein.c. Les octets attendus sont identiques dans les deux exe.
TABLES = {
    0x6a36c177: dict(nom="ancien exe 1.5.18-win32", h1=0x7018ce, h2=0x701a3d, h2_goto=0x701a8a, h3=0x6ff0fb,
                     pab=0x6febda, pcd=0x6febe7, pe=0x6febc0, pc=0x6fe788, h5=0x6fe470, h5_goto=0x6ff20a,
                     cap=0x6ff379, fn=(0x6fc7e0, 0x701fa8), tables=((0x701fa8, 5), (0x701fd0, 6))),
    0x6ae228f3: dict(nom="nouvel exe 1.5.18-win32-6ae228f3", h1=0x7019de, h2=0x701b4d, h2_goto=0x701b9a, h3=0x6ff20b,
                     pab=0x6fecea, pcd=0x6fecf7, pe=0x6fecd0, pc=0x6fe898, h5=0x6fe580, h5_goto=0x6ff31a,
                     cap=0x6ff489, fn=(0x6fc8f0, 0x7020b8), tables=((0x7020b8, 5), (0x7020e0, 6))),
}
SITES = [  # nom, cle, octets attendus
    ("H1", "h1", "8b 40 04 83 f8 05"),
    ("H2", "h2", "8d 85 28 fd ff ff"),
    ("H3 (lecture seule)", "h3", "8b 8d 04 fe ff ff"),
    ("sonde A/B (lecture seule)", "pab", "f3 0f 10 8d a4 fd ff ff"),
    ("sonde C/D (lecture seule)", "pcd", "f3 0f 10 8d a4 fd ff ff"),
    ("sonde E (lecture seule)", "pe", "f3 0f 10 8d a4 fd ff ff"),
    ("sonde C passee (lecture seule)", "pc", "8b 8d b4 fd ff ff"),
    ("H5", "h5", "c6 85 fb fd ff ff 01"),
    ("sonde de la prise en charge (lecture seule)", "cap", "89 47 6c 8b 8e 88 00 00 00"),
]
GOTOS = [  # nom, cle, debut attendu de l'instruction
    ("cible de H2", "h2_goto", None),
    ("cible de H5 (test de toucher)", "h5_goto", "f3 0f 10 95 1c fd ff ff"),
]


class PE:
    def __init__(self, path):
        self.d = open(path, "rb").read()
        d = self.d
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        self.stamp = struct.unpack_from("<I", d, pe + 8)[0]
        n = struct.unpack_from("<H", d, pe + 6)[0]
        osz = struct.unpack_from("<H", d, pe + 20)[0]
        self.base = struct.unpack_from("<I", d, pe + 52)[0]
        reloc_rva, reloc_size = struct.unpack_from("<II", d, pe + 24 + 96 + 5 * 8)
        self.secs = []
        for i in range(n):
            o = pe + 24 + osz + 40 * i
            name = d[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
            vs, va, rs, raw = struct.unpack_from("<IIII", d, o + 8)
            ch = struct.unpack_from("<I", d, o + 36)[0]
            self.secs.append((name, self.base + va, vs, raw, rs, ch))
        self.relocs = set()
        p, end = self.off(self.base + reloc_rva), self.off(self.base + reloc_rva) + reloc_size
        while p < end:
            page, size = struct.unpack_from("<II", d, p)
            if size < 8:
                break
            for k in range((size - 8) // 2):
                e = struct.unpack_from("<H", d, p + 8 + 2 * k)[0]
                if e >> 12 == 3:
                    self.relocs.add(self.base + page + (e & 0xFFF))
            p += size

    def off(self, va):
        for _, sva, vs, raw, rs, _ in self.secs:
            if sva <= va < sva + max(vs, rs):
                return raw + va - sva
        raise ValueError(hex(va))

    def read(self, va, n):
        o = self.off(va)
        return self.d[o:o + n]

    def text(self):
        for name, sva, vs, raw, rs, ch in self.secs:
            if ch & 0x20000000:  # code exécutable
                return sva, self.d[raw:raw + min(vs, rs)]
        raise ValueError("pas de section de code")


def branch_targets(pe):
    """Toutes les cibles de sauts et d'appels DIRECTS du code (balayage lineaire, avec resynchronisation)."""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = True
    sva, code = pe.text()
    targets = {}
    for addr, size, mn, ops in md.disasm_lite(code, sva):
        if (mn.startswith("j") or mn == "call" or mn.startswith("loop")) and ops.startswith("0x"):
            try:
                t = int(ops, 16)
            except ValueError:
                continue
            targets.setdefault(t, addr)
    return targets


SQRT_BYTES = bytes.fromhex("55 8b ec 83 e4 f8 f3 0f 5a c0 0f 57 c9 66 0f 2e c8 77 0c f2 0f 51 c0 f2 0f 5a c0 8b e5 5d c3")
GPR = ["eax", "ebx", "ecx", "edx", "esi", "edi"]
XMM = ["xmm%d" % i for i in range(8)]
TRACKED = set(GPR + XMM)


def liveness_at(pe, fn, tables, point):
    """Registres lus avant d'etre ecrits sur au moins un chemin partant de 'point', dans la fonction fn."""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    lo, hi = fn
    code = pe.read(lo, hi - lo)
    ins = {}
    order = []
    for i in md.disasm(code, lo):
        ins[i.address] = i
        order.append(i.address)
    nxt = {a: order[k + 1] if k + 1 < len(order) else None for k, a in enumerate(order)}
    jt = {}
    for tva, n in tables:
        jt[tva] = [struct.unpack_from("<I", pe.read(tva + 4 * k, 4))[0] for k in range(n)]

    def is_sqrt(target):
        """La racine carrée du jeu (0x40ae90 dans l'ancien exe) : xmm0 -> xmm0, ne lit ni ecx ni edx (relu à la main)."""
        return pe.read(target, len(SQRT_BYTES)) == SQRT_BYTES

    def norm(r):
        r = r.lower()
        m = {"al": "eax", "ah": "eax", "ax": "eax", "bl": "ebx", "bh": "ebx", "bx": "ebx", "cl": "ecx", "ch": "ecx",
             "cx": "ecx", "dl": "edx", "dh": "edx", "dx": "edx", "si": "esi", "di": "edi"}
        return m.get(r, r)

    def uses_defs(i):
        u, dfs = set(), set()
        try:
            regs_read, regs_write = i.regs_access()
        except capstone.CsError:
            regs_read, regs_write = [], []
        for r in regs_read:
            u.add(norm(i.reg_name(r)))
        for r in regs_write:
            dfs.add(norm(i.reg_name(r)))
        # xor r,r / xorps x,x / pxor x,x : écriture sans lecture
        if i.mnemonic in ("xor", "xorps", "pxor", "sub") and len(i.operands) == 2 and \
                i.operands[0].type == x86.X86_OP_REG and i.operands[1].type == x86.X86_OP_REG and \
                i.operands[0].reg == i.operands[1].reg:
            u.discard(norm(i.reg_name(i.operands[0].reg)))
        # écriture partielle d'un registre (mov al / mov dl / movss xmm, mem / cvt*ss) : la partie haute reste lue
        if i.mnemonic == "call":
            op = i.operands[0]
            if op.type != x86.X86_OP_IMM:
                u |= {"ecx"}  # appel virtuel (thiscall) : ecx seulement
            elif not is_sqrt(op.imm):
                u |= {"ecx", "edx"}  # appel direct : ecx et edx peuvent porter des arguments
            dfs = set()  # appel transparent : on ne suppose rien d'écrasé
        return u & TRACKED, dfs & TRACKED, i

    def partial_write(i):
        """Instructions qui n'écrivent qu'une partie du registre destination (le reste est 'lu')."""
        mn = i.mnemonic
        if mn in ("movss", "movsd") and len(i.operands) == 2 and i.operands[1].type == x86.X86_OP_REG:
            return True  # movss xmm, xmm : garde les 96 bits hauts
        if mn in ("cvtsi2ss", "cvtss2sd", "cvtsd2ss", "sqrtss", "sqrtsd", "addss", "subss", "mulss", "divss",
                  "minss", "maxss", "addsd", "subsd", "mulsd", "divsd", "cvtps2pd", "cvtpd2ps", "rcpss", "rsqrtss"):
            return True
        if mn == "mov" and i.operands and i.operands[0].type == x86.X86_OP_REG and i.operands[0].size < 4:
            return True
        return False

    def succ(a):
        i = ins[a]
        mn = i.mnemonic
        if mn == "ret":
            return []
        if mn == "jmp":
            op = i.operands[0]
            if op.type == x86.X86_OP_IMM:
                return [op.imm]
            if op.type == x86.X86_OP_MEM and op.mem.disp in jt:
                return list(jt[op.mem.disp])
            return []
        if mn.startswith("j"):
            return [i.operands[0].imm, nxt[a]]
        return [nxt[a]] if nxt[a] else []

    # analyse en arrière classique, au niveau de l'instruction
    live_in = {a: set() for a in order}
    changed = True
    info = {a: uses_defs(ins[a]) for a in order}
    while changed:
        changed = False
        for a in reversed(order):
            u, dfs, i = info[a]
            out = set()
            for s in succ(a):
                if s in live_in:
                    out |= live_in[s]
            kill = set() if partial_write(i) else dfs
            new = u | (out - kill)
            if new != live_in[a]:
                live_in[a] = new
                changed = True
    return sorted(live_in.get(point, {"(point hors fonction)"}))


def pending_pushes_before(pe, fn, site):
    """Pushes non consommés par un appel entre le début du bloc d'instructions linéaire et le site."""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    seq = [(a, mn) for a, s, mn, o in md.disasm_lite(pe.read(site - 0x60, 0x60), site - 0x60)]
    pending = 0
    for a, mn in seq:
        if mn == "push":
            pending += 1
        elif mn == "call":
            pending = 0
    return pending


def main():
    out = []
    say = out.append
    for path in sys.argv[1:3]:
        pe = PE(path)
        t = TABLES.get(pe.stamp)
        say("=" * 100)
        say("%s : horodatage PE 0x%08x -> %s" % (path, pe.stamp, t["nom"] if t else "INCONNU"))
        if not t:
            say("  ECHEC : horodatage inconnu")
            continue
        targets = branch_targets(pe)
        ok = True
        for nom, k, exp in SITES:
            va = t[k]
            want = bytes.fromhex(exp)
            got = pe.read(va, len(want))
            rel = [hex(r) for r in pe.relocs if va <= r < va + len(want) or va <= r + 3 < va + len(want)]
            inner = ["0x%x (depuis 0x%x)" % (x, targets[x]) for x in range(va + 1, va + len(want)) if x in targets]
            good = got == want and not rel and not inner
            ok &= good
            say("  %-45s 0x%06x  %d octets  %s  relocations:%s  sauts vers l'interieur:%s  -> %s" % (
                nom, va, len(want), "octets OK" if got == want else "OCTETS DIFFERENTS " + got.hex(" "),
                " aucune" if not rel else " " + ", ".join(rel), " aucun" if not inner else " " + ", ".join(inner),
                "SUR" if good else "A REVOIR"))
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        for nom, k, exp in GOTOS:
            va = t[k]
            i = next(md.disasm(pe.read(va, 16), va))
            good = exp is None or i.bytes == bytes.fromhex(exp)
            ok &= good
            say("  %-45s 0x%06x  %s %s  -> %s" % (nom, va, i.mnemonic, i.op_str, "OK" if good else "A REVOIR"))
        live = liveness_at(pe, t["fn"], t["tables"], t["h5_goto"])
        say("  registres vivants a la cible de H5 (0x%x) : %s" % (t["h5_goto"], ", ".join(live) or "aucun"))
        extra = [r for r in live if r not in ("ebx", "esi", "edi")]
        say("    -> H5 fournit edi (gestionnaire) et esi (navire) ; ebx = pile d'origine de la fonction, constant ; autres : %s"
            % (", ".join(extra) if extra else "aucun"))
        ok &= not extra
        pp = pending_pushes_before(pe, t["fn"], t["h5"])
        say("  pushes en attente juste avant H5 : %d (0 = meme profondeur de pile que la cible)" % pp)
        ok &= pp == 0
        say("  BILAN %s : %s" % (t["nom"], "TOUT EST SUR" if ok else "A REVOIR"))
    text = "\n".join(out)
    print(text)
    if len(sys.argv) > 3:
        open(sys.argv[3], "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()
