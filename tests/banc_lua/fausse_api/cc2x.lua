-- FAUSSE TABLE cc2x (le SDK CC2X de DYOR + le plugin maison cc2x_modes.dll v3).
--
-- Niveaux de fidelite :
--   "0.4"  = ce que dit passation_windows/sdk_public_cc2x/LUA_API.md (copie du 25/10, SDK 0.4.0, API 3) : DOC.
--            cc2x.vehicles() SANS argument ; champs d'un vehicule : id, definition, team, dock_state, attached_to, hp, fuel, x, y, z.
--   "0.5"  = SDK 0.5.0 (API 4) : le texte de son LUA_API.md (137 lignes) N'EST PAS dans le depot. On n'en sait que ce que disent
--            tour/atterrissage_manuel/VERDICT_relecture_SDK.md et tour/etudes_modes_carburant/ETUDE.md (annexe B) : cc2x.vehicle(id) donne
--            speed, fuel, control_speed, control_power, team_is_ai, is_wing... ; fonctions de commande. Les noms exacts des champs
--            (flight_state, is_wing...) et cc2x.tick() sont DEDUITS de library_custom_3.lua : statut SCRIPT, comportement SUPPOSE.
--   plugin modes (cc2x.modes.*) : LU dans tour/etudes_modes_carburant/plugin/cc2x_modes.c (commentaire d'en-tete et lua_set/get/hold/status).
-- Principe documente : "CC2X functions never raise Lua errors; they return nil (or false) when something is not available."

local Inv = require("fausse_api.inventaire")
local Jeu = require("fausse_api.jeu")
local decl = Inv.decl

local Cc2x = {}

local RESERVOIR = { [8] = 800, [10] = 1200 }    -- SUPPOSE (tour/etudes_modes_carburant/lua/v2 : RESERVOIR) : carburant absolu = fuel_factor * reservoir

local function etat_de_vol(v)
	-- DOC (passation_windows/COMPARAISON_MAC_WINDOWS.md) : 0 gare, 1 sol, 2 en vol
	if v.flight_state ~= nil then return v.flight_state end
	if v.dock_state == Jeu.ETAT.VOL then return 2 end
	if v.dock_state == Jeu.ETAT.HANGAR then return 0 end
	return 1
end

local function est_aile(v)
	return v.def == Jeu.DEFS.chassis_air_wing_light or v.def == Jeu.DEFS.chassis_air_wing_heavy
end

-- options : niveau ("0.4"|"0.5"), plugin_modes (true|false), equipe_ignoree (vrai : vehicles(team) ignore son argument),
--           enregistrer (fonction(plugin) appelee pour que le scenario voie les appels), plugin_v1 (set/get seulement)
function Cc2x.nouveau(jeu, opts)
	opts = opts or {}
	local niveau = opts.niveau or "0.5"
	local t = {}
	local sdk = { jeu = jeu, niveau = niveau, appels_modes = {}, lignes_log = jeu.journal_cc2x }
	t.version = (niveau == "0.5") and "0.5.0" or "0.4.0"    -- DOC (LUA_API.md : chaine de version) ; 0.5.0 pour le SDK installe (JOURNAL_atterrissage.md)
	t.api = (niveau == "0.5") and 4 or 3                      -- DOC (VERDICT_relecture_SDK.md : API 3 -> 4 en 0.5.0)
	t.game_build = "1.5.18-win32"                             -- DOC (LUA_API.md)

	decl("cc2x", "has", "DOC", "vrai si un plugin a enregistre la fonctionnalite (ici : \"modes\" quand le plugin est charge)")
	t.has = function(nom) return nom == "modes" and opts.plugin_modes == true end

	decl("cc2x", "log", "DOC", "ecrit ses arguments (separes par une espace, SUPPOSE) sur UNE ligne de cc2x.log ; 900 caracteres au plus (VERDICT_relecture_SDK.md : lua_world.c) : la fausse version REFUSE le depassement (avertissement + ligne tronquee)")
	t.log = function(...)
		local m = {}
		for i = 1, select("#", ...) do m[#m + 1] = tostring((select(i, ...))) end
		local ligne = table.concat(m, " ")
		if #ligne > 900 then
			jeu:avertir("cc2x.log : ligne de " .. #ligne .. " caracteres tronquee a 900")
			ligne = ligne:sub(1, 900)
		end
		jeu.journal_cc2x[#jeu.journal_cc2x + 1] = ligne
	end

	local function instantane(v)
		local reservoir = RESERVOIR[v.def] or 1000
		local r = {
			id = v.id, definition = v.def, team = v.team, dock_state = v.dock_state, attached_to = v.attached_parent,
			hp = v.hp or 100.0, fuel = v.fuel * reservoir, x = v.x, y = v.y, z = v.z,
		}
		if niveau == "0.5" then
			-- SCRIPT : champs lus par library_custom_3.lua ; noms DEDUITS (ETUDE.md annexe B ne cite que speed, fuel, control_speed, control_power, team_is_ai, is_wing)
			r.speed = v.vitesse
			r.control_speed = v.vitesse_cible or 0.0
			r.control_power = v.puissance or 1.0
			r.team_is_ai = (v.team == 0)
			r.is_wing = est_aile(v)
			r.flight_state = etat_de_vol(v)
		end
		return r
	end

	decl("cc2x", "vehicles", "DOC", "tableau de TOUS les vehicules du serveur (LUA_API.md : sans argument). En 0.5 le banc SUPPOSE qu'un argument numerique filtre par equipe (library_custom_3 le suppose) ; opts.equipe_ignoree=true montre le cas contraire")
	t.vehicles = function(equipe)
		local r = {}
		for _, id in ipairs(jeu.ordre_ids) do
			local v = jeu.vehicules[id]
			local garde = true
			if niveau == "0.5" and type(equipe) == "number" and not opts.equipe_ignoree then garde = (v.team == equipe) end
			if garde then r[#r + 1] = instantane(v) end
		end
		return r
	end
	decl("cc2x", "vehicle", "DOC", "un vehicule ou nil")
	t.vehicle = function(id)
		local v = jeu.vehicules[id]
		return v and instantane(v) or nil
	end
	decl("cc2x", "tiles", "DOC", "tableau des tuiles (vide ici : aucun script du depot ne s'en sert)")
	t.tiles = function() return {} end
	decl("cc2x", "tile", "DOC", "une tuile ou nil (toujours nil ici)")
	t.tile = function() return nil end

	if niveau == "0.5" then
		decl("cc2x", "tick", "SCRIPT", "tick logique du serveur (entier) ; absent de la doc 0.4.0, appele par library_custom_3.lua ; SUPPOSE identique a update_get_logic_tick")
		t.tick = function() return jeu.tick end
	end

	-- --------------------------------------------------------------- plugin modes (v3)
	if opts.plugin_modes then
		local HOLD_TICKS, MAX_SET = 90, 64
		local plugin = {
			table_modes = {},     -- id -> mode (0 NORMAL, 1 ECO, 2 FLANK)
			nb = 0,
			tenus = {},           -- id -> tick jusqu'auquel l'avion est tenu (hold)
			actif = {},           -- id -> 0 aucun / 1 ECO / 2 FLANK (ce que le plugin ECRIRAIT ; fixe par le scenario, jamais calcule ici)
			enabled = false,      -- modes.ini enabled=1 ?
			ini = { eco_cap_light = 0.65, eco_cap_heavy = 0.35, flank_floor_light = 1.0, flank_floor_heavy = 1.0 },
			appels = sdk.appels_modes,
		}
		sdk.plugin = plugin

		-- LU (cc2x_modes.c l_tointeger de cc2x.c:620) : accepte un entier ou un flottant (tronque) ; refuse texte/booleen/nil
		local function entier(v)
			if math.type(v) == "integer" then return v end
			if math.type(v) == "float" and v == v and v > -9.3e18 and v < 9.3e18 then return math.tointeger(v >= 0 and math.floor(v) or math.ceil(v)) end
			return nil
		end
		local function id_valide(v)
			local n = entier(v)
			if n == nil or n <= 0 or n > 0x7fffffff then return nil end
			return n
		end

		local modes = {}
		decl("cc2x.modes (plugin v3)", "set", "DOC", "LU dans cc2x_modes.c : set(id, mode), id entier 1..0x7fffffff, mode 0 NORMAL / 1 ECO / 2 FLANK -> true ; sinon false (arguments faux ou table pleine : 64 avions)")
		modes.set = function(id, mode)
			plugin.appels[#plugin.appels + 1] = { "set", id, mode, tick = jeu.tick }
			local i, m = id_valide(id), entier(mode)
			if not i or m == nil or m < 0 or m > 2 then return false end
			if plugin.table_modes[i] == nil then
				if plugin.nb >= MAX_SET then return false end
				plugin.nb = plugin.nb + 1
			end
			plugin.table_modes[i] = m
			return true
		end
		if not opts.plugin_v1 then
			decl("cc2x.modes (plugin v3)", "get", "DOC", "get(id) -> mode demande (0..2), actif (0 rien / 1 ECO / 2 FLANK : ce qui est ecrit en ce moment), tenu (bool) ; nil si id invalide")
			modes.get = function(id)
				plugin.appels[#plugin.appels + 1] = { "get", id, tick = jeu.tick }
				local i = id_valide(id)
				if not i then return nil end
				local tenu = plugin.tenus[i] ~= nil and plugin.tenus[i] > jeu.tick
				return plugin.table_modes[i] or 0, plugin.actif[i] or 0, tenu
			end
			decl("cc2x.modes (plugin v3)", "hold", "DOC", "hold(id) : \"le joueur pilote cet avion\", le plugin lache les gaz pendant 90 ticks (3 s) ; -> true, false si id invalide")
			modes.hold = function(id)
				plugin.appels[#plugin.appels + 1] = { "hold", id, tick = jeu.tick }
				local i = id_valide(id)
				if not i then return false end
				plugin.tenus[i] = jeu.tick + HOLD_TICKS
				return true
			end
			decl("cc2x.modes (plugin v3)", "status", "DOC", "status() -> { version = 3, enabled, eco_cap_light, eco_cap_heavy, flank_floor_light, flank_floor_heavy }")
			modes.status = function()
				plugin.appels[#plugin.appels + 1] = { "status", tick = jeu.tick }
				return { version = 3, enabled = plugin.enabled, eco_cap_light = plugin.ini.eco_cap_light, eco_cap_heavy = plugin.ini.eco_cap_heavy,
					flank_floor_light = plugin.ini.flank_floor_light, flank_floor_heavy = plugin.ini.flank_floor_heavy }
			end
		end
		t.modes = modes
	end

	sdk.table = t
	return sdk
end

return Cc2x
