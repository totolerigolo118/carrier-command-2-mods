#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Out-of-game test of the 'squadron speed' bar (fichiers/vitesse_boutons/library_custom_6.lua).

Fake vehicle control screen (like tests/test_horloge.py) loaded with the clock, then the bar:
drawing and position, clicks (consumed in the bar, passed on elsewhere), mode read and set by cc2_vitesse,
screens not concerned, replacement-mod sub-windows, missing patch code, drawing error.
Option --lua53: same test with Lua 5.3, the version embedded in the game.
Option --apercu FILE: writes the drawing calls (JSON) for the preview of the bar.
"""
import json, os, sys
if "--lua53" in sys.argv:
    from lupa.lua53 import LuaRuntime
else:
    from lupa import LuaRuntime

ICI = os.path.dirname(os.path.abspath(__file__))
ATELIER = os.path.dirname(ICI)
ROM = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents/Resources/rom_0/scripts")

FAUX_JEU = r"""
tick = 0
dessins = {}
evenements_ecran = 0
pointeurs_ecran = 0
reglages = {}
equipe_ecran = 1
modes_programme = {}
e_input = { pointer_1 = 7, pointer_2 = 8 }
e_input_action = { press = 0, release = 1 }
function color8(r, g, b, a) return { r, g, b, a } end
function update_get_logic_tick() return tick end
function update_get_screen_team_id() return equipe_ecran end
function update_ui_rectangle(x, y, w, h, c) table.insert(dessins, { "rect", x, y, w, h, c[1], c[2], c[3], c[4] }) end
function update_ui_rectangle_outline(x, y, w, h, c) table.insert(dessins, { "cadre", x, y, w, h, c[1], c[2], c[3], c[4] }) end
function update_ui_get_text_size(t, w, a) return #t * 5, 9 end
function update_ui_text(x, y, t, w, al, c) table.insert(dessins, { "texte", x, y, t, w, c[1], c[2], c[3], c[4] }) end
function begin_get_screen_name() return nom_ecran end
function begin_load() end
function begin() begin_load() end
function update(screen_w, screen_h, ticks) return "return1", screen_w + screen_h + ticks end
function input_event(event, action) evenements_ecran = evenements_ecran + 1 end
function input_pointer(is_hovered, x, y) pointeurs_ecran = pointeurs_ecran + 1 end
-- simulated patch code of the game executable (module vitesse_escadrille)
function cc2_vitesse(equipe, mode)
    if mode ~= nil then
        table.insert(reglages, mode)
        if mode >= 1 and mode <= 3 then modes_programme[equipe] = mode end
    end
    return modes_programme[equipe] or 0
