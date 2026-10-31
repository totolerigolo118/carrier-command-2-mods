#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generates the "pont_retour_x2" module of the workshop from the disassembly (never by hand).

After touchdown, a plane taxis on the deck in 3 legs (runway states 5, 6, 7 of
c_vehicle_server_carrier::docking_manager_air::update): roll back from the front of the runway to taxi_a
(~125 m), taxi_a -> lift_upper_wait, then -> elevator platform. On each tick, the progress along the
leg increases by v / (L x 30). The three "mulss [30.0]" of these states are distinct instructions:
we make them read 15.0 (constant already present) -> taxiing goes 2x faster, for these three
legs only. The runway stays reserved until the elevator, as in the original game.

The generator checks, on the original executable (sauvegarde/build_mac_origine):
  - each targeted instruction: address, mnemonic, constant read (30.0);
  - the new constant (15.0), read-only;
  - that each instruction is reached ONLY from its own state: complete list of the function's jumps
    that lead to it, and previous instruction (whether it falls through into it or not).
Usage: python3 outil/generateurs/generer_pont_retour.py
Study: part 03 of the notes
"""
import os, re, struct, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
OUTIL = os.path.dirname(ICI)
ORIGINE = os.path.join(os.path.dirname(OUTIL), "sauvegarde", "build_mac_origine")
BASE = 0x100000000
DEBUT, FIN = 0x1001accd8, 0x1001b2618     # docking_manager_air::update
TRENTE, QUINZE = 0x102869898, 0x1028699cc

CIBLES = [
    # (address, jumps of the function that lead to it, does the previous instruction fall through into it?, explanation)
    (0x1001b0824, {0x1001adf65}, False, "state 5 : roll back from the front of the runway to taxi_a (~125 m)"),
    (0x1001ae07c, {0x1001ae05e, 0x1001ae06f}, True, "state 6 : taxi_a -> lift_upper_wait (~17 m)"),
    (0x1001b0831, {0x1001ae134}, False, "state 7 : lift_upper_wait -> elevator platform (15.5 m)"),
]
# bounds of the code of each state (jump table 0x1001b25d8): the source jumps must lie within
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
    # __TEXT,__const: read-only, shared -> we do not modify it, we redirect the read
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
"""Taxiing x2 on the deck on return: after touchdown, planes (and helicopters) taxi 2x faster
from the front of the runway to the elevator.

GENERATED FILE by outil/generateurs/generer_pont_retour.py (do not edit by hand).
Function: c_vehicle_server_carrier::docking_manager_air::update, runway states 5, 6 and 7. On each tick,
the progress along a leg increases by v / (L x 30); here v / (L x 15) for these three legs only
(constant 30.0 -> 15.0, already present). The runway stays reserved until the elevator, as in the original:
no new collision risk. Together with ascenseur_x2 (other bytes: acceleration and ceiling): time on
the deck ~42 s -> ~22 s. Study: part 03 of the notes
"""
NOM = "pont_retour_x2"
TITRE = "Taxiing x2 on the deck on return (planes, helicopters)"
TYPE = "programme"

RETOUCHES = [
%s]
'''


def main():
    lignes = "".join('    ("rip", %#x, "%s", %#x, %#x, 0.5),  # mulss 30.0 -> 15.0 : %s\n'
                     % (va, avant, TRENTE, QUINZE, expl) for va, avant, expl in generer())
    chemin = os.path.join(OUTIL, "modules", "pont_retour_x2.py")
    open(chemin, "w").write(MODELE % lignes)
    print("  written: %s (3 patches)" % os.path.relpath(chemin, os.path.dirname(OUTIL)))


if __name__ == "__main__":
    sys.exit(main())
