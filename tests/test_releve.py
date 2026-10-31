#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste le releve des performances hors du jeu : faux ecrans, fausses unites, fausse horloge.

Charge, comme le jeu, le script de l'ecran puis library_custom_0.lua (fumee tricolore), 1 (horloge),
4 (journal) et 5 (le releve), appelle begin() puis update() a chaque « image », et lit ce que print()
aurait ecrit dans le fichier. Option --lua53 : meme test avec Lua 5.3, la version embarquee dans le jeu.

Option --fichier CHEMIN : en plus, simule une partie de 15 minutes (plusieurs ecrans, pilotage, combat,
pause) et ecrit le releve obtenu dans CHEMIN, pour tester l'outil des courbes (faire_courbes.py).
"""
import math, os, random, sys
if "--lua53" in sys.argv:
    from lupa.lua53 import LuaRuntime
else:
    from lupa import LuaRuntime

ICI = os.path.dirname(os.path.abspath(__file__))
FICHIERS = os.path.join(os.path.dirname(ICI), "fichiers")
ROM = "/Users/UTILISATEUR/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents/Resources/rom_0/scripts"

FAUX_JEU = r"""
epoch = 1792850000
tick = 0
appels_update = 0
vehicules = {}            -- { id, def, equipe, etat, visible }
casse = {}                -- noms de fonctions du jeu qui levent une erreur
allume, focus = true, false
function color8(r, g, b, a) return { r, g, b, a } end
function update_get_logic_tick() return tick end
function update_get_time_since_epoch() if casse.epoch then error("x") end return epoch end
function update_ui_rectangle() end
function update_ui_get_text_size(t, w, a) return #t * 5, 9 end
function update_ui_text(x, y, t) end
function update_get_screen_team_id() return 1 end
function update_get_missile_count() return missiles or 0 end
function update_get_projectile_count() return obus or 0 end
function update_get_map_destroyed_vehicle_count() return 3 end
function update_get_screen_state_active() return allume end
function update_get_is_focus_local() return focus end
local function objet(v)
    return {
        get = function(self) return v ~= nil end,
        get_id = function(self) return v.id end,
        get_team = function(self) return v.equipe end,
        get_dock_state = function(self) return v.etat end,
        get_dock_parent_id = function(self) return 1 end,
        get_definition_index = function(self) return v.def end,
        get_is_visible = function(self) return v.visible end,
    }
end
function update_get_screen_vehicle() return objet({ id = 1 }) end
function update_get_map_vehicle_count() if casse.compte then error("compte") end return #vehicules end
function update_get_map_vehicle_by_index(i) return objet(vehicules[i + 1]) end
function update_get_map_vehicle_by_id(id)
    for _, v in ipairs(vehicules) do if v.id == id then return objet(v) end end
    return objet(nil)
end
function print(...)
    local t = table.pack(...)
    for k = 1, t.n do t[k] = tostring(t[k]) end
    sortie(table.concat(t, "\t", 1, t.n))
end
function begin_load() end
function begin() begin_load() end
"""
UPDATE_ECRAN = """
function update(screen_w, screen_h, ticks)
    appels_update = appels_update + 1
    return "retour1", screen_w + screen_h + ticks
end
"""
UPDATE_HUD = """
function update(screen_w, screen_h, tick_fraction, delta_time, local_peer_id, vehicle, map_data)
    appels_update = appels_update + 1
    return "retour1", screen_w + screen_h
end
"""
UPDATE_PAUSE = """
function update(screen_w, screen_h, delta_time)
    appels_update = appels_update + 1
    return "retour1", screen_w + screen_h
