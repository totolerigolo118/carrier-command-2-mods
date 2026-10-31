"""Etape 2 : retrouve chaque site dans le nouvel exe par DESASSEMBLAGE ; compare ; verifie les valeurs flottantes.
Lecture seule. Sorties : travail/analyse_sites.json, travail/etape2_desassemblage.txt"""
import sys, os, json, glob, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portlib as P
from analyse import *
from collections import Counter

assert P.sha(old.b) == P.SHA_ORIG and P.sha(new.b) == P.SHA_NEW
os.makedirs(P.TRAVAIL, exist_ok=True)

def f32eq(a, b):
    return struct.pack('<f', a) == struct.pack('<f', b)

def target_new(t_old, d):
    """Cherche la cible de saut dans le nouvel exe : memes 5 instructions, decalage proche de d."""
    co = desasm(old, t_old)
    res = []
    for dt in range(d - 0x60, d + 0x60):
        cn = desasm(new, t_old + dt)
        if len(cn) == 5 and same_chain(co, cn):
            res.append(dt)
    return res

mods = {}
for f in sorted(glob.glob(P.MODDIR + '*.json')):
    m = json.load(open(f, encoding='utf-8'))
    mods[m['nom']] = m
out = {}
txt = []

def traite_pointeur(r, c, on, txt):
    pa = struct.unpack('<I', bytes.fromhex(c['avant']))[0]
    pb = struct.unpack('<I', bytes.fromhex(c['apres']))[0]
    pn = struct.unpack('<I', new.b[on:on + 4])[0]
    fa = old.f32(pa)
    fn = new.f32(pn)
    r['avant_ptr_ancien'] = pa
    r['avant_ptr_nouveau'] = pn
    r['avant_valeur_ancien'] = fa
    r['avant_valeur_nouveau'] = fn
    r['avant_valeur_identique'] = f32eq(fa, fn)
    r['decalage_constante_avant'] = pn - pa
    txt.append('  VALEUR avant : ancien [0x%08x]=%r ; nouveau [0x%08x]=%r ; identique=%s ; decalage %+#x' % (pa, fa, pn, fn, r['avant_valeur_identique'], pn - pa))
    sa = old.sec_of_va(pb)
    fb = old.f32(pb)
    r['apres_ptr_ancien'] = pb
    r['apres_valeur_ancien'] = fb
    if sa == 'EN-TETE':
        r['apres_ptr_nouveau'] = pb
        r['apres_methode'] = 'en-tete : meme adresse'
        txt.append('  VALEUR apres : adresse en-tete 0x%08x conservee ; valeur ecrite par ascenseur_x2 #0' % pb)
        return
    dd, L, n = ctx_find(pb)
    r['apres_methode'] = 'contexte +-%d octets, %d candidat(s)' % (L, n)
    if dd is None:
        r['apres_ptr_nouveau'] = None
        txt.append('  VALEUR apres : ancien [0x%08x]=%r ; NON RETROUVE (%s)' % (pb, fb, r['apres_methode']))
        return
    pbn = pb + dd
    fbn = new.f32(pbn)
    r['apres_ptr_nouveau'] = pbn
    r['apres_valeur_nouveau'] = fbn
    r['apres_valeur_identique'] = f32eq(fb, fbn)
    r['apres_decalage'] = dd
    txt.append('  VALEUR apres : ancien [0x%08x]=%r ; nouveau [0x%08x]=%r ; identique=%s ; decalage %+#x ; %s' % (pb, fb, pbn, fbn, r['apres_valeur_identique'], dd, r['apres_methode']))

