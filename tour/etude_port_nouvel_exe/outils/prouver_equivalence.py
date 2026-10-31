#!/usr/bin/env python3
"""PARTIE 1, etape D : preuve « mêmes instructions qu'à l'ancien exe patché », site par site, sur les OCTETS (rien n'est lance).

Construit en memoire (avec les fonctions de patch_exe.py, jamais sur le vrai jeu) :
  - l'ancien exe d'origine + les 6 modules de l'ancien profil          (= « ancien patche »)
  - le nouvel exe de Steam + les 6 modules du profil 461E1262          (= « nouveau patche »)
puis, pour chacun des 41 champs, desassemble l'instruction dans les DEUX fichiers patches et compare :
  mnemonique, registres, taille, valeur finalement lue (la constante pointee) ou immediat ou cible du saut.
Les valeurs voulues sont ecrites ICI a la main (independantes des JSON).
Controle aussi : seuls les champs listes different de l'original, les relocations sont intactes, les frontieres
d'instructions de toute la zone balayee sont inchangees par le patch.

Usage : python -I -B prouver_equivalence.py <ancien_original> <nouveau> <sites_localises.json> <sortie.txt>
"""
import importlib.util
import json
import os
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
from pe_lecture import Exe  # noqa: E402
from localiser_sites import Balayage  # noqa: E402

spec = importlib.util.spec_from_file_location('patch_exe_epreuve', os.path.join(ICI, '..', '..', 'outils', 'patch_exe.py'))
PE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PE)

VOULU = {   # reglage -> valeur finale (float) ; ecrite a la main : doubler l'ascenseur, la grue, le roulage...
    'CP_T_ENERGY_SHARE': 0.8, 'CP_T_PLATFORM_STEP': 0.05, 'CP_T_PLATFORM_STEP_NEG': -0.05,
    'CP_T_CRANE_H': 1 / 3, 'CP_T_CRANE_H_NEG': -1 / 3, 'CP_T_CRANE_V': 1 / 15, 'CP_T_CRANE_V_NEG': -1 / 15,
    'CP_T_CRANE_ROT': 0.08, 'CP_T_CRANE_ROT_NEG': -0.08, 'CP_T_TAXI_ACCEL': 0.1, 'CP_T_TAXI_CAP': 5.0,
    'RETURN_TAXI_TICKS_PER_SECOND': 15.0, 'HELI_APPROACH_AIM_AHEAD_M': 100.0,
    'LANDING_CIRCLE_STATE3_END': -1800.0, 'LANDING_CIRCLE_STATE5_END': -1800.0, 'LANDING_CIRCLE_FRONT_CENTER_Z': -1800.0,
    'SERVER_SPEED_FACTOR': 2.0,
}
GATES = {'LANDING_GATE_STATE1', 'LANDING_GATE_STATE2', 'LANDING_GATE_STATE2_TO_3'}


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def charger(profil):
    mods, sha_o = PE.charger_tous(profil)
    return mods, sha_o


def patcher_tout(data, mods):
    b = bytearray(data)
    for m in mods.values():
        for c in m['changements']:
            b[c['offset']:c['offset'] + 4] = bytes.fromhex(c['apres'])
    return bytes(b)


