#!/usr/bin/env python3
"""Etude du circuit d'atterrissage : retrouve et verifie, sur une COPIE de carrier_command.exe (1.5.18, 32 bits),
les endroits a retoucher pour porter le patch « atterrissage » du Mac. LECTURE SEULE : ne modifie aucun fichier,
n'ecrit rien (le resultat est imprime ; on le redirige vers un fichier si on veut).

Usage : python -I verifier_sites.py <copie_de_exe> [--sans-recouvrement <dossier_modules_exe>]
Adresses d'image, base 0x400000 (celles de Ghidra / IDA).

Ce que le script controle, pour chaque site :
  1. l'instruction decodee (capstone) a l'adresse donnee : mnemonique, longueur, cible ou constante lue ;
  2. les octets d'origine du champ a changer (4 octets) ;
  3. les nouveaux octets, puis, sur une copie EN MEMOIRE, que l'instruction relue se comporte comme voulu
     (nouvelle cible de saut, nouvelle constante lue, nouvelle valeur immediate) ;
  4. que la cible des sauts redirigés est bien le debut d'une instruction (decodage lineaire de toute la fonction) ;
  5. pour les champs qui sont des ADRESSES absolues : qu'ils ont une entree dans la table de relocation (ASLR) ;
     pour les autres (immediats, deplacements relatifs) : qu'ils n'en ont PAS ;
  6. que la constante visee est dans une section de donnees en lecture seule ;
  7. que les champs ne chevauchent ni les autres sites, ni les modules deja poses (ascenseur_x2, temps_x2).
"""
import glob
import json
import os
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

DEBUT_FONCTION, FIN_FONCTION = 0x006FC730, 0x00701FA8      # docking_manager_air::update (equivalent Windows), ~22 Ko
SORTIE = 0x00701B04          # fin commune d'un etat du circuit (pose la consigne de l'avion)
BLOC_PISTE = 0x00701A2A      # `cmp dword ptr [edi], 1` : debut du test qui donne la piste (equivalent du bloc 0x1001af914 du Mac)
CST_600, CST_M1800 = 0x00DB7A70, 0x00DB7E54      # float 600.0 et -1800.0 (constantes partagees : on ne les modifie JAMAIS)

# (id, sites du Mac, adresse de l'instruction, mnemonique attendu, longueur, decalage du champ, nature du champ, texte)
# nature : 'rel32' deplacement de saut ; 'imm32' valeur immediate ; 'abs32' adresse absolue d'une constante ; 'op' octets d'opcode
SITES = [
    ('S1', '1 (0x1001af900)', 0x007019FA, 'jbe', 6, 2, 'rel32', "etat 1 (1re moitie du virage arriere) : `x <= -1000 -> sortie` devient `-> test de la piste`"),
    ('S2', '2 (0x1001af85b)', 0x00701D33, 'jbe', 6, 2, 'rel32', "etat 2 (2e moitie du virage) : `z <= -1800 -> sortie` devient `-> test de la piste`"),
    ('S3', '3 (0x1001af867)', 0x00701D4E, 'jmp', 5, 1, 'rel32', "etat 2 -> 3 (changement d'etat) : `-> sortie` devient `-> test de la piste`"),
    ('C1', '4, 5, 6, 7 (4 x addps)', 0x00701379, 'mov', 10, 6, 'imm32', "centre du virage AVANT, z : 600 -> -1800 (meme cercle que le virage arriere)"),
    ('C2', '8 (0x1001af870)', 0x00701D5B, 'comiss', 7, 3, 'abs32', "etat 3 : fin de la ligne droite `z > 600` -> `z > -1800`"),
    ('C3', '9 (0x1001afaf2)', 0x00701F4E, 'movss', 8, 4, 'abs32', "etat 5 : fin du virage avant `z < 600` -> `z < -1800`"),
    ('C4', '10 (0x1001af87b)', 0x00701D65, 'addss', 8, None, 'addss', "etat 3 : visee 1800 m devant (`addss [600]` -> `subss [-1800]`) : FACULTATIF, voir ETUDE.md"),
]


