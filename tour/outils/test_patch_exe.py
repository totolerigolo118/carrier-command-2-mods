#!/usr/bin/env python3
"""Tests de patch_exe.py sur des COPIES (jamais sur le vrai jeu).

Usage : python test_patch_exe.py <copie_originale.exe> <dossier_de_travail_vide>
Le dossier de travail recoit des copies de 11 Mo ; il peut etre supprime ensuite.
"""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

ORIG, TRAVAIL = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
ICI = os.path.dirname(os.path.abspath(__file__))
OUTIL = os.path.join(ICI, 'patch_exe.py')
MOD = json.load(open(os.path.join(ICI, 'modules_exe', 'ascenseur_x2.json'), encoding='utf-8'))
os.makedirs(TRAVAIL, exist_ok=True)

echecs = 0
total = 0


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()


def verifie(cond, msg):
    global echecs, total
    total += 1
    if not cond:
        echecs += 1
        print('    ECHEC :', msg)


def outil(*args):
    r = subprocess.run([sys.executable, '-I', OUTIL, *args], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def copie(nom):
    p = os.path.join(TRAVAIL, nom)
    shutil.copyfile(ORIG, p)
    return p


def titre(t):
    print('\n== %s' % t)


SHA_O, SHA_P = MOD['sha256_origine'], MOD['sha256_patche']
verifie(sha(ORIG) == SHA_O, 'la copie fournie est bien l\'original')

# --------------------------------------------------------------------------
titre('1. cycle normal : etat, a blanc, activer, deja actif, retirer')
w = copie('cycle.exe')
rc, out = outil('etat', '--exe', w)
verifie(rc == 0 and 'ORIGINAL' in out, 'etat = ORIGINAL : ' + out.strip().splitlines()[2])
rc, out = outil('activer', '--exe', w)
verifie(rc != 0 and sha(w) == SHA_O, 'activer sans --sauvegarde est refuse, fichier intact')
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--a-blanc')
verifie(rc == 0 and sha(w) == SHA_O and 'A BLANC' in out, 'activer --a-blanc n\'ecrit rien')
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG)
verifie(rc == 0 and sha(w) == SHA_P and 'ACTIF' in out, 'activer : sha256 du fichier = sha256 patche attendu')
rc, out = outil('etat', '--exe', w)
verifie(rc == 0 and 'PATCHE' in out, 'etat = PATCHE')
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG)
verifie(rc == 0 and 'Deja actif' in out and sha(w) == SHA_P, 'activer une 2e fois : rien ne change')
patche_path = os.path.join(TRAVAIL, 'patche_garde.exe')
shutil.copyfile(w, patche_path)
rc, out = outil('retirer', '--exe', w)
verifie(rc == 0 and sha(w) == SHA_O, 'retirer : le fichier est redevenu EXACTEMENT l\'original (sha256)')
rc, out = outil('retirer', '--exe', w)
verifie(rc == 0 and 'Deja d\'origine' in out, 'retirer une 2e fois : rien ne change')

# --------------------------------------------------------------------------
titre('2. le fichier patche relu au desassembleur (capstone) : 31 sites')
data = open(patche_path, 'rb').read()
pe = struct.unpack_from('<I', data, 0x3C)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
optsz = struct.unpack_from('<H', data, pe + 20)[0]
opt = pe + 24
base = struct.unpack_from('<I', data, opt + 28)[0]
soh = struct.unpack_from('<I', data, opt + 60)[0]
secs = []
for i in range(nsec):
    o = opt + optsz + 40 * i
    vs, va, rs, rp = struct.unpack_from('<IIII', data, o + 8)
    secs.append((base + va, min(vs, rs), rp))


def off(va):
    if base <= va < base + soh:
        return va - base
    for sva, n, rp in secs:
        if sva <= va < sva + n:
            return rp + va - sva
    raise ValueError(hex(va))


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


VOULU = {'CP_T_ENERGY_SHARE': 0.8, 'CP_T_PLATFORM_STEP': 0.05, 'CP_T_PLATFORM_STEP_NEG': -0.05,
         'CP_T_CRANE_H': 1 / 3, 'CP_T_CRANE_H_NEG': -1 / 3, 'CP_T_CRANE_V': 1 / 15, 'CP_T_CRANE_V_NEG': -1 / 15,
         'CP_T_CRANE_ROT': 0.08, 'CP_T_CRANE_ROT_NEG': -0.08, 'CP_T_TAXI_ACCEL': 0.1, 'CP_T_TAXI_CAP': 5.0}
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
n_sites = 0
for c in MOD['changements']:
    if c['va'] < base + soh:
        continue    # le changement situe dans l'en-tete est la valeur ajoutee, pas une instruction
    if c['reglage'] == 'CP_T_ENERGY_SHARE':
        debut = c['va'] - 3
        ins = next(md.disasm(data[off(debut):off(debut) + 15], debut))
        ok = ins.mnemonic == 'mov' and struct.unpack('<f', ins.bytes[3:7])[0] == f32(0.8)
        verifie(ok, 'energie : %s %s = 0,8' % (ins.mnemonic, ins.op_str))
        n_sites += 1
        continue
    debut = c['va'] - 4
    ins = next(md.disasm(data[off(debut):off(debut) + 15], debut))
    mem = [op for op in ins.operands if op.type == X86_OP_MEM]
    cva = mem[0].mem.disp & 0xFFFFFFFF
    val = struct.unpack_from('<f', data, off(cva))[0]
    ok = (len(mem) == 1 and mem[0].mem.base == 0 and cva == c['constante_va'] and val == f32(VOULU[c['reglage']])
          and ins.size == 8)
    verifie(ok, '0x%08x %s %s lit %.9g (voulu %.9g)' % (debut, ins.mnemonic, ins.op_str, val, VOULU[c['reglage']]))
    n_sites += 1
