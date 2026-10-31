#!/usr/bin/env python3
"""Tests de patch_exe.py pour le PROFIL du build de Steam du 28/10/2026 (461E1262...), sur des COPIES (jamais sur le vrai jeu).

Usage : python -I -B test_patch_exe_nouveau.py <nouvel_exe_original_461E1262.exe> <ancien_original_1C9A01C3.exe> <dossier_de_travail_vide> [<dossier_du_jeu>]
Le dossier de travail recoit des copies de 11 Mo ; il peut etre supprime ensuite.
Le dossier du jeu (facultatif) n'est LU que pour `etat` (lecture seule) : on y verifie que le vrai exe est reconnu et que les
autres exe (vr, serveur dedie) sont refuses. Rien n'est jamais ecrit dans ce dossier.
"""
import hashlib
import importlib.util
import itertools
import json
import os
import shutil
import struct
import subprocess
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

NEUF, ANCIEN, TRAVAIL = (os.path.abspath(a) for a in sys.argv[1:4])
JEU = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else None
ICI = os.path.dirname(os.path.abspath(__file__))
OUTIL = os.path.join(ICI, 'patch_exe.py')
DOSSIER_JSON = os.path.join(ICI, 'modules_exe_461E1262')
os.makedirs(TRAVAIL, exist_ok=True)

SHA_NEUF = '461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A'
SHA_ANCIEN = '1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026'
NOMS = ['ascenseur_x2', 'temps_x2', 'atterrissage_cercle', 'atterrissage_creneau', 'pont_retour_x2', 'helicos_approche_x2']
MODS = {n: json.load(open(os.path.join(DOSSIER_JSON, n + '.json'), encoding='utf-8')) for n in NOMS}

echecs = 0
total = 0


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()


def sha_octets(b):
    return hashlib.sha256(bytes(b)).hexdigest().upper()


def verifie(cond, msg):
    global echecs, total
    total += 1
    if not cond:
        echecs += 1
        print('    ECHEC :', msg)


def outil(*args):
    r = subprocess.run([sys.executable, '-I', '-B', OUTIL, *args], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def copie(nom, source=NEUF):
    p = os.path.join(TRAVAIL, nom)
    shutil.copyfile(source, p)
    return p


def titre(t):
    print('\n== %s' % t)


verifie(sha(NEUF) == SHA_NEUF, 'la copie fournie est bien le nouvel exe de Steam (461E1262...)')
verifie(sha(ANCIEN) == SHA_ANCIEN, 'l\'ancien original fourni est bien 1C9A01C3...')
orig = open(NEUF, 'rb').read()


def attendu_sha(noms):
    """Somme calculee ICI : original + les changements des modules donnes (sans passer par l'outil)."""
    b = bytearray(orig)
    for n in noms:
        for c in MODS[n]['changements']:
            b[c['offset']:c['offset'] + 4] = bytes.fromhex(c['apres'])
    return sha_octets(b)


# --------------------------------------------------------------------------
titre('0. les JSON du profil : somme epinglee, champs disjoints, octets d\'origine, relocations')
spec = importlib.util.spec_from_file_location('patch_exe_sous_test', OUTIL)
PE_OUTIL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PE_OUTIL)
sys.path.insert(0, ICI)
verifie(len(PE_OUTIL.PROFILS) == 2, 'l\'outil connait exactement 2 profils')
verifie(all(m['sha256_origine'] == SHA_NEUF and m['build']['horodatage_pe'] == '0x6ae228f3' for m in MODS.values()),
        'les 6 modules portent la somme 461E1262... et l\'horodatage 0x6ae228f3')
verifie({n: len(m['changements']) for n, m in MODS.items()} == {'ascenseur_x2': 32, 'temps_x2': 1, 'atterrissage_cercle': 3,
                                                                  'atterrissage_creneau': 3, 'pont_retour_x2': 1, 'helicos_approche_x2': 1},
        'nombres de changements = ceux de l\'ancien profil (32, 1, 3, 3, 1, 1)')
plages = sorted((c['offset'], c['offset'] + 4, n) for n, m in MODS.items() for c in m['changements'])
verifie(len(plages) == 41 and all(plages[i][1] <= plages[i + 1][0] for i in range(len(plages) - 1)), '41 champs, aucun chevauchement')
verifie(all(orig[c['offset']:c['offset'] + 4].hex() == c['avant'] for m in MODS.values() for c in m['changements']),
        'les octets d\'origine de chaque champ sont ceux du nouvel exe')