def ecrire_exe_temp(data, chemin):
    with open(chemin, 'wb') as f:
        f.write(data)


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    p_old, p_new, p_sites, p_txt = sys.argv[1:5]
    A, N = Exe(p_old), Exe(p_new)
    mods_a, sha_a = charger(PE.PROFILS[0])
    mods_n, sha_n = charger(PE.PROFILS[1])
    assert sha_a == A.sha and sha_n == N.sha
    pa, pn = patcher_tout(A.data, mods_a), patcher_tout(N.data, mods_n)
    # Exe attend un fichier : on reutilise les objets en remplacant les octets (la structure PE est la meme)
    A2, N2 = Exe(p_old), Exe(p_new)
    A2.data, N2.data = pa, pn
    with open(p_sites, 'r', encoding='utf-8') as f:
        loc = json.load(f)
    L = []
    echecs = []

    def ok(cond, msg):
        if not cond:
            echecs.append(msg)
        return cond

    L.append('Preuve « memes instructions qu\'a l\'ancien exe patche » (octets seulement, rien lance)')
    L.append('ancien patche (6 modules) : %d octets, sha256 %s' % (len(pa), PE.sha256_octets(pa)))
    L.append('nouveau patche (6 modules): %d octets, sha256 %s' % (len(pn), PE.sha256_octets(pn)))
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    def ins_a(exe, va):
        return next(md.disasm(exe.octets(va, 15), va))

    # --- 1. champs : seuls les champs listes different de l'original, dans les deux builds
    for nom_b, orig, patche, mods in (('ancien', A, pa, mods_a), ('nouveau', N, pn, mods_n)):
        champs = set()
        for m in mods.values():
            for c in m['changements']:
                champs.update(range(c['offset'], c['offset'] + 4))
        diff = {i for i in range(len(orig.data)) if orig.data[i] != patche[i]}
        ok(len(orig.data) == len(patche) and diff <= champs, '%s : octets modifies hors des champs listes' % nom_b)
        L.append('%s : %d octets different de l\'original (champs permis : %d), tous dans les champs listes : %s' % (
            nom_b, len(diff), len(champs), 'OUI' if diff <= champs else 'NON'))

    # --- 2. chaque site
    L.append('')
    L.append('--- site par site (ancien patche | nouveau patche)')
    n_sites = 0
    ref_vus = {}
    for r in loc['resultats']:
        n_sites += 1
        reglage = r['reglage']
        if r['type'] == 'cave_entete':
            va = r['va_ancien']
            va_ = A2.f32(va), N2.f32(va)
            ok(va_[0] == va_[1] == f32(VOULU[reglage]), 'en-tete %s' % reglage)
            L.append('%-22s en-tete 0x%08x : ancien %.9g | nouveau %.9g (voulu %.9g) %s' % (
                r['module'], va, va_[0], va_[1], VOULU[reglage], 'OK' if va_[0] == va_[1] == f32(VOULU[reglage]) else 'ECHEC'))
            continue
        # instruction contenant le champ
        ia_va = int(r['instruction_ancien'].split()[0], 16)
        in_va = int(r['instruction_nouveau'].split()[0], 16)
        ia, inn = ins_a(A2, ia_va), ins_a(N2, in_va)
        meme = ia.mnemonic == inn.mnemonic and ia.size == inn.size
        det = ''
        if r['type'] == 'abs':
            ma = [o for o in ia.operands if o.type == X86_OP_MEM][0]
            mn = [o for o in inn.operands if o.type == X86_OP_MEM][0]
            ca, cn = ma.mem.disp & 0xFFFFFFFF, mn.mem.disp & 0xFFFFFFFF
            va_, vn_ = A2.f32(ca), N2.f32(cn)
            regs_ok = ia.op_str.replace('0x%x' % ca, 'C') == inn.op_str.replace('0x%x' % cn, 'C')
            voulu = f32(VOULU[reglage])
            c_ok = meme and regs_ok and ma.mem.base == 0 == mn.mem.base and va_ == vn_ == voulu \
                and A2.nom_section(ca) == N2.nom_section(cn) and N2.est_reloc(r['va_nouveau'])
            # la constante lue est en lecture seule (jamais .data)
            sn = N2.section(cn)
            c_ok = c_ok and (not sn['ecriture'])
            ref_vus.setdefault(ca, set()).add(cn)
            det = 'lit %.9g (voulu %.9g) en 0x%08x/0x%08x, %s' % (vn_, voulu, ca, cn, N2.nom_section(cn))
        elif r['type'] == 'imm':
            imm_a = ia.operands[-1].imm & 0xFFFFFFFF
            imm_n = inn.operands[-1].imm & 0xFFFFFFFF
            voulu = f32(VOULU[reglage])
            c_ok = meme and imm_a == imm_n and struct.unpack('<f', struct.pack('<I', imm_n))[0] == voulu \
                and ia.op_str == inn.op_str and not N2.est_reloc(r['va_nouveau'])
            det = 'immediat %.9g (voulu %.9g)' % (struct.unpack('<f', struct.pack('<I', imm_n))[0], voulu)
        else:   # rel32 : le saut doit aller au test de la piste, `cmp dword ptr [edi], 1`, suivi des memes instructions
            ta, tn = ia.operands[0].imm & 0xFFFFFFFF, inn.operands[0].imm & 0xFFFFFFFF
            suite_a = [(i.mnemonic, i.op_str) for i in md.disasm(A2.octets(ta, 80), ta)][:8]
            suite_n = [(i.mnemonic, i.op_str) for i in md.disasm(N2.octets(tn, 80), tn)][:8]
            # les operandes des sauts relatifs de la suite changent d'adresse : on compare les mnemoniques et les operandes non relatifs
            def norm(suite):
                return [(m_, o if not o.startswith('0x') else 'CIBLE') for m_, o in suite]
            c_ok = meme and suite_a[0] == ('cmp', 'dword ptr [edi], 1') and norm(suite_a) == norm(suite_n) and ia.mnemonic == inn.mnemonic
            det = 'saute en 0x%08x/0x%08x : %s' % (ta, tn, ' ; '.join('%s %s' % s for s in suite_n[:3]))
        ok(c_ok, '%s 0x%08x' % (r['module'], r['va_ancien']))
        L.append('%-22s 0x%08x|0x%08x  %s %s | %s %s ; %s -> %s' % (
            r['module'], ia_va, in_va, ia.mnemonic, ia.op_str, inn.mnemonic, inn.op_str, det, 'OK' if c_ok else 'ECHEC'))
    ok(n_sites == 41, '41 champs attendus (%d)' % n_sites)

    # --- 3. relocations intactes, frontieres d'instructions inchangees par le patch (zone balayee)
    L.append('')
    L.append('--- controles globaux')
    ok(A2.relocs == A.relocs and N2.relocs == N.relocs, 'table de relocation modifiee')
    L.append('table de relocation identique avant/apres patch (150969 / 150985 entrees) : %s' % (
        'OUI' if A2.relocs == A.relocs and N2.relocs == N.relocs else 'NON'))
    for nom_b, e0, e1 in (('ancien', A, A2), ('nouveau', N, N2)):
        b0, b1 = Balayage(e0), Balayage(e1)
        egal = b0.addr == b1.addr and b0.size == b1.size and b0.mn == b1.mn
        ok(egal, '%s : frontieres d\'instructions changees par le patch' % nom_b)
        L.append('%s : les %d instructions de tout .text gardent leurs frontieres et mnemoniques apres patch : %s' % (
            nom_b, len(b0.addr), 'OUI' if egal else 'NON'))
    # une meme ancienne constante lue -> toujours la meme nouvelle
    multi = {a: b for a, b in ref_vus.items() if len(b) > 1}
    ok(not multi, 'une meme constante ancienne a plusieurs equivalents')
    L.append('constantes finales lues (ancienne -> nouvelle) : %d, correspondances multiples : %d' % (len(ref_vus), len(multi)))
    L.append('')
    L.append('RESULTAT : %s' % ('TOUT CONCORDE (%d echec)' % len(echecs) if not echecs else '%d ECHEC(S) : %s' % (len(echecs), '; '.join(echecs))))
    with open(p_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L[-12:]))
    return 1 if echecs else 0


if __name__ == '__main__':
    sys.exit(main())
