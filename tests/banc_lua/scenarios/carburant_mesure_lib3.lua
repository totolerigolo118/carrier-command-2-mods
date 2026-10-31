-- Scenarios de tour/etudes_modes_carburant/lua/library_custom_3.lua : TELEMETRIE des avions en LECTURE SEULE (etude ECO / NORMAL / FLANK).
-- Il ecrit des lignes "CC2MODES|..." dans cc2x.log (SDK CC2X >= 0.5.0, API >= 4) ; sans CC2X il ne fait rien.
-- Format reel verifie sur le journal du 28/10 : tour/etudes_modes_carburant/mesures/2026-10-28_partie1_CC2MODES.csv (12 champs par avion).
local cadre = ...
local Jeu = require("fausse_api.jeu")
local Contexte = require("fausse_api.contexte")
local A = require("fausse_api.aides")

local E = Jeu.ETAT
local SCRIPT = "tour/etudes_modes_carburant/lua/library_custom_3.lua"

local function decouper(texte, sep)
	local r = {}
	for morceau in (texte .. sep):gmatch("(.-)" .. sep:gsub("%p", "%%%0")) do r[#r + 1] = morceau end
	return r
end

-- lignes CC2MODES du journal cc2x.log, analysees
local function lignes(jeu, genre)
	local r = {}
	for _, l in ipairs(jeu.journal_cc2x) do
		local p = decouper(l, "|")
		if p[1] == "CC2MODES" and (genre == nil or p[2] == genre) then
			r[#r + 1] = { brut = l, genre = p[2], tick = tonumber(p[3]), ecran = p[4], reste = { table.unpack(p, 5) } }
		end
	end
	return r
end

local function items(ligne)         -- ligne "A" -> liste de listes de 12 champs
	local r = {}
	for _, it in ipairs(decouper(ligne.reste[2], ";")) do r[#r + 1] = decouper(it, ",") end
	return r
end

local function avion_en_vol(jeu, id, extra)
	local v = { id = id, def = Jeu.DEFS.chassis_air_wing_light, dock_state = E.VOL, x = 19622.4, y = 24.2, z = 14625.0,
		vitesse = 70.12, fuel = 0.9973675, vitesse_cible = 48.0, puissance = 1.0 }
	for k, x in pairs(extra or {}) do v[k] = x end
	return jeu:ajouter(v)
end

-- ecran de bord avec la table cc2x (opts_cc2x nil = pas de SDK)
local function ecran(jeu, opts_cc2x, opts)
	opts = opts or {}
	local ctx = Contexte.nouveau(jeu, { nom = opts.nom or "screen_veh_m", profil = opts.profil or "bord", vehicule_ecran = opts.vehicule_ecran, cc2x = opts_cc2x, liaison = opts.liaison })
	ctx:monter({ ecran = opts.ecran or "bord_controle", libs = { SCRIPT }, ordre = opts.ordre })
	return ctx
end

cadre.groupe("library_custom_3.lua : telemetrie des avions (lecture seule)", function()

	cadre.scenario("se charge sans erreur dans les 4 ordres ; sans CC2X ou avec un SDK trop ancien (API 3) : muet", function(t)
		for _, c in ipairs(A.COMBINAISONS) do
			for _, cas in ipairs({ { "sans cc2x", nil }, { "SDK 0.4 (API 3)", { niveau = "0.4" } } }) do
				local jeu = Jeu.nouveau()
				avion_en_vol(jeu, 9)
				local ctx = ecran(jeu, cas[2], c)
				jeu:jouer(10)
				t:verifier(#ctx.erreurs == 0, ("%s : aucune erreur (%s)"):format(cas[1], A.nom_combinaison(c)), ctx.erreurs[1])
				t:egal(#jeu.journal_cc2x, 0, ("%s : aucune ligne dans cc2x.log (%s)"):format(cas[1], A.nom_combinaison(c)))
			end
		end
	end)

	cadre.scenario("barriere d'API : exige cc2x.api >= 4 (nombre) meme si le reste de la table existe", function(t)
		for _, cas in ipairs({ { 3, false }, { "4", false }, { 4, true }, { 5, true } }) do
			local jeu = Jeu.nouveau()
			avion_en_vol(jeu, 9)
			local ctx = ecran(jeu, { niveau = "0.5" })
			ctx.env.cc2x.api = cas[1]
			jeu:jouer_jusqu_au_tick(5)
			t:egal(#lignes(jeu, "A") > 0, cas[2], ("cc2x.api = %s : %s"):format(tostring(cas[1]), cas[2] and "mesure ecrite" or "rien ecrit"))
			t:verifier(#ctx.erreurs == 0, "aucune erreur")
		end
	end)

	cadre.scenario("ne cree que ses propres globales (un seul drapeau g_cm_mesure_*)", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", cc2x = { niveau = "0.5" } })
		ctx:charger_ecran("bord_controle")
		local avant = A.cles(ctx.env)
		ctx:charger_script(SCRIPT)
		t:egal(A.nouvelles_cles(avant, ctx.env), { "g_cm_mesure_accroche" }, "globales creees au chargement")
		ctx:begin()
		local apres = {}
		for _, k in ipairs(A.nouvelles_cles(avant, ctx.env)) do if k:sub(1, 2) == "g_" then apres[#apres + 1] = k end end     -- begin() lie aussi l'API C du jeu
		t:egal(apres, { "g_cm_mesure_accroche", "g_cm_mesure_update" }, "globales du script apres begin()")
	end)

	cadre.scenario("en-tete une fois ; une mesure toutes les 150 ticks (5 s) ; format identique au journal reel", function(t)
		local jeu = Jeu.nouveau()
		avion_en_vol(jeu, 9)
		local ctx = ecran(jeu, { niveau = "0.5" })
		jeu:jouer_jusqu_au_tick(1500)
		local h, a = lignes(jeu, "H"), lignes(jeu, "A")
		t:egal(#h, 1, "une seule ligne d'en-tete")
		t:egal(h[1].brut, "CC2MODES|H|1|screen_veh_m|1|cc2x=0.5.0/api4", "en-tete : version du format, version et API du SDK")
		local ticks = {}
		for _, l in ipairs(a) do ticks[#ticks + 1] = l.tick end
		t:egal(ticks, { 1, 150, 300, 450, 600, 750, 900, 1050, 1200, 1350, 1500 }, "une mesure par tranche de 150 ticks")
		local it = items(a[1])[1]
		t:egal(it, { "9", "8", "19622", "24", "14625", "70.1", "797.894", "48.0", "1.000", "0.997", "-", "-" },
			"12 champs comme dans le CSV du 28/10 (id, def, x, y, z, vitesse, carburant, control_speed, control_power, jeu_carburant, jeu_vitesse = '-', jeu_gaz = '-')")
		t:egal(a[1].reste[1], "1/1", "numero de ligne p/n")
		t:verifier(#ctx.erreurs == 0 and #lignes(jeu, "E") == 0, "aucune erreur ni ligne d'erreur")
		t:verifier(#jeu.avertissements == 0, "aucune ligne tronquee ni avertissement", jeu.avertissements[1])
	end)

	cadre.scenario("jeu_vitesse / jeu_gaz : '-' quand le contexte n'a pas ces methodes (96 % du journal reel), valeurs sinon", function(t)
		local jeu = Jeu.nouveau()
		local av = avion_en_vol(jeu, 9)
		av.gaz = 0.93
		ecran(jeu, { niveau = "0.5" })
		jeu:jouer_jusqu_au_tick(5)
		local it = items(lignes(jeu, "A")[1])[1]
		t:egal({ it[10], it[11], it[12] }, { "0.997", "-", "-" }, "get_fuel_factor lu ; get_linear_speed et get_throttle_factor absents (cas majoritaire du journal reel) -> '-'")
		local jeu2 = Jeu.nouveau()
		jeu2.avec_vitesse_gaz = true
		local av2 = avion_en_vol(jeu2, 9); av2.gaz = 0.93
		ecran(jeu2, { niveau = "0.5" })
		jeu2:jouer_jusqu_au_tick(5)
		local it2 = items(lignes(jeu2, "A")[1])[1]
		t:egal({ it2[10], it2[11], it2[12] }, { "0.997", "70.1", "0.930" }, "si le jeu les fournit : lues et formatees (1 et 3 decimales)")
	end)

	cadre.scenario("selection : seulement les avions (ailes fixes) EN VOL de l'equipe de l'ecran", function(t)
		local jeu = Jeu.nouveau()
		avion_en_vol(jeu, 9)                                                                    -- garde
		avion_en_vol(jeu, 10, { dock_state = E.HANGAR })                                        -- au hangar : flight_state 0
		avion_en_vol(jeu, 11, { def = Jeu.DEFS.chassis_air_rotor_light })                       -- helicoptere : is_wing faux
		avion_en_vol(jeu, 12, { team = 0 })                                                     -- avion de l'IA
		avion_en_vol(jeu, 13, { def = Jeu.DEFS.chassis_air_wing_heavy })                        -- garde (Manta)
		jeu:ajouter({ id = 1, def = Jeu.DEFS.chassis_carrier })                                 -- porte-avions
		ecran(jeu, { niveau = "0.5" }, { vehicule_ecran = 1 })
		jeu:jouer_jusqu_au_tick(5)
		local ids = {}
		for _, it in ipairs(items(lignes(jeu, "A")[1])) do ids[#ids + 1] = it[1] end
		t:egal(ids, { "9", "13" }, "seuls 9 et 13 sont journalises")
	end)

	cadre.scenario("14 avions : 3 lignes (6 + 6 + 2), numerotees p/n, chacune sous la limite de 900 caracteres de cc2x.log", function(t)
		local jeu = Jeu.nouveau()
		for i = 1, 14 do avion_en_vol(jeu, 100 + i, { x = 12345678.9, y = 99999.4, z = -12345678.9, vitesse = 289.99, fuel = 1.0, def = Jeu.DEFS.chassis_air_wing_heavy }) end
		ecran(jeu, { niveau = "0.5" })
		jeu:jouer_jusqu_au_tick(5)
		local a = lignes(jeu, "A")
		t:egal(#a, 3, "3 lignes")
		t:egal({ #items(a[1]), #items(a[2]), #items(a[3]) }, { 6, 6, 2 }, "6 + 6 + 2 avions")
		t:egal({ a[1].reste[1], a[2].reste[1], a[3].reste[1] }, { "1/3", "2/3", "3/3" }, "numeros p/n")
		local pire = 0
		for _, l in ipairs(a) do pire = math.max(pire, #l.brut) end
		t:verifier(pire <= 900, "ligne la plus longue (avec des coordonnees extremes) sous 900 caracteres", pire)
		t:verifier(#jeu.avertissements == 0, "la fausse cc2x.log n'a rien tronque", jeu.avertissements[1])
		for _, l in ipairs(a) do for _, it in ipairs(items(l)) do t:verifier(#it == 12, "12 champs par avion", #it) end end
	end)

	cadre.scenario("methodes du jeu absentes ou en erreur : '-' dans les champs jeu_*, sans erreur", function(t)
		local jeu = Jeu.nouveau()
		avion_en_vol(jeu, 9)
		local ctx = ecran(jeu, { niveau = "0.5" })
		ctx.env.update_get_map_vehicle_by_id = function() return nil end
		jeu:jouer_jusqu_au_tick(5)
		t:egal({ items(lignes(jeu, "A")[1])[1][10] }, { "-" }, "objet du jeu nil : '-'")
		ctx.env.update_get_map_vehicle_by_id = function() return { get = function() return true end, get_fuel_factor = function() error("boum") end } end
		jeu:jouer_jusqu_au_tick(160)
		t:egal({ items(lignes(jeu, "A")[2])[1][10] }, { "-" }, "get_fuel_factor qui plante : '-'")
		ctx.env.update_get_map_vehicle_by_id = nil
		jeu:jouer_jusqu_au_tick(310)
		t:egal({ items(lignes(jeu, "A")[3])[1][10] }, { "-" }, "update_get_map_vehicle_by_id absente : '-'")
		t:verifier(#ctx.erreurs == 0 and #lignes(jeu, "E") == 0, "aucune erreur")
	end)

	cadre.scenario("erreur dans le SDK : une ligne 'E' la 1re fois seulement, chemins Windows masques, l'ecran continue", function(t)
		local jeu = Jeu.nouveau()
		avion_en_vol(jeu, 9)
		local ctx = ecran(jeu, { niveau = "0.5" })
		local vrai = ctx.env.cc2x.vehicles
		ctx.env.cc2x.vehicles = function() error("C:\\Users\\UTILISATEUR\\AppData\\x.lua:12: boom", 0) end
		jeu:jouer_jusqu_au_tick(1000)
		local e = lignes(jeu, "E")
		t:egal(#e, 1, "une seule ligne d'erreur malgre 7 tentatives")
		t:verifier(e[1] and e[1].reste[1] == "<chemin> boom", "chemin Windows remplace par <chemin>", e[1] and e[1].reste[1])
		ctx.env.cc2x.vehicles = function() error("autre erreur", 0) end
		jeu:jouer_jusqu_au_tick(1200)
		t:egal(#lignes(jeu, "E"), 2, "une erreur differente est journalisee")
		t:verifier(#ctx.erreurs == 0, "l'ecran n'a jamais recu d'erreur")
		ctx.env.cc2x.vehicles = vrai
		jeu:jouer_jusqu_au_tick(1400)
		t:verifier(#lignes(jeu, "A") > 0, "la mesure reprend des que le SDK repond")
	end)

	cadre.scenario("retour en arriere du tick (nouvelle partie) : l'en-tete est re-ecrite", function(t)
		local jeu = Jeu.nouveau()
		avion_en_vol(jeu, 9)
		ecran(jeu, { niveau = "0.5" })
		jeu:jouer_jusqu_au_tick(400)
		jeu.tick = 20                                  -- chargement d'une autre partie
		jeu:jouer(1)
		t:egal(#lignes(jeu, "H"), 2, "2e en-tete apres le retour en arriere")
		jeu.tick = 400 - 30                            -- petit retour (< 60 ticks) : pas de nouvelle en-tete
		jeu:jouer(1)
		t:egal(#lignes(jeu, "H"), 2, "un retour de moins de 60 ticks ne compte pas comme une nouvelle partie")
	end)

	cadre.scenario("tick nul ou illisible : rien n'est ecrit", function(t)
		local jeu = Jeu.nouveau()
		avion_en_vol(jeu, 9)
		local ctx = ecran(jeu, { niveau = "0.5" })
		local vrai = ctx.env.cc2x.tick
		ctx.env.cc2x.tick = function() return nil end
		jeu:jouer(3)
		ctx.env.cc2x.tick = function() return 0 end
		jeu:jouer(3)
		ctx.env.cc2x.tick = function() return "12" end
		jeu:jouer(3)
		t:egal(#jeu.journal_cc2x, 0, "aucune ligne pour tick nil, 0 ou texte")
		t:verifier(#ctx.erreurs == 0, "aucune erreur")
	end)

	cadre.scenario("l'enveloppe de update est transparente (7 parametres, retours avec nil) et unique", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", cc2x = { niveau = "0.5" } })
		ctx:charger_texte("function update(...) g_recu = table.pack(...); return 1, nil, 3, nil end function begin() begin_load() end", "ecran_nil")
		ctx:charger_script(SCRIPT); ctx:charger_script(SCRIPT)
		ctx:begin(); ctx:begin()
		local r = ctx:update_brut(300, 200, 0.5, 33.0, "p5", nil, "p7")
		t:egal({ r.n, r[2], r[3], r[4], r[5] }, { 5, 1, nil, 3, nil }, "retours conserves")
		t:egal(ctx.env.g_recu.n, 7, "7 parametres retransmis")
	end)

	cadre.scenario("plusieurs ecrans de bord : chacun ecrit sa mesure (doublons attendus, nom d'ecran dans la ligne)", function(t)
		local jeu = Jeu.nouveau()
		avion_en_vol(jeu, 9)
		for _, nom in ipairs({ "screen_veh_l", "screen_veh_m", "screen_veh_r" }) do ecran(jeu, { niveau = "0.5" }, { nom = nom }) end
		jeu:jouer_jusqu_au_tick(5)
		local a = lignes(jeu, "A")
		local ecrans = {}
		for _, l in ipairs(a) do ecrans[#ecrans + 1] = l.ecran end
		table.sort(ecrans)
		t:egal(ecrans, { "screen_veh_l", "screen_veh_m", "screen_veh_r" }, "3 lignes identiques, une par ecran (documente dans l'en-tete du script)")
	end)

	cadre.scenario("RISQUE MES-R1 : cc2x.vehicles(equipe) n'est pas documente (LUA_API.md 0.4.0 : sans argument)", function(t)
		t:risque("MES-R1", "si le SDK 0.5.0 ignore l'argument d'equipe, les avions de l'IA sont journalises comme 'ton equipe'", function()
			local jeu = Jeu.nouveau()
			avion_en_vol(jeu, 9)
			avion_en_vol(jeu, 12, { team = 0 })
			ecran(jeu, { niveau = "0.5", equipe_ignoree = true })
			jeu:jouer_jusqu_au_tick(5)
			local ids = {}
			for _, it in ipairs(items(lignes(jeu, "A")[1])) do ids[#ids + 1] = it[1] end
			return #ids == 2, "avions journalises : " .. table.concat(ids, ",")
		end)
	end)

	cadre.scenario("RISQUE MES-R3 : l'idiome 'a and f(x) or f()' bascule sur TOUTES les equipes quand cc2x.vehicles(equipe) renvoie nil", function(t)
		t:risque("MES-R3", "library_custom_3.lua l. 68 : (equipe ~= nil) and cc2x.vehicles(equipe) or cc2x.vehicles() ; LUA_API.md : les fonctions CC2X renvoient nil quand 'quelque chose n'est pas disponible'", function()
			local jeu = Jeu.nouveau()
			avion_en_vol(jeu, 9)
			avion_en_vol(jeu, 12, { team = 0 })
			local ctx = ecran(jeu, { niveau = "0.5" })
			local vrai = ctx.env.cc2x.vehicles
			ctx.env.cc2x.vehicles = function(equipe) if equipe ~= nil then return nil end return vrai() end
			jeu:jouer_jusqu_au_tick(5)
			local ids = {}
			for _, it in ipairs(items(lignes(jeu, "A")[1])) do ids[#ids + 1] = it[1] end
			return #ids == 2, "avions journalises : " .. table.concat(ids, ",")
		end)
	end)

	cadre.scenario("RISQUE MES-R4 : l'enveloppe 'update = function(...)' fait passer nparams de 7 a 0 sur l'ecran de pilotage", function(t)
		t:risque("MES-R4", "partage_detail/07 : l'ecran de pilotage 'is recognised by debug.getinfo(update).nparams == 7' ; library_custom_3.lua l. 128 remplace update par une fonction vararg dans TOUT etat qui appelle begin_load", function()
			local jeu = Jeu.nouveau()
			local ctx = Contexte.nouveau(jeu, { nom = "?", profil = "hud", cc2x = { niveau = "0.5" } })
			ctx:charger_texte("function update(a, b, c, d, e, f, g) end function begin() begin_load() end", "hud_7_parametres")
			local avant = debug.getinfo(ctx.env.update, "u").nparams
			ctx:charger_script(SCRIPT)
			ctx:begin()
			local apres = debug.getinfo(ctx.env.update, "u").nparams
			return avant == 7 and apres == 0, ("nparams avant = %d, apres = %d"):format(avant, apres)
		end)
	end)

	cadre.scenario("RISQUE MES-R2 : un etat Lua sans update_get_screen_team_id (ecran d'indications) journalise TOUTES les equipes", function(t)
		t:risque("MES-R2", "begin_load est appele par l'ecran d'indications (hypothese de tour/auto) et cet etat n'a pas l'API du monde : equipe = nil -> cc2x.vehicles() complet, nom d'ecran '?'", function()
			local jeu = Jeu.nouveau()
			avion_en_vol(jeu, 9)
			avion_en_vol(jeu, 12, { team = 0 })
			local hud = ecran(jeu, { niveau = "0.5" }, { profil = "hud", ecran = "indications", nom = "?" })
			jeu:jouer_jusqu_au_tick(5)
			local a = lignes(jeu, "A")
			local ids = {}
			for _, it in ipairs(items(a[1])) do ids[#ids + 1] = it[1] end
			return #a == 1 and a[1].ecran == "?" and #ids == 2, "ecran '" .. tostring(a[1] and a[1].ecran) .. "', avions : " .. table.concat(ids, ",")
		end)
	end)
end)