verifie(all(m['sha256_patche'] == attendu_sha([n]) for n, m in MODS.items()), 'sha256_patche de chaque JSON = somme recalculee ici')

# structure PE (lecture a part, sans les outils de l'etude)
pe = struct.unpack_from('<I', orig, 0x3C)[0]
nsec = struct.unpack_from('<H', orig, pe + 6)[0]
optsz = struct.unpack_from('<H', orig, pe + 20)[0]
opt = pe + 24
base = struct.unpack_from('<I', orig, opt + 28)[0]
soh = struct.unpack_from('<I', orig, opt + 60)[0]
secs = []
for i in range(nsec):
    o = opt + optsz + 40 * i
    nom_s = orig[o:o + 8].rstrip(b'\0').decode()
    vs, va, rs, rp = struct.unpack_from('<IIII', orig, o + 8)
    fl = struct.unpack_from('<I', orig, o + 36)[0]
    secs.append((base + va, min(vs, rs), rp, nom_s, fl))


def off(va):
    if base <= va < base + soh:
        return va - base
    for sva, n, rp, _, _ in secs:
        if sva <= va < sva + n:
            return rp + va - sva
    raise ValueError(hex(va))


def flags(va):
    for sva, n, rp, nm, fl in secs:
        if sva <= va < sva + n:
            return nm, fl
    return '(en-tete)', 0


