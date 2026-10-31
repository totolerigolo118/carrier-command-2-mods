"""Compare deux DLL du SDK fonction par fonction (LECTURE SEULE). Bornes des fonctions : les FDE de la section .debug_frame.

Pour chaque fonction : instructions normalisées (adresses internes masquées), et surtout ce qu'elle TOUCHE :
imports appelés (par nom), fonctions internes appelées (par rang), chaînes et données lues (par contenu ou par rang).
Une fonction qui change de forme mais garde exactement les mêmes imports, appels et chaînes n'a pas reçu de nouveau
comportement visible du système (pas de nouveau fichier, réseau, processus...).

Usage : python -I -B comparer_fonctions_dll.py <dll_A> <dll_B>
"""
import collections
import re
import struct
import sys

import capstone as cs

MD = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_32)
MD.detail = True


class DLL:
    def __init__(self, p):
        self.p = p
        b = self.b = open(p, 'rb').read()
        e = struct.unpack_from('<I', b, 0x3c)[0]
        nsec, = struct.unpack_from('<H', b, e + 6)
        self.ts, = struct.unpack_from('<I', b, e + 8)
        pst, nsym = struct.unpack_from('<II', b, e + 12)
        opt, = struct.unpack_from('<H', b, e + 20)
        self.base, = struct.unpack_from('<I', b, e + 24 + 28)
        self.taille, = struct.unpack_from('<I', b, e + 24 + 56)
        self.dd = [struct.unpack_from('<II', b, e + 24 + 96 + 8 * i) for i in range(16)]
        strtab = pst + 18 * nsym
        self.secs = {}
        for i in range(nsec):
            s = e + 24 + opt + 40 * i
            nom = b[s:s + 8].rstrip(b'\0').decode()
            if nom.startswith('/'):
                o = strtab + int(nom[1:])
                nom = b[o:b.index(b'\0', o)].decode()
            vs, rva, rs, rp = struct.unpack_from('<IIII', b, s + 8)
            self.secs[nom] = (rva, vs, rp, rs)
        self.imports = self._imports()

    def off(self, rva):
        for rva0, vs, rp, rs in self.secs.values():
            if rva0 <= rva < rva0 + max(vs, rs):
                return rp + rva - rva0
        return None

    def sec_de(self, va):
        rva = va - self.base
        for nom, (rva0, vs, rp, rs) in self.secs.items():
            if rva0 <= rva < rva0 + vs:
                return nom
        return None

    def cstr(self, va, maxi=80):
        o = self.off(va - self.base)
        if o is None:
            return None
        fin = self.b.find(b'\0', o, o + maxi)
        s = self.b[o:fin if fin != -1 else o + maxi]
        if len(s) >= 3 and all(0x20 <= c < 0x7f for c in s):
            return s.decode()
        w = self.b[o:o + 2 * maxi]
        m = re.match(rb'((?:[\x20-\x7e]\x00){3,})\x00\x00', w)
        if m:
            return 'L"' + m.group(1).decode('utf-16le') + '"'
        return None

    def _imports(self):
        """va de chaque case de l'IAT -> 'dll!fonction'."""
        rva, _ = self.dd[1]
        out = {}
        i = 0
        while True:
            oft, _, _, nom, ft = struct.unpack_from('<IIIII', self.b, self.off(rva + 20 * i))
            if not (oft or nom or ft):
                break
            dll = self.b[self.off(nom):self.b.index(b'\0', self.off(nom))].decode()
            j = 0
            while True:
                v, = struct.unpack_from('<I', self.b, self.off((oft or ft) + 4 * j))
                if not v:
                    break
                o = self.off(v + 2)
                out[self.base + ft + 4 * j] = dll.lower() + '!' + self.b[o:self.b.index(b'\0', o)].decode()
                j += 1
            i += 1
        return out

    def fonctions(self):
        rva, vs, rp, rs = self.secs['.debug_frame']
        d = self.b[rp:rp + vs]
        o, out = 0, []
        while o + 4 <= len(d):
            n, = struct.unpack_from('<I', d, o)
            if n == 0:
                break
            cie, = struct.unpack_from('<I', d, o + 4)
            if cie != 0xffffffff:
                debut, taille = struct.unpack_from('<II', d, o + 8)
                out.append((debut, taille))
            o += 4 + n
        return sorted(set(out))


