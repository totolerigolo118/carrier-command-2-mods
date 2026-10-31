#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generates the "atterrissage" (landing) modules of the workshop from the disassembly (never by hand).

Reads the original executable (sauvegarde/build_mac_origine), disassembles the planes' holding pattern
in c_vehicle_server_carrier::docking_manager_air::update (0x1001af631 -> 0x1001afc63), checks every
targeted instruction (address, mnemonic, jump target or constant read) and writes:
  outil/modules/atterrissage.py                    setting B: widened slot + circular pattern
  outil/modules_en_reserve/atterrissage_creneau.py setting A: widened slot only
Usage: python3 outil/generateurs/generer_atterrissage.py
Details of the game logic: see part 03 of the notes.
"""
import os, re, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
OUTIL = os.path.dirname(ICI)
ORIGINE = os.path.join(os.path.dirname(OUTIL), "sauvegarde", "build_mac_origine")
BASE = 0x100000000
DEBUT, FIN = 0x1001af631, 0x1001afc63
BLOC_PISTE = 0x1001af914      # "cmpl $1, (%r14)": start of the test that hands the runway to the plane

# Setting A: the "not yet" exits of states 1 and 2 of the pattern go through the runway test
SAUTS = [
    # (address, mnemonic, old target, new target, explanation)
    (0x1001af900, "jbe", 0x1001afb05, BLOC_PISTE, "state 1: test the runway on every tick, not only at the bottom of the turn"),
    (0x1001af85b, "jbe", 0x1001afb05, BLOC_PISTE, "state 2: test the runway during the rest of the rear turn"),
    (0x1001af867, "jmp", 0x1001afb05, BLOC_PISTE, "state 2 -> 3: test the runway at the moment of the change as well"),
]

# Setting B (in addition to A): the front turn is flown on the same circle as the rear turn
RIP = [
    # (address, mnemonic, old constant, new constant, expected values of the new one)
    (0x1001af785, "addps", 0x10286b8c0, 0x10286b920, (1000.0, 1800.0), "state 4: turn centre (-1000, 600) -> (-1000, -1800)"),
    (0x1001af7d4, "addps", 0x10286b900, 0x10286b930, (-1000.0, -1800.0), "state 4: same (back to the original frame)"),
    (0x1001afa98, "addps", 0x10286b8c0, 0x10286b920, (1000.0, 1800.0), "state 5: same"),
    (0x1001afae7, "addps", 0x10286b900, 0x10286b930, (-1000.0, -1800.0), "state 5: same (back to the original frame)"),
    (0x1001af870, "movss", 0x1028697d4, 0x102869adc, (-1800.0,), "state 3: end of the straight line z > 600 -> z > -1800"),
    (0x1001afaf2, "movss", 0x1028697d4, 0x102869adc, (-1800.0,), "state 5: end of the turn z < 600 -> z < -1800"),
]
INSTRUCTIONS = [
    # (address, original text, new text): assembled by "as" to get the bytes
    (0x1001af87b, "addss %xmm1, %xmm0", "subss %xmm1, %xmm0",
     "state 3: the target stays 1800 m ahead of the plane (z - (-1800)) instead of z + 600"),
]


def desassembler(chemin):
    sortie = subprocess.run(["objdump", "-d", "--print-imm-hex", "--start-address=%#x" % DEBUT,
                             "--stop-address=%#x" % FIN, chemin], capture_output=True, text=True, check=True).stdout
    instr = {}
    for ligne in sortie.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*(\S+)\s*([^#]*)(?:##\s*(0x[0-9a-f]+))?", ligne)
        if m:
            instr[int(m.group(1), 16)] = (bytes.fromhex(m.group(2).replace(" ", "")), m.group(3),
                                          m.group(4).strip(), int(m.group(5), 16) if m.group(5) else None)
    return instr


def assembler(texte):
    with tempfile.TemporaryDirectory() as tmp:
        src, obj = os.path.join(tmp, "a.s"), os.path.join(tmp, "a.o")
        open(src, "w").write(texte + "\n")
        subprocess.run(["as", "-arch", "x86_64", "-o", obj, src], check=True)
        sortie = subprocess.run(["objdump", "-d", obj], capture_output=True, text=True, check=True).stdout
    m = re.search(r"^\s*0:\s+((?:[0-9a-f]{2} )+)", sortie, re.M)
    return bytes.fromhex(m.group(1).replace(" ", ""))


def generer(chemin=ORIGINE):
    donnees = open(chemin, "rb").read()
    instr = desassembler(chemin)
    sauts, rips, autres = [], [], []
    for va, mnem, vieille, neuve, expl in SAUTS:
        octets, m, ops, _ = instr[va]
        cible = int(ops.split()[0], 16) if ops.startswith("0x") else None
        assert m == mnem and cible == vieille, (hex(va), m, ops)
        assert octets[:-4] in (b"\x0f\x86", b"\xe9"), "unexpected jump encoding at %#x" % va
        apres = octets[:-4] + (neuve - (va + len(octets))).to_bytes(4, "little", signed=True)
        sauts.append((va, octets.hex(), apres.hex(), "%s %#x -> %#x : %s" % (mnem, vieille, neuve, expl)))
    for va, mnem, vieille, neuve, valeurs, expl in RIP:
        octets, m, ops, lue = instr[va]
        assert m == mnem and lue == vieille, (hex(va), m, ops, lue)
        assert int.from_bytes(octets[-4:], "little", signed=True) == vieille - (va + len(octets))
        trouve = struct.unpack_from("<%df" % len(valeurs), donnees, neuve - BASE)
        assert trouve == valeurs, (hex(neuve), trouve)
        if mnem.endswith("ps"):
            assert neuve % 16 == 0, "unaligned constant for %s" % mnem
        rips.append((va, octets.hex(), vieille, neuve, "%s %s : %s" % (mnem, valeurs, expl)))
    for va, avant, apres_txt, expl in INSTRUCTIONS:
        octets, m, ops, _ = instr[va]
        assert "%s %s" % (m, ops) == avant and assembler(avant) == octets, (hex(va), m, ops)
        apres = assembler(apres_txt)
        assert len(apres) == len(octets)
        autres.append((va, octets.hex(), apres.hex(), "%s -> %s : %s" % (avant, apres_txt, expl)))
    return sauts, rips, autres


ENTETE = '''# -*- coding: utf-8 -*-
"""%s

