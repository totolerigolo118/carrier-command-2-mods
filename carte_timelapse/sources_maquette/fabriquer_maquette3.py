"""Maquette 2 de la carte CC2 : vraies donnees de la sauvegarde + scenario INVENTE de 10 minutes
(routes des porte-avions, salves de missiles). Usage :
python3 -I fabriquer_maquette2.py <save.xml> <modele.html> <sortie.html>
"""
import json
import math
import re
import sys
import xml.etree.ElementTree as ET

save, tpl, out_html = sys.argv[1:4]
txt = re.sub(r"<\?xml[^>]*\?>", "", open(save, encoding="utf-8", errors="replace").read())
root = ET.fromstring("<root>" + txt + "</root>")
fl = float

islands = []
for t in root.find("scene/tiles/tiles"):
    b = t.find("bounds")
    mn, mx = b.find("min").attrib, b.find("max").attrib
    wp = t.find("world_position").attrib
    islands.append(dict(id=int(t.get("id")), x=round(fl(wp["x"]), 1), z=round(fl(wp["z"]), 1),
                        half=round((fl(mx["x"]) - fl(mn["x"])) / 2, 1), team=int(t.get("team_control"))))
units = []
for v in root.find("vehicles/vehicles"):
    m = v.find("transform").attrib
    units.append({"id": int(v.get("id")), "def": int(v.get("definition_index")), "team": int(v.get("team_id")),
                  "x": round(fl(m["tx"]), 1), "z": round(fl(m["tz"]), 1), "yaw": round(math.atan2(fl(m["m02"]), fl(m["m22"])), 3)})
tick = int(root.find("scene").get("logic_tick"))

# ---- le vrai missile de la sauvegarde
rm = root.find("missiles/missiles/m")
rt, rv = rm.find("transform").attrib, rm.find("linear_velocity").attrib
real_missile = dict(x=fl(rt["tx"]), z=fl(rt["tz"]), vx=fl(rv["x"]), vz=fl(rv["z"]), team=int(rm.get("team_id")), speed=math.sqrt(sum(fl(rv[k]) ** 2 for k in "xyz")))

cv1 = next(u for u in units if u["def"] == 0 and u["team"] == 1)
cv2 = next(u for u in units if u["def"] == 0 and u["team"] == 2)
isl = {i["id"]: i for i in islands}
P1, P2 = [cv1["x"], cv1["z"]], [cv2["x"], cv2["z"]]


def catmull(pts, n=120):
    P = [pts[0]] + pts + [pts[-1]]
    segs = len(pts) - 1
    out = []
    for i in range(n + 1):
        u = i / n * segs
        s = min(int(u), segs - 1)
        t = u - s
        a, b, c, d = P[s], P[s + 1], P[s + 2], P[s + 3]
        g = lambda k: 0.5 * ((2 * b[k]) + (-a[k] + c[k]) * t + (2 * a[k] - 5 * b[k] + 4 * c[k] - d[k]) * t * t + (-a[k] + 3 * b[k] - 3 * c[k] + d[k]) * t ** 3)
        out.append([round(g(0), 1), round(g(1), 1)])
    return out


# routes INVENTEES des porte-avions (le depart est le vrai)
CP = {1: catmull([P1, [14000, 11800], [16200, 13200], [18300, 13800], [19700, 14800]]),
      2: catmull([P2, [22600, 26200], [21700, 24300], [21100, 22700], [21500, 21500]])}


def cpos(team, f):
    a = CP[team]
    x = max(0.0, min(1.0, f)) * (len(a) - 1)
    i = min(int(x), len(a) - 2)
    k = x - i
    return [a[i][0] + (a[i + 1][0] - a[i][0]) * k, a[i][1] + (a[i + 1][1] - a[i][1]) * k]


def lerp(a, b, k):
    return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k]


def bent(a, b, off):
    dx, dz = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dz) or 1
    mid = lerp(a, b, 0.5)
    mid = [mid[0] - dz / n * n * off, mid[1] + dx / n * n * off]
    return [a, lerp(a, mid, 0.5), mid, lerp(mid, b, 0.5), b]


def circle(c, r, n=20):
    return [[c[0] + math.cos(k / n * 2 * math.pi) * r, c[1] + math.sin(k / n * 2 * math.pi) * r] for k in range(n + 1)]


at = lambda i: [isl[i]["x"], isl[i]["z"]]
# avions INVENTES : les trajets partent des porte-avions a l'instant du lancement (approx : position de depart)
flights = [
    dict(team=1, **{"def": 10}, path=bent(P1, at(3), 0.10)),
    dict(team=1, **{"def": 8}, path=bent(P1, at(4), -0.08)),
    dict(team=1, **{"def": 8}, path=bent(P1, lerp(P1, P2, 0.55), 0.06)),
    dict(team=2, **{"def": 10}, path=bent(P2, lerp(P2, P1, 0.7), -0.07)),
    dict(team=2, **{"def": 8}, path=bent(P2, at(2), 0.08)),
    dict(team=2, **{"def": 8}, path=bent(P2, at(6), -0.06)),
    dict(team=0, **{"def": 8}, path=circle(at(2), 2400)),
    dict(team=0, **{"def": 10}, path=circle(at(3), 2000)),
]
for q in flights:
    q["path"] = [[round(p[0], 1), round(p[1], 1)] for p in q["path"]]


def fpos(i, t):
    path = flights[i]["path"]
    cum = [0.0]
    for k in range(1, len(path)):
        cum.append(cum[-1] + math.hypot(path[k][0] - path[k - 1][0], path[k][1] - path[k - 1][1]))
    d = max(0.0, min(1.0, t)) * cum[-1]
    k = 1
    while k < len(path) - 1 and cum[k] < d:
        k += 1
    seg = (cum[k] - cum[k - 1]) or 1
    return lerp(path[k - 1], path[k], (d - cum[k - 1]) / seg)


