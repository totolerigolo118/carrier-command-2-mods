#!/usr/bin/env python3
"""Genere les modules `pont_retour_x2` et `helicos_approche_x2` pour patch_exe.py (Windows 1.5.18, 32 bits).

Ports de deux patchs du Mac (voir ETUDE.md) :
  pont_retour_x2       roulage de retour sur le pont x2 : `movss xmm7,[30.0]` (0x006fdda9, ticks par seconde gardes dans xmm7 pour
                       tous les etats de piste) lit 15.0 au lieu de 30.0. Les etats 5, 6, 7 partagent UNE queue de calcul
                       (`mulss xmm0,xmm7` a 0x007007e3). Effet de bord deduit : la queue de roulage du DEPART (0x00700c10) lit aussi
                       xmm7 sur le chemin direct.
  helicos_approche_x2  approche des helicos x2 : le point vise est 100 m devant l'helico au lieu de 50 m
                       (`addss xmm2,[50.0]` a 0x006fe1b3, partie « helico » de l'etat 3, apres le test `get_is_rotor`).

Chaque module est une SEULE lecture de constante redirigee (4 octets) vers une constante deja presente en lecture seule.
LECTURE SEULE sur l'exe donne (jamais modifie). Rien n'est ecrit si un controle echoue.

Usage : python -I generer_modules.py <exe_origine> <dossier_sortie_json> [<dossier_modules_exe_existants>]
"""
import glob
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

# (nom, description, avertissement, adresse de l'instruction, octets attendus, texte attendu,
#  ancienne constante (adresse, valeur), nouvelle constante (adresse, valeur), reglage, role)
MODULES = [
    ('pont_retour_x2',
     "roulage de retour sur le pont x2 : la constante 30,0 (ticks par seconde) lue pour les etats 5, 6, 7 devient 15,0 (1 lecture redirigee)",
     "Les avions et helicos qui reviennent roulent 2 fois plus vite sur le pont apres le toucher (piste -> ascenseur). "
     "EFFET DE BORD deduit de l'analyse (non vu en jeu) : le roulage du depart (ascenseur -> bout de piste) peut aussi aller x2 "
     "(en plus de l'ascenseur_x2). Les deux porte-avions ont le meme code. Jamais vu en jeu avant la premiere mesure.",
     0x006FDDA9, 'f30f103d8c79db00', 'movss xmm7, dword ptr [0xdb798c]',
     (0x00DB798C, 30.0), (0x00DB7930, 15.0),
     'RETURN_TAXI_TICKS_PER_SECOND',
     "`movss xmm7,[30.0]` (debut de la boucle de la file) : la lecture de 30,0 devient 15,0 ; "
     "queue commune des etats 5, 6, 7 : t += v/(L x 15) [mulss xmm0,xmm7 a 0x007007e3]"),
    ('helicos_approche_x2',
     "approche des helicos x2 : le point vise est 100 m devant l'helico au lieu de 50 m (1 lecture redirigee)",
     "Les helicos qui reviennent s'approchent environ 2 fois plus vite (visee a 100 m au lieu de 50 m). Les avions ne sont pas touches "
     "(la partie est reservee aux helicos, apres le test get_is_rotor). Valide sur le Mac avec le toucher pres de l'ascenseur ; "
     "SEUL, jamais vu. Jamais vu en jeu sur Windows avant la premiere mesure.",
     0x006FE1B3, 'f30f5815b879db00', 'addss xmm2, dword ptr [0xdb79b8]',
     (0x00DB79B8, 50.0), (0x00DB79E0, 100.0),
     'HELI_APPROACH_AIM_AHEAD_M',
     "partie helico de l'etat 3 (apres `call [vtable+0x4c]` / `test al,al` / `je 0x6fe436`) : `addss xmm2,[50.0]` (z vise = z + 50) -> `[100.0]`"),
]


