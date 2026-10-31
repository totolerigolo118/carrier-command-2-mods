#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generates the module "cancel the exit of a plane already picked up by the crane" from grue_annulation.c.

1. compiles the graft (clang -arch x86_64, same options as the other grafts);
2. links it at address ZONE (dead code of ImGui::ShowDemoWindow), with the linker of
   generer_helicos_ascenseur.py (same relocations, JEU table specific to this module);
3. writes outil/modules/grue_annulation.py: 1 "imm" patch for the added code + 2 hooks.

The "before" bytes are read from the rebuilt original executable (sauvegarde/build_mac_origine).
Study: part 02 of the notes, section 5. Usage: python3 outil/generateurs/generer_grue_annulation.py
"""
import hashlib, os, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import generer_helicos_ascenseur as G

OUTIL = os.path.dirname(ICI)
SOURCE = os.path.join(ICI, "grue_annulation.c")
MODULE = os.path.join(OUTIL, "modules", "grue_annulation.py")
ZONE, ZONE_TAILLE = 0x100061200, 0x400      # free as of 2026-10-25: 0x100061800... = cctv (planned), 0x100061a00... = releve

JEU = {
    "_g_push_geste": 0x10019a450,    # mm_vector<e_crane_state>::push_back()
    "_g_vider_route": 0x10009060c,   # mm_vector<c_vehicle_waypoint_data>::clear()
    "_g_reset_route": 0x10010cea4,   # c_vehicle_server::reset_waypoint_path()
    "g_ret_a8c0e": 0x1001a8c0e,      # epilogue of docking_manager_air::undock
    "g_ret_ad9b2": 0x1001ad9b2,      # continuation of the "end of crane" block (launch mode)
}

BRANCHEMENTS = [
    (0x1001a8c01, "4183be200200000775 03895f28".replace(" ", ""), "_ag_a",
     "undock, plane already in the crane/elevator/runway: cmpl $7,0x220(%r14) ; jne ; movl %ebx,0x28(%rdi)"),
    (0x1001ad9ad, "41837e1800", "_ag_b", "end of crane in launch mode: cmpl $0,0x18(%r14)"),
]

DOC = """Cancel the exit of a plane already picked up by the hangar crane (public tracker request #20652).

GENERATED FILE by outil/generateurs/generer_grue_annulation.py from grue_annulation.c (do not
edit by hand). Study: part 02 of the notes, section 5.
In the original game, a 2nd press of the bay button only cancels the exit if the plane is still waiting
in the queue; but the crane takes it almost immediately. Here, a 2nd press while the crane is busy with
the plane brings it back to its bay:
  - crane not yet hooked on: it goes back up and returns to rest, the plane has not moved;
  - plane hooked on, not yet turned: the crane goes back up, carries it back above its bay, sets it
    down, returns.
Too late (nothing changes, as before): plane being turned or already released above the elevator, on the
elevator, on the deck. The plane becomes "in the hangar" again (route cleared, like the game's own
cancellation). Launch mode only; the enemy AI only launches aircraft that are in the hangar.
Code added in the dead code of ImGui::ShowDemoWindow + 2 hooks (docking_manager_air::undock and
::update). Removing the module blocks nothing: a plane in the middle of a return would then be handed on
to the elevator."""


def generer(programme, dossier):
    objet = os.path.join(dossier, "grue_annulation.o")
    r = subprocess.run(["clang"] + G.DRAPEAUX + ["-o", objet, SOURCE], capture_output=True, text=True)
    if r.returncode:
        raise G.Erreur("compilation: " + r.stderr)
    ancien = G.JEU
    G.JEU = JEU                                  # the linker reads the JEU table of its own module
    try:
        image, points, relocs = G.relier(open(objet, "rb").read(), ZONE)
    finally:
        G.JEU = ancien
    if len(image) > ZONE_TAILLE or not G.ZONE_DEBUT <= ZONE < ZONE + len(image) <= G.ZONE_FIN:
        raise G.Erreur("the graft exceeds its space (%d bytes)" % len(image))
    off = ZONE - G.BASE_FICHIER
    retouches = [(ZONE, programme[off:off + len(image)].hex(), image.hex(),
                  "added code (%d bytes) in place of ImGui::ShowDemoWindow, never called" % len(image))]
    for va, attendu, point, commentaire in BRANCHEMENTS:
        o2 = va - G.BASE_FICHIER
        n = len(attendu) // 2
        if programme[o2:o2 + n].hex() != attendu:
            raise G.Erreur("unexpected original bytes at %#x" % va)
        saut = b"\xe9" + struct.pack("<i", points[point] - (va + 5))
        retouches.append((va, attendu, (saut + b"\x90" * (n - 5)).hex(),
                          "%s -> jmp %s (%#x)" % (commentaire, point, points[point])))
    modifie = bytearray(programme)
    for va, avant, apres, _ in retouches:
        modifie[va - G.BASE_FICHIER:va - G.BASE_FICHIER + len(avant) // 2] = bytes.fromhex(apres)
    return retouches, hashlib.md5(modifie).hexdigest(), points, relocs, len(image)


def main():
    programme = open(G.ORIGINE, "rb").read()
    if hashlib.md5(programme).hexdigest() != G.MD5_ORIGINE:
        raise G.Erreur("sauvegarde/build_mac_origine is not the expected original executable")
    with tempfile.TemporaryDirectory(prefix="greffe_cc2_") as dossier:
        retouches, md5_modifie, points, relocs, taille = generer(programme, dossier)
    G.ecrire_module(MODULE, "grue_annulation", "Crane: cancel the exit of a plane already picked up (2nd press)",
                    DOC, retouches, md5_modifie)
    print("grue_annulation: %d bytes of code at %#x, %d links, md5 with this module alone %s"
          % (taille, ZONE, len(relocs), md5_modifie))
    for p, a in sorted(points.items(), key=lambda x: x[1]):
        print("    %-12s %#x" % (p, a))
    for p, cible, nom in relocs:
        if not ZONE <= cible < ZONE + taille:
            print("    link %#x -> %#x %s" % (p, cible, nom))
    print("    -> " + os.path.relpath(MODULE, os.path.dirname(OUTIL)))


if __name__ == "__main__":
    try:
        main()
    except G.Erreur as e:
        sys.exit("ERROR: %s" % e)
