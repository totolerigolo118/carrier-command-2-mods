#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generates the "ecriture_releve" module from ecriture_releve.s.

Lua's print() then writes to ~/Library/Application Support/Carrier Command 2/releve_cc2.txt instead of
standard output (lost when Steam launches the game). Used for the performance recording (module "releve",
library_custom_5.lua) and for the performance curves (the plotting tool (not included)).

1. assembles the graft (clang -arch x86_64);
2. links it at address 0x100061a00, in the dead code of ImGui::ShowDemoWindow, with the mini
   linker of generer_helicos_ascenseur.py;
3. writes outil/modules_en_reserve/ecriture_releve.py and its copy in outil/modules/.

The "before" bytes are read from the rebuilt original executable (sauvegarde/build_mac_origine).
Usage: python3 outil/generateurs/generer_ecriture_releve.py
"""
import hashlib, os, shutil, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import generer_helicos_ascenseur as editeur

OUTIL = os.path.dirname(ICI)
SOURCE = os.path.join(ICI, "ecriture_releve.s")
ORIGINE = os.path.join(os.path.dirname(OUTIL), "sauvegarde", "build_mac_origine")
RESERVE = os.path.join(OUTIL, "modules_en_reserve")
MODULES = os.path.join(OUTIL, "modules")
MD5_ORIGINE = "b0107170ddaf0245cbfee8a2d876aeb6"
BASE_FICHIER = 0x100000000
CHEMIN_RELEVE = os.path.expanduser("~/Library/Application Support/Carrier Command 2/releve_cc2.txt")

# end of the dead code of ImGui::ShowDemoWindow (0x10005af39..0x100061c00); already taken: 0x10005af40..0x10005c4e0
# (helicos_ascenseur, in reserve) and 0x100061b80..0x100061b9c (helicos_pres_ascenseur)
ZONE_DEBUT, ZONE_FIN = 0x100061a00, 0x100061b80

JEU = {
    "_g_fopen": 0x102867e78,          # stub _fopen
    "_g_got_stdoutp": 0x10299dff0,    # GOT entry for ___stdoutp (contains &__stdoutp)
    "_g_case": 0x102a2a828,           # guard variable for ShowExampleAppLog(bool*)::log (__bss, 8 bytes, dead code only)
}

BRANCHEMENTS = [
    (0x10283aed0, "4c8b2519311600", "_rv_r12", "movq GOT(__stdoutp), %r12 (luaB_print, before the arguments)"),
    (0x10283af78, "488b1d71301600", "_rv_rbx", "movq GOT(__stdoutp), %rbx (luaB_print, final \"\\n\" and fflush)"),
]

DOC = """Recording output: Lua's print() writes to a file instead of standard output.

GENERATED FILE by outil/generateurs/generer_ecriture_releve.py from ecriture_releve.s
(do not edit by hand). Purpose: performance curves, examined after play.
When Steam launches the game, what Lua scripts write with print() is lost. Here, at the first print(),
the game opens (in append mode) %s
and writes there everything print() writes (if opening fails: standard output, as before).
Two instructions of luaB_print (0x10283aed0 and 0x10283af78) call added code (about sixty bytes,
plus the file path) in the dead code of ImGui::ShowDemoWindow; the FILE* is kept in a memory cell that only
this dead code used.
Without the "releve" module (library_custom_5.lua), only the mods' print() calls end up in the file.""" % CHEMIN_RELEVE


def assembler(chemin_releve, dossier):
    source = os.path.join(dossier, "ecriture_releve.s")
    texte = open(SOURCE).read()
    if "__CHEMIN__" not in texte or '"' in chemin_releve or "\\" in chemin_releve:
        raise editeur.Erreur("unusable recording path")
    open(source, "w").write(texte.replace("__CHEMIN__", chemin_releve))
    objet = os.path.join(dossier, "ecriture_releve.o")
    r = subprocess.run(["clang", "-arch", "x86_64", "-c", "-o", objet, source], capture_output=True, text=True)
    if r.returncode:
        raise editeur.Erreur("assembly: " + r.stderr)
    return objet


def generer(programme, dossier):
    objet = assembler(CHEMIN_RELEVE, dossier)
    ancien = editeur.JEU
    editeur.JEU = JEU
    try:
        image, points, relocs = editeur.relier(open(objet, "rb").read(), ZONE_DEBUT)
    finally:
        editeur.JEU = ancien
    if ZONE_DEBUT + len(image) > ZONE_FIN:
        raise editeur.Erreur("the graft exceeds the free zone")
    off = ZONE_DEBUT - BASE_FICHIER
    retouches = [(ZONE_DEBUT, programme[off:off + len(image)].hex(), image.hex(),
                  "added code (%d bytes, including the file path) in the dead code of ImGui::ShowDemoWindow" % len(image))]
    for va, attendu, point, commentaire in BRANCHEMENTS:
        o = va - BASE_FICHIER
        n = len(attendu) // 2
        if programme[o:o + n].hex() != attendu:
            raise editeur.Erreur("unexpected original bytes at %#x" % va)
        appel = b"\xe8" + struct.pack("<i", points[point] - (va + 5)) + b"\x66\x90"
        retouches.append((va, attendu, appel.hex(), "%s -> call %s (%#x)" % (commentaire, point, points[point])))
    modifie = bytearray(programme)
    for va, avant, apres, _ in retouches:
        modifie[va - BASE_FICHIER:va - BASE_FICHIER + len(avant) // 2] = bytes.fromhex(apres)
    return retouches, hashlib.md5(modifie).hexdigest(), points, relocs, len(image)


def main():
    programme = open(ORIGINE, "rb").read()
    if hashlib.md5(programme).hexdigest() != MD5_ORIGINE:
        raise editeur.Erreur("sauvegarde/build_mac_origine is not the expected original executable")
    with tempfile.TemporaryDirectory(prefix="greffe_cc2_") as dossier:
        retouches, md5_modifie, points, relocs, taille = generer(programme, dossier)
    chemin = os.path.join(RESERVE, "ecriture_releve.py")
    editeur.ecrire_module(chemin, "ecriture_releve", "Recording: print() writes to a file (performance curves)",
                          DOC, retouches, md5_modifie)
    shutil.copyfile(chemin, os.path.join(MODULES, "ecriture_releve.py"))
    print("ecriture_releve: %d bytes of code, %d links, md5 with this module alone %s" % (taille, len(relocs), md5_modifie))
    for p, a in sorted(points.items(), key=lambda x: x[1]):
        print("    %-10s %#x" % (p, a))
    for p, cible, nom in relocs:
        print("    link %#x -> %#x (%s)" % (p, cible, nom))
    print("    -> outil/modules_en_reserve/ecriture_releve.py (+ copy in outil/modules/)")


if __name__ == "__main__":
    try:
        main()
    except editeur.Erreur as e:
        sys.exit("ERROR: %s" % e)
