#!/usr/bin/env python3
"""Banc d'essai Lua HORS JEU : charge un script du mod dans un vrai interpreteur Lua 5.1 (lua51.dll d'OBS Studio,
logiciel signe deja installe, appele depuis Python par ctypes ; aucun reseau, aucun fichier ecrit), avec de FAUX appels du jeu.

  python -I lua_sonde.py syntaxe  fichier.lua [...]      -> compile seulement : vraie verification de syntaxe
  python -I lua_sonde.py auto     fichier.lua            -> simule le menu, la couche d'affichage et une sortie/retour de 4 avions

Limites : Lua 5.1 (le jeu est plus recent : table.pack / table.unpack sont ajoutes en raccord) ; les appels du jeu sont des
doublures ecrites ici, donc ce banc prouve la SYNTAXE et la LOGIQUE d'accrochage, pas le comportement reel du jeu.
"""
import ctypes
import os
import sys

DLL = r'C:\Program Files\obs-studio\bin\64bit\lua51.dll'
GLOBALS = -10002          # LUA_GLOBALSINDEX (Lua 5.1)


class VM:
    def __init__(self):
        L = ctypes.CDLL(DLL)
        L.luaL_newstate.restype = ctypes.c_void_p
        for n, a in (('luaL_openlibs', [ctypes.c_void_p]), ('lua_close', [ctypes.c_void_p]),
                     ('lua_settop', [ctypes.c_void_p, ctypes.c_int]),
                     ('luaL_loadbuffer', [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p]),
                     ('lua_pcall', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int])):
            getattr(L, n).argtypes = a
        L.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
        L.lua_tolstring.restype = ctypes.c_char_p
        self.L = L
        self.s = L.luaL_newstate()
        L.luaL_openlibs(self.s)

    def run(self, code, nom='chunk'):
        """Execute du Lua ; renvoie (ok, texte) ou texte = valeur renvoyee (chaine) ou message d'erreur."""
        L, s = self.L, self.s
        b = code.encode('utf-8')
        r = L.luaL_loadbuffer(s, b, len(b), ('=' + nom).encode())
        if r == 0:
            r = L.lua_pcall(s, 0, 1, 0)
        n = ctypes.c_size_t()
        p = L.lua_tolstring(s, -1, ctypes.byref(n))
        txt = p.decode('utf-8', 'replace') if p else ''
        L.lua_settop(s, 0)
        return r == 0, txt

    def close(self):
        self.L.lua_close(self.s)


PRELUDE = r'''
table.pack = table.pack or function(...) return { n = select('#', ...), ... } end
table.unpack = table.unpack or unpack
journal = {}
function note(...) local t = {} for i = 1, select('#', ...) do t[#t + 1] = tostring((select(i, ...))) end journal[#journal + 1] = table.concat(t, " ") end
print = note
function color8(r, g, b, a) return { r, g, b, a } end
calls = { text = 0, rect = 0, red = 0, events = {} }
function update_ui_text(x, y, s, w, a, c, d) calls.text = calls.text + 1; calls.last_text = s end
function update_ui_rectangle(x, y, w, h, c) calls.rect = calls.rect + 1; if c and c[1] == 200 and c[2] == 0 then calls.red = calls.red + 1 end end
function update_ui_get_text_size(s, w, f) return #s * 5, 8 end
function update_ui_event(e, a) calls.events[#calls.events + 1] = e .. (a and (":" .. tostring(a)) or "") end
function update_set_is_visible(v) calls.visible = v end
function update_get_save_slots() return { { slot_index = 3 }, { slot_index = 18 }, { slot_index = 19 } } end
function update_get_logic_tick() return TICK or 0 end
function update_get_time_since_epoch() return NOW or 0 end
function update_get_join_password() return JP or "" end
function update_set_join_password(v) JP = v end
function update_get_screen_team_id() return 1 end
function begin_get_screen_name() return SCREEN or "?" end
e_game_object_type = { chassis_carrier = 0, chassis_air_wing_light = 8, chassis_air_wing_heavy = 10 }
-- comme library_util.lua du jeu : begin_load existe deja quand les library_custom sont chargees
function begin_load() end
'''


def charge_script(chemin):
    with open(chemin, encoding='utf-8') as f:
        return f.read()