verifie(n_sites == 31, '31 sites relus (trouve %d)' % n_sites)
cave = [c for c in MOD['changements'] if c['va'] < base + soh]
verifie(len(cave) == 1 and struct.unpack_from('<f', data, off(cave[0]['constante_va']))[0] == f32(-1 / 15),
        '-1/15 present dans le bourrage de l\'en-tete')

# --------------------------------------------------------------------------
titre('3. refus : fichier abime, etat melange, mauvaise sauvegarde, vrai jeu, options inconnues')
w = copie('abime.exe')
b = bytearray(open(w, 'rb').read())
c0 = MOD['changements'][5]
b[c0['offset']] ^= 0xFF
open(w, 'wb').write(b)
avant = sha(w)
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG)
verifie(rc != 0 and sha(w) == avant and 'INCONNU' in out, 'un site different de l\'original : activer refuse, fichier intact')

w = copie('melange.exe')
shutil.copyfile(patche_path, w)
b = bytearray(open(w, 'rb').read())
c1 = MOD['changements'][3]
b[c1['offset']:c1['offset'] + 4] = bytes.fromhex(c1['avant'])
open(w, 'wb').write(b)
avant = sha(w)
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG)
verifie(rc != 0 and sha(w) == avant and 'MELANGE' in out, 'etat melange : activer refuse')
rc, out = outil('retirer', '--exe', w)
verifie(rc != 0 and sha(w) == avant, 'etat melange : retirer sans sauvegarde refuse')
rc, out = outil('retirer', '--exe', w, '--sauvegarde', ORIG, '--restaurer-tout-l-exe')
verifie(rc == 0 and sha(w) == SHA_O, 'etat melange : retirer avec la sauvegarde ET --restaurer-tout-l-exe remet l\'original exact')

w = copie('mauvaise_sauv.exe')
rc, out = outil('activer', '--exe', w, '--sauvegarde', patche_path)
verifie(rc != 0 and sha(w) == SHA_O, 'sauvegarde qui n\'est pas l\'original : refuse')
rc, out = outil('activer', '--exe', w, '--sauvegarde', w)
verifie(rc != 0 and sha(w) == SHA_O, 'sauvegarde = le fichier lui-meme : refuse')
rc, out = outil('activer', '--exe', w, '--sauvegarde', os.path.join(TRAVAIL, 'nexiste_pas.exe'))
verifie(rc != 0 and sha(w) == SHA_O, 'sauvegarde absente : refuse')

faux = os.path.join(TRAVAIL, 'steamapps', 'common', 'Carrier Command 2')
os.makedirs(faux, exist_ok=True)
w = os.path.join(faux, 'carrier_command.exe')
shutil.copyfile(ORIG, w)
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG)
verifie(rc != 0 and sha(w) == SHA_O and 'VRAI jeu' in out, 'chemin « steamapps » sans --cest-le-vrai-jeu : refuse')
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--cest-le-vrai-jeu')
verifie(rc == 0 and sha(w) == SHA_P, 'chemin « steamapps » avec la confirmation (jeu ferme) : active')
rc, out = outil('retirer', '--exe', w, '--cest-le-vrai-jeu')
verifie(rc == 0 and sha(w) == SHA_O, 'puis retire : original exact')

w = copie('options.exe')
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--option-inconnue')
verifie(rc == 2 and sha(w) == SHA_O, 'option inconnue : refus, fichier intact')
rc, out = outil('activer', '--exe', w, '--sauv', ORIG)
verifie(rc == 2 and sha(w) == SHA_O, 'option abregee (--sauv) : refus, fichier intact')
rc, out = outil('activer', '--sauvegarde', ORIG)
verifie(rc == 2, 'sans --exe : refus (aucun chemin par defaut)')

