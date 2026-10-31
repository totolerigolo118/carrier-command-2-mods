-- Objets que l'API du jeu renvoie aux scripts : poignee de vehicule (update_get_map_vehicle_by_id & co) et vec2.
-- Les scripts appellent  v:get()  puis  v:get_dock_state()  etc. : ce sont des POIGNEES (toujours renvoyees, jamais nil) ;
-- v:get() dit si le vehicule existe encore. Appeler une methode de lecture sur un vehicule disparu LEVE une erreur ici
-- (SUPPOSE : le vrai jeu fait peut-etre autre chose ; cela force les scripts a tester v:get() d'abord).

local Inv = require("fausse_api.inventaire")
local decl = Inv.decl

local Obj = {}

-- ------------------------------------------------------------------ vec2
local Vec2 = {}
Vec2.__index = Vec2
function Vec2:x() return self._x end
function Vec2:y() return self._y end
function Obj.vec2(x, y) return setmetatable({ _x = x, _y = y }, Vec2) end

-- ------------------------------------------------------------------ poignee de vehicule
local M = {}
local OPTIONNELLES
local Poignee = {}
Poignee.__index = function(h, nom)
	if OPTIONNELLES and OPTIONNELLES[nom] and not rawget(h, "_jeu").avec_vitesse_gaz then return nil end
	return M[nom]
end

local function enregistrement(h, nom)
	local v = h._jeu.vehicules[h._id]
	if not v then error(("%s : vehicule %s inexistant (get() est faux)"):format(nom, tostring(h._id)), 3) end
	return v
end

function Obj.poignee(jeu, id)
	return setmetatable({ _jeu = jeu, _id = id }, Poignee)
end

local function lecture(nom, statut, note, fn)
	decl("vehicule (poignee)", nom, statut, note)
	M[nom] = function(h, ...) return fn(enregistrement(h, nom), h, ...) end
end

decl("vehicule (poignee)", "get", "SCRIPT", "vrai si le vehicule existe encore ; la poignee, elle, est toujours renvoyee (jamais nil)")
function M.get(h) return h._jeu.vehicules[h._id] ~= nil end

lecture("get_id", "SCRIPT", "identifiant entier", function(v) return v.id end)
lecture("get_team", "SCRIPT", "numero d'equipe (0 = IA, doc 08)", function(v) return v.team end)
lecture("get_definition_index", "DOC", "e_game_object_type du vehicule (doc 07)", function(v) return v.def end)
lecture("get_dock_state", "DOC", "e_vehicle_dock_state 0..7 (partage_detail/03)", function(v) return v.dock_state end)
lecture("get_dock_parent_id", "DOC", "id du bateau d'accostage (doc 07/03) ; -1 SUPPOSE quand il n'y en a pas", function(v) return v.dock_parent end)
lecture("get_attached_parent_id", "SCRIPT", "id du porte-avions auquel l'appareil est RATTACHE (lu dans screen_propulsion.lua d'apres library_custom_9) ; -1 SUPPOSE si aucun", function(v) return v.attached_parent end)
lecture("get_attached_vehicle_id", "SCRIPT", "porte-avions : id du vehicule range dans la baie n ; -1 SUPPOSE si la baie est vide ou hors limites", function(v, _, baie)
	if type(baie) ~= "number" then error("get_attached_vehicle_id : numero de baie attendu", 2) end
	return (v.baies and v.baies[baie]) or -1
end)
lecture("get_position_xz", "SCRIPT", "vec2 (x(), y()) = x et z horizontaux en metres ; y() est donc le z du monde", function(v) return Obj.vec2(v.x, v.z) end)
lecture("get_velocity_magnitude", "DOC", "vitesse en m/s (ETUDE modes carburant, annexe B)", function(v) return v.vitesse end)
-- MESURE EN JEU (tour/etudes_modes_carburant/mesures/2026-10-28_partie1_CC2MODES.csv, 24 641 lignes) : jeu_vitesse et jeu_gaz valent "-" dans 96 % des
-- lignes (23 690) et sont numeriques dans 4 % (~190 lignes par avion, tous les avions) alors que jeu_carburant (get_fuel_factor) est toujours lu.
-- Les deux methodes (citees dans l'exe, annexe B) existent donc dans CERTAINS contextes/ecrans seulement ; lesquels, le journal ne le dit pas
-- (il melange les ecrans). Le banc prend le cas MAJORITAIRE : absentes, sauf si jeu.avec_vitesse_gaz = true.
OPTIONNELLES = { get_linear_speed = true, get_throttle_factor = true }
lecture("get_linear_speed", "SUPPOSE", "ABSENT par defaut (cas majoritaire du journal du 28/10 : '-' dans 96 % des lignes, numerique dans 4 % : contexte inconnu) ; avec jeu.avec_vitesse_gaz = true : vitesse en m/s", function(v) return v.vitesse end)
lecture("get_throttle_factor", "SUPPOSE", "ABSENT par defaut (cas majoritaire du journal du 28/10 : '-' dans 96 % des lignes, numerique dans 4 % : contexte inconnu) ; avec jeu.avec_vitesse_gaz = true : gaz 0..1", function(v) return v.gaz end)
lecture("get_fuel_factor", "DOC", "carburant restant 0..1 (annexe B)", function(v) return v.fuel end)
lecture("get_ammo_factor", "SCRIPT", "munitions 0..1", function(v) return v.ammo end)
lecture("get_waypoint_count", "SCRIPT", "nombre de waypoints en file", function(v) return #v.waypoints end)
lecture("get_is_fuel_blocked", "SCRIPT", "bool", function(v) return v.fuel_bloque or false end)
lecture("get_is_ammo_blocked", "SCRIPT", "bool", function(v) return v.munitions_bloquees or false end)
lecture("get_is_visible", "DOC", "faux si le vehicule est cache par le brouillard (doc 07)", function(v) return v.visible end)

-- ordres de vol : "equivalents d'une action du joueur" (doc 07 section 3)
local function ordre(nom, statut, note, fn)
	decl("vehicule (poignee)", nom, statut, note)
	M[nom] = function(h, ...)
		local v = enregistrement(h, nom)
		local jeu = h._jeu
		if jeu.refuser_ordres then error(nom .. " : ordre refuse (scenario)", 2) end
		if jeu.refuser_ids and jeu.refuser_ids[v.id] then error(nom .. " : ordre refuse pour le vehicule " .. v.id .. " (scenario)", 2) end
		local r = fn(v, jeu, ...)
		jeu.journal_ordres[#jeu.journal_ordres + 1] = { tick = jeu.tick, id = v.id, nom = nom, args = table.pack(...) }
		if jeu.au_ordre then jeu.au_ordre(jeu, v, nom, ...) end
		return r
	end
end

ordre("clear_waypoints", "DOC", "vide la liste des waypoints", function(v) v.waypoints = {} end)
ordre("clear_attack_target", "DOC", "sans effet visible ici", function() end)
ordre("add_waypoint", "DOC", "ajoute un waypoint (x, z) et RENVOIE son numero (notes : `local wp = v:add_waypoint(..)` puis `set_target_vehicle(wp, ..)`, teste en jeu le 25/10)", function(v, jeu, x, z)
	if type(x) ~= "number" or type(z) ~= "number" then error("add_waypoint : deux nombres attendus", 3) end
	local id = jeu.prochain_waypoint
	jeu.prochain_waypoint = id + 1
	v.waypoints[#v.waypoints + 1] = { id = id, x = x, z = z }
	return id
end)
ordre("set_target_vehicle", "DOC", "attache le waypoint a un vehicule (rappel = waypoint sur le porte-avions + cible)", function(v, jeu, wp, vid)
	if type(wp) ~= "number" or type(vid) ~= "number" then error("set_target_vehicle : deux nombres attendus", 3) end
	for _, w in ipairs(v.waypoints) do
		if w.id == wp then w.cible = vid; return end
	end
	error("set_target_vehicle : waypoint inconnu " .. tostring(wp), 3)
end)

return Obj
