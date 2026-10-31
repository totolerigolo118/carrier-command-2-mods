"""test_portage.py : refait toutes les verifications du portage SANS le jeu. Affiche OK ou ECHEC par test.
Usage : python -I test_portage.py   (ecrit seulement dans travail/)"""
import sys, os, json, glob, struct, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portlib as P
from analyse import *

ECHECS = []
def t(nom, ok, detail=''):
    print('%-6s %s %s' % ('OK' if ok else 'ECHEC', nom, detail))
    if not ok:
        ECHECS.append(nom)

def f(x):
    return struct.pack('<f', x)

def u(h):
    return struct.unpack('<I', bytes.fromhex(h))[0]

os.makedirs(P.TRAVAIL, exist_ok=True)
patched_old = P.Exe(P.F_PATCH)
t('T1 sha256 des 3 copies', P.sha(old.b) == P.SHA_ORIG and P.sha(new.b) == P.SHA_NEW and P.sha(patched_old.b) == P.SHA_PATCH)

orig_mods = {}
for fn in sorted(glob.glob(P.MODDIR + '*.json')):
    m = json.load(open(fn, encoding='utf-8'))
    orig_mods[m['nom']] = m
couverts = set()
presents = {}
for n, m in orig_mods.items():
    k = 0
    for c in m['changements']:
        if patched_old.b[c['offset']:c['offset'] + 4].hex() == c['apres']:
            k += 1
            couverts.update(range(c['offset'], c['offset'] + 4))
    presents[n] = k
diff = set(i for i in range(len(old.b)) if old.b[i] != patched_old.b[i])
t('T2 8E7FCBB6 = original + ascenseur_x2 + temps_x2, sans pont_retour_x2, aucun octet inexplique',
  presents == dict(ascenseur_x2=32, atterrissage_cercle=0, atterrissage_creneau=0, helicos_approche_x2=0, pont_retour_x2=0, temps_x2=1) and diff <= couverts,
  str(presents))

nm = {}
for fn in sorted(glob.glob(P.NOUVEAU_DIR + '*.json')):
    m = json.load(open(fn, encoding='utf-8'))
    nm[m['nom']] = m
attendu = dict(ascenseur_x2=32, atterrissage_cercle=3, atterrissage_creneau=3, helicos_approche_x2=1, pont_retour_x2=1, temps_x2=1)
t('T3 6 modules portes, memes nombres de changements que les originaux',
  set(nm) == set(orig_mods) and all(len(nm[n]['changements']) == len(orig_mods[n]['changements']) == attendu[n] == nm[n]['nb_changements'] for n in nm))
t('T3b sha256_origine = 461E1262 et build du nouvel exe', all(m['sha256_origine'] == P.SHA_NEW and m['build']['taille'] == 11354112 and m['build']['horodatage_pe'] == '0x6ae228f3' for m in nm.values()))
t('T3c va/offset coherents avec le nouvel exe', all(new.va2off(c['va']) == c['offset'] for m in nm.values() for c in m['changements']))
t('T3d champ avant = octets du nouvel exe', all(new.b[c['offset']:c['offset'] + 4].hex() == c['avant'] for m in nm.values() for c in m['changements']))

mauvais = []
nb = 0
for n, m in nm.items():
    for c in m['changements']:
        p = c['portage']
        nb += 1
        if c['offset'] < 0x400:
            if not (p['offset_ancien'] == c['offset'] == 0x310 and all(x == 0 for x in new.b[0x310:0x400]) and all(x == 0 for x in old.b[0x310:0x400])):
                mauvais.append((n, 'entete'))
            continue
        va_o, va_n = p['va_ancien'], c['va']
        if match_at(va_o, va_n) is None:
            mauvais.append((n, hex(va_o), 'instructions differentes'))
            continue
        if p['type_de_champ'] == 'pointeur':
            ok = f(old.f32(u(p['avant_ancien']))) == f(new.f32(u(c['avant'])))
            qa = u(p['apres_ancien'])
            qn = u(c['apres'])
            if qa >= 0x401000:
                ok = ok and f(old.f32(qa)) == f(new.f32(qn))
            else:
                ok = ok and qa == qn == 0x400310
            ok = ok and (va_o - P.BASE) in RO and (va_n - P.BASE) in RN
            if not ok:
                mauvais.append((n, hex(va_o), 'valeur de constante'))
        elif p['type_de_champ'] == 'immediat':
            if c['apres'] != p['apres_ancien'] or c['avant'] != p['avant_ancien']:
                mauvais.append((n, hex(va_o), 'immediat'))
        elif p['type_de_champ'] == 'saut_relatif':
            ta = va_o + 4 + struct.unpack('<i', bytes.fromhex(p['apres_ancien']))[0]
            tn = va_n + 4 + struct.unpack('<i', bytes.fromhex(c['apres']))[0]
            if not same_chain(desasm(old, ta, 5), desasm(new, tn, 5)):
                mauvais.append((n, hex(va_o), 'cible du saut'))
t('T4 %d changements : meme instruction (11 instr.), valeurs de constantes identiques, relocations' % nb, not mauvais, str(mauvais))

asc = nm['ascenseur_x2']
hdr = [c for c in asc['changements'] if c['offset'] == 0x310][0]
lecteurs = [c for c in asc['changements'] if c['offset'] >= 0x400 and u(c['apres']) == 0x400310]
vh = struct.unpack('<f', bytes.fromhex(hdr['apres']))[0]
t('T4b en-tete : 1 ecriture (0x310) + 4 lectures vers VA 0x400310', len(lecteurs) == 4 and hdr['apres'] == hdr['portage']['apres_ancien'], 'valeur ecrite %r' % vh)