# --------------------------------------------------------------------------
titre('4. second module temps_x2, combinaison des deux modules, verification globale')
T2 = json.load(open(os.path.join(ICI, 'modules_exe', 'temps_x2.json'), encoding='utf-8'))
w = copie('combo.exe')
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', 'temps_x2')
verifie(rc == 0 and sha(w) == T2['sha256_patche'] and 'ACTIF' in out, 'temps_x2 seul : sha256 = celui attendu')
d2 = open(w, 'rb').read()
ins = next(md.disasm(d2[off(0x835cc5):off(0x835cc5) + 15], 0x835cc5))
verifie(ins.mnemonic == 'mov' and ins.op_str == 'dword ptr [edi + 0x140], 0x40000000',
        'relu au desassembleur : %s %s (facteur de vitesse = 2.0)' % (ins.mnemonic, ins.op_str))
rc, out = outil('etat', '--exe', w)
verifie(rc == 0 and 'temps_x2' in out and 'PATCHE' in out and 'ascenseur_x2  : ORIGINAL' in out, 'etat : temps_x2 patche, ascenseur_x2 d\'origine')
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG)
attendu = bytearray(open(ORIG, 'rb').read())
for m in (MOD, T2):
    for c in m['changements']:
        attendu[c['offset']:c['offset'] + 4] = bytes.fromhex(c['apres'])
verifie(rc == 0 and sha(w) == hashlib.sha256(bytes(attendu)).hexdigest().upper(),
        'les deux modules : sha256 = original + les deux jeux de changements (calcul independant)')
rc, out = outil('retirer', '--exe', w, '--module', 'temps_x2')
verifie(rc == 0 and sha(w) == SHA_P, 'retirer temps_x2 : il reste EXACTEMENT ascenseur_x2 seul (sha256)')
rc, out = outil('retirer', '--exe', w)
verifie(rc == 0 and sha(w) == SHA_O, 'retirer ascenseur_x2 : original exact')
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', 'nexiste_pas')
verifie(rc != 0 and sha(w) == SHA_O, 'module inconnu : refus')
w2 = copie('autre_octet.exe')
b = bytearray(open(w2, 'rb').read())
b[0x2000] ^= 0xFF                                   # un octet qui n'appartient a aucun module
open(w2, 'wb').write(b)
avant2 = sha(w2)
rc, out = outil('activer', '--exe', w2, '--sauvegarde', ORIG, '--module', 'temps_x2')
verifie(rc != 0 and sha(w2) == avant2 and 'INCONNU' in out, 'un octet modifie hors des modules : activer refuse (autre version / fichier abime)')
rc, out = outil('retirer', '--exe', w2)
verifie(rc != 0 and sha(w2) == avant2, 'idem : retirer sans sauvegarde refuse')
rc, out = outil('etat', '--exe', w2)
verifie(rc == 3 and 'INCONNU' in out, 'idem : etat = INCONNU, code de sortie 3')

# --------------------------------------------------------------------------
titre('5. modules atterrissage_creneau / atterrissage_cercle : octets recalcules a part, relecture, combinaisons, retour')
CRE = json.load(open(os.path.join(ICI, 'modules_exe', 'atterrissage_creneau.json'), encoding='utf-8'))
CER = json.load(open(os.path.join(ICI, 'modules_exe', 'atterrissage_cercle.json'), encoding='utf-8'))
MODS = {'ascenseur_x2': MOD, 'temps_x2': T2, 'atterrissage_creneau': CRE, 'atterrissage_cercle': CER}
BLOC_PISTE, CST_M1800 = 0x00701A2A, 0x00DB7E54


def sha_octets(b):
    return hashlib.sha256(bytes(b)).hexdigest().upper()


def rel32(fin_instruction, cible):
    return struct.pack('<i', cible - fin_instruction)


# octets attendus APRES, calcules ici a partir du sens de la retouche, sans lire les JSON
VOULU_AT = {
    0x007019FC: rel32(0x007019FA + 6, BLOC_PISTE),      # S1 : jbe (6 octets) -> test de la piste
    0x00701D35: rel32(0x00701D33 + 6, BLOC_PISTE),      # S2 : jbe (6 octets)
    0x00701D4F: rel32(0x00701D4E + 5, BLOC_PISTE),      # S3 : jmp (5 octets)
    0x0070137F: struct.pack('<f', -1800.0),             # C1 : centre du virage avant, z
    0x00701D5E: struct.pack('<I', CST_M1800),           # C2 : adresse de la constante -1800.0
    0x00701F52: struct.pack('<I', CST_M1800),           # C3
}
for nom_m in ('atterrissage_creneau', 'atterrissage_cercle'):
    m = MODS[nom_m]
    verifie(len(m['changements']) == 3 and m['nb_changements'] == 3 and m['sha256_origine'] == SHA_O,
            '%s : 3 changements, meme sha256 d\'origine que les autres modules' % nom_m)
    for c in m['changements']:
        verifie(bytes.fromhex(c['apres']) == VOULU_AT.get(c['va']) and c['offset'] == off(c['va']),
                '%s : champ 0x%08x -> %s (recalcule a part) et decalage fichier correct' % (nom_m, c['va'], c['apres']))
