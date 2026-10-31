#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere le module « vitesse de l'escadrille » (ECO / NORMAL / FLANK) a partir de vitesse_escadrille.c.

1. compile la greffe (clang -arch x86_64, memes options que les autres greffes, CHEMIN = fichier du mode) ;
2. la relie a l'adresse ZONE (code mort de ImGui::ShowDemoWindow), avec l'editeur de liens de
   generer_helicos_ascenseur.py (table JEU propre a ce module) ;
3. ecrit outil/modules/vitesse_escadrille.py : la greffe, le branchement dans tick_control des avions et
   l'entree « dofile » de base_funcs qui devient « cc2_vitesse ».

Les octets « avant » sont lus dans le programme d'origine reconstruit (sauvegarde/build_mac_origine).
Etude : etudes/ia_vitesse.md. Usage : python3 outil/generateurs/generer_vitesse_escadrille.py
"""
import hashlib, os, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import generer_helicos_ascenseur as G

OUTIL = os.path.dirname(ICI)
SOURCE = os.path.join(ICI, "vitesse_escadrille.c")
MODULE = os.path.join(OUTIL, "modules", "vitesse_escadrille.py")
ZONE, ZONE_TAILLE = 0x10005d000, 0x400       # libre le 25/10 : 0x10005c4e0..0x100061200
CHEMIN = os.path.expanduser("~/Library/Application Support/Carrier Command 2/vitesse_escadrille.txt")

JEU = {
    "_g_lua_gettop": 0x1028278dc,
    "_g_lua_tointegerx": 0x102827dc4,
    "_g_lua_pushinteger": 0x10282801b,
    "_g_fopen": 0x102867e78,          # stubs de la libc
    "_g_fgetc": 0x102867e60,
    "_g_fputs": 0x102867e84,
    "_g_fclose": 0x102867e42,
    "_g_vit_modes": 0x1029e5680,      # fin de ShowDemoWindowWidgets()::text (__data, zeros, code mort)
    "_g_vit_etat": 0x1029e5690,
    "_g_ret_2b8e": 0x1001c2b8e,       # tick_control : movl 0x318(%r13), %esi
}

# c_vehicle_server_wing::tick_control, 0x1001c2b4b..0x1001c2b8e (aucun saut n'y entre, sauf a la fin)
BRANCHEMENT = (0x1001c2b4b,
               "f30f1003" "0f28c8" "f30f5f0d966f6a02" "f30f5d0dca6f6a02" "f3410f118dc8020000"
               "4183bd900000000a" "7519" "f30f5f05b36f6a02" "f30f5d05a76f6a02" "f3410f1185c8020000",
               "_vit_plancher", "vitesse visee des avions (mode 0) : bornes [48|72, 144] -> plancher selon le mode")

BASE_FUNCS_DOFILE = 0x1029dd310       # { "dofile", luaB_dofile } dans base_funcs (__DATA,__const)
DOFILE = (0x10297970e, 0x10283aa8c)   # verifie a la generation

DOC = """Vitesse de croisiere des avions sous IA choisie par l'ecran (ECO / NORMAL / FLANK).

FICHIER GENERE par outil/generateurs/generer_vitesse_escadrille.py a partir de vitesse_escadrille.c (ne pas
modifier a la main). Etude : etudes/ia_vitesse.md. Demande du moddeur le 25/10/2026.
En vol vers un point, l'IA des avions vise la vitesse plancher : 48 m/s (Albatros) ou 72 m/s (Manta). Ici le
plancher depend du mode choisi par l'equipe : ECO = jeu d'origine, NORMAL = 61 / 91 m/s (environ 80 % de
puissance, estimation), FLANK = 144 m/s (plein gaz). Equipes pilotees par l'IA (ennemis) : jeu d'origine.
Le mode est regle par la fonction Lua cc2_vitesse(equipe [, mode]) (a la place de dofile, inutilise) que
dessine le module « vitesse_boutons » ; le dernier mode est garde dans
~/Library/Application Support/Carrier Command 2/vitesse_escadrille.txt.
Sans le module « vitesse_boutons », rien ne choisit de mode : les avions volent comme dans le jeu d'origine."""


