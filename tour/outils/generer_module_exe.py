#!/usr/bin/env python3
"""Genere la liste des octets a changer dans carrier_command.exe pour le module `ascenseur_x2`
(methode du Mac : on modifie le programme sur le disque, sans DLL ni code d'un tiers).

Source unique : la table SITES_ENERGY de extension_windows/src/cp_groups.c (31 sites relus au
desassembleur). Pour chaque site on :
  - relit les octets d'origine dans le fichier et refuse la moindre difference ;
  - choisit, pour chaque constante, une copie DEJA PRESENTE de la valeur doublee dans une section
    de donnees en LECTURE SEULE (jamais .data) ; si aucune n'existe (-1/15), la place dans le
    bourrage inutilise de l'en-tete du fichier (octets nuls entre la table des sections et
    SizeOfHeaders) ;
  - verifie que l'operande modifie a bien une entree de relocation (sinon l'adresse serait fausse
    si Windows deplace le programme) ;
  - calcule les sha256 attendus (origine, patche).
Ecrit un JSON lisible, que lit patch_exe.py. LECTURE SEULE sur l'exe.

Usage : python -I generer_module_exe.py <exe_origine> <cp_groups.c> <sortie.json> <rapport.md>
"""
import hashlib
import json
import re
import struct
import sys

EXE, CFILE, OUT_JSON, OUT_MD = sys.argv[1:5]

# valeur DOUBLEE de chaque reglage (celles validees sur le Mac)
NOUVELLE = {
    'CP_T_ENERGY_SHARE': 0.8,
    'CP_T_PLATFORM_STEP': 0.05, 'CP_T_PLATFORM_STEP_NEG': -0.05,
    'CP_T_CRANE_H': 1.0 / 3.0, 'CP_T_CRANE_H_NEG': -1.0 / 3.0,
    'CP_T_CRANE_V': 1.0 / 15.0, 'CP_T_CRANE_V_NEG': -1.0 / 15.0,
    'CP_T_CRANE_ROT': 0.08, 'CP_T_CRANE_ROT_NEG': -0.08,
    'CP_T_TAXI_ACCEL': 0.1, 'CP_T_TAXI_CAP': 5.0,
}
ANCIENNE = {   # valeur d'origine attendue de la constante lue (cp_tunables.c, colonne stock)
    'CP_T_ENERGY_SHARE': 0.4,
    'CP_T_PLATFORM_STEP': 0.025, 'CP_T_PLATFORM_STEP_NEG': -0.025,
    'CP_T_CRANE_H': 1.0 / 6.0, 'CP_T_CRANE_H_NEG': -1.0 / 6.0,
    'CP_T_CRANE_V': 1.0 / 30.0, 'CP_T_CRANE_V_NEG': -1.0 / 30.0,
    'CP_T_CRANE_ROT': 0.04, 'CP_T_CRANE_ROT_NEG': -0.04,
    'CP_T_TAXI_ACCEL': 0.05, 'CP_T_TAXI_CAP': 2.5,
}


def f32b(x):
    return struct.pack('<f', x)


data = open(EXE, 'rb').read()
sha_origine = hashlib.sha256(data).hexdigest().upper()

# ------------------------------------------------------------------ PE
pe = struct.unpack_from('<I', data, 0x3C)[0]
assert data[pe:pe + 4] == b'PE\0\0'
nsec = struct.unpack_from('<H', data, pe + 6)[0]
optsz = struct.unpack_from('<H', data, pe + 20)[0]
opt = pe + 24
base = struct.unpack_from('<I', data, opt + 28)[0]
size_of_headers = struct.unpack_from('<I', data, opt + 60)[0]
ts = struct.unpack_from('<I', data, pe + 8)[0]
size_of_image = struct.unpack_from('<I', data, opt + 56)[0]
secs = []
for i in range(nsec):
    o = opt + optsz + 40 * i
    nom = data[o:o + 8].rstrip(b'\0').decode()
    vsize, va, rawsz, rawptr = struct.unpack_from('<IIII', data, o + 8)
    fl = struct.unpack_from('<I', data, o + 36)[0]
    secs.append(dict(nom=nom, va=base + va, vsize=vsize, rawsz=rawsz, rawptr=rawptr,
                     exec=bool(fl & 0x20000000), ecriture=bool(fl & 0x80000000)))
fin_table = opt + optsz + 40 * nsec


def va_vers_off(va):
    if base <= va < base + size_of_headers:
        return va - base
    for s in secs:
        if s['va'] <= va < s['va'] + min(s['vsize'], s['rawsz']):
            return s['rawptr'] + va - s['va']
    raise SystemExit('adresse non couverte par le fichier : 0x%08x' % va)


