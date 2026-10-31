#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Courbes du lag de Carrier Command 2, a regarder apres la partie (demande du moddeur le 24/10/2026).

Lit le releve ecrit par le jeu (modules « releve » + « ecriture_releve » de l'atelier) et le moniteur de
temperature (outils/monitoring/historique.db), puis ecrit une page HTML (presentation n° 1 de
maquette_courbes_cc2.html, choisie par le moddeur) dans mods/cc2-patchs/courbes/, et affiche le bilan.

Usage :
  python3 outil/courbes/faire_courbes.py                    derniere partie
  python3 outil/courbes/faire_courbes.py --liste            parties enregistrees (numero, date, duree, vitesse)
  python3 outil/courbes/faire_courbes.py --partie 3         la partie n° 3 de la liste (-2 = l'avant-derniere)
  python3 outil/courbes/faire_courbes.py --comparer 2       la derniere partie, comparee a la n° 2
Pour les tests : --releve FICHIER (autre releve), --sortie DOSSIER, --sans-mac (sans le moniteur).
"""
import datetime, json, math, os, re, sqlite3, statistics, sys

ICI = os.path.dirname(os.path.abspath(__file__))
ATELIER = os.path.dirname(os.path.dirname(ICI))
RELEVE = os.path.expanduser("~/Library/Application Support/Carrier Command 2/releve_cc2.txt")
MONITEUR = os.path.expanduser("~/Documents/ZClaude/outils/monitoring/historique.db")
MODELE = os.path.join(ICI, "modele_courbes.html")
SORTIE = os.path.join(ATELIER, "courbes")

PAS = 5                     # secondes par point
TROU_SESSION = 120          # s sans aucune ligne : nouvelle partie
DUREE_MIN = 60              # s : plus court = ignore (menu, chargement rate)
PRIORITE = ["holomap_screen", "screen_veh_m", "screen_nav_m", "hud"]
COLONNES = ["pa", "terre", "avion", "helico", "navire", "tourelle", "autre", "hangar", "caches"]
EN_JEU = ["pa", "terre", "avion", "helico", "navire", "tourelle"]
NOMS_TYPES = {"pa": "porte-avions", "terre": "terrestres", "avion": "avions", "helico": "hélicos",
              "navire": "navires", "tourelle": "tourelles"}
PILOTES = {2: "un véhicule terrestre", 4: "un véhicule terrestre", 6: "un véhicule terrestre", 8: "un avion",
           10: "un avion", 12: "un hélico", 14: "un hélico", 58: "un robot-chien", 77: "un navire", 79: "un navire"}
ACTIVITES = ["sur le pont", "aux commandes", "sur la carte", "en pause"]
LIGNE = re.compile(r"CC2R1 ([SDE]) (.*?) FIN")


class Erreur(Exception):
    pass


# ---------------------------------------------------------------- lecture du releve
def lire_releve(chemin):
    if not os.path.exists(chemin):
        raise Erreur("pas de releve : %s n'existe pas (le jeu n'a encore rien ecrit, ou les modules "
                     "« releve » et « ecriture_releve » ne sont pas actifs)" % chemin)
    lignes, etrangeres = [], 0
    with open(chemin, encoding="utf-8", errors="replace") as f:
        for brut in f:
            trouve = False
            for m in LIGNE.finditer(brut):
                champs = {}
                for morceau in m.group(2).split():
                    if "=" in morceau:
                        k, v = morceau.split("=", 1)
                        champs[k] = v
                try:
                    champs["e"], champs["t"] = int(champs["e"]), int(champs["t"])
                except (KeyError, ValueError):
                    continue
                champs["type"] = m.group(1)
                lignes.append(champs)
                trouve = True
            if not trouve and brut.strip():
                etrangeres += 1
    lignes.sort(key=lambda c: c["e"])
    return lignes, etrangeres


def decouper(lignes):
    """Une partie = des lignes sans trou de plus de 2 min, et sans retour en arriere de l'horloge du jeu
    (chargement d'une sauvegarde, nouvelle partie)."""
    parties, cour, tmax = [], [], None
    for c in lignes:
        nouvelle = cour and (c["e"] - cour[-1]["e"] > TROU_SESSION or (tmax is not None and c["t"] < tmax - 300))
        if nouvelle:
            parties.append(cour)
            cour, tmax = [], None
        cour.append(c)
        tmax = c["t"] if tmax is None else max(tmax, c["t"])
    if cour:
        parties.append(cour)
    return [p for p in parties if p[-1]["e"] - p[0]["e"] >= DUREE_MIN]


# ---------------------------------------------------------------- points toutes les 5 s
def camps(c, moi):
    out = {"moi": dict.fromkeys(COLONNES, 0), "adv": dict.fromkeys(COLONNES, 0), "iles": dict.fromkeys(COLONNES, 0)}
    for k, v in c.items():
        if not re.fullmatch(r"q-?\d+", k):
            continue
        equipe = int(k[1:])
        valeurs = [int(x) for x in v.split(",")]
        camp = "moi" if equipe == moi else ("iles" if equipe == 0 else "adv")
        for nom, x in zip(COLONNES, valeurs):
            out[camp][nom] += x
    return out


def preparer(partie, mac):
    debut = partie[0]["e"] - partie[0]["e"] % PAS
    fin = partie[-1]["e"]
    # horloge : pour chaque seconde, le plus petit top lu (les ecrans qui regardent l'heure 1 fois sur 8 sont en retard)
    tops = {}
    for c in partie:
        if c["e"] not in tops or c["t"] < tops[c["e"]]:
            tops[c["e"]] = c["t"]
    secondes = sorted(tops)
    donnees = {}
    for c in partie:
        if c["type"] == "D":
            rang = PRIORITE.index(c["s"]) if c["s"] in PRIORITE else 99
            if c["e"] not in donnees or rang < donnees[c["e"]][0]:
                donnees[c["e"]] = (rang, c)
    equipes = [int(c["moi"]) for c in partie if c["type"] == "D" and c.get("moi", "-1") not in ("-1", None)]
    moi = statistics.mode(equipes) if equipes else 1
    battements = [c for c in partie if c["type"] == "E"]
    hud = [c["e"] for c in partie if c["s"] == "hud"]
    pilote = {c["e"]: int(c["pil"]) for c in partie if c["type"] == "D" and c["s"] == "hud" and "pil" in c}
    import bisect

    def premier_apres(e):
        i = bisect.bisect_left(secondes, e)
        return secondes[i] if i < len(secondes) else None

    points = []
    for b in range(debut, fin + 1, PAS):
        p = {"t": b}
        e1, e2 = premier_apres(b), premier_apres(b + PAS)
        v = None
        if e1 is not None and e2 is not None and e1 < b + PAS and e2 > e1 and e2 - e1 <= 4 * PAS:
            v = (tops[e2] - tops[e1]) / (30.0 * (e2 - e1))
        p["v"] = None if v is None else round(min(max(v, 0.0), 1.5), 3)
        p["jeu"] = tops.get(e1) if e1 is not None and e1 < b + PAS else None
        d = donnees.get(b, (None, None))[1]
        if d is not None:
            cp = camps(d, moi)
            for camp in ("moi", "adv", "iles"):
                p[camp] = sum(cp[camp][k] for k in EN_JEU)
                p["det_" + camp] = [cp[camp][k] for k in EN_JEU]
            p["hangar"] = cp["moi"]["hangar"]
            p["caches"] = cp["adv"]["caches"] + cp["iles"]["caches"]
            p["tot"] = p["moi"] + p["adv"] + p["iles"]
            p["mis"] = max(0, int(d.get("mis", -1)))
            p["obu"] = max(0, int(d.get("pro", -1)))
            p["epa"] = max(0, int(d.get("epa", -1)))
            p["src"] = d["s"]
        if b in pilote:
            p["pil"] = pilote[b]
        # ecrans : derniers battements dans les 10 s qui precedent la fin du point
        fen = [c for c in battements if b + PAS - 10 < c["e"] <= b + PAS and c["s"] not in ("hud", "autre")]
        vus = {}
        for c in fen:
            vus[c["s"]] = c
        if vus:
            p["ecr"] = sum(1 for c in vus.values() if c.get("a") != "0")
            p["ecr_tous"] = len(vus)
            focus = [s for s, c in vus.items() if c.get("f") == "1"]
            if focus:
                p["focus"] = focus[0]
        ips = [int(c["n"]) / 10.0 for c in fen if c.get("n", "0").isdigit() and int(c["n"]) > 0]
        hud_fen = [c for c in battements if c["s"] == "hud" and b + PAS - 10 < c["e"] <= b + PAS]
        if hud_fen:
            ips = [int(c["n"]) / 10.0 for c in hud_fen if c.get("n", "0").isdigit()]
        if ips:
            p["ips"] = round(statistics.median(ips), 1)
        # ce que faisait le joueur
        k = bisect.bisect_right(hud, b + PAS - 10)
        en_hud = k < len(hud) and hud[k] <= b + PAS
        if p["v"] is not None and p["v"] < 0.02:       # le jeu n'avance plus : pause (menu, Echap)
            p["act"] = 3
        elif en_hud:
            p["act"] = 1
        elif p.get("focus") == "holomap_screen":
            p["act"] = 2
        else:
            p["act"] = 0
        points.append(p)
    # Mac (moniteur) : moyenne du processeur, maximum de la temperature, par point
    if mac:
        for p in points:
            m = mac.get(p["t"] - p["t"] % PAS)
            if m:
                p["cpu"], p["temp"] = m
    # premiers points sans vitesse (chargement) : retires
    while points and points[0]["v"] is None:
        points.pop(0)
    while points and points[-1]["v"] is None:
        points.pop()
    return points, moi


def lire_mac(debut, fin, chemin=MONITEUR):
    if not os.path.exists(chemin):
        return {}
    try:
        c = sqlite3.connect("file:%s?mode=ro" % chemin, uri=True, timeout=5)
        rows = c.execute("select ts, cpu_pct, cpu_temp from samples where ts between ? and ? order by ts",
                         (debut - PAS, fin + PAS)).fetchall()
    except sqlite3.Error:
        return {}
    seaux = {}
    for ts, cpu, temp in rows:
        if cpu is None or temp is None:
            continue
        k = int(ts) - int(ts) % PAS
        seaux.setdefault(k, []).append((cpu, temp))
    return {k: (round(sum(x for x, _ in v) / len(v), 1), round(max(y for _, y in v), 1)) for k, v in seaux.items()}


# ---------------------------------------------------------------- bilan
def heure(t):
    return datetime.datetime.fromtimestamp(t).strftime("%H:%M")


def moyenne(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def correlation(xs, ys):
    paires = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(paires) < 12:
        return None
    mx, my = moyenne([x for x, _ in paires]), moyenne([y for _, y in paires])
    a = sum((x - mx) * (y - my) for x, y in paires)
    b = sum((x - mx) ** 2 for x, _ in paires)
    c = sum((y - my) ** 2 for _, y in paires)
    return a / math.sqrt(b * c) if b > 0 and c > 0 else None


SUJETS = [("tot", "le nombre d'unités"), ("mis", "les missiles en vol"), ("obu", "les obus en vol"),
          ("ecr", "les écrans allumés"), ("temp", "la température du Mac"), ("cpu", "la charge du processeur")]


def analyser(points):
    jeu = [p for p in points if p["v"] is not None and p["act"] != 3]
    an = {"vmoy": moyenne([p["v"] for p in jeu]) or 0.0}
    an["pause"] = sum(PAS for p in points if p["act"] == 3)
    pire = None
    for i in range(0, len(points) - 11):
        w = points[i:i + 12]
        if any(p["v"] is None or p["act"] == 3 for p in w):
            continue
        m = moyenne([p["v"] for p in w])
        if pire is None or m < pire[0]:
            pire = (m, i)
    if pire is None:                       # partie trop courte : le pire point
        i = min(range(len(points)), key=lambda k: points[k]["v"] if points[k]["v"] is not None else 9)
        pire = (points[i]["v"] or 0.0, i)
    an["pire"], an["pire_i"] = pire
    w = points[pire[1]:pire[1] + 12]
    acts = [p["act"] for p in w]
    an["act_pire"] = max(set(acts), key=acts.count)
    pil = [p["pil"] for p in w if "pil" in p]
    an["pil_pire"] = max(set(pil), key=pil.count) if pil else None
    for k in ("tot", "mis", "obu", "ecr", "temp", "cpu", "iles"):
        an[k + "_moy"] = moyenne([p.get(k) for p in jeu])
        an[k + "_pire"] = moyenne([p.get(k) for p in w])
        an[k + "_max"] = max([p.get(k) for p in points if p.get(k) is not None], default=None)
        an[k + "_max_pire"] = max([p.get(k) for p in w if p.get(k) is not None], default=None)
    an["r"] = {k: correlation([p.get(k) for p in jeu], [p["v"] for p in jeu]) for k, _ in SUJETS}
    return an


def pc(x):
    return "%d %%" % round(100 * x)


def bilan(points, an, autre=None, an_autre=None):
    phrases = []
    vm = an["vmoy"]
    phrases.append("Le jeu a tourné à <b>%s</b> de sa vitesse en moyenne : une minute réelle n'a fait que %d secondes de jeu."
                   % (pc(vm), round(60 * vm)))
    p0 = points[an["pire_i"]]
    quoi = ACTIVITES[an["act_pire"]]
    if an["act_pire"] == 1 and an["pil_pire"] in PILOTES:
        quoi = "aux commandes d'" + PILOTES[an["pil_pire"]]
    causes = []
    for k, nom in (("mis", "missiles"), ("obu", "obus")):
        mx, moy = an[k + "_max_pire"], an[k + "_moy"]
        if mx is not None and mx >= 3 and mx >= 3 * max(1.0, moy or 0):
            causes.append("%d %s" % (mx, nom))
    texte = "Pire minute : <b>%s</b>, à <b>%s</b>, <b>%s</b>" % (heure(p0["t"]), pc(an["pire"]), quoi)
    if causes:
        texte += ", avec %s en vol (presque rien le reste du temps)" % " et ".join(causes)
    if an["tot_pire"] and an["tot_moy"] and an["tot_pire"] >= 1.1 * an["tot_moy"]:
        texte += ", et plus d'unités que d'habitude (%d contre %d)" % (round(an["tot_pire"]), round(an["tot_moy"]))
    phrases.append(texte + ".")
    if an["temp_pire"] is not None and an["temp_moy"] is not None:
        d = an["temp_pire"] - an["temp_moy"]
        if abs(d) < 3:
            phrases.append("Le Mac était à %d °C, comme le reste de la partie : la chaleur n'explique pas ce creux."
                           % round(an["temp_pire"]))
        else:
            phrases.append("Le Mac était à %d °C, %d °C %s que d'habitude." % (round(an["temp_pire"]), round(abs(d)),
                                                                                "de plus" if d > 0 else "de moins"))
    if an["tot_max"] is not None:
        phrases.append("Unités : jusqu'à %d en même temps, dont environ %d sur les îles."
                       % (an["tot_max"], round(an["iles_moy"] or 0)))
    liens = sorted([(r, k) for k, r in an["r"].items() if r is not None and r <= -0.3])
    if liens:
        r, k = liens[0]
        nom = dict(SUJETS)[k]
        phrases.append("Ce qui va le plus avec le ralentissement : %s (lien %s). Un lien n'est pas une preuve."
                       % (nom, "fort" if r <= -0.6 else "moyen"))
    if an["pause"] >= 30:
        phrases.append("Pauses : %d min %02d s, pas comptées dans la moyenne." % (an["pause"] // 60, an["pause"] % 60))
    if autre is not None:
        phrases.append("Autre partie (%s) : <b>%s</b> en moyenne, avec environ %d unités sur les îles au lieu de %d."
                       % (datetime.datetime.fromtimestamp(autre[0]["t"]).strftime("%d/%m à %H:%M"), pc(an_autre["vmoy"]),
                          round(an_autre["iles_moy"] or 0), round(an["iles_moy"] or 0)))
    return phrases


def tuiles(points, an):
    return [[pc(an["vmoy"]), "vitesse moyenne"],
            [pc(an["pire"]), "pire minute (%s)" % heure(points[an["pire_i"]]["t"])],
            ["%d" % an["tot_max"] if an["tot_max"] is not None else "–", "unités au plus fort"],
            ["%d °C" % round(an["temp_max"]) if an["temp_max"] is not None else "–", "Mac au plus chaud"]]


# ---------------------------------------------------------------- page
def nom_partie(points):
    d = datetime.datetime.fromtimestamp(points[0]["t"])
    duree = (points[-1]["t"] - points[0]["t"] + PAS) // 60
    return "Partie du %s, %s → %s (%d min)" % (d.strftime("%d/%m/%Y"), heure(points[0]["t"]), heure(points[-1]["t"] + PAS), duree)


def ecrire_page(points, an, phrases, sortie, autre=None):
    data = {"pas": PAS, "partie": {"nom": nom_partie(points), "points": points, "bilan": phrases, "tuiles": tuiles(points, an)},
            "autre": None if autre is None else {"nom": nom_partie(autre), "points": autre}}
    modele = open(MODELE, encoding="utf-8").read()
    page = modele.replace("__TITRE__", nom_partie(points)).replace("__DATA__", json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    os.makedirs(sortie, exist_ok=True)
    d = datetime.datetime.fromtimestamp(points[0]["t"])
    chemin = os.path.join(sortie, "courbes_%s%s.html" % (d.strftime("%Y-%m-%d_%Hh%M"), "_comparee" if autre else ""))
    open(chemin, "w", encoding="utf-8").write(page)
    return chemin


def lire_args(argv):
    opts = {"releve": RELEVE, "sortie": SORTIE, "mac": True, "liste": False, "partie": -1, "comparer": None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--liste":
            opts["liste"] = True
        elif a == "--sans-mac":
            opts["mac"] = False
        elif a in ("--releve", "--sortie", "--partie", "--comparer") and i + 1 < len(argv):
            v = argv[i + 1]
            opts[a[2:]] = int(v) if a in ("--partie", "--comparer") else v
            i += 1
        else:
            raise Erreur("argument non compris : %r" % a)
        i += 1
    return opts


def choisir(parties, n):
    if not parties:
        raise Erreur("aucune partie dans le releve (il faut au moins une minute de jeu)")
    if n < 0:
        n = len(parties) + 1 + n
    if not 1 <= n <= len(parties):
        raise Erreur("pas de partie n° %d (il y en a %d : --liste)" % (n, len(parties)))
    return parties[n - 1]


def main(argv):
    opts = lire_args(argv)
    lignes, etrangeres = lire_releve(opts["releve"])
    parties = decouper(lignes)
    if opts["liste"]:
        print("%d partie(s) dans %s :" % (len(parties), opts["releve"]))
        for k, p in enumerate(parties, 1):
            pts, _ = preparer(p, {})
            an = analyser(pts) if pts else {"vmoy": 0}
            print("  n° %-3d %s  vitesse moyenne %s" % (k, nom_partie(pts) if pts else "?", pc(an["vmoy"])))
        return
    p = choisir(parties, opts["partie"])
    mac = lire_mac(p[0]["e"], p[-1]["e"]) if opts["mac"] else {}
    points, moi = preparer(p, mac)
    if len(points) < 12:
        raise Erreur("partie trop courte pour des courbes (%d points)" % len(points))
    an = analyser(points)
    autre = an_autre = None
    if opts["comparer"] is not None:
        q = choisir(parties, opts["comparer"])
        autre, _ = preparer(q, lire_mac(q[0]["e"], q[-1]["e"]) if opts["mac"] else {})
        an_autre = analyser(autre)
    phrases = bilan(points, an, autre, an_autre)
    chemin = ecrire_page(points, an, phrases, opts["sortie"], autre)
    print(nom_partie(points))
    for s in phrases:
        print("  - " + re.sub(r"</?b>", "", s))
    sources = sorted(set(pt.get("src") for pt in points if pt.get("src")))
    print("Donnees : %d points de %d s, unites lues sur %s, equipe du joueur %d, Mac %s, %d ligne(s) d'autres mods."
          % (len(points), PAS, ", ".join(sources) or "aucun ecran", moi, "oui" if mac else "non", etrangeres))
    print("Page : " + chemin)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Erreur as e:
        sys.exit("ERREUR : %s" % e)
