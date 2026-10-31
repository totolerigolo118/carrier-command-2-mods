#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the landing log outside the game: fake carrier, fake aircraft, fake clock.

Loads, like the game does, the screen script, then library_custom_0.lua (tricolour smoke), 1 (clock)
and 4 (the log), calls begin() then update() on every "frame" while advancing the states of the
aircraft according to a known scenario, and checks the displayed times.
Option --lua53: same test with Lua 5.3, the version embedded in the game.
"""
import os, sys
if "--lua53" in sys.argv:
    from lupa.lua53 import LuaRuntime
else:
    from lupa import LuaRuntime

ICI = os.path.dirname(os.path.abspath(__file__))
FICHIERS = os.path.join(os.path.dirname(ICI), "fichiers")
ROM = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents/Resources/rom_0/scripts")

FAUX_JEU = r"""
tick = 0
textes = {}
appels_update = 0
vehicules = {}            -- { id, def, parent, etat }
function color8(r, g, b, a) return { r, g, b, a } end
function update_get_logic_tick() return tick end
function update_ui_rectangle() end
function update_ui_get_text_size(t, w, a) return #t * 5, 9 end
function update_ui_text(x, y, t) table.insert(textes, t) end
function begin_get_screen_name() return nom_ecran end
local function objet(v)
    return {
        get = function(self) return v ~= nil end,
        get_id = function(self) return v.id end,
        get_dock_state = function(self) return v.etat end,
        get_dock_parent_id = function(self) return v.parent end,
        get_definition_index = function(self) return v.def end,
    }
end
function update_get_screen_vehicle() return objet({ id = 1 }) end
function update_get_map_vehicle_count() return #vehicules end
function update_get_map_vehicle_by_index(i) return objet(vehicules[i + 1]) end
function update_get_map_vehicle_by_id(id)
    for _, v in ipairs(vehicules) do if v.id == id then return objet(v) end end
    return objet(nil)
end
function begin_load() end
function begin() begin_load() end
function update(screen_w, screen_h, ticks)
    appels_update = appels_update + 1
    return "return1", screen_w + screen_h + ticks
