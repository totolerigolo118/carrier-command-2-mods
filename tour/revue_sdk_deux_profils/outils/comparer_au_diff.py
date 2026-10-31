"""Compare les valeurs trouvées par trouver_profil.py (fichier de sortie) aux valeurs écrites dans les sources modifiées,
puis contrôle, sur une copie patchée de l'exe, que les octets autour de chaque adresse du SDK sont ceux de l'exe de Steam.

Usage : python -I -B comparer_au_diff.py <sortie_trouver_profil.txt> <cc2x.c> <world.c> <exe_steam> <exe_patché>
"""
import re
import struct
import sys

sortie, p_c, p_w, p_steam, p_patch = sys.argv[1:6]

trouve = {}
dans_resume = False
for ligne in open(sortie, 'rb').read().decode('utf-8', 'replace').splitlines():
    if ligne.startswith('== R'):
        dans_resume = True
        continue
    m = re.match(r'\s+(\S+)\s+(0x[0-9a-f]+)$', ligne)
    if dans_resume and m:
        trouve[m.group(1)] = int(m.group(2), 16)

# --- valeurs du 2e profil dans cc2x.c (ordre des champs de la structure Profile)
c = open(p_c, encoding='utf-8').read()
bloc = c[c.index('"1.5.18-win32-6ae228f3"'):]
bloc = bloc[:bloc.index('}};')]
bloc = re.sub(r'\{[^}]*\}', '', bloc)            # retire le tableau lua_site_bytes
nums = [int(x, 16) for x in re.findall(r'0x[0-9a-fA-F]+', bloc)]
champs = ['timestamp', 'image_size', 'server_vtable', 'server_init', 'server_tick', 'server_end', 'lua_site',
          'f_index2addr', 'f_auxsetstr', 'f_finishset', 'f_luaS_new', 'f_luaH_new', 'f_luaC_step', 'nilobject']
assert len(nums) == len(champs), nums
source = dict(zip(champs, nums))
octets_site = re.search(r'"1\.5\.18-win32-6ae228f3".*?\{([^}]*)\}', c, re.S).group(1)
source['lua_site_bytes'] = bytes(int(x, 16) for x in re.findall(r'0x[0-9a-fA-F]+', octets_site))

# --- valeurs du 2e Layout dans world.c
w = open(p_w, encoding='utf-8').read()
lay = w[w.index('.build = "1.5.18-win32-6ae228f3"'):]
lay = lay[:lay.index('}};')]
for nom, val in re.findall(r'\.(\w+) = (0x[0-9a-fA-F]+)', lay):
    source[nom] = int(val, 16)
m = re.search(r'\.h_controller = \{(0x[0-9a-f]+), (0x[0-9a-f]+)\}', lay)
source['h_controller[0]'], source['h_controller[1]'] = int(m.group(1), 16), int(m.group(2), 16)
# décalages de champs : identiques entre les deux Layout ?
lay1 = w[w.index('.build = "1.5.18-win32"'):w.index('.build = "1.5.18-win32-6ae228f3"')]
off1 = dict(re.findall(r'\.(\w+) = (0x[0-9a-fA-F]+)', lay1))
off2 = dict(re.findall(r'\.(\w+) = (0x[0-9a-fA-F]+)', lay))
adresses = {'f_vehicle_by_id', 'f_tile_by_id', 'f_tile_at', 'f_request_landing', 'f_waypoints_clear', 'f_deque_grow',
            'vt_rigid_dynamic', 'h_waypoints', 'h_hangar', 'h_hangar_found', 'h_hangar_none', 'h_spawn', 'f_spawn',
            'h_af_tick', 'f_af_tick'}
dec1 = {k: v for k, v in off1.items() if k not in adresses}
dec2 = {k: v for k, v in off2.items() if k not in adresses}
print('décalages de champs (hors adresses) : %d dans le 1er Layout, %d dans le 2e, identiques : %s' % (
    len(dec1), len(dec2), dec1 == dec2))
