#!/usr/bin/env python3
"""Etape 1 : cherche dans carrier_command.exe (1.5.18, 32 bits) les empreintes de la
section 6 de PASSATION_windows.md. LECTURE SEULE : ne modifie aucun fichier du jeu.

Usage : python -I etape1_empreintes.py <exe> <rapport.md>

Methode (sans desassembleur) : une constante flottante lue par du code 32 bits l'est par
une adresse absolue (disp32 apres un modrm 0x05). On cherche donc (1) ou la constante
est rangee dans les sections de donnees, (2) tous les endroits du code qui contiennent
cette adresse sur 4 octets, que l'on decode par l'octet d'operation (movss, mulss...).
Les adresses affichees sont des adresses d'image, base 0x400000, comme Ghidra / IDA.
"""
import struct
import sys
import hashlib
import collections

EXE, OUT = sys.argv[1], sys.argv[2]

FLOATS = {
    '0.4': 0x3ECCCCCD, '0.8': 0x3F4CCCCD, '0.6': 0x3F19999A, '0.2': 0x3E4CCCCD,
    '0.025': 0x3CCCCCCD, '-0.025': 0xBCCCCCCD, '0.001': 0x3A83126F,
    '1/6': 0x3E2AAAAB, '-1/6': 0xBE2AAAAB, '1/30': 0x3D088889, '-1/30': 0xBD088889,
    '0.04': 0x3D23D70A, '-0.04': 0xBD23D70A, '0.05': 0x3D4CCCCD, '2.5': 0x40200000,
    '11.0': 0x41300000, '12.0': 0x41400000, '30.0': 0x41F00000,
    '0.01': 0x3C23D70A, '0.1': 0x3DCCCCCD, '0.5': 0x3F000000,
    '48': 0x42400000, '72': 0x42900000, '144': 0x43100000,
    '600': 0x44160000, '1800': 0x44E10000, '-1800': 0xC4E10000,
    '80': 0x42A00000, '1200': 0x44960000, '1000': 0x447A0000, '-1000': 0xC47A0000,
    '50': 0x42480000, '100': 0x42C80000, '120': 0x42F00000, '20': 0x41A00000,
    '70': 0x428C0000, '23.5': 0x41BC0000, '-2.0': 0xC0000000,
}
VECTORS = {
    'vec(1000,-600,0,0)': struct.pack('<4f', 1000.0, -600.0, 0.0, 0.0),
    'vec(-1000,600,0,0)': struct.pack('<4f', -1000.0, 600.0, 0.0, 0.0),
    'vec(1000,1800,0,0) [deja patche ?]': struct.pack('<4f', 1000.0, 1800.0, 0.0, 0.0),
}
STRINGS = [b'lift_constraint', b'load_lift_lower', b'runway_start', b'runway_end',
           b'lift_lower', b'lift_upper', b'hanger_center', b'vehicle_ai_wing_cruise_speed',
           b'docking_queue', b'runway_state', b'vehicle_id_crane', b'crane_instructions',
           b'docking_join_time', b'docking_manager_air', b'c_vehicle_server_carrier']
ENERGY_IMM = {'0.8': 0x3F4CCCCD, '0.6': 0x3F19999A, '0.4': 0x3ECCCCCD, '0.2': 0x3E4CCCCD}

data = open(EXE, 'rb').read()
sha = hashlib.sha256(data).hexdigest().upper()

pe = struct.unpack_from('<I', data, 0x3C)[0]
assert data[pe:pe + 4] == b'PE\0\0'
nsec = struct.unpack_from('<H', data, pe + 6)[0]
optsz = struct.unpack_from('<H', data, pe + 20)[0]
opt = pe + 24
assert struct.unpack_from('<H', data, opt)[0] == 0x10B, 'pas un PE32'
imagebase = struct.unpack_from('<I', data, opt + 28)[0]
timestamp = struct.unpack_from('<I', data, pe + 8)[0]
secs = []
for i in range(nsec):
    o = opt + optsz + 40 * i
    name = data[o:o + 8].rstrip(b'\0').decode('latin1')
    vsize, va, rawsz, rawptr = struct.unpack_from('<IIII', data, o + 8)
    flags = struct.unpack_from('<I', data, o + 36)[0]
    n = min(vsize, rawsz)
    secs.append(dict(name=name, va=imagebase + va, vsize=vsize, rawptr=rawptr,
                     rawsz=rawsz, flags=flags, exec=bool(flags & 0x20000000),
                     bytes=data[rawptr:rawptr + n]))

