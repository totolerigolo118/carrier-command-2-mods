-- ============================================================================
--  SQUADRON SPEED  --  ECO / NORMAL / FLANK bar at the bottom right of the
--  vehicle control screens. A click chooses the cruise speed of
--  all the AI-piloted planes of the team:
--    ECO    = original game behaviour (about 50 % power)
--    NORMAL = about 80 % power
--    FLANK  = full throttle
--
--  The choice goes through cc2_vitesse(team [, mode]), a function added to the
--  game executable by the "vitesse_escadrille" module (without it, the bar is not
--  displayed). The executable keeps the last mode from one game to the next;
--  all screens read the same mode. First time: NORMAL.
--  Study: part 05 of the notes (cc2-patchs workshop).
-- ============================================================================

g_vit_ecrans = {
	screen_veh_l = true, screen_veh_m = true, screen_veh_r = true, screen_veh_ll = true,
	tacops_left_control = true, tacops_middle_control = true, tacops_right_control = true,
}
g_vit_noms = { "ECO", "NORMAL", "FLANK" }
g_vit_couleurs = {
	color8(16, 255, 127, 255),     -- ECO: green
	color8(16, 255, 255, 255),     -- NORMAL: cyan
	color8(255, 176, 32, 255),     -- FLANK: orange
}
g_vit_mode_defaut = 2

g_vit = { visible = false, mode = 0, zones = {}, px = -1, py = -1, survol = false, appui = false }

-- current mode of this screen's team (0 if the patch code is missing); first call: NORMAL
function vit_lire()
	if type(cc2_vitesse) ~= "function" then return 0 end
	local equipe = update_get_screen_team_id()
	local mode = cc2_vitesse(equipe)
	if mode == 0 then
		mode = cc2_vitesse(equipe, g_vit_mode_defaut)
	end
	return mode
end

function vit_choisir(mode)
	if type(cc2_vitesse) ~= "function" then return end
	g_vit.mode = cc2_vitesse(update_get_screen_team_id(), mode)
end

-- the screen shows the map (not a replacement-mod sub-window nor a vehicle view)
function vit_carte_affichee(screen_w, screen_h)
	if screen_w < 200 or screen_h < 200 then return false end
	if type(g_screen_index) == "number" and g_screen_index ~= 0 then return false end
	if type(g_viewing_vehicle_id) == "number" and g_viewing_vehicle_id > 0 then return false end
	return true
end

function vit_dans(zone, x, y)
	return x >= zone[1] and x < zone[1] + zone[3] and y >= zone[2] and y < zone[2] + zone[4]
end

function vit_dessiner(screen_w, screen_h)
	g_vit.visible = false
	if not vit_carte_affichee(screen_w, screen_h) then return end
	local mode = vit_lire()
	if mode < 1 or mode > 3 then return end
	g_vit.mode = mode

	-- last line of the screen, on the right (the clock is on the left, the map scale just above)
	local _, th = update_ui_get_text_size("NORMAL", 200, 0)
	local h = th + 3
	local y = screen_h - h - 2
	local x = screen_w - 3
	for i = 3, 1, -1 do
		local tw = update_ui_get_text_size(g_vit_noms[i], 200, 0)
		local w = tw + 8
		x = x - w
		g_vit.zones[i] = { x, y, w, h }
		x = x - 2
	end
	local gauche = x - 10
	update_ui_rectangle(gauche, y - 2, screen_w - gauche, h + 4, color8(0, 0, 0, 210))

	-- small plane icon
	local ix, iy = gauche + 2, y + math.floor((h - 7) / 2)
	local gris = color8(160, 200, 200, 255)
	update_ui_rectangle(ix + 3, iy, 1, 7, gris)
	update_ui_rectangle(ix, iy + 2, 7, 2, gris)
	update_ui_rectangle(ix + 2, iy + 6, 3, 1, gris)

	for i = 1, 3 do
		local z = g_vit.zones[i]
		local actif = (i == mode)
		local survol = g_vit.survol and vit_dans(z, g_vit.px, g_vit.py)
		if actif then
			update_ui_rectangle(z[1], z[2], z[3], z[4], g_vit_couleurs[i])
		else
			update_ui_rectangle(z[1], z[2], z[3], z[4], color8(4, 12, 12, 255))
			update_ui_rectangle_outline(z[1], z[2], z[3], z[4], survol and g_vit_couleurs[i] or color8(63, 63, 63, 255))
		end
		update_ui_text(z[1] + 4, z[2] + 2, g_vit_noms[i], z[3] - 4, 0,
			actif and color8(0, 0, 0, 255) or color8(190, 204, 204, 255), 0)
	end
	g_vit.visible = true
end

-- transparent wrappers: same parameters, same return values; an error in the
-- bar cannot break the screen (pcall)
function vit_update(...)
	local retours = table.pack(g_vit_update_origine(...))
	local screen_w, screen_h = ...
	local ok = pcall(vit_dessiner, screen_w, screen_h)
	if not ok then g_vit.visible = false end
	return table.unpack(retours, 1, retours.n)
end

function vit_input_pointer(is_hovered, x, y, ...)
	g_vit.survol, g_vit.px, g_vit.py = is_hovered, x, y
	return g_vit_input_pointer_origine(is_hovered, x, y, ...)
end

function vit_input_event(event, action, ...)
	if event == e_input.pointer_1 then
		if action == e_input_action.press and g_vit.visible and g_vit.survol then
			for i = 1, 3 do
				local z = g_vit.zones[i]
				if z and vit_dans(z, g_vit.px, g_vit.py) then
					pcall(vit_choisir, i)
					g_vit.appui = true
					return
				end
			end
		elseif action == e_input_action.release and g_vit.appui then
			g_vit.appui = false
			return
		end
	end
	return g_vit_input_event_origine(event, action, ...)
end

function vit_begin_load(...)
	local retours = table.pack(g_vit_begin_load_origine(...))

	local nom = nil
	if type(begin_get_screen_name) == "function" then
		local ok, valeur = pcall(begin_get_screen_name)
		if ok then nom = valeur end
	end

	if nom and g_vit_ecrans[nom] and g_vit_update_origine == nil
		and type(update) == "function" and type(input_event) == "function"
		and type(input_pointer) == "function" then
		g_vit_update_origine = update
		update = vit_update
		g_vit_input_pointer_origine = input_pointer
		input_pointer = vit_input_pointer
		g_vit_input_event_origine = input_event
		input_event = vit_input_event
	end

	return table.unpack(retours, 1, retours.n)
end

if type(begin_load) == "function" and g_vit_begin_load_origine == nil then
	g_vit_begin_load_origine = begin_load
	begin_load = vit_begin_load
end
