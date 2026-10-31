#!/usr/bin/env python3
"""Etape 3 : table des sites du groupe `energy_lift_crane_taxi` (module Mac ascenseur_x2).

Pour CHAQUE site, relit l'instruction dans carrier_command.exe avec capstone et verifie :
  - une seule instruction de la longueur annoncee, au mnemonique annonce ;
  - son operande memoire est une adresse absolue (pas de registre) ;
  - la constante lue vaut bien la valeur d'origine du reglage (float 32 bits exact) ;
  - le disp32 est bien les 4 derniers octets (decalage `off`).
Puis ecrit la table en C dans extension_windows/src/cp_groups.c, entre les reperes
BEGIN/END WINDOWS SITES. Les octets sont ceux du FICHIER .exe, jamais ecrits a la main.

Usage : python -I generer_groupe_energie.py <exe> <cp_groups.c> <rapport.md>
"""
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

EXE, CFILE, REPORT = sys.argv[1], sys.argv[2], sys.argv[3]

# valeur d'origine de chaque reglage (cp_tunables.c, colonne stock)
STOCK = {
    'CP_T_PLATFORM_STEP': 0.025, 'CP_T_PLATFORM_STEP_NEG': -0.025,
    'CP_T_CRANE_H': 1.0 / 6.0, 'CP_T_CRANE_H_NEG': -1.0 / 6.0,
    'CP_T_CRANE_V': 1.0 / 30.0, 'CP_T_CRANE_V_NEG': -1.0 / 30.0,
    'CP_T_CRANE_ROT': 0.04, 'CP_T_CRANE_ROT_NEG': -0.04,
    'CP_T_TAXI_ACCEL': 0.05, 'CP_T_TAXI_CAP': 2.5,
    'CP_T_ENERGY_SHARE': 0.4,
}

# (adresse d'image, reglage, mnemonique attendu, role)
ABS = [
    (0x00705c10, 'CP_T_PLATFORM_STEP', 'movss', 'plateforme : pas +0,025 (charge xmm3, sert au minss et au divss)'),
    (0x00705c3a, 'CP_T_PLATFORM_STEP_NEG', 'maxss', 'plateforme : pas -0,025 (borne basse)'),
    (0x00700f22, 'CP_T_CRANE_H', 'movss', 'grue horizontale +1/6, bloc A'),
    (0x00700f2d, 'CP_T_CRANE_H_NEG', 'movss', 'grue horizontale -1/6, bloc A'),
    (0x00700f7e, 'CP_T_CRANE_V_NEG', 'movss', 'grue verticale -1/30, bloc A'),
    (0x00700f96, 'CP_T_CRANE_V', 'movss', 'grue verticale +1/30, bloc A'),
    (0x00701031, 'CP_T_CRANE_H', 'movss', 'grue horizontale +1/6, bloc B'),
    (0x0070103c, 'CP_T_CRANE_H_NEG', 'movss', 'grue horizontale -1/6, bloc B'),
    (0x0070107f, 'CP_T_CRANE_V_NEG', 'movss', 'grue verticale -1/30, bloc B'),
    (0x007010a2, 'CP_T_CRANE_V', 'movss', 'grue verticale +1/30, bloc B'),
    (0x00701120, 'CP_T_CRANE_V', 'movss', 'grue verticale +1/30, bloc C (hauteur 12)'),
    (0x00701128, 'CP_T_CRANE_V_NEG', 'movss', 'grue verticale -1/30, bloc C (hauteur 12)'),
    (0x007011b2, 'CP_T_CRANE_V', 'movss', 'grue verticale +1/30, bloc D (hauteur 11)'),
    (0x007011ba, 'CP_T_CRANE_V_NEG', 'movss', 'grue verticale -1/30, bloc D (hauteur 11)'),
    (0x00701215, 'CP_T_CRANE_ROT', 'movss', 'grue rotation +0,04'),
    (0x00701221, 'CP_T_CRANE_ROT_NEG', 'movss', 'grue rotation -0,04'),
    (0x006f9841, 'CP_T_TAXI_ACCEL', 'addss', 'roulage : acceleration 0,05, bloc 1'),
    (0x006fb2ca, 'CP_T_TAXI_ACCEL', 'addss', 'roulage : acceleration 0,05, bloc 2'),
    (0x006fcba6, 'CP_T_TAXI_ACCEL', 'addss', 'roulage : acceleration 0,05, bloc 3'),
    (0x006fce4a, 'CP_T_TAXI_ACCEL', 'addss', 'roulage : acceleration 0,05, bloc 4'),
    (0x006fd8d1, 'CP_T_TAXI_ACCEL', 'addss', 'roulage : acceleration 0,05, bloc 5'),
    (0x006fddb1, 'CP_T_TAXI_ACCEL', 'movss', 'roulage : acceleration 0,05 chargee dans xmm2 avant l\'aiguillage (bloc 6)'),
    (0x006ffaeb, 'CP_T_TAXI_ACCEL', 'addss', 'roulage : acceleration 0,05, bloc 7'),
    (0x006f980d, 'CP_T_TAXI_CAP', 'movss', 'roulage : plafond 2,5, bloc 1'),
    (0x006fb2e5, 'CP_T_TAXI_CAP', 'movss', 'roulage : plafond 2,5, bloc 2'),
    (0x006fcbae, 'CP_T_TAXI_CAP', 'movss', 'roulage : plafond 2,5, bloc 3'),
    (0x006fce52, 'CP_T_TAXI_CAP', 'movss', 'roulage : plafond 2,5, bloc 4'),
    (0x006fd8ec, 'CP_T_TAXI_CAP', 'movss', 'roulage : plafond 2,5, bloc 5'),
    (0x006fddb9, 'CP_T_TAXI_CAP', 'movss', 'roulage : plafond 2,5 chargee dans xmm5 avant l\'aiguillage (bloc 6, sert au bloc 7)'),
    (0x006ffa64, 'CP_T_TAXI_CAP', 'movss', 'roulage : plafond 2,5, bloc 7'),
]
IMM = (0x006ea09e, 'CP_T_ENERGY_SHARE', 7, 3, 'energie : 5e ecriture de la fonction, part ascenseur / grue presumee (a confirmer par le Mac, Q3), mov [edi+8], 0,4')
# NON retouche a dessein : 0x006fb3d8 movss xmm2,[2,5] = vitesse de DEPART d'un troncon (mode 0) :
# min(2,5 ; reste). Pas d'equivalent identifie sur le Mac ; garde d'origine (voir le journal).

