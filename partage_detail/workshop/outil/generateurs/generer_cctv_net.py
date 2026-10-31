#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generates the "cctv_net" module (sharper CCTV camera screen) from cctv_net.s.

Public tracker idea #1499 ("128x128 -> 256x256"); study: part 06 of the notes. Chosen size:
512 x 512 (4 times finer, negligible cost).

1. assembles the grafts (clang -arch x86_64) with TAILLE = 512;
2. links them at address 0x100061800, in the dead code of ImGui::ShowDemoWindow, with the mini
   linker of generer_helicos_ascenseur.py;
3. replaces 4 places in the game with a jump to the grafts (each graft replays the original code
   when the screen is not the CCTV one);
4. writes outil/modules_en_reserve/cctv_net.py and its copy in outil/modules/.

The "before" bytes are read from the rebuilt original executable (sauvegarde/build_mac_origine).
Usage: python3 outil/generateurs/generer_cctv_net.py
"""
import hashlib, os, shutil, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import generer_helicos_ascenseur as editeur

OUTIL = os.path.dirname(ICI)
SOURCE = os.path.join(ICI, "cctv_net.s")
ORIGINE = os.path.join(os.path.dirname(OUTIL), "sauvegarde", "build_mac_origine")
RESERVE = os.path.join(OUTIL, "modules_en_reserve")
MODULES = os.path.join(OUTIL, "modules")
MD5_ORIGINE = "b0107170ddaf0245cbfee8a2d876aeb6"
BASE_FICHIER = 0x100000000

TAILLE = 512                      # side of the CCTV screen image, in points (original game: 128)
COTE_INTERFACE = 128.0            # units of the screen's Lua interface (type 0), unchanged

# dead code of ImGui::ShowDemoWindow (0x10005af39..0x100061c00); already taken: 0x10005af40..0x10005c4e0
# (helicos_ascenseur, in reserve, and the area planned for "cancel the ascent"), 0x100061a00..0x100061aa5
# (ecriture_releve), 0x100061b80..0x100061b9c (helicos_pres_ascenseur)
ZONE_DEBUT, ZONE_FIN = 0x100061800, 0x100061a00

JEU = {
    "g_ret_a": 0x1000ad77c,       # create_lite: movq 0xc8(%rbx), %rdi (after the size is chosen)
    "g_tab_haut": 0x1028b1470,    # heights per screen type (u32): 128,128,256,256,192,32
    "g_tab_larg": 0x1028b1488,    # widths per screen type (u32): 128,256,512,256,256,64
    "g_ret_b": 0x10021ce85,       # render_screen: movl $0x2, (%rbx) (interface camera)
    "g_128": 0x10286988c,         # 128.0 (default interface size, tick_screens)
    "g_echelle": 0x102a2a864,     # ShowExampleAppSimpleOverlay(bool*)::corner (__bss, 4 bytes, dead code only)
    "g_ret_c": 0x10015e6a8,       # element_clip::render: callq glScissor
    "g_demi": 0x10286974c,        # 0.5
    "g_ret_d": 0x10021cf18,       # render_screen: callq glEnable(0xb44) after the interface
}

# (address, original bytes, entry point, comment)
BRANCHEMENTS = [
    (0x1000ad74f, "486344086041b98000000041b8800000004883f8057716488d0d033d8002448b0c81488d0d103d8002448b0481",
     "_cctv_a", "create_lite: size of the screen image (type -> tables)"),
    (0x10021ce70, "418b4e200f57c0f3480f2ac1418b4e24f3480f2ad1",
     "_cctv_b", "render_screen: width / height of the interface camera"),
    (0x10015e662, "f30f1005e2b07002f30f104f14f30f58c8660f3a0ac909f30f2cc9f30f584710660f3a0ac009f30f2cd00f57c0"
                  "660f3a0a470c09f30f2cf00f57c0660f3a0a470809f30f2cf8",
     "_cctv_c", "c_ui::element_clip::render: computation of the glScissor rectangle"),
    (0x10021cf13, "bf440b0000", "_cctv_d", "render_screen: movl $0xb44, %edi after the interface"),
]

CONSTANTES = [  # (address, format, expected values)
    (0x1028b1470, "<6I", (128, 128, 256, 256, 192, 32)),
    (0x1028b1488, "<6I", (128, 256, 512, 256, 256, 64)),
    (0x10286988c, "<f", (COTE_INTERFACE,)),
    (0x10286974c, "<f", (0.5,)),
]

DOC = """Sharper CCTV camera screen (screen_veh_top_r, scripts/screen_cctv.lua): %d x %d image instead of 128 x 128.

