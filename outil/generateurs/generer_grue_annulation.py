#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere le module « annuler la sortie d'un avion deja pris par la grue » a partir de grue_annulation.c.

1. compile la greffe (clang -arch x86_64, memes options que les autres greffes) ;
2. la relie a l'adresse ZONE (code mort de ImGui::ShowDemoWindow), avec l'editeur de liens de
   generer_helicos_ascenseur.py (memes relocations, table JEU propre a ce module) ;
3. ecrit outil/modules/grue_annulation.py : 1 retouche « imm » pour le code ajoute + 2 branchements.

Les octets « avant » sont lus dans le programme d'origine reconstruit (sauvegarde/build_mac_origine).
Etude : etudes/annuler_montee.md. Usage : python3 outil/generateurs/generer_grue_annulation.py
"""
import hashlib, os, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import generer_helicos_ascenseur as G

OUTIL = os.path.dirname(ICI)
SOURCE = os.path.join(ICI, "grue_annulation.c")
MODULE = os.path.join(OUTIL, "modules", "grue_annulation.py")
ZONE, ZONE_TAILLE = 0x100061200, 0x400      # libre le 25/10 : 0x100061800... = cctv (prevu), 0x100061a00... = releve

JEU = {
    "_g_push_geste": 0x10019a450,    # mm_vector<e_crane_state>::push_back()
    "_g_vider_route": 0x10009060c,   # mm_vector<c_vehicle_waypoint_data>::clear()
    "_g_reset_route": 0x10010cea4,   # c_vehicle_server::reset_waypoint_path()
    "g_ret_a8c0e": 0x1001a8c0e,      # epilogue de docking_manager_air::undock
    "g_ret_ad9b2": 0x1001ad9b2,      # suite du bloc « fin de grue » (mode lancement)
}

BRANCHEMENTS = [
    (0x1001a8c01, "4183be200200000775 03895f28".replace(" ", ""), "_ag_a",
     "undock, avion deja dans la grue/l'ascenseur/la piste : cmpl $7,0x220(%r14) ; jne ; movl %ebx,0x28(%rdi)"),
    (0x1001ad9ad, "41837e1800", "_ag_b", "fin de grue en mode lancement : cmpl $0,0x18(%r14)"),
]

DOC = """Annuler la sortie d'un avion deja pris par la grue du hangar (demande Geometa n° 20652).

FICHIER GENERE par outil/generateurs/generer_grue_annulation.py a partir de grue_annulation.c (ne pas
modifier a la main). Etude : etudes/annuler_montee.md. Demande du moddeur le 25/10/2026.
Dans le jeu d'origine, un 2e appui sur le bouton de la baie n'annule la sortie que si l'avion attend encore
dans la file ; or la grue le prend presque aussitot. Ici, un 2e appui pendant que la grue s'occupe de l'avion
le ramene a sa baie :
  - grue pas encore accrochee : elle remonte et revient au repos, l'avion n'a pas bouge ;
  - avion accroche, pas encore tourne : la grue remonte, le rapporte au-dessus de sa baie, le pose, revient.
Trop tard (rien ne change, comme avant) : avion en train d'etre retourne ou deja lache au-dessus de
l'ascenseur, sur l'ascenseur, sur le pont. L'avion redevient « au hangar » (route effacee, comme
l'annulation du jeu). Mode lancement seulement ; l'IA ennemie ne lance que des appareils au hangar.
Code ajoute dans le code mort de ImGui::ShowDemoWindow + 2 branchements (docking_manager_air::undock et
::update). Retirer le module ne bloque rien : un avion en cours de retour serait alors passe a l'ascenseur."""


def generer(programme, dossier):
    objet = os.path.join(dossier, "grue_annulation.o")
    r = subprocess.run(["clang"] + G.DRAPEAUX + ["-o", objet, SOURCE], capture_output=True, text=True)
    if r.returncode:
        raise G.Erreur("compilation : " + r.stderr)
    ancien = G.JEU
    G.JEU = JEU                                  # l'editeur de liens lit la table JEU de son module
    try:
        image, points, relocs = G.relier(open(objet, "rb").read(), ZONE)
    finally:
        G.JEU = ancien
    if len(image) > ZONE_TAILLE or not G.ZONE_DEBUT <= ZONE < ZONE + len(image) <= G.ZONE_FIN:
        raise G.Erreur("la greffe depasse sa place (%d octets)" % len(image))
    off = ZONE - G.BASE_FICHIER
    retouches = [(ZONE, programme[off:off + len(image)].hex(), image.hex(),
                  "code ajoute (%d octets) a la place de ImGui::ShowDemoWindow, jamais appele" % len(image))]
    for va, attendu, point, commentaire in BRANCHEMENTS:
        o2 = va - G.BASE_FICHIER
        n = len(attendu) // 2
        if programme[o2:o2 + n].hex() != attendu:
            raise G.Erreur("octets d'origine inattendus a %#x" % va)
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
        raise G.Erreur("sauvegarde/build_mac_origine n'est pas le programme d'origine attendu")
    with tempfile.TemporaryDirectory(prefix="greffe_cc2_") as dossier:
        retouches, md5_modifie, points, relocs, taille = generer(programme, dossier)
    G.ecrire_module(MODULE, "grue_annulation", "Grue : annuler la sortie d'un avion deja pris (2e appui)",
                    DOC, retouches, md5_modifie)
    print("grue_annulation : %d octets de code a %#x, %d liens, md5 avec ce module seul %s"
          % (taille, ZONE, len(relocs), md5_modifie))
    for p, a in sorted(points.items(), key=lambda x: x[1]):
        print("    %-12s %#x" % (p, a))
    for p, cible, nom in relocs:
        if not ZONE <= cible < ZONE + taille:
            print("    lien %#x -> %#x %s" % (p, cible, nom))
    print("    -> " + os.path.relpath(MODULE, os.path.dirname(OUTIL)))


if __name__ == "__main__":
    try:
        main()
    except G.Erreur as e:
        sys.exit("ERREUR : %s" % e)