APP = P.B + '/portage_appliquer.py'
def run(*a):
    return subprocess.run([sys.executable, '-I', APP] + list(a), capture_output=True, text=True)

ensembles = [(n, [n]) for n in nm] + [('TOUS', list(nm))]
for etiq, lst in ensembles:
    sortie = P.TRAVAIL + 'nouveau_%s.exe' % etiq
    r = run('fabriquer', '--exe', P.F_NEW, '--sortie', sortie, '--module', ','.join(lst))
    if r.returncode != 0 or not os.path.isfile(sortie):
        t('T5 copie %s' % etiq, False, r.stdout + r.stderr)
        continue
    b = P.lire(sortie)
    attendus = {}
    for n in lst:
        for c in nm[n]['changements']:
            for k in range(4):
                attendus[c['offset'] + k] = bytes.fromhex(c['apres'])[k]
    diffs = [i for i in range(len(new.b)) if new.b[i] != b[i]]
    ok = len(b) == len(new.b) and set(diffs) <= set(attendus) and all(b[i] == attendus[i] for i in attendus)
    nbchg = sum(len(nm[n]['changements']) for n in lst)
    sortie2 = P.TRAVAIL + 'retrait_%s.exe' % etiq
    r2 = run('retirer', '--exe', sortie, '--sortie', sortie2)
    ok2 = r2.returncode == 0 and P.lire(sortie2) == new.b and P.sha(P.lire(sortie2)) == P.SHA_NEW
    t('T5 copie %-22s : %2d changements, %2d octets differents de 461E1262, seuls les octets prevus' % (etiq, nbchg, len(diffs)), ok, 'sha256 ' + P.sha(b))
    t('T5 retrait %-20s : redonne exactement 461E1262' % etiq, ok2)
    if etiq != 'TOUS':
        t('T5 sha256_patche du JSON = copie fabriquee (%s)' % etiq, nm[etiq]['sha256_patche'] == P.sha(b))

r = run('retirer', '--exe', P.TRAVAIL + 'nouveau_TOUS.exe', '--sortie', P.TRAVAIL + 'retrait_partiel.exe', '--module', 'temps_x2')
ref = run('fabriquer', '--exe', P.F_NEW, '--sortie', P.TRAVAIL + 'ref_sans_temps.exe', '--module', ','.join(n for n in nm if n != 'temps_x2'))
t('T5b TOUS moins temps_x2 = copie fabriquee avec les 5 autres', r.returncode == 0 and ref.returncode == 0 and P.lire(P.TRAVAIL + 'retrait_partiel.exe') == P.lire(P.TRAVAIL + 'ref_sans_temps.exe'))

nx = P.Exe(P.TRAVAIL + 'nouveau_ascenseur_x2.exe')
nt = P.Exe(P.TRAVAIL + 'nouveau_temps_x2.exe')
mauvais = []
for n, ex in (('ascenseur_x2', nx), ('temps_x2', nt)):
    for c in nm[n]['changements']:
        p = c['portage']
        oo = p['offset_ancien']
        if c['offset'] < 0x400:
            if patched_old.b[oo:oo + 4] != ex.b[c['offset']:c['offset'] + 4]:
                mauvais.append('entete')
        elif p['type_de_champ'] == 'pointeur':
            if f(patched_old.f32(struct.unpack('<I', patched_old.b[oo:oo + 4])[0])) != f(ex.f32(struct.unpack('<I', ex.b[c['offset']:c['offset'] + 4])[0])):
                mauvais.append((n, hex(p['va_ancien'])))
        elif patched_old.b[oo:oo + 4] != ex.b[c['offset']:c['offset'] + 4]:
            mauvais.append((n, hex(p['va_ancien'])))
t('T6 ascenseur_x2 + temps_x2 portes : memes valeurs lues que dans 8E7FCBB6 (ancien exe patche)', not mauvais, str(mauvais))

fake = P.TRAVAIL + 'steamapps/x.exe'
r = run('fabriquer', '--exe', P.F_NEW, '--sortie', fake, '--tous')
t('T7a refuse une sortie dans un chemin steamapps (rien ecrit)', r.returncode != 0 and not os.path.exists(fake))
r = run('fabriquer', '--exe', P.F_NEW, '--sortie', P.F_NEW, '--tous')
t('T7b refuse sortie = entree', r.returncode != 0 and P.sha(P.lire(P.F_NEW)) == P.SHA_NEW)
r = run('fabriquer', '--exe', P.F_ORIG, '--sortie', P.TRAVAIL + 'ne_doit_pas_exister.exe', '--tous')
t('T7c refuse l ancien exe (mauvais sha256)', r.returncode != 0 and not os.path.exists(P.TRAVAIL + 'ne_doit_pas_exister.exe'))
r = run('etat', '--exe', P.TRAVAIL + 'nouveau_TOUS.exe')
t('T7d etat de la copie TOUS : 6 modules patches', r.returncode == 0 and r.stdout.count('patche') == 6, r.stdout.replace('\n', ' | '))

t('T8 les 3 copies de copies/ sont intactes', P.sha(P.lire(P.F_ORIG)) == P.SHA_ORIG and P.sha(P.lire(P.F_NEW)) == P.SHA_NEW and P.sha(P.lire(P.F_PATCH)) == P.SHA_PATCH)
print()
print('RESULTAT GLOBAL :', 'OK' if not ECHECS else 'ECHEC (%s)' % ', '.join(ECHECS))
sys.exit(1 if ECHECS else 0)
