import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portlib as P
from collections import Counter
a = json.load(open(P.TRAVAIL + 'analyse_sites.json'))
for n in a:
    L = a[n]
    c = Counter()
    for r in L:
        c['total'] += 1
        c['site unique par desassemblage'] += (r.get('nb_candidats') == 1)
        c['kind=' + r['kind']] += 1
        c['decalage code ' + hex(r.get('decalage_code', -1))] += 1
        if r['kind'] == 'pointeur':
            c['ptr: dans liste de relocation (ancien et nouveau)'] += (r['reloc_ancien'] and r['reloc_nouveau'])
            c['ptr: valeur avant identique'] += r['avant_valeur_identique']
            c['ptr: apres retrouve'] += (r.get('apres_ptr_nouveau') is not None)
            c['ptr: valeur apres identique'] += bool(r.get('apres_valeur_identique'))
            c['ptr: apres en-tete'] += (r['apres_methode'].startswith('en-tete'))
        if r['kind'] == 'immediat':
            c['imm: avant identique'] += r['avant_identique_octets']
            c['imm: reloc'] += r['reloc_nouveau']
        if r['kind'] == 'saut_relatif':
            c['saut: cible avant coherente'] += r['cible_avant_coherente']
            c['saut: cible apres retrouvee unique'] += (len(r['dt_apres']) == 1)
            c['saut: apres rel nouveau == ancien'] += (r.get('apres_nouveau_rel') == r['apres'])
    print('##', n)
    for k in sorted(c):
        print('   ', k, c[k])
