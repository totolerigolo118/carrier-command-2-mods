"""Lecture faite maison (LECTURE SEULE, rien n'est chargé) des DLL du SDK CC2X : en-têtes PE, sections, imports, exports,
TLS, imports retardés, débogage, ressources, chaînes ; comparaison entre DLL ; décodage des tables PROFILES et LAYOUTS.

Usage : python -I -B analyser_dll.py <cc2x.c modifié> <world.c modifié> <dll_nouvelle> <dll_posée> [<autres dll>...]
"""
import difflib
import hashlib
import re
import struct
import sys

import capstone as cs

NOMS_DD = ['export', 'import', 'ressources', 'exception', 'sécurité', 'relocations', 'débogage', 'architecture',
           'globalptr', 'TLS', 'load_config', 'bound_import', 'IAT', 'imports_retardés', 'CLR', 'réservé']


class DLL:
    def __init__(self, chemin):
        self.chemin = chemin
        self.b = b = open(chemin, 'rb').read()
        self.sha = hashlib.sha256(b).hexdigest().upper()
        assert b[:2] == b'MZ'
        e = self.e = struct.unpack_from('<I', b, 0x3c)[0]
        assert b[e:e + 4] == b'PE\0\0'
        (self.machine, nsec, self.ts, _, _, opt_size, self.carac) = struct.unpack_from('<HHIIIHH', b, e + 4)
        o = e + 24
        self.magic = struct.unpack_from('<H', b, o)[0]
        self.entree = struct.unpack_from('<I', b, o + 16)[0]
        self.base = struct.unpack_from('<I', b, o + 28)[0]
        self.taille_image = struct.unpack_from('<I', b, o + 56)[0]
        self.somme = struct.unpack_from('<I', b, o + 64)[0]
        self.sous_sys, self.dllcar = struct.unpack_from('<HH', b, o + 68)
        nrva = struct.unpack_from('<I', b, o + 92)[0]
        self.dd = [struct.unpack_from('<II', b, o + 96 + 8 * i) for i in range(nrva)]
        self.sections = []
        for i in range(nsec):
            s = o + opt_size + 40 * i
            nom = b[s:s + 8].rstrip(b'\0').decode('ascii', 'replace')
            vs, rva, rs, rp = struct.unpack_from('<IIII', b, s + 8)
            car = struct.unpack_from('<I', b, s + 36)[0]
            self.sections.append(dict(nom=nom, vs=vs, rva=rva, rs=rs, rp=rp, car=car))
        fin = max(s['rp'] + s['rs'] for s in self.sections)
        self.surplus = len(b) - fin

    def off(self, rva):
        for s in self.sections:
            if s['rva'] <= rva < s['rva'] + max(s['vs'], s['rs']):
                return s['rp'] + rva - s['rva']
        raise ValueError('rva hors sections %#x' % rva)

    def u32(self, rva):
        return struct.unpack_from('<I', self.b, self.off(rva))[0]

    def cstr(self, rva):
        o = self.off(rva)
        return self.b[o:self.b.index(b'\0', o)].decode('latin-1')

    def imports(self):
        rva, taille = self.dd[1]
        res = {}
        if not rva:
            return res
        i = 0
        while True:
            oft, ts, fwd, nom, ft = struct.unpack_from('<IIIII', self.b, self.off(rva + 20 * i))
            if not (oft or nom or ft):
                break
            dll = self.cstr(nom)
            fns = []
            t = oft or ft
            j = 0
            while True:
                v = self.u32(t + 4 * j)
                if not v:
                    break
                fns.append('#%d' % (v & 0xffff) if v & 0x80000000 else self.cstr(v + 2))
                j += 1
            res[dll] = fns
            i += 1
        return res

    def exports(self):
        rva, taille = self.dd[0]
        if not rva:
            return []
        (_, _, _, _, nom, base, nf, nn, af, an, ao) = struct.unpack_from('<IIHHIIIIIII', self.b, self.off(rva))
        out = []
        for k in range(nn):
            n = self.cstr(self.u32(an + 4 * k))
            ordi = struct.unpack_from('<H', self.b, self.off(ao + 2 * k))[0]
            cible = self.u32(af + 4 * ordi)
            fwd = rva <= cible < rva + taille
            out.append((n, ordi + base, ('-> ' + self.cstr(cible)) if fwd else '%#x' % cible))
        return out, self.cstr(nom)

    def tls(self):
        rva, taille = self.dd[9]
        if not rva:
            return None
        deb, fin, idx, cb, zf, car = struct.unpack_from('<IIIIII', self.b, self.off(rva))
        rappels = []
        if cb:
            k = 0
            while True:
                v = self.u32(cb - self.base + 4 * k)
                if not v:
                    break
                rappels.append('%#x' % v)
                k += 1
        return dict(debut=hex(deb), fin=hex(fin), rappels=rappels)

    def debogage(self):
        rva, taille = self.dd[6]
        out = []
        for k in range(taille // 28 if rva else 0):
            car, ts, ma, mi, typ, t, arva, aptr = struct.unpack_from('<IIHHIIII', self.b, self.off(rva) + 28 * k)
            info = ''
            if typ == 2:
                rec = self.b[aptr:aptr + t]
                info = repr(rec[:4]) + ' ' + rec[24:].rstrip(b'\0').decode('latin-1', 'replace') if rec[:4] == b'RSDS' else rec[:16].hex()
            out.append((typ, '%#x' % ts, t, aptr, info))
        return out

    def chaines(self, mini=5):
        asc = set(m.group().decode('ascii') for m in re.finditer(rb'[\x20-\x7e]{%d,}' % mini, self.b))
        uni = set(m.group().decode('utf-16le') for m in re.finditer(rb'(?:[\x20-\x7e]\x00){%d,}' % mini, self.b))
        return asc, uni

    def section(self, nom):
        for s in self.sections:
            if s['nom'] == nom:
                return s


def rwx(car):
    return ''.join(c if car & f else '-' for c, f in (('R', 0x40000000), ('W', 0x80000000), ('X', 0x20000000)))


def resume(d):
    print('\n==== %s' % d.chemin)
    print('taille %d, sha256 %s' % (len(d.b), d.sha))
    print('machine %#x (i386=0x14c), PE32=%s, DLL=%s, horodatage %#x, somme %#x, base %#x, taille image %#x, entrée %#x' % (
        d.machine, d.magic == 0x10b, bool(d.carac & 0x2000), d.ts, d.somme, d.base, d.taille_image, d.entree))
    print('sous-système %d, DllCharacteristics %#x (ASLR=%s NX=%s)' % (d.sous_sys, d.dllcar, bool(d.dllcar & 0x40), bool(d.dllcar & 0x100)))
    for s in d.sections:
        print('  section %-8s rva %#08x vs %#08x brut %#08x  %s' % (s['nom'], s['rva'], s['vs'], s['rs'], rwx(s['car'])))
    print('  répertoires non vides :', [(NOMS_DD[i], hex(r), t) for i, (r, t) in enumerate(d.dd) if r or t])
    print('  surplus après la dernière section :', d.surplus)
    print('  TLS :', d.tls())
    print('  débogage :', d.debogage())
    ex = d.exports()
    print('  exports (%s) :' % (ex[1] if ex else '-'), ex[0] if ex else [])
    for dll, fns in d.imports().items():
        print('  import %s (%d) : %s' % (dll, len(fns), ', '.join(fns)))


# ---------------------------------------------------------------- tables PROFILES / LAYOUTS
PROFILE = ['build', 'timestamp', 'image_size', 'server_vtable', 'server_init', 'server_tick', 'server_end', 'lua_site',
           'lua_site_bytes_0', 'lua_site_bytes_1', 'f_index2addr', 'f_auxsetstr', 'f_finishset', 'f_luaS_new', 'f_luaH_new',
           'f_luaC_step', 'nilobject']
LAYOUT = (['build', 'f_vehicle_by_id', 'f_tile_by_id', 'f_tile_at', 'f_request_landing', 'f_waypoints_clear', 'f_deque_grow',
           'vt_rigid_dynamic', 'h_waypoints', 'h_hangar', 'h_hangar_found', 'h_hangar_none', 'h_controller[0]', 'h_controller[1]',
           'h_spawn', 'h_af_tick'] + ['octets_%d' % k for k in range(7)] +
          ['f_spawn', 'f_af_tick', 'vt_rules_is_ai', 's_vehicle_map', 's_vehicles', 's_tile_map', 's_tiles', 's_broadcast',
           'v_id', 'v_definition', 'v_bodies', 'v_wheels', 'v_team', 'v_attached', 'v_dock_vehicle', 'v_dock_tile',
           'v_dock_airfield', 'v_fuel', 'v_waypoints', 'v_sync_count', 'v_attachments', 'v_flight_state', 'v_dock_state', 'v_hp',
           'v_team_object', 'v_control_mode', 'v_control_target', 'v_control_speed', 'v_control_power', 'v_control_taxi',
           'v_sync_data', 'vt_is_air', 'vt_is_wing', 'vt_is_rotor', 'vt_brakes', 'vt_gear', 'body_actor', 'body_pos',
           'team_is_ai', 'wheel_size', 'attachment_flying', 'waypoint_size', 'wp_type', 'wp_param', 't_id', 't_pos', 't_team',
           't_saved_count', 't_saved_set', 't_island', 'i_airfields', 'a_env', 'a_xform', 'a_hangars', 'a_hangar_count',
           'a_mode', 'a_state', 'a_runway_vehicle', 'a_end_node', 'a_start_node', 'a_path', 'a_dock_queue', 'a_undock_queue',
           'a_tile', 'env_nodes', 'node_size', 'node_pos'])


def valeurs_source(p_c, p_w):
    c = open(p_c, encoding='utf-8').read()
    w = open(p_w, encoding='utf-8').read()
    profils = []
    bloc = c[c.index('static const Profile PROFILES[] = {{'):]
    bloc = bloc[:bloc.index('}};')]
    for m in re.finditer(r'"([^"]+)",\s*(.*?)(?=\}, \{|$)', re.sub(r'/\*.*?\*/', '', bloc, flags=re.S), re.S):
        corps = m.group(2)
        octs = [int(x, 16) for x in re.findall(r'0x[0-9a-fA-F]+', re.search(r'\{([^}]*)\}', corps).group(1))]
        reste = [int(x, 16) for x in re.findall(r'0x[0-9a-fA-F]+', re.sub(r'\{[^}]*\}', '', corps))]
        v = dict(zip(['timestamp', 'image_size', 'server_vtable', 'server_init', 'server_tick', 'server_end', 'lua_site',
                      'f_index2addr', 'f_auxsetstr', 'f_finishset', 'f_luaS_new', 'f_luaH_new', 'f_luaC_step', 'nilobject'], reste))
        v['build'] = m.group(1)
        v['lua_site_bytes_0'], v['lua_site_bytes_1'] = struct.unpack('<II', bytes(octs))
        profils.append(v)
    layouts = []
    bloc = w[w.index('static const Layout LAYOUTS[] = {{'):]
    bloc = bloc[:bloc.index('}};')]
    for part in bloc.split('.build = ')[1:]:
        v = {'build': part[1:part.index('"', 1)]}
        for nom, val in re.findall(r'\.(\w+) = (0x[0-9a-fA-F]+)', part):
            v[nom] = int(val, 16)
        hc = re.search(r'\.h_controller = \{(0x[0-9a-f]+), (0x[0-9a-f]+)\}', part)
        v['h_controller[0]'], v['h_controller[1]'] = int(hc.group(1), 16), int(hc.group(2), 16)
        oct_ = []
        for nom in ('h_waypoints_bytes', 'h_hangar_bytes', 'h_controller_bytes'):
            m = re.search(r'\.%s = (\{\{.*?\}\}|\{.*?\})' % nom, part, re.S)
            oct_ += [int(x, 16) for x in re.findall(r'0x[0-9a-fA-F]+', m.group(1))]
        oct_ += [0, 0, 0]                              # remplissage d'alignement (25 octets -> 28)
        for k in range(7):
            v['octets_%d' % k] = struct.unpack_from('<I', bytes(oct_), 4 * k)[0]
        layouts.append(v)
    return profils, layouts


def decoder(d, champs, cle, taille_struct):
    """Cherche les éléments de table dont les 2 premiers champs numériques valent `cle`, décode le tableau entier."""
    motif = struct.pack('<II', *cle)
    o = d.b.find(motif)
    assert o != -1 and d.b.find(motif, o + 1) == -1, 'clé introuvable ou multiple'
    debut = o - 4
    sortie = []
    k = 0
    while True:
        oo = debut + k * taille_struct
        vals = struct.unpack_from('<%dI' % len(champs), d.b, oo)
        v = dict(zip(champs, vals))
        try:
            v['build'] = d.cstr(v['build'] - d.base)
        except Exception:
            break
        if not v['build'].startswith('1.5.18'):
            break
        sortie.append((oo, v))
        k += 1
    return sortie


def comparer_tables(d, profils, layouts):
    print('\n==== tables dans %s' % d.chemin)
    ok = True
    for nom, champs, src, cle in (('PROFILES', PROFILE, profils, (0x6a36c177, 0x00af7000)),
                                  ('LAYOUTS', LAYOUT, layouts, (0x005ee6a0, 0x00631240))):
        assert len(champs) * 4 == {'PROFILES': 68, 'LAYOUTS': 360}[nom]
        trouves = decoder(d, champs, cle, len(champs) * 4)
        print('%s : %d élément(s) dans la DLL, %d dans la source' % (nom, len(trouves), len(src)))
        for i, (oo, v) in enumerate(trouves):
            s = src[i] if i < len(src) else {}
            ecarts = [k for k in champs if v.get(k) != s.get(k)]
            ok = ok and not ecarts and len(trouves) == len(src)
            print('  [%d] fichier %#x, build "%s" : %d champs, écarts avec la source : %s' % (
                i, oo, v['build'], len(champs), ecarts or 'aucun'))
    return ok


# ---------------------------------------------------------------- comparaison du code
MD = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_32)
MD.detail = True


