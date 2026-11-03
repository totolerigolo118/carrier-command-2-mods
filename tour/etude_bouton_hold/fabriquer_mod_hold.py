#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fabrique, HORS JEU, un mod qui ajoute des COPIES du bouton rouge « Hold On Deck ».

Le bouton d'origine (`vehicle_control_air_hold`, type 18, panneau 0 = console des avions) reste
là où il est. Le mod en ajoute :
  - copie A : sur le panneau 8 (moteur), au milieu du trou entre « Démarrer » et « Arrêter » ;
  - copie B : sur le panneau 7 (direction et feux), au milieu du trou entre « Maintien de cap »
    et « Feux de navigation » ;
  - copie C : la copie B (meme nom) deplacee sur l'avant du plateau, devant le voyant des feux de
    navigation (02/11, encadre rouge du moddeur). B et C s'excluent.
Les coordonnées (tx, tz) sont celles du fichier du jeu, relatives au panneau. Le contour des
panneaux n'est PAS connu : l'emplacement est choisi au milieu d'un trou entre deux boutons qui
existent déjà (donc sûrement sur le panneau). `ty` (hauteur au-dessus du panneau) = celui des
voisins moins 1,4 mm, écart observé entre le Hold et les boutons voisins de la console des avions.

INFÉRÉ, JAMAIS ESSAYÉ EN JEU : que le moteur accepte un bouton ajouté, qu'il l'affiche et qu'il le
traite comme l'original (même type 18). Seul un essai en jeu le dit.

Ce que fait l'outil (et rien d'autre) :
  1. lit `<jeu>\\rom_0\\game_objects\\vehicle_chassis_carrier.xml` (lecture seule) ;
  2. ajoute 1 ou 2 blocs <button> juste après celui d'origine ;
  3. CONTRÔLE : XML bien formé, noms uniques, panneaux existants, et comparaison ligne à ligne :
     la seule différence avec l'original est l'insertion de 3 lignes par copie (aucune ligne
     supprimée ni modifiée) ;
  4. écrit un mod dans un dossier NEUF (jamais dans le jeu ni dans %APPDATA%) et le relit.

Il ne pose RIEN dans le jeu : la pose (une ligne dans mods.xml, fichier protégé) est une autre
étape qui demande l'accord du moddeur. Aucun réseau, aucun sous-processus.

Usage (toujours avec `python -I`) :
  python -I fabriquer_mod_hold.py fabriquer --jeu "<dossier du jeu>" --sortie <dossier NEUF> [--options AB]
  python -I fabriquer_mod_hold.py autotest
