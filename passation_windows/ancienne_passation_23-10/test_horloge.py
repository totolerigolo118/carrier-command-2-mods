#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste l'horloge de jeu hors du jeu : faux ecran, fausse horloge.

Charge, comme le jeu, le script de l'ecran puis library_custom_0.lua (fumee tricolore,
celui installe dans le jeu) puis library_custom_1.lua (l'horloge), appelle begin() puis
update(). Option --lua53 : meme test avec Lua 5.3, la version embarquee dans le jeu.
"""
import os, sys
if "--lua53" in sys.argv:
    from lupa.lua53 import LuaRuntime
else:
    from lupa import LuaRuntime

ICI = os.path.dirname(os.path.abspath(__file__))
ROM = "/Users/UTILISATEUR/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents/Resources/rom_0/scripts"

FAUX_JEU = r"""
tick = 0
textes = {}
appels_update = 0
function color8(r, g, b, a) return { r, g, b, a } end
function update_get_logic_tick() return tick end
function update_ui_rectangle() end
function update_ui_get_text_size(t, w, a) return #t * 5, 9 end
function update_ui_text(x, y, t) table.insert(textes, t) end
function begin_get_screen_name() return nom_ecran end
function begin_load() end
function begin() begin_load() end
function update(screen_w, screen_h, ticks)
    appels_update = appels_update + 1
    return "retour1", screen_w + screen_h + ticks
end
"""


def jeu(nom_ecran="screen_veh_m", texte_casse=False):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(FAUX_JEU)
    lua.globals().nom_ecran = nom_ecran
    if texte_casse:
        lua.execute("function update_ui_text() error('police absente') end")
    for f in (os.path.join(ROM, "library_custom_0.lua"), os.path.join(ICI, "library_custom_1.lua")):
        lua.execute(open(f, encoding="utf-8").read())
    lua.execute("begin()")
    return lua


def afficher(lua, tick):
    lua.globals().tick = tick
    lua.execute("textes = {}")
    r = lua.eval("table.pack(update(240, 200, 1))")
    return list(lua.globals().textes.values()), r


ok = True
def verifier(nom, condition, detail=""):
    global ok
    ok = ok and condition
    print("  %-52s %s %s" % (nom, "OK" if condition else "ECHEC", detail))


print("\nTest de l'horloge de jeu (%s)" % LuaRuntime().eval("_VERSION"))
lua = jeu()
for tick, attendu in ((0, "0:00.0"), (4410, "2:27.0"), (30 * 3600 + 4410 + 3, "1:02:27.1")):
    t, r = afficher(lua, tick)
    verifier("top %d affiche %s" % (tick, attendu), t == ["TEMPS DE JEU  " + attendu], str(t))
verifier("l'ecran d'origine renvoie toujours ses valeurs", r[1] == "retour1" and r[2] == 441, str((r[1], r[2])))
verifier("l'ecran d'origine a tourne a chaque fois", lua.globals().appels_update == 3)

lua = jeu(texte_casse=True)
t, r = afficher(lua, 100)
verifier("police absente : l'ecran d'origine marche quand meme", r[1] == "retour1" and lua.globals().appels_update == 1)

for nom in ("screen_inv_l", "screen_nav_top_r", "holomap_screen", "screen_veh_top_m"):
    lua = jeu(nom)
    t, r = afficher(lua, 100)
    verifier("rien d'affiche sur " + nom, t == [] and r[1] == "retour1")

print("\nRESULTAT : " + ("TOUT EST BON" if ok else "IL Y A DES ECHECS"))
sys.exit(0 if ok else 1)