orig_octets = open(ORIG, 'rb').read()
for nom_m in ('atterrissage_creneau', 'atterrissage_cercle'):
    for c in MODS[nom_m]['changements']:
        verifie(orig_octets[c['offset']:c['offset'] + 4].hex() == c['avant'], '%s : octets d\'origine 0x%08x relus dans l\'original' % (nom_m, c['va']))

plages = sorted((c['offset'], c['offset'] + 4, n) for n, m in MODS.items() for c in m['changements'])
verifie(all(plages[i][1] <= plages[i + 1][0] for i in range(len(plages) - 1)),
        'aucun chevauchement entre les %d champs des 4 modules' % len(plages))


def attendu_sha(noms):
    b = bytearray(orig_octets)
    for n in noms:
        for c in MODS[n]['changements']:
            b[c['offset']:c['offset'] + 4] = bytes.fromhex(c['apres'])
    return sha_octets(b)


ACTUEL = ['ascenseur_x2', 'temps_x2']
verifie(attendu_sha(ACTUEL) == '8E7FCBB6CE27BD3D8FEB02BF7F3DBBA646CCE6D4944360570F082972E8DFE8BE',
        'ascenseur_x2 + temps_x2 recalcules ici = la somme de l\'executable actuel (8E7FCBB6...)')
verifie(attendu_sha(ACTUEL + ['atterrissage_creneau']) == 'C7851BBF06C2BBD681B675E4E8C187D15A7566494058EEA86244761202FE72EB',
        'actuel + creneau = la somme annoncee par l\'etude (C7851BBF...)')
verifie(attendu_sha(ACTUEL + ['atterrissage_cercle']) == '80E9D871A342FA7D244453BE4062A93653C30838B99ED84471026C2FAC7098DA',
        'actuel + cercle = la somme annoncee par l\'etude (80E9D871...)')
verifie(attendu_sha(ACTUEL + ['atterrissage_creneau', 'atterrissage_cercle']) == '563994278CB0B3ED1504C99B43087B3CEFABA98627AA68C84FBB3B797860202C',
        'actuel + creneau + cercle = la somme annoncee par l\'etude (56399427...)')
for nom_m in ('atterrissage_creneau', 'atterrissage_cercle'):
    verifie(attendu_sha([nom_m]) == MODS[nom_m]['sha256_patche'], '%s : sha256_patche du JSON = somme recalculee' % nom_m)

# cycle sur copie : chaque module seul, puis les deux
for nom_m in ('atterrissage_creneau', 'atterrissage_cercle'):
    w = copie('cycle_%s.exe' % nom_m)
    rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', nom_m, '--a-blanc')
    verifie(rc == 0 and sha(w) == SHA_O and 'A BLANC' in out and '3 changement' in out, '%s : --a-blanc n\'ecrit rien' % nom_m)
    rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', nom_m)
    verifie(rc == 0 and sha(w) == MODS[nom_m]['sha256_patche'] and 'ACTIF' in out, '%s : activer -> somme attendue' % nom_m)
    rc, out = outil('etat', '--exe', w)
    verifie(rc == 0 and 'PATCHE (%s' % nom_m in out, '%s : etat = PATCHE' % nom_m)
    rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', nom_m)
    verifie(rc == 0 and 'Deja actif' in out and sha(w) == MODS[nom_m]['sha256_patche'], '%s : 2e activation sans effet' % nom_m)
    rc, out = outil('retirer', '--exe', w, '--module', nom_m)
    verifie(rc == 0 and sha(w) == SHA_O and 'EXACTEMENT' in out, '%s : retirer -> original exact' % nom_m)

# relecture au desassembleur des 4 modules actifs ensemble
tout = copie('tous_les_modules.exe')
for n in MODS:
    outil('activer', '--exe', tout, '--sauvegarde', ORIG, '--module', n)
d_tout = open(tout, 'rb').read()
verifie(sha_octets(d_tout) == attendu_sha(list(MODS)), 'les 4 modules actifs : somme = original + les 4 jeux de changements (calcul a part)')
champs_ok = set()
for _, m in MODS.items():
    for c in m['changements']:
        champs_ok.update(range(c['offset'], c['offset'] + 4))
diff = [i for i in range(len(orig_octets)) if orig_octets[i] != d_tout[i]]
verifie(len(d_tout) == len(orig_octets) and set(diff) <= champs_ok,
        'aucun octet modifie hors des champs listes (%d octets differents, %d permis)' % (len(diff), len(champs_ok)))


def balayage(donnees):
    o = off(0x006FC730)
    return {i.address: i for i in md.disasm(bytes(donnees[o:o + 0x00701FA8 - 0x006FC730]), 0x006FC730)}


f_o, f_p = balayage(orig_octets), balayage(d_tout)
verifie(sorted(f_o) == sorted(f_p) and len(f_o) > 4000,
        'frontieres des %d instructions de toute la fonction du circuit inchangees' % len(f_o))
