#!/usr/bin/env python3
"""PARTIE 3 : controle des decalages de champs d'objets sur les ACCES DU CODE. LECTURE SEULE.

Idee : si un champ avait bouge dans le nouvel exe (structure recompilee avec un champ de plus ou de moins), TOUS les acces a ce
champ et aux champs suivants auraient un deplacement different, et apparaitraient dans les blocs de code qui different.
Pour chaque decalage suivi on compte donc les instructions de l'ancien exe qui ont un operande memoire avec ce deplacement
(registre de base quelconque), et on dit combien sont dans du code IDENTIQUE au nouvel exe (alignement, voir alignement.py) :
ces acces-la lisent forcement le meme decalage dans le nouvel exe. On compte aussi les acces du nouvel exe.

Les decalages suivis : ceux de la table `Layout` de world.c (lue dans la source du clone, jamais modifiee), +0x308..0x314 (gaz,
cc2x_modes), le gestionnaire d'atterrissage (+0x1c, +0x5c, +0xd4) et les cases de pile des crochets du frein, ces dernieres
comptees seulement dans la grande fonction de piste (0x6fc730..0x701fa8 ancien).

Usage : python -I -B acces_champs.py <ancien_original> <nouveau> <world.c> <sortie.txt>
"""
import bisect
import os
import re
import sys
from collections import defaultdict

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_lecture import Exe  # noqa: E402
from alignement import Alignement  # noqa: E402

FONCTION_PISTE = (0x6FC730, 0x701FA8)      # ancien exe : grande fonction du circuit d'atterrissage (tous les crochets du frein y sont)
RE_DISP = re.compile(r'\[(?P<base>[a-z]{2,3})?(?: \+ [a-z]{2,3}(?:\*\d)?)?(?: (?P<sg>[+-]) (?P<hx>0x[0-9a-f]+))?\]')


def deplacements(op):
    """Liste des (base, deplacement signe) des operandes memoire d'une chaine d'operandes capstone."""
    out = []
    for m in RE_DISP.finditer(op):
        if m.group('hx'):
            d = int(m.group('hx'), 16) * (-1 if m.group('sg') == '-' else 1)
            out.append((m.group('base') or '', d))
    return out


def balayer(exe):
    """-> liste de (adresse, [(base, disp)...]) pour toutes les instructions de .text qui ont un deplacement."""
    s = exe.sec_nom('.text')
    buf = exe.data[s['rawptr']:s['rawptr'] + min(s['vsize'], s['rawsz'])]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    out = []
    for a, sz, mn, op in md.disasm_lite(buf, s['va']):
        if '[' in op and ('+ 0x' in op or '- 0x' in op):
            d = deplacements(op)
            if d:
                out.append((a, d))
    return out


def champs_layout(chemin):
    """(nom, valeur) des champs d'objets du premier Layout de world.c (hors adresses du jeu)."""
    t = open(chemin, encoding='utf-8').read()
    a = t.index('static const Layout LAYOUTS[] = {{')
    b = t.index('}};', a)
    out = []
    for m in re.finditer(r'\.(\w+) = (0x[0-9a-f]+)', t[a:b]):
        nom, val = m.group(1), int(m.group(2), 16)
        if nom.startswith(('f_', 'h_', 'vt_rigid')) or val >= 0x1000:
            continue
        out.append((nom, val))
    return out


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    A, N = Exe(sys.argv[1]), Exe(sys.argv[2])
    al = Alignement(A, N)
    print('balayage des acces memoire...', flush=True)
    sa, sn = balayer(A), balayer(N)
    suivis = list(champs_layout(sys.argv[3]))
    suivis += [('gaz +0x308', 0x308), ('gaz +0x30c', 0x30c), ('gaz +0x310', 0x310), ('gaz THR_OFFSET +0x314', 0x314),
               ('gestionnaire piste: etat +0x1c', 0x1c), ('gestionnaire piste: proprietaire +0x5c', 0x5c), ('gestionnaire piste: compteur +0xd4', 0xd4)]
    cases_pile = [('pile [ebp-0x%x] %s' % (-d, nom), d) for nom, d in (
        ('avion', -0x1fc), ('gestionnaire', -0x204), ('octet zone finale', -0x205), ('drapeau d\'echec', -0x224), ('decalage z', -0x278),
        ('decalage x', -0x2cc), ('decalage y', -0x270), ('distance', -0x25c), ('vecteur A/B (1)', -0x294), ('vecteur A/B (2)', -0x244),
        ('vecteur A/B (3)', -0x284), ('porte C', -0x24c), ('H2 lea', -0x2d8))]

    def dans_identique(va):
        nv, st, _ = al.va_nouveau(va)
        return st == 'egal'

    L = ['Acces du code aux decalages suivis (ancien exe 1C9A01C3... / nouvel exe 461E1262...), LECTURE SEULE', '',
         'decalage | nom | acces ancien | dont dans du code IDENTIQUE au nouvel | acces nouveau', '---|---|---|---|---']
    # indexation : disp -> adresses (hors cases de pile ebp/esp)
    idx_a, idx_n = defaultdict(list), defaultdict(list)
    for tab, idx in ((sa, idx_a), (sn, idx_n)):
        for a, ds in tab:
            for base, d in ds:
                if base not in ('ebp', 'esp'):
                    idx[d].append(a)
    deja = set()
    for nom, val in suivis:
        if (nom, val) in deja:
            continue
        deja.add((nom, val))
        lst_a = idx_a.get(val, [])
        ident = sum(1 for a in lst_a if dans_identique(a))
        L.append('+0x%x | %s | %d | %d | %d' % (val, nom, len(lst_a), ident, len(idx_n.get(val, []))))
    # champs d'objets : toute la liste ci-dessus est comptee sur tout le code ; les cases de pile seulement dans la fonction de piste
    lo_a, hi_a = FONCTION_PISTE
    L += ['', 'Cases de pile des crochets du frein (base ebp), comptees dans la grande fonction de piste seulement :', '',
          'case | acces ancien (0x6fc730..0x701fa8) | dont dans du code identique | acces nouveau (meme fonction, +0x110)', '---|---|---|---']
    lo_n, hi_n = lo_a + 0x110, hi_a + 0x110
    for nom, d in cases_pile:
        na = [a for a, ds in sa if lo_a <= a < hi_a and any(b == 'ebp' and dd == d for b, dd in ds)]
        nn = [a for a, ds in sn if lo_n <= a < hi_n and any(b == 'ebp' and dd == d for b, dd in ds)]
        ident = sum(1 for a in na if dans_identique(a))
        L.append('%s | %d | %d | %d' % (nom, len(na), ident, len(nn)))
    # la fonction de piste entiere est-elle UNE suite identique ?
    i0 = al.index_ancien(lo_a)
    i1 = al.index_ancien(hi_a - 1)
    k = bisect.bisect_right(al._starts, i0) - 1
    run = al.egaux[k]
    entiere = run[0] <= i0 and i1 < run[0] + run[2]
    L += ['', 'La grande fonction de piste (ancien 0x%x..0x%x, %d instructions) est entierement dans UNE suite d\'instructions identiques au nouvel exe : %s' % (
        lo_a, hi_a, i1 - i0 + 1, 'OUI' if entiere else 'NON'),
        '(sa version dans le nouvel exe commence en 0x%x ; premiere instruction nouvelle de la suite : 0x%x)' % (lo_n, al.BN.addr[run[1] + (i0 - run[0])])]
    open(sys.argv[4], 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    return 0


if __name__ == '__main__':
    sys.exit(main())