def section_de(va):
    if base <= va < base + size_of_headers:
        return '(en-tete)'
    for s in secs:
        if s['va'] <= va < s['va'] + s['vsize']:
            return s['nom']
    return '?'


# table de relocation : ensemble des RVA qui portent une adresse absolue (type HIGHLOW)
reloc_rva, reloc_size = struct.unpack_from('<II', data, opt + 96 + 5 * 8)
relocs = set()
r_off = va_vers_off(base + reloc_rva)
p, fin = r_off, r_off + reloc_size
while p < fin:
    page, blk = struct.unpack_from('<II', data, p)
    if blk < 8:
        break
    for k in range((blk - 8) // 2):
        e = struct.unpack_from('<H', data, p + 8 + 2 * k)[0]
        if (e >> 12) == 3:
            relocs.add(page + (e & 0xFFF))
    p += blk

# ------------------------------------------------------------------ table C
texte = open(CFILE, 'r', encoding='utf-8').read().replace('\r\n', '\n')
b0 = texte.index('/* BEGIN WINDOWS SITES energy_lift_crane_taxi')
b1 = texte.index('/* END WINDOWS SITES energy_lift_crane_taxi */')
bloc = texte[b0:b1]
sites = []
commentaire = ''
lignes = bloc.split('\n')
i = 0
while i < len(lignes):
    ln = lignes[i].strip()
    if ln.startswith('/*') and ln.endswith('*/') and 'BEGIN' not in ln:
        commentaire = ln[2:-2].strip()
    m = re.match(r'CP_ABS_FLOAT\((0x[0-9a-f]+), (\d+), (\d+), (CP_T_\w+), CP_BYTES\(([^)]*)\)\),', ln)
    if m:
        sites.append(dict(kind='abs', addr=int(m.group(1), 16), len=int(m.group(2)), off=int(m.group(3)),
                          tun=m.group(4), exp=bytes(int(x, 16) for x in m.group(5).split(',')), role=commentaire))
    m = re.match(r'\{ \.addr = (0x[0-9a-f]+), \.len = (\d+), \.kind = CP_SITE_IMM, \.tunable = (CP_T_\w+), \.off = (\d+),', ln)
    if m:
        suite = lignes[i + 1].strip()
        m2 = re.match(r'\.expected = CP_BYTES\(([^)]*)\) \},', suite)
        sites.append(dict(kind='imm', addr=int(m.group(1), 16), len=int(m.group(2)), off=int(m.group(4)),
                          tun=m.group(3), exp=bytes(int(x, 16) for x in m2.group(1).split(',')), role=commentaire))
        i += 1
    i += 1
assert len(sites) == 31, 'attendu 31 sites, trouve %d' % len(sites)

# ------------------------------------------------------------------ constantes deja presentes (lecture seule)
ro = [s for s in secs if not s['exec'] and not s['ecriture'] and s['rawsz'] > 0]


def copies_lecture_seule(bits4):
    out = []
    for s in ro:
        blob = data[s['rawptr']:s['rawptr'] + min(s['vsize'], s['rawsz'])]
        j = blob.find(bits4)
        while j != -1:
            if j % 4 == 0:
                out.append(s['va'] + j)
            j = blob.find(bits4, j + 1)
    return sorted(out)


# bourrage de l'en-tete : octets nuls entre la fin de la table des sections et SizeOfHeaders
cave_debut = (fin_table + 15) & ~15
assert all(b == 0 for b in data[fin_table:size_of_headers]), "le bourrage de l'en-tete n'est pas entierement nul"
cave_suivant = cave_debut
choix = {}          # tunable -> (va, section, origine du choix)
changements = []    # dicts
caves = []
for tun in sorted({s['tun'] for s in sites if s['kind'] == 'abs'}):
    bits4 = f32b(NOUVELLE[tun])
    cop = copies_lecture_seule(bits4)
    if cop:
        choix[tun] = (cop[0], section_de(cop[0]), 'copie existante (%d en lecture seule)' % len(cop))
    else:
        va = base + cave_suivant
        cave_suivant += 16
        assert cave_suivant <= size_of_headers
        choix[tun] = (va, '(en-tete)', "bourrage inutilise de l'en-tete du fichier")
        caves.append((va, bits4, tun))

problemes = []
for s in sites:
    off_site = va_vers_off(s['addr'])
    reel = data[off_site:off_site + s['len']]
    if reel != s['exp']:
        problemes.append('0x%08x : octets %s, attendu %s' % (s['addr'], reel.hex(' '), s['exp'].hex(' ')))
        continue
    if s['kind'] == 'abs':
        cible_va = struct.unpack_from('<I', s['exp'], s['off'])[0]
        val_actuelle = struct.unpack_from('<f', data, va_vers_off(cible_va))[0]
        if val_actuelle != struct.unpack('<f', f32b(ANCIENNE[s['tun']]))[0]:
            problemes.append('0x%08x : la constante lue vaut %r, attendu %r' % (s['addr'], val_actuelle, ANCIENNE[s['tun']]))
        rva_disp = s['addr'] + s['off'] - base
        if rva_disp not in relocs:
            problemes.append("0x%08x : l'operande n'a pas d'entree de relocation" % s['addr'])
        nouveau = struct.pack('<I', choix[s['tun']][0])
        ancien = s['exp'][s['off']:s['off'] + 4]
        changements.append(dict(va=s['addr'] + s['off'], offset=off_site + s['off'], avant=ancien.hex(), apres=nouveau.hex(),
                                role=s['role'], reglage=s['tun'], constante_va=choix[s['tun']][0]))
    else:
        ancien = s['exp'][s['off']:s['off'] + 4]
        if ancien != f32b(ANCIENNE[s['tun']]):
            problemes.append('0x%08x : immediat %s, attendu %r' % (s['addr'], ancien.hex(), ANCIENNE[s['tun']]))
        rva_imm = s['addr'] + s['off'] - base
        if rva_imm in relocs:
            problemes.append("0x%08x : l'immediat a une entree de relocation (pas un nombre)" % s['addr'])
        changements.append(dict(va=s['addr'] + s['off'], offset=off_site + s['off'], avant=ancien.hex(),
                                apres=f32b(NOUVELLE[s['tun']]).hex(), role=s['role'], reglage=s['tun'], constante_va=0))
for va, bits4, tun in caves:
    o = va - base
    assert data[o:o + 4] == bytes(4)
    changements.append(dict(va=va, offset=o, avant='00000000', apres=bits4.hex(),
                            role="valeur ajoutee dans le bourrage de l'en-tete (%s)" % tun, reglage=tun, constante_va=va))

if problemes:
    print('ERREURS (rien n\'est ecrit) :')
    for e in problemes:
        print(' -', e)
    sys.exit(1)

# chevauchements entre changements
changements.sort(key=lambda c: c['offset'])
for a, b in zip(changements, changements[1:]):
    assert a['offset'] + 4 <= b['offset'], 'chevauchement %x / %x' % (a['offset'], b['offset'])

patche = bytearray(data)
for c in changements:
    patche[c['offset']:c['offset'] + 4] = bytes.fromhex(c['apres'])
sha_patche = hashlib.sha256(bytes(patche)).hexdigest().upper()

module = dict(
    nom='ascenseur_x2',
    description="ascenseur / grue / roulage sur le pont x2 (methode du Mac : octets du programme, sans DLL)",
    build=dict(fichier='carrier_command.exe', taille=len(data), horodatage_pe='0x%08x' % ts,
               taille_image='0x%08x' % size_of_image, base='0x%08x' % base),
    sha256_origine=sha_origine, sha256_patche=sha_patche,
    nb_changements=len(changements),
    changements=changements)
json.dump(module, open(OUT_JSON, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

# rapport lisible
md = ['# Module exe `ascenseur_x2` : octets a changer dans carrier_command.exe (1.5.18)', '',
      'Genere par `tour/outils/generer_module_exe.py` a partir de `SITES_ENERGY` (cp_groups.c) et de la copie de sauvegarde.', '',
      '- sha256 origine : `%s`' % sha_origine, '- sha256 apres patch : `%s`' % sha_patche,
      '- %d changements de 4 octets chacun (%d operandes de constantes + 1 immediat d\'energie + %d valeur(s) ajoutee(s) dans l\'en-tete).' % (
          len(changements), sum(1 for s in sites if s['kind'] == 'abs'), len(caves)),
      '- Toutes les adresses modifiees ont une entree de relocation : le patch reste correct si Windows deplace le programme.', '',
      '## Constantes choisies (valeur doublee)', '', '| reglage | nouvelle valeur | adresse | section | origine |', '|---|---|---|---|---|']
for tun, (va, sec, org) in choix.items():
    md.append('| `%s` | %.9g | `0x%08x` | %s | %s |' % (tun, NOUVELLE[tun], va, sec, org))
md += ['', '## Changements', '', '| adresse | decalage fichier | avant | apres | role |', '|---|---|---|---|---|']
for c in changements:
    md.append('| `0x%08x` | `0x%x` | `%s` | `%s` | %s |' % (c['va'], c['offset'], c['avant'], c['apres'], c['role']))
open(OUT_MD, 'w', encoding='utf-8').write('\n'.join(md) + '\n')

print('OK : %d changements, sha256 patche %s' % (len(changements), sha_patche))
for tun, (va, sec, org) in choix.items():
    print('  %-24s -> %-10.9g a 0x%08x (%s : %s)' % (tun, NOUVELLE[tun], va, sec, org))