verifie(BLOC_PISTE in f_p and bytes(f_p[BLOC_PISTE].bytes) == bytes.fromhex('833f01'), 'le test de la piste 0x00701a2a est bien `cmp dword ptr [edi], 1`')
for va_i in (0x007019FA, 0x00701D33, 0x00701D4E):
    n = f_p[va_i]
    verifie(n.mnemonic == f_o[va_i].mnemonic and n.size == f_o[va_i].size and (n.operands[0].imm & 0xFFFFFFFF) == BLOC_PISTE,
            '0x%08x : %s %s (saute au test de la piste)' % (va_i, n.mnemonic, n.op_str))
n = f_p[0x00701379]
verifie(n.mnemonic == 'mov' and n.size == 10 and struct.unpack('<f', struct.pack('<I', n.operands[1].imm & 0xFFFFFFFF))[0] == -1800.0
        and n.operands[0].mem.disp & 0xFFFFFFFF == 0xFFFFFD5C, '0x00701379 : %s %s (centre avant z = -1800)' % (n.mnemonic, n.op_str))
verifie(struct.unpack_from('<f', d_tout, off(CST_M1800))[0] == -1800.0, 'la constante lue en 0x00db7e54 vaut -1800.0 (non modifiee)')
for va_i in (0x00701D5B, 0x00701F4E):
    n = f_p[va_i]
    mem = [o for o in n.operands if o.type == X86_OP_MEM][0]
    verifie(n.size == f_o[va_i].size and (mem.mem.disp & 0xFFFFFFFF) == CST_M1800, '0x%08x : %s %s (lit -1800.0)' % (va_i, n.mnemonic, n.op_str))
verifie(struct.unpack_from('<f', d_tout, off(0x00DB7A70))[0] == 600.0 and d_tout[off(0x00DB7A70):off(0x00DB7A70) + 4] == orig_octets[off(0x00DB7A70):off(0x00DB7A70) + 4],
        'la constante partagee 600.0 (0x00db7a70) n\'est pas modifiee')

# les 16 combinaisons : chaque etape = somme calculee a part ; puis retour dans l'ordre inverse, puis dans l'ordre direct
NOMS_ORDRE = list(MODS)
n_combos = 0
for masque in range(1, 16):
    choisis = [n for i, n in enumerate(NOMS_ORDRE) if masque >> i & 1]
    w = copie('combo_%d.exe' % masque)
    bon = True
    for k, n in enumerate(choisis):
        rc, _ = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', n)
        bon = bon and rc == 0 and sha(w) == attendu_sha(choisis[:k + 1])
    verifie(bon, 'combinaison %s : somme juste apres chaque activation' % '+'.join(choisis))
    ordre_retour = list(reversed(choisis)) if masque % 2 else list(choisis)         # alterne : ordre inverse / ordre direct
    restant = list(choisis)
    bon = True
    for n in ordre_retour:
        rc, _ = outil('retirer', '--exe', w, '--module', n)
        restant.remove(n)
        bon = bon and rc == 0 and sha(w) == (attendu_sha(restant) if restant else SHA_O)
    verifie(bon and sha(w) == SHA_O, 'combinaison %s : retirer un a un (%s) redonne chaque etat puis l\'original exact' % (
        '+'.join(choisis), 'ordre inverse' if masque % 2 else 'ordre direct'))
    n_combos += 1
verifie(n_combos == 15, '15 combinaisons non vides des 4 modules testees')

# depuis l'executable ACTUEL (ascenseur_x2 + temps_x2) : poser puis retirer chaque module d'atterrissage
actuel = copie('actuel.exe')
for n in ACTUEL:
    outil('activer', '--exe', actuel, '--sauvegarde', ORIG, '--module', n)
verifie(sha(actuel) == '8E7FCBB6CE27BD3D8FEB02BF7F3DBBA646CCE6D4944360570F082972E8DFE8BE', 'exe actuel reconstitue sur copie = 8E7FCBB6...')
sauv_actuel = os.path.join(TRAVAIL, 'actuel_garde.exe')
shutil.copyfile(actuel, sauv_actuel)
rc, out = outil('activer', '--exe', actuel, '--sauvegarde', ORIG, '--module', 'atterrissage_cercle')
verifie(rc == 0 and sha(actuel) == '80E9D871A342FA7D244453BE4062A93653C30838B99ED84471026C2FAC7098DA', 'actuel + cercle : 80E9D871...')
rc, out = outil('retirer', '--exe', actuel, '--module', 'atterrissage_cercle')
verifie(rc == 0 and sha(actuel) == '8E7FCBB6CE27BD3D8FEB02BF7F3DBBA646CCE6D4944360570F082972E8DFE8BE', 'cercle retire : retour exact a 8E7FCBB6...')
rc, out = outil('activer', '--exe', actuel, '--sauvegarde', ORIG, '--module', 'atterrissage_creneau')
verifie(rc == 0 and sha(actuel) == 'C7851BBF06C2BBD681B675E4E8C187D15A7566494058EEA86244761202FE72EB', 'actuel + creneau : C7851BBF...')
rc, out = outil('activer', '--exe', actuel, '--sauvegarde', ORIG, '--module', 'atterrissage_cercle')
verifie(rc == 0 and sha(actuel) == '563994278CB0B3ED1504C99B43087B3CEFABA98627AA68C84FBB3B797860202C', 'actuel + creneau + cercle : 56399427...')
rc, out = outil('retirer', '--exe', actuel, '--module', 'atterrissage_creneau')
rc2, out2 = outil('retirer', '--exe', actuel, '--module', 'atterrissage_cercle')
verifie(rc == 0 and rc2 == 0 and sha(actuel) == '8E7FCBB6CE27BD3D8FEB02BF7F3DBBA646CCE6D4944360570F082972E8DFE8BE',
        'les deux retires : retour exact a 8E7FCBB6...')