class Image:
    def __init__(self, chemin):
        self.data = bytearray(open(chemin, 'rb').read())
        d = self.data
        pe = struct.unpack_from('<I', d, 0x3C)[0]
        nsec = struct.unpack_from('<H', d, pe + 6)[0]
        optsz = struct.unpack_from('<H', d, pe + 20)[0]
        opt = pe + 24
        self.base = struct.unpack_from('<I', d, opt + 28)[0]
        self.secs = []
        for i in range(nsec):
            o = opt + optsz + 40 * i
            nom = bytes(d[o:o + 8]).rstrip(b'\0').decode()
            vsize, va, rawsz, rawptr = struct.unpack_from('<IIII', d, o + 8)
            car = struct.unpack_from('<I', d, o + 36)[0]
            self.secs.append((nom, self.base + va, min(vsize, rawsz), rawptr, car))
        rva_rel, taille_rel = struct.unpack_from('<II', d, opt + 96 + 5 * 8)    # repertoire n°5 : relocations
        self.relocs = set()
        o = self.off(self.base + rva_rel)
        fin = o + taille_rel
        while o < fin:
            page, blk = struct.unpack_from('<II', d, o)
            if blk < 8:
                break
            for k in range((blk - 8) // 2):
                e = struct.unpack_from('<H', d, o + 8 + 2 * k)[0]
                if e >> 12 == 3:                    # HIGHLOW
                    self.relocs.add(self.base + page + (e & 0xFFF))
            o += blk
        self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        self.md.detail = True

    def section(self, va):
        for s in self.secs:
            if s[1] <= va < s[1] + s[2]:
                return s
        return None

    def off(self, va):
        s = self.section(va)
        return None if s is None else s[3] + va - s[1]

    def octets(self, va, n):
        o = self.off(va)
        return bytes(self.data[o:o + n])

    def decoder(self, va, donnees=None):
        n = 16
        o = self.off(va)
        src = bytes((donnees or self.data)[o:o + n])
        return next(self.md.disasm(src, va))

    def flt(self, va):
        return struct.unpack('<f', self.octets(va, 4))[0]

    def fonction(self, donnees=None):
        o = self.off(DEBUT_FONCTION)
        d = donnees if donnees is not None else self.data
        return {i.address: i for i in self.md.disasm(bytes(d[o:o + FIN_FONCTION - DEBUT_FONCTION]), DEBUT_FONCTION)}


def rel32(depuis_fin, cible):
    return struct.pack('<i', cible - depuis_fin)


def calculer(img, site):
    """Rend (adresse du champ, octets avant, octets apres, instruction decodee) ; verifie l'instruction d'origine."""
    sid, mac, va, mnem, lng, dec, nature, txt = site
    ins = img.decoder(va)
    assert ins.mnemonic == mnem and ins.size == lng, (sid, ins.mnemonic, ins.size)
    brut = bytes(ins.bytes)
    if nature == 'rel32':
        cible = ins.operands[0].imm & 0xFFFFFFFF
        assert cible == SORTIE, (sid, hex(cible))
        champ = va + dec
        avant = brut[dec:dec + 4]
        apres = rel32(va + lng, BLOC_PISTE)
    elif nature == 'imm32':
        assert ins.operands[0].type == X86_OP_MEM and ins.operands[1].type == X86_OP_IMM
        assert ins.operands[1].imm & 0xFFFFFFFF == 0x44160000, hex(ins.operands[1].imm)       # 600.0
        assert ins.operands[0].mem.disp & 0xFFFFFFFF == (-0x2A4) & 0xFFFFFFFF                 # [ebp - 0x2a4] = centre avant, z
        champ = va + dec
        avant = brut[dec:dec + 4]
        apres = struct.pack('<f', -1800.0)
        assert apres == bytes.fromhex('0000e1c4')
    elif nature == 'abs32':
        op = [o for o in ins.operands if o.type == X86_OP_MEM][0]
        assert op.mem.base == 0 and op.mem.index == 0 and (op.mem.disp & 0xFFFFFFFF) == CST_600, hex(op.mem.disp)
        champ = va + dec
        avant = brut[dec:dec + 4]
        assert avant == struct.pack('<I', CST_600)
        apres = struct.pack('<I', CST_M1800)
    elif nature == 'addss':
        op = [o for o in ins.operands if o.type == X86_OP_MEM][0]
        assert (op.mem.disp & 0xFFFFFFFF) == CST_600 and brut[:4] == bytes.fromhex('f30f580d')
        champ = va
        avant = brut[:8]
        apres = bytes.fromhex('f30f5c0d') + struct.pack('<I', CST_M1800)
    return champ, avant, apres, ins


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    img = Image(sys.argv[1])
    dossier_modules = None
    if '--sans-recouvrement' in sys.argv:
        dossier_modules = sys.argv[sys.argv.index('--sans-recouvrement') + 1]
    ok = True

    def verdict(cond, texte):
        nonlocal ok
        print('  [%s] %s' % ('OK ' if cond else 'ECHEC', texte))
        ok = ok and cond

    print('# Verification des sites du circuit d\'atterrissage (copie de travail, lecture seule)\n')
    print('base %#x ; fonction %#x-%#x ; %d relocations HIGHLOW lues' % (img.base, DEBUT_FONCTION, FIN_FONCTION, len(img.relocs)))
    avant_fonction = img.fonction()
    verdict(BLOC_PISTE in avant_fonction, 'le test de la piste %#x est bien le debut d\'une instruction' % BLOC_PISTE)
    ins = avant_fonction[BLOC_PISTE]
    verdict(ins.mnemonic == 'cmp' and bytes(ins.bytes) == bytes.fromhex('833f01'), 'et c\'est `%s %s` (mode == 1 ?)' % (ins.mnemonic, ins.op_str))
    verdict(SORTIE in avant_fonction, 'la sortie commune %#x est aussi un debut d\'instruction' % SORTIE)
    s = img.section(CST_M1800)
    verdict(s is not None and not (s[4] & 0x80000000), 'la constante -1800.0 (%#x) est dans la section %s, SANS droit d\'ecriture' % (CST_M1800, s[0] if s else '?'))
    verdict(img.flt(CST_M1800) == -1800.0, 'et elle vaut bien %g' % img.flt(CST_M1800))
    verdict(img.flt(CST_600) == 600.0, 'la constante lue aujourd\'hui (%#x) vaut bien %g (on ne la modifie pas)' % (CST_600, img.flt(CST_600)))

    deja = []        # champs deja poses par les modules actuels
    if dossier_modules:
        for p in sorted(glob.glob(os.path.join(dossier_modules, '*.json'))):
            m = json.load(open(p, encoding='utf-8'))
            for c in m['changements']:
                deja.append((c['va'], c['va'] + len(c['avant']) // 2, m['nom']))

    champs = []
    patch = bytearray(img.data)
    print('\n| site | Mac | adresse | instruction | champ | avant | apres | relocation |')
    print('|---|---|---|---|---|---|---|---|')
    resultats = []
    for site in SITES:
        champ, avant, apres, ins = calculer(img, site)
        reloc_attendue = site[6] == 'abs32'
        if site[6] == 'addss':
            relocs_presentes = (champ + 4) in img.relocs
            reloc_attendue = True
        else:
            relocs_presentes = champ in img.relocs
        verdict(img.octets(champ, len(avant)) == avant, '%s : octets d\'origine lus dans le fichier = ceux de l\'instruction decodee' % site[0])
        verdict(relocs_presentes == reloc_attendue, '%s : %s' % (site[0], 'le champ est une adresse absolue avec entree de relocation (ASLR) : on garde la meme entree' if reloc_attendue
                                                              else 'le champ n\'est PAS une adresse (pas de relocation) : rien a recaler'))
        gene = [nom for a, b, nom in deja if champ < b and a < champ + len(avant)]
        gene += ['un autre site' for autre in champs if champ < autre[1] and autre[0] < champ + len(avant)]
        verdict(not gene, '%s : ne chevauche aucun des %d endroits deja retouches par les modules poses ni un autre site%s' % (
            site[0], len(deja), (' (GENE : %s)' % ', '.join(gene)) if gene else ''))
        champs.append((champ, champ + len(avant)))
        o = img.off(champ)
        patch[o:o + len(avant)] = apres
        resultats.append((site, champ, avant, apres, ins))
        print('| %s | %s | `%#010x` | `%s %s` | `%#010x` (+%d) | `%s` | `%s` | %s |' % (
            site[0], site[1], site[2], ins.mnemonic, ins.op_str, champ, champ - site[2], avant.hex(' '), apres.hex(' '),
            'oui (a garder)' if reloc_attendue else 'non'))

    print('\nRelecture au desassemblage de la copie PATCHEE EN MEMOIRE :')
    apres_fonction = img.fonction(patch)
    verdict(sorted(apres_fonction) == sorted(avant_fonction), 'les frontieres d\'instructions de toute la fonction (%d instructions) sont inchangees' % len(avant_fonction))
    for site, champ, avant, apres, ins in resultats:
        n = apres_fonction[site[2]]
        sid = site[0]
        if sid in ('S1', 'S2', 'S3'):
            verdict(n.mnemonic == ins.mnemonic and (n.operands[0].imm & 0xFFFFFFFF) == BLOC_PISTE and n.size == ins.size,
                    '%s : `%s %s` saute maintenant en %#x (= test de la piste)' % (sid, n.mnemonic, n.op_str, BLOC_PISTE))
        elif sid == 'C1':
            verdict(n.operands[1].imm & 0xFFFFFFFF == 0xC4E10000 and struct.unpack('<f', struct.pack('<I', n.operands[1].imm & 0xFFFFFFFF))[0] == -1800.0,
                    '%s : `%s %s` (centre avant z = -1800)' % (sid, n.mnemonic, n.op_str))
        elif sid in ('C2', 'C3'):
            op = [o for o in n.operands if o.type == X86_OP_MEM][0]
            verdict((op.mem.disp & 0xFFFFFFFF) == CST_M1800 and n.mnemonic == ins.mnemonic and n.size == ins.size,
                    '%s : `%s %s` lit maintenant -1800' % (sid, n.mnemonic, n.op_str))
        elif sid == 'C4':
            op = [o for o in n.operands if o.type == X86_OP_MEM][0]
            verdict(n.mnemonic == 'subss' and (op.mem.disp & 0xFFFFFFFF) == CST_M1800 and n.size == ins.size,
                    '%s : `%s %s` (z - (-1800) = z + 1800)' % (sid, n.mnemonic, n.op_str))

    n_champs = sum(1 for r in resultats if r[0][0] != 'C4')
    print('\nResume : %d changements de 4 octets (C4 facultatif en plus : 2 champs) ; octets touches hors de ces champs : 0.' % n_champs)
    print('VERDICT GLOBAL : %s' % ('TOUT EST COHERENT' if ok else 'ECHEC (voir les lignes [ECHEC])'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