GENERATED FILE by outil/generateurs/generer_cctv_net.py from cctv_net.s (do not edit by hand).
Public tracker idea #1499; study: part 06 of the notes; chosen size: 512.
Only the screen whose script is screen_cctv.lua changes (the 34 other 128 x 128 screens stay original).
The frame, texts and buttons keep the same size: the interface stays at 128 units, drawn %d times
larger, and the window clipping (glScissor) follows the same scale. Four places in the game jump to
code added in the dead code of ImGui::ShowDemoWindow (create_lite, render_screen x 2, element_clip);
the scale is kept in a memory cell that only this dead code used (0x102a2a864).""" % (TAILLE, TAILLE, TAILLE // 128)


def assembler(taille, dossier, source=SOURCE):
    if taille % 128 or not 128 < taille <= 4096:
        raise editeur.Erreur("unexpected size: %r" % taille)
    echelle = struct.unpack("<I", struct.pack("<f", taille / COTE_INTERFACE))[0]
    chemin = os.path.join(dossier, "cctv_net.s")
    open(chemin, "w").write(".set TAILLE, %d\n.set ECHELLE, 0x%08x\n" % (taille, echelle) + open(source).read())
    objet = os.path.join(dossier, "cctv_net.o")
    r = subprocess.run(["clang", "-arch", "x86_64", "-c", "-o", objet, chemin], capture_output=True, text=True)
    if r.returncode:
        raise editeur.Erreur("assembly: " + r.stderr)
    return objet


def generer(programme, dossier, taille=TAILLE):
    for va, fmt, attendu in CONSTANTES:
        if struct.unpack_from(fmt, programme, va - BASE_FICHIER) != attendu:
            raise editeur.Erreur("unexpected constant at %#x" % va)
    objet = assembler(taille, dossier)
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
                  "added code (%d bytes) in the dead code of ImGui::ShowDemoWindow" % len(image))]
    for va, attendu, point, commentaire in BRANCHEMENTS:
        o = va - BASE_FICHIER
        n = len(attendu) // 2
        if programme[o:o + n].hex() != attendu:
            raise editeur.Erreur("unexpected original bytes at %#x" % va)
        saut = b"\xe9" + struct.pack("<i", points[point] - (va + 5)) + b"\x90" * (n - 5)
        retouches.append((va, attendu, saut.hex(), "%s -> jmp %s (%#x)" % (commentaire, point, points[point])))
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
    chemin = os.path.join(RESERVE, "cctv_net.py")
    editeur.ecrire_module(chemin, "cctv_net", "Sharper CCTV camera screen (%d x %d)" % (TAILLE, TAILLE),
                          DOC, retouches, md5_modifie)
    shutil.copyfile(chemin, os.path.join(MODULES, "cctv_net.py"))
    print("cctv_net: %d bytes of code, %d links, md5 with this module alone %s" % (taille, len(relocs), md5_modifie))
    for p, a in sorted(points.items(), key=lambda x: x[1]):
        print("    %-8s %#x" % (p, a))
    for p, cible, nom in relocs:
        print("    link %#x -> %#x (%s)" % (p, cible, nom))
    print("    -> outil/modules_en_reserve/cctv_net.py (+ copy in outil/modules/)")


if __name__ == "__main__":
    try:
        main()
    except editeur.Erreur as e:
        sys.exit("ERROR: %s" % e)