reloc_rva, reloc_size = struct.unpack_from('<II', orig, opt + 96 + 5 * 8)
relocs = set()
p = off(base + reloc_rva)
while p < off(base + reloc_rva) + reloc_size:
    page, blk = struct.unpack_from('<II', orig, p)
    if blk < 8:
        break
    for k in range((blk - 8) // 2):
        e = struct.unpack_from('<H', orig, p + 8 + 2 * k)[0]
        if (e >> 12) == 3:
            relocs.add(page + (e & 0xFFF))
    p += blk
for n, m in MODS.items():
    for c in m['changements']:
        if c['type'] == 'abs':
            verifie((c['va'] - base) in relocs, '%s 0x%08x : operande avec entree de relocation' % (n, c['va']))
        elif c['type'] in ('imm',):
            verifie((c['va'] - base) not in relocs, '%s 0x%08x : immediat sans relocation' % (n, c['va']))

# --------------------------------------------------------------------------
titre('1. cycle normal de CHAQUE module (etat, a blanc, activer, deja actif, retirer)')
for n in NOMS:
    m = MODS[n]
    w = copie('cycle_%s.exe' % n)
    rc, out = outil('etat', '--exe', w)
    verifie(rc == 0 and 'ORIGINAL' in out and '461E1262' in out, '%s : etat initial = ORIGINAL' % n)
    rc, out = outil('activer', '--exe', w, '--module', n)
    verifie(rc != 0 and sha(w) == SHA_NEUF, '%s : activer sans --sauvegarde refuse, fichier intact' % n)
    rc, out = outil('activer', '--exe', w, '--sauvegarde', NEUF, '--module', n, '--a-blanc')
    verifie(rc == 0 and sha(w) == SHA_NEUF and 'A BLANC' in out, '%s : --a-blanc n\'ecrit rien' % n)
    rc, out = outil('activer', '--exe', w, '--sauvegarde', NEUF, '--module', n)
    verifie(rc == 0 and sha(w) == m['sha256_patche'] and 'ACTIF' in out, '%s : activer -> somme attendue %s' % (n, m['sha256_patche'][:8]))
    rc, out = outil('etat', '--exe', w)
    verifie(rc == 0 and 'PATCHE (%s' % n in out, '%s : etat = PATCHE' % n)
    rc, out = outil('activer', '--exe', w, '--sauvegarde', NEUF, '--module', n)
    verifie(rc == 0 and 'Deja actif' in out and sha(w) == m['sha256_patche'], '%s : 2e activation sans effet' % n)
    rc, out = outil('retirer', '--exe', w, '--module', n)
    verifie(rc == 0 and sha(w) == SHA_NEUF and 'EXACTEMENT' in out, '%s : retirer -> le fichier redevient EXACTEMENT 461E1262...' % n)
    rc, out = outil('retirer', '--exe', w, '--module', n)
    verifie(rc == 0 and 'Deja d\'origine' in out, '%s : 2e retrait sans effet' % n)

# --------------------------------------------------------------------------
titre('2. relecture au desassembleur des 6 modules actifs : valeurs finales voulues (ecrites ici a la main)')
tout = copie('tous_les_modules.exe')
for n in NOMS:
    rc, _ = outil('activer', '--exe', tout, '--sauvegarde', NEUF, '--module', n)
    verifie(rc == 0, '%s activer (ensemble des 6)' % n)
d_tout = open(tout, 'rb').read()
verifie(sha_octets(d_tout) == attendu_sha(NOMS), 'les 6 modules actifs : somme = original + 6 jeux de changements (calcul a part)')


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


VOULU = {'CP_T_ENERGY_SHARE': 0.8, 'CP_T_PLATFORM_STEP': 0.05, 'CP_T_PLATFORM_STEP_NEG': -0.05,
         'CP_T_CRANE_H': 1 / 3, 'CP_T_CRANE_H_NEG': -1 / 3, 'CP_T_CRANE_V': 1 / 15, 'CP_T_CRANE_V_NEG': -1 / 15,
         'CP_T_CRANE_ROT': 0.08, 'CP_T_CRANE_ROT_NEG': -0.08, 'CP_T_TAXI_ACCEL': 0.1, 'CP_T_TAXI_CAP': 5.0,
         'RETURN_TAXI_TICKS_PER_SECOND': 15.0, 'HELI_APPROACH_AIM_AHEAD_M': 100.0,
         'LANDING_CIRCLE_STATE3_END': -1800.0, 'LANDING_CIRCLE_STATE5_END': -1800.0, 'LANDING_CIRCLE_FRONT_CENTER_Z': -1800.0,
         'SERVER_SPEED_FACTOR': 2.0}
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
n_vus = 0
for n, m in MODS.items():
    for c in m['changements']:
        if c['va'] < base + soh:
            v = struct.unpack_from('<f', d_tout, off(c['va']))[0]
            verifie(v == f32(VOULU[c['reglage']]), '%s : -1/15 present dans le bourrage de l\'en-tete' % n)
            n_vus += 1
            continue
        t = c['type']
        if t == 'imm':
            k = {'CP_T_ENERGY_SHARE': 3, 'SERVER_SPEED_FACTOR': 6, 'LANDING_CIRCLE_FRONT_CENTER_Z': 6}[c['reglage']]   # le champ est la fin de `mov [mem], imm32`
            ins = next(md.disasm(d_tout[off(c['va']) - k:off(c['va']) - k + 15], c['va'] - k))
            ok = (ins.mnemonic == 'mov' and ins.size == k + 4
                  and (ins.operands[-1].imm & 0xFFFFFFFF) == struct.unpack('<I', struct.pack('<f', VOULU[c['reglage']]))[0])
            verifie(ok, '%s 0x%08x : %s %s' % (n, c['va'], ins.mnemonic, ins.op_str))
        elif t == 'abs':
            # l'operande est la fin de l'instruction : movss/addss/maxss = 8 octets (prefixe f3), comiss = 7 octets
            k = 3 if c['reglage'] == 'LANDING_CIRCLE_STATE3_END' else 4
            ins = next(md.disasm(d_tout[off(c['va']) - k:off(c['va']) - k + 15], c['va'] - k))
            mem = [o for o in ins.operands if o.type == X86_OP_MEM]
            cva = mem[0].mem.disp & 0xFFFFFFFF
            val = struct.unpack_from('<f', d_tout, off(cva))[0]
            nm_s, fl_s = flags(cva)
            ok = (len(mem) == 1 and mem[0].mem.base == 0 and mem[0].mem.index == 0 and cva == c['constante_va']
                  and val == f32(VOULU[c['reglage']]) and ins.size == k + 4 and not (fl_s & 0x80000000))
            verifie(ok, '%s 0x%08x %s %s lit %.9g (voulu %.9g, %s)' % (n, ins.address, ins.mnemonic, ins.op_str, val, VOULU[c['reglage']], nm_s))
        else:   # rel32 : jbe (6 octets, champ a +2) ou jmp (5 octets, champ a +1)
            k, mn = (1, 'jmp') if c['reglage'] == 'LANDING_GATE_STATE2_TO_3' else (2, 'jbe')
            ins = next(md.disasm(d_tout[off(c['va']) - k:off(c['va']) - k + 15], c['va'] - k))
            cible = ins.operands[0].imm & 0xFFFFFFFF
            blk = next(md.disasm(d_tout[off(cible):off(cible) + 15], cible))
            verifie(ins.mnemonic == mn and ins.size == k + 4 and blk.mnemonic == 'cmp' and blk.op_str == 'dword ptr [edi], 1',
                    '%s 0x%08x : %s %s -> `%s %s` (test de la piste)' % (n, c['va'], ins.mnemonic, ins.op_str, blk.mnemonic, blk.op_str))
        n_vus += 1
verifie(n_vus == 41, '41 champs relus (trouve %d)' % n_vus)

# --------------------------------------------------------------------------
titre('3. combinaisons : les 63 combinaisons (en memoire, avec les fonctions de l\'outil) + 8 par la ligne de commande')
mods_outil, sha_o_outil = PE_OUTIL.charger_tous(PE_OUTIL.PROFILS[1])
verifie(sha_o_outil == SHA_NEUF and set(mods_outil) == set(NOMS), 'l\'outil charge les 6 modules du profil Steam')
n_combos = 0
bons = True
for r_ in range(1, 7):
    for combo in itertools.combinations(NOMS, r_):
        data = orig
        for n in combo:
            data = PE_OUTIL.appliquer(data, mods_outil[n], 'apres')
        ok1 = sha_octets(data) == attendu_sha(combo)
        ok2 = PE_OUTIL.coherence_globale(data, mods_outil, sha_o_outil)[0]
        ok3 = all(PE_OUTIL.etat_module(data, mods_outil[n], mods_outil, sha_o_outil)[0] == ('patche' if n in combo else 'original') for n in NOMS)
        dd = data
        for n in reversed(combo):
            dd = PE_OUTIL.appliquer(dd, mods_outil[n], 'avant')
        ok4 = dd == orig
        bons = bons and ok1 and ok2 and ok3 and ok4
        n_combos += 1
verifie(n_combos == 63 and bons, '63 combinaisons : somme juste, coherence globale, etat de chaque module, retour exact a 461E1262...')
for combo, ordre in ((NOMS, 'inverse'), (NOMS, 'direct'), (['ascenseur_x2', 'temps_x2'], 'inverse'), (['temps_x2', 'ascenseur_x2'], 'direct'),
                     (['atterrissage_cercle', 'atterrissage_creneau', 'pont_retour_x2'], 'inverse'),
                     (['helicos_approche_x2', 'ascenseur_x2'], 'direct'), (['pont_retour_x2', 'temps_x2'], 'inverse'),
                     (['atterrissage_creneau', 'helicos_approche_x2', 'temps_x2'], 'direct')):
    w = copie('combo_%s.exe' % '_'.join(n[:4] for n in combo))
    bon = True
    for k, n in enumerate(combo):
        rc, _ = outil('activer', '--exe', w, '--sauvegarde', NEUF, '--module', n)
        bon = bon and rc == 0 and sha(w) == attendu_sha(combo[:k + 1])
    verifie(bon, 'ligne de commande %s : somme juste apres chaque activation' % '+'.join(combo))
    retour = list(reversed(combo)) if ordre == 'inverse' else list(combo)
    restant = list(combo)
    bon = True
    for n in retour:
        rc, _ = outil('retirer', '--exe', w, '--module', n)
        restant.remove(n)
        bon = bon and rc == 0 and sha(w) == (attendu_sha(restant) if restant else SHA_NEUF)
    verifie(bon and sha(w) == SHA_NEUF, 'ligne de commande %s : retirer (ordre %s) redonne chaque etat puis 461E1262... exact' % ('+'.join(combo), ordre))

# --------------------------------------------------------------------------
titre('4. refus sur le profil Steam : octets abimes, melange, mauvaises sauvegardes, options')


def refuse_sans_rien_ecrire(w, *args, mots=()):
    avant = sha(w)
    rc, out = outil(*args)
    return rc == 3 and sha(w) == avant and not os.path.exists(w + '.cc2_tmp') and all(mot in out for mot in mots), out


w = copie('abime_site.exe')
b = bytearray(open(w, 'rb').read())
c0 = MODS['ascenseur_x2']['changements'][5]
b[c0['offset']] ^= 0xFF
open(w, 'wb').write(b)
for args, nom in ((('activer', '--exe', w, '--sauvegarde', NEUF), 'activer'), (('retirer', '--exe', w), 'retirer'),
                  (('retirer', '--exe', w, '--sauvegarde', NEUF, '--restaurer-tout-l-exe'), 'retirer --restaurer-tout-l-exe'),
                  (('etat', '--exe', w), 'etat')):
    ok, out = refuse_sans_rien_ecrire(w, *args, mots=('INCONNU',))
    verifie(ok, 'un site de module abime : %s -> refus (code 3), octets inchanges' % nom)
w = copie('abime_autre.exe')
b = bytearray(open(w, 'rb').read())
b[0x2000] ^= 0xFF
open(w, 'wb').write(b)
for args, nom in ((('activer', '--exe', w, '--sauvegarde', NEUF, '--module', 'temps_x2'), 'activer'), (('retirer', '--exe', w), 'retirer'),
                  (('retirer', '--exe', w, '--sauvegarde', NEUF, '--restaurer-tout-l-exe'), 'retirer --restaurer-tout-l-exe')):
    ok, out = refuse_sans_rien_ecrire(w, *args, mots=('INCONNU', 'demander au moddeur'))
    verifie(ok, 'un octet modifie hors des modules : %s -> refus (code 3), octets inchanges' % nom)

w = copie('melange.exe')
outil('activer', '--exe', w, '--sauvegarde', NEUF, '--module', 'ascenseur_x2')
b = bytearray(open(w, 'rb').read())
c1 = MODS['ascenseur_x2']['changements'][3]
b[c1['offset']:c1['offset'] + 4] = bytes.fromhex(c1['avant'])
open(w, 'wb').write(b)
ok, out = refuse_sans_rien_ecrire(w, 'activer', '--exe', w, '--sauvegarde', NEUF)
verifie(ok and 'MELANGE' in out, 'etat melange : activer refuse')
ok, out = refuse_sans_rien_ecrire(w, 'retirer', '--exe', w)
verifie(ok, 'etat melange : retirer sans sauvegarde refuse')
ok, out = refuse_sans_rien_ecrire(w, 'retirer', '--exe', w, '--sauvegarde', NEUF)
verifie(ok and '--restaurer-tout-l-exe' in out, 'etat melange : --sauvegarde seule ne remplace pas le fichier')
ok, out = refuse_sans_rien_ecrire(w, 'retirer', '--exe', w, '--sauvegarde', ANCIEN, '--restaurer-tout-l-exe')
verifie(ok, 'etat melange : sauvegarde = l\'ANCIEN original (autre build) refusee')
rc, out = outil('retirer', '--exe', w, '--sauvegarde', NEUF, '--restaurer-tout-l-exe')
verifie(rc == 0 and sha(w) == SHA_NEUF, 'etat melange : sauvegarde 461E1262... + drapeau explicite -> original exact')

w = copie('mauvaise_sauv.exe')
patche_ref = copie('patche_ref.exe')
outil('activer', '--exe', patche_ref, '--sauvegarde', NEUF, '--module', 'ascenseur_x2')
for sauv, nom in ((ANCIEN, 'l\'ANCIEN original 1C9A01C3...'), (patche_ref, 'un exe patche'), (w, 'le fichier lui-meme'),
                  (os.path.join(TRAVAIL, 'nexiste_pas.exe'), 'un fichier absent')):
    ok, out = refuse_sans_rien_ecrire(w, 'activer', '--exe', w, '--sauvegarde', sauv)
    verifie(ok, 'sauvegarde = %s : activer refuse, octets inchanges' % nom)

faux = os.path.join(TRAVAIL, 'steamapps', 'common', 'Carrier Command 2')
os.makedirs(faux, exist_ok=True)
w = os.path.join(faux, 'carrier_command.exe')
shutil.copyfile(NEUF, w)
for args, nom in ((('activer', '--exe', w, '--sauvegarde', NEUF), 'sans confirmation'),
                  (('activer', '--exe', w, '--sauvegarde', NEUF, '--cest-le-vrai-jeu'), 'AVEC --cest-le-vrai-jeu'),
                  (('activer', '--exe', w, '--sauvegarde', NEUF, '--cest-le-vrai-jeu', '--module', 'temps_x2'), 'temps_x2 avec --cest-le-vrai-jeu'),
                  (('activer', '--exe', w, '--sauvegarde', NEUF, '--cest-le-vrai-jeu', '--a-blanc'), 'a blanc avec --cest-le-vrai-jeu')):
    ok, out = refuse_sans_rien_ecrire(w, *args, mots=('JAMAIS', 'steamapps', 'demander au moddeur'))
    verifie(ok, 'chemin « steamapps » : activer %s -> refus (code 3), octets inchanges' % nom)
rc, out = outil('etat', '--exe', w)
verifie(rc == 0 and 'ORIGINAL' in out and sha(w) == SHA_NEUF, 'chemin « steamapps » : etat (lecture seule) reste permis')
# retirer sur une copie patchee placee sous steamapps (cas d'un patch fait avant) : refuse aussi
w2 = os.path.join(faux, 'carrier_command_copie_patchee.exe')
shutil.copyfile(patche_ref, w2)
ok, out = refuse_sans_rien_ecrire(w2, 'retirer', '--exe', w2, '--cest-le-vrai-jeu')
verifie(ok and 'JAMAIS' in out, 'chemin « steamapps » : retirer refuse aussi, meme avec --cest-le-vrai-jeu')

w = copie('options.exe')
rc, out = outil('activer', '--exe', w, '--sauvegarde', NEUF, '--option-inconnue')
verifie(rc == 2 and sha(w) == SHA_NEUF, 'option inconnue : refus, fichier intact')
rc, out = outil('activer', '--exe', w, '--sauv', NEUF)
verifie(rc == 2 and sha(w) == SHA_NEUF, 'option abregee (--sauv) : refus, fichier intact')
rc, out = outil('activer', '--sauvegarde', NEUF)
verifie(rc == 2, 'sans --exe : refus (aucun chemin par defaut)')
rc, out = outil('activer', '--exe', w, '--sauvegarde', NEUF, '--module', 'nexiste_pas')
verifie(rc != 0 and sha(w) == SHA_NEUF, 'module inconnu : refus')

# --------------------------------------------------------------------------
titre('5. melange de profils : le profil se choisit par l\'horodatage ET les octets doivent suivre ; aucun autre fichier accepte')


def exe_modifie(nom, source, modif):
    p = os.path.join(TRAVAIL, nom)
    b = bytearray(open(source, 'rb').read())
    modif(b)
    open(p, 'wb').write(b)
    return p


def met_horodatage(b, valeur):
    struct.pack_into('<I', b, struct.unpack_from('<I', b, 0x3C)[0] + 8, valeur)


w = exe_modifie('ancien_avec_horodatage_neuf.exe', ANCIEN, lambda b: met_horodatage(b, 0x6ae228f3))
for args, nom in ((('activer', '--exe', w, '--sauvegarde', NEUF), 'activer'), (('retirer', '--exe', w, '--sauvegarde', NEUF, '--restaurer-tout-l-exe'), 'retirer + drapeau')):
    ok, out = refuse_sans_rien_ecrire(w, *args, mots=('INCONNU', 'BUILD DE STEAM', 'demander au moddeur'))
    verifie(ok, 'ancien exe deguise (horodatage Steam) : %s -> refus, octets inchanges' % nom)
w = exe_modifie('neuf_avec_horodatage_ancien.exe', NEUF, lambda b: met_horodatage(b, 0x6a36c177))
for args, nom in ((('activer', '--exe', w, '--sauvegarde', ANCIEN), 'activer'), (('retirer', '--exe', w, '--sauvegarde', ANCIEN, '--restaurer-tout-l-exe'), 'retirer + drapeau')):
    ok, out = refuse_sans_rien_ecrire(w, *args, mots=('INCONNU', 'demander au moddeur'))
    verifie(ok, 'nouvel exe deguise (horodatage ancien) : %s -> refus, octets inchanges' % nom)
w = exe_modifie('autre_horodatage.exe', NEUF, lambda b: met_horodatage(b, 0x12345678))
for args, nom in ((('activer', '--exe', w, '--sauvegarde', NEUF), 'activer'), (('retirer', '--exe', w, '--sauvegarde', NEUF, '--restaurer-tout-l-exe'), 'retirer + drapeau'),
                  (('etat', '--exe', w), 'etat')):
    ok, out = refuse_sans_rien_ecrire(w, *args, mots=('horodatage de compilation',))
    verifie(ok, 'horodatage 0x12345678 : %s -> refus (code 3), octets inchanges' % nom)
w = os.path.join(TRAVAIL, 'pas_un_pe.exe')
open(w, 'wb').write(b'MZ' + bytes(100))
ok, out = refuse_sans_rien_ecrire(w, 'retirer', '--exe', w, '--sauvegarde', NEUF, '--restaurer-tout-l-exe', mots=('illisible',))
verifie(ok, 'fichier qui n\'est pas un PE lisible : retirer refuse, octets inchanges')
# le sha d'un fichier ajoute a la liste noire est refuse meme avec un horodatage connu
copie_ref = open(patche_ref, 'rb').read()
PE_OUTIL.SHA256_BUILDS_ETRANGERS.add(sha_octets(copie_ref))
verifie('BUILD ETRANGER' in (PE_OUTIL.build_refuse(copie_ref) or ''), 'liste noire de sommes : refuse meme avec le bon horodatage')
PE_OUTIL.SHA256_BUILDS_ETRANGERS.discard(sha_octets(copie_ref))
verifie(PE_OUTIL.build_refuse(orig) is None and PE_OUTIL.build_refuse(open(ANCIEN, 'rb').read()) is None and PE_OUTIL.build_refuse(copie_ref) is None,
        'les deux originaux et une copie patchee passent la garde « build »')

# l'ancien exe reste accepte par le meme outil, avec SON profil
w = copie('ancien_cycle.exe', ANCIEN)
rc, out = outil('etat', '--exe', w)
verifie(rc == 0 and 'ancien build' in out and 'ORIGINAL' in out, 'l\'ancien exe est reconnu avec le profil ancien')
rc, out = outil('activer', '--exe', w, '--sauvegarde', ANCIEN)
verifie(rc == 0 and sha(w) == 'DAC8B1E66B03ACEA7DC64B02EB24F6A9F19C61FA242D7E8E68F0C5D8B7888B48', 'ancien exe + ascenseur_x2 : somme DAC8B1E6... (inchangee)')
ok, out = refuse_sans_rien_ecrire(w, 'activer', '--exe', w, '--sauvegarde', NEUF, '--module', 'temps_x2')
verifie(ok, 'ancien exe avec la sauvegarde du NOUVEL original : refuse')
rc, out = outil('retirer', '--exe', w)
verifie(rc == 0 and sha(w) == SHA_ANCIEN, 'ancien exe : retirer -> 1C9A01C3... exact')

# --------------------------------------------------------------------------
if JEU:
    titre('6. LECTURE SEULE du dossier du jeu (aucune ecriture) : le vrai exe est reconnu, les autres exe sont refuses')
    vrai = os.path.join(JEU, 'carrier_command.exe')
    avant = sha(vrai)
    rc, out = outil('etat', '--exe', vrai)
    verifie(rc == 0 and 'ORIGINAL' in out and avant == SHA_NEUF, 'le vrai carrier_command.exe de Steam : etat = ORIGINAL (461E1262...)')
    rc, out = outil('activer', '--exe', vrai, '--sauvegarde', NEUF, '--cest-le-vrai-jeu', '--a-blanc')
    verifie(rc == 3 and 'JAMAIS' in out and sha(vrai) == avant, 'le vrai exe de Steam : activer (meme a blanc, meme avec --cest-le-vrai-jeu) est REFUSE')
    rc, out = outil('retirer', '--exe', vrai, '--cest-le-vrai-jeu', '--a-blanc')
    verifie(rc == 3 and 'JAMAIS' in out and sha(vrai) == avant, 'le vrai exe de Steam : retirer refuse aussi')
    for nom in ('carrier_command_vr.exe', 'dedicated_server.exe'):
        p_ = os.path.join(JEU, nom)
        if os.path.isfile(p_):
            a_ = sha(p_)
            rc, out = outil('etat', '--exe', p_)
            verifie(rc == 3 and 'INCONNU' in out and sha(p_) == a_, '%s : etat = INCONNU (code 3)' % nom)
    rc, out = outil('etat', '--exe', os.path.join(JEU, 'carrier_command_ancien_8E7FCBB6.exe'))
    if os.path.isfile(os.path.join(JEU, 'carrier_command_ancien_8E7FCBB6.exe')):
        verifie(rc == 0 and 'PATCHE (ascenseur_x2, temps_x2' in out and 'ancien build' in out, 'carrier_command_ancien_8E7FCBB6.exe : profil ancien, PATCHE (ascenseur_x2, temps_x2)')
    verifie(sha(vrai) == avant, 'le vrai exe de Steam est reste identique (sha256 relu apres tous ces essais)')

print('\n%d verifications, %d echec(s)' % (total, echecs))
print('RESULTAT :', 'TOUT PASSE' if not echecs else 'ECHEC')
sys.exit(1 if echecs else 0)