end
"""


def jeu(nom_ecran="screen_veh_m"):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(FAUX_JEU)
    lua.execute(open(os.path.join(ROM, "library_enum.lua"), encoding="utf-8").read())
    lua.globals().nom_ecran = nom_ecran
    for f in (os.path.join(ROM, "library_custom_0.lua"),
              os.path.join(FICHIERS, "horloge", "library_custom_1.lua"),
              os.path.join(FICHIERS, "journal", "library_custom_4.lua")):
        lua.execute(open(f, encoding="utf-8").read())
    lua.execute("begin()")
    return lua


def image(lua, tick):
    lua.globals().tick = tick
    lua.execute("textes = {}")
    r = lua.eval("table.pack(update(256, 200, 1))")
    return list(lua.globals().textes.values()), r


ok = True
def verifier(nom, condition, detail=""):
    global ok
    ok = ok and condition
    print("  %-58s %s %s" % (nom, "OK" if condition else "FAIL", detail))


S = 30   # game ticks per second
# scenario: (second, id, state). States: 0 flying, 1 runway, 4 stowed, 5 queue, 6 deck.
# plane 11: queue 0 s, runway 20 s, deck 90 s, stowed 150 s
# plane 12: queue 5 s, runway 120 s, MISSED APPROACH 150 s (back to the queue), runway 240 s, deck 310 s, stowed 370 s
# plane 13: queue 10 s, runway 330 s, deck 400 s, stowed 460 s
# helicopter 14: queue 15 s, runway 470 s, deck 500 s, stowed 540 s
SCENARIO = [(0, 11, 5), (5, 12, 5), (10, 13, 5), (15, 14, 5), (20, 11, 1), (90, 11, 6), (120, 12, 1), (150, 11, 4),
            (150, 12, 5), (240, 12, 1), (310, 12, 6), (330, 13, 1), (370, 12, 4), (400, 13, 6), (460, 13, 4),
            (470, 14, 1), (500, 14, 6), (540, 14, 4)]


def jouer(lua, jusqua, pas=1, trou=None):
    """Advances the game second by second up to 'jusqua' (s); trou = (start, end) with no frames."""
    lua.execute("vehicules = {}")
    defs = {11: "chassis_air_wing_light", 12: "chassis_air_wing_light", 13: "chassis_air_wing_heavy",
            14: "chassis_air_rotor_light", 20: "chassis_land_wheel_light"}
    for i, d in defs.items():
        lua.execute("table.insert(vehicules, { id = %d, def = e_game_object_type.%s, parent = 1, etat = 4 })" % (i, d))
    lua.execute("table.insert(vehicules, { id = 30, def = e_game_object_type.chassis_air_wing_light, parent = 99, etat = 5 })")
    textes, r, fait = [], None, 0
    for s in range(0, jusqua + 1, pas):
        while fait < len(SCENARIO) and SCENARIO[fait][0] <= s:
            t, i, e = SCENARIO[fait]
            fait += 1
            lua.execute("for _, v in ipairs(vehicules) do if v.id == %d then v.etat = %d end end" % (i, e))
        if trou and trou[0] <= s < trou[1]:
            continue
        textes, r = image(lua, s * S)
    return textes, r


print("\nLanding log test (%s)" % LuaRuntime().eval("_VERSION"))
lua = jeu()
t, r = image(lua, 0)
verifier("before any return: only the clock is displayed", t == ["GAME TIME  0:00.0"], str(t))

lua = jeu()
t, r = jouer(lua, 200)
verifier("ongoing: clock + title + columns + 4 rows + 3 summary lines", len(t) == 10, str(len(t)))
verifier('ongoing: "ONGOING 3:20 : 3 planes + 1 copter"', "ONGOING 3:20 : 3 planes + 1 copter" in t, str(t))

lua = jeu()
t, r = jouer(lua, 600)
attendu = [
    "GAME TIME  10:00.0",
    "LANDING LOG (game time)",
    "         runway   deck hangar",
    "1 plane    0:20   1:30   2:30",
    "2 plane    4:00   5:10   6:10",
    "3 plane    5:30   6:40   7:40",
    "4 copter   7:50   8:20   9:00",
    "DONE in 9:00 : 3 planes + 1 copter",
    "runway every 2:30  missed 1",
    "approach 1:00  deck>hangar 0:55",
]
for a, b in zip(attendu, t):
    verifier('"%s"' % a, a == b, "" if a == b else "read: " + b)
verifier("number of lines", len(t) == len(attendu), str(len(t)))
verifier("no line longer than 36 characters (otherwise it wraps in game)", max(len(x) for x in t) <= 36,
         str(max(len(x) for x in t)))
verifier("the land vehicle and the plane of another ship are ignored", not any("5 " in x[:2] for x in t))
verifier("the original screen always returns its values", r[1] == "return1" and r[2] == 457, str((r[1], r[2])))

lua = jeu()
t, r = jouer(lua, 600, trou=(100, 110))
verifier("screen frozen for 10 s during the return: warning displayed", any("screen frozen 0:1" in x for x in t), str(t[-2:]))

lua = jeu()
t, r = jouer(lua, 600, pas=3)
verifier("screen updated every 3 s: result to within 3 s", any(x.startswith("DONE") for x in t)
         and not any("screen frozen" in x for x in t), str(t[5:8]))

lua = jeu()
jouer(lua, 600)
lua.execute("for _, v in ipairs(vehicules) do if v.id == 11 then v.etat = 5 end end")
t, r = image(lua, 700 * S)
verifier("new return: the log starts again from zero", "1 plane   --:--  --:--  --:--" in t
         and "ONGOING 0:00 : 1 plane" in t, str(t[:3]))

lua = jeu()
lua.execute("function update_get_map_vehicle_count() error('failure') end")
lua.execute("table.insert(vehicules, { id = 11, def = 0, parent = 1, etat = 5 })")
t, r = image(lua, 30)
verifier("error in the log: the screen and the clock still work",
         r[1] == "return1" and t == ["GAME TIME  0:01.0"], str(t))

for nom in ("screen_inv_l", "screen_nav_top_r", "holomap_screen", "screen_veh_top_m"):
    lua = jeu(nom)
    t, r = jouer(lua, 60)
    verifier("nothing displayed on " + nom, t == [] and r[1] == "return1", str(t))

print("\nRESULT: " + ("ALL PASSED" if ok else "THERE ARE FAILURES"))
sys.exit(0 if ok else 1)
