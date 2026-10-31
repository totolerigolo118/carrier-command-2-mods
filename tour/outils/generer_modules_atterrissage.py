#!/usr/bin/env python3
"""Genere les deux modules `atterrissage_creneau` et `atterrissage_cercle` pour patch_exe.py (Windows 1.5.18, 32 bits).

Port du patch « atterrissage » du Mac (voir tour/etudes_circuit_atterrissage/ETUDE.md) :
  atterrissage_creneau : la piste peut etre donnee a l'avion pendant TOUT le virage arriere, pas seulement a l'instant
                         du passage au portillon (3 sauts redirigés vers le test de la piste, 0x00701a2a) ;
  atterrissage_cercle  : le circuit d'attente devient un CERCLE au lieu d'un ovale (centre du virage avant z 600 -> -1800,
                         et les deux seuils de fin de ligne 600 -> -1800, lus a la constante -1800.0 deja presente).
Chaque module est tout ou rien (3 changements de 4 octets) ; les deux sont independants (aucun octet commun).
Aucune constante partagee n'est modifiee : on redirige des lectures vers -1800.0 (0x00db7e54, section .rdata).

Tout est relu dans le fichier (les sites sont definis et decodes par tour/etudes_circuit_atterrissage/verifier_sites.py) ;
rien n'est ecrit si un controle echoue.

Usage : python -I generer_modules_atterrissage.py <exe_origine> <dossier_des_json> <rapport.md>
        (l'exe donne doit etre l'ORIGINAL 1C9A01C3...341026 ; il n'est jamais modifie)
"""
import hashlib
import importlib.util
import json
import os
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
SHA_ORIGINE = '1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026'

spec = importlib.util.spec_from_file_location(
    'verifier_sites', os.path.join(ICI, '..', 'etudes_circuit_atterrissage', 'verifier_sites.py'))
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)

