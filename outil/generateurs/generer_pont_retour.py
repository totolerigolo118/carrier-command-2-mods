#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere le module « pont_retour_x2 » de l'atelier a partir du desassemblage (jamais a la main).

Apres le toucher, un avion roule sur le pont en 3 troncons (etats de piste 5, 6, 7 de
c_vehicle_server_carrier::docking_manager_air::update) : recul de l'avant de la piste jusqu'a taxi_a
(~125 m), taxi_a -> lift_upper_wait, puis -> plateforme de l'ascenseur. Chaque tick, l'avancement le long
du troncon augmente de v / (L x 30). Les trois « mulss [30.0] » de ces etats sont des instructions
distinctes : on les fait lire 15.0 (constante deja presente) -> le roulage va 2x plus vite, pour ces
trois troncons seulement. La piste reste reservee jusqu'a l'ascenseur, comme dans le jeu d'origine.

Le generateur verifie, sur le programme d'origine (sauvegarde/build_mac_origine) :
  - chaque instruction visee : adresse, mnemonique, constante lue (30.0) ;
  - la nouvelle constante (15.0), en lecture seule ;
  - qu'on n'arrive a chaque instruction QUE depuis son etat : liste complete des sauts de la fonction
    qui y menent, et instruction precedente (qui tombe dedans ou non).
Usage : python3 outil/generateurs/generer_pont_retour.py
Etude : mods/cc2-patchs/etudes/piste_et_pont.md
"""
import os, re, struct, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
OUTIL = os.path.dirname(ICI)
ORIGINE = os.path.join(os.path.dirname(OUTIL), "sauvegarde", "build_mac_origine")
BASE = 0x100000000
DEBUT, FIN = 0x1001accd8, 0x1001b2618     # docking_manager_air::update
TRENTE, QUINZE = 0x102869898, 0x1028699cc

CIBLES = [
    # (adresse, sauts de la fonction qui y menent, l'instruction precedente tombe-t-elle dedans ?, explication)
    (0x1001b0824, {0x1001adf65}, False, "etat 5 : recul de l'avant de la piste jusqu'a taxi_a (~125 m)"),
    (0x1001ae07c, {0x1001ae05e, 0x1001ae06f}, True, "etat 6 : taxi_a -> lift_upper_wait (~17 m)"),
    (0x1001b0831, {0x1001ae134}, False, "etat 7 : lift_upper_wait -> plateforme de l'ascenseur (15,5 m)"),
]
# bornes du code de chaque etat (table de saut 0x1001b25d8) : les sauts sources doivent y etre
ETATS = {5: (0x1001adeef, 0x1001adfe4), 6: (0x1001adfe4, 0x1001ae0be), 7: (0x1001ae0be, 0x1001ae231)}


def desassembler(chemin):
    sortie = subprocess.run(["objdump", "-d", "--print-imm-hex", "--start-address=%#x" % DEBUT,
                             "--stop-address=%#x" % FIN, chemin], capture_output=True, text=True, check=True).stdout
    instr = []
    for ligne in sortie.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*(\S+)\s*([^#]*)(?:##\s*(0x[0-9a-f]+))?", ligne)
        if m:
            instr.append((int(m.group(1), 16), bytes.fromhex(m.group(2).replace(" ", "")), m.group(3),
                          m.group(4).strip(), int(m.group(5), 16) if m.group(5) else None))
    return instr


def generer(chemin=ORIGINE):
    donnees = open(chemin, "rb").read()
    instr = desassembler(chemin)
    par_adresse = {i[0]: i for i in instr}
    assert struct.unpack_from("<f", donnees, TRENTE - BASE)[0] == 30.0
    assert struct.unpack_from("<f", donnees, QUINZE - BASE)[0] == 15.0
    # __TEXT,__const : lecture seule, partagee -> on ne la modifie pas, on redirige la lecture
    assert 0x102869720 <= QUINZE < 0x102900000
    sauts = {}
    for va, octets, mnem, ops, _ in instr:
        if mnem.startswith("j") and ops.startswith("0x"):
            sauts.setdefault(int(ops.split()[0], 16), set()).add(va)
    retouches = []
    for va, sources, chute, expl in CIBLES:
        _, octets, mnem, ops, lue = par_adresse[va]
        assert mnem == "mulss" and lue == TRENTE and ops.endswith("%xmm1"), (hex(va), mnem, ops, lue)
        assert int.from_bytes(octets[-4:], "little", signed=True) == TRENTE - (va + len(octets))
        assert sauts.get(va, set()) == sources, (hex(va), sorted(map(hex, sauts.get(va, set()))))
        k = [i[0] for i in instr].index(va)
        precedente = instr[k - 1][2]
        assert (precedente not in ("jmp", "jmpq", "retq", "ud2")) == chute, (hex(va), precedente)
        etat = int(expl.split()[1])
        lo, hi = ETATS[etat]
        assert all(lo <= s < hi for s in sources), (hex(va), etat)
        retouches.append((va, octets.hex(), expl))
    return retouches


MODELE = '''# -*- coding: utf-8 -*-
"""Roulage x2 sur le pont au retour : apres le toucher, les avions (et les helicos) roulent 2x plus vite
de l'avant de la piste jusqu'a l'ascenseur.

FICHIER GENERE par outil/generateurs/generer_pont_retour.py (ne pas modifier a la main).
Fonction : c_vehicle_server_carrier::docking_manager_air::update, etats de piste 5, 6 et 7. Chaque tick,
l'avancement d'un troncon augmente de v / (L x 30) ; ici v / (L x 15) pour ces trois troncons seulement
(constante 30.0 -> 15.0, deja presente). La piste reste reservee jusqu'a l'ascenseur, comme a l'origine :
aucun nouveau risque de collision. Avec ascenseur_x2 (autres octets : acceleration et plafond) : temps sur
le pont ~42 s -> ~22 s. Choisi par le moddeur le 25/10/2026. Etude : etudes/piste_et_pont.md
"""
NOM = "pont_retour_x2"
TITRE = "Roulage x2 sur le pont au retour (avions, helicos)"
TYPE = "programme"

RETOUCHES = [
%s]
'''


def main():
    lignes = "".join('    ("rip", %#x, "%s", %#x, %#x, 0.5),  # mulss 30.0 -> 15.0 : %s\n'
                     % (va, avant, TRENTE, QUINZE, expl) for va, avant, expl in generer())
    chemin = os.path.join(OUTIL, "modules", "pont_retour_x2.py")
    open(chemin, "w").write(MODELE % lignes)
    print("  ecrit : %s (3 retouches)" % os.path.relpath(chemin, os.path.dirname(OUTIL)))


if __name__ == "__main__":
    sys.exit(main())
