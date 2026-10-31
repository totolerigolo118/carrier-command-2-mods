#!/usr/bin/env python3
"""PARTIE 3 : inventaire EN LECTURE SEULE des crochets (patch_mid) et des adresses fixes des plugins, avec le site equivalent dans
le nouvel exe : sur / incertain / introuvable. LECTURE SEULE sur les exe et sur les sources des plugins (jamais modifies).

Pour chaque site (liste ecrite A LA MAIN d'apres le source des plugins, avec leurs octets attendus) :
  - nouvelle adresse par DEUX methodes independantes : alignement du code entier, et recherche du contexte desassemble ;
  - les octets attendus par le plugin sont-ils la au nouvel endroit ? les instructions deplacees (la longueur du crochet)
    tombent-elles sur des frontieres d'instructions identiques ? y a-t-il un saut du jeu vers l'INTERIEUR des octets deplaces ?
  - combien d'instructions identiques de chaque cote, et distance au plus proche bloc de code qui differe.
Classement (regle fixe, ecrite ici) :
  SUR        les deux methodes donnent la meme adresse, octets attendus identiques, frontieres identiques, aucun saut vers
             l'interieur des octets deplaces, au moins 30 instructions identiques de chaque cote ;
  INCERTAIN  tout est coherent mais moins de 30 instructions identiques d'un cote (une difference toute proche) ;
  INTROUVABLE les deux methodes ne s'accordent pas, ou les octets attendus ne sont pas la.

Usage : python -I -B inventaire_plugins.py <ancien_original> <nouveau> <sortie.json> <sortie.txt>
"""
import bisect
import json
import os
import re
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_lecture import Exe  # noqa: E402
from alignement import Alignement  # noqa: E402
from localiser_sites import retrouver  # noqa: E402

B = lambda *x: bytes(x)  # noqa: E731

# (plugin, nom, adresse ancienne, longueur deplacee, octets attendus par le plugin, role)
SITES = [
    # --- cc2x_frein.c v10 (commite) : patch_mid via install_hooks(), uniquement si recall_force=1
    ('frein v10', 'H1', 0x7018ce, 6, B(0x8b, 0x40, 0x04, 0x83, 0xf8, 0x05), 'crochet : mov eax,[eax+4] ; cmp eax,5 (element de la file)'),
    ('frein v10', 'H2', 0x701a3d, 6, B(0x8d, 0x85, 0x28, 0xfd, 0xff, 0xff), 'crochet : lea eax,[ebp-0x2d8] (test des 1000 m)'),
    ('frein v10', 'H3', 0x6ff0fb, 6, B(0x8b, 0x8d, 0x04, 0xfe, 0xff, 0xff), 'crochet LECTURE SEULE : mov ecx,[ebp-0x1fc] (debut du chemin « approche abandonnee »)'),
    ('frein v10', 'sonde A/B', 0x6febda, 8, B(0xf3, 0x0f, 0x10, 0x8d, 0xa4, 0xfd, 0xff, 0xff), 'crochet LECTURE SEULE : movss xmm1,[ebp-0x25c]'),
    ('frein v10', 'sonde C/D', 0x6febe7, 8, B(0xf3, 0x0f, 0x10, 0x8d, 0xa4, 0xfd, 0xff, 0xff), 'crochet LECTURE SEULE : movss xmm1,[ebp-0x25c]'),
    ('frein v10', 'sonde E', 0x6febc0, 8, B(0xf3, 0x0f, 0x10, 0x8d, 0xa4, 0xfd, 0xff, 0xff), 'crochet LECTURE SEULE : movss xmm1,[ebp-0x25c]'),
    ('frein v10', 'sonde C passee', 0x6fe788, 6, B(0x8b, 0x8d, 0xb4, 0xfd, 0xff, 0xff), 'crochet LECTURE SEULE : mov ecx,[ebp-0x24c]'),
    ('frein v10', 'cible de saut H2', 0x701a8a, 0, None, 'adresse fixe LUE : instruction apres le test des 1000 m (cpu->jump_to = A->va(0x701a8a))'),
    # --- cc2x_frein.c v11 (NON commite, worktree musing-nobel-a0872c) : le meme + H4
    ('frein v11 (non commite)', 'H4', 0x6fe470, 7, B(0xc6, 0x85, 0xfb, 0xfd, 0xff, 0xff, 0x01), 'crochet : mov byte [ebp-0x205],1 (zone finale) ; redirige le flux'),
    ('frein v11 (non commite)', 'cible de saut H4', 0x6fe55b, 0, None, 'adresse fixe LUE : evaluation du commit (portes A-E), cpu->jump_to = A->va(0x6fe55b)'),
    # --- cc2x_modes.c v3.1 : AUCUN crochet ; une adresse lue (porte de securite, 8 octets, memcmp) et un decalage d'objet
    ('modes v3.1', 'site du gaz', 0x71dbbf, 8, B(0xf3, 0x0f, 0x11, 0x87, 0x14, 0x03, 0x00, 0x00), 'adresse fixe LUE (memcmp, porte de securite) : movss [edi+0x314],xmm0'),
]


