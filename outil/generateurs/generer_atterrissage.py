#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere les modules « atterrissage » de l'atelier a partir du desassemblage (jamais a la main).

Lit le programme d'origine (sauvegarde/build_mac_origine), desassemble le circuit d'attente des avions
dans c_vehicle_server_carrier::docking_manager_air::update (0x1001af631 -> 0x1001afc63), verifie chaque
instruction visee (adresse, mnemonique, cible ou constante lue) et ecrit :
  outil/modules/atterrissage.py                    reglage B : creneau elargi + circuit en cercle
  outil/modules_en_reserve/atterrissage_creneau.py reglage A : creneau elargi seul
Usage : python3 outil/generateurs/generer_atterrissage.py
Detail de la logique du jeu : fiche DEMARRER_cc2_patchs.md, section 4.
"""
import os, re, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
OUTIL = os.path.dirname(ICI)
ORIGINE = os.path.join(os.path.dirname(OUTIL), "sauvegarde", "build_mac_origine")
BASE = 0x100000000
DEBUT, FIN = 0x1001af631, 0x1001afc63
BLOC_PISTE = 0x1001af914      # « cmpl $1, (%r14) » : debut du test qui donne la piste a l'avion

# Reglage A : les sorties « pas encore » des etats 1 et 2 du circuit passent par le test de la piste
SAUTS = [
    # (adresse, mnemonique, ancienne cible, nouvelle cible, explication)
    (0x1001af900, "jbe", 0x1001afb05, BLOC_PISTE, "etat 1 : tester la piste a chaque tick, pas seulement au bas du virage"),
    (0x1001af85b, "jbe", 0x1001afb05, BLOC_PISTE, "etat 2 : tester la piste pendant le reste du virage arriere"),
    (0x1001af867, "jmp", 0x1001afb05, BLOC_PISTE, "etat 2 -> 3 : tester la piste aussi au moment du changement"),
]

# Reglage B (en plus de A) : le virage avant se fait sur le meme cercle que le virage arriere
RIP = [
    # (adresse, mnemonique, ancienne constante, nouvelle constante, valeurs attendues de la nouvelle)
    (0x1001af785, "addps", 0x10286b8c0, 0x10286b920, (1000.0, 1800.0), "etat 4 : centre du virage (-1000, 600) -> (-1000, -1800)"),
    (0x1001af7d4, "addps", 0x10286b900, 0x10286b930, (-1000.0, -1800.0), "etat 4 : idem (retour au repere)"),
    (0x1001afa98, "addps", 0x10286b8c0, 0x10286b920, (1000.0, 1800.0), "etat 5 : idem"),
    (0x1001afae7, "addps", 0x10286b900, 0x10286b930, (-1000.0, -1800.0), "etat 5 : idem (retour au repere)"),
    (0x1001af870, "movss", 0x1028697d4, 0x102869adc, (-1800.0,), "etat 3 : fin de la ligne droite z > 600 -> z > -1800"),
    (0x1001afaf2, "movss", 0x1028697d4, 0x102869adc, (-1800.0,), "etat 5 : fin du virage z < 600 -> z < -1800"),
]
INSTRUCTIONS = [
    # (adresse, texte d'origine, nouveau texte) : assemble par « as » pour obtenir les octets
    (0x1001af87b, "addss %xmm1, %xmm0", "subss %xmm1, %xmm0",
     "etat 3 : la cible reste 1800 m devant l'avion (z - (-1800)) au lieu de z + 600"),
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
        assert octets[:-4] in (b"\x0f\x86", b"\xe9"), "saut court inattendu a %#x" % va
        apres = octets[:-4] + (neuve - (va + len(octets))).to_bytes(4, "little", signed=True)
        sauts.append((va, octets.hex(), apres.hex(), "%s %#x -> %#x : %s" % (mnem, vieille, neuve, expl)))
    for va, mnem, vieille, neuve, valeurs, expl in RIP:
        octets, m, ops, lue = instr[va]
        assert m == mnem and lue == vieille, (hex(va), m, ops, lue)
        assert int.from_bytes(octets[-4:], "little", signed=True) == vieille - (va + len(octets))
        trouve = struct.unpack_from("<%df" % len(valeurs), donnees, neuve - BASE)
        assert trouve == valeurs, (hex(neuve), trouve)
        if mnem.endswith("ps"):
            assert neuve % 16 == 0, "constante non alignee pour %s" % mnem
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

FICHIER GENERE par outil/generateurs/generer_atterrissage.py (ne pas modifier a la main).
Fonction : c_vehicle_server_carrier::docking_manager_air::update, circuit d'attente des avions
(les helicos ne sont pas concernes). Logique d'origine : un avion ne recoit la piste qu'au tick ou il
passe le bas du virage arriere (la « porte », 3 km derriere le bateau), une fois par tour de 12,3 km.
%s
"""
NOM = "%s"
TITRE = "%s"
TYPE = "programme"

RETOUCHES = [
'''


def ecrire(chemin, doc, detail, nom, titre, sauts, rips, autres):
    lignes = [ENTETE % (doc, detail, nom, titre)]
    lignes.append("    # creneau elargi\n")
    for va, avant, apres, com in sauts:
        lignes.append('    ("imm", %#x, "%s", "%s"),  # %s\n' % (va, avant, apres, com))
    if rips or autres:
        lignes.append("    # circuit en cercle\n")
    for va, avant, vieille, neuve, com in rips:
        lignes.append('    ("rip", %#x, "%s", %#x, %#x, None),  # %s\n' % (va, avant, vieille, neuve, com))
    for va, avant, apres, com in autres:
        lignes.append('    ("imm", %#x, "%s", "%s"),  # %s\n' % (va, avant, apres, com))
    lignes.append("]\n")
    open(chemin, "w").write("".join(lignes))
    print("  ecrit : %s (%d retouches)" % (os.path.relpath(chemin, os.path.dirname(OUTIL)),
                                            len(sauts) + len(rips) + len(autres)))


def main():
    sauts, rips, autres = generer()
    ecrire(os.path.join(OUTIL, "modules", "atterrissage.py"),
           "Atterrissages plus rapides (reglage B) : creneau elargi + circuit d'attente en cercle.",
           "Ici : la piste peut etre donnee sur tout le virage arriere (~2,7 km, ~35 s de vol), et le virage\n"
           "avant se fait sur le meme cercle que l'arriere : tour de 7,5 km (94 s a 80 m/s) au lieu de 12,3 km.\n"
           "Cercle de centre (-1000, -1800), rayon 1200 m (repere du bateau), a 859 m au plus pres du bateau.\n"
           "Choisi par le moddeur le 23/10/2026. Le reglage A seul est dans modules_en_reserve/atterrissage_creneau.py.",
           "atterrissage", "Atterrissages : creneau elargi + circuit en cercle", sauts, rips, autres)
    ecrire(os.path.join(OUTIL, "modules_en_reserve", "atterrissage_creneau.py"),
           "Atterrissages (reglage A) : creneau elargi seul, circuit d'origine.",
           "Ici : la piste peut etre donnee sur tout le virage arriere (~2,7 km, ~35 s de vol).\n"
           "EN RESERVE : touche les memes octets que le module atterrissage (reglage B), donc les deux ne\n"
           "peuvent pas etre dans outil/modules/ en meme temps. A utiliser si le reglage B se revele plus lent.",
           "atterrissage_creneau", "Atterrissages : creneau elargi (circuit d'origine)", sauts, [], [])


if __name__ == "__main__":
    sys.exit(main())
