#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere le module « cctv_net » (ecran des cameras CCTV plus net) a partir de cctv_net.s.

Demande du moddeur le 25/10/2026 (idee n° 1499 du site de Geometa, « 128x128 -> 256x256 ») ; etude :
etudes/cctv_net.md. Il a choisi 512 x 512 (4 fois plus fin, cout negligeable).

1. assemble les greffes (clang -arch x86_64) avec TAILLE = 512 ;
2. les relie a l'adresse 0x100061800, dans le code mort de ImGui::ShowDemoWindow, avec le mini editeur de
   liens de generer_helicos_ascenseur.py ;
3. remplace 4 endroits du jeu par un saut vers les greffes (chaque greffe rejoue le code d'origine quand
   l'ecran n'est pas le CCTV) ;
4. ecrit outil/modules_en_reserve/cctv_net.py et sa copie dans outil/modules/.

Les octets « avant » sont lus dans le programme d'origine reconstruit (sauvegarde/build_mac_origine).
Usage : python3 outil/generateurs/generer_cctv_net.py
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

TAILLE = 512                      # cote de l'image de l'ecran CCTV, en points (jeu d'origine : 128)
COTE_INTERFACE = 128.0            # unites de l'interface Lua de l'ecran (type 0), inchangees

# code mort de ImGui::ShowDemoWindow (0x10005af39..0x100061c00) ; deja pris : 0x10005af40..0x10005c4e0
# (helicos_ascenseur, en reserve, et zone prevue pour « annuler la montee »), 0x100061a00..0x100061aa5
# (ecriture_releve), 0x100061b80..0x100061b9c (helicos_pres_ascenseur)
ZONE_DEBUT, ZONE_FIN = 0x100061800, 0x100061a00

JEU = {
    "g_ret_a": 0x1000ad77c,       # create_lite : movq 0xc8(%rbx), %rdi (apres le choix de la taille)
    "g_tab_haut": 0x1028b1470,    # hauteurs par type d'ecran (u32) : 128,128,256,256,192,32
    "g_tab_larg": 0x1028b1488,    # largeurs par type d'ecran (u32) : 128,256,512,256,256,64
    "g_ret_b": 0x10021ce85,       # render_screen : movl $0x2, (%rbx) (camera de l'interface)
    "g_128": 0x10286988c,         # 128.0 (taille par defaut de l'interface, tick_screens)
    "g_echelle": 0x102a2a864,     # ShowExampleAppSimpleOverlay(bool*)::corner (__bss, 4 o, code mort seulement)
    "g_ret_c": 0x10015e6a8,       # element_clip::render : callq glScissor
    "g_demi": 0x10286974c,        # 0.5
    "g_ret_d": 0x10021cf18,       # render_screen : callq glEnable(0xb44) apres l'interface
}

# (adresse, octets d'origine, point d'entree, commentaire)
BRANCHEMENTS = [
    (0x1000ad74f, "486344086041b98000000041b8800000004883f8057716488d0d033d8002448b0c81488d0d103d8002448b0481",
     "_cctv_a", "create_lite : taille de l'image de l'ecran (type -> tables)"),
    (0x10021ce70, "418b4e200f57c0f3480f2ac1418b4e24f3480f2ad1",
     "_cctv_b", "render_screen : largeur / hauteur de la camera de l'interface"),
    (0x10015e662, "f30f1005e2b07002f30f104f14f30f58c8660f3a0ac909f30f2cc9f30f584710660f3a0ac009f30f2cd00f57c0"
                  "660f3a0a470c09f30f2cf00f57c0660f3a0a470809f30f2cf8",
     "_cctv_c", "c_ui::element_clip::render : calcul du rectangle de glScissor"),
    (0x10021cf13, "bf440b0000", "_cctv_d", "render_screen : movl $0xb44, %edi apres l'interface"),
]

CONSTANTES = [  # (adresse, format, valeurs attendues)
    (0x1028b1470, "<6I", (128, 128, 256, 256, 192, 32)),
    (0x1028b1488, "<6I", (128, 256, 512, 256, 256, 64)),
    (0x10286988c, "<f", (COTE_INTERFACE,)),
    (0x10286974c, "<f", (0.5,)),
]