# etat melange (module a moitie pose) et refus
for nom_m, indice in (('atterrissage_cercle', 0), ('atterrissage_creneau', 2)):
    w = copie('melange_%s.exe' % nom_m)
    outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', nom_m)
    b = bytearray(open(w, 'rb').read())
    c = MODS[nom_m]['changements'][indice]
    b[c['offset']:c['offset'] + 4] = bytes.fromhex(c['avant'])
    open(w, 'wb').write(b)
    avant = sha(w)
    rc, out = outil('etat', '--exe', w)
    verifie(rc == 3 and 'MELANGE' in out and nom_m in out, '%s : 2 champs sur 3 -> etat MELANGE, code 3' % nom_m)
    rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', nom_m)
    verifie(rc != 0 and sha(w) == avant and 'MELANGE' in out, '%s : activer refuse sur un etat melange, fichier intact' % nom_m)
    rc, out = outil('retirer', '--exe', w, '--module', nom_m)
    verifie(rc != 0 and sha(w) == avant, '%s : retirer sans sauvegarde refuse sur un etat melange' % nom_m)
    rc, out = outil('retirer', '--exe', w, '--module', nom_m, '--sauvegarde', ORIG, '--restaurer-tout-l-exe')
    verifie(rc == 0 and sha(w) == SHA_O, '%s : retirer avec la sauvegarde ET --restaurer-tout-l-exe remet l\'original exact' % nom_m)
w = copie('autre_octet_atterrissage.exe')
b = bytearray(open(w, 'rb').read())
b[0x2000] ^= 0xFF
open(w, 'wb').write(b)
avant = sha(w)
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', 'atterrissage_cercle')
verifie(rc != 0 and sha(w) == avant and 'INCONNU' in out, 'un octet modifie hors des modules : le cercle refuse de se poser')

# chemin « steamapps » (vrai jeu) : confirmation obligatoire, aussi pour les nouveaux modules
faux = os.path.join(TRAVAIL, 'steamapps2', 'common', 'Carrier Command 2')
os.makedirs(faux, exist_ok=True)
w = os.path.join(faux, 'carrier_command.exe')
shutil.copyfile(ORIG, w)
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', 'atterrissage_cercle')
verifie(rc != 0 and sha(w) == SHA_O and 'VRAI jeu' in out, 'cercle sur un chemin « steamapps » sans --cest-le-vrai-jeu : refuse')
rc, out = outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', 'atterrissage_cercle', '--cest-le-vrai-jeu')
verifie(rc == 0 and sha(w) == MODS['atterrissage_cercle']['sha256_patche'], 'cercle sur chemin « steamapps » avec confirmation (jeu ferme) : pose')
rc, out = outil('retirer', '--exe', w, '--module', 'atterrissage_cercle', '--cest-le-vrai-jeu')
verifie(rc == 0 and sha(w) == SHA_O, 'puis retire : original exact')

# --------------------------------------------------------------------------
titre('6. securite : jamais d\'ecrasement du fichier entier sur un exe INCONNU ou d\'un autre build ; drapeau explicite pour la restauration')
VRAI = os.path.join(TRAVAIL, 'steamapps3', 'common', 'Carrier Command 2')   # faux « vrai jeu » : un dossier temporaire
os.makedirs(VRAI, exist_ok=True)


def exe_modifie(nom, modif, dossier=TRAVAIL):
    """Copie de l'original dont les octets sont changes par modif(bytearray) ; renvoie le chemin."""
    p = os.path.join(dossier, nom)
    b = bytearray(open(ORIG, 'rb').read())
    modif(b)
    open(p, 'wb').write(b)
    return p


def met_horodatage(b, valeur):
    struct.pack_into('<I', b, struct.unpack_from('<I', b, 0x3C)[0] + 8, valeur)