data = open(EXE, 'rb').read()
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


def off_of(va):
    for sva, n, rp in secs:
        if sva <= va < sva + n:
            return rp + va - sva
    raise SystemExit('adresse hors image : 0x%08x' % va)


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
errors = []
rows = []     # (addr, len, off, tunable, bytes, texte, const_va, valeur)
for addr, tun, mn, role in ABS:
    raw = data[off_of(addr):off_of(addr) + 15]
    ins = next(md.disasm(raw, addr), None)
    if ins is None:
        errors.append('0x%08x : instruction illisible' % addr)
        continue
    mems = [op for op in ins.operands if op.type == X86_OP_MEM]
    if ins.mnemonic != mn:
        errors.append('0x%08x : mnemonique %s au lieu de %s' % (addr, ins.mnemonic, mn))
    if len(mems) != 1 or mems[0].mem.base != 0 or mems[0].mem.index != 0:
        errors.append('0x%08x : operande memoire non absolue (%s %s)' % (addr, ins.mnemonic, ins.op_str))
        continue
    cva = mems[0].mem.disp & 0xFFFFFFFF
    if ins.bytes[-4:] != struct.pack('<I', cva):
        errors.append('0x%08x : le disp32 n\'est pas en fin d\'instruction' % addr)
    val = struct.unpack('<f', data[off_of(cva):off_of(cva) + 4])[0]
    if val != f32(STOCK[tun]):
        errors.append('0x%08x : la constante 0x%08x vaut %r, attendu %r (%s)' % (addr, cva, val, f32(STOCK[tun]), tun))
    rows.append((addr, ins.size, ins.size - 4, tun, bytes(ins.bytes), '%s %s' % (ins.mnemonic, ins.op_str), cva, val, role))

# site immediat de l'energie
iaddr, itun, ilen, ioff, irole = IMM
raw = data[off_of(iaddr):off_of(iaddr) + 15]
ins = next(md.disasm(raw, iaddr))
if not (ins.mnemonic == 'mov' and ins.size == ilen and 'dword ptr [edi + 8]' in ins.op_str):
    errors.append('0x%08x : instruction inattendue (%s %s)' % (iaddr, ins.mnemonic, ins.op_str))
imm_bits = struct.unpack('<I', ins.bytes[ioff:ioff + 4])[0]
if imm_bits != struct.unpack('<I', struct.pack('<f', f32(STOCK[itun])))[0]:
    errors.append('0x%08x : immediat 0x%08x, attendu 0,4' % (iaddr, imm_bits))
