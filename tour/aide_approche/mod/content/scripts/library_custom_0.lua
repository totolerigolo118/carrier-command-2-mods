-- ============================================================================
--  DECOLLAGE AUTO AU DEMARRAGE  --  au debut d'une PARTIE NEUVE, envoie en l'air l'avion
--  pose du porte-avions de ton equipe (le premier avion a ailes, numero le plus petit
--  = en principe l'avion 9 de la baie A1) : il decolle comme si tu lui avais donne un
--  waypoint sur la carte, puis il rejoint un point a 1200 m derriere le navire, a 300 m
--  d'altitude. Tu peux alors le prendre en main et t'entrainer a l'approche.
--
--  - Une seule fois par partie. Rien si la partie est CHARGEE (le jeu a deja tourne
--    longtemps : on n'agit que pendant les 90 premieres secondes de jeu).
--  - Pour l'eteindre : mettre  actif = false  juste en dessous.
--  - Ne fait que donner un ordre normal a un de tes avions (pas de memoire touchee,
--    aucun fichier, aucun reseau). Un message s'affiche 15 s en bas de l'ecran central
--    du pont (screen_veh_m) pour dire ce qui s'est passe.
--  - NON TESTE EN JEU : si l'ordre n'est pas accepte depuis ce contexte, rien ne se
--    passe (le message le dit).
-- ============================================================================

local DA = {
	actif = true,
	fenetre_ticks = 2700,        -- 90 s de jeu (30 tops par seconde) apres le debut de partie
	distance_derriere = 1200,    -- m derriere le navire
	altitude = 300,              -- m
}

g_decollage_auto = g_decollage_auto or { fait = false, message = nil, fin_message = 0 }

local function da_chercher()
	local equipe = update_get_screen_team_id()
	local navire = nil
	for i = 0, update_get_map_vehicle_count() - 1 do
		local v = update_get_map_vehicle_by_index(i)
		if v:get() and v:get_definition_index() == e_game_object_type.chassis_carrier then
			local ok, e = pcall(function() return v:get_team_id() end)
			if ok and e == equipe then navire = v break end
		end
	end
	if navire == nil then return nil, nil end

	local avion = nil
	for i = 0, update_get_map_vehicle_count() - 1 do
		local v = update_get_map_vehicle_by_index(i)
		if v:get() then
			local d = v:get_definition_index()
			if d == e_game_object_type.chassis_air_wing_light or d == e_game_object_type.chassis_air_wing_heavy then
				local ok, e = pcall(function() return v:get_team_id() end)
				if ok and e == equipe and v:get_dock_state() == e_vehicle_dock_state.docked then
					if avion == nil or v:get_id() < avion:get_id() then avion = v end
				end
			end
		end
	end
	return navire, avion
end

local function da_lancer(navire, avion)
	local pos = navire:get_position_xz()
	local dir = navire:get_direction()
	local n = math.sqrt(dir:x() * dir:x() + dir:y() * dir:y())
	if n < 0.001 then return false, "cap du navire inconnu" end
	local x = pos:x() - dir:x() / n * DA.distance_derriere
	local z = pos:y() - dir:y() / n * DA.distance_derriere
	avion:clear_waypoints()
	local wp = avion:add_waypoint(x, z)
	if wp == nil or wp == 0 then return false, "waypoint refuse" end
	avion:set_waypoint_altitude(wp, DA.altitude)
	return true, string.format("plane %d ordered to take off", avion:get_id())
end

function decollage_auto_observer()
	local s = g_decollage_auto
	if s.fait or not DA.actif then return end
	local t = update_get_logic_tick()
	if t > DA.fenetre_ticks then s.fait = true return end   -- partie chargee, ou fenetre passee
	local navire, avion = da_chercher()
	if navire == nil or avion == nil then return end         -- pas encore pret : on reessaie
	s.fait = true
	local ok, res, msg = pcall(da_lancer, navire, avion)
	if ok then s.message = (res and "AUTO LAUNCH: " or "AUTO LAUNCH FAILED: ") .. tostring(msg)
	else s.message = "AUTO LAUNCH ERR: " .. tostring(res) end
	s.fin_message = t + 450
	s.erreur = not (ok and res)
end

function decollage_auto_dessiner(screen_w, screen_h)
	local s = g_decollage_auto
	if s.message == nil or update_get_logic_tick() > s.fin_message then return end
	local c = s.erreur and color8(255, 60, 60, 255) or color8(110, 255, 140, 255)
	update_ui_text(4, screen_h - 14, s.message, screen_w - 8, 0, c, 0)
end

-- enveloppe transparente : memes parametres, memes retours ; une erreur ici ne casse pas l'ecran (pcall)
function decollage_auto_update(...)
	local retours = table.pack(g_decollage_auto_update_origine(...))
	local screen_w, screen_h = ...
	pcall(decollage_auto_observer)
	pcall(decollage_auto_dessiner, screen_w, screen_h)
	return table.unpack(retours, 1, retours.n)
end

function decollage_auto_begin_load(...)
	local retours = table.pack(g_decollage_auto_begin_load_origine(...))

	local nom = nil
	if type(begin_get_screen_name) == "function" then
		local ok, valeur = pcall(begin_get_screen_name)
		if ok then nom = valeur end
	end

	-- un seul ecran (le central) pour ne donner l'ordre qu'une fois
	if nom == "screen_veh_m" and type(update) == "function" and g_decollage_auto_update_origine == nil then
		g_decollage_auto_update_origine = update
		update = decollage_auto_update
	end

	return table.unpack(retours, 1, retours.n)
end

if type(begin_load) == "function" and g_decollage_auto_begin_load_origine == nil then
	g_decollage_auto_begin_load_origine = begin_load
	begin_load = decollage_auto_begin_load
end
