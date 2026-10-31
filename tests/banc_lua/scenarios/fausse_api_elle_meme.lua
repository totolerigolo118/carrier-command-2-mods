-- Auto-tests de la FAUSSE API : si elle derive de ce qu'elle pretend imiter, tout le reste du banc perd son sens.
-- Ici : l'horloge (30 ticks par seconde), les profils d'API, la liaison au begin_load, la verification des arguments,
-- les contrats du plugin cc2x.modes (LUS dans cc2x_modes.c) et de cc2x.log (900 caracteres).
local cadre = ...
local Jeu = require("fausse_api.jeu")
local Contexte = require("fausse_api.contexte")
local Cc2x = require("fausse_api.cc2x")
local Obj = require("fausse_api.objets")
local UI = require("fausse_api.ui")
local A = require("fausse_api.aides")

cadre.groupe("fausse API : auto-tests", function()

	cadre.scenario("horloge : 30 ticks par seconde de jeu, vitesse de simulation reglable, temps reel en secondes flottantes", function(t)
		local jeu = Jeu.nouveau()
		local r0 = jeu.reel
		jeu:jouer(10, { fps = 30 })
		t:egal(jeu.tick, 300, "10 s a x1 = 300 ticks")
		t:verifier(math.abs(jeu.reel - r0 - 10) < 1e-3, "10 s reelles ecoulees (au cumul d'arrondi pres)", jeu.reel - r0)
		jeu:jouer(10, { fps = 20, vitesse = 2 })
		t:egal(jeu.tick, 300 + 600, "10 s a x2 = 600 ticks de plus")
		jeu:jouer(10, { fps = 7, vitesse = 0.5 })
		t:egal(jeu.tick, 900 + 150, "10 s a x0,5 = 150 ticks de plus (images irregulieres)")
		t:verifier(math.type(jeu.tick) == "integer", "le tick est un entier Lua 5.3")
		t:verifier(jeu.reel > 1.7e9, "l'horloge reelle a l'ordre de grandeur d'une date 'depuis 1970'")
		local vu = {}
		jeu:a_tick(jeu.tick + 3, function(j) vu[#vu + 1] = j.tick end)
		jeu:avancer_ticks(5)
		t:egal(vu, { 1050 + 3 }, "un rappel planifie part exactement au bon tick")
	end)

	cadre.scenario("l'API C n'est liee qu'au begin_load ; l'overlay la possede des le chargement mais sans l'API du monde", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord" })
		t:verifier(ctx.env.update_get_logic_tick == nil and ctx.env.update_ui_text == nil, "avant begin_load : update_* absents")
		t:verifier(type(ctx.env.color8) == "function" and ctx.env.e_game_object_type.chassis_carrier == 0, "color8 et les enumerations existent des le chargement")
		ctx.env.begin_load()
		t:verifier(type(ctx.env.update_get_logic_tick) == "function" and type(ctx.env.update_ui_text) == "function", "apres begin_load : lies")
		local ov = Contexte.nouveau(jeu, { nom = "overlay", profil = "overlay" })
		t:verifier(type(ov.env.update_set_is_visible) == "function" and type(ov.env.update_ui_text) == "function", "overlay : liee des le chargement")
		t:verifier(ov.env.update_get_logic_tick == nil and ov.env.update_get_map_vehicle_count == nil and ov.env.update_get_screen_team_id == nil, "overlay : pas d'API du monde (mesure du 27/10)")
		t:verifier(ov.env.begin_get_screen_name == nil, "overlay : pas de begin_get_screen_name")
		local menu = Contexte.nouveau(jeu, { nom = "screen_front", profil = "menu" })
		menu.env.begin_load()
		t:verifier(type(menu.env.update_ui_event) == "function" and type(menu.env.update_get_save_slots) == "function" and menu.env.update_get_map_vehicle_count == nil, "menu : API du frontend, pas celle du monde")
	end)

	cadre.scenario("environnement : seulement base, math, string, table, utf8, debug (pas de io, os, package, coroutine, dofile, load)", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord" })
		for _, nom in ipairs({ "io", "os", "package", "require", "coroutine", "dofile", "loadfile", "load", "loadstring" }) do
			t:verifier(ctx.env[nom] == nil, nom .. " absent")
		end
		for _, nom in ipairs({ "string", "table", "math", "utf8", "debug", "pcall", "table" }) do
			t:verifier(ctx.env[nom] ~= nil, nom .. " present")
		end
		t:verifier(ctx.env._G == ctx.env and ctx.env._VERSION == "Lua 5.3", "_G est l'environnement du contexte ; Lua 5.3")
		-- deux contextes ne partagent pas leurs globales
		local autre = Contexte.nouveau(jeu, { nom = "screen_veh_l", profil = "bord" })
		ctx:charger_texte("g_test = 1", "x")
		t:verifier(autre.env.g_test == nil, "les globales d'un contexte ne fuient pas dans un autre")
		-- print est capture
		ctx:charger_texte("print('a', 1, nil)", "x")
		t:egal(ctx.prints, { "a\t1\tnil" }, "print capture, rien sur la sortie standard")
	end)

	cadre.scenario("arguments verifies comme le ferait une liaison C : texte nil, couleur absente, nombres faux", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1 })
		ctx.env.begin_load()
		local e = ctx.env
		local c = e.color8(1, 2, 3, 4)
		t:verifier(not pcall(e.update_ui_text, 0, 0, nil, 10, 0, c, 0), "update_ui_text(texte nil) leve une erreur")
		t:verifier(not pcall(e.update_ui_text, 0, 0, "a", 10, 0, nil, 0), "update_ui_text(couleur nil) leve une erreur")
		t:verifier(not pcall(e.update_ui_text, "0", 0, "a", 10, 0, c, 0), "update_ui_text(x texte) leve une erreur")
		t:verifier(not pcall(e.update_ui_rectangle, 0, 0, 10, "h", c), "update_ui_rectangle(h texte) leve une erreur")
		t:verifier(not pcall(e.update_get_map_vehicle_by_id, "9"), "update_get_map_vehicle_by_id('9') leve une erreur")
		t:verifier(not pcall(e.color8, 1, 2, 3), "color8 a quatre nombres")
		e.color8(300, 0, 0, 0)
		t:egal(#jeu.avertissements, 1, "color8 hors 0..255 : avertissement")
		e.update_ui_event("evenement_inconnu")
		t:egal(#jeu.avertissements, 2, "update_ui_event inconnu : avertissement")
		t:verifier(select(2, pcall(e.update_ui_text, 0, 0, nil, 10, 0, c, 0)):find("bad argument #3", 1, true), "message de type 'bad argument #3'")
	end)

	cadre.scenario("vehicules : poignee toujours renvoyee, get() faux apres disparition, lecture sur vehicule disparu = erreur", function(t)
		local jeu = Jeu.nouveau()
		jeu:ajouter({ id = 5, def = Jeu.DEFS.chassis_air_wing_light, dock_state = Jeu.ETAT.HANGAR })
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord" })
		ctx.env.begin_load()
		local v = ctx.env.update_get_map_vehicle_by_id(5)
		t:verifier(v:get() and v:get_dock_state() == 4 and v:get_definition_index() == 8, "lecture d'un vehicule existant")
		local inconnu = ctx.env.update_get_map_vehicle_by_id(999)
		t:verifier(inconnu ~= nil and inconnu:get() == false, "id inconnu : poignee dont get() est faux")
		t:verifier(not pcall(inconnu.get_dock_state, inconnu), "lire un vehicule inexistant leve une erreur (SUPPOSE, force a tester get())")
		jeu:retirer(5)
		t:verifier(v:get() == false, "apres destruction : get() faux")
		t:verifier(ctx.env.update_get_map_vehicle_by_index(0):get() == false and ctx.env.update_get_map_vehicle_count() == 0, "la carte est vide")
		t:verifier(v.get_linear_speed == nil and v.get_throttle_factor == nil, "get_linear_speed / get_throttle_factor absents par defaut (cas majoritaire du journal du 28/10)")
		jeu.avec_vitesse_gaz = true
		t:verifier(type(v.get_linear_speed) == "function", "... sauf si le scenario les active")
	end)

	cadre.scenario("ordres de vol : waypoint renvoye, cible attachee, refus injectable", function(t)
		local jeu = Jeu.nouveau()
		jeu:ajouter({ id = 5, def = Jeu.DEFS.chassis_air_wing_light })
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord" })
		ctx.env.begin_load()
		local v = ctx.env.update_get_map_vehicle_by_id(5)
		local wp = v:add_waypoint(1.5, 2.5)
		t:verifier(math.type(wp) == "integer" and v:get_waypoint_count() == 1, "add_waypoint renvoie un numero entier et ajoute un waypoint")
		v:set_target_vehicle(wp, 1)
		t:egal(jeu.vehicules[5].waypoints[1].cible, 1, "set_target_vehicle attache la cible")
		t:verifier(not pcall(v.set_target_vehicle, v, 9999, 1), "waypoint inconnu : erreur")
		v:clear_waypoints()
		t:egal(v:get_waypoint_count(), 0, "clear_waypoints vide la liste")
		jeu.refuser_ordres = true
		t:verifier(not pcall(v.add_waypoint, v, 1, 2), "refuser_ordres : add_waypoint leve une erreur")
		t:egal(#jeu.journal_ordres, 3, "le journal ne garde que les ordres acceptes (add, set_target, clear) : l'ordre refuse n'y est pas")
	end)

	cadre.scenario("update_ui_event : memorise l'evenement et l'appelant ; aucun effet de jeu simule", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_front", profil = "menu" })
		ctx.env.begin_load()
		ctx.env.update_ui_event("load_game", 18)
		ctx.env.update_ui_event("quit_game")
		t:egal(#jeu.evenements, 2, "2 evenements")
		t:egal({ jeu.evenements[1].ctx, jeu.evenements[1].nom, jeu.evenements[1].args[1] }, { "screen_front", "load_game", 18 }, "contexte, nom et argument")
		t:egal(#jeu.avertissements, 0, "noms connus : pas d'avertissement")
	end)

	cadre.scenario("cc2x.log : une ligne, 900 caracteres au plus (SDK), arguments joints", function(t)
		local jeu = Jeu.nouveau()
		local sdk = Cc2x.nouveau(jeu, { niveau = "0.5" })
		sdk.table.log("a", 1, true)
		t:egal(jeu.journal_cc2x, { "a 1 true" }, "arguments convertis et joints par une espace")
		sdk.table.log(string.rep("x", 1000))
		t:egal(#jeu.journal_cc2x[2], 900, "tronque a 900")
		t:egal(#jeu.avertissements, 1, "avec un avertissement (un script qui depasse perd de l'information)")
	end)

	cadre.scenario("cc2x : niveau 0.4 conforme a LUA_API.md ; niveau 0.5 ajoute tick() et les champs supposes", function(t)
		local jeu = Jeu.nouveau()
		jeu:ajouter({ id = 9, def = 8, x = 1.0, y = 2.0, z = 3.0, fuel = 0.5 })
		local v4 = Cc2x.nouveau(jeu, { niveau = "0.4" }).table
		t:egal({ v4.version, v4.api, v4.game_build }, { "0.4.0", 3, "1.5.18-win32" }, "version, api, build")
		t:verifier(v4.tick == nil, "pas de cc2x.tick() en 0.4")
		local veh = v4.vehicles()[1]
		local cles = {}
		for k in pairs(veh) do cles[#cles + 1] = k end
		table.sort(cles)
		t:egal(cles, { "attached_to", "definition", "dock_state", "fuel", "hp", "id", "team", "x", "y", "z" }, "champs d'un vehicule 0.4 = ceux de LUA_API.md")
		t:egal(v4.vehicle(9).fuel, 400.0, "fuel absolu (0,5 x 800 pour un Albatros, SUPPOSE)")
		t:verifier(v4.vehicle(404) == nil and v4.tile(1) == nil, "vehicle/tile inconnus : nil (jamais d'erreur)")
		local v5 = Cc2x.nouveau(jeu, { niveau = "0.5" }).table
		t:egal({ v5.api, type(v5.tick), v5.vehicle(9).is_wing, v5.vehicle(9).flight_state }, { 4, "function", true, 2 }, "0.5 : api 4, tick(), is_wing, flight_state")
	end)

	cadre.scenario("cc2x.modes : contrat du plugin v3 (set/get/hold/status, bornes, 64 avions, 90 ticks)", function(t)
		local jeu = Jeu.nouveau()
		local sdk = Cc2x.nouveau(jeu, { niveau = "0.5", plugin_modes = true })
		local m = sdk.table.modes
		t:verifier(sdk.table.has("modes") == true and sdk.table.has("autre") == false, "cc2x.has('modes')")
		t:egal(m.set(9, 1), true, "set(9, 1)")
		t:egal({ m.get(9) }, { 1, 0, false }, "get(9) -> mode, actif, tenu")
		t:egal(m.set(9.9, 2), true, "id flottant : tronque (l_tointeger du SDK)")
		t:egal(m.get(9), 2, "... donc c'est l'avion 9")
		for _, mauvais in ipairs({ 0, -1, 0x80000000, "9", true, 0 / 0 }) do
			t:egal(m.set(mauvais, 1), false, "set(" .. tostring(mauvais) .. ", 1) refuse")
		end
		for _, mauvais in ipairs({ 3, -1, "1", true, nil }) do
			t:egal(m.set(10, mauvais), false, "set(10, " .. tostring(mauvais) .. ") refuse")
		end
		t:egal(m.get(0), nil, "get(0) -> nil")
		t:egal(m.hold(0), false, "hold(0) -> false")
		t:egal(m.hold(9), true, "hold(9) -> true")
		t:egal(select(3, m.get(9)), true, "tenu")
		jeu:avancer_ticks(90)
		t:egal(select(3, m.get(9)), false, "relache apres 90 ticks (3 s)")
		for i = 100, 100 + 62 do m.set(i, 1) end
		t:egal(m.set(5000, 1), false, "65e avion : table pleine, refuse")
		t:egal(m.set(100, 2), true, "mais un avion deja connu peut changer de mode")
		local s = m.status()
		t:egal({ s.version, s.enabled, s.eco_cap_light, s.eco_cap_heavy, s.flank_floor_light, s.flank_floor_heavy }, { 3, false, 0.65, 0.35, 1.0, 1.0 }, "status() : valeurs par defaut de modes.ini.example")
	end)

	cadre.scenario("interface g_ui : piles, fenetres, survol, fautes injectees", function(t)
		local jeu = Jeu.nouveau()
		local ui = UI.nouvelle({ jeu = jeu })
		t:verifier(not pcall(ui.end_window, ui), "end_window sans fenetre : erreur")
		local f = ui:begin_window("T", 10, 20, 70, 50, nil, true, 2)
		t:egal({ #ui.window_stack, #ui.region_stack, ui:get_region(), f.cx, f.cy }, { 1, 1, 66, 12, 32 }, "begin_window empile fenetre et region")
		ui.pointeur = { x = 13, y = 33 }
		t:verifier(ui:hoverable(12, 32, 10, 5) and not ui:hoverable(0, 0, 5, 5), "hoverable suit le pointeur")
		ui:text_basic("x", 1, 2); ui:spacer(3)
		t:egal(f.cy, 32 + 11 + 3, "text_basic descend de 11, spacer de n")
		ui.faute = { methode = "spacer", fenetre = "autre" }
		ui:spacer(1)
		ui.faute = { methode = "spacer", fenetre = "T" }
		t:verifier(not pcall(ui.spacer, ui, 1), "faute injectee limitee a la fenetre")
		ui:end_window()
		t:egal({ #ui.window_stack, #ui.region_stack }, { 0, 0 }, "end_window depile les deux")
	end)
end)
