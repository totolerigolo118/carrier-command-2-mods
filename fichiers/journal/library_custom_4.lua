-- ============================================================================
--  JOURNAL DES ATTERRISSAGES  --  chronometre tout seul les retours d'avions
--  et d'helicos sur ce porte-avions, et affiche le resultat en bas a gauche
--  des ecrans de controle des vehicules (screen_veh_l / _m / _r), au-dessus de
--  l'horloge de jeu. Ne change rien au jeu : il ne fait que lire des etats.
--
--  Pour chaque appareil : heure ou il entre dans la file d'attente, ou il
--  recoit la piste, ou il touche le pont, ou il est range au hangar (temps de
--  jeu, 30 tops par seconde : le lag du Mac ne fausse rien). Un « retour »
--  commence quand un appareil entre dans la file alors que rien n'est en cours,
--  et se termine quand tous sont ranges. Le resultat reste affiche jusqu'au
--  retour suivant.
-- ============================================================================

g_journal = { appareils = {}, ordre = {}, debut = nil, fini = false, dernier_tick = nil, trou = 0 }

local FILE, PISTE, PONT, RANGE, VOL = 5, 1, 6, 4, 0

function journal_duree(ticks)
	if ticks == nil then return "--:--" end
	local s = math.floor(ticks / 30 + 0.5)
	return string.format("%d:%02d", math.floor(s / 60), s % 60)
end

function journal_genre(vehicule)
	local d = vehicule:get_definition_index()
	if d == e_game_object_type.chassis_air_wing_light or d == e_game_object_type.chassis_air_wing_heavy then
		return "avion"
	elseif d == e_game_object_type.chassis_air_rotor_light or d == e_game_object_type.chassis_air_rotor_heavy then
		return "helico"
	end
	return nil
end

function journal_nouveau(id, genre, t, etat)
	local j = g_journal
	if j.debut == nil or j.fini then
		j.appareils, j.ordre, j.debut, j.fini, j.trou = {}, {}, t, false, 0
	end
	local a = { id = id, genre = genre, file = t, etat = etat, ratees = 0 }
	if etat == PISTE then a.piste = t end
	if etat == PONT then a.pont = t end
	j.appareils[id] = a
	table.insert(j.ordre, a)
end

function journal_suivre(a, etat, t)
	if etat == a.etat then return end
	if etat == PISTE then
		a.piste = t
	elseif etat == PONT then
		a.pont = t
	elseif etat == RANGE then
		a.range = t
	elseif etat == FILE and a.etat == PISTE then
		a.ratees = a.ratees + 1                     -- approche ratee : retour dans la file
	elseif etat == VOL then
		a.abandon = true                            -- rappel annule, ou plus de place
	end
	a.etat = etat
end

function journal_observer()
	local j = g_journal
	local t = update_get_logic_tick()
	if j.dernier_tick ~= nil and j.debut ~= nil and not j.fini and t - j.dernier_tick > j.trou then
		j.trou = t - j.dernier_tick
	end
	j.dernier_tick = t

	local bateau = update_get_screen_vehicle()
	if not bateau:get() then return end
	local id_bateau = bateau:get_id()

	-- nouveaux appareils qui rentrent sur ce bateau
	for i = 0, update_get_map_vehicle_count() - 1 do
		local v = update_get_map_vehicle_by_index(i)
		if v:get() then
			local etat = v:get_dock_state()
			if (etat == FILE or etat == PISTE or etat == PONT) and v:get_dock_parent_id() == id_bateau then
				local id = v:get_id()
				local a = (not j.fini) and j.appareils[id] or nil
				if a == nil then
					local genre = journal_genre(v)
					if genre then journal_nouveau(id, genre, t, etat) end
				elseif a.abandon and a.range == nil then
					a.abandon, a.etat = false, etat         -- rappele de nouveau pendant le meme retour
				end
			end
		end
	end

	-- appareils deja suivis
	if j.debut ~= nil and not j.fini then
		local reste = 0
		for _, a in ipairs(j.ordre) do
			if a.range == nil and not a.abandon then
				local v = update_get_map_vehicle_by_id(a.id)
				if v:get() then
					journal_suivre(a, v:get_dock_state(), t)
				else
					a.abandon = true                    -- appareil detruit
				end
				if a.range == nil and not a.abandon then reste = reste + 1 end
			end
		end
		if reste == 0 and #j.ordre > 0 then j.fini = true end
	end
end

