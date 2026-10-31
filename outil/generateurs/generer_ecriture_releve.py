#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere le module « ecriture_releve » a partir de ecriture_releve.s.

Le print() de Lua ecrit alors dans ~/Library/Application Support/Carrier Command 2/releve_cc2.txt au lieu
de la sortie standard (perdue quand Steam lance le jeu). Sert au releve des performances (module « releve »,
library_custom_5.lua) et aux courbes du lag (outil/courbes/faire_courbes.py).

1. assemble la greffe (clang -arch x86_64) ;
2. la relie a l'adresse 0x100061a00, dans le code mort de ImGui::ShowDemoWindow, avec le mini editeur de
   liens de generer_helicos_ascenseur.py ;
3. ecrit outil/modules_en_reserve/ecriture_releve.py et sa copie dans outil/modules/.

Les octets « avant » sont lus dans le programme d'origine reconstruit (sauvegarde/build_mac_origine).
Usage : python3 outil/generateurs/generer_ecriture_releve.py
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
CHEMIN_RELEVE = "/Users/UTILISATEUR/Library/Application Support/Carrier Command 2/releve_cc2.txt"

# fin du code mort de ImGui::ShowDemoWindow (0x10005af39..0x100061c00) ; deja pris : 0x10005af40..0x10005c4e0
# (helicos_ascenseur, en reserve) et 0x100061b80..0x100061b9c (helicos_pres_ascenseur)
ZONE_DEBUT, ZONE_FIN = 0x100061a00, 0x100061b80

JEU = {
    "_g_fopen": 0x102867e78,          # stub _fopen
    "_g_got_stdoutp": 0x10299dff0,    # entree de la GOT pour ___stdoutp (contient &__stdoutp)
    "_g_case": 0x102a2a828,           # guard variable for ShowExampleAppLog(bool*)::log (__bss, 8 o, code mort seulement)
}

BRANCHEMENTS = [
    (0x10283aed0, "4c8b2519311600", "_rv_r12", "movq GOT(__stdoutp), %r12 (luaB_print, avant les arguments)"),
    (0x10283af78, "488b1d71301600", "_rv_rbx", "movq GOT(__stdoutp), %rbx (luaB_print, \"\\n\" final et fflush)"),
]

DOC = """Ecriture du releve : le print() de Lua ecrit dans un fichier au lieu de la sortie standard.

FICHIER GENERE par outil/generateurs/generer_ecriture_releve.py a partir de ecriture_releve.s
(ne pas modifier a la main). Demande du moddeur le 24/10/2026 (courbes du lag, regardees apres la partie).
Quand Steam lance le jeu, ce que les scripts Lua ecrivent avec print() est perdu. Ici, au premier print(),
le jeu ouvre (en ajout) %s
et y ecrit tout ce que print() ecrit (si l'ouverture echoue : sortie standard, comme avant).
Deux instructions de luaB_print (0x10283aed0 et 0x10283af78) appellent du code ajoute (une soixantaine d'octets,
plus le chemin du fichier) dans le code mort de ImGui::ShowDemoWindow ; le FILE* est garde dans une case que seul
ce code mort utilisait.
Sans le module « releve » (library_custom_5.lua), seuls les print() des mods arrivent dans le fichier.""" % CHEMIN_RELEVE


def assembler(chemin_releve, dossier):
    source = os.path.join(dossier, "ecriture_releve.s")
    texte = open(SOURCE).read()
    if "__CHEMIN__" not in texte or '"' in chemin_releve or "\\" in chemin_releve:
        raise editeur.Erreur("chemin du releve inutilisable")
    open(source, "w").write(texte.replace("__CHEMIN__", chemin_releve))
    objet = os.path.join(dossier, "ecriture_releve.o")
    r = subprocess.run(["clang", "-arch", "x86_64", "-c", "-o", objet, source], capture_output=True, text=True)
    if r.returncode:
        raise editeur.Erreur("assemblage : " + r.stderr)
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
        raise editeur.Erreur("la greffe depasse la zone libre")
    off = ZONE_DEBUT - BASE_FICHIER
    retouches = [(ZONE_DEBUT, programme[off:off + len(image)].hex(), image.hex(),
                  "code ajoute (%d octets, dont le chemin du fichier) dans le code mort de ImGui::ShowDemoWindow" % len(image))]
    for va, attendu, point, commentaire in BRANCHEMENTS:
        o = va - BASE_FICHIER
        n = len(attendu) // 2
        if programme[o:o + n].hex() != attendu:
            raise editeur.Erreur("octets d'origine inattendus a %#x" % va)
        appel = b"\xe8" + struct.pack("<i", points[point] - (va + 5)) + b"\x66\x90"
        retouches.append((va, attendu, appel.hex(), "%s -> call %s (%#x)" % (commentaire, point, points[point])))
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
    chemin = os.path.join(RESERVE, "ecriture_releve.py")
    editeur.ecrire_module(chemin, "ecriture_releve", "Releve : print() ecrit dans un fichier (courbes du lag)",
                          DOC, retouches, md5_modifie)
    shutil.copyfile(chemin, os.path.join(MODULES, "ecriture_releve.py"))
    print("ecriture_releve : %d octets de code, %d liens, md5 avec ce module seul %s" % (taille, len(relocs), md5_modifie))
    for p, a in sorted(points.items(), key=lambda x: x[1]):
        print("    %-10s %#x" % (p, a))
    for p, cible, nom in relocs:
        print("    lien %#x -> %#x (%s)" % (p, cible, nom))
    print("    -> outil/modules_en_reserve/ecriture_releve.py (+ copie dans outil/modules/)")


if __name__ == "__main__":
    try:
        main()
    except editeur.Erreur as e:
        sys.exit("ERREUR : %s" % e)
