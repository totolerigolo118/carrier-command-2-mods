#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test hors jeu de la barre « vitesse de l'escadrille » (fichiers/vitesse_boutons/library_custom_6.lua).

Faux ecran de controle des vehicules (comme tests/test_horloge.py) charge avec l'horloge puis la barre :
dessin et position, clics (consommes dans la barre, transmis ailleurs), mode lu et regle par cc2_vitesse,
ecrans non concernes, sous-fenetres de Revolution, greffe absente, erreur de dessin.
Option --lua53 : meme test avec Lua 5.3, la version embarquee dans le jeu.
Option --apercu FICHIER : ecrit les appels de dessin (JSON) pour l'apercu de la barre.
"""
import json, os, sys
if "--lua53" in sys.argv:
    from lupa.lua53 import LuaRuntime
else:
    from lupa import LuaRuntime

ICI = os.path.dirname(os.path.abspath(__file__))
ATELIER = os.path.dirname(ICI)
ROM = "/Users/UTILISATEUR/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents/Resources/rom_0/scripts"

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
function update(screen_w, screen_h, ticks) return "retour1", screen_w + screen_h + ticks end
function input_event(event, action) evenements_ecran = evenements_ecran + 1 end
function input_pointer(is_hovered, x, y) pointeurs_ecran = pointeurs_ecran + 1 end
-- greffe du programme (module vitesse_escadrille) simulee
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
    print(("  OK   " if condition else "  ECHEC ") + nom + ("" if condition or not detail else " : " + str(detail)))
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
    """textes ECO/NORMAL/FLANK -> (x, y, couleur du texte)"""
    return {x[3]: x for x in d if x[0] == "texte" and x[3] in ("ECO", "NORMAL", "FLANK")}


def zone(lua, i):
    z = lua.eval("g_vit.zones[%d]" % i)
    return [z[k] for k in (1, 2, 3, 4)]


def cliquer(lua, x, y, action="press"):
    lua.execute("input_pointer(true, %d, %d)" % (x, y))
    lua.execute("input_event(e_input.pointer_1, e_input_action.%s)" % action)


print("1. Ecran de controle des vehicules, premiere partie (aucun mode encore choisi)")
lua = jeu()
d, r = image(lua)
b = boutons(d)
verifier("les trois boutons sont dessines", set(b) == {"ECO", "NORMAL", "FLANK"}, list(b))
verifier("premiere fois : NORMAL choisi tout seul", list(lua.globals().reglages.values()) == [2] and lua.eval("g_vit.mode") == 2)
verifier("update garde ses retours", (r[1], r[2], r["n"]) == ("retour1", 513, 2), list(r.values()))
verifier("l'horloge est toujours dessinee", any(x[0] == "texte" and str(x[3]).startswith("TEMPS DE JEU") for x in d))
zs = [zone(lua, i) for i in (1, 2, 3)]
verifier("boutons sur la derniere ligne (sous l'echelle de la carte, y >= 236)", all(z[1] >= 236 and z[1] + z[3] <= 254 for z in zs), zs)
verifier("boutons dans l'ecran, a droite, sans se chevaucher",
         zs[0][0] + zs[0][2] < zs[1][0] and zs[1][0] + zs[1][2] < zs[2][0] and zs[2][0] + zs[2][2] <= 256 and zs[0][0] > 120, zs)
horloge = [x for x in d if x[0] == "rect" and x[1] == 4]
fond = [x for x in d if x[0] == "rect" and x[2] >= 230 and x[1] > 100 and x[8] == 210]
verifier("pas de chevauchement avec l'horloge", horloge and fond and horloge[0][1] + horloge[0][3] < fond[0][1],
         (horloge[:1], fond[:1]))
actif = [x for x in d if x[0] == "rect" and x[1:5] == zs[1]]
verifier("NORMAL est rempli en cyan", actif and actif[0][5:8] == [16, 255, 255], actif)
verifier("texte du bouton actif en noir, des autres en clair", b["NORMAL"][5:8] == [0, 0, 0] and b["ECO"][5:8] == [190, 204, 204])
if "--apercu" in sys.argv:
    cliquer(lua, zs[2][0] + 3, zs[2][1] + 3)
    cliquer(lua, zs[2][0] + 3, zs[2][1] + 3, "release")
    apercu = {}
    for nom, m in (("ECO", 1), ("NORMAL", 2), ("FLANK", 3)):
        lua.execute("modes_programme[1] = %d" % m)
        apercu[nom] = image(lua)[0]
    json.dump(apercu, open(sys.argv[sys.argv.index("--apercu") + 1], "w"))

print("2. Clics")
lua = jeu()
image(lua)
z3 = zone(lua, 3)
avant = lua.globals().evenements_ecran
cliquer(lua, z3[0] + 2, z3[1] + 2)
verifier("clic sur FLANK : mode 3 envoye au programme", list(lua.globals().reglages.values())[-1] == 3)
verifier("clic sur FLANK : l'ecran ne recoit pas le clic", lua.globals().evenements_ecran == avant)
cliquer(lua, z3[0] + 2, z3[1] + 2, "release")
verifier("relachement apres un clic dans la barre : pas transmis non plus", lua.globals().evenements_ecran == avant)
d, _ = image(lua)
actif = [x for x in d if x[0] == "rect" and x[1:5] == zone(lua, 3)]
verifier("FLANK est rempli en orange a l'image suivante", actif and actif[0][5:8] == [255, 176, 32], actif)
verifier("le pointeur est toujours transmis a l'ecran", lua.globals().pointeurs_ecran >= 2)
z1 = zone(lua, 1)
cliquer(lua, z1[0] + 1, z1[1] + 1)
cliquer(lua, z1[0] + 1, z1[1] + 1, "release")
verifier("clic sur ECO : mode 1", lua.eval("modes_programme[1]") == 1)
avant = lua.globals().evenements_ecran
cliquer(lua, 100, 100)
cliquer(lua, 100, 100, "release")
verifier("clic sur la carte : transmis a l'ecran (appui + relachement)", lua.globals().evenements_ecran == avant + 2)
avant = lua.globals().evenements_ecran
cliquer(lua, 100, 100)
cliquer(lua, z3[0] + 2, z3[1] + 2, "release")
verifier("appui sur la carte, relache sur la barre : les deux transmis, mode inchange",
         lua.globals().evenements_ecran == avant + 2 and lua.eval("modes_programme[1]") == 1)
avant = lua.globals().evenements_ecran
lua.execute("input_pointer(false, %d, %d)" % (z3[0] + 2, z3[1] + 2))
lua.execute("input_event(e_input.pointer_1, e_input_action.press)")
verifier("pointeur hors de l'ecran : clic transmis", lua.globals().evenements_ecran == avant + 1)
avant = lua.globals().evenements_ecran
lua.execute("input_pointer(true, %d, %d)" % (z3[0] + 2, z3[1] + 2))
lua.execute("input_event(e_input.pointer_2, e_input_action.press)")
verifier("clic droit sur la barre : transmis a l'ecran", lua.globals().evenements_ecran == avant + 1)

print("3. Mode deja choisi lors d'une partie precedente")
lua = jeu(mode_initial=3)
d, _ = image(lua)
verifier("FLANK repris, rien de renvoye au programme", lua.eval("g_vit.mode") == 3 and len(lua.globals().reglages) == 0)
lua.execute("equipe_ecran = 4")
image(lua)
verifier("autre equipe : son propre mode (NORMAL la premiere fois)", lua.eval("modes_programme[4]") == 2)

print("4. Ecrans et cas ou la barre ne doit pas apparaitre")
for nom in ("screen_veh_l", "screen_veh_r", "screen_veh_ll", "tacops_left_control", "tacops_middle_control", "tacops_right_control"):
    verifier("barre sur " + nom, len(boutons(image(jeu(nom))[0])) == 3)
for nom in ("screen_veh_top_m", "holomap_screen", "sidebar_1", "screen_veh_captchair"):
    lua = jeu(nom)
    d, _ = image(lua)
    verifier("rien sur " + nom + " (ni dessin, ni clic intercepte)",
             not boutons(d) and lua.eval("input_event == vit_input_event") is False and lua.eval("update == vit_update") is False)
lua = jeu(sans_greffe=True)
d, _ = image(lua)
avant = lua.globals().evenements_ecran
cliquer(lua, 240, 248)
verifier("sans le module programme : pas de barre, clics transmis", not boutons(d) and lua.globals().evenements_ecran == avant + 1)
lua = jeu()
lua.execute("g_screen_index = 2")
d, _ = image(lua)
avant = lua.globals().evenements_ecran
cliquer(lua, 240, 248)
verifier("sous-fenetre de Revolution ouverte : pas de barre, clics transmis", not boutons(d) and lua.globals().evenements_ecran == avant + 1)
lua.execute("g_screen_index = 0 ; g_viewing_vehicle_id = 12")
verifier("vue d'un vehicule (Revolution) : pas de barre", not boutons(image(lua)[0]))
lua = jeu()
verifier("ecran trop petit (128 x 128) : pas de barre", not boutons(image(lua, 128, 128)[0]))
lua = jeu()
lua.execute("function update_ui_text() error('police absente') end")
d, r = image(lua)
verifier("erreur de dessin : update ne casse pas et garde ses retours", (r[1], r[2], r["n"]) == ("retour1", 513, 2))
avant = lua.globals().evenements_ecran
cliquer(lua, 240, 248)
verifier("erreur de dessin : clics transmis a l'ecran", lua.globals().evenements_ecran == avant + 1)
lua = jeu()
lua.execute("begin()")
d, _ = image(lua)
verifier("begin() appele deux fois : une seule barre", len([x for x in d if x[0] == "texte" and x[3] == "FLANK"]) == 1)

print("\nRESULTAT : " + ("TOUT EST BON" if ok else "IL Y A DES ECHECS"))
sys.exit(0 if ok else 1)
