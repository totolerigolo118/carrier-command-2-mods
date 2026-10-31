#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generates the "squadron speed" module (ECO / NORMAL / FLANK) from vitesse_escadrille.c.

1. compiles the graft (clang -arch x86_64, same options as the other grafts, CHEMIN = file of the mode);
2. links it at address ZONE (dead code of ImGui::ShowDemoWindow), with the linker of
   generer_helicos_ascenseur.py (JEU table specific to this module);
3. writes outil/modules/vitesse_escadrille.py: the graft, the hook in the planes' tick_control and
   the "dofile" entry of base_funcs which becomes "cc2_vitesse".

The "before" bytes are read from the rebuilt original executable (sauvegarde/build_mac_origine).
Study: part 05 of the notes. Usage: python3 outil/generateurs/generer_vitesse_escadrille.py
"""
import hashlib, os, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import generer_helicos_ascenseur as G

OUTIL = os.path.dirname(ICI)
SOURCE = os.path.join(ICI, "vitesse_escadrille.c")
MODULE = os.path.join(OUTIL, "modules", "vitesse_escadrille.py")
ZONE, ZONE_TAILLE = 0x10005d000, 0x400       # free as of 2026-10-25: 0x10005c4e0..0x100061200
CHEMIN = os.path.expanduser("~/Library/Application Support/Carrier Command 2/vitesse_escadrille.txt")

JEU = {
    "_g_lua_gettop": 0x1028278dc,
    "_g_lua_tointegerx": 0x102827dc4,
    "_g_lua_pushinteger": 0x10282801b,
    "_g_fopen": 0x102867e78,          # libc stubs
    "_g_fgetc": 0x102867e60,
    "_g_fputs": 0x102867e84,
    "_g_fclose": 0x102867e42,
    "_g_vit_modes": 0x1029e5680,      # end of ShowDemoWindowWidgets()::text (__data, zeros, dead code)
    "_g_vit_etat": 0x1029e5690,
    "_g_ret_2b8e": 0x1001c2b8e,       # tick_control: movl 0x318(%r13), %esi
}

# c_vehicle_server_wing::tick_control, 0x1001c2b4b..0x1001c2b8e (no jump enters it, except at the end)
BRANCHEMENT = (0x1001c2b4b,
               "f30f1003" "0f28c8" "f30f5f0d966f6a02" "f30f5d0dca6f6a02" "f3410f118dc8020000"
               "4183bd900000000a" "7519" "f30f5f05b36f6a02" "f30f5d05a76f6a02" "f3410f1185c8020000",
               "_vit_plancher", "aimed speed of the planes (mode 0): bounds [48|72, 144] -> floor depending on the mode")

BASE_FUNCS_DOFILE = 0x1029dd310       # { "dofile", luaB_dofile } in base_funcs (__DATA,__const)
DOFILE = (0x10297970e, 0x10283aa8c)   # checked at generation time

DOC = """Cruise speed of AI-piloted planes chosen from the screen (ECO / NORMAL / FLANK).

GENERATED FILE by outil/generateurs/generer_vitesse_escadrille.py from vitesse_escadrille.c (do not
edit by hand). Study: part 05 of the notes.
When flying to a point, the planes' AI aims at the floor speed: 48 m/s (Albatros) or 72 m/s (Manta). Here the
floor depends on the mode chosen by the team: ECO = original game, NORMAL = 61 / 91 m/s (about 80 % of
power, estimate), FLANK = 144 m/s (full throttle). Teams piloted by the AI (enemies): original game.
The mode is set by the Lua function cc2_vitesse(team [, mode]) (in place of dofile, which is unused), called
by the module "vitesse_boutons", which draws the screen buttons; the last mode is kept in
~/Library/Application Support/Carrier Command 2/vitesse_escadrille.txt.
Without the "vitesse_boutons" module, nothing chooses a mode: planes fly as in the original game."""


def compiler_et_relier(dossier, chemin):
    objet = os.path.join(dossier, "vitesse_escadrille.o")
    r = subprocess.run(["clang"] + G.DRAPEAUX + ['-DCHEMIN="%s"' % chemin, "-o", objet, SOURCE],
                       capture_output=True, text=True)
    if r.returncode:
        raise G.Erreur("compilation: " + r.stderr)
    ancien = G.JEU
    G.JEU = JEU
    try:
        image, points, relocs = G.relier(open(objet, "rb").read(), ZONE)
    finally:
        G.JEU = ancien
    if len(image) > ZONE_TAILLE or not G.ZONE_DEBUT <= ZONE < ZONE + len(image) <= G.ZONE_FIN:
        raise G.Erreur("the graft exceeds its space (%d bytes)" % len(image))
    return image, points, relocs


def generer(programme, dossier, chemin=CHEMIN):
    image, points, relocs = compiler_et_relier(dossier, chemin)
    off = ZONE - G.BASE_FICHIER
    retouches = [(ZONE, programme[off:off + len(image)].hex(), image.hex(),
                  "added code (%d bytes) in place of ImGui::ShowDemoWindow, never called" % len(image))]

    va, attendu, point, commentaire = BRANCHEMENT
    o2 = va - G.BASE_FICHIER
    n = len(attendu) // 2
    if programme[o2:o2 + n].hex() != attendu:
        raise G.Erreur("unexpected original bytes at %#x" % va)
    saut = b"\xe9" + struct.pack("<i", points[point] - (va + 5))
    retouches.append((va, attendu, (saut + b"\xcc" * (n - 5)).hex(),
                      "%s -> jmp %s (%#x)" % (commentaire, point, points[point])))

    o3 = BASE_FUNCS_DOFILE - G.BASE_FICHIER
    nom, fonction = struct.unpack_from("<QQ", programme, o3)
    if (nom, fonction) != DOFILE or programme[nom - G.BASE_FICHIER:nom - G.BASE_FICHIER + 7] != b"dofile\0":
        raise G.Erreur("base_funcs: unexpected dofile entry at %#x" % BASE_FUNCS_DOFILE)
    retouches.append((BASE_FUNCS_DOFILE, programme[o3:o3 + 16].hex(),
                      struct.pack("<QQ", points["_vit_nom_lua"], points["_vit_lua"]).hex(),
                      "base_funcs: { \"dofile\", luaB_dofile } -> { \"cc2_vitesse\", vit_lua }"))

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
    G.ecrire_module(MODULE, "vitesse_escadrille", "Squadron speed (ECO / NORMAL / FLANK): executable part",
                    DOC, retouches, md5_modifie)
    print("vitesse_escadrille: %d bytes of code at %#x, %d links, md5 with this module alone %s"
          % (taille, ZONE, len(relocs), md5_modifie))
    for p, a in sorted(points.items(), key=lambda x: x[1]):
        print("    %-16s %#x" % (p, a))
    for p, cible, nom in relocs:
        if not ZONE <= cible < ZONE + taille:
            print("    link %#x -> %#x %s" % (p, cible, nom))
    print("    -> " + os.path.relpath(MODULE, os.path.dirname(OUTIL)))


if __name__ == "__main__":
    try:
        main()
    except G.Erreur as e:
        sys.exit("ERROR: %s" % e)