octs1 = re.findall(r'_bytes = (\{.*?\}\}|\{.*?\})', lay1)
octs2 = re.findall(r'_bytes = (\{.*?\}\}|\{.*?\})', lay)
print('octets attendus des sites (h_*_bytes) identiques entre les deux Layout :', octs1 == octs2)

print('\n%-18s %-12s %-12s %s' % ('champ', 'source', 'trouvé ici', 'accord'))
ecarts = 0
for k in sorted(trouve):
    s = source.get(k)
    ok = s == trouve[k]
    ecarts += not ok
    print('%-18s %-12s %-12s %s' % (k, '%#010x' % s if s is not None else 'ABSENT', '%#010x' % trouve[k], 'OUI' if ok else '*** ÉCART ***'))
print('timestamp source %#x, image_size %#x' % (source['timestamp'], source['image_size']))
print('=> %d valeurs comparées, %d écart(s)' % (len(trouve), ecarts))


# --- copie patchée : octets identiques autour de chaque adresse ?
def sections(b):
    e = struct.unpack_from('<I', b, 0x3c)[0]
    n = struct.unpack_from('<H', b, e + 6)[0]
    opt = struct.unpack_from('<H', b, e + 20)[0]
    out = []
    for i in range(n):
        o = e + 24 + opt + 40 * i
        vs, rva, rs, rp = struct.unpack_from('<IIII', b, o + 8)
        out.append((0x400000 + rva, min(vs, rs), rp))
    return out, struct.unpack_from('<I', b, e + 8)[0], struct.unpack_from('<I', b, e + 24 + 56)[0]


S = open(p_steam, 'rb').read()
P = open(p_patch, 'rb').read()
secs, ts_s, soi_s = sections(S)
_, ts_p, soi_p = sections(P)
print('\ncopie patchée : %d octets, horodatage %#x (Steam %#x), taille d\'image %#x (Steam %#x)' % (len(P), ts_p, ts_s, soi_p, soi_s))
assert len(S) == len(P)
diffs = [i for i in range(len(S)) if S[i] != P[i]] if False else None
import itertools
ia = memoryview(S)
ib = memoryview(P)
# plages modifiées (rapide : par blocs de 4096)
plages = []
for blk in range(0, len(S), 4096):
    if ia[blk:blk + 4096] != ib[blk:blk + 4096]:
        for i in range(blk, min(blk + 4096, len(S))):
            if S[i] != P[i]:
                if plages and plages[-1][1] == i:
                    plages[-1][1] = i + 1
                else:
                    plages.append([i, i + 1])


def off2va(o):
    for va, taille, rp in secs:
        if rp <= o < rp + taille:
            return va + o - rp
    return None


pva = [(off2va(a), off2va(b - 1) + 1 if off2va(b - 1) else None) for a, b in plages]
print('%d plage(s) d\'octets changées par les patchs (%d octets en tout)' % (len(plages), sum(b - a for a, b in plages)))
longueurs = {'server_vtable': 12, 'lua_site': 8, 'h_waypoints': 6, 'h_hangar': 5, 'h_controller[0]': 7,
             'h_controller[1]': 7, 'h_spawn': 5, 'h_af_tick': 5}
mini = None
for k, va in source.items():
    if not isinstance(va, int) or k in ('timestamp', 'image_size') or va < 0x400000 or (k not in trouve):
        continue
    n = longueurs.get(k, 8)
    for a, b in pva:
        if a is None:
            continue
        d = max(a - (va + n), va - b, 0)
        if mini is None or d < mini[0]:
            mini = (d, k, a, b)
print('distance minimale entre une adresse du SDK (et sa longueur) et un octet patché : %d octets (%s, plage %#x-%#x)' % mini)
memes = 0
for k in trouve:
    va = source[k]
    o = None
    for sva, taille, rp in secs:
        if sva <= va < sva + taille:
            o = rp + va - sva
    if S[o - 64:o + 64] == P[o - 64:o + 64]:
        memes += 1
    else:
        print('  octets DIFFÉRENTS autour de', k)
print('fenêtres de 128 octets autour des %d adresses identiques entre exe de Steam et copie patchée : %d/%d' % (
    len(trouve), memes, len(trouve)))