function journal_resume()
	local j = g_journal
	local lignes = {}
	local genres = { avion = 0, helico = 0 }
	local pistes, approches, ponts, ratees, fin = {}, {}, {}, 0, nil
	for k, a in ipairs(j.ordre) do
		genres[a.genre] = genres[a.genre] + 1
		local nom = (a.genre == "avion") and "avion " or "helico"
		local etat = a.abandon and " abandon" or ""
		-- court (< 36 signes) : plus long, le texte passe a la ligne sur l'ecran du jeu (vu le 23/10)
		table.insert(lignes, string.format("%d %s  %5s  %5s  %5s%s", k, nom,
			journal_duree(a.piste and a.piste - j.debut), journal_duree(a.pont and a.pont - j.debut),
			journal_duree(a.range and a.range - j.debut), etat))
		if a.piste then table.insert(pistes, a.piste) end
		if a.piste and a.pont then table.insert(approches, a.pont - a.piste) end
		if a.pont and a.range then table.insert(ponts, a.range - a.pont) end
		if a.range and (fin == nil or a.range > fin) then fin = a.range end
		ratees = ratees + a.ratees
	end
	local function moyenne(liste)
		if #liste == 0 then return nil end
		local s = 0
		for _, x in ipairs(liste) do s = s + x end
		return s / #liste
	end
	table.sort(pistes)
	local ecarts = {}
	for k = 2, #pistes do table.insert(ecarts, pistes[k] - pistes[k - 1]) end

	local function compte(n, mot) return string.format("%d %s%s", n, mot, (n > 1) and "s" or "") end
	local quoi = compte(genres.avion, "avion")
	if genres.helico > 0 then quoi = quoi .. " + " .. compte(genres.helico, "helico") end
	if j.fini then
		table.insert(lignes, string.format("FINI en %s : %s", journal_duree(fin and fin - j.debut), quoi))
	else
		table.insert(lignes, string.format("EN COURS %s : %s", journal_duree(j.dernier_tick - j.debut), quoi))
	end
	table.insert(lignes, string.format("piste toutes les %s  ratees %d", journal_duree(moyenne(ecarts)), ratees))
	table.insert(lignes, string.format("approche %s  pont>hangar %s", journal_duree(moyenne(approches)),
		journal_duree(moyenne(ponts))))
	if j.trou > 150 then
		table.insert(lignes, string.format("! ecran fige %s : mesure douteuse", journal_duree(j.trou)))
	end
	return lignes
end

function journal_dessiner(screen_w, screen_h)
	if g_journal.debut == nil then return end
	local lignes = journal_resume()
	table.insert(lignes, 1, "          piste   pont hangar")
	table.insert(lignes, 1, "JOURNAL ATTERRISSAGES (temps de jeu)")
	local _, hh = update_ui_get_text_size("TEMPS DE JEU", 1000, 0)
	local w = 0
	local th = hh
	for _, l in ipairs(lignes) do
		local tw, h = update_ui_get_text_size(l, 1000, 0)
		if tw > w then w = tw end
		th = h
	end
	w = math.min(w + 8, screen_w - 8)
	local h = #lignes * (th + 1) + 4
	local x, y = 4, screen_h - 4 - (hh + 4) - 2 - h          -- juste au-dessus de l'horloge
	update_ui_rectangle(x, y, w, h, color8(0, 0, 0, 210))
	for k, l in ipairs(lignes) do
		local couleur = (k == 1) and color8(255, 200, 80, 255) or color8(255, 255, 255, 255)
		update_ui_text(x + 4, y + 2 + (k - 1) * (th + 1), l, w - 8, 0, couleur, 0)
	end
end

-- enveloppe transparente : memes parametres, memes retours ; une erreur du
-- journal ne peut pas casser l'ecran (pcall)
function journal_update(...)
	local retours = table.pack(g_journal_update_origine(...))
	local screen_w, screen_h = ...
	pcall(journal_observer)
	pcall(journal_dessiner, screen_w, screen_h)
	return table.unpack(retours, 1, retours.n)
end

function journal_begin_load(...)
	local retours = table.pack(g_journal_begin_load_origine(...))

	local nom = nil
	if type(begin_get_screen_name) == "function" then
		local ok, valeur = pcall(begin_get_screen_name)
		if ok then nom = valeur end
	end

	if (nom == "screen_veh_l" or nom == "screen_veh_m" or nom == "screen_veh_r")
		and type(update) == "function"
		and g_journal_update_origine == nil then
		g_journal_update_origine = update
		update = journal_update
	end

	return table.unpack(retours, 1, retours.n)
end

if type(begin_load) == "function" and g_journal_begin_load_origine == nil then
	g_journal_begin_load_origine = begin_load
	begin_load = journal_begin_load
end