def instructions(d):
    s = d.section('.text')
    code = d.b[s['rp']:s['rp'] + s['vs']]
    lo, hi = d.base, d.base + d.taille_image
    out = []
    for i in MD.disasm(code, d.base + s['rva']):
        txt = i.mnemonic + ' ' + i.op_str
        txt = re.sub(r'0x[0-9a-f]+', lambda m: 'ADR' if lo <= int(m.group(), 16) < hi else m.group(), txt)
        out.append((i.address, txt))
    return out


def comparer_code(a, b):
    ia, ib = instructions(a), instructions(b)
    sm = difflib.SequenceMatcher(None, [t for _, t in ia], [t for _, t in ib], autojunk=False)
    blocs = [op for op in sm.get_opcodes() if op[0] != 'equal']
    print('\n==== code : %s (%d instr.) contre %s (%d instr.), adresses internes masquées : %d bloc(s) différent(s)' % (
        a.chemin.split('/')[-2], len(ia), b.chemin.split('/')[-2], len(ib), len(blocs)))
    print('  (les 3 premiers blocs pour exemple ; le détail fonction par fonction est dans comparer_fonctions_dll.py)')
    for tag, i1, i2, j1, j2 in blocs[:3]:
        print('  %s  A[%d:%d] (%#x)  B[%d:%d] (%#x)' % (tag, i1, i2, ia[i1][0] if i1 < len(ia) else 0, j1, j2,
                                                       ib[j1][0] if j1 < len(ib) else 0))
        for _, t in ia[max(i1 - 3, 0):i2 + 1][:40]:
            print('      A: ' + t)
        for _, t in ib[max(j1 - 3, 0):j2 + 1][:40]:
            print('      B: ' + t)
    return blocs