end
"""


class Fichier:
    def __init__(self):
        self.lignes = []

    def __call__(self, ligne):
        self.lignes.append(ligne)


def ecran(fichier, nom, genre="ecran", sans=()):
    """genre : ecran (a un nom), hud (affichage de pilotage), pause (menu pause, sans nom)."""
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().sortie = fichier
    lua.execute(FAUX_JEU)
    lua.execute({"ecran": UPDATE_ECRAN, "hud": UPDATE_HUD, "pause": UPDATE_PAUSE}[genre])
    if genre == "ecran":
        lua.execute("function begin_get_screen_name() return %r end" % nom)
    for f in sans:
        lua.execute("%s = nil" % f)
    lua.execute(open(os.path.join(ROM, "library_enum.lua"), encoding="utf-8").read())
    for f in (os.path.join(ROM, "library_custom_0.lua"), os.path.join(FICHIERS, "horloge", "library_custom_1.lua"),
              os.path.join(FICHIERS, "journal", "library_custom_4.lua"), os.path.join(FICHIERS, "releve", "library_custom_5.lua")):
        lua.execute(open(f, encoding="utf-8").read())
    lua.execute("begin()")
    return lua


def image(lua, epoch, tick, genre="ecran", vehicule_pilote=None):
    g = lua.globals()
    g.epoch, g.tick = epoch, tick
    if genre == "hud":
        g.pilote = lua.table_from({"get_definition_index": lua.eval("function(self) return %d end" % (vehicule_pilote or 8))})
        return lua.eval("table.pack(update(240, 200, 0.5, 33, 1, pilote, nil))")
    return lua.eval("table.pack(update(240, 200, 1))")


def mettre_unites(lua, unites):
    lua.execute("vehicules = {" + ",".join("{ id = %d, equipe = %d, def = %d, etat = %d, visible = %s }"
                % (i + 10, equipe, d, etat, "true" if visible else "false")
                for i, (equipe, d, etat, visible) in enumerate(unites)) + "}")


def champs(ligne):
    m = ligne.split()
    assert m[0] == "CC2R1" and m[-1] == "FIN", ligne
    return m[1], dict(x.split("=", 1) for x in m[2:-1])


ok = True
def verifier(nom, condition, detail=""):
    global ok
    ok = ok and condition
    print("  %-62s %s %s" % (nom, "OK" if condition else "ECHEC", detail))


UNITES = [
    (1, 0, 0, True),                 # mon porte-avions
    (1, 8, 4, True), (1, 8, 0, True), (1, 12, 4, True), (1, 2, 0, True), (1, 64, 0, True),   # 2 au hangar, 1 drydock
    (2, 0, 0, False), (2, 8, 0, False), (2, 10, 0, True),           # adverse : 2 caches
    (0, 2, 0, False), (0, 2, 0, False), (0, 59, 0, False), (0, 77, 0, True),   # iles
]


def tests():
    print("\nTest du releve des performances (%s)" % LuaRuntime().eval("_VERSION"))
    f = Fichier()
    holo = ecran(f, "holomap_screen")
    inv = ecran(f, "screen_inv_l")
    for lua in (holo, inv):
        mettre_unites(lua, UNITES)
        lua.globals().missiles, lua.globals().obus = 4, 17
    e0 = 1792850000
    retours = []
    for k in range(20 * 23):                      # 23 s a 20 images par seconde, jeu a 60 %
        e = e0 + k // 20
        t = int(k * 0.05 * 30 * 0.6)
        retours.append(image(holo, e, t))
        image(inv, e, t)
    verifier("l'ecran d'origine renvoie toujours ses valeurs", all(r[1] == "retour1" and r[2] == 441 for r in retours))
    verifier("l'ecran d'origine a tourne a chaque image", holo.globals().appels_update == 460)
    lignes = [champs(l) for l in f.lignes]
    verifier("toutes les lignes ont le bon format (CC2R1 ... FIN)", len(lignes) == len(f.lignes) and len(lignes) > 0)
    d = [c for t, c in lignes if t == "D"]
    verifier("lignes D : seulement l'ecran de donnees (holomap)", d and all(c["s"] == "holomap_screen" for c in d),
             str(sorted(set(c["s"] for c in d))))
    verifier("lignes D : toutes les 5 s pile", [int(c["e"]) % 5 for c in d] == [0] * len(d) and len(d) == 5,
             str([int(c["e"]) - e0 for c in d]))
    c = d[-1]
    verifier("lignes D : top du jeu pris des que la seconde change",
             int(c["t"]) == int((int(c["e"]) - e0) * 20 * 0.05 * 30 * 0.6), "%s" % c["t"])
    verifier("mes unites : 1 PA, 1 terrestre, 1 avion, 2 au hangar, 1 autre", c.get("q1") == "1,1,1,0,0,0,1,2,0", c.get("q1"))
    verifier("adverse : 1 PA + 2 avions dont 2 caches", c.get("q2") == "1,0,2,0,0,0,0,0,2", c.get("q2"))
    verifier("iles : 2 terrestres, 1 tourelle, 1 navire, 3 caches", c.get("q0") == "0,2,0,0,1,1,0,0,3", c.get("q0"))
    verifier("missiles, obus, epaves, equipe, nombre d'unites", (c["mis"], c["pro"], c["epa"], c["moi"], c["nv"]) == ("4", "17", "3", "1", "13"))
    s = [c for t, c in lignes if t == "S"]
    verifier("ligne S au debut, seulement pour l'ecran de donnees", len(s) == 1 and s[0]["s"] == "holomap_screen")
    eh = [c for t, c in lignes if t == "E" and c["s"] == "holomap_screen"]
    ei = [c for t, c in lignes if t == "E" and c["s"] == "screen_inv_l"]
    def attendus(nom):        # 1er battement tout de suite, puis aux secondes ou (e - decalage) % 10 == 0
        dec = sum(nom.encode()) % 10
        return [0] + [x for x in range(1, 23) if (x - dec) % 10 == 0]
    verifier("battements toutes les 10 s (holomap)", [int(c["e"]) - e0 for c in eh] == attendus("holomap_screen"),
             str([int(c["e"]) - e0 for c in eh]))
    verifier("battements de l'autre ecran (heure lue 1 fois sur 8)",
             [int(c["e"]) - e0 for c in ei] == attendus("screen_inv_l"), str([int(c["e"]) - e0 for c in ei]))
    verifier("battement : nombre d'appels a update depuis le precedent", int(eh[2]["n"]) == 200, eh[2]["n"])
    verifier("battement : ecran allume, joueur pas dessus", eh[1]["a"] == "1" and eh[1]["f"] == "0")

    # print() d'un mod : 20 par minute, le reste compte
    f.lignes.clear()
    for k in range(25):
        holo.eval("print('erreur du mod', %d)" % k)
    autres = [l for l in f.lignes if not l.startswith("CC2R1")]
    verifier("print() d'un mod : 20 passent sur 25", len(autres) == 20 and autres[0] == "erreur du mod\t0", str(len(autres)))
    for k in range(20 * 11):
        image(holo, e0 + 30 + k // 20, 5000 + k)
    e = [champs(l)[1] for l in f.lignes if l.startswith("CC2R1 E")]
    verifier("print() d'un mod : les 5 jetes sont comptes (x=5)", e and e[0]["x"] == "5", str(e[:1]))
    holo.eval("print('minute suivante')")
    verifier("print() d'un mod : de nouveau permis la minute suivante", f.lignes[-1] == "minute suivante")

    # erreurs
    f.lignes.clear()
    holo.execute("casse.compte = true")
    r = None
    for k in range(20 * 6):
        r = image(holo, e0 + 100 + k // 20, 9000 + k)
    verifier("compte d'unites en erreur : l'ecran marche quand meme", r[1] == "retour1")
    verifier("compte d'unites en erreur : les battements continuent", any(l.startswith("CC2R1 E") for l in f.lignes))
    holo.execute("casse.compte = nil; casse.epoch = true")
    n = len(f.lignes)
    for k in range(20 * 12):
        r = image(holo, e0 + 110 + k // 20, 9200 + k)
    verifier("heure reelle en erreur : l'ecran marche, rien n'est ecrit", r[1] == "retour1" and len(f.lignes) == n)

    # affichage de pilotage
    f.lignes.clear()
    hud = ecran(f, "hud", genre="hud")
    mettre_unites(hud, UNITES)
    for k in range(20 * 6):
        r = image(hud, e0 + 200 + k // 20, 10000 + k, genre="hud", vehicule_pilote=12)
    lignes = [champs(l) for l in f.lignes]
    d = [c for t, c in lignes if t == "D"]
    verifier("pilotage : reconnu (s=hud) et lignes D", d and d[0]["s"] == "hud", str(lignes[:1]))
    verifier("pilotage : type du vehicule pilote (pil=12, helico)", d and d[0].get("pil") == "12")
    verifier("pilotage : l'affichage d'origine renvoie ses valeurs", r[1] == "retour1" and r[2] == 440)

    # menu pause (sans nom d'ecran, 3 parametres)
    f.lignes.clear()
    pause = ecran(f, "", genre="pause")
    for k in range(40):
        image(pause, e0 + 300 + k // 20, 20000)
    lignes = [champs(l) for l in f.lignes]
    verifier("menu pause : nomme « autre », battements seulement",
             lignes and all(c["s"] == "autre" and t == "E" for t, c in lignes), str(lignes[:1]))

    # sans heure reelle : rien n'est enveloppe
    f.lignes.clear()
    sans = ecran(f, "screen_veh_m", sans=("update_get_time_since_epoch",))
    for k in range(40):
        r = image(sans, e0 + k // 20, k)
    verifier("ecran sans heure reelle : rien d'ecrit, ecran intact",
             not f.lignes and r[1] == "retour1" and sans.eval("g_releve_update_origine") is None)

    # horloge et journal toujours la sur les ecrans de controle des vehicules
    veh = ecran(Fichier(), "screen_veh_m")
    textes = []
    veh.globals().update_ui_text = lambda x, y, t, *a: textes.append(t)
    image(veh, e0, 4410)
    verifier("ecran de controle : l'horloge s'affiche toujours", any(str(t).startswith("TEMPS DE JEU") for t in textes), str(textes[:2]))


def simuler(chemin):
    """Une partie de 15 minutes : pont, carte, pilotage d'un avion, combat, pause d'une minute."""
    random.seed(4)
    f = Fichier()
    noms = ["holomap_screen", "screen_veh_m", "screen_veh_l", "screen_veh_r", "screen_nav_m", "screen_inv_l",
            "screen_inv_r", "screen_com_l", "screen_nav_l", "screen_nav_r"]
    ecrans = {n: ecran(f, n) for n in noms}
    hud = None
    e0, tick, fps = 1792850000, 0.0, 20
    iles = [(0, 2, 0, False)] * 44 + [(0, 59, 0, False)] * 9 + [(0, 77, 0, False)] * 8
    for k in range(15 * 60 * fps):
        s = k / fps
        m = s / 60
        pilote = 6.0 <= m < 9.0
        combat = 7.0 <= m < 8.5
        pause = 12.0 <= m < 13.0
        carte = 3.0 <= m < 4.5
        perdues = int(max(0.0, min(m, 8.5) - 7.0) * 6)
        unites = [(1, 0, 0, True), (1, 8, 0 if 2 <= m < 11 else 4, True), (1, 8, 0 if 2.5 <= m < 11 else 4, True),
                  (1, 12, 4, True), (1, 2, 0, True), (1, 2, 4, True), (1, 64, 0, True),
                  (2, 0, 0, False), (2, 8, 0, False), (2, 10, 0, m > 5), (2, 2, 4, False)] + iles[perdues:]
        vitesse = 0.0 if pause else max(0.35, 0.74 - 0.0015 * (len(unites) - 60) - (0.08 if pilote else 0)
                                         - (0.12 if combat else 0) + random.gauss(0, 0.01))
        tick += vitesse * 30 / fps
        e = e0 + int(s)
        if k % fps == 0:
            for n, lua in ecrans.items():
                mettre_unites(lua, unites)
                g = lua.globals()
                g.missiles = int(combat) * random.randint(4, 12)
                g.obus = int(combat) * random.randint(20, 45) + random.randint(0, 2)
                g.focus = (n == "holomap_screen" and carte)
            if pilote and hud is None:
                hud = ecran(f, "hud", genre="hud")
            if hud is not None:
                mettre_unites(hud, unites)
                hud.globals().missiles = ecrans["holomap_screen"].globals().missiles
        actifs = noms[:3] if pilote else noms        # en pilotage, seuls 3 ecrans du pont tournent encore
        for n in actifs:
            image(ecrans[n], e, int(tick))
        if pilote:
            image(hud, e, int(tick), genre="hud", vehicule_pilote=8)
    with open(chemin, "w") as sortie:
        sortie.write("\n".join(f.lignes) + "\n")
    print("\nPartie simulee : %d lignes ecrites dans %s" % (len(f.lignes), chemin))


tests()
if "--fichier" in sys.argv:
    simuler(sys.argv[sys.argv.index("--fichier") + 1])
print("\nRESULTAT : " + ("TOUT EST BON" if ok else "IL Y A DES ECHECS"))
sys.exit(0 if ok else 1)
