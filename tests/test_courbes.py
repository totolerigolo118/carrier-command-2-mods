#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste l'outil des courbes du lag (outil/courbes/faire_courbes.py) sur une partie simulee.

La partie est jouee par le vrai script du releve (tests/test_releve.py --fichier : 10 ecrans du pont, carte de
3:00 a 4:30, pilotage d'un avion de 6:00 a 9:00, combat de 7:00 a 8:30, pause de 12:00 a 13:00), puis l'outil
en tire les points toutes les 5 s, le bilan et la page. On verifie que ce qu'il trouve correspond au scenario.
"""
import os, re, shutil, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(ICI), "outil", "courbes"))
import faire_courbes as F

ok = True
def verifier(nom, condition, detail=""):
    global ok
    ok = ok and condition
    print("  %-62s %s %s" % (nom, "OK" if condition else "ECHEC", detail))


print("\nTest de l'outil des courbes")
tmp = tempfile.mkdtemp(prefix="test_courbes_cc2_")
try:
    releve = os.path.join(tmp, "releve_cc2.txt")
    r = subprocess.run([sys.executable, os.path.join(ICI, "test_releve.py"), "--lua53", "--fichier", releve],
                       capture_output=True, text=True)
    verifier("partie simulee par le script du releve", r.returncode == 0 and os.path.exists(releve), r.stdout.strip().splitlines()[-1])
    with open(releve, "a") as f:
        f.write("message d'un mod\nCC2R1 D e=12 t=x FIN\n")          # lignes etrangere et abimee : ignorees
    lignes, etrangeres = F.lire_releve(releve)
    parties = F.decouper(lignes)
    verifier("une seule partie trouvee", len(parties) == 1, str(len(parties)))
    verifier("ligne d'un mod et ligne abimee : comptees a part, ignorees", etrangeres == 2 and all(isinstance(c["t"], int) for c in lignes), str(etrangeres))
    pts, moi = F.preparer(parties[0], {})
    e0 = 1792850000
    a = lambda m: [p for p in pts if m[0] * 60 <= p["t"] - e0 < m[1] * 60]
    verifier("equipe du joueur = 1", moi == 1)
    v_pont = F.moyenne([p["v"] for p in a((0.5, 2.5))])
    verifier("vitesse sur le pont ~ 72 % (scenario : 0,74 - 0,0015 x 12)", abs(v_pont - 0.722) < 0.015, "%.3f" % v_pont)
    v_combat = F.moyenne([p["v"] for p in a((7.2, 8.3))])
    verifier("vitesse pendant le combat en pilotage ~ 50 %", 0.45 < v_combat < 0.56, "%.3f" % v_combat)
    p1 = a((0.5, 1))[0]
    verifier("unites au debut : toi 2, adverse 3, iles 61 (total 66)",
             (p1["moi"], p1["adv"], p1["iles"], p1["tot"]) == (2, 3, 61, 66), str((p1["moi"], p1["adv"], p1["iles"], p1["tot"])))
    verifier("detail : iles = 44 terrestres, 8 navires, 9 tourelles", p1["det_iles"] == [0, 44, 0, 0, 8, 9], str(p1["det_iles"]))
    verifier("hangar : 4 de mes unites", p1["hangar"] == 4, str(p1["hangar"]))
    verifier("caches : 4 adverses (dont PA et hangar) + 61 des iles", p1["caches"] == 65, str(p1["caches"]))
    verifier("missiles et obus seulement pendant le combat",
             all(p["mis"] == 0 for p in a((0.5, 6.9)) if "mis" in p) and max(p["mis"] for p in a((7.1, 8.4))) >= 4)
    verifier("activite : carte de 3:00 a 4:30", all(p["act"] == 2 for p in a((3.2, 4.3))))
    verifier("activite : aux commandes de 6:00 a 9:00 (avion)", all(p["act"] == 1 and p.get("pil", 8) == 8 for p in a((6.2, 8.8))))
    verifier("activite : pause de 12:00 a 13:00", all(p["act"] == 3 for p in a((12.1, 12.9))) and all(p["act"] != 3 for p in a((13.3, 14))))
    verifier("ecrans allumes : 10 sur le pont, 3 en pilotage",
             a((1, 2))[0].get("ecr") == 10 and a((7, 8))[0].get("ecr") == 3, "%s / %s" % (a((1, 2))[0].get("ecr"), a((7, 8))[0].get("ecr")))
    verifier("images par seconde ~ 20 (simulation a 20 images/s)", 19.5 <= a((1, 2))[0].get("ips", 0) <= 20.5, str(a((1, 2))[0].get("ips")))
    an = F.analyser(pts)
    verifier("pire minute pendant le combat", 7.0 * 60 <= pts[an["pire_i"]]["t"] - e0 <= 8.5 * 60, F.heure(pts[an["pire_i"]]["t"]))
    verifier("pause comptee a part (~ 1 min)", 50 <= an["pause"] <= 65, str(an["pause"]))
    phrases = F.bilan(pts, an)
    texte = " ".join(phrases)
    verifier("bilan : vitesse moyenne, pilotage d'un avion, missiles, pause",
             "vitesse en moyenne" in texte and "aux commandes d'un avion" in texte and "missiles" in texte and "Pauses" in texte)
    verifier("bilan : le lien le plus fort est un sujet du combat", re.search(r"ralentissement : les (obus|missiles)", texte) is not None, texte[-160:])
    sortie = os.path.join(tmp, "courbes")
    F.main(["--releve", releve, "--sortie", sortie, "--sans-mac"])
    pages = os.listdir(sortie)
    page = open(os.path.join(sortie, pages[0]), encoding="utf-8").read() if pages else ""
    verifier("page ecrite, donnees et titre remplis", len(pages) == 1 and "__DATA__" not in page and "__TITRE__" not in page
             and '"points":[' in page, str(pages))
    try:
        F.main(["--releve", releve, "--partie", "5"])
        verifier("partie inexistante : refus", False)
    except F.Erreur as e:
        verifier("partie inexistante : refus", "pas de partie" in str(e))
    try:
        F.main(["--releve", releve, "--partie 1"])
        verifier("arguments colles : refus", False)
    except F.Erreur as e:
        verifier("arguments colles : refus", "non compris" in str(e))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\nRESULTAT : " + ("TOUT EST BON" if ok else "IL Y A DES ECHECS"))
sys.exit(0 if ok else 1)