def cmd_syntaxe(fichiers):
    ok_tout = True
    for f in fichiers:
        vm = VM()
        try:
            L, s = vm.L, vm.s
            b = charge_script(f).encode('utf-8')
            r = L.luaL_loadbuffer(s, b, len(b), ('=' + os.path.basename(f)).encode())
            n = ctypes.c_size_t()
            p = L.lua_tolstring(s, -1, ctypes.byref(n))
            msg = p.decode('utf-8', 'replace') if (p and r != 0) else ''
            print('%-26s %s' % (os.path.basename(f), 'SYNTAXE OK' if r == 0 else 'ERREUR DE SYNTAXE : ' + msg))
            ok_tout = ok_tout and r == 0
        finally:
            vm.close()
    return 0 if ok_tout else 1


def cmd_auto(fichier):
    src = charge_script(fichier)
    bad = 0

    def verif(cond, msg):
        nonlocal bad
        print(('  OK  ' if cond else '  ECHEC ') + msg)
        if not cond:
            bad += 1

    # ---- 1. etat "menu" : screen_menu_main.lua definit g_is_menu_active, begin() appelle begin_load()
    vm = VM()
    ok, t = vm.run(PRELUDE, 'prelude')
    verif(ok, 'prelude : %s' % t)
    ok, t = vm.run(src, 'library_custom_5')
    verif(ok, 'chargement du script (menu) : %s' % (t or 'sans erreur'))
    ok, t = vm.run('''
        SCREEN = "screen_front"
        g_is_menu_active = true
        function update(w, h, ticks) calls.updates = (calls.updates or 0) + 1 end
        begin_load()
        for i = 1, 6000 do NOW = 1000 + i * 0.01; update(256, 256, 0) end      -- 60 s de temps reel
        return table.concat(calls.events, ",") .. " | rouge=" .. calls.red .. " | updates=" .. calls.updates .. " | menu=" .. tostring(g_ca.menu)
    ''', 'menu')
    verif(ok, 'simulation du menu : %s' % t)
    verif(t.startswith('load_game:18 |') or t.split(' |')[0] == 'load_game:18', 'le menu demande load_game:18 UNE SEULE fois (%s)' % t.split(' |')[0])
    verif('quit_game' not in t, 'le menu ne ferme pas le jeu (sonde de calibrage coupee)')
    vm.close()
    # la sauvegarde voulue est fixee par la ligne que l'orchestrateur place en tete du fichier
    vm = VM()
    vm.run(PRELUDE, 'prelude')
    vm.run('g_ca_slot_voulu = 19\n' + src, 'library_custom_5')
    vm.run('SCREEN = "x"; g_is_menu_active = true; function update(w, h, t) end; begin_load(); for i = 1, 6000 do NOW = 1000 + i * 0.01; update(256, 256, 0) end', 'menu19')
    ok, t = vm.run('return table.concat(calls.events, ",")', 'evenements')
    verif(t == 'load_game:19', 'avec g_ca_slot_voulu = 19 le menu demande load_game:19 une seule fois (%s)' % t)
    vm.close()

    # ---- 1a. SIX ecrans de menu (six contextes Lua separes) executent le meme script : un seul doit demander le chargement.
    #          Le verrou est le mot de passe de connexion du jeu, partage entre contextes : on l'emule en le recopiant d'un contexte a l'autre.
    vms = []
    for _ in range(6):
        v = VM()
        v.run(PRELUDE, 'prelude')
        v.run(src, 'library_custom_5')
        v.run('SCREEN = "screen_pilot"; g_is_menu_active = true; function update(w, h, t) end; begin_load()', 'menu')
        vms.append(v)
    partage = ''
    total = []
    for i in range(1, 6001):
        for v in vms:
            ok, r = v.run('JP = "%s"; NOW = %f; update(256, 256, 0); return JP .. "|" .. table.concat(calls.events, ",")' % (partage, 1000 + i * 0.01), 'tour')
            partage, ev = r.split('|', 1)
            if ev:
                total.append(ev)
    # chaque contexte garde son propre journal d'evenements : on compte les contextes qui ont demande un chargement
    demandes = [v.run('return table.concat(calls.events, ",")', 'ev')[1] for v in vms]
    verif(sum(1 for e in demandes if e == 'load_game:18') == 1 and sum(1 for e in demandes if e) == 1,
          'six ecrans de menu : UN SEUL contexte demande le chargement (%s)' % demandes)
    verif(partage == '__cc2_auto_verrou__', 'le verrou commun est pose (%r)' % partage)
    for v in vms:
        v.close()

    # ---- 1b. mode "menu_seul" : le menu charge toujours, mais rien n'est accroche ailleurs (ecran de bord, couche d'affichage)
    vm = VM()
    vm.run(PRELUDE, 'prelude')
    vm.run('g_ca_mode = "menu_seul"\n' + src, 'library_custom_5')
    ok, t = vm.run('''
        SCREEN = "x"; g_is_menu_active = true; function update(w, h, t) end; begin_load()
        for i = 1, 6000 do NOW = 1000 + i * 0.01; update(256, 256, 0) end
        return table.concat(calls.events, ",")
    ''', 'menu_seul')
    verif(t == 'load_game:18', 'menu_seul : le menu charge une seule fois (%s)' % t)
    vm.close()
    vm = VM()
    vm.run(PRELUDE, 'prelude')
    vm.run('g_ca_mode = "menu_seul"\n' + src, 'library_custom_5')
    ok, t = vm.run('''
        function update(w, h, t) calls.base = (calls.base or 0) + 1 end     -- un ecran de bord ordinaire (pas le menu)
        begin_load()
        for i = 1, 50 do update(256, 256, 0) end
        return "base=" .. calls.base .. " texte=" .. calls.text .. " rect=" .. calls.rect .. " events=" .. #calls.events
    ''', 'menu_seul_bord')
    verif(t == 'base=50 texte=0 rect=0 events=0', 'menu_seul : un ecran de bord n\'est ni accroche ni dessine (%s)' % t)
    vm.close()

    # ---- 2. ecran d'indications (interactions.lua) : il definit g_interactions et appelle begin_load() ; c'est la que le panneau est dessine
    vm = VM()
    vm.run(PRELUDE, 'prelude')
    ok, t = vm.run(src, 'library_custom_5')
    verif(ok, 'chargement du script (ecran d\'indications) : %s' % (t or 'sans erreur'))
    vm.close()
    vm = VM()
    vm.run(PRELUDE, 'prelude')
    ok, t = vm.run('g_ca_hud = true\n' + src, 'library_custom_5')
    ok, t = vm.run('''
        g_interactions = {}
        function update(w, h, dt) calls.base = (calls.base or 0) + 1 end
        begin_load()
        for i = 1, 10 do update(1920, 1080, 16) end
        return "base=" .. tostring(calls.base) .. " texte=" .. calls.text .. " rect=" .. calls.rect .. " dernier=" .. tostring(calls.last_text)
    ''', 'hud')
    verif(ok, 'simulation de l\'ecran d\'indications : %s' % t)
    verif('base=10' in t, 'l\'update d\'origine est toujours appelee')
    verif('texte=0' not in t and 'rect=0' not in t, 'le panneau est dessine par-dessus')
    vm.close()
    # couche overlay.lua : bibliotheques chargees AVANT le script ; begin_load n'y est jamais appele ; la surveillance enveloppe "update"
    vm = VM()
    vm.run(PRELUDE, 'prelude')
    ok, t = vm.run(src, 'library_custom_5')
    verif(ok, 'chargement du script (overlay) : %s' % (t or 'sans erreur'))
    ok, t = vm.run('''
        g_is_loading = false
        g_loading_text = "chargement"
        function update(w, h, tf, dt) calls.base = (calls.base or 0) + 1 end
        for i = 1, 10 do update(1920, 1080, 0, 16) end
        local avant = tostring(calls.visible)                              -- menu : aucun chargement vu, visibilite non touchee
        g_is_loading = true
        for i = 1, 5 do update(1920, 1080, 0, 16) end                      -- un chargement
        local pendant = tostring(calls.visible)
        g_is_loading = false
        for i = 1, 250 do update(1920, 1080, 0, 16) end                    -- 250 images apres : pas encore
        local tot = tostring(calls.visible)
        for i = 1, 100 do update(1920, 1080, 0, 16) end                    -- 350 images apres : visible
        return "base=" .. tostring(calls.base) .. " texte=" .. calls.text .. " rect=" .. calls.rect .. " avant=" .. avant .. " pendant=" .. pendant .. " tot=" .. tot .. " apres=" .. tostring(calls.visible)
    ''', 'overlay')
    verif(ok, 'simulation de la couche overlay : %s' % t)
    verif('texte=0' not in t and 'rect=0' not in t and 'avant=nil' in t and 'pendant=nil' in t and 'tot=nil' in t and 'apres=true' in t,
          'overlay : panneau dessine, visibilite forcee seulement 300 images APRES la fin d\'un chargement (%s)' % t)
    vm.close()

    # ---- 3. scenario complet : porte-avions + 4 avions en baie, sortie puis retour (doublures de vehicules)
    vm = VM()
    vm.run(PRELUDE, 'prelude')
    vm.run(src, 'library_custom_5')
    ok, t = vm.run(r'''
        local acft = {}
        for i = 1, 4 do acft[100 + i] = { id = 100 + i, def = (i % 2 == 0) and 10 or 8, st = 4, team = 1, wp = 0 } end
        local carrier = { id = 1, def = 0, team = 1, x = 10, z = 20 }
        local function wrap_v(o)
            local v = {}
            function v:get() return o ~= nil end
            function v:get_id() return o.id end
            function v:get_definition_index() return o.def end
            function v:get_team() return o.team end
            function v:get_dock_state() return o.st end
            function v:get_attached_vehicle_id(b) local id = 100 + b + 1 if acft[id] then return id end return -1 end
            function v:get_position_xz() return { x = function() return o.x end, y = function() return o.z end } end
            function v:clear_waypoints() end
            function v:clear_attack_target() end
            function v:add_waypoint(x, z) o.wp = o.wp + 1; o.dest = z; return o.wp end
            function v:set_target_vehicle(w, id) o.back = true end
            return v
        end
        function update_get_map_vehicle_count() return 5 end
        function update_get_map_vehicle_by_index(i) if i == 0 then return wrap_v(carrier) end return wrap_v(acft[100 + i]) end
        function update_get_map_vehicle_by_id(id) if id == 1 then return wrap_v(carrier) end return wrap_v(acft[id]) end
        SCREEN = "screen_veh_m"                       -- ecran de bord central : il a l'API du monde, c'est la que tourne la logique
        function update_get_screen_vehicle() return wrap_v(carrier) end
        function update(w, h, tf) end
        begin_load()
        local dt = 33
        local phase = 0
        for tick = 1, 40000 do
            TICK = tick
            NOW = 5000 + tick * 0.033
            update(1920, 1080, 0, dt)
            if tick == 400 then for _, a in pairs(acft) do end end
            -- decollage : 3 s de jeu apres l'ordre, passage 2 -> 3 -> 0
            for _, a in pairs(acft) do
                if a.dest and a.st == 4 and not a.back then a.t0 = a.t0 or tick; if tick - a.t0 > 60 then a.st = 3 end end
                if a.st == 3 and tick - (a.t0 or 0) > 120 + (a.id - 100) * 30 then a.st = 0 end
                if a.back and a.st == 0 then a.t1 = a.t1 or tick; if tick - a.t1 > 300 + (a.id - 100) * 200 then a.st = 5 end end
                if a.st == 5 and tick - a.t1 > 400 + (a.id - 100) * 200 then a.st = 1 end
                if a.st == 1 and tick - a.t1 > 500 + (a.id - 100) * 200 then a.st = 6 end
                if a.st == 6 and tick - a.t1 > 600 + (a.id - 100) * 200 then a.st = 4 end
            end
        end
        return "etat=" .. g_ca.etat .. " rec=" .. #g_ca.rec .. " msg=" .. tostring(g_ca.message) .. " info=" .. g_ca.info .. " err=" .. tostring(g_ca.err)
            .. " dernier=" .. tostring(calls.last_text) .. " events=" .. table.concat(calls.events, ",")
    ''', 'scenario')
    print('  scenario :', t)
    verif(ok, 'simulation d\'un essai complet sans erreur Lua')
    verif('etat=fin' in t and 'rec=4' in t, 'le script mene sortie + retour de 4 avions jusqu\'au bilan')
    verif('err=nil' in t, 'aucune erreur interne (g_ca.err)')
    verif('chat:CA BILAN fin' in t and 'quit_game' in t, 'le bilan est envoye dans le chat du jeu, puis le jeu est quitte')
    vm.close()
    print('%s' % ('TOUT EST OK' if bad == 0 else '%d ECHEC(S)' % bad))
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'syntaxe':
        sys.exit(cmd_syntaxe(sys.argv[2:]))
    if len(sys.argv) == 3 and sys.argv[1] == 'auto':
        sys.exit(cmd_auto(sys.argv[2]))
    sys.exit(__doc__)