"""
import argparse
import difflib
import hashlib
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

BOUTON_ORIGINAL = "vehicle_control_air_hold"
FICHIER_RELATIF = os.path.join("rom_0", "game_objects", "vehicle_chassis_carrier.xml")
NOM_MOD = "cc2_hold_copies"

IDENTITE = ('m00="1.00000000e+00" m01="0.00000000e+00" m02="0.00000000e+00" '
            'm10="0.00000000e+00" m11="1.00000000e+00" m12="0.00000000e+00" '
            'm20="0.00000000e+00" m21="0.00000000e+00" m22="1.00000000e+00"')

COPIES = {
    "A": {"nom": BOUTON_ORIGINAL + "_copie_moteur", "panneau": 8,
          "tx": 0.0, "ty": 0.0015, "tz": 0.117},
    "B": {"nom": BOUTON_ORIGINAL + "_copie_feux", "panneau": 7,
          "tx": -0.117, "ty": 0.0011, "tz": 0.036},
    # C = la copie B deplacee (demande du moddeur, 02/11) : sur le plateau, devant le voyant des feux de navigation (encadre
    # rouge de sa capture). LU dans meshes/.../aircraft_carrier_bridge.mesh : le plateau est plat a y = 29,7607 (= le
    # panneau 7) de x -27,458 a -26,939 jusqu'a z -23,417 (tz -0,278), puis un rebord vertical de 8 cm. INFERE (camera de la
    # capture recalee sur 8 reperes, erreur 2 px) : centre de l'encadre vers tx -0,03, tz -0,24. Choisi : 5,8 cm du rebord.
    "C": {"nom": BOUTON_ORIGINAL + "_copie_feux", "panneau": 7,
          "tx": -0.025, "ty": 0.0011, "tz": -0.220},
}
EXCLUSIVES = ("B", "C")          # meme nom : une seule des deux

DESCRIPTION = (
    "Copie le bouton rouge Hold On Deck (vehicle_control_air_hold) sur le panneau moteur (copie A) "
    "et/ou sur le panneau direction et feux (copie B) du porte-avions. L original reste sur la "
    "console des avions. ATTENTION : ce mod remplace tout le fichier game_objects/"
    "vehicle_chassis_carrier.xml, il est a refaire apres chaque mise a jour du jeu, et il ne doit "
    "pas etre actif en meme temps qu un autre mod qui remplace ce fichier. Aucun code, aucun "
    "reseau. Pour le retirer : enlever la ligne cc2_hold_copies de mods.xml."
)


class ErreurMod(Exception):
    pass


def sha256_octets(donnees):
    return hashlib.sha256(donnees).hexdigest().upper()


def fmt(x):
    return "%.8e" % x


def trouver_bloc(texte):
    """Le bloc <button> d'origine (3 lignes), qui doit exister UNE seule fois."""
    motif = re.compile(
        r'^(?P<tab>[ \t]*)<button name="' + re.escape(BOUTON_ORIGINAL) + r'" [^>\r\n]*>\r\n'
        r'[ \t]*<transform [^>\r\n]*/>\r\n'
        r'[ \t]*</button>\r\n', re.MULTILINE)
    trouves = list(motif.finditer(texte))
    if len(trouves) != 1:
        raise ErreurMod("le bouton %s doit apparaitre exactement une fois (3 lignes, fins de ligne "
                        "Windows) ; trouve %d fois. Le fichier du jeu a change : relire avant "
                        "d'aller plus loin." % (BOUTON_ORIGINAL, len(trouves)))
    return trouves[0]


def fabriquer_bloc(bloc, cle):
    c = COPIES[cle]
    transform = '<transform %s tx="%s" ty="%s" tz="%s"/>' % (IDENTITE, fmt(c["tx"]), fmt(c["ty"]), fmt(c["tz"]))
    b, n1 = re.subn(r'name="' + re.escape(BOUTON_ORIGINAL) + '"', lambda m: 'name="%s"' % c["nom"], bloc, count=1)
    b, n2 = re.subn(r'button_panel_index="\d+"', lambda m: 'button_panel_index="%d"' % c["panneau"], b, count=1)
    b, n3 = re.subn(r'<transform [^>\r\n]*/>', lambda m: transform, b, count=1)
    if (n1, n2, n3) != (1, 1, 1):
        raise ErreurMod("remplacement incomplet dans le bloc copie %s : %r" % (cle, (n1, n2, n3)))
    return b


def assembler(texte, options):
    if all(c in options for c in EXCLUSIVES):
        raise ErreurMod("les copies %s portent le meme nom : une seule des deux" % " et ".join(EXCLUSIVES))
    m = trouver_bloc(texte)
    ajout = "".join(fabriquer_bloc(m.group(0), cle) for cle in options)
    return texte[:m.end()] + ajout + texte[m.end():]