def refuse_sans_rien_ecrire(w, *args, mots=()):
    avant = sha(w)
    rc, out = outil(*args)
    return rc == 3 and sha(w) == avant and not os.path.exists(w + '.cc2_tmp') and all(m in out for m in mots), out


# 6a. la commande « piegee » de l'etude roulage retour, sur un exe INCONNU, chemin « steamapps », toutes les confirmations
w = exe_modifie('inconnu_octet.exe', lambda b: b.__setitem__(0x2000, b[0x2000] ^ 0xFF), VRAI)
w = os.path.join(VRAI, 'inconnu_octet.exe')
for args, nom in (
        (('retirer', '--exe', w, '--sauvegarde', ORIG, '--cest-le-vrai-jeu'), 'la commande piegee (retirer --sauvegarde --cest-le-vrai-jeu)'),
        (('retirer', '--exe', w, '--module', 'temps_x2', '--sauvegarde', ORIG, '--cest-le-vrai-jeu'), 'idem avec --module'),
        (('retirer', '--exe', w, '--sauvegarde', ORIG, '--cest-le-vrai-jeu', '--restaurer-tout-l-exe'), 'idem avec --restaurer-tout-l-exe'),
        (('retirer', '--exe', w, '--sauvegarde', ORIG, '--cest-le-vrai-jeu', '--restaurer-tout-l-exe', '--a-blanc'), 'idem a blanc'),
        (('activer', '--exe', w, '--sauvegarde', ORIG, '--cest-le-vrai-jeu'), 'activer avec toutes les confirmations')):
    ok, out = refuse_sans_rien_ecrire(w, *args, mots=('INCONNU', 'demander au moddeur'))
    verifie(ok, 'exe INCONNU : %s -> refus (code 3), octets inchanges, message « demander au moddeur »' % nom)
# un site de module different (ni l'original ni le patch) : meme refus
w = exe_modifie('inconnu_site.exe', lambda b: b.__setitem__(MOD['changements'][5]['offset'], b[MOD['changements'][5]['offset']] ^ 0xFF), VRAI)
ok, out = refuse_sans_rien_ecrire(w, 'retirer', '--exe', w, '--sauvegarde', ORIG, '--cest-le-vrai-jeu', '--restaurer-tout-l-exe', mots=('INCONNU',))
verifie(ok, 'un site de module abime (etat INCONNU) : retirer --sauvegarde --restaurer-tout-l-exe refuse, octets inchanges')

# 6b. autre build : horodatage de compilation du build de Steam du 28/10 (0x6ae228f3), un autre horodatage, un fichier qui n'est pas un PE
w = exe_modifie('build_steam.exe', lambda b: met_horodatage(b, 0x6ae228f3), VRAI)
for args, nom in (
        (('activer', '--exe', w, '--sauvegarde', ORIG, '--cest-le-vrai-jeu'), 'activer'),
        (('retirer', '--exe', w, '--sauvegarde', ORIG, '--cest-le-vrai-jeu', '--restaurer-tout-l-exe'), 'retirer avec toutes les confirmations'),
        (('retirer', '--exe', w, '--module', 'temps_x2', '--cest-le-vrai-jeu'), 'retirer un module')):
    ok, out = refuse_sans_rien_ecrire(w, *args, mots=('BUILD DE STEAM', 'demander au moddeur'))
    verifie(ok, 'exe au horodatage du build Steam (0x6ae228f3) : %s -> refus, octets inchanges' % nom)
w = exe_modifie('autre_horodatage.exe', lambda b: met_horodatage(b, 0x12345678))
ok, out = refuse_sans_rien_ecrire(w, 'retirer', '--exe', w, '--sauvegarde', ORIG, '--restaurer-tout-l-exe', mots=('horodatage de compilation', 'demander au moddeur'))
verifie(ok, 'exe d\'un autre horodatage (0x12345678) : retirer refuse, octets inchanges')
ok, out = refuse_sans_rien_ecrire(w, 'activer', '--exe', w, '--sauvegarde', ORIG, mots=('horodatage de compilation',))
verifie(ok, 'exe d\'un autre horodatage : activer refuse, octets inchanges')
w = os.path.join(TRAVAIL, 'pas_un_pe.exe')
open(w, 'wb').write(b'MZ' + bytes(100))
ok, out = refuse_sans_rien_ecrire(w, 'retirer', '--exe', w, '--sauvegarde', ORIG, '--restaurer-tout-l-exe', mots=('illisible',))
verifie(ok, 'fichier qui n\'est pas un PE lisible : retirer refuse, octets inchanges')