GENERATED FILE by outil/generateurs/generer_atterrissage.py (do not edit by hand).
Function: c_vehicle_server_carrier::docking_manager_air::update, holding pattern of the planes
(helicopters are not affected). Original logic: a plane is only given the runway on the tick when it
passes the bottom of the rear turn (the "gate", 3 km behind the ship), once per 12.3 km lap.
%s
"""
NOM = "%s"
TITRE = "%s"
TYPE = "programme"

RETOUCHES = [
'''


def ecrire(chemin, doc, detail, nom, titre, sauts, rips, autres):
    lignes = [ENTETE % (doc, detail, nom, titre)]
    lignes.append("    # widened slot\n")
    for va, avant, apres, com in sauts:
        lignes.append('    ("imm", %#x, "%s", "%s"),  # %s\n' % (va, avant, apres, com))
    if rips or autres:
        lignes.append("    # circular pattern\n")
    for va, avant, vieille, neuve, com in rips:
        lignes.append('    ("rip", %#x, "%s", %#x, %#x, None),  # %s\n' % (va, avant, vieille, neuve, com))
    for va, avant, apres, com in autres:
        lignes.append('    ("imm", %#x, "%s", "%s"),  # %s\n' % (va, avant, apres, com))
    lignes.append("]\n")
    open(chemin, "w").write("".join(lignes))
    print("  written: %s (%d patches)" % (os.path.relpath(chemin, os.path.dirname(OUTIL)),
                                          len(sauts) + len(rips) + len(autres)))


def main():
    sauts, rips, autres = generer()
    ecrire(os.path.join(OUTIL, "modules", "atterrissage.py"),
           "Faster landings (setting B): widened slot + circular holding pattern.",
           "Here: the runway can be given during the whole rear turn (~2.7 km, ~35 s of flight), and the\n"
           "front turn is flown on the same circle as the rear one: lap of 7.5 km (94 s at 80 m/s) instead of 12.3 km.\n"
           "Circle centred on (-1000, -1800), radius 1200 m (ship frame), 859 m from the ship at its closest.\n"
           "Setting A alone is in modules_en_reserve/atterrissage_creneau.py.",
           "atterrissage", "Landings: widened slot + circular pattern", sauts, rips, autres)
    ecrire(os.path.join(OUTIL, "modules_en_reserve", "atterrissage_creneau.py"),
           "Landings (setting A): widened slot only, original pattern.",
           "Here: the runway can be given during the whole rear turn (~2.7 km, ~35 s of flight).\n"
           "IN RESERVE: touches the same bytes as the atterrissage module (setting B), so the two\n"
           "cannot be in outil/modules/ at the same time. Use it if setting B turns out slower.",
           "atterrissage_creneau", "Landings: widened slot (original pattern)", sauts, [], [])


if __name__ == "__main__":
    sys.exit(main())
