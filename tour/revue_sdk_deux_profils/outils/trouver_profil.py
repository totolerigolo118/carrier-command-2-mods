"""Retrouve, en LECTURE SEULE et sans lire le rapport de portage, les adresses du profil SDK CC2X dans le nouvel exe.

Méthode : pour chaque adresse de l'ancien profil (ancien exe 0x6a36c177), on désassemble (capstone) une fenêtre de code
à partir de cette adresse, on masque uniquement les octets qui portent une adresse absolue de l'image ou un saut relatif,
et on cherche cette fenêtre dans le code du nouvel exe : une seule correspondance exigée. Les constantes (décalages de
champs, tailles, valeurs) restent dans le motif : elles sont donc vérifiées au passage. Pour chaque adresse masquée,
on affiche la valeur correspondante dans le nouvel exe (contrôle de cohérence des décalages).
Pour les données (table du serveur, nilobject, vtable PhysX) : on part du code de l'ancien exe qui y fait référence.

Usage : python -I -B trouver_profil.py <ancien.exe> <nouveau.exe>
"""
import re
import struct
import sys

import capstone as cs

BASE = 0x400000


class PE:
    def __init__(self, chemin):
        self.b = open(chemin, 'rb').read()
        e = struct.unpack_from('<I', self.b, 0x3c)[0]
        self.ts = struct.unpack_from('<I', self.b, e + 8)[0]
        nsec = struct.unpack_from('<H', self.b, e + 6)[0]
        opt = struct.unpack_from('<H', self.b, e + 20)[0]
        self.taille = struct.unpack_from('<I', self.b, e + 24 + 56)[0]
        self.sections = []
        for i in range(nsec):
            o = e + 24 + opt + 40 * i
            nom = self.b[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
            vsize, rva, rsize, rptr = struct.unpack_from('<IIII', self.b, o + 8)
            car = struct.unpack_from('<I', self.b, o + 36)[0]
            self.sections.append((nom, BASE + rva, vsize, rptr, rsize, car))

    def off(self, va):
        for nom, sva, vs, rp, rs, car in self.sections:
            if sva <= va < sva + min(vs, rs):
                return rp + va - sva
        raise ValueError('hors fichier : %#x' % va)

    def lire(self, va, n):
        o = self.off(va)
        return self.b[o:o + n]

    def u32(self, va):
        return struct.unpack('<I', self.lire(va, 4))[0]

    def code(self):
        return [(s[1], s[3], s[4]) for s in self.sections if s[5] & 0x20000000]

    def dans_image(self, v):
        return BASE <= v < BASE + self.taille


MD = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_32)
MD.detail = True


def fenetre(pe, va, n):
    """Instructions couvrant au moins n octets depuis va ; renvoie (octets, masque, refs) ; refs = [(pos, ancienne valeur)]."""
    brut = pe.lire(va, n + 16)
    octets, masque, refs, insns = bytearray(), [], [], []
    for i in MD.disasm(brut, va):
        debut = len(octets)
        octets += i.bytes
        m = [False] * i.size
        rel = any(g in (cs.CS_GRP_JUMP, cs.CS_GRP_CALL) for g in i.groups) and i.imm_size and \
            any(op.type == cs.x86.X86_OP_IMM for op in i.operands)
        if i.imm_size and (rel or pe.dans_image(int.from_bytes(i.bytes[i.imm_offset:i.imm_offset + 4], 'little')
                                                if i.imm_size == 4 else 0)):
            for k in range(i.imm_offset, i.imm_offset + i.imm_size):
                m[k] = True
            if rel:
                refs.append((debut + i.imm_offset, i.imm_size, 'rel', i.operands[0].imm))
            else:
                refs.append((debut + i.imm_offset, 4, 'abs', int.from_bytes(i.bytes[i.imm_offset:i.imm_offset + 4], 'little')))
        if i.disp_size == 4:
            d = int.from_bytes(i.bytes[i.disp_offset:i.disp_offset + 4], 'little')
            if pe.dans_image(d):
                for k in range(i.disp_offset, i.disp_offset + 4):
                    m[k] = True
                refs.append((debut + i.disp_offset, 4, 'abs', d))
        masque += m
        insns.append((i.address, i.mnemonic, i.op_str))
        if len(octets) >= n:
            break
    return bytes(octets), masque, refs, insns


