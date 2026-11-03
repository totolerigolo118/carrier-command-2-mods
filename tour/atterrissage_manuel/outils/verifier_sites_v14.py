"""Lecture seule : verifie, dans l'ancien et le nouvel exe, les sites des crochets de cc2x_frein v14 (v12 + H6 helicos + retour automatique).

Usage : python -I -B verifier_sites_v14.py <ancien exe 1C9A01C3> <nouvel exe 461E1262> [sortie.txt]

Pour chaque exe et sa table d'adresses (la meme que dans cc2x_frein.c) :
  1. horodatage PE attendu ;
  2. chaque site de crochet : octets attendus, aucune entree de relocation dans les octets deplaces,
     aucun saut ni appel direct de tout le code qui vise l'INTERIEUR des octets deplaces ;
  3. chaque cible de saut (H2, H5) : debut d'instruction et instruction attendue ;
  4. H5 : registres vivants a la cible 0x6ff20a (analyse en arriere sur la grande fonction de la piste,
     appels consideres transparents ; un appel virtuel lit ecx, un appel direct ecx et edx, sauf la racine
     carree du jeu, reconnue a ses octets, qui ne lit que xmm0) ; ce que H5 doit donc fournir ;
  5. H5 : aucun push en attente entre le dernier appel et le site (meme profondeur de pile qu'a la cible) ;
  6. v13, H6 : entre le site et sa cible (0x6fdcf2), seulement des instructions SSE de registre et la comparaison (aucun push, pop,
     appel, acces memoire) ; registres ecrits entre les deux (xmm2, xmm3) PAS vivants a la cible ; [ebp-0x270] ecrit par le jeu
     (vehicule trouve) avant le site ; et le chemin des helicopteres lu dans l'etude (constantes -100, -240, 10000, 20, 30 ; le
     test 0x4c ; la boucle de la file qui envoie les helicos au point d'attente sans passer par H1).
  7. v14, retour automatique : l'entree +0x7c de la table du porte-avions est la fonction de demande d'accostage ; cette fonction
     (cherche l'appareil avec le monde [ebp+8] et l'id [ebp+0xc], DOCK_STATE = 5 deux fois, DOCK_VEHICLE, 'ret 8' = deux arguments) ;
     l'appel du serveur pour l'ordre du joueur (lea eax,[esi+0x344] = le monde, puis carrier->[+0x7c](monde, id)).
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
                     cap=0x6ff379, h6=0x6fdcdd, h6_goto=0x6fdcf2, carrier_vt=0xd596cc, dock_fn=0x707330, srv_call=0x7784e1, fn=(0x6fc7e0, 0x701fa8), tables=((0x701fa8, 5), (0x701fd0, 6))),
    0x6ae228f3: dict(nom="nouvel exe 1.5.18-win32-6ae228f3", h1=0x7019de, h2=0x701b4d, h2_goto=0x701b9a, h3=0x6ff20b,
                     pab=0x6fecea, pcd=0x6fecf7, pe=0x6fecd0, pc=0x6fe898, h5=0x6fe580, h5_goto=0x6ff31a,
                     cap=0x6ff489, h6=0x6fdded, h6_goto=0x6fde02, carrier_vt=0xd596ec, dock_fn=0x707440, srv_call=0x7785d1, fn=(0x6fc8f0, 0x7020b8), tables=((0x7020b8, 5), (0x7020e0, 6))),
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
    ("H6 (v13, helicopteres)", "h6", "f3 0f 59 d2 f3 0f 59 db"),
]
GOTOS = [  # nom, cle, debut attendu de l'instruction
    ("cible de H2", "h2_goto", None),
    ("cible de H5 (test de toucher)", "h5_goto", "f3 0f 10 95 1c fd ff ff"),
    ("cible de H6 (don de la piste a l'helico)", "h6_goto", "8b 8d 88 fd ff ff"),
]
# v13 : faits du chemin des helicopteres, decalages par rapport a l'ancien exe (le nouvel exe : +0x110 dans la grande fonction)
#   (nom, adresse ancien exe, debut d'instruction attendu, constante flottante attendue a l'adresse lue par l'instruction ou None)
HELI = [
    ("file : test helico (vtable+0x4c)", 0x7016d6, "8b 40 4c", None),
    ("file : helico -> point d'attente, element suivant (jmp 0x701c38, sans H1)", 0x70186c, "e9", None),
    ("don helico : x du point d'attente", 0x6fdcac, "f3 0f 10 15", -100.0),
    ("don helico : z du point d'attente", 0x6fdcb4, "f3 0f 10 1d", -240.0),
    ("don helico : 100 m au carre", 0x6fdcd1, "f3 0f 10 05", 10000.0),
    ("don helico : comparaison", 0x6fdce9, "0f 2f c3", None),
    ("don helico : ecrit le proprietaire de la piste", 0x6fdd17, "89 47 5c", None),
    ("don helico : etat de piste 3", 0x6fdd1a, "c7 47 1c 03 00 00 00", None),
    ("don helico : DOCK_STATE = 1", 0x6fdd42, "c7 80 74 01 00 00 01 00 00 00", None),
    ("etat 3 : test helico", 0x6fe18b, "8b 40 4c", None),
    ("branche helico : proche si distance au milieu < 20 m", 0x6fe3e7, "f3 0f 10 05", 20.0),
    ("branche helico : ecart lateral <= 30 m", 0x6fe422, "0f 2f 05", 30.0),
    ("tronc : saute le cone pour un helico (vtable+0x4c)", 0x6fef79, "8b 40 4c", None),
    ("toucher : vitesse relative <= 10 m/s", 0x6ff263, "0f 2f 05", 10.0),
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


def h6_controles(pe, t, md, say):
    """v13 : le saut de H6 (site -> cible) et le chemin des helicopteres lu dans l'etude."""
    ok = True
    dec = t["h6"] - 0x6fdcdd
    md.detail = True
    seq = list(md.disasm(pe.read(t["h6"], t["h6_goto"] - t["h6"]), t["h6"]))
    fin = seq[-1].address + seq[-1].size if seq else 0
    permis = {"mulss", "addss", "comiss", "jbe"}
    mauvais = [f"{i.address:#x} {i.mnemonic} {i.op_str}" for i in seq if i.mnemonic not in permis or
               (i.mnemonic != "jbe" and any(o.type == x86.X86_OP_MEM for o in i.operands))]
    sortie = [i.operands[0].imm for i in seq if i.mnemonic == "jbe"]
    bon = fin == t["h6_goto"] and not mauvais and len(sortie) == 1
    ok &= bon
    say("  H6 : %d instructions entre le site et la cible : %s ; seulement SSE de registres + la comparaison : %s ; sortie du test : %s -> %s" % (
        len(seq), ", ".join(i.mnemonic + " " + i.op_str for i in seq), "oui" if not mauvais else "NON " + "; ".join(mauvais),
        ", ".join(hex(x) for x in sortie), "OK" if bon else "A REVOIR"))
    ecrits = {"xmm2", "xmm3"}
    live = liveness_at(pe, t["fn"], t["tables"], t["h6_goto"])
    gene = sorted(ecrits & set(live))
    say("  registres vivants a la cible de H6 (0x%x) : %s ; parmi xmm2/xmm3 (ecrits entre site et cible) : %s -> %s" % (
        t["h6_goto"], ", ".join(live) or "aucun", ", ".join(gene) or "aucun", "OK" if not gene else "A REVOIR"))
    ok &= not gene
    # [ebp-0x270] (l'helico) et [ebp-0x278] (sa place dans la file) ecrits par le jeu dans ce bloc avant le site
    av = list(md.disasm(pe.read(t["h6"] - 0x140, 0x140), t["h6"] - 0x140))
    w270 = [i for i in av if i.mnemonic == "mov" and "dword ptr [ebp - 0x270], eax" == i.op_str]
    w278 = [i for i in av if i.mnemonic == "mov" and i.op_str.startswith("dword ptr [ebp - 0x278]")]
    bon = bool(w270) and bool(w278)
    ok &= bon
    say("  [ebp-0x270] = helico trouve (%s), [ebp-0x278] = place dans la file (%s) -> %s" % (
        ", ".join(hex(i.address) for i in w270) or "NON", ", ".join(hex(i.address) for i in w278) or "NON", "OK" if bon else "A REVOIR"))
    for nom, a0, debut, cst in HELI:
        a = a0 + dec
        i = next(md.disasm(pe.read(a, 16), a))
        bon = i.bytes.hex(" ").startswith(debut)
        val = None
        if cst is not None:
            mem = [o for o in i.operands if o.type == x86.X86_OP_MEM and o.mem.base == 0]
            if mem:
                val = struct.unpack("<f", pe.read(mem[0].mem.disp & 0xffffffff, 4))[0]
            bon &= val == cst
        if i.mnemonic == "jmp" and a0 == 0x70186c:
            bon &= i.operands[0].imm == 0x701c38 + dec
        ok &= bon
        say("  helico %-70s 0x%06x  %s %s%s -> %s" % (nom, a, i.mnemonic, i.op_str, "" if val is None else "  (= %g)" % val, "OK" if bon else "A REVOIR"))
    return ok


