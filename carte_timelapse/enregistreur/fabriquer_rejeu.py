"""Assemble la page de rejeu (carte_rejeu.html) : modele + police + pictos du jeu + journal de demonstration.
Usage : python3 -I fabriquer_rejeu.py <modele.html> <police.css> <journal_demo.log> <scenario_demo.json> <dossier_icones> <sortie.html>
"""
import base64
import json
import os
import sys

tpl, fontcss, demolog, scen, icodir, out = sys.argv[1:7]
icons = {}
for nm in ("albatros", "manta", "razorbill", "petrel", "seal", "walrus", "bear", "mule", "needlefish", "turret", "carrier", "carrier16", "missile", "lifeboat16"):
    icons[nm] = "data:image/png;base64," + base64.b64encode(open("%s/%s.png" % (icodir, nm), "rb").read()).decode()
D = json.load(open(scen, encoding="utf-8"))
assets = dict(icons=icons, demoHalf={str(i["id"]): i["half"] for i in D["islands"]})
log = open(demolog, encoding="utf-8").read()
assert "</script" not in log.lower()
html = (open(tpl, encoding="utf-8").read()
        .replace("/*FONT*/", open(fontcss, encoding="utf-8").read())
        .replace("/*ASSETS*/", json.dumps(assets, ensure_ascii=False))
        .replace("/*DEMOLOG*/", log))
open(out, "w", encoding="utf-8").write(html)
print("ecrit :", out, "|", round(len(html) / 1024), "Ko")
