-- ============================================================================
--  JOURNAL DES SORTIES  --  chronometre tout seul les decollages d'avions et
--  d'helicos depuis ce porte-avions et les affiche en HAUT A DROITE des ecrans de
--  controle des vehicules (screen_veh_l / screen_veh_m / screen_veh_r). Quand tous
--  les appareils de la sortie sont en l'air, la derniere ligne passe au vert :
--  "4/4 EN L'AIR : FINI en 2:15".
--
--  Ne change rien au jeu : il ne fait que lire des etats (comme le journal des
--  atterrissages). Temps de jeu (30 tops par seconde). Une sortie commence quand un
--  appareil recoit l'ordre de decoller alors qu'aucune sortie n'est en cours, et se
--  termine quand tous les appareils ordonnes pendant ce temps sont en l'air. Le
--  resultat reste affiche 2 minutes de jeu apres la fin, puis disparait.
--  Fichier SEPARE de l'horloge et du journal : une erreur ici ne les touche pas.
-- ============================================================================

g_sorties = { appareils = {}, ordre = {}, debut = nil, fini = false, fin = nil, dernier_tick = nil }

local DEMANDE, SORTIE, ATTENTE, HANGAR, VOL = 2, 3, 7, 4, 0
local AFFICHAGE_APRES_FIN = 3600        -- 2 minutes de jeu

function sorties_duree(ticks)
	if ticks == nil then return "--:--" end
	local s = math.floor(ticks / 30 + 0.5)
	return string.format("%d:%02d", math.floor(s / 60), s % 60)
end

function sorties_genre(vehicule)
	local d = vehicule:get_definition_index()
	if d == e_game_object_type.chassis_air_wing_light or d == e_game_object_type.chassis_air_wing_heavy then
		return "avion"
	elseif d == e_game_object_type.chassis_air_rotor_light or d == e_game_object_type.chassis_air_rotor_heavy then
		return "helico"
	end
	return nil
end

function sorties_nouveau(id, genre, t)
	local s = g_sorties
	if s.debut == nil or s.fini then
		s.appareils, s.ordre, s.debut, s.fini, s.fin = {}, {}, t, false, nil
	end
	local a = { id = id, genre = genre, demande = t }
	s.appareils[id] = a
	table.insert(s.ordre, a)
end

function sorties_observer()
	local s = g_sorties
	local t = update_get_logic_tick()
	s.dernier_tick = t

	local bateau = update_get_screen_vehicle()
	if not bateau:get() then return end
	local id_bateau = bateau:get_id()

	-- nouveaux appareils : ordre de sortie donne. Comme l'ecran de propulsion du jeu (screen_propulsion.lua),
	-- un appareil en sortie est RATTACHE a son porte-avions (get_attached_parent_id) ; par prudence on accepte
	-- aussi la parente d'accostage. `inconnus` compte les appareils en sortie qu'aucune des deux ne relie a ce bateau.
	local inconnus = 0
	for i = 0, update_get_map_vehicle_count() - 1 do
		local v = update_get_map_vehicle_by_index(i)
		if v:get() then
			local etat = v:get_dock_state()
			if etat == DEMANDE or etat == SORTIE or etat == ATTENTE then
				local ok1, rattache = pcall(function() return v:get_attached_parent_id() end)
				local ok2, accoste = pcall(function() return v:get_dock_parent_id() end)
				local genre = sorties_genre(v)
				if genre then
					if (ok1 and rattache == id_bateau) or (ok2 and accoste == id_bateau) then
						local id = v:get_id()
						local a = (not s.fini) and s.appareils[id] or nil
						if a == nil then
							sorties_nouveau(id, genre, t)
						elseif a.abandon and a.vol == nil then
							a.abandon = false            -- ordonne de nouveau pendant la meme sortie
						end
					elseif v:get_team() == update_get_screen_team_id() then
						inconnus = inconnus + 1          -- un des notres, en sortie, mais relie a aucun bateau connu
					end
				end
			end
		end
	end
	s.inconnus = inconnus

	-- appareils deja suivis
	if s.debut ~= nil and not s.fini then
		local reste = 0
		for _, a in ipairs(s.ordre) do
			if a.vol == nil and not a.abandon then
				local v = update_get_map_vehicle_by_id(a.id)
				if v:get() then
					local etat = v:get_dock_state()
					if etat == VOL then
						a.vol = t
					elseif etat == SORTIE and a.sortie == nil then
						a.sortie = t
					elseif etat == HANGAR then
						a.abandon = true                 -- ordre annule : il est reste ou retourne au hangar
					end
				else
					a.abandon = true                     -- appareil detruit
				end
				if a.vol == nil and not a.abandon then reste = reste + 1 end
			end
		end
		if reste == 0 and #s.ordre > 0 then
			s.fini, s.fin = true, t
		end
	end
