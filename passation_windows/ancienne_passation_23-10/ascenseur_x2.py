#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ascenseur x2 : sorties et retours d'avions 2 fois plus rapides dans Carrier Command 2,
contre 2 fois plus d'energie pour le systeme ASCENSEUR/GRUE du porte-avions.

Modifie le programme du jeu (MacOS/build_mac, version Mac du 05/01/2026) a 34 endroits :
  - energie  : part maximale du systeme ascenseur/grue 0,4 -> 0,8
  - ascenseur: pas maximal de la plateforme 0,025 -> 0,05 m par tick (0,75 -> 1,5 m/s)
  - grue     : grue du hangar, horizontal 5 -> 10 m/s, vertical 1 -> 2 m/s,
               rotation 1,2 -> 2,4 rad/s
  - roulage  : avions sur le pont, vitesse max 2,5 -> 5 m/s, acceleration 1,5 -> 3 m/s2

Chaque retouche redirige une instruction vers une valeur doublee DEJA presente dans la zone
en lecture seule du programme (aucune valeur partagee n'est modifiee, rien n'est decale).

Usage :
  ascenseur_x2.py             -> applique
  ascenseur_x2.py --origine   -> remet le programme d'origine (octet pour octet)
  ascenseur_x2.py --etat      -> dit ou on en est, sans rien toucher
  --fichier CHEMIN            -> travaille sur une copie au lieu du jeu (tests)