code = [s for s in secs if s['exec']]
rest = [s for s in secs if not s['exec'] and s['rawsz'] > 0]


def find_all(hay, pat, step=1):
    i = hay.find(pat)
    while i != -1:
        yield i
        i = hay.find(pat, i + 1)


def section_of(va):
    for s in secs:
        if s['va'] <= va < s['va'] + s['vsize']:
            return s['name']
    return '?'


SS = {0x10: 'movss', 0x11: 'movss(ecrit)', 0x58: 'addss', 0x59: 'mulss', 0x5C: 'subss',
      0x5E: 'divss', 0x5D: 'minss', 0x5F: 'maxss', 0x5A: 'cvtss2sd', 0x51: 'sqrtss',
      0x2A: 'cvtsi2ss', 0xC2: 'cmpss'}
PS = {0x28: 'movaps', 0x29: 'movaps(ecrit)', 0x10: 'movups', 0x11: 'movups(ecrit)',
      0x54: 'andps', 0x57: 'xorps', 0x58: 'addps', 0x59: 'mulps', 0x5C: 'subps',
      0x5E: 'divps', 0x2F: 'comiss', 0x2E: 'ucomiss', 0x5D: 'minps', 0x5F: 'maxps',
      0x14: 'unpcklps', 0xC6: 'shufps', 0x12: 'movlps', 0x16: 'movhps'}
X87 = {(0xD9, 0x05): 'fld', (0xD8, 0x0D): 'fmul', (0xD8, 0x05): 'fadd', (0xD8, 0x25): 'fsub',
       (0xD8, 0x35): 'fdiv', (0xD8, 0x15): 'fcom', (0xD8, 0x1D): 'fcomp'}


def decode(c, p):
    """c = octets de la section, p = decalage du disp32. Renvoie (mnemonique, registre)."""
    m = c[p - 1] if p >= 1 else 0
    if p >= 2 and (c[p - 2], m) in X87:
        return X87[(c[p - 2], m)] + ' dword', ''
    if (m & 0xC7) == 0x05 and p >= 3:
        reg = 'xmm%d' % ((m >> 3) & 7)
        op = c[p - 2]
        if p >= 4 and c[p - 3] == 0x0F and c[p - 4] in (0xF3, 0xF2, 0x66):
            if c[p - 4] == 0xF3:
                return SS.get(op, 'op0F%02X(F3)' % op), reg
            if c[p - 4] == 0x66:
                return PS.get(op, 'op0F%02X' % op) + '(66)', reg
            return 'op0F%02X(F2)' % op, reg
        if c[p - 3] == 0x0F:
            return PS.get(op, 'op0F%02X' % op), reg
    return '?', ''


def refs_to(va):
    """Tous les endroits du code qui contiennent l'adresse va sur 4 octets."""
    pat = struct.pack('<I', va)
    out = []
    for s in code:
        for p in find_all(s['bytes'], pat):
            mn, reg = decode(s['bytes'], p)
            a = max(0, p - 6)
            out.append(dict(va=s['va'] + p, mn=mn, reg=reg,
                            hexa=s['bytes'][a:p + 4].hex(' '), sec=s['name']))
    return out


lines = []


def w(s=''):
    lines.append(s)


w('# Etape 1 : empreintes dans carrier_command.exe (resultat brut du script)')
w()
w('Script : `tour/outils/etape1_empreintes.py` (lecture seule). Fichier lu : copie de sauvegarde.')
w()
w('- sha256 : `%s`' % sha)
w('- taille fichier : %d ; ImageBase 0x%x ; horodatage PE 0x%08x' % (len(data), imagebase, timestamp))
w()
w('| section | adresse | taille virtuelle | taille fichier | exec |')
w('|---|---|---|---|---|')
for s in secs:
    w('| %s | 0x%08x | 0x%x | 0x%x | %s |' % (s['name'], s['va'], s['vsize'], s['rawsz'], 'oui' if s['exec'] else ''))