DOC = """Ecran des cameras CCTV (screen_veh_top_r, scripts/screen_cctv.lua) plus net : image %d x %d au lieu de 128 x 128.

FICHIER GENERE par outil/generateurs/generer_cctv_net.py a partir de cctv_net.s (ne pas modifier a la main).
Demande du moddeur le 25/10/2026 (idee n° 1499 de Geometa) ; etude : etudes/cctv_net.md ; il a choisi 512.
Seul l'ecran dont le script est screen_cctv.lua change (les 34 autres ecrans de 128 x 128 restent d'origine).
Le cadre, les textes et les boutons gardent la meme taille : l'interface reste en 128 unites, dessinee %d fois
plus grande, et le decoupage des fenetres (glScissor) suit la meme echelle. Quatre endroits du jeu sautent vers
du code ajoute dans le code mort de ImGui::ShowDemoWindow (create_lite, render_screen x 2, element_clip) ;
l'echelle est gardee dans une case que seul ce code mort utilisait (0x102a2a864).""" % (TAILLE, TAILLE, TAILLE // 128)


def assembler(taille, dossier, source=SOURCE):
    if taille % 128 or not 128 < taille <= 4096:
        raise editeur.Erreur("taille inattendue : %r" % taille)
    echelle = struct.unpack("<I", struct.pack("<f", taille / COTE_INTERFACE))[0]
    chemin = os.path.join(dossier, "cctv_net.s")
    open(chemin, "w").write(".set TAILLE, %d\n.set ECHELLE, 0x%08x\n" % (taille, echelle) + open(source).read())
    objet = os.path.join(dossier, "cctv_net.o")
    r = subprocess.run(["clang", "-arch", "x86_64", "-c", "-o", objet, chemin], capture_output=True, text=True)
    if r.returncode:
        raise editeur.Erreur("assemblage : " + r.stderr)
    return objet


def generer(programme, dossier, taille=TAILLE):
    for va, fmt, attendu in CONSTANTES:
        if struct.unpack_from(fmt, programme, va - BASE_FICHIER) != attendu:
            raise editeur.Erreur("constante inattendue a %#x" % va)
    objet = assembler(taille, dossier)
    ancien = editeur.JEU
    editeur.JEU = JEU
    try:
        image, points, relocs = editeur.relier(open(objet, "rb").read(), ZONE_DEBUT)
    finally:
        editeur.JEU = ancien
    if ZONE_DEBUT + len(image) > ZONE_FIN:
        raise editeur.Erreur("la greffe depasse la zone libre")
    off = ZONE_DEBUT - BASE_FICHIER
    retouches = [(ZONE_DEBUT, programme[off:off + len(image)].hex(), image.hex(),
                  "code ajoute (%d octets) dans le code mort de ImGui::ShowDemoWindow" % len(image))]
    for va, attendu, point, commentaire in BRANCHEMENTS:
        o = va - BASE_FICHIER
        n = len(attendu) // 2
        if programme[o:o + n].hex() != attendu:
            raise editeur.Erreur("octets d'origine inattendus a %#x" % va)
        saut = b"\xe9" + struct.pack("<i", points[point] - (va + 5)) + b"\x90" * (n - 5)
        retouches.append((va, attendu, saut.hex(), "%s -> jmp %s (%#x)" % (commentaire, point, points[point])))
    modifie = bytearray(programme)
    for va, avant, apres, _ in retouches:
        modifie[va - BASE_FICHIER:va - BASE_FICHIER + len(avant) // 2] = bytes.fromhex(apres)
    return retouches, hashlib.md5(modifie).hexdigest(), points, relocs, len(image)


def main():
    programme = open(ORIGINE, "rb").read()
    if hashlib.md5(programme).hexdigest() != MD5_ORIGINE:
        raise editeur.Erreur("sauvegarde/build_mac_origine n'est pas le programme d'origine attendu")
    with tempfile.TemporaryDirectory(prefix="greffe_cc2_") as dossier:
        retouches, md5_modifie, points, relocs, taille = generer(programme, dossier)
    chemin = os.path.join(RESERVE, "cctv_net.py")
    editeur.ecrire_module(chemin, "cctv_net", "Ecran des cameras CCTV plus net (%d x %d)" % (TAILLE, TAILLE),
                          DOC, retouches, md5_modifie)
    shutil.copyfile(chemin, os.path.join(MODULES, "cctv_net.py"))
    print("cctv_net : %d octets de code, %d liens, md5 avec ce module seul %s" % (taille, len(relocs), md5_modifie))
    for p, a in sorted(points.items(), key=lambda x: x[1]):
        print("    %-8s %#x" % (p, a))
    for p, cible, nom in relocs:
        print("    lien %#x -> %#x (%s)" % (p, cible, nom))
    print("    -> outil/modules_en_reserve/cctv_net.py (+ copie dans outil/modules/)")


if __name__ == "__main__":
    try:
        main()
    except editeur.Erreur as e:
        sys.exit("ERREUR : %s" % e)
