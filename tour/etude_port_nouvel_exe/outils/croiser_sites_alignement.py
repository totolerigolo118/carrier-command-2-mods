#!/usr/bin/env python3
"""Croise les deux methodes independantes : (1) la recherche par contexte (localiser_sites.py) et (2) l'alignement de tout
le code (alignement.py). Pour chaque site de code, les deux doivent donner la MEME nouvelle adresse. LECTURE SEULE.
Usage : python -I -B croiser_sites_alignement.py <ancien> <nouveau> <sites_localises.json> <sortie.txt>"""
import bisect
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_lecture import Exe  # noqa: E402
from alignement import Alignement  # noqa: E402

A, N = Exe(sys.argv[1]), Exe(sys.argv[2])
al = Alignement(A, N)
loc = json.load(open(sys.argv[3], encoding='utf-8'))
dif_starts = [al.BA.addr[d[0]] if d[0] < len(al.BA.addr) else 1 << 40 for d in al.diffs]
dif_ends = [al.BA.addr[d[1] - 1] + al.BA.size[d[1] - 1] if d[1] > d[0] else al.BA.addr[d[0]] for d in al.diffs]
L = ['Croisement recherche-par-contexte / alignement du code entier (ancien -> nouveau)', '']
mauvais = 0
for r in loc['resultats']:
    if r['type'] == 'cave_entete':
        continue
    va = r['va_ancien']
    nv, st, marge = al.va_nouveau(va)
    k = bisect.bisect_right(dif_starts, va)
    avant = va - dif_ends[k - 1] if k > 0 else None
    apres = dif_starts[k] - va if k < len(dif_starts) else None
    ok = nv == r['va_nouveau']
    mauvais += (not ok)
    L.append('%-22s 0x%08x -> 0x%08x  alignement: %s %s ; plus proche bloc different : %s octets avant / %s octets apres' % (
        r['module'], va, r['va_nouveau'], st, 'MEME adresse' if ok else 'ADRESSE DIFFERENTE 0x%x' % (nv or 0),
        '-0x%x' % avant if avant is not None else '-', '+0x%x' % apres if apres is not None else '-'))
L += ['', '%d sites de code croises, %d desaccord(s)' % (sum(1 for r in loc['resultats'] if r['type'] != 'cave_entete'), mauvais)]
open(sys.argv[4], 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print(L[-1])
sys.exit(1 if mauvais else 0)