imm_row = (iaddr, ins.size, ioff, itun, bytes(ins.bytes), '%s %s' % (ins.mnemonic, ins.op_str), 0, 0.4, irole)

# chevauchements
allr = [imm_row] + rows
for i, a in enumerate(allr):
    for b in allr[i + 1:]:
        if a[0] < b[0] + b[1] and b[0] < a[0] + a[1]:
            errors.append('chevauchement 0x%08x / 0x%08x' % (a[0], b[0]))

if errors:
    print('ERREURS (rien n\'est ecrit) :')
    for e in errors:
        print(' -', e)
    sys.exit(1)


def cbytes(b):
    return ', '.join('0x%02x' % x for x in b)


lines = []
lines.append('/* BEGIN WINDOWS SITES energy_lift_crane_taxi')
lines.append(' * Written by tour/outils/generer_groupe_energie.py from carrier_command.exe 1.5.18 (sha256 1C9A01C3...341026):')
lines.append(' * every site was re-read with a disassembler (mnemonic, absolute operand, stock value of the constant).')
lines.append(' * Do not edit by hand: rerun the script. %d sites (the Mac module has 34: the Microsoft compiler loads' % (1 + len(rows)))
lines.append(' * 0.025 once into a register, so the platform needs 2 sites instead of 3, and the vertical crane has 8 instead of 10).')
lines.append(' * NOT patched on purpose: 0x006fb3d8 (movss xmm2, [2.5]) = starting speed of a taxi leg, min(2.5, remaining). */')
lines.append('static const cp_site SITES_ENERGY[] = {')
a, ln, off, tun, bts, txt, cva, val, role = imm_row
lines.append('    /* %s: %s */' % (role, txt))
lines.append('    { .addr = 0x%08x, .len = %d, .kind = CP_SITE_IMM, .tunable = %s, .off = %d,' % (a, ln, tun, off))
lines.append('      .expected = CP_BYTES(%s) },' % cbytes(bts))
last_role = None
for a, ln, off, tun, bts, txt, cva, val, role in rows:
    lines.append('    /* %s: %s, constante 0x%08x = %.9g */' % (role, txt, cva, val))
    lines.append('    CP_ABS_FLOAT(0x%08x, %d, %d, %s, CP_BYTES(%s)),' % (a, ln, off, tun, cbytes(bts)))
lines.append('};')
lines.append('#define N_SITES_ENERGY ((int)(sizeof(SITES_ENERGY) / sizeof(SITES_ENERGY[0])))')
lines.append('/* END WINDOWS SITES energy_lift_crane_taxi */')

raw = open(CFILE, 'rb').read().decode('utf-8')
eol = '\r\n' if '\r\n' in raw else '\n'
text = raw.replace('\r\n', '\n')
frag = '\n'.join(lines)
b0, b1 = text.find('/* BEGIN WINDOWS SITES energy_lift_crane_taxi'), text.find('/* END WINDOWS SITES energy_lift_crane_taxi */')
if b0 != -1 and b1 != -1:
    text = text[:b0] + frag + text[b1 + len('/* END WINDOWS SITES energy_lift_crane_taxi */'):]
else:
    anchor = '*/ /* END MAC-ONLY ascenseur_x2 */\n'
    k = text.find(anchor)
    if k == -1:
        sys.exit('repere END MAC-ONLY ascenseur_x2 introuvable')
    k += len(anchor)
    text = text[:k] + '\n' + frag + '\n' + text[k:]
open(CFILE, 'wb').write(text.replace('\n', eol).encode('utf-8'))

rep = ['# Etape 3 : verification des %d sites du groupe energy_lift_crane_taxi' % (1 + len(rows)), '',
       'Relus avec capstone dans `carrier_command.exe` (copie de sauvegarde). Aucune erreur. Adresses d\'image, base 0x400000.', '',
       '| adresse | long. | disp | reglage | instruction | constante lue | role |', '|---|---|---|---|---|---|---|']
for a, ln, off, tun, bts, txt, cva, val, role in allr:
    cst = ('0x%08x = %.9g' % (cva, val)) if cva else 'immediat 0,4'
    rep.append('| `0x%08x` | %d | +%d | `%s` | `%s` | %s | %s |' % (a, ln, off, tun, txt, cst, role))
open(REPORT, 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('OK : %d sites ecrits dans %s' % (len(allr), CFILE))
print('rapport :', REPORT)