def decrire(d, fns):
    rang = {debut: i for i, (debut, _) in enumerate(fns)}
    s_text = d.secs['.text']
    lo, hi = d.base, d.base + d.taille
    res = []
    for debut, taille in fns:
        code = d.b[d.off(debut - d.base):d.off(debut - d.base) + taille]
        instr, touche = [], collections.Counter()
        for i in MD.disasm(code, debut):
            txt = re.sub(r'0x[0-9a-f]+', lambda m: 'ADR' if lo <= int(m.group(), 16) < hi else m.group(),
                         i.mnemonic + ' ' + i.op_str)
            instr.append(txt)
            vals = []
            if i.imm_size == 4 or (i.imm_size and any(g in (cs.CS_GRP_CALL, cs.CS_GRP_JUMP) for g in i.groups)):
                for op in i.operands:
                    if op.type == cs.x86.X86_OP_IMM:
                        vals.append(op.imm & 0xffffffff)
            if i.disp_size == 4:
                for op in i.operands:
                    if op.type == cs.x86.X86_OP_MEM:
                        vals.append(op.mem.disp & 0xffffffff)
            appel = any(g == cs.CS_GRP_CALL for g in i.groups)
            for v in vals:
                if not (lo <= v < hi):
                    continue
                if v in d.imports:
                    touche[('import', d.imports[v])] += 1
                elif v in rang:
                    touche[('appel' if appel else 'adresse_fonction', rang[v])] += 1
                elif debut <= v < debut + taille:
                    pass                                        # saut interne
                else:
                    sec = d.sec_de(v)
                    s = d.cstr(v)
                    if s is not None and sec in ('.rdata', '.data'):
                        touche[('chaine', s)] += 1
                    else:
                        touche[('donnee', sec)] += 1
        res.append((debut, taille, instr, touche))
    return res


def main():
    A, B = DLL(sys.argv[1]), DLL(sys.argv[2])
    fa, fb = A.fonctions(), B.fonctions()
    print('A %s : %d fonctions (FDE) ; B %s : %d fonctions' % (A.p, len(fa), B.p, len(fb)))
    da, db = decrire(A, fa), decrire(B, fb)
    if len(da) != len(db):
        print('NOMBRE DE FONCTIONS DIFFÉRENT')
    memes = changees = 0
    alerte = 0
    imp_a, imp_b = collections.Counter(), collections.Counter()
    ch_a, ch_b = collections.Counter(), collections.Counter()
    for (a0, ta, ia, ka), (b0, tb, ib, kb) in zip(da, db):
        for k, n in ka.items():
            if k[0] == 'import':
                imp_a[k[1]] += n
            if k[0] == 'chaine':
                ch_a[k[1]] += n
        for k, n in kb.items():
            if k[0] == 'import':
                imp_b[k[1]] += n
            if k[0] == 'chaine':
                ch_b[k[1]] += n
        if ia == ib:
            memes += 1
            continue
        changees += 1
        sa = {k for k in ka if k[0] in ('import', 'appel', 'chaine', 'adresse_fonction')}
        sb = {k for k in kb if k[0] in ('import', 'appel', 'chaine', 'adresse_fonction')}
        donnees_a = {k: n for k, n in ka.items() if k[0] == 'donnee'}
        donnees_b = {k: n for k, n in kb.items() if k[0] == 'donnee'}
        diff = sorted(sa ^ sb)
        alerte += bool(diff)
        print('\nfonction #%d  A %#x (%d o, %d instr.)  B %#x (%d o, %d instr.)' % (
            fa.index((a0, ta)), a0, ta, len(ia), b0, tb, len(ib)))
        print('   imports appelés : %s' % sorted(k[1] for k in sb if k[0] == 'import'))
        print('   chaînes lues    : %s' % sorted(k[1] for k in sb if k[0] == 'chaine'))
        print('   appels internes : %s' % sorted(k[1] for k in sb if k[0] == 'appel'))
        print('   données .data/.rdata (hors chaînes) A %s ; B %s' % (donnees_a, donnees_b))
        print('   ensembles (imports, appels, chaînes) identiques : %s%s' % (
            not diff, '' if not diff else '  *** seulement A : %s ; seulement B : %s' % (sorted(sa - sb), sorted(sb - sa))))
    print('\n%d fonctions identiques, %d changées ; changées dont les imports/appels/chaînes diffèrent : %d' % (memes, changees, alerte))
    print('nombre total de références à chaque import identique (A/B) :', imp_a == imp_b)
    if imp_a != imp_b:
        for k in sorted(set(imp_a) | set(imp_b)):
            if imp_a[k] != imp_b[k]:
                print('   %s : A %d, B %d' % (k, imp_a[k], imp_b[k]))
    print('chaînes référencées par le code : A %d distinctes, B %d ; seulement A : %s ; seulement B : %s' % (
        len(ch_a), len(ch_b), sorted(set(ch_a) - set(ch_b)), sorted(set(ch_b) - set(ch_a))))
    for k in sorted(set(ch_a) | set(ch_b)):
        if ch_a[k] != ch_b[k]:
            print('   nombre de références différent : %r A %d, B %d' % (k, ch_a[k], ch_b[k]))


if __name__ == '__main__':
    main()