def motif(octets, masque):
    return re.compile(b''.join(b'.' if m else re.escape(bytes([x])) for x, m in zip(octets, masque)), re.DOTALL)


def chercher(pe, rx):
    trouves = []
    for sva, rp, rs in pe.code():
        for m in rx.finditer(pe.b, rp, rp + rs):
            trouves.append(sva + m.start() - rp)
    return trouves


def valeur_nouvelle(pe_n, va_n, pos, taille, genre):
    raw = pe_n.lire(va_n + pos, taille)
    v = int.from_bytes(raw, 'little', signed=(genre == 'rel'))
    if genre == 'rel':
        return (va_n + pos + taille + v) & 0xffffffff
    return v


def apparier(pe_a, pe_n, va, tailles=(48, 96, 160, 256)):
    for n in tailles:
        octets, masque, refs, insns = fenetre(pe_a, va, n)
        tr = chercher(pe_n, motif(octets, masque))
        if len(tr) == 1:
            va_n = tr[0]
            couples = [(genre, ancien, valeur_nouvelle(pe_n, va_n, pos, t, genre)) for pos, t, genre, ancien in refs]
            return va_n, len(octets), couples, insns
        if not tr:
            return None, len(octets), [], insns
    return 'ambigu', len(octets), [], insns


def references_code(pe, valeur):
    """Instructions de l'ancien exe dont un opérande vaut exactement `valeur` (adresse absolue)."""
    cle = struct.pack('<I', valeur)
    res = []
    for sva, rp, rs in pe.code():
        o = pe.b.find(cle, rp, rp + rs)
        while o != -1:
            for recul in range(1, 8):
                debut = sva + o - rp - recul
                ins = next(MD.disasm(pe.lire(debut, 16), debut), None)
                if ins and ins.size > recul and (
                        (ins.disp_size == 4 and ins.disp_offset == recul) or (ins.imm_size == 4 and ins.imm_offset == recul)):
                    res.append(debut)
                    break
            o = pe.b.find(cle, o + 1, rp + rs)
    return res


CODE = {
    # cc2x.c Profile
    'server_init': 0x00772fd0, 'server_tick': 0x0077ee10, 'server_end': 0x0077eea0,
    'lua_site': 0x004465ec,
    'f_index2addr': 0x008cda70, 'f_auxsetstr': 0x008ce200, 'f_finishset': 0x008ff6b0, 'f_luaS_new': 0x00908220,
    'f_luaH_new': 0x00904a50, 'f_luaC_step': 0x00904050,
    # world.c Layout
    'f_vehicle_by_id': 0x005ee6a0, 'f_tile_by_id': 0x00631240, 'f_tile_at': 0x00631040,
    'f_request_landing': 0x0062b4a0, 'f_waypoints_clear': 0x00854870, 'f_deque_grow': 0x00860c90,
    'h_waypoints': 0x007781d4, 'h_hangar': 0x0062ae8d, 'h_hangar_found': 0x0062aefc, 'h_hangar_none': 0x0062aead,
    'h_controller[0]': 0x0063014f, 'h_controller[1]': 0x00634981, 'h_spawn': 0x00634f3d, 'f_spawn': 0x0062ca30,
    'h_af_tick': 0x0062b8f3, 'f_af_tick': 0x00628600,
}
DONNEES = {'server_vtable': 0x00d34bc4, 'nilobject': 0x00d03518, 'vt_rigid_dynamic': 0x00cdd478}