def sauts_vers_interieur(exe, site, longueur, fenetre=0x3000):
    """Adresses des sauts (rel8 / rel32, jmp / jcc / call) du code voisin dont la cible tombe DANS (site, site+longueur)."""
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    debut = max(site - fenetre, exe.sec_nom('.text')['va'])
    out = []
    for ins in md.disasm(exe.octets(debut, 2 * fenetre), debut):
        if ins.group(1) or ins.group(2):      # CS_GRP_JUMP = 1, CS_GRP_CALL = 2
            if ins.operands and ins.operands[0].type == 2:    # X86_OP_IMM
                cible = ins.operands[0].imm & 0xFFFFFFFF
                if site < cible < site + longueur:
                    out.append((ins.address, cible))
    return out


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    A, N = Exe(sys.argv[1]), Exe(sys.argv[2])
    al = Alignement(A, N)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    L, res = ['Inventaire des crochets et adresses fixes des plugins : ancien exe -> nouvel exe (LECTURE SEULE)', '',
              'plugin | nom | ancien | nouveau | alignement | contexte | octets | frontieres | sauts dans les octets deplaces | identiques av/ap | plus proche bloc different | verdict'], []
    dif_starts = [al.BA.addr[d[0]] if d[0] < len(al.BA.addr) else 1 << 40 for d in al.diffs]
    dif_ends = [al.BA.addr[d[1] - 1] + al.BA.size[d[1] - 1] if d[1] > d[0] else al.BA.addr[d[0]] for d in al.diffs]
    for plugin, nom, va, ln, attendu, role in SITES:
        r = dict(plugin=plugin, nom=nom, ancien=va, longueur=ln, role=role)
        nv_a, st, marge = al.va_nouveau(va)
        i = al.index_ancien(va)
        nv_c, ctx = None, 'non cherche'
        if i is not None and al.BA.addr[i] == va:
            trouve, raison = retrouver(al.BA, al.BN, i)
            if trouve:
                Nn, i0, i1, pos = trouve
                import bisect as _b
                va_deb = al.BN.va_texte + pos
                j = _b.bisect_left(al.BN.addr, va_deb)
                nv_c = al.BN.addr[j + (i - i0)]
                ctx = 'unique %d+%d' % (Nn, Nn)
            else:
                ctx = raison[0].lower()
        else:
            ctx = 'pas un debut d\'instruction de l\'ancien balayage'
        # extension : si le contexte seul ne donne rien, l'alignement fait foi mais on le dit
        deux = nv_a is not None and nv_c is not None and nv_a == nv_c
        nv = nv_a if nv_a is not None else nv_c
        r.update(nouveau=nv, alignement=st, contexte=ctx, accord=deux)
        octets_ok = front_ok = None
        sauts_a = sauts_n = []
        av = ap = 0
        proche = ''
        if nv is not None:
            if attendu is not None:
                octets_ok = N.octets(nv, len(attendu)) == attendu and A.octets(va, len(attendu)) == attendu
            # frontieres : les instructions qui couvrent les `ln` octets deplaces sont les memes (taille, mnemonique) dans les deux exe
            if ln:
                ia = list(md.disasm(A.octets(va, 24), va))
                inn = list(md.disasm(N.octets(nv, 24), nv))
                def couvre(ins_list):
                    tot, out = 0, []
                    for x in ins_list:
                        out.append((x.size, x.mnemonic))
                        tot += x.size
                        if tot >= ln:
                            return tot, out
                    return tot, out
                ta, oa = couvre(ia)
                tn, on = couvre(inn)
                front_ok = (ta == ln and tn == ln and oa == on)
                sauts_a = sauts_vers_interieur(A, va, ln)
                sauts_n = sauts_vers_interieur(N, nv, ln)
            # instructions identiques de chaque cote (suite egale qui contient le site)
            k = bisect.bisect_right(al._starts, i) - 1 if i is not None else -1
            if k >= 0:
                i0_, j0_, n_ = al.egaux[k]
                if i0_ <= i < i0_ + n_:
                    av, ap = i - i0_, i0_ + n_ - 1 - i
            kk = bisect.bisect_right(dif_starts, va)
            d_av = va - dif_ends[kk - 1] if kk > 0 else None
            d_ap = dif_starts[kk] - va if kk < len(dif_starts) else None
            proche = '-0x%x / +0x%x octets' % (d_av if d_av is not None else 0, d_ap if d_ap is not None else 0)
        r.update(octets_ok=octets_ok, frontieres_ok=front_ok, sauts_ancien=[(hex(a), hex(b)) for a, b in sauts_a],
                 sauts_nouveau=[(hex(a), hex(b)) for a, b in sauts_n], identiques_avant=av, identiques_apres=ap, bloc_proche=proche)
        if nv is None or not deux or octets_ok is False or front_ok is False or sauts_n:
            verdict = 'INTROUVABLE' if (nv is None or not deux or octets_ok is False) else 'INCERTAIN'
        elif min(av, ap) < 30:
            verdict = 'INCERTAIN'
        else:
            verdict = 'SUR'
        # remarque : un saut vers l'interieur des octets deplaces existe-t-il deja dans l'ancien exe ? (alors ce n'est pas une regression)
        if sauts_n and sauts_n == [(a, b) for a, b in []]:
            pass
        r['verdict'] = verdict
        res.append(r)
        L.append('%s | %s | 0x%08x | %s | %s | %s | %s | %s | %s | %d / %d | %s | %s' % (
            plugin, nom, va, '0x%08x' % nv if nv else '?', st if st != 'egal' else ('egal' + ('' if deux else ' (contexte: ' + ctx + ')')), ctx,
            {True: 'OK', False: 'DIFFERENTS', None: '-'}[octets_ok], {True: 'OK', False: 'DIFFERENTES', None: '-'}[front_ok],
            'aucun' if not sauts_n else sauts_n, av, ap, proche, verdict))
    with open(sys.argv[3], 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1, default=str)
    with open(sys.argv[4], 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))
    return 0


if __name__ == '__main__':
    sys.exit(main())