def controler(original, nouveau, options):
    """Leve ErreurMod au moindre doute. Renvoie un petit compte rendu (liste de lignes)."""
    rapport = []
    # 1. XML bien formé
    try:
        racine = ET.fromstring(nouveau.encode("utf-8"))
        racine_orig = ET.fromstring(original.encode("utf-8"))
    except ET.ParseError as e:
        raise ErreurMod("XML mal forme : %s" % e)
    # 2. noms uniques, bons panneaux
    boutons = list(racine.iter("button"))
    noms = [b.get("name") for b in boutons]
    n_orig = len(list(racine_orig.iter("button")))
    if len(boutons) != n_orig + len(options):
        raise ErreurMod("nombre de boutons %d, attendu %d" % (len(boutons), n_orig + len(options)))
    if len(set(noms)) != len(noms):
        raise ErreurMod("noms de boutons en double")
    panneaux = list(racine.iter("button_panel"))
    for cle in options:
        c = COPIES[cle]
        b = next((x for x in boutons if x.get("name") == c["nom"]), None)
        if b is None:
            raise ErreurMod("copie %s absente" % cle)
        if b.get("button_panel_index") != str(c["panneau"]) or b.get("type") != "18":
            raise ErreurMod("copie %s : panneau ou type incorrect" % cle)
        if c["panneau"] >= len(panneaux):
            raise ErreurMod("le panneau %d n'existe pas (%d panneaux)" % (c["panneau"], len(panneaux)))
        rapport.append("copie %s : bouton '%s' sur le panneau %d ('%s'), type 18, tx=%s ty=%s tz=%s" % (
            cle, c["nom"], c["panneau"], panneaux[c["panneau"]].get("texture") or panneaux[c["panneau"]].get("name"),
            fmt(c["tx"]), fmt(c["ty"]), fmt(c["tz"])))
    # 3. fins de ligne : aucune ligne à fin LF seule dans le texte ajouté
    if nouveau.count("\n") != nouveau.count("\r\n"):
        raise ErreurMod("fins de ligne melangees")
    # 4. comparaison ligne à ligne : uniquement des insertions, 3 lignes par copie
    a = original.splitlines(keepends=True)
    b = nouveau.splitlines(keepends=True)
    ops = [op for op in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if op[0] != "equal"]
    if any(op[0] != "insert" for op in ops):
        raise ErreurMod("une ligne de l'original a ete modifiee ou supprimee : %r" % [op for op in ops if op[0] != "insert"])
    inserees = sum(op[4] - op[3] for op in ops)
    if inserees != 3 * len(options):
        raise ErreurMod("%d lignes inserees, attendu %d" % (inserees, 3 * len(options)))
    rapport.append("comparaison ligne a ligne : %d lignes de l'original inchangees, %d lignes ajoutees, 0 supprimee, 0 modifiee"
                   % (len(a), inserees))
    rapport.append("boutons : %d dans le jeu, %d dans le mod ; XML bien forme ; noms uniques" % (n_orig, len(boutons)))
    return rapport