"""
import hashlib, os, shutil, struct, subprocess, sys

JEU = "/Users/UTILISATEUR/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents/MacOS/build_mac"
DOSSIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAUVEGARDE = os.path.join(DOSSIER, "sauvegarde", "build_mac_origine")

MD5_ORIGINE = "b0107170ddaf0245cbfee8a2d876aeb6"   # build_mac du 05/01/2026
BASE = 0x100000000                                   # binaire x86_64 seul : offset = adresse - BASE

# Part d'energie : movl $0x3ecccccd (0,4), 0x118(%r15) dans
# c_vehicle_carrier_server_power_manager::build ; on remplace la valeur immediate.
ENERGIE = (0x10019f0ad, "41c78718010000cdcccc3e", "41c78718010000cdcc4c3f")

# (adresse de l'instruction, octets d'origine, ancienne constante, nouvelle constante, groupe, instruction)
# Ascenseur : c_vehicle_server_carrier::tick_server_type ; grue et roulage :
# c_vehicle_server_carrier::docking_manager_air::update.
REDIRECTIONS = [
    (0x10019455a, "f30f5f0d02556d02", 0x102869a64, 0x10286995c, "ascenseur", "maxss"),
    (0x100194562, "f30f5d0d0e546d02", 0x102869978, 0x1028697a4, "ascenseur", "minss"),
    (0x100194583, "f30f5e1ded536d02", 0x102869978, 0x1028697a4, "ascenseur", "divss"),
    (0x1001ae8bc, "f30f103d10b26b02", 0x102869ad4, 0x102869750, "grue", "movss"),
    (0x1001aea04, "f30f103dc8b06b02", 0x102869ad4, 0x102869750, "grue", "movss"),
    (0x1001ae8c8, "f30f10158cae6b02", 0x10286975c, 0x1028b232c, "grue", "movss"),
    (0x1001aea10, "f30f101d44ad6b02", 0x10286975c, 0x1028b232c, "grue", "movss"),
    (0x1001ae8d4, "f30f5f35fcb06b02", 0x1028699d8, 0x102869c7c, "grue", "maxss"),
    (0x1001ae968, "f30f5f1d68b06b02", 0x1028699d8, 0x102869c7c, "grue", "maxss"),
    (0x1001aea1c, "f30f5f35b4af6b02", 0x1028699d8, 0x102869c7c, "grue", "maxss"),
    (0x1001aeab8, "f30f5f1d18af6b02", 0x1028699d8, 0x102869c7c, "grue", "maxss"),
    (0x1001aeba7, "f30f5f1d29ae6b02", 0x1028699d8, 0x102869c7c, "grue", "maxss"),
    (0x1001ae8dc, "f30f5d35f0b06b02", 0x1028699d4, 0x102869b80, "grue", "minss"),
    (0x1001ae970, "f30f100d5cb06b02", 0x1028699d4, 0x102869b80, "grue", "movss"),
    (0x1001aea24, "f30f5d35a8af6b02", 0x1028699d4, 0x102869b80, "grue", "minss"),
    (0x1001aeac0, "f30f100d0caf6b02", 0x1028699d4, 0x102869b80, "grue", "movss"),
    (0x1001aebaf, "f30f100d1dae6b02", 0x1028699d4, 0x102869b80, "grue", "movss"),
    (0x1001aeb2b, "f30f5f0dd1ae6b02", 0x102869a04, 0x102869974, "grue", "maxss"),
    (0x1001aeb33, "f30f101d95ac6b02", 0x1028697d0, 0x10286986c, "grue", "movss"),
    (0x1001ad6f9, "f30f5825a3c06b02", 0x1028697a4, 0x1028697b0, "roulage", "addss"),
    (0x1001adf35, "f30f582567b86b02", 0x1028697a4, 0x1028697b0, "roulage", "addss"),
    (0x1001ae02a, "f30f582572b76b02", 0x1028697a4, 0x1028697b0, "roulage", "addss"),
    (0x1001ae104, "f30f582598b66b02", 0x1028697a4, 0x1028697b0, "roulage", "addss"),
    (0x1001ae2c1, "f30f581ddbb46b02", 0x1028697a4, 0x1028697b0, "roulage", "addss"),
    (0x1001ae6e0, "f30f5825bcb06b02", 0x1028697a4, 0x1028697b0, "roulage", "addss"),
    (0x1001b010f, "f30f58258d966b02", 0x1028697a4, 0x1028697b0, "roulage", "addss"),
    (0x1001ad701, "f30f1015b3c06b02", 0x1028697bc, 0x10286976c, "roulage", "movss"),
    (0x1001adf41, "f30f101573b86b02", 0x1028697bc, 0x10286976c, "roulage", "movss"),
    (0x1001ae036, "f30f10157eb76b02", 0x1028697bc, 0x10286976c, "roulage", "movss"),
    (0x1001ae110, "f30f1015a4b66b02", 0x1028697bc, 0x10286976c, "roulage", "movss"),
    (0x1001ae2cd, "f30f1025e7b46b02", 0x1028697bc, 0x10286976c, "roulage", "movss"),
    (0x1001ae6e8, "f30f1015ccb06b02", 0x1028697bc, 0x10286976c, "roulage", "movss"),
    (0x1001b0117, "f30f10159d966b02", 0x1028697bc, 0x10286976c, "roulage", "movss"),
]

def lire_f32(donnees, va):
    return struct.unpack_from("<f", donnees, va - BASE)[0]


def construire_table(donnees):
    """Liste de (offset, octets d'origine, octets modifies, groupe). Verifie tout au passage."""
    table = []
    va, avant, apres = ENERGIE
    table.append((va - BASE, bytes.fromhex(avant), bytes.fromhex(apres), "energie"))
    for va, avant, vieux, neuf, groupe, _ in REDIRECTIONS:
        avant = bytes.fromhex(avant)
        fin = va + len(avant)
        assert int.from_bytes(avant[-4:], "little", signed=True) == vieux - fin, hex(va)
        v_vieux, v_neuf = lire_f32(donnees, vieux), lire_f32(donnees, neuf)
        assert v_neuf == 2 * v_vieux, (hex(va), v_vieux, v_neuf)
        apres = avant[:-4] + (neuf - fin).to_bytes(4, "little", signed=True)
        table.append((va - BASE, avant, apres, groupe))
    return table


def etat(donnees, table):
    """'origine', 'modifie', ou 'inconnu' (jeu mis a jour, ou fichier abime)."""
    n_avant = sum(donnees[o:o + len(a)] == a for o, a, _, _ in table)
    n_apres = sum(donnees[o:o + len(b)] == b for o, _, b, _ in table)
    if n_avant == len(table):
        return "origine"
    if n_apres == len(table):
        return "modifie"
    return "inconnu"


def md5(chemin):
    h = hashlib.md5()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def ecrire(chemin, donnees):
    tmp = chemin + ".tmp_ascenseur_x2"
    with open(tmp, "wb") as f:
        f.write(donnees)
    shutil.copymode(chemin, tmp)
    os.replace(tmp, chemin)


def main(argv):
    fichier = argv[argv.index("--fichier") + 1] if "--fichier" in argv else JEU
    print("\n  ASCENSEUR x2 (Carrier Command 2) : avions 2x plus rapides, energie x2")
    print("  " + "-" * 66)

    if fichier == JEU and subprocess.run(["pgrep", "-f", "carriercommand|build_mac"],
                                         capture_output=True, text=True).stdout.strip():
        print("\n  ARRET : ferme d'abord Carrier Command 2.\n")
        return 2
    if not os.path.isfile(fichier):
        print("\n  ARRET : programme du jeu introuvable :\n    " + fichier + "\n")
        return 2

    with open(fichier, "rb") as f:
        donnees = bytearray(f.read())
    try:
        table = construire_table(donnees)
    except (AssertionError, struct.error) as e:
        print("\n  ARRET : le programme ne ressemble plus a celui que j'ai analyse (mise a jour Steam ?).")
        print("    detail : %r\n" % (e,))
        return 2
    avant = etat(donnees, table)
    print("  Etat actuel : " + {"origine": "jeu d'origine", "modifie": "ascenseur x2 actif",
                                "inconnu": "INCONNU"}[avant])

    if "--etat" in argv:
        return 0
    if avant == "inconnu":
        print("\n  ARRET : programme ni d'origine ni modifie (mise a jour Steam ?). Rien n'est touche.\n")
        return 2

    voulu = "origine" if "--origine" in argv else "modifie"
    if avant == voulu:
        print("\n  Rien a faire : deja dans cet etat.\n")
        return 0

    if voulu == "modifie" and fichier == JEU:
        if md5(fichier) != MD5_ORIGINE:
            print("\n  ARRET : le programme n'est pas celui du 05/01/2026 que j'ai analyse.\n")
            return 2
        if not os.path.isfile(SAUVEGARDE):
            os.makedirs(os.path.dirname(SAUVEGARDE), exist_ok=True)
            shutil.copy2(fichier, SAUVEGARDE)
            print("  Copie de securite du programme d'origine : sauvegarde/build_mac_origine")

    for o, a, b, _ in table:
        donnees[o:o + len(a)] = b if voulu == "modifie" else a
    ecrire(fichier, bytes(donnees))

    with open(fichier, "rb") as f:
        relu = f.read()
    apres = etat(relu, table)
    ok = apres == voulu
    if voulu == "origine" and fichier == JEU:
        ok = ok and md5(fichier) == MD5_ORIGINE
    groupes = {}
    for _, _, _, g in table:
        groupes[g] = groupes.get(g, 0) + 1
    print("  Retouches : " + ", ".join("%s %d" % (g, n) for g, n in groupes.items()) +
          " (total %d)" % len(table))
    if ok and voulu == "modifie":
        print("\n  OK : ascenseur x2 ACTIF. Relance le jeu pour en profiter.")
        print("  (A refaire apres chaque mise a jour Steam ou verification des fichiers.)\n")
    elif ok:
        print("\n  OK : programme d'origine remis, identique octet pour octet.\n")
    else:
        print("\n  PROBLEME : la relecture ne donne pas l'etat attendu (%s).\n" % apres)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