w()

# 1. emplacements des constantes (donnees) et lectures dans le code
w('## 1. Constantes flottantes : ou elles sont rangees, combien de lectures dans le code')
w()
w('| valeur | bits | copies en donnees | lectures dans le code (total) |')
w('|---|---|---|---|')
const_refs = {}   # nom -> liste de refs (toutes copies confondues)
const_locs = {}
for name, bits in FLOATS.items():
    pat = struct.pack('<I', bits)
    locs = []
    for s in rest:
        for p in find_all(s['bytes'], pat):
            if p % 4 == 0:
                locs.append(s['va'] + p)
    refs = []
    for va in locs:
        for r in refs_to(va):
            r['const_va'] = va
            refs.append(r)
    refs.sort(key=lambda r: r['va'])
    const_locs[name] = locs
    const_refs[name] = refs
    w('| %s | 0x%08X | %d | %d |' % (name, bits, len(locs), len(refs)))
w()

# 2. detail des lectures pour les constantes peu communes
w('## 2. Detail des lectures (limite a 60 par constante)')
w()
for name, refs in const_refs.items():
    w('### %s (copies en donnees : %s)' % (name, ', '.join('0x%08x' % v for v in const_locs[name][:6]) or 'aucune'))
    for r in refs[:60]:
        w('- 0x%08x [%s] %s %s  (constante 0x%08x)  octets : `%s`' % (r['va'], r['sec'], r['mn'], r['reg'], r['const_va'], r['hexa']))
    if len(refs) > 60:
        w('- ... %d de plus' % (len(refs) - 60))
    w()

# 3. vecteurs de 4 nombres
w('## 3. Vecteurs de 4 nombres (atterrissage)')
w()
vec_refs = {}
for name, pat in VECTORS.items():
    locs = []
    for s in secs:
        if s['rawsz'] == 0:
            continue
        for p in find_all(s['bytes'], pat):
            locs.append((s['va'] + p, s['name']))
    refs = []
    for va, _ in locs:
        for r in refs_to(va):
            r['const_va'] = va
            refs.append(r)
    refs.sort(key=lambda r: r['va'])
    vec_refs[name] = refs
    w('### %s : copies %s' % (name, ', '.join('0x%08x (%s, align16=%s)' % (va, sn, va % 16 == 0) for va, sn in locs) or 'aucune'))
    for r in refs:
        w('- 0x%08x %s %s  (vecteur 0x%08x)  octets : `%s`' % (r['va'], r['mn'], r['reg'], r['const_va'], r['hexa']))
    w()

# 4. chaines
w('## 4. Chaines qui existent dans tous les builds')
w()
w('| chaine | adresse(s) | nombre de references (code + donnees) |')
w('|---|---|---|')
str_refs = {}
for sname in STRINGS:
    locs = []
    for s in secs:
        if s['rawsz'] == 0:
            continue
        for p in find_all(s['bytes'], sname + b'\0'):
            if p == 0 or s['bytes'][p - 1] == 0:
                locs.append(s['va'] + p)
    allr = []
    for va in locs:
        pat = struct.pack('<I', va)
        for s in secs:
            if s['rawsz'] == 0:
                continue
            for p in find_all(s['bytes'], pat):
                allr.append((s['va'] + p, s['name']))
    str_refs[sname] = (locs, allr)
    w('| `%s` | %s | %d |' % (sname.decode(), ', '.join('0x%08x' % v for v in locs) or 'ABSENTE', len(allr)))
w()
for sname, (locs, allr) in str_refs.items():
    if allr:
        w('- `%s` utilisee en : %s' % (sname.decode(), ', '.join('0x%08x (%s)' % a for a in allr[:12])))
w()