# ---- missiles
missiles, events = [], []
T0 = tick / 30.0


def stamp(f):
    s = T0 + f * 600
    return "%02d:%02d" % (int(s // 60), int(s % 60))


def salvo(team, src, tgt, f0, n, stagger, dur, results, label_src, label_tgt):
    first, last = None, 0
    for k in range(n):
        m0 = f0 + k * stagger
        m1 = m0 + dur
        a = src(m0)
        b = tgt(m1)
        r = results[k]
        if r == "intercept":
            b = lerp(a, b, 0.82)
        elif r == "water":
            dx, dz = b[0] - a[0], b[1] - a[1]
            nn = math.hypot(dx, dz) or 1
            b = [b[0] - dz / nn * 700, b[1] + dx / nn * 700]
        missiles.append(dict(id="s%d_%d" % (int(f0 * 100), k), team=team, f0=round(m0, 4), f1=round(m1, 4),
                             a=[round(a[0], 1), round(a[1], 1)], b=[round(b[0], 1), round(b[1], 1)], res=r))
        last = max(last, m1)
    c = {"hit": 0, "intercept": 0, "water": 0}
    for r in results:
        c[r] += 1
    events.append(dict(f=round(f0, 4), team=team, text="%s lance %d missiles sur %s" % (label_src, n, label_tgt)))
    events.append(dict(f=round(last + 0.004, 4), team=team,
                       text="Résultat : %d touché%s, %d intercepté%s, %d dans l'eau" % (c["hit"], "s" if c["hit"] > 1 else "", c["intercept"], "s" if c["intercept"] > 1 else "", c["water"])))


# le missile REEL de la sauvegarde (equipe 2, en vol au debut)
sp = math.hypot(real_missile["vx"], real_missile["vz"])
dur_r = 0.05
to_r = [real_missile["x"] + real_missile["vx"] * dur_r * 600, real_missile["z"] + real_missile["vz"] * dur_r * 600]
missiles.append(dict(id="reel", team=real_missile["team"], f0=0.0, f1=dur_r, a=[round(real_missile["x"], 1), round(real_missile["z"], 1)],
                     b=[round(to_r[0], 1), round(to_r[1], 1)], res="none", real=True,
                     pre=[[round(real_missile["x"] - real_missile["vx"] * k * 2.0, 1), round(real_missile["z"] - real_missile["vz"] * k * 2.0, 1)] for k in range(1, 12)]))
events.append(dict(f=0.0, team=2, text="Missile réel de la sauvegarde : équipe 2, %d m/s, en vol" % round(real_missile["speed"]), real=True))

salvo(2, lambda f: cpos(2, f), lambda f: cpos(1, f), 0.20, 3, 0.006, 0.055, ["intercept", "intercept", "water"], "Équipe 2", "le porte-avions 1")
salvo(1, lambda f: cpos(1, f), lambda f: cpos(2, f), 0.36, 4, 0.006, 0.060, ["hit", "intercept", "hit", "intercept"], "Équipe 1", "le porte-avions 2")
salvo(0, lambda f: at(4), lambda f: fpos(1, f), 0.50, 2, 0.010, 0.030, ["hit", "intercept"], "L'IA de l'île 4", "un avion de l'équipe 1")
salvo(2, lambda f: cpos(2, f), lambda f: cpos(1, f), 0.66, 5, 0.006, 0.052, ["hit", "intercept", "intercept", "hit", "water"], "Équipe 2", "le porte-avions 1")
salvo(1, lambda f: cpos(1, f), lambda f: cpos(2, f), 0.82, 3, 0.006, 0.055, ["hit", "hit", "intercept"], "Équipe 1", "le porte-avions 2")
events.sort(key=lambda e: e["f"])

import base64, os
icons = {}
idir = os.path.dirname(out_html) + "/icones"
for nm in ("albatros", "manta", "razorbill", "petrel", "seal", "walrus", "bear", "mule", "needlefish", "turret", "carrier", "carrier16", "missile", "lifeboat16"):
    icons[nm] = "data:image/png;base64," + base64.b64encode(open("%s/%s.png" % (idir, nm), "rb").read()).decode()
data = dict(tick=tick, islands=islands, units=units, flights=flights, icons=icons,
            scenario=dict(carriers={"1": CP[1], "2": CP[2]}, missiles=missiles, events=events, seconds=600))
font = open(os.path.dirname(tpl) + "/fontface.css", encoding="utf-8").read()
html = open(tpl, encoding="utf-8").read().replace("/*FONT*/", font).replace("/*DATA*/", json.dumps(data, ensure_ascii=False))
open(out_html, "w", encoding="utf-8").write(html)
print("missiles", len(missiles), "evenements", len(events), "taille", len(html))
print("distance PA1-PA2 au depart / a la fin (km) :", round(math.hypot(*[a - b for a, b in zip(cpos(1, 0), cpos(2, 0))]) / 1000, 1),
      round(math.hypot(*[a - b for a, b in zip(cpos(1, 1), cpos(2, 1))]) / 1000, 1))
print("missile reel :", round(real_missile["x"]), round(real_missile["z"]), "vitesse", round(real_missile["speed"]))

json.dump({k: v for k, v in data.items() if k != "icons"}, open(os.path.dirname(out_html) + "/enregistreur/scenario_demo.json", "w"), ensure_ascii=False)
print("scenario_demo.json ecrit")
