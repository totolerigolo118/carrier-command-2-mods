-- ============================================================================
--  LANDING LOG  --  automatically times the returns of planes
--  and helicopters to this carrier, and displays the result at the bottom left
--  of the vehicle control screens (screen_veh_l / _m / _r), above the
--  game clock. Changes nothing in the game: it only reads states.
--
--  For each aircraft: the time it enters the queue, the time it
--  is given the runway, the time it touches the deck and the time it is stowed in the hangar (game
--  time, 30 ticks per second: lag does not distort anything). A "return"
--  starts when an aircraft enters the queue while nothing is in progress,
--  and ends when all of them are stowed. The result stays displayed until the
--  next return.
-- ============================================================================

g_journal = { appareils = {}, ordre = {}, debut = nil, fini = false, dernier_tick = nil, trou = 0 }  -- appareils = aircraft, ordre = order of arrival, debut = start, fini = finished, trou = longest gap between two frames

local FILE, PISTE, PONT, RANGE, VOL = 5, 1, 6, 4, 0  -- get_dock_state() values: FILE = queue, PISTE = runway, PONT = deck, RANGE = stowed in the hangar, VOL = flying

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
		a.ratees = a.ratees + 1                     -- missed approach: back to the queue
	elseif etat == VOL then
		a.abandon = true                            -- recall cancelled, or no room left
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

	-- new aircraft returning to this ship
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
					a.abandon, a.etat = false, etat         -- recalled again during the same return
				end
			end
		end
	end

	-- aircraft already being tracked
	if j.debut ~= nil and not j.fini then
		local reste = 0
		for _, a in ipairs(j.ordre) do
			if a.range == nil and not a.abandon then
				local v = update_get_map_vehicle_by_id(a.id)
				if v:get() then
					journal_suivre(a, v:get_dock_state(), t)
				else
					a.abandon = true                    -- aircraft destroyed
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
	local genres = { avion = 0, helico = 0 }  -- keys: avion = plane, helico = helicopter
	local pistes, approches, ponts, ratees, fin = {}, {}, {}, 0, nil
	for k, a in ipairs(j.ordre) do
		genres[a.genre] = genres[a.genre] + 1
		local nom = (a.genre == "avion") and "plane " or "copter"
		local etat = a.abandon and " abandon" or ""
		-- short (< 36 characters): anything longer wraps onto a new line on the game screen (observed in game)
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
	local quoi = compte(genres.avion, "plane")
	if genres.helico > 0 then quoi = quoi .. " + " .. compte(genres.helico, "copter") end
	if j.fini then
		table.insert(lignes, string.format("DONE in %s : %s", journal_duree(fin and fin - j.debut), quoi))
	else
		table.insert(lignes, string.format("ONGOING %s : %s", journal_duree(j.dernier_tick - j.debut), quoi))
	end
	table.insert(lignes, string.format("runway every %s  missed %d", journal_duree(moyenne(ecarts)), ratees))
	table.insert(lignes, string.format("approach %s  deck>hangar %s", journal_duree(moyenne(approches)),
		journal_duree(moyenne(ponts))))
	if j.trou > 150 then
		table.insert(lignes, string.format("! screen frozen %s : unreliable", journal_duree(j.trou)))
	end
	return lignes
end

function journal_dessiner(screen_w, screen_h)
	if g_journal.debut == nil then return end
	local lignes = journal_resume()
	table.insert(lignes, 1, "         runway   deck hangar")
	table.insert(lignes, 1, "LANDING LOG (game time)")
	local _, hh = update_ui_get_text_size("GAME TIME", 1000, 0)
	local w = 0
	local th = hh
	for _, l in ipairs(lignes) do
		local tw, h = update_ui_get_text_size(l, 1000, 0)
		if tw > w then w = tw end
		th = h
	end
	w = math.min(w + 8, screen_w - 8)
	local h = #lignes * (th + 1) + 4
	local x, y = 4, screen_h - 4 - (hh + 4) - 2 - h          -- just above the clock
	update_ui_rectangle(x, y, w, h, color8(0, 0, 0, 210))
	for k, l in ipairs(lignes) do
		local couleur = (k == 1) and color8(255, 200, 80, 255) or color8(255, 255, 255, 255)
		update_ui_text(x + 4, y + 2 + (k - 1) * (th + 1), l, w - 8, 0, couleur, 0)
	end
end

-- transparent wrapper: same parameters, same return values; an error in the
-- log cannot break the screen (pcall)
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