# 6c. la somme du build Steam est bien connue de l'outil, l'ancien build et nos copies patchees passent la garde (en memoire)
import importlib.util
spec = importlib.util.spec_from_file_location('patch_exe_sous_test', OUTIL)
PE_OUTIL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PE_OUTIL)
# [30/10 : le build Steam du 28/10 n'est plus « etranger » : il a son PROFIL (voir test_patch_exe_nouveau.py). Les refus
#  d'un exe aux octets inconnus, d'un autre horodatage, d'un melange de profils restent testes ci-dessus et la-bas.]
verifie(any(p['sha256_origine'] == '461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A'
            and p['horodatage'] == 0x6ae228f3 and not p['ecriture_dans_steamapps'] for p in PE_OUTIL.PROFILS)
        and not PE_OUTIL.SHA256_BUILDS_ETRANGERS,
        'le build Steam du 28/10 (461E1262...) a son profil (somme epinglee, horodatage 0x6ae228f3, jamais d\'ecriture sous steamapps)')
verifie(PE_OUTIL.HORODATAGE_PE_ATTENDU == 0x6a36c177 and PE_OUTIL.HORODATAGE_PE_BUILD_STEAM_28_10 == 0x6ae228f3, 'horodatages de reference de l\'outil')
verifie(PE_OUTIL.build_refuse(open(ORIG, 'rb').read()) is None and PE_OUTIL.build_refuse(open(patche_path, 'rb').read()) is None,
        'l\'original et la copie patchee passent la garde « build »')
copie_gardee = open(patche_path, 'rb').read()
PE_OUTIL.SHA256_BUILDS_ETRANGERS.add(sha_octets(copie_gardee))
verifie('BUILD ETRANGER' in (PE_OUTIL.build_refuse(copie_gardee) or ''), 'un fichier dont la somme est dans la liste est refuse meme avec le bon horodatage')
PE_OUTIL.SHA256_BUILDS_ETRANGERS.discard(sha_octets(copie_gardee))

# 6d. etat MELANGE connu : retour par la copie seulement avec le drapeau explicite + la bonne sauvegarde
w = os.path.join(TRAVAIL, 'melange_drapeau.exe')
shutil.copyfile(patche_path, w)
b = bytearray(open(w, 'rb').read())
c1 = MOD['changements'][3]
b[c1['offset']:c1['offset'] + 4] = bytes.fromhex(c1['avant'])
open(w, 'wb').write(b)
ok, out = refuse_sans_rien_ecrire(w, 'retirer', '--exe', w, '--sauvegarde', ORIG, mots=('MELANGE', '--restaurer-tout-l-exe'))
verifie(ok, 'etat melange : --sauvegarde seule ne remplace plus le fichier (le drapeau explicite est exige), octets inchanges')
ok, out = refuse_sans_rien_ecrire(w, 'retirer', '--exe', w, '--restaurer-tout-l-exe')
verifie(ok, 'etat melange : --restaurer-tout-l-exe sans --sauvegarde refuse')
ok, out = refuse_sans_rien_ecrire(w, 'retirer', '--exe', w, '--sauvegarde', patche_path, '--restaurer-tout-l-exe')
verifie(ok, 'etat melange : sauvegarde qui n\'est pas l\'original refuse')
ok, out = refuse_sans_rien_ecrire(w, 'retirer', '--exe', w, '--sauvegarde', w, '--restaurer-tout-l-exe')
verifie(ok, 'etat melange : sauvegarde = le fichier lui-meme refuse')
avant = sha(w)
rc, out = outil('retirer', '--exe', w, '--sauvegarde', ORIG, '--restaurer-tout-l-exe', '--a-blanc')
verifie(rc == 0 and sha(w) == avant and 'A BLANC' in out, 'etat melange : restauration a blanc, rien n\'est ecrit')
rc, out = outil('retirer', '--exe', w, '--sauvegarde', ORIG, '--restaurer-tout-l-exe')
verifie(rc == 0 and sha(w) == SHA_O, 'etat melange : avec le drapeau et la bonne sauvegarde, l\'original exact revient (comportement d\'avant)')

# 6e. le drapeau ne remplace pas tout hors etat melange, et n'a de sens que pour retirer
w = copie('drapeau_hors_melange.exe')
outil('activer', '--exe', w, '--sauvegarde', ORIG)
outil('activer', '--exe', w, '--sauvegarde', ORIG, '--module', 'temps_x2')
rc, out = outil('retirer', '--exe', w, '--module', 'temps_x2', '--sauvegarde', ORIG, '--restaurer-tout-l-exe')
verifie(rc == 0 and sha(w) == SHA_P, 'etat patche : --restaurer-tout-l-exe ne remplace pas tout, seul temps_x2 est retire (ascenseur_x2 reste)')
avant = sha(w)
for cmd in ('activer', 'etat'):
    rc, out = outil(cmd, '--exe', w, '--sauvegarde', ORIG, '--restaurer-tout-l-exe')
    verifie(rc != 0 and sha(w) == avant, '--restaurer-tout-l-exe avec la commande %s : refuse, octets inchanges' % cmd)

print('\n%d verifications, %d echec(s)' % (total, echecs))
print('RESULTAT :', 'TOUT PASSE' if not echecs else 'ECHEC')
sys.exit(1 if echecs else 0)
