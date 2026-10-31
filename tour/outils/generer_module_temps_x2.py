#!/usr/bin/env python3
"""Genere le module `temps_x2` : la simulation tourne 2x plus vite (MODE TEST, jamais en multijoueur).

Principe (trouve sur le Mac, retrouve sur Windows par structure identique) : la boucle du serveur calcule la duree
d'un pas de simulation = 33 ms / facteur, ou `facteur` est un champ float du serveur ([this + 0x140]) initialise a 1.0
dans le constructeur. Passer cet immediat de 1.0 a 2.0 = pas de 16 ms = environ 2,06 fois plus vite en temps reel.
UN SEUL changement de 4 octets ; aucune constante partagee modifiee.

Verifications faites avant d'ecrire quoi que ce soit (relues avec capstone dans le fichier) :
  boucle 0x0077ee10 : mov ebx,0x21 ; movss xmm1,[esi+0x140] ; comiss > 0 ; movss xmm0,[33.0] ; divss ; mov eax,0x7d0
  constructeur 0x00835b50 : mov edi,ecx ... mov dword ptr [edi+0x140], 0x3f800000 (UNE seule ecriture dans l'exe)
  l'immediat n'a pas d'entree de relocation (c'est un nombre, pas une adresse).

Usage : python -I generer_module_temps_x2.py <exe_origine> <sortie.json> <rapport.md>
"""
import hashlib
import json
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE, OUT_JSON, OUT_MD = sys.argv[1:4]
data = open(EXE, 'rb').read()
sha_o = hashlib.sha256(data).hexdigest().upper()
pe = struct.unpack_from('<I', data, 0x3C)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
optsz = struct.unpack_from('<H', data, pe + 20)[0]
opt = pe + 24
base = struct.unpack_from('<I', data, opt + 28)[0]
ts = struct.unpack_from('<I', data, pe + 8)[0]
soi = struct.unpack_from('<I', data, opt + 56)[0]
secs = []
for i in range(nsec):
    o = opt + optsz + 40 * i
    vs, va, rs, rp = struct.unpack_from('<IIII', data, o + 8)
    secs.append((base + va, min(vs, rs), rp))


def off(va):
    for sva, n, rp in secs:
        if sva <= va < sva + n:
            return rp + va - sva
    raise SystemExit('adresse hors fichier 0x%08x' % va)