MODULES = [
    ('atterrissage_creneau',
     "creneau de piste elargi : la piste peut etre donnee a l'avion pendant tout le virage arriere (3 sauts)",
     ['S1', 'S2', 'S3']),
    ('atterrissage_cercle',
     "circuit d'attente des avions en CERCLE au lieu d'un ovale (1 valeur ecrite dans le code, 2 lectures de constante)",
     ['C1', 'C2', 'C3']),
]
ROLES = {
    'S1': "etat 1 du circuit (1re moitie du virage arriere) : `jbe 0x701b04` (sortie) -> `jbe 0x701a2a` (test de la piste)",
    'S2': "etat 2 (2e moitie du virage arriere) : `jbe 0x701b04` (sortie) -> `jbe 0x701a2a` (test de la piste)",
    'S3': "passage etat 2 -> 3 : `jmp 0x701b04` (sortie) -> `jmp 0x701a2a` (test de la piste)",
    'C1': "centre du virage AVANT, z : `mov dword ptr [ebp-0x2a4], 600.0` -> `-1800.0` (meme cercle que le virage arriere)",
    'C2': "etat 3 : seuil de fin de la ligne droite `comiss xmm0,[600.0]` -> `[-1800.0]`",
    'C3': "etat 5 : seuil de fin du virage avant `movss xmm0,[600.0]` -> `[-1800.0]`",
}
REGLAGES = {'S1': 'LANDING_GATE_STATE1', 'S2': 'LANDING_GATE_STATE2', 'S3': 'LANDING_GATE_STATE2_TO_3',
            'C1': 'LANDING_CIRCLE_FRONT_CENTER_Z', 'C2': 'LANDING_CIRCLE_STATE3_END', 'C3': 'LANDING_CIRCLE_STATE5_END'}


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    exe, dossier, rapport = sys.argv[1:4]
    data = open(exe, 'rb').read()
    sha_o = hashlib.sha256(data).hexdigest().upper()
    erreurs = []
    if sha_o != SHA_ORIGINE:
        sys.exit("REFUS : l'exe donne n'est pas l'original 1C9A01C3...341026 (sha256 %s)" % sha_o)
    img = vs.Image(exe)
    base = img.base
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    ts = struct.unpack_from('<I', data, pe + 8)[0]
    soi = struct.unpack_from('<I', data, pe + 24 + 56)[0]

    avant_fonction = img.fonction()
    if vs.BLOC_PISTE not in avant_fonction or bytes(avant_fonction[vs.BLOC_PISTE].bytes) != bytes.fromhex('833f01'):
        erreurs.append("0x%08x n'est pas `cmp dword ptr [edi], 1`" % vs.BLOC_PISTE)
    if vs.SORTIE not in avant_fonction:
        erreurs.append('la sortie commune 0x%08x n\'est pas un debut d\'instruction' % vs.SORTIE)
    s = img.section(vs.CST_M1800)
    if s is None or (s[4] & 0x80000000):
        erreurs.append('-1800.0 n\'est pas dans une section sans droit d\'ecriture')
    if img.flt(vs.CST_M1800) != -1800.0 or img.flt(vs.CST_600) != 600.0:
        erreurs.append('les constantes -1800.0 / 600.0 ne valent pas ce qui est attendu')

    sites = {site[0]: site for site in vs.SITES}
    calcul = {}
    patch_total = bytearray(data)
    deja = []
    for nom, _, ids in MODULES:
        for sid in ids:
            champ, avant, apres, ins = vs.calculer(img, sites[sid])
            reloc_attendue = sites[sid][6] == 'abs32'
            if (champ in img.relocs) != reloc_attendue:
                erreurs.append('%s : relocation inattendue (%s)' % (sid, 'attendue' if reloc_attendue else 'absente attendue'))
            if img.octets(champ, 4) != avant or len(avant) != 4:
                erreurs.append('%s : octets d\'origine differents ou longueur != 4' % sid)
            for a, b, autre in deja:
                if champ < b and a < champ + 4:
                    erreurs.append('%s chevauche %s' % (sid, autre))
            deja.append((champ, champ + 4, sid))
            calcul[sid] = (champ, avant, apres, ins)
            o = img.off(champ)
            patch_total[o:o + 4] = apres
    # relecture de la copie patchee en memoire : memes frontieres d'instructions, memes cibles
    apres_fonction = img.fonction(patch_total)
    if sorted(apres_fonction) != sorted(avant_fonction):
        erreurs.append('les frontieres d\'instructions de la fonction changent apres patch')
    for sid in ('S1', 'S2', 'S3'):
        n = apres_fonction[sites[sid][2]]
        if (n.operands[0].imm & 0xFFFFFFFF) != vs.BLOC_PISTE:
            erreurs.append('%s ne saute pas en 0x%08x' % (sid, vs.BLOC_PISTE))
    n = apres_fonction[sites['C1'][2]]
    if struct.unpack('<f', struct.pack('<I', n.operands[1].imm & 0xFFFFFFFF))[0] != -1800.0:
        erreurs.append('C1 n\'ecrit pas -1800.0')
    for sid in ('C2', 'C3'):
        n = apres_fonction[sites[sid][2]]
        mem = [o for o in n.operands if o.type == vs.X86_OP_MEM][0]
        if (mem.mem.disp & 0xFFFFFFFF) != vs.CST_M1800:
            erreurs.append('%s ne lit pas -1800.0' % sid)
    if erreurs:
        print("ERREURS (rien n'est ecrit) :")
        for e in erreurs:
            print(' -', e)
        sys.exit(1)

    os.makedirs(dossier, exist_ok=True)
    resume = []
    for nom, description, ids in MODULES:
        patche = bytearray(data)
        changements = []
        for sid in ids:
            champ, avant, apres, ins = calcul[sid]
            o = img.off(champ)
            patche[o:o + 4] = apres
            cva = {'C2': vs.CST_M1800, 'C3': vs.CST_M1800}.get(sid, 0)
            changements.append(dict(va=champ, offset=o, avant=avant.hex(), apres=apres.hex(),
                                    role='%s [%s %s a 0x%08x]' % (ROLES[sid], ins.mnemonic, ins.op_str, sites[sid][2]),
                                    reglage=REGLAGES[sid], constante_va=cva))
        sha_p = hashlib.sha256(bytes(patche)).hexdigest().upper()
        module = dict(
            nom=nom, description=description,
            avertissement="Change le circuit d'attente des avions au retour pour les DEUX porte-avions (le code est le meme). "
                          "Tout ou rien : les 3 changements vont ensemble. Jamais vu en jeu avant la premiere mesure.",
            build=dict(fichier='carrier_command.exe', taille=len(data), horodatage_pe='0x%08x' % ts,
                       taille_image='0x%08x' % soi, base='0x%08x' % base),
            sha256_origine=sha_o, sha256_patche=sha_p, nb_changements=len(changements), changements=changements)
        with open(os.path.join(dossier, nom + '.json'), 'w', encoding='utf-8') as f:
            json.dump(module, f, indent=1, ensure_ascii=False)
        resume.append((nom, description, changements, sha_p))
        print('OK : module %s : %d changements, sha256 avec ce module seul %s' % (nom, len(changements), sha_p))

    sha_deux = hashlib.sha256(bytes(patch_total)).hexdigest().upper()
    md = ['# Modules exe `atterrissage_creneau` et `atterrissage_cercle`', '',
          'Genere par `tour/outils/generer_modules_atterrissage.py` (sites definis dans `tour/etudes_circuit_atterrissage/verifier_sites.py`). '
          'Etude complete : `tour/etudes_circuit_atterrissage/ETUDE.md`.', '']
    for nom, description, changements, sha_p in resume:
        md += ['## `%s`' % nom, '', description + '.', '', '| adresse du champ | decalage fichier | avant | apres | role |', '|---|---|---|---|---|']
        for c in changements:
            md.append('| `0x%08x` | `0x%x` | `%s` | `%s` | %s |' % (c['va'], c['offset'], c['avant'], c['apres'], c['role']))
        md += ['', '- sha256 avec ce module seul (a partir de l\'original) : `%s`' % sha_p,
               '- Retour arriere : `patch_exe.py retirer --module %s`.' % nom, '']
    md += ['## Les deux ensemble (reglage « B » du Mac)', '',
           '- sha256 de l\'original + les deux modules : `%s`.' % sha_deux,
           '- Aucun octet commun entre les deux modules ni avec `ascenseur_x2` / `temps_x2` (controle fait a la generation et par `test_patch_exe.py`).', '']
    with open(rapport, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print('OK : les deux ensemble (a partir de l\'original) %s' % sha_deux)


if __name__ == '__main__':
    main()