def traite_saut(r, c, va, vn, on, d, txt):
    ra = struct.unpack('<i', bytes.fromhex(c['avant']))[0]
    rb = struct.unpack('<i', bytes.fromhex(c['apres']))[0]
    rn = struct.unpack('<i', new.b[on:on + 4])[0]
    ta = va + 4 + ra
    tb = va + 4 + rb
    tn = vn + 4 + rn
    dta = target_new(ta, d)
    dtb = target_new(tb, d)
    r['cible_avant_ancien'] = ta
    r['cible_apres_ancien'] = tb
    r['cible_avant_nouveau_lue'] = tn
    r['dt_avant'] = dta
    r['dt_apres'] = dtb
    ok1 = (len(dta) == 1 and ta + dta[0] == tn)
    r['cible_avant_coherente'] = ok1
    txt.append('  SAUT : cible avant ancien 0x%x ; cible lue dans le nouvel exe 0x%x ; decalage de cible retrouve par desassemblage %s ; coherent=%s' % (ta, tn, [hex(x) for x in dta], ok1))
    txt.append('  cible apres (ancien) 0x%x ; decalage de cible retrouve %s' % (tb, [hex(x) for x in dtb]))
    if len(dtb) == 1:
        newrel = (tb + dtb[0]) - (vn + 4)
        r['apres_nouveau_rel'] = struct.pack('<i', newrel).hex()
        txt.append('  apres calcule pour le nouvel exe : %s (ancien %s)' % (r['apres_nouveau_rel'], c['apres']))
    for nomc, tt, dts in (('cible avant', ta, dta), ('cible apres', tb, dtb)):
        if len(dts) == 1:
            for a, b in zip(desasm(old, tt, 3), desasm(new, tt + dts[0], 3)):
                txt.append('      %s : %-44s| %s' % (nomc, fmt(a), fmt(b)))

for nom, m in mods.items():
    out[nom] = []
    for i, c in enumerate(m['changements']):
        va = c['va']
        off = c['offset']
        r = dict(i=i, va=va, offset=off, avant=c['avant'], apres=c['apres'], role=c['role'])
        txt.append('=' * 100)
        txt.append('%s #%d  va 0x%08x offset 0x%x  avant %s apres %s' % (nom, i, va, off, c['avant'], c['apres']))
        txt.append('  role : ' + c['role'][:220])
        assert old.va2off(va) == off
        assert old.b[off:off + 4].hex() == c['avant']
        out[nom].append(r)
        if off < 0x400:
            r['kind'] = 'entete'
            r['statut'] = 'EN-TETE'
            txt.append('  EN-TETE (voir etape 3)')
            continue
        r['reloc_ancien'] = (va - P.BASE) in RO
        hits = find_new(va)
        r['nb_candidats'] = len(hits)
        if len(hits) != 1:
            r['statut'] = 'AMBIGU' if hits else 'NON RETROUVE'
            r['decalages_candidats'] = [h[0] for h in hits]
            txt.append('  %s : candidats %s' % (r['statut'], [hex(h[0]) for h in hits]))
            continue
        d, (co, cn, ix) = hits[0]
        vn = va + d
        on = new.va2off(vn)
        r['decalage_code'] = d
        r['va_nouveau'] = vn
        r['offset_nouveau'] = on
        r['reloc_nouveau'] = (vn - P.BASE) in RN
        r['kind'] = classify(co[ix], va)
        r['avant_nouveau'] = new.b[on:on + 4].hex()
        r['instruction_ancien'] = fmt(co[ix])
        r['instruction_nouveau'] = fmt(cn[ix])
        txt.append('  site nouveau : va 0x%08x offset 0x%x (decalage +0x%x) ; champ : %s ; liste de relocation ancien/nouveau : %s/%s' % (vn, on, d, r['kind'], r['reloc_ancien'], r['reloc_nouveau']))
        txt.append('  ANCIEN exe (1C9A01C3)                                       | NOUVEL exe (461E1262)')
        for k in range(len(co)):
            txt.append('  %s %-56s| %s' % ('>>' if k == ix else '  ', fmt(co[k]), fmt(cn[k])))
        r['statut'] = 'trouve'
        if r['kind'] == 'pointeur':
            traite_pointeur(r, c, on, txt)
        elif r['kind'] == 'immediat':
            r['apres_ptr_nouveau'] = None
            r['avant_identique_octets'] = (r['avant_nouveau'] == c['avant'])
            txt.append('  IMMEDIAT (aucune adresse) : %s -> %s ; avant dans le nouvel exe = %s (identique=%s)' % (c['avant'], c['apres'], r['avant_nouveau'], r['avant_identique_octets']))
        elif r['kind'] == 'saut_relatif':
            traite_saut(r, c, va, vn, on, d, txt)
json.dump(out, open(P.TRAVAIL + 'analyse_sites.json', 'w'), indent=1)
open(P.TRAVAIL + 'etape2_desassemblage.txt', 'w', encoding='utf-8').write('\n'.join(txt))
cnt = Counter((r.get('statut'), r.get('kind')) for v in out.values() for r in v)
print(cnt)