end

function sorties_lignes()
	local s = g_sorties
	local blanc, orange, vert = color8(255, 255, 255, 255), color8(255, 200, 80, 255), color8(110, 255, 140, 255)
	local lignes = {}
	table.insert(lignes, { "SORTIES (temps de jeu)", orange })
	table.insert(lignes, { "          ordre  en l'air", blanc })
	local en_vol, total, vols = 0, 0, {}
	for k, a in ipairs(s.ordre) do
		total = total + 1
		if a.vol then en_vol = en_vol + 1; table.insert(vols, a.vol) end
		local nom = (a.genre == "avion") and "avion " or "helico"
		table.insert(lignes, { string.format("%d %s   %5s   %5s%s", k, nom,
			sorties_duree(a.demande - s.debut), sorties_duree(a.vol and a.vol - s.debut),
			a.abandon and " abandon" or ""), blanc })
	end
	table.sort(vols)
	if s.fini then
		table.insert(lignes, { string.format("%d/%d EN L'AIR : FINI en %s", en_vol, total, sorties_duree(s.fin - s.debut)), vert })
		if #vols >= 2 then
			table.insert(lignes, { string.format("ecart moyen entre decollages %s",
				sorties_duree((vols[#vols] - vols[1]) / (#vols - 1))), vert })
		end
	else
		table.insert(lignes, { string.format("%d/%d EN L'AIR  (en cours %s)", en_vol, total,
			sorties_duree((s.dernier_tick or s.debut) - s.debut)), orange })
	end
	return lignes
end

function sorties_dessiner(screen_w, screen_h)
	local s = g_sorties
	if s.debut == nil then
		-- message de secours : des appareils sont en sortie mais aucun n'est relie a ce bateau
		if (s.inconnus or 0) > 0 then
			local texte = string.format("SORTIES ? %d en sortie, non reconnu(s)", s.inconnus)
			local tw, th = update_ui_get_text_size(texte, 1000, 0)
			local w = math.min(tw + 8, screen_w - 8)
			local x = screen_w - 4 - w
			update_ui_rectangle(x, 4, w, th + 4, color8(0, 0, 0, 210))
			update_ui_text(x + 4, 6, texte, w - 8, 0, color8(255, 120, 120, 255), 0)
		end
		return
	end
	if s.fini and s.fin ~= nil and s.dernier_tick ~= nil and s.dernier_tick - s.fin > AFFICHAGE_APRES_FIN then return end

	local lignes = sorties_lignes()
	local w, th = 0, 0
	for _, l in ipairs(lignes) do
		local tw, h = update_ui_get_text_size(l[1], 1000, 0)
		if tw > w then w = tw end
		th = h
	end
	w = math.min(w + 8, screen_w - 8)
	local h = #lignes * (th + 1) + 4
	local x, y = screen_w - 4 - w, 4
	update_ui_rectangle(x, y, w, h, color8(0, 0, 0, 210))
	for k, l in ipairs(lignes) do
		update_ui_text(x + 4, y + 2 + (k - 1) * (th + 1), l[1], w - 8, 0, l[2], 0)
	end
end

-- enveloppe transparente : memes parametres, memes retours ; une erreur ici ne casse pas l'ecran (pcall)
function sorties_update(...)
	local retours = table.pack(g_sorties_update_origine(...))
	local screen_w, screen_h = ...
	pcall(sorties_observer)
	pcall(sorties_dessiner, screen_w, screen_h)
	return table.unpack(retours, 1, retours.n)
end

function sorties_begin_load(...)
	local retours = table.pack(g_sorties_begin_load_origine(...))

	local nom = nil
	if type(begin_get_screen_name) == "function" then
		local ok, valeur = pcall(begin_get_screen_name)
		if ok then nom = valeur end
	end

	if (nom == "screen_veh_l" or nom == "screen_veh_m" or nom == "screen_veh_r")
		and type(update) == "function"
		and g_sorties_update_origine == nil then
		g_sorties_update_origine = update
		update = sorties_update
	end

	return table.unpack(retours, 1, retours.n)
end

if type(begin_load) == "function" and g_sorties_begin_load_origine == nil then
	g_sorties_begin_load_origine = begin_load
	begin_load = sorties_begin_load
end