end
"""

ok = True


def verifier(nom, condition, detail=""):
    global ok
    print(("  OK   " if condition else "  FAIL ") + nom + ("" if condition or not detail else " : " + str(detail)))
    ok = ok and bool(condition)


def jeu(nom_ecran="screen_veh_m", sans_greffe=False, mode_initial=None):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(FAUX_JEU)
    lua.globals().nom_ecran = nom_ecran
    if sans_greffe:
        lua.execute("cc2_vitesse = nil")
    if mode_initial:
        lua.execute("modes_programme[1] = %d" % mode_initial)
    for f in (os.path.join(ROM, "library_custom_0.lua"),
              os.path.join(ATELIER, "fichiers", "horloge", "library_custom_1.lua"),
              os.path.join(ATELIER, "fichiers", "vitesse_boutons", "library_custom_6.lua")):
        lua.execute(open(f, encoding="utf-8").read())
    lua.execute("begin()")
    return lua


def image(lua, w=256, h=256):
    lua.execute("dessins = {}")
    r = lua.eval("table.pack(update(%d, %d, 1))" % (w, h))
    d = [list(x.values()) for x in lua.globals().dessins.values()]
    return d, r


def boutons(d):
    """ECO/NORMAL/FLANK texts -> (x, y, text colour)"""
    return {x[3]: x for x in d if x[0] == "texte" and x[3] in ("ECO", "NORMAL", "FLANK")}


def zone(lua, i):
    z = lua.eval("g_vit.zones[%d]" % i)
    return [z[k] for k in (1, 2, 3, 4)]


def cliquer(lua, x, y, action="press"):
    lua.execute("input_pointer(true, %d, %d)" % (x, y))
    lua.execute("input_event(e_input.pointer_1, e_input_action.%s)" % action)


print("1. Vehicle control screen, first game (no mode chosen yet)")
lua = jeu()
d, r = image(lua)
b = boutons(d)
verifier("the three buttons are drawn", set(b) == {"ECO", "NORMAL", "FLANK"}, list(b))
verifier("first time: NORMAL chosen automatically", list(lua.globals().reglages.values()) == [2] and lua.eval("g_vit.mode") == 2)
verifier("update keeps its return values", (r[1], r[2], r["n"]) == ("return1", 513, 2), list(r.values()))
verifier("the clock is still drawn", any(x[0] == "texte" and str(x[3]).startswith("GAME TIME") for x in d))
zs = [zone(lua, i) for i in (1, 2, 3)]
verifier("buttons on the last line (below the map scale, y >= 236)", all(z[1] >= 236 and z[1] + z[3] <= 254 for z in zs), zs)
verifier("buttons inside the screen, on the right, not overlapping",
         zs[0][0] + zs[0][2] < zs[1][0] and zs[1][0] + zs[1][2] < zs[2][0] and zs[2][0] + zs[2][2] <= 256 and zs[0][0] > 120, zs)
horloge = [x for x in d if x[0] == "rect" and x[1] == 4]
fond = [x for x in d if x[0] == "rect" and x[2] >= 230 and x[1] > 100 and x[8] == 210]
verifier("no overlap with the clock", horloge and fond and horloge[0][1] + horloge[0][3] < fond[0][1],
         (horloge[:1], fond[:1]))
actif = [x for x in d if x[0] == "rect" and x[1:5] == zs[1]]
verifier("NORMAL is filled in cyan", actif and actif[0][5:8] == [16, 255, 255], actif)
verifier("text of the active button in black, of the others in a light colour", b["NORMAL"][5:8] == [0, 0, 0] and b["ECO"][5:8] == [190, 204, 204])
if "--apercu" in sys.argv:
    cliquer(lua, zs[2][0] + 3, zs[2][1] + 3)
    cliquer(lua, zs[2][0] + 3, zs[2][1] + 3, "release")
    apercu = {}
    for nom, m in (("ECO", 1), ("NORMAL", 2), ("FLANK", 3)):
        lua.execute("modes_programme[1] = %d" % m)
        apercu[nom] = image(lua)[0]
    json.dump(apercu, open(sys.argv[sys.argv.index("--apercu") + 1], "w"))

print("2. Clicks")
lua = jeu()
image(lua)
z3 = zone(lua, 3)
avant = lua.globals().evenements_ecran
cliquer(lua, z3[0] + 2, z3[1] + 2)
verifier("click on FLANK: mode 3 sent to the executable", list(lua.globals().reglages.values())[-1] == 3)
verifier("click on FLANK: the screen does not receive the click", lua.globals().evenements_ecran == avant)
cliquer(lua, z3[0] + 2, z3[1] + 2, "release")
verifier("release after a click in the bar: not passed on either", lua.globals().evenements_ecran == avant)
d, _ = image(lua)
actif = [x for x in d if x[0] == "rect" and x[1:5] == zone(lua, 3)]
verifier("FLANK is filled in orange on the next frame", actif and actif[0][5:8] == [255, 176, 32], actif)
verifier("the pointer is still passed on to the screen", lua.globals().pointeurs_ecran >= 2)
z1 = zone(lua, 1)
cliquer(lua, z1[0] + 1, z1[1] + 1)
cliquer(lua, z1[0] + 1, z1[1] + 1, "release")
verifier("click on ECO: mode 1", lua.eval("modes_programme[1]") == 1)
avant = lua.globals().evenements_ecran
cliquer(lua, 100, 100)
cliquer(lua, 100, 100, "release")
verifier("click on the map: passed on to the screen (press + release)", lua.globals().evenements_ecran == avant + 2)
avant = lua.globals().evenements_ecran
cliquer(lua, 100, 100)
cliquer(lua, z3[0] + 2, z3[1] + 2, "release")
verifier("press on the map, release on the bar: both passed on, mode unchanged",
         lua.globals().evenements_ecran == avant + 2 and lua.eval("modes_programme[1]") == 1)
avant = lua.globals().evenements_ecran
lua.execute("input_pointer(false, %d, %d)" % (z3[0] + 2, z3[1] + 2))
lua.execute("input_event(e_input.pointer_1, e_input_action.press)")
verifier("pointer outside the screen: click passed on", lua.globals().evenements_ecran == avant + 1)
avant = lua.globals().evenements_ecran
lua.execute("input_pointer(true, %d, %d)" % (z3[0] + 2, z3[1] + 2))
lua.execute("input_event(e_input.pointer_2, e_input_action.press)")
verifier("right click on the bar: passed on to the screen", lua.globals().evenements_ecran == avant + 1)

print("3. Mode already chosen in a previous game")
lua = jeu(mode_initial=3)
d, _ = image(lua)
verifier("FLANK restored, nothing sent back to the executable", lua.eval("g_vit.mode") == 3 and len(lua.globals().reglages) == 0)
lua.execute("equipe_ecran = 4")
image(lua)
verifier("other team: its own mode (NORMAL the first time)", lua.eval("modes_programme[4]") == 2)

print("4. Screens and cases where the bar must not appear")
for nom in ("screen_veh_l", "screen_veh_r", "screen_veh_ll", "tacops_left_control", "tacops_middle_control", "tacops_right_control"):
    verifier("bar on " + nom, len(boutons(image(jeu(nom))[0])) == 3)
for nom in ("screen_veh_top_m", "holomap_screen", "sidebar_1", "screen_veh_captchair"):
    lua = jeu(nom)
    d, _ = image(lua)
    verifier("nothing on " + nom + " (no drawing, no click intercepted)",
             not boutons(d) and lua.eval("input_event == vit_input_event") is False and lua.eval("update == vit_update") is False)
lua = jeu(sans_greffe=True)
d, _ = image(lua)
avant = lua.globals().evenements_ecran
cliquer(lua, 240, 248)
verifier("without the executable module: no bar, clicks passed on", not boutons(d) and lua.globals().evenements_ecran == avant + 1)
lua = jeu()
lua.execute("g_screen_index = 2")
d, _ = image(lua)
avant = lua.globals().evenements_ecran
cliquer(lua, 240, 248)
verifier("replacement-mod sub-window open: no bar, clicks passed on", not boutons(d) and lua.globals().evenements_ecran == avant + 1)
lua.execute("g_screen_index = 0 ; g_viewing_vehicle_id = 12")
verifier("vehicle view (replacement mod): no bar", not boutons(image(lua)[0]))
lua = jeu()
verifier("screen too small (128 x 128): no bar", not boutons(image(lua, 128, 128)[0]))
lua = jeu()
lua.execute("function update_ui_text() error('font missing') end")
d, r = image(lua)
verifier("drawing error: update does not break and keeps its return values", (r[1], r[2], r["n"]) == ("return1", 513, 2))
avant = lua.globals().evenements_ecran
cliquer(lua, 240, 248)
verifier("drawing error: clicks passed on to the screen", lua.globals().evenements_ecran == avant + 1)
lua = jeu()
lua.execute("begin()")
d, _ = image(lua)
verifier("begin() called twice: only one bar", len([x for x in d if x[0] == "texte" and x[3] == "FLANK"]) == 1)

print("\nRESULT: " + ("ALL PASSED" if ok else "THERE ARE FAILURES"))
sys.exit(0 if ok else 1)
