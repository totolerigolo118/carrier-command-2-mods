"""Etape 4 : ecrit un JSON porte par module dans modules_exe_nouvel_exe/ (a partir de travail/analyse_sites.json).
N'ecrit rien dans tour/outils/modules_exe/. Un changement non verifie n'entre pas dans le JSON."""
import json, os, sys, struct, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portlib as P

new = P.Exe(P.F_NEW)
assert P.sha(new.b) == P.SHA_NEW
ana = json.load(open(P.TRAVAIL + 'analyse_sites.json'))
os.makedirs(P.NOUVEAU_DIR, exist_ok=True)
rejets = []

def le(v):
    return struct.pack('<I', v).hex()

def porte(r, c):
    """Renvoie (changement_porte, raison_refus)."""
    if r['kind'] == 'entete':
        o = c['offset']
        ok = (new.b[o:o + 4].hex() == c['avant']) and new.sec_of_va(c['va']) == 'EN-TETE' and all(x == 0 for x in new.b[0x310:0x400])
        if not ok:
            return None, 'en-tete du nouvel exe different'
        return dict(va=c['va'], offset=o, avant=c['avant'], apres=c['apres']), None
    if r.get('statut') != 'trouve' or r['nb_candidats'] != 1:
        return None, 'site non retrouve de facon unique par desassemblage'
    on = r['offset_nouveau']
    avant_new = new.b[on:on + 4].hex()
    if r['kind'] == 'pointeur':
        if not (r['avant_valeur_identique'] and r['reloc_nouveau'] and r.get('apres_ptr_nouveau') is not None):
            return None, 'valeur avant non identique, ou pas dans la liste de relocation, ou apres non retrouve'
        if not r['apres_methode'].startswith('en-tete') and not r['apres_valeur_identique']:
            return None, 'valeur apres differente'
        apres = le(r['apres_ptr_nouveau'])
    elif r['kind'] == 'immediat':
        if not r['avant_identique_octets']:
            return None, 'immediat different'
        apres = c['apres']
    elif r['kind'] == 'saut_relatif':
        if not (r['cible_avant_coherente'] and len(r['dt_apres']) == 1 and r.get('apres_nouveau_rel')):
            return None, 'cible de saut non retrouvee de facon unique'
        apres = r['apres_nouveau_rel']
    else:
        return None, 'type de champ inconnu'
    d = dict(va=r['va_nouveau'], offset=on, avant=avant_new, apres=apres)
    return d, None

def appliquer_liste(data, chs, vers):
    b = bytearray(data)
    for c in chs:
        b[c['offset']:c['offset'] + 4] = bytes.fromhex(c[vers])
    return bytes(b)

for f in sorted(glob.glob(P.MODDIR + '*.json')):
    m = json.load(open(f, encoding='utf-8'))
    nom = m['nom']
    chs = []
    for i, c in enumerate(m['changements']):
        r = ana[nom][i]
        d, raison = porte(r, c)
        if d is None:
            rejets.append((nom, i, hex(c['va']), raison))
            continue
        # champs de l'original conserves
        out = dict(va=d['va'], offset=d['offset'], avant=d['avant'], apres=d['apres'], role=c['role'])
        if 'reglage' in c:
            out['reglage'] = c['reglage']
        cv = c.get('constante_va', 0)
        if cv and r['kind'] == 'pointeur':
            pb = struct.unpack('<I', bytes.fromhex(c['apres']))[0]
            if cv == pb:
                cv = r['apres_ptr_nouveau']
            else:
                rejets.append((nom, i, hex(c['va']), 'constante_va (%#x) differe du pointeur apres (%#x) : champ informatif non transpose, a relire' % (cv, pb)))
                cv = 0
        out['constante_va'] = cv
        out['portage'] = dict(va_ancien=c['va'], offset_ancien=c['offset'], avant_ancien=c['avant'], apres_ancien=c['apres'],
                              type_de_champ=r['kind'],
                              instruction_ancien_exe=r.get('instruction_ancien'), instruction_nouvel_exe=r.get('instruction_nouveau'),
                              verifie_par_desassemblage=(r['kind'] != 'entete'),
                              valeur_avant=r.get('avant_valeur_nouveau'), valeur_apres=r.get('apres_valeur_nouveau', r.get('apres_valeur_ancien')))
        chs.append(out)
    if len(chs) != len(m['changements']):
        print('ATTENTION module %s : %d changements portes sur %d : JSON NON ecrit' % (nom, len(chs), len(m['changements'])))
        continue
    patched = appliquer_liste(new.b, chs, 'apres')
    mod = dict(nom=nom, description=m['description'], avertissement=m.get('avertissement', ''),
               etat_du_portage='PORTE SUR COPIE, JAMAIS ESSAYE EN JEU (etude portage_credits)',
               build=dict(fichier='carrier_command.exe', taille=len(new.b), horodatage_pe='0x%08x' % new.pe['ts'],
                          taille_image='0x%08x' % new.pe['imgsize'], base='0x00400000',
                          steam_build='26277078', build_precedent='23836745'),
               sha256_origine=P.SHA_NEW, sha256_patche=P.sha(patched), nb_changements=len(chs), changements=chs)
    json.dump(mod, open(P.NOUVEAU_DIR + nom + '.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ecrit', nom, len(chs), 'changements ; sha256 patche seul', mod['sha256_patche'][:16])
with open(P.NOUVEAU_DIR + 'CHANGEMENTS_NON_PORTES.txt', 'w', encoding='utf-8') as g:
    g.write('Changements non portes ou a relire (module, numero, va ancienne, raison) :\n')
    for r in rejets:
        g.write(' | '.join(str(x) for x in r) + '\n')
    if not rejets:
        g.write('(aucun)\n')
print('non portes / a relire :', len(rejets))
for r in rejets: print('  ', r)