reloc_rva, reloc_size = struct.unpack_from('<II', data, opt + 96 + 5 * 8)
relocs = set()
p = off(base + reloc_rva)
while p < off(base + reloc_rva) + reloc_size:
    page, blk = struct.unpack_from('<II', data, p)
    if blk < 8:
        break
    for k in range((blk - 8) // 2):
        e = struct.unpack_from('<H', data, p + 8 + 2 * k)[0]
        if (e >> 12) == 3:
            relocs.add(page + (e & 0xFFF))
    p += blk

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
erreurs = []


def instr(va):
    return next(md.disasm(data[off(va):off(va) + 15], va))


# 1. la boucle du serveur
attendu_boucle = [
    (0x77ee1c, 'mov', 'ebx, 0x21'),
    (0x77ee26, 'movss', 'xmm1, dword ptr [esi + 0x140]'),
    (0x77ee39, 'movss', 'xmm0, dword ptr [0xdb79a0]'),
    (0x77ee41, 'divss', 'xmm0, xmm1'),
    (0x77ee4c, 'mov', 'eax, 0x7d0'),
]
for va, mn, ops in attendu_boucle:
    i = instr(va)
    if i.mnemonic != mn or i.op_str != ops:
        erreurs.append('boucle 0x%08x : %s %s (attendu %s %s)' % (va, i.mnemonic, i.op_str, mn, ops))
if struct.unpack_from('<f', data, off(0xdb79a0))[0] != 33.0:
    erreurs.append('la constante 0xdb79a0 ne vaut pas 33.0')

# 2. le constructeur
CTOR = 0x835cc5
i = instr(CTOR)
if not (i.mnemonic == 'mov' and i.size == 10 and i.op_str == 'dword ptr [edi + 0x140], 0x3f800000'):
    erreurs.append('constructeur 0x%08x : %s %s' % (CTOR, i.mnemonic, i.op_str))
IMM = CTOR + 6
o_imm = off(IMM)
avant = data[o_imm:o_imm + 4]
if avant != struct.pack('<f', 1.0):
    erreurs.append('immediat %s au lieu de 1.0' % avant.hex())
if (IMM - base) in relocs:
    erreurs.append("l'immediat a une entree de relocation")
pat = bytes([0xC7]) + bytes([0x80 + r for r in (7,)]) + bytes([0x40, 0x01, 0x00, 0x00, 0x00, 0x00, 0x80, 0x3F])
n_ecritures = 0
for sva, n, rp in secs:
    blob = data[rp:rp + n]
    j = blob.find(pat)
    while j != -1:
        n_ecritures += 1
        j = blob.find(pat, j + 1)
if n_ecritures != 1:
    erreurs.append("%d ecriture(s) de 1.0 dans [edi+0x140] (attendu 1)" % n_ecritures)

if erreurs:
    print("ERREURS (rien n'est ecrit) :")
    for e in erreurs:
        print(' -', e)
    sys.exit(1)

apres = struct.pack('<f', 2.0)
patche = bytearray(data)
patche[o_imm:o_imm + 4] = apres
sha_p = hashlib.sha256(bytes(patche)).hexdigest().upper()
module = dict(
    nom='temps_x2',
    description="simulation 2x plus vite (facteur de vitesse du serveur 1.0 -> 2.0) : MODE TEST, jamais en multijoueur",
    avertissement="Le serveur dicte la vitesse : les autres joueurs d'une partie hebergee verraient le jeu 2x plus vite. "
                  "Toute la partie accelere (ennemis, animations). A retirer pour jouer normalement.",
    build=dict(fichier='carrier_command.exe', taille=len(data), horodatage_pe='0x%08x' % ts,
               taille_image='0x%08x' % soi, base='0x%08x' % base),
    sha256_origine=sha_o, sha256_patche=sha_p, nb_changements=1,
    changements=[dict(va=IMM, offset=o_imm, avant=avant.hex(), apres=apres.hex(),
                      role='constructeur du serveur 0x00835b50 : [edi+0x140] (facteur de vitesse) 1.0 -> 2.0',
                      reglage='SERVER_SPEED_FACTOR', constante_va=0)])
json.dump(module, open(OUT_JSON, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
md = ['# Module exe `temps_x2` : simulation 2x plus vite (MODE TEST)', '',
      'Genere par `tour/outils/generer_module_temps_x2.py`. **Un seul changement de 4 octets.**', '',
      '- Boucle du serveur `0x0077ee10` (relue au desassembleur) : `mov ebx,0x21` (pas par defaut 33 ms), `movss xmm1,[esi+0x140]` (facteur), `comiss > 0`, `movss xmm0,[33.0]`, `divss xmm0,xmm1`, plafond `0x7d0` (2000 ms).',
      '- Constructeur du serveur `0x00835b50` : `mov dword ptr [edi+0x140], 0x3f800000` en `0x%08x` (la SEULE ecriture dans l\'exe) : l\'immediat `00 00 80 3f` (1.0) devient `00 00 00 40` (2.0), en `0x%08x` (decalage fichier `0x%x`).' % (CTOR, IMM, o_imm),
      '- Effet attendu : pas de 33 / 2 = 16 ms (conversion entiere) soit environ x2,06 en temps reel ; plus vite encore pour un facteur plus grand (33 / 3 = 11 ms) ; la machine doit suivre.',
      '- Precautions : mode test uniquement (le serveur dicte la vitesse, donc aussi aux joueurs d\'une partie hebergee) ; toute la partie accelere ; meteo et ocean sur leurs propres fils.',
      '- sha256 origine `%s`, sha256 avec ce seul module `%s`.' % (sha_o, sha_p),
      '- Retour arriere : `patch_exe.py retirer --module temps_x2`.']
open(OUT_MD, 'w', encoding='utf-8').write('\n'.join(md) + '\n')
print('OK : 1 changement a 0x%08x (decalage 0x%x) : %s -> %s ; sha256 avec ce module seul %s' % (IMM, o_imm, avant.hex(), apres.hex(), sha_p))
