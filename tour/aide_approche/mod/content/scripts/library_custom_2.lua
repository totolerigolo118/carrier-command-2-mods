-- ============================================================================
--  AIDE A L'APPROCHE  --  des "portes" rectangulaires le long de la trajectoire
--  d'approche derriere ton porte-avions, dans le HUD de l'avion que tu pilotes.
--
--  - Portes : 6 rectangles (a 100, 200, 300, 450, 600 et 800 m derriere le point de
--    toucher), poses sur la pente de 0,14 (~8 degres) que vise l'IA. Cyan = simple repere.
--  - La PROCHAINE porte devant toi est plus grosse et prend la couleur du verdict :
--      VERT   = dans l'axe, a la bonne hauteur, vitesse relative <= 30 m/s
--      ORANGE = un des trois est hors tolerance (le texte en haut dit lequel)
--      ROUGE  = trop vite (> 36 m/s par rapport au navire)
--  - Un petit texte en haut au centre : ecart lateral, ecart de hauteur, vitesse relative.
--
--  Ne change RIEN au jeu : il ne fait que lire des positions et dessiner dans le HUD
--  (aucun fichier, aucun reseau, aucune ecriture en memoire, pas besoin de CC2X).
--  Emplacement library_custom_2.lua (libres chez toi : 1, 3-9 sont pris par d'autres mods).
--  Une erreur ici est avalee (pcall) : au pire les portes ne s'affichent pas.
--
--  REGLAGES : tout est dans le bloc "reglages" juste en dessous.
-- ============================================================================

-- reglages (repere du navire : z vers l'avant, y vers le haut, metres)
local AP = {
	z_toucher = -50,            -- ou tu veux toucher le pont (la piste va de -68 a +82)
	y_pont = 20,                -- hauteur du pont au-dessus de l'origine du navire
	decalage_haut = 6,          -- remonte toutes les portes (et la hauteur visee) de ce nombre de metres
	pente = 0.14,               -- metres de hauteur par metre de distance (celle de l'IA)
	portes = { 100, 200, 300, 450, 600, 800 },   -- distances derriere le point de toucher
	largeur = 30,               -- largeur d'une porte
	hauteur = 12,               -- hauteur d'une porte
	portee = 1500,              -- les portes n'apparaissent que si le navire est a moins de ca
	tol_lateral = 12,           -- vert si l'ecart lateral est sous cette valeur
	tol_hauteur = 10,           -- idem pour la hauteur
	vitesse_ok = 30,            -- vert si la vitesse relative est sous cette valeur
	vitesse_rouge = 36,         -- rouge au dela
}

-- essaie plusieurs noms de methode (le jeu n'en offre pas les memes selon le contexte) ; renvoie le premier qui repond
local function ap_essai(objet, ...)
	for _, nom in ipairs({ ... }) do
		local f = objet[nom]
		if type(f) == "function" then
			local ok, r = pcall(f, objet)
			if ok and r ~= nil then return r end
		end
	end
	return nil
end

local function ap_equipe(v)
	local e = ap_essai(v, "get_team_id", "get_team")
	return e
end

-- navire de ton equipe le plus proche
local function ap_navire_proche(avion)
	local pos = avion:get_position()
	local equipe = ap_equipe(avion)
	if equipe == nil then equipe = update_get_screen_team_id() end
	local meilleur, meilleure_d = nil, nil
	for i = 0, update_get_map_vehicle_count() - 1 do
		local v = update_get_map_vehicle_by_index(i)
		if v:get() and v:get_definition_index() == e_game_object_type.chassis_carrier and ap_equipe(v) == equipe then
			local p = v:get_position()
			local dx, dz = p:x() - pos:x(), p:z() - pos:z()
			local d = math.sqrt(dx * dx + dz * dz)
			if meilleure_d == nil or d < meilleure_d then
				meilleur, meilleure_d = v, d
			end
		end
	end
	return meilleur, meilleure_d
end

local function ap_dessiner(screen_w, screen_h, avion)
	-- avion detruit : l'objet existe mais est vide, et lui poser une question fait planter le jeu (pcall n'y peut rien)
	if avion == nil or avion:get() == nil then return end
	local def = avion:get_definition_index()
	if def ~= e_game_object_type.chassis_air_wing_light and def ~= e_game_object_type.chassis_air_wing_heavy
		and def ~= e_game_object_type.chassis_air_rotor_light and def ~= e_game_object_type.chassis_air_rotor_heavy then
		return
	end
	-- seulement quand c'est toi qui pilotes (pas l'autopilote)
	if avion:get_control_mode() ~= "manual" or not avion:get_is_controlling_peer() then return end

	local navire, dist = ap_navire_proche(avion)
	if navire == nil or dist > AP.portee then return end

	local np = navire:get_position()
	-- cap du navire : un vehicule de la carte donne get_direction() (vec2 x,z) ; get_forward() n'existe que sur le vehicule de l'ecran
	local fx, fz
	local nd = ap_essai(navire, "get_direction")
	if nd ~= nil then
		fx, fz = nd:x(), nd:y()
	else
		local nf = navire:get_forward()
		fx, fz = nf:x(), nf:z()
	end
	local n = math.sqrt(fx * fx + fz * fz)
	if n < 0.001 then return end
	fx, fz = fx / n, fz / n
	local sx, sz = fz, -fx                 -- "a droite" du navire (z devant, x a droite)

	local function monde(lat, lon, haut)  -- repere du navire -> monde
		return np:x() + fx * lon + sx * lat, np:y() + haut, np:z() + fz * lon + sz * lat
	end

	-- position et vitesse de l'avion dans le repere du navire
	local ap = avion:get_position()
	local rx, rz = ap:x() - np:x(), ap:z() - np:z()
	local lon = rx * fx + rz * fz
	local lat = rx * sx + rz * sz
	local hauteur = ap:y() - np:y()
	local va, vn = avion:get_linear_velocity(), navire:get_linear_velocity()
	local rvx, rvy, rvz = va:x() - vn:x(), va:y() - vn:y(), va:z() - vn:z()
	local vrel = math.sqrt(rvx * rvx + rvy * rvy + rvz * rvz)

	-- hauteur ideale a cette distance : la pente, plate au dela du point de toucher
	local derriere = AP.z_toucher - lon
	if derriere < 0 then derriere = 0 end
	local ecart_h = hauteur - (AP.y_pont + AP.decalage_haut + AP.pente * derriere)

	if lon > AP.z_toucher + 160 then return end   -- deja au-dessus / apres le pont : plus d'aide

	local cyan = color8(0, 220, 255, 150)
	local vert = color8(60, 255, 90, 255)
	local orange = color8(255, 170, 40, 255)
	local rouge = color8(255, 60, 60, 255)

	local verdict, texte_pb = vert, ""
	if math.abs(lat) > AP.tol_lateral then verdict, texte_pb = orange, texte_pb .. " AXIS" end
	if math.abs(ecart_h) > AP.tol_hauteur then verdict, texte_pb = orange, texte_pb .. " HEIGHT" end
	if vrel > AP.vitesse_ok then verdict, texte_pb = orange, texte_pb .. " SPEED" end
	if vrel > AP.vitesse_rouge then verdict = rouge end

	local cam = update_get_camera_position()
	local cf = update_get_camera_forward()

	-- porte a dessiner : la plus proche encore devant l'avion ; on les dessine toutes
	local prochaine = nil
	for k = #AP.portes, 1, -1 do
		if lon < AP.z_toucher - AP.portes[k] then prochaine = k end
	end

	for k, d in ipairs(AP.portes) do
		local centre_lon = AP.z_toucher - d
		local centre_h = AP.y_pont + AP.decalage_haut + AP.pente * d
		local grosse = (k == prochaine)
		local l, h = AP.largeur, AP.hauteur
		local coins = {
			{ -l / 2, centre_h - h / 2 }, { l / 2, centre_h - h / 2 },
			{ l / 2, centre_h + h / 2 }, { -l / 2, centre_h + h / 2 },
		}
		local pts, ok = {}, true
		for i, c in ipairs(coins) do
			local wx, wy, wz = monde(c[1], centre_lon, c[2])
			-- derriere la camera : on saute la porte
			local dot = (wx - cam:x()) * cf:x() + (wy - cam:y()) * cf:y() + (wz - cam:z()) * cf:z()
			if dot <= 1 then ok = false break end
			local s, bloque = update_world_to_screen(vec3(wx, wy, wz))
			if bloque then ok = false break end
			pts[i] = s
		end
		if ok then
			local couleur = grosse and verdict or cyan
			for i = 1, 4 do
				local a, b = pts[i], pts[i % 4 + 1]
				update_ui_line(a:x(), a:y(), b:x(), b:y(), couleur)
				if grosse then
					-- double trait : plus visible
					update_ui_line(a:x() + 1, a:y(), b:x() + 1, b:y(), couleur)
					update_ui_line(a:x(), a:y() + 1, b:x(), b:y() + 1, couleur)
				end
			end
		end
	end

	-- petit texte en haut au centre
	local texte = string.format("APPROACH  LAT %+d  HEIGHT %+d  SPD %d%s",
		math.floor(lat + 0.5), math.floor(ecart_h + 0.5), math.floor(vrel + 0.5), texte_pb)
	local tw, th = update_ui_get_text_size(texte, 1000, 0)
	local w = math.min(tw + 8, screen_w - 8)
	local x = math.floor((screen_w - w) / 2)
	update_ui_rectangle(x, 4, w, th + 4, color8(0, 0, 0, 180))
	update_ui_text(x + 4, 6, texte, w - 8, 0, verdict, 0)
end

-- enveloppe transparente : memes parametres, memes retours ; une erreur ici ne casse pas l'ecran (pcall)
function aide_approche_update(...)
	local retours = table.pack(g_aide_approche_update_origine(...))
	local screen_w, screen_h = ...
	local avion = select(6, ...)
	if avion ~= nil and avion:get() then
		local ok, erreur = pcall(ap_dessiner, screen_w, screen_h, avion)
		if not ok then
			-- on montre l'erreur a l'ecran (petit texte rouge en bas) au lieu de l'avaler en silence
			pcall(function()
				local texte = "APPROACH ERR: " .. tostring(erreur)
				update_ui_text(4, screen_h - 14, texte, screen_w - 8, 0, color8(255, 60, 60, 255), 0)
			end)
		end
	end
	return table.unpack(retours, 1, retours.n)
end

function aide_approche_begin_load(...)
	local retours = table.pack(g_aide_approche_begin_load_origine(...))

	-- on ne s'accroche qu'a l'ecran du HUD des vehicules (celui qui definit render_flight_hud)
	if type(render_flight_hud) == "function"
		and type(update) == "function"
		and g_aide_approche_update_origine == nil then
		g_aide_approche_update_origine = update
		update = aide_approche_update
	end

	return table.unpack(retours, 1, retours.n)
end

if type(begin_load) == "function" and g_aide_approche_begin_load_origine == nil then
	g_aide_approche_begin_load_origine = begin_load
	begin_load = aide_approche_begin_load
end