def png_vignette():
    """Vignette 64x64 : disque rouge sur fond gris foncé (PNG fait à la main, sans bibliothèque)."""
    n = 64
    lignes = []
    for y in range(n):
        ligne = bytearray([0])
        for x in range(n):
            dedans = (x - 31.5) ** 2 + (y - 31.5) ** 2 <= 22 ** 2
            ligne += bytes((200, 30, 30)) if dedans else bytes((40, 40, 44))
        lignes.append(bytes(ligne))

    def morceau(typ, donnees):
        corps = typ + donnees
        return struct.pack(">I", len(donnees)) + corps + struct.pack(">I", zlib.crc32(corps) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + morceau(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
            + morceau(b"IDAT", zlib.compress(b"".join(lignes), 9)) + morceau(b"IEND", b""))


def verifier_sortie(sortie):
    bas = os.path.normcase(os.path.abspath(sortie))
    if "steamapps" in bas or "carrier command 2" in bas:
        raise ErreurMod("le dossier de sortie est dans le jeu ou dans ses donnees : refuse (la pose est une autre etape)")
    if os.path.exists(sortie) and os.listdir(sortie):
        raise ErreurMod("le dossier de sortie existe deja et n'est pas vide : donner un dossier NEUF")


def ecrire_mod(sortie, nouveau, options):
    racine_mod = os.path.join(sortie, NOM_MOD)
    dossier_xml = os.path.join(racine_mod, "content", "game_objects")
    os.makedirs(dossier_xml, exist_ok=False)
    octets_xml = nouveau.encode("utf-8")
    chemin_xml = os.path.join(dossier_xml, "vehicle_chassis_carrier.xml")
    with open(chemin_xml, "wb") as f:
        f.write(octets_xml)
    mod_xml = ('<?xml version="1.0" encoding="UTF-8"?>\r\n<data name="Hold copies" author="Yolo" '
               'description="%s">\r\n</data>\r\n' % DESCRIPTION).encode("utf-8")
    with open(os.path.join(racine_mod, "mod.xml"), "wb") as f:
        f.write(mod_xml)
    with open(os.path.join(racine_mod, "thumbnail.png"), "wb") as f:
        f.write(png_vignette())
    with open(chemin_xml, "rb") as f:
        relu = f.read()
    if relu != octets_xml:
        raise ErreurMod("la relecture du fichier ecrit ne correspond pas")
    ET.parse(chemin_xml)
    ET.parse(os.path.join(racine_mod, "mod.xml"))
    return racine_mod, sha256_octets(octets_xml)


def fabriquer(jeu, sortie, options):
    verifier_sortie(sortie)
    source = os.path.join(jeu, FICHIER_RELATIF)
    with open(source, "rb") as f:
        brut = f.read()
    try:
        original = brut.decode("utf-8")
    except UnicodeDecodeError:
        raise ErreurMod("le fichier du jeu n'est pas de l'UTF-8")
    if original.startswith("\ufeff"):
        raise ErreurMod("le fichier du jeu commence par un BOM : cas non prevu")
    nouveau = assembler(original, options)
    rapport = controler(original, nouveau, options)
    racine_mod, sha_sortie = ecrire_mod(sortie, nouveau, options)
    print("Source (lue, jamais modifiee) : %s" % source)
    print("  %d octets, sha256 %s" % (len(brut), sha256_octets(brut)))
    for ligne in rapport:
        print("  " + ligne)
    print("Mod ecrit dans : %s" % racine_mod)
    print("  content/game_objects/vehicle_chassis_carrier.xml : %d octets, sha256 %s" % (len(nouveau.encode("utf-8")), sha_sortie))
    print("RIEN n'a ete pose dans le jeu. Pose = une ligne dans mods.xml, avec l'accord du moddeur.")


# ----------------------------------------------------------------- autotest
def _xml_synthetique(nb_hold=1):
    panneaux = "".join('\t\t<button_panel name="p%d" body_index="0" texture="t%d">\r\n\t\t</button_panel>\r\n' % (i, i)
                       for i in range(9))
    autre = ('\t\t<button name="autre" display_name_loc="1" button_panel_index="8" button_cover_index="4294967295" type="3" help_tag="">\r\n'
             '\t\t\t<transform %s tx="0.00000000e+00" ty="0.00000000e+00" tz="0.00000000e+00"/>\r\n\t\t</button>\r\n' % IDENTITE)
    hold = ('\t\t<button name="%s" display_name_loc="1527" button_panel_index="0" button_cover_index="4294967295" type="18" help_tag="veh_con_button_hold_air">\r\n'
            '\t\t\t<transform %s tx="-7.55367503e-02" ty="6.21786108e-04" tz="-1.95847884e-01"/>\r\n\t\t</button>\r\n'
            % (BOUTON_ORIGINAL, IDENTITE)) * nb_hold
    return ('<?xml version="1.0" encoding="UTF-8"?>\r\n<vehicle>\r\n\t<button_panels>\r\n%s\t</button_panels>\r\n\t<buttons>\r\n%s%s\t</buttons>\r\n</vehicle>\r\n'
            % (panneaux, autre, hold))


def autotest():
    echecs = []

    def verif(nom, condition):
        print(("OK     " if condition else "ECHEC  ") + nom)
        if not condition:
            echecs.append(nom)

    def leve(fonction, *args):
        try:
            fonction(*args)
        except ErreurMod:
            return True
        return False

    base = _xml_synthetique()
    for options in ("A", "B", "AB", "C", "AC"):
        nouveau = assembler(base, options)
        verif("options %s : controle passe" % options, bool(controler(base, nouveau, options)))
        fin = trouver_bloc(base).end()
        taille_ajout = len(nouveau) - len(base)
        verif("options %s : sans l'insertion, on retrouve l'original octet pour octet" % options,
              nouveau[:fin] + nouveau[fin + taille_ajout:] == base)
    verif("bloc d'origine absent : refuse", leve(assembler, base.replace(BOUTON_ORIGINAL, "autre_nom"), "AB"))
    verif("bloc d'origine en double : refuse", leve(assembler, _xml_synthetique(2), "AB"))
    nouveau = assembler(base, "AB")
    verif("une ligne de l'original modifiee : detectee", leve(controler, base, nouveau.replace('texture="t3"', 'texture="zzz"'), "AB"))
    verif("une ligne de l'original supprimee : detectee", leve(controler, base, nouveau.replace("\t\t<button_panel name=\"p3\" body_index=\"0\" texture=\"t3\">\r\n", ""), "AB"))
    verif("XML casse : detecte", leve(controler, base, nouveau.replace("</vehicle>", ""), "AB"))
    verif("nom en double : detecte", leve(controler, base, nouveau.replace(COPIES["B"]["nom"], COPIES["A"]["nom"]), "AB"))
    verif("sortie dans le dossier du jeu : refusee", leve(verifier_sortie, r"C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2\x"))
    verif("sortie dans %APPDATA%\\Carrier Command 2 : refusee", leve(verifier_sortie, r"C:\Users\x\AppData\Roaming\Carrier Command 2\mods\y"))
    verif("copie A au bon endroit (panneau 8, type 18)", 'button_panel_index="8" button_cover_index="4294967295" type="18"' in assembler(base, "A"))
    verif("copie B au bon endroit (panneau 7, type 18)", 'button_panel_index="7" button_cover_index="4294967295" type="18"' in assembler(base, "B"))
    verif("copies B et C ensemble (meme nom) : refuse", leve(assembler, base, "BC"))
    ab, ac = assembler(base, "AB"), assembler(base, "AC")
    diff = [op for op in difflib.SequenceMatcher(None, ab.splitlines(True), ac.splitlines(True), autojunk=False).get_opcodes() if op[0] != "equal"]
    verif("C = B deplacee : une seule ligne differe, la position (transform) de la copie aux feux",
          len(diff) == 1 and diff[0][0] == "replace" and diff[0][2] - diff[0][1] == 1 and diff[0][4] - diff[0][3] == 1
          and 'tz="-2.20000000e-01"' in ac.splitlines(True)[diff[0][3]] and "<transform " in ac.splitlines(True)[diff[0][3]])
    verif("vignette PNG valide (signature)", png_vignette()[:8] == b"\x89PNG\r\n\x1a\n")
    print("%d echec(s)" % len(echecs))
    return 0 if not echecs else 1


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = p.add_subparsers(dest="cmd", required=True)
    f = sp.add_parser("fabriquer", help="fabrique le mod dans un dossier neuf (ne pose rien)")
    f.add_argument("--jeu", required=True, help="dossier du jeu (lecture seule)")
    f.add_argument("--sortie", required=True, help="dossier NEUF, hors du jeu")
    f.add_argument("--options", default="AB", choices=["A", "B", "AB", "C", "AC"],
                   help="copies a ajouter (defaut AB ; C = la copie aux feux deplacee sur l'avant du plateau)")
    sp.add_parser("autotest", help="controles sur un fichier synthetique")
    a = p.parse_args(argv)
    if a.cmd == "autotest":
        return autotest()
    try:
        fabriquer(a.jeu, a.sortie, a.options)
    except (ErreurMod, OSError) as e:
        print("REFUSE : %s" % e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