# 5. groupes
def near(anchor, others, window):
    rows = []
    for a in const_refs[anchor]:
        row = [a]
        ok = True
        for o in others:
            cand = [r for r in const_refs[o] if abs(r['va'] - a['va']) <= window]
            if not cand:
                ok = False
                row.append(None)
            else:
                row.append(min(cand, key=lambda r: abs(r['va'] - a['va'])))
        rows.append((ok, row))
    return rows


w('## 5. Groupes (voisinage dans le code)')
w()


def report_group(title, anchor, others, window, show=40):
    rows = near(anchor, others, window)
    good = [r for ok, r in rows if ok]
    w('### %s' % title)
    w('Ancre %s (%d lectures), voisins %s dans +/-%d octets : **%d ancres avec tous les voisins**.' % (anchor, len(rows), others, window, len(good)))
    for row in good[:show]:
        w('- ' + ' | '.join('%s@0x%08x %s' % (n, r['va'], r['mn']) for n, r in zip([anchor] + others, row)))
    w()


report_group('Plateforme : 0,025 et 0,001', '0.025', ['0.001'], 300)
report_group('Plateforme : -0,025 et 0,001', '-0.025', ['0.001'], 300)
report_group('Roulage : 2,5 et 0,05 (7 paires attendues)', '2.5', ['0.05'], 120)
report_group('Grue : 1/6, 1/30, 11, 12', '1/6', ['1/30', '11.0', '12.0'], 900)
report_group('Grue : -1/6, -1/30', '-1/6', ['-1/30'], 900)
report_group('Rotation grue 0,04 pres de 1/6', '0.04', ['1/6'], 900)
report_group('Vitesse IA : 144, 48, 72', '144', ['48', '72'], 500)
report_group('Atterrissage : 600 pres des vecteurs et de 1200 / 80', '600', ['1200', '80'], 3000)

w('### Energie : immediats 0,8 / 0,6 / 0,4 / 0,2 dans le code')
imm = {}
for name, bits in ENERGY_IMM.items():
    pat = struct.pack('<I', bits)
    pos = []
    for s in code:
        for p in find_all(s['bytes'], pat):
            pos.append(s['va'] + p)
    imm[name] = pos
    w('- %s : %d occurrences en immediat' % (name, len(pos)))
cl = []
for a in imm['0.4']:
    near8 = [x for x in imm['0.8'] if abs(x - a) <= 400]
    near6 = [x for x in imm['0.6'] if abs(x - a) <= 400]
    near2 = [x for x in imm['0.2'] if abs(x - a) <= 400]
    if near8 and near6 and near2:
        cl.append((a, near8, near6, near2))
w('Groupes {0,8 ; 0,6 ; 0,4 ; 0,2} a moins de 400 octets : **%d**' % len(cl))
for a, n8, n6, n2 in cl[:20]:
    sec = next(s for s in code if s['va'] <= a < s['va'] + s['vsize'])
    off = a - sec['va']
    ctx = sec['bytes'][max(0, off - 3):off + 4].hex(' ')
    w('- 0,4 en 0x%08x (octets autour : `%s`) ; 0,8 en %s ; 0,6 en %s ; 0,2 en %s' % (
        a, ctx, ', '.join('0x%08x' % x for x in n8), ', '.join('0x%08x' % x for x in n6), ', '.join('0x%08x' % x for x in n2)))
w()

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

# resume console
print('sha256', sha)
print('ImageBase 0x%x, horodatage 0x%08x, %d sections' % (imagebase, timestamp, nsec))
for name in ('0.4', '0.025', '-0.025', '0.001', '2.5', '0.05', '1/6', '1/30', '0.04', '11.0', '12.0', '30.0',
             '48', '72', '144', '600', '-1800', '1200', '80'):
    print('%-8s copies=%d lectures=%d' % (name, len(const_locs[name]), len(const_refs[name])))
for name, refs in vec_refs.items():
    print('%-40s lectures=%d' % (name, len(refs)))
for sname, (locs, allr) in str_refs.items():
    print('%-32s %s refs=%d' % (sname.decode(), 'ABSENTE' if not locs else 'presente', len(allr)))
print('groupes energie 0,8/0,6/0,4/0,2 :', len(cl))
print('rapport ecrit :', OUT)
