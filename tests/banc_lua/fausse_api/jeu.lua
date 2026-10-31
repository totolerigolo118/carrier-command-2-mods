-- LE JEU FACTICE : horloge, monde (vehicules), evenements recus, mots de passe, planning.
-- Un seul "jeu" est partage par tous les contextes Lua (ecrans) d'un scenario, comme le vrai jeu
-- (chaque ecran a son propre etat Lua, mais le monde, l'horloge et le mot de passe de connexion sont communs).
--
-- Statuts utilises dans les commentaires et dans INVENTAIRE_API.md :
--   DOC      decrit dans la documentation du depot (LUA_API.md, WORLD_API.md, partage_detail/, notes de passation)
--   SCRIPT   non documente, mais appele par un script du depot : forme de l'appel connue, comportement DEVINE
--   SUPPOSE  rien ne l'etablit : choix du banc pour pouvoir faire tourner le script

local Jeu = {}
Jeu.__index = Jeu

-- SUPPOSE : update_get_time_since_epoch() rend des secondes (flottant) depuis 1970 (doc 07 : "seconds, real time").
-- On part d'une valeur de l'ordre d'octobre 2026 pour que la precision des flottants soit celle du vrai jeu.
local ORIGINE_REEL = 1793000000.0

function Jeu.nouveau(opts)
	opts = opts or {}
	return setmetatable({
		tick = opts.tick or 0,                 -- DOC : 30 ticks de simulation par seconde de jeu
		reel = opts.reel or ORIGINE_REEL,      -- secondes reelles
		reste_ticks = 0.0,
		vehicules = {},                        -- id -> enregistrement
		ordre_ids = {},                        -- ids dans l'ordre d'ajout (pour update_get_map_vehicle_by_index)
		equipe_joueur = opts.equipe_joueur or 1,   -- DOC (doc 08) : les numeros d'equipe varient selon la partie ; 0 = IA
		pairs_reseau = opts.pairs_reseau or { { equipe = opts.equipe_joueur or 1 } },
		evenements = {},                       -- update_ui_event recus : { ctx, nom, args, tick, reel }
		journal_cc2x = {},                     -- lignes ecrites par cc2x.log
		avertissements = {},                   -- appels suspects releves par la fausse API (types, bornes...)
		mot_de_passe_connexion = "",           -- update_get/set_join_password : COMMUN a tous les contextes
		mot_de_passe_hote = nil,               -- update_set_host_password (boite aux lettres du script d'essai auto)
		mods = opts.mods or {},                -- update_get_mod_details()
		sauvegardes = opts.sauvegardes or {    -- update_get_save_slots() ; champs DOC (doc 07) : slot_index, display_name, save_name, time
			{ slot_index = 3, display_name = "slot 3", save_name = "slot_3", time = 0 },
			{ slot_index = 18, display_name = "slot 18", save_name = "slot_18", time = 0 },
			{ slot_index = 19, display_name = "slot 19", save_name = "slot_19", time = 0 },
		},
		planning = {},                         -- tick -> liste de fonctions
		contextes = {},
		prochain_waypoint = 1,
		refuser_ordres = false,                -- vrai : add_waypoint & co levent une erreur (ordre refuse)
		refuser_ids = nil,                     -- { [id] = true } : seuls les ordres adresses a ces vehicules sont refuses
		journal_ordres = {},                   -- { tick, id, nom, args } pour chaque ordre de vol ACCEPTE
		au_ordre = nil,                        -- hook(jeu, vehicule, genre, ...) appele apres chaque ordre de vol
	}, Jeu)
end

-- ------------------------------------------------------------------ vehicules
local DEFS = {   -- DOC : doc 08 section 4 (e_game_object_type)
	chassis_carrier = 0, chassis_land_wheel_light = 2, chassis_land_wheel_medium = 4, chassis_land_wheel_heavy = 6,
	chassis_air_wing_light = 8, chassis_air_wing_heavy = 10, chassis_air_rotor_light = 12, chassis_air_rotor_heavy = 14,
}
Jeu.DEFS = DEFS

-- etats d'accostage (DOC : partage_detail/03, e_vehicle_dock_state)
Jeu.ETAT = { VOL = 0, ATTERRIT = 1, DEMANDE = 2, SORTIE = 3, HANGAR = 4, FILE = 5, PONT = 6, ATTENTE = 7 }

function Jeu:ajouter(v)
	assert(type(v.id) == "number" and v.id > 0, "id de vehicule invalide")
	assert(self.vehicules[v.id] == nil, "id deja pris : " .. v.id)
	v.team = v.team or self.equipe_joueur
	v.def = v.def or DEFS.chassis_air_wing_light
	v.dock_state = v.dock_state or Jeu.ETAT.VOL
	v.dock_parent = v.dock_parent or -1       -- SUPPOSE : -1 quand il n'y a pas de parent
	v.attached_parent = v.attached_parent or -1
	v.x, v.y, v.z = v.x or 0.0, v.y or 0.0, v.z or 0.0
	v.fuel = v.fuel or 1.0
	v.ammo = v.ammo or 1.0
	v.vitesse = v.vitesse or 0.0
	v.gaz = v.gaz or 0.0
	v.waypoints = v.waypoints or {}
	v.visible = (v.visible == nil) and true or v.visible
	v.baies = v.baies           -- porte-avions : [numero de baie] = id de vehicule rattache
	self.vehicules[v.id] = v
	self.ordre_ids[#self.ordre_ids + 1] = v.id
	return v
end

function Jeu:retirer(id)       -- vehicule detruit : l'objet disparait de la carte
	self.vehicules[id] = nil
	for i, x in ipairs(self.ordre_ids) do
		if x == id then table.remove(self.ordre_ids, i); break end
	end
end

function Jeu:avertir(msg)
	self.avertissements[#self.avertissements + 1] = msg
end

-- ------------------------------------------------------------------ temps et planning
function Jeu:a_tick(tick, fn)
	local l = self.planning[tick]
	if not l then l = {}; self.planning[tick] = l end
	l[#l + 1] = fn
end

function Jeu:dans(ticks, fn) self:a_tick(self.tick + ticks, fn) end

function Jeu:avancer_ticks(n)
	for _ = 1, n do
		self.tick = self.tick + 1
		local l = self.planning[self.tick]
		if l then
			self.planning[self.tick] = nil
			for _, fn in ipairs(l) do fn(self) end
		end
	end
end

-- avance l'horloge reelle de dt secondes ; la simulation avance de 30 * dt * vitesse ticks (vitesse 1.0 = temps reel)
function Jeu:avancer(dt, vitesse)
	vitesse = vitesse or 1.0
	self.reel = self.reel + dt
	self.reste_ticks = self.reste_ticks + 30.0 * dt * vitesse
	local n = math.floor(self.reste_ticks + 1e-9)
	self.reste_ticks = self.reste_ticks - n
	self:avancer_ticks(n)
end

-- joue des images : a chaque image l'horloge avance puis chaque contexte actif recoit update().
--   opts.fps (30)   opts.vitesse (1.0)   opts.contextes (tous)   opts.jusqu_a(jeu) -> vrai pour s'arreter
function Jeu:jouer(secondes_reelles, opts)
	opts = opts or {}
	local fps = opts.fps or 30
	local dt = 1.0 / fps
	local ctxs = opts.contextes or self.contextes
	local n = math.floor(secondes_reelles * fps + 0.5)
	for _ = 1, n do
		self:avancer(dt, opts.vitesse)
		for _, c in ipairs(ctxs) do c:image(dt) end
		if opts.jusqu_a and opts.jusqu_a(self) then return true end
	end
	return false
end

-- joue jusqu'a ce que le tick de jeu atteigne `tick` (vitesse reglable), 30 images par seconde reelle
function Jeu:jouer_jusqu_au_tick(tick, opts)
	opts = opts or {}
	local garde = 0
	local ctxs = opts.contextes or self.contextes
	local fps = opts.fps or 30
	local dt = 1.0 / fps
	while self.tick < tick do
		self:avancer(dt, opts.vitesse)
		for _, c in ipairs(ctxs) do c:image(dt) end
		garde = garde + 1
		if garde > 5000000 then error("jouer_jusqu_au_tick : trop d'images (vitesse nulle ?)") end
		if opts.jusqu_a and opts.jusqu_a(self) then return true end
	end
	return false
end

-- ------------------------------------------------------------------ evenements (update_ui_event)
function Jeu:evenement(nom_contexte, nom, args)
	self.evenements[#self.evenements + 1] = { ctx = nom_contexte, nom = nom, args = args, tick = self.tick, reel = self.reel }
end

function Jeu:evenements_nommes(nom)
	local r = {}
	for _, e in ipairs(self.evenements) do if e.nom == nom then r[#r + 1] = e end end
	return r
end

return Jeu
