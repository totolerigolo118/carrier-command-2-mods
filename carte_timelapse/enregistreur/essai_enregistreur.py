"""Banc de test HORS JEU de l'enregistreur CC2MAP.

Il fait « jouer » le scenario de demonstration (10 minutes de jeu, 30 ticks par seconde) dans un faux
jeu : faux SDK CC2X (cc2x.tick / vehicles / tiles / log) et fausse API des ecrans (missiles, begin_load,
update). L'enregistreur Lua est execute tel quel par lupa. Sortie : le journal qu'il ecrirait.

Usage : python3 -I essai_enregistreur.py scenario_demo.json cc2map_enregistreur.lua sortie.log [--lua51|--lua53|--lua54] [--doublon]
"""
import json
import math
import sys

import lupa

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opts = [a for a in sys.argv[1:] if a.startswith("--")]
scen_path, lua_path, out_path = args
variant = next((o[2:] for o in opts if o in ("--lua51", "--lua52", "--lua53", "--lua54")), "lua53")
doublon = "--doublon" in opts          # deux ecrans qui enregistrent en meme temps (comme en vrai)
mod = __import__("lupa." + variant, fromlist=["LuaRuntime"])

D = json.load(open(scen_path, encoding="utf-8"))
SCN = D["scenario"]
TICK0, SECS = D["tick"], SCN["seconds"]
TICKS = SECS * 30
CP = {int(k): v for k, v in SCN["carriers"].items()}


def lerp(a, b, k):
    return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k]


def pos_at(arr, f):
    x = max(0.0, min(1.0, f)) * (len(arr) - 1)
    i = min(int(x), len(arr) - 2)
    return lerp(arr[i], arr[i + 1], x - i)


def flight_at(fl, t):
    path = fl["path"]
    if "_cum" not in fl:
        fl["_cum"] = [0.0]
        for k in range(1, len(path)):
            fl["_cum"].append(fl["_cum"][-1] + math.hypot(path[k][0] - path[k - 1][0], path[k][1] - path[k - 1][1]))
    cum = fl["_cum"]
    d = max(0.0, min(1.0, t)) * cum[-1]
    i = 1
    while i < len(path) - 1 and cum[i] < d:
        i += 1
    seg = (cum[i] - cum[i - 1]) or 1
    p = lerp(path[i - 1], path[i], (d - cum[i - 1]) / seg)
    return p[0], p[1], math.atan2(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])


def vehicles_at(tick):
    f = max(0.0, min(1.0, (tick - TICK0) / TICKS))
    out = []
    for u in D["units"]:
        if u["def"] == 0:
            p = pos_at(CP[u["team"]], f)
            a, b = pos_at(CP[u["team"]], max(0, f - 0.012)), pos_at(CP[u["team"]], min(1, f + 0.012))
            out.append(dict(id=u["id"], definition=0, team=u["team"], x=p[0], y=0.0, z=p[1], yaw=math.atan2(b[0] - a[0], b[1] - a[1]), is_air=False))
        else:
            out.append(dict(id=u["id"], definition=u["def"], team=u["team"], x=u["x"], y=0.0, z=u["z"], yaw=u["yaw"], is_air=u["def"] in (8, 10, 12, 14)))
    for i, fl in enumerate(D["flights"]):
        x, z, yaw = flight_at(fl, f)
        out.append(dict(id=9000 + i, definition=fl["def"], team=fl["team"], x=x, y=300.0, z=z, yaw=yaw, is_air=True))
    return out


def tiles_at(tick):
    return [dict(id=i["id"], team=i["team"], x=i["x"], y=-1.0, z=i["z"], island=True) for i in D["islands"]]


def missiles_at(tick):
    f = (tick - TICK0) / TICKS
    out = []
    for n, m in enumerate(SCN["missiles"]):
        if m["f0"] <= f <= m["f1"]:
            k = (f - m["f0"]) / (m["f1"] - m["f0"])
            p = lerp(m["a"], m["b"], k)
            out.append(dict(id=500 + n, definition=49, team=m["team"], x=p[0], z=p[1]))
    return out


LOG = []


def make_runtime(screen_name):
    lua = mod.LuaRuntime(unpack_returned_tuples=True)
    state = {"tick": TICK0}
    g = lua.globals()
    mk = lambda d: lua.table_from(d)
    g.PY_LOG = lambda s: LOG.append(s)
    g.PY_TICK = lambda: state["tick"]
    g.PY_VEH = lambda: lua.table(*[mk(v) for v in vehicles_at(state["tick"])])
    g.PY_TIL = lambda: lua.table(*[mk(t) for t in tiles_at(state["tick"])])
    g.PY_MIS = lambda: lua.table(*[mk(m) for m in missiles_at(state["tick"])])
    g.SCREEN = screen_name
    lua.execute("""
        cc2x = { api = 4, version = "0.5.0", game_build = "1.5.18-win32",
                 log = function(s) PY_LOG(s) end, tick = function() return PY_TICK() end,
                 vehicles = function() return PY_VEH() end, tiles = function() return PY_TIL() end }
        local cur = {}
        local function mkm(p) return {
            get = function(self) return true end,
            get_position_xz = function(self) return { x = function(s) return p.x end, y = function(s) return p.z end } end,
            get_definition_index = function(self) return p.definition end,
            get_team = function(self) return p.team end,
            get_id = function(self) return p.id end } end
        function update_get_missile_count() cur = PY_MIS(); return #cur end
        function update_get_missile_by_index(i) return mkm(cur[i + 1]) end
        function begin_get_screen_name() return SCREEN end
        UPDATES = 0
        function update() UPDATES = UPDATES + 1 end
        function begin_load() end
    """)
    lua.execute(open(lua_path, encoding="utf-8").read())
    return lua, state


runtimes = [make_runtime("holomap_screen")]
if doublon:
    runtimes.append(make_runtime("screen_veh_m"))
for lua, st in runtimes:
    lua.globals().begin_load()           # le jeu appelle begin_load -> notre crochet enveloppe update()
for tick in range(TICK0, TICK0 + TICKS + 1):
    for lua, st in runtimes:
        st["tick"] = tick
        lua.globals().update()

# pas de lignes si l'enregistreur n'est pas accroche : c'est un echec du test
prefix = "[2026-10-27 12:00:00.000] [lua] "
with open(out_path, "w", encoding="utf-8") as fh:
    fh.write("[2026-10-27 12:00:00.000] [cc2x] CC2X 0.5.0 (build 1.5.18-win32) - ligne de demarrage factice\n")
    for s in LOG:
        fh.write(prefix + s + "\n")
kinds = {}
for s in LOG:
    kinds[s.split("|")[1]] = kinds.get(s.split("|")[1], 0) + 1
size = sum(len(prefix + s) + 1 for s in LOG)
print("Lua :", variant, "| ecrans enregistreurs :", len(runtimes))
print("lignes ecrites :", len(LOG), "| par type :", kinds, "| taille :", round(size / 1024), "Ko pour", SECS // 60, "minutes de jeu")
print("ligne la plus longue :", max(len(s) for s in LOG), "caracteres")
print("exemples :")
for k in ("H", "V", "T", "M"):
    ex = next((s for s in LOG if s.split("|")[1] == k and s.split("|")[3] != "1/1" ), None)
    print("  ", (ex or "(aucune)")[:150])
