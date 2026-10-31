-- ============================================================================
--  GAME CLOCK  --  displays the game time at the bottom left of the vehicle
--  control screens (screen_veh_l / screen_veh_m / screen_veh_r).
--  No other screen is touched.
--
--  This is the game's internal clock (30 ticks per second of game time): if the game
--  lags, the clock slows down with it, so lag does not distort a measurement.
--  Read the clock at the start and at the end; the difference = duration in game time.
-- ============================================================================

function horloge_format(ticks)
	local s = ticks / 30
	local h = math.floor(s / 3600)
	local m = math.floor((s - 3600 * h) / 60)
	local r = s - 3600 * h - 60 * m
	if h > 0 then
		return string.format("%d:%02d:%04.1f", h, m, r)
	end
	return string.format("%d:%04.1f", m, r)
end

function horloge_dessiner(screen_w, screen_h)
	local texte = "GAME TIME  " .. horloge_format(update_get_logic_tick())
	local tw, th = update_ui_get_text_size(texte, 1000, 0)
	local w, h = math.min(tw + 8, screen_w - 8), th + 4
	local x, y = 4, screen_h - 4 - h
	update_ui_rectangle(x, y, w, h, color8(0, 0, 0, 210))
	update_ui_text(x + 4, y + 2, texte, w - 8, 0, color8(255, 255, 255, 255), 0)
end

-- transparent wrapper: same parameters, same return values; an error in the
-- clock cannot break the screen (pcall)
function horloge_update(...)
	local retours = table.pack(g_horloge_update_origine(...))
	local screen_w, screen_h = ...
	pcall(horloge_dessiner, screen_w, screen_h)
	return table.unpack(retours, 1, retours.n)
end

function horloge_begin_load(...)
	local retours = table.pack(g_horloge_begin_load_origine(...))

	local nom = nil
	if type(begin_get_screen_name) == "function" then
		local ok, valeur = pcall(begin_get_screen_name)
		if ok then nom = valeur end
	end

	if (nom == "screen_veh_l" or nom == "screen_veh_m" or nom == "screen_veh_r")
		and type(update) == "function"
		and g_horloge_update_origine == nil then
		g_horloge_update_origine = update
		update = horloge_update
	end

	return table.unpack(retours, 1, retours.n)
end

if type(begin_load) == "function" and g_horloge_begin_load_origine == nil then
	g_horloge_begin_load_origine = begin_load
	begin_load = horloge_begin_load
end
