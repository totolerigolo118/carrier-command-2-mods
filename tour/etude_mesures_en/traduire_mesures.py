#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Traduit en ANGLAIS le texte AFFICHE par le mod `cc2_mesures` (journal des atterrissages, journal des sorties, horloge).

HORS JEU : lit les 4 scripts du mod installe (lecture seule) et ecrit les versions anglaises dans un dossier NEUF.
Ne change QUE des textes affiches : chaque phrase doit etre trouvee EXACTEMENT UNE fois, sinon l'outil refuse. Les noms de
variables, les valeurs internes ("avion" / "helico" servent de cles) et la logique ne sont pas touches. Puis il verifie :
meme nombre de lignes, uniquement des lignes remplacees (rien d'ajoute ni de supprime), syntaxe Lua (lua_syntaxe.py).

  python -I -B traduire_mesures.py --mod "<...>\\Carrier Command 2\\mods\\cc2_mesures" --sortie <dossier NEUF>

Il ne pose rien. Aucun reseau. Un seul sous-processus : le verificateur de syntaxe Lua du depot.
"""
import argparse
import difflib
import hashlib
import os
import subprocess
import sys

AVION_HELICO = ('and "avion " or "helico"', 'and "plane " or "heli  "')   # meme largeur (6) : les colonnes restent alignees
ABANDON = ('" abandon"', '" aborted"')                                   # meme largeur (8)

REMPLACEMENTS = {
    "library_custom_1.lua": [                                            # horloge
        ('"TEMPS DE JEU  "', '"GAME TIME  "'),
    ],
    "library_custom_7.lua": [                                            # vitesse de simulation (largeur de l'horloge)
        ('"TEMPS DE JEU  8:88:88.8"', '"GAME TIME  8:88:88.8"'),
    ],
    "library_custom_4.lua": [                                            # journal des atterrissages
        ('"JOURNAL ATTERRISSAGES (temps de jeu)"', '"LANDING LOG (game time)"'),
        ('"          piste   pont hangar"', '"         runway   deck hangar"'),
        ('update_ui_get_text_size("TEMPS DE JEU", 1000, 0)', 'update_ui_get_text_size("GAME TIME", 1000, 0)'),
        AVION_HELICO,
        ABANDON,
        ('compte(genres.avion, "avion")', 'compte(genres.avion, "plane")'),
        ('compte(genres.helico, "helico")', 'compte(genres.helico, "heli")'),
        ('"FINI en %s : %s"', '"DONE in %s : %s"'),
        ('"EN COURS %s : %s"', '"IN PROGRESS %s : %s"'),
        ('"piste toutes les %s  ratees %d"', '"runway every %s  missed %d"'),
        ('"approche %s  pont>hangar %s"', '"approach %s  deck>hangar %s"'),
        ('"! ecran fige %s : mesure douteuse"', '"! screen froze %s : unreliable"'),
    ],
    "library_custom_9.lua": [                                            # journal des sorties
        ('"SORTIES (temps de jeu)"', '"LAUNCHES (game time)"'),
        ('"          ordre  en l\'air"', '"          order  airborne"'),
        AVION_HELICO,
        ABANDON,
        ('"%d/%d EN L\'AIR : FINI en %s"', '"%d/%d AIRBORNE : DONE in %s"'),
        ('"ecart moyen entre decollages %s"', '"avg gap between takeoffs %s"'),
        ('"%d/%d EN L\'AIR  (en cours %s)"', '"%d/%d AIRBORNE  (running %s)"'),
        ('"SORTIES ? %d en sortie, non reconnu(s)"', '"LAUNCHES ? %d launching, not recognized"'),
    ],
}

# mots francais qu'on s'attend a retrouver encore dans le code (cles internes, commentaires) : on les LISTE pour relecture
MOTS_FR = ("avion", "helico", "piste", "pont", "hangar", "ratees", "approche", "FINI", "COURS", "SORTIES", "TEMPS DE JEU",
           "ATTERRISSAGES", "ordre", "en l'air", "abandon", "ecran", "ecart")


class Refus(Exception):
    pass


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def traduire(texte, nom):
    for ancien, nouveau in REMPLACEMENTS[nom]:
        n = texte.count(ancien)
        if n != 1:
            raise Refus("%s : la phrase %r doit apparaitre exactement une fois ; trouvee %d fois (le mod a change ?)" % (nom, ancien, n))
        texte = texte.replace(ancien, nouveau)
    return texte


def controler(nom, avant, apres):
    a, b = avant.splitlines(keepends=True), apres.splitlines(keepends=True)
    if len(a) != len(b):
        raise Refus("%s : le nombre de lignes a change" % nom)
    changements = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        if op != "replace" or (i2 - i1) != (j2 - j1):
            raise Refus("%s : autre chose que des lignes remplacees (%s)" % (nom, op))
        for k in range(i2 - i1):
            changements.append((i1 + k + 1, a[i1 + k].rstrip("\r\n"), b[j1 + k].rstrip("\r\n")))
    if not changements:
        raise Refus("%s : rien n'a change" % nom)
    return changements


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], allow_abbrev=False)
    p.add_argument("--mod", required=True, help="dossier du mod cc2_mesures installe (lecture seule)")
    p.add_argument("--sortie", required=True, help="dossier NEUF")
    a = p.parse_args()
    try:
        bas = os.path.normcase(os.path.abspath(a.sortie))
        if "steamapps" in bas or "carrier command 2" in bas:
            raise Refus("le dossier de sortie est dans le jeu ou ses donnees : refuse")
        if os.path.exists(a.sortie) and os.listdir(a.sortie):
            raise Refus("le dossier de sortie existe deja et n'est pas vide : donner un dossier NEUF")
        scripts = os.path.join(a.mod, "content", "scripts")
        resultats = {}
        for nom in REMPLACEMENTS:
            with open(os.path.join(scripts, nom), "rb") as f:
                brut = f.read()
            avant = brut.decode("utf-8")
            apres = traduire(avant, nom)
            changements = controler(nom, avant, apres)
            resultats[nom] = (brut, apres.encode("utf-8"), changements)
        sortie_scripts = os.path.join(a.sortie, "content", "scripts")
        os.makedirs(sortie_scripts, exist_ok=True)
        for nom, (brut, neuf, changements) in resultats.items():
            with open(os.path.join(sortie_scripts, nom), "wb") as f:
                f.write(neuf)
            with open(os.path.join(sortie_scripts, nom), "rb") as f:
                if f.read() != neuf:
                    raise Refus("%s : relecture differente" % nom)
            print("== %s : %d ligne(s) changee(s)   source %s -> anglais %s" % (nom, len(changements), sha(brut)[:8], sha(neuf)[:8]))
            for n, ancien, nouveau in changements:
                print("   ligne %d" % n)
                print("   - " + ancien.strip())
                print("   + " + nouveau.strip())
        print("\n== Syntaxe Lua (verificateur du depot, rien n'est execute)")
        verif = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outils", "lua_syntaxe.py")
        r = subprocess.run([sys.executable, "-I", "-B", verif, "-q", sortie_scripts], capture_output=True, text=True, timeout=120)
        print(r.stdout.strip() or "(rien)")
        if r.returncode != 0:
            raise Refus("la syntaxe Lua n'est pas valide : %s" % r.stderr.strip())
        print("\n== Mots francais qui RESTENT dans le code hors commentaires (cles internes voulues, a relire)")
        for nom, (_, neuf, _) in resultats.items():
            for n, ligne in enumerate(neuf.decode("utf-8").splitlines(), 1):
                s = ligne.strip()
                if s.startswith("--"):
                    continue
                if any(m in s for m in MOTS_FR):
                    print("   %s:%d: %s" % (nom, n, s[:130]))
        print("\nRIEN n'a ete pose dans le jeu. Dossier ecrit :", os.path.abspath(a.sortie))
    except (Refus, OSError) as e:
        print("REFUSE : %s" % e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