def autres_champs(dossier):
    """(va, va+4, nom) de tous les changements des modules deja existants (hors les notres)."""
    res = []
    nos = {x[0] for x in MODULES}
    for p in sorted(glob.glob(os.path.join(dossier, '*.json'))):
        m = json.load(open(p, encoding='utf-8'))
        if m['nom'] in nos:
            continue
        for c in m['changements']:
            res.append((c['va'], c['va'] + len(bytes.fromhex(c['avant'])), m['nom']))
    return res


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    exe, sortie = sys.argv[1], sys.argv[2]
    existants = sys.argv[3] if len(sys.argv) == 4 else os.path.join(ICI, '..', 'outils', 'modules_exe')
    data = open(exe, 'rb').read()
    sha_o = hashlib.sha256(data).hexdigest().upper()
    if sha_o != SHA_ORIGINE:
        sys.exit("REFUS : l'exe donne n'est pas l'original 1C9A01C3...341026 (sha256 %s)" % sha_o)
    img = vs.Image(exe)
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    ts = struct.unpack_from('<I', data, pe + 8)[0]
    soi = struct.unpack_from('<I', data, pe + 24 + 56)[0]
    err = []
    deja = autres_champs(existants)
    calcul = []
    for nom, desc, avert, va, octets, texte, (c_av, v_av), (c_ap, v_ap), reglage, role in MODULES:
        ins = img.decoder(va)
        if bytes(ins.bytes) != bytes.fromhex(octets) or '%s %s' % (ins.mnemonic, ins.op_str) != texte:
            err.append('%s : 0x%08x n\'est pas `%s`' % (nom, va, texte))
            continue
        champ = va + 4
        avant = img.octets(champ, 4)
        if avant != struct.pack('<I', c_av):
            err.append('%s : octets d\'origine inattendus' % nom)
        if champ not in img.relocs:
            err.append('%s : pas de relocation (ASLR) sur le champ 0x%08x' % (nom, champ))
        for c, valeur in ((c_av, v_av), (c_ap, v_ap)):
            s = img.section(c)
            if s is None or (s[4] & 0x80000000) or (s[4] & 0x20000000) or img.flt(c) != valeur:
                err.append('%s : constante 0x%08x != %g ou section inscriptible' % (nom, c, valeur))
        for a, b, autre in deja:
            if champ < b and a < champ + 4:
                err.append('%s chevauche %s' % (nom, autre))
        apres = struct.pack('<I', c_ap)
        patche = bytearray(data)
        o = img.off(champ)
        patche[o:o + 4] = apres
        i3 = next(img.md.disasm(bytes(patche[img.off(va):img.off(va) + 16]), va))
        if i3.size != 8 or i3.mnemonic != ins.mnemonic:
            err.append('%s : relecture apres patch inattendue' % nom)
        else:
            lu = [x for x in i3.operands if x.type == vs.X86_OP_MEM][0].mem.disp & 0xFFFFFFFF
            if lu != c_ap:
                err.append('%s : la relecture lit 0x%08x et non 0x%08x' % (nom, lu, c_ap))
        calcul.append((nom, desc, avert, champ, o, avant, apres, reglage, role, c_ap, bytes(patche)))
    if err:
        print("ERREURS (rien n'est ecrit) :")
        for e in err:
            print(' -', e)
        sys.exit(1)
    os.makedirs(sortie, exist_ok=True)
    for nom, desc, avert, champ, o, avant, apres, reglage, role, c_ap, patche in calcul:
        sha_p = hashlib.sha256(patche).hexdigest().upper()
        module = dict(nom=nom, description=desc, avertissement=avert,
                      build=dict(fichier='carrier_command.exe', taille=len(data), horodatage_pe='0x%08x' % ts,
                                 taille_image='0x%08x' % soi, base='0x%08x' % img.base),
                      sha256_origine=sha_o, sha256_patche=sha_p, nb_changements=1,
                      changements=[dict(va=champ, offset=o, avant=avant.hex(), apres=apres.hex(), role=role,
                                        reglage=reglage, constante_va=c_ap)])
        with open(os.path.join(sortie, nom + '.json'), 'w', encoding='utf-8') as f:
            json.dump(module, f, indent=1, ensure_ascii=False)
        print('OK : module %s : 1 changement (0x%08x : %s -> %s), sha256 avec ce module seul %s'
              % (nom, champ, avant.hex(), apres.hex(), sha_p))


if __name__ == '__main__':
    main()
