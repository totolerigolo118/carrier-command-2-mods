-- ============================================================================
--  VITESSE DE SIMULATION  --  affiche "SIM x1.00" en bas a gauche des ecrans de
--  controle des vehicules (screen_veh_l / screen_veh_m / screen_veh_r), a droite
--  de l'horloge de jeu. C'est le temps de jeu (pas de simulation, 30 par seconde)
--  divise par le temps reel, calcule sur des fenetres de 10 secondes :
--  x1.00 = vitesse normale ; x2.00 = simulation 2 fois plus vite ; en dessous de
--  la vitesse voulue = la machine ne suit pas (le jeu ralentit).
--
--  Ne change rien au jeu : il lit deux horloges et dessine du texte. Chaque appel
--  est sous pcall, et ce fichier est SEPARE de l'horloge et du journal : une
--  erreur ici ne peut pas faire disparaitre l'horloge.
-- ============================================================================

g_vsim = { tick0 = nil, reel0 = nil, vitesse = nil }

function vsim_observer()
	if type(update_get_time_since_epoch) ~= "function" or type(update_get_logic_tick) ~= "function" then
		return
	end
	local tick = update_get_logic_tick()
	local reel = update_get_time_since_epoch()
	local v = g_vsim
	if v.tick0 == nil or tick < v.tick0 or reel < v.reel0 then
		v.tick0, v.reel0 = tick, reel          -- premiere mesure, ou retour en arriere (nouvelle partie)
		return
	end
	local d = reel - v.reel0
	if d >= 10 then
		v.vitesse = ((tick - v.tick0) / 30) / d
		v.tick0, v.reel0 = tick, reel
	end
end

function vsim_dessiner(screen_w, screen_h)
	local texte
	if g_vsim.vitesse == nil then
		texte = "SIM ..."
	else
		texte = string.format("SIM x%.2f", g_vsim.vitesse)
	end
	-- a droite de l'horloge : sa largeur maximale est celle de ce modele de texte
	local cw = update_ui_get_text_size("TEMPS DE JEU  8:88:88.8", 1000, 0)
	local tw, th = update_ui_get_text_size(texte, 1000, 0)
	local w, h = tw + 8, th + 4
	local x, y = 4 + cw + 16, screen_h - 4 - h
	if x + w > screen_w - 4 then return end    -- pas la place : on ne dessine rien plutot que de deborder
	update_ui_rectangle(x, y, w, h, color8(0, 0, 0, 210))
	update_ui_text(x + 4, y + 2, texte, w - 8, 0, color8(120, 255, 160, 255), 0)
end

-- enveloppe transparente : memes parametres, memes retours
function vsim_update(...)
	local retours = table.pack(g_vsim_update_origine(...))
	local screen_w, screen_h = ...
	pcall(vsim_observer)
	pcall(vsim_dessiner, screen_w, screen_h)
	return table.unpack(retours, 1, retours.n)
end

function vsim_begin_load(...)
	local retours = table.pack(g_vsim_begin_load_origine(...))

	local nom = nil
	if type(begin_get_screen_name) == "function" then
		local ok, valeur = pcall(begin_get_screen_name)
		if ok then nom = valeur end
	end

	if (nom == "screen_veh_l" or nom == "screen_veh_m" or nom == "screen_veh_r")
		and type(update) == "function"
		and g_vsim_update_origine == nil then
		g_vsim_update_origine = update
		update = vsim_update
	end

	return table.unpack(retours, 1, retours.n)
end

if type(begin_load) == "function" and g_vsim_begin_load_origine == nil then
	g_vsim_begin_load_origine = begin_load
	begin_load = vsim_begin_load
end
