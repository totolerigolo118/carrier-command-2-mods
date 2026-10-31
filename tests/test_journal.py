#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste le journal des atterrissages hors du jeu : faux porte-avions, faux avions, fausse horloge.

Charge, comme le jeu, le script de l'ecran puis library_custom_0.lua (fumee tricolore), 1 (horloge)
et 4 (le journal), appelle begin() puis update() a chaque « image » en faisant avancer les etats des
appareils selon un scenario connu, et verifie les heures affichees.
Option --lua53 : meme test avec Lua 5.3, la version embarquee dans le jeu.
"""
import os, sys
if "--lua53" in sys.argv:
    from lupa.lua53 import LuaRuntime
else:
    from lupa import LuaRuntime

ICI = os.path.dirname(os.path.abspath(__file__))
FICHIERS = os.path.join(os.path.dirname(ICI), "fichiers")
ROM = "/Users/UTILISATEUR/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents/Resources/rom_0/scripts"

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
    return "retour1", screen_w + screen_h + ticks
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
    print("  %-58s %s %s" % (nom, "OK" if condition else "ECHEC", detail))


S = 30   # tops par seconde de jeu
# scenario : (seconde, id, etat). Etats : 0 vol, 1 piste, 4 range, 5 file, 6 pont.
# avion 11 : file 0 s, piste 20 s, pont 90 s, range 150 s
# avion 12 : file 5 s, piste 120 s, APPROCHE RATEE 150 s (retour en file), piste 240 s, pont 310 s, range 370 s
# avion 13 : file 10 s, piste 330 s, pont 400 s, range 460 s
# helico 14 : file 15 s, piste 470 s, pont 500 s, range 540 s
SCENARIO = [(0, 11, 5), (5, 12, 5), (10, 13, 5), (15, 14, 5), (20, 11, 1), (90, 11, 6), (120, 12, 1), (150, 11, 4),
            (150, 12, 5), (240, 12, 1), (310, 12, 6), (330, 13, 1), (370, 12, 4), (400, 13, 6), (460, 13, 4),
            (470, 14, 1), (500, 14, 6), (540, 14, 4)]


def jouer(lua, jusqua, pas=1, trou=None):
    """Fait avancer le jeu seconde par seconde jusqu'a « jusqua » (s) ; trou = (debut, fin) sans image."""
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


print("\nTest du journal des atterrissages (%s)" % LuaRuntime().eval("_VERSION"))
lua = jeu()
t, r = image(lua, 0)
verifier("avant tout retour : seule l'horloge s'affiche", t == ["TEMPS DE JEU  0:00.0"], str(t))

lua = jeu()
t, r = jouer(lua, 200)
verifier("en cours : horloge + titre + colonnes + 4 lignes + 3 de resume", len(t) == 10, str(len(t)))
verifier("en cours : « EN COURS 3:20 : 3 avions + 1 helico »", "EN COURS 3:20 : 3 avions + 1 helico" in t, str(t))

lua = jeu()
t, r = jouer(lua, 600)
attendu = [
    "TEMPS DE JEU  10:00.0",
    "JOURNAL ATTERRISSAGES (temps de jeu)",
    "          piste   pont hangar",
    "1 avion    0:20   1:30   2:30",
    "2 avion    4:00   5:10   6:10",
    "3 avion    5:30   6:40   7:40",
    "4 helico   7:50   8:20   9:00",
    "FINI en 9:00 : 3 avions + 1 helico",
    "piste toutes les 2:30  ratees 1",
    "approche 1:00  pont>hangar 0:55",
]
for a, b in zip(attendu, t):
    verifier("« %s »" % a, a == b, "" if a == b else "lu : " + b)
verifier("nombre de lignes", len(t) == len(attendu), str(len(t)))
verifier("aucune ligne de plus de 36 signes (sinon elle passe a la ligne en jeu)", max(len(x) for x in t) <= 36,
         str(max(len(x) for x in t)))
verifier("le vehicule terrestre et l'avion d'un autre bateau sont ignores", not any("5 " in x[:2] for x in t))
verifier("l'ecran d'origine renvoie toujours ses valeurs", r[1] == "retour1" and r[2] == 457, str((r[1], r[2])))

lua = jeu()
t, r = jouer(lua, 600, trou=(100, 110))
verifier("ecran fige 10 s pendant le retour : alerte affichee", any("ecran fige 0:1" in x for x in t), str(t[-2:]))

lua = jeu()
t, r = jouer(lua, 600, pas=3)
verifier("ecran mis a jour toutes les 3 s : resultat a 3 s pres", any(x.startswith("FINI") for x in t)
         and not any("ecran fige" in x for x in t), str(t[5:8]))

lua = jeu()
jouer(lua, 600)
lua.execute("for _, v in ipairs(vehicules) do if v.id == 11 then v.etat = 5 end end")
t, r = image(lua, 700 * S)
verifier("nouveau retour : le journal repart de zero", "1 avion   --:--  --:--  --:--" in t
         and "EN COURS 0:00 : 1 avion" in t, str(t[:3]))

lua = jeu()
lua.execute("function update_get_map_vehicle_count() error('panne') end")
lua.execute("table.insert(vehicules, { id = 11, def = 0, parent = 1, etat = 5 })")
t, r = image(lua, 30)
verifier("erreur dans le journal : l'ecran et l'horloge marchent quand meme",
         r[1] == "retour1" and t == ["TEMPS DE JEU  0:01.0"], str(t))

for nom in ("screen_inv_l", "screen_nav_top_r", "holomap_screen", "screen_veh_top_m"):
    lua = jeu(nom)
    t, r = jouer(lua, 60)
    verifier("rien d'affiche sur " + nom, t == [] and r[1] == "retour1", str(t))

print("\nRESULTAT : " + ("TOUT EST BON" if ok else "IL Y A DES ECHECS"))
sys.exit(0 if ok else 1)