def main():
    p_c, p_w, p_new, p_pose = sys.argv[1:5]
    autres = sys.argv[5:]
    dlls = [DLL(p) for p in [p_new, p_pose] + autres]
    for d in dlls:
        resume(d)
    n, pose = dlls[0], dlls[1]
    print('\n==== comparaisons (nouvelle %s contre posée %s)' % (n.sha[:8], pose.sha[:8]))
    print('imports identiques :', n.imports() == pose.imports())
    print('exports identiques :', n.exports() == pose.exports())
    print('TLS identique :', n.tls() == pose.tls())
    print('sections (nom, droits) identiques :', [(s['nom'], s['car']) for s in n.sections] == [(s['nom'], s['car']) for s in pose.sections])
    print('tailles de section nouvelle - posée :', [(s['nom'], s['vs'] - t['vs']) for s, t in zip(n.sections, pose.sections)])
    print('répertoires vides/non vides identiques :', [bool(r) for r, _ in n.dd] == [bool(r) for r, _ in pose.dd])
    a_n, u_n = n.chaines()
    a_p, u_p = pose.chaines()
    print('chaînes ASCII (>=5) : nouvelle %d, posée %d' % (len(a_n), len(a_p)))
    print('  présentes seulement dans la nouvelle :', sorted(a_n - a_p))
    print('  présentes seulement dans la posée    :', sorted(a_p - a_n))
    print('chaînes UTF-16 (>=5) : nouvelle %d, posée %d ; seulement nouvelle : %s ; seulement posée : %s' % (
        len(u_n), len(u_p), sorted(u_n - u_p), sorted(u_p - u_n)))
    for d in dlls[2:]:
        print('\n-- %s contre posée : octets différents :' % d.chemin, end=' ')
        if len(d.b) == len(pose.b):
            diff = [i for i in range(len(d.b)) if d.b[i] != pose.b[i]]
            print(len(diff), ['%#x' % x for x in diff[:40]])
        else:
            print('tailles différentes (%d / %d)' % (len(d.b), len(pose.b)))
    profils, layouts = valeurs_source(p_c, p_w)
    print('\nsource : %d profil(s) %s, %d layout(s) %s' % (len(profils), [p['build'] for p in profils], len(layouts),
                                                      [l['build'] for l in layouts]))
    for d in dlls:
        comparer_tables(d, profils, layouts)
    comparer_code(pose, n)


if __name__ == '__main__':
    main()
