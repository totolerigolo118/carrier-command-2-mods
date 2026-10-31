#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the game clock outside the game: fake screen, fake clock.

Loads, like the game does, the screen script, then library_custom_0.lua (tricolour smoke,
the one installed in the game), then library_custom_1.lua (the clock), calls begin() then
update(). Option --lua53: same test with Lua 5.3, the version embedded in the game.
"""
import os, sys
if "--lua53" in sys.argv:
    from lupa.lua53 import LuaRuntime
else:
    from lupa import LuaRuntime

ICI = os.path.dirname(os.path.abspath(__file__))
ROM = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents/Resources/rom_0/scripts")

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
    return "return1", screen_w + screen_h + ticks
end
"""


def jeu(nom_ecran="screen_veh_m", texte_casse=False):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(FAUX_JEU)
    lua.globals().nom_ecran = nom_ecran
    if texte_casse:
        lua.execute("function update_ui_text() error('font missing') end")
    for f in (os.path.join(ROM, "library_custom_0.lua"), os.path.join(os.path.dirname(ICI), "fichiers", "horloge", "library_custom_1.lua")):
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
    print("  %-52s %s %s" % (nom, "OK" if condition else "FAIL", detail))


print("\nGame clock test (%s)" % LuaRuntime().eval("_VERSION"))
lua = jeu()
for tick, attendu in ((0, "0:00.0"), (4410, "2:27.0"), (30 * 3600 + 4410 + 3, "1:02:27.1")):
    t, r = afficher(lua, tick)
    verifier("tick %d displays %s" % (tick, attendu), t == ["GAME TIME  " + attendu], str(t))
verifier("the original screen always returns its values", r[1] == "return1" and r[2] == 441, str((r[1], r[2])))
verifier("the original screen ran every time", lua.globals().appels_update == 3)

lua = jeu(texte_casse=True)
t, r = afficher(lua, 100)
verifier("font missing: the original screen still works", r[1] == "return1" and lua.globals().appels_update == 1)

for nom in ("screen_inv_l", "screen_nav_top_r", "holomap_screen", "screen_veh_top_m"):
    lua = jeu(nom)
    t, r = afficher(lua, 100)
    verifier("nothing displayed on " + nom, t == [] and r[1] == "return1")

print("\nRESULT: " + ("ALL PASSED" if ok else "THERE ARE FAILURES"))
sys.exit(0 if ok else 1)