def compiler_et_relier(dossier, chemin):
    objet = os.path.join(dossier, "vitesse_escadrille.o")
    r = subprocess.run(["clang"] + G.DRAPEAUX + ['-DCHEMIN="%s"' % chemin, "-o", objet, SOURCE],
                       capture_output=True, text=True)
    if r.returncode:
        raise G.Erreur("compilation : " + r.stderr)
    ancien = G.JEU
    G.JEU = JEU
    try:
        image, points, relocs = G.relier(open(objet, "rb").read(), ZONE)
    finally:
        G.JEU = ancien
    if len(image) > ZONE_TAILLE or not G.ZONE_DEBUT <= ZONE < ZONE + len(image) <= G.ZONE_FIN:
        raise G.Erreur("la greffe depasse sa place (%d octets)" % len(image))
    return image, points, relocs


def generer(programme, dossier, chemin=CHEMIN):
    image, points, relocs = compiler_et_relier(dossier, chemin)
    off = ZONE - G.BASE_FICHIER
    retouches = [(ZONE, programme[off:off + len(image)].hex(), image.hex(),
                  "code ajoute (%d octets) a la place de ImGui::ShowDemoWindow, jamais appele" % len(image))]

    va, attendu, point, commentaire = BRANCHEMENT
    o2 = va - G.BASE_FICHIER
    n = len(attendu) // 2
    if programme[o2:o2 + n].hex() != attendu:
        raise G.Erreur("octets d'origine inattendus a %#x" % va)
    saut = b"\xe9" + struct.pack("<i", points[point] - (va + 5))
    retouches.append((va, attendu, (saut + b"\xcc" * (n - 5)).hex(),
                      "%s -> jmp %s (%#x)" % (commentaire, point, points[point])))

    o3 = BASE_FUNCS_DOFILE - G.BASE_FICHIER
    nom, fonction = struct.unpack_from("<QQ", programme, o3)
    if (nom, fonction) != DOFILE or programme[nom - G.BASE_FICHIER:nom - G.BASE_FICHIER + 7] != b"dofile\0":
        raise G.Erreur("base_funcs : entree dofile inattendue a %#x" % BASE_FUNCS_DOFILE)
    retouches.append((BASE_FUNCS_DOFILE, programme[o3:o3 + 16].hex(),
                      struct.pack("<QQ", points["_vit_nom_lua"], points["_vit_lua"]).hex(),
                      "base_funcs : { \"dofile\", luaB_dofile } -> { \"cc2_vitesse\", vit_lua }"))

    modifie = bytearray(programme)
    for va, avant, apres, _ in retouches:
        modifie[va - G.BASE_FICHIER:va - G.BASE_FICHIER + len(avant) // 2] = bytes.fromhex(apres)
    return retouches, hashlib.md5(modifie).hexdigest(), points, relocs, len(image)


def main():
    programme = open(G.ORIGINE, "rb").read()
    if hashlib.md5(programme).hexdigest() != G.MD5_ORIGINE:
        raise G.Erreur("sauvegarde/build_mac_origine n'est pas le programme d'origine attendu")
    with tempfile.TemporaryDirectory(prefix="greffe_cc2_") as dossier:
        retouches, md5_modifie, points, relocs, taille = generer(programme, dossier)
    G.ecrire_module(MODULE, "vitesse_escadrille", "Vitesse de l'escadrille (ECO / NORMAL / FLANK) : programme",
                    DOC, retouches, md5_modifie)
    print("vitesse_escadrille : %d octets de code a %#x, %d liens, md5 avec ce module seul %s"
          % (taille, ZONE, len(relocs), md5_modifie))
    for p, a in sorted(points.items(), key=lambda x: x[1]):
        print("    %-16s %#x" % (p, a))
    for p, cible, nom in relocs:
        if not ZONE <= cible < ZONE + taille:
            print("    lien %#x -> %#x %s" % (p, cible, nom))
    print("    -> " + os.path.relpath(MODULE, os.path.dirname(OUTIL)))


if __name__ == "__main__":
    try:
        main()
    except G.Erreur as e:
        sys.exit("ERREUR : %s" % e)