def b_controles(pe, t, say):
    """v14 : la table du porte-avions, sa fonction +0x7c et l'appel que fait le serveur (lecture seule)."""
    ok = True
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    entree = struct.unpack("<I", pe.read(t["carrier_vt"] + 0x7c, 4))[0]
    bon = entree == t["dock_fn"]
    ok &= bon
    say("  retour auto : table du porte-avions 0x%x, entree +0x7c = 0x%x (attendu 0x%x) -> %s" % (t["carrier_vt"], entree, t["dock_fn"], "OK" if bon else "A REVOIR"))
    code = list(md.disasm(pe.read(t["dock_fn"], 0x330), t["dock_fn"]))
    fin = next((k for k, i in enumerate(code) if i.mnemonic == "ret"), None)
    corps = code[:fin + 1] if fin is not None else code
    txt = [(i.mnemonic, i.op_str) for i in corps]
    d5 = sum(1 for m, o in txt if m == "mov" and o == "dword ptr [edi + 0x174], 5")
    dv = ("mov", "dword ptr [edi + 0x114], eax") in txt
    ret8 = fin is not None and corps[-1].op_str == "8"
    debut = txt[:12]
    trouve = ("mov", "ecx, dword ptr [ebp + 8]") in debut and ("push", "dword ptr [ebp + 0xc]") in debut and any(m == "call" for m, o in debut)
    ecrits = sorted({o.split(",")[0] for m, o in txt if m == "mov" and o.startswith("dword ptr [edi + 0x")})
    bon = d5 == 2 and dv and ret8 and trouve
    ok &= bon
    say("  retour auto : fonction 0x%x : %d instructions ; recherche de l'appareil avec monde = [ebp+8], id = [ebp+0xc] : %s ; DOCK_STATE = 5 x%d ; DOCK_VEHICLE : %s ; "
        "fin 'ret %s' ; champs de l'appareil ecrits : %s -> %s" % (t["dock_fn"], len(corps), "oui" if trouve else "NON", d5, "oui" if dv else "NON",
                                                                    corps[-1].op_str if fin is not None else "?", ", ".join(ecrits), "OK" if bon else "A REVOIR"))
    a = t["srv_call"]
    seq = list(md.disasm(pe.read(a, 13), a))
    bon = len(seq) >= 4 and seq[0].mnemonic == "lea" and seq[0].op_str == "eax, [esi + 0x344]" and seq[1].op_str == "eax" and seq[2].op_str == "edx" and seq[3].mnemonic == "call"
    cible = seq[3].operands[0].imm if bon else 0
    if bon:
        c2 = list(md.disasm(pe.read(cible, 0x40), cible))
        k = next((j for j, i in enumerate(c2) if i.mnemonic == "call" and i.op_str == "dword ptr [eax + 0x7c]"), None)
        bon = k is not None and c2[k - 1].op_str == "dword ptr [ebp + 0xc]" and any(i.op_str == "dword ptr [edi + 0x80]" for i in c2[:k])
    ok &= bon
    say("  retour auto : appel du serveur 0x%x : lea eax,[esi+0x344] (monde = serveur + 0x344), puis 0x%x qui pousse l'id puis le monde et appelle [+0x7c] -> %s" % (
        a, cible, "OK" if bon else "A REVOIR"))
    return ok


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
        ok &= h6_controles(pe, t, md, say)
        ok &= b_controles(pe, t, say)
        say("  BILAN %s : %s" % (t["nom"], "TOUT EST SUR" if ok else "A REVOIR"))
    text = "\n".join(out)
    print(text)
    if len(sys.argv) > 3:
        open(sys.argv[3], "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()