def main():
    A, N = PE(sys.argv[1]), PE(sys.argv[2])
    print('ancien : horodatage %#x taille %#x ; nouveau : horodatage %#x taille %#x' % (A.ts, A.taille, N.ts, N.taille))
    print('sections ancien :', [(s[0], hex(s[1]), hex(s[2])) for s in A.sections])
    print('sections nouveau:', [(s[0], hex(s[1]), hex(s[2])) for s in N.sections])
    trouve = {}
    print('\n== CODE : une fenêtre de l\'ancien exe, cherchée dans tout le code du nouveau')
    for nom, va in CODE.items():
        va_n, n, couples, insns = apparier(A, N, va)
        if isinstance(va_n, int):
            trouve[nom] = va_n
            deltas = sorted({(g, (nv - av) & 0xffffffff) for g, av, nv in couples})
            print('%-18s ancien %#010x -> nouveau %#010x (écart %+#x), fenêtre %d o, 1 seule correspondance' % (
                nom, va, va_n, va_n - va, n))
            for g, av, nv in couples:
                print('      ref %s %#010x -> %#010x (%+#x)' % (g, av, nv, (nv - av if nv >= av else -(av - nv))))
        else:
            print('%-18s ancien %#010x -> %s (fenêtre %d o)' % (nom, va, va_n, n))
            for x in insns[:12]:
                print('      %#x %s %s' % x)

    print('\n== DONNÉES : par le code de l\'ancien exe qui y fait référence')
    for nom, va in DONNEES.items():
        refs = references_code(A, va)
        print('%s ancien %#010x : %d instruction(s) de code y font référence' % (nom, va, len(refs)))
        vus = {}
        for r in refs[:40]:
            va_n, n, couples, insns = apparier(A, N, r)
            if not isinstance(va_n, int):
                print('    depuis %#x : %s' % (r, va_n))
                continue
            nv = [c[2] for c in couples if c[0] == 'abs' and c[1] == va]
            for v in nv:
                vus[v] = vus.get(v, 0) + 1
            print('    depuis %#x (-> %#x) : %s' % (r, va_n, ', '.join('%#010x' % v for v in nv)))
        print('  => valeurs nouvelles vues : %s' % {('%#010x' % k): v for k, v in vus.items()})
        if len(vus) == 1:
            trouve[nom] = next(iter(vus))

    print('\n== CONTRÔLES')
    if 'server_vtable' in trouve:
        t = trouve['server_vtable']
        a3 = [A.u32(DONNEES['server_vtable'] + 4 * k) for k in range(3)]
        n3 = [N.u32(t + 4 * k) for k in range(3)]
        print('table serveur ancien %s ; nouveau %s ; attendu (fonctions appariées) %s' % (
            [hex(x) for x in a3], [hex(x) for x in n3],
            [hex(trouve.get(k, 0)) for k in ('server_init', 'server_tick', 'server_end')]))
        avant_a = [A.u32(DONNEES['server_vtable'] - 4 * k) for k in range(1, 4)]
        avant_n = [N.u32(t - 4 * k) for k in range(1, 4)]
        print('  3 cases avant la table : ancien %s ; nouveau %s' % ([hex(x) for x in avant_a], [hex(x) for x in avant_n]))
        brut = struct.pack('<III', *[trouve.get(k, 0) for k in ('server_init', 'server_tick', 'server_end')])
        occ = [m.start() for m in re.finditer(re.escape(brut), N.b)]
        print('  le triplet (init, tick, end) apparié apparaît %d fois dans le fichier nouveau' % len(occ))
    if 'nilobject' in trouve:
        print('nilobject : ancien %s ; nouveau %s' % (A.lire(DONNEES['nilobject'], 16).hex(), N.lire(trouve['nilobject'], 16).hex()))
    if 'vt_rigid_dynamic' in trouve:
        t = trouve['vt_rigid_dynamic']
        print('vtable PhysX (8 premières cases) : ancien %s' % [hex(A.u32(DONNEES['vt_rigid_dynamic'] + 4 * k)) for k in range(8)])
        print('                                   nouveau %s' % [hex(N.u32(t + 4 * k)) for k in range(8)])
    sig = {'f_index2addr': '8b4114 85d27e0dc1', 'f_auxsetstr': '558bec83ec085356', 'f_finishset': '558bec83e4f883ec',
           'f_luaS_new': '558bec83ec08538b', 'f_luaH_new': '568b711033d26a20', 'f_luaC_step': '538bd956578b7b10'}
    for k, s in sig.items():
        if k in trouve:
            print('LUA_SIGS %-13s %#010x : %s' % (k, trouve[k], 'OK' if N.lire(trouve[k], 8) == bytes.fromhex(s.replace(' ', '')) else 'DIFFÉRENT'))
    if 'lua_site' in trouve:
        print('lua_site %#010x : %s (attendu 6a20898564ffffff)' % (trouve['lua_site'], N.lire(trouve['lua_site'], 8).hex()))
    print('\n== RÉSUMÉ (valeurs trouvées ici)')
    for k in list(DONNEES) + list(CODE):
        print('  %-18s %s' % (k, ('%#010x' % trouve[k]) if k in trouve else 'NON TROUVÉ'))


if __name__ == '__main__':
    main()
