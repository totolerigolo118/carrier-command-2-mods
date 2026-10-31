-- FAUX screen_vehicle_control.lua (ecrans de bord screen_veh_l / screen_veh_m / screen_veh_r).
-- N'imite QUE ce dont dependent les scripts du depot ; tout ce qui suit est SUPPOSE ou deduit de l'usage qu'en font ces scripts
-- (tour/etudes_modes_carburant/ETUDE.md section 4.1, passation_windows/JOURNAL_tour.md l. 26 : begin() puis begin_load() ligne 1464-1465).

g_viewing_vehicle_id = 0                 -- SUPPOSE : nombre ; 0 = l'ecran ne montre pas de vehicule (lu par le module vitesse du Mac : "> 0" = vue d'un vehicule)
g_selected_vehicle_ui = { confirm_self_destruct = false }   -- SUPPOSE : table d'etat de la boite "etes-vous sur" de l'autodestruction
g_screen_index = 0                       -- SUPPOSE (module vitesse du Mac)
g_vehicule_clique = nil                  -- BANC : id du vehicule clique sur la carte (le faux ecran le dessine)

-- Dans le vrai script (ligne 346) : fenetres STATUS et LOADOUT. Ici : deux fenetres de meme geometrie (LOADOUT a x = 10 + (w - 74 - 25) + 5, y 10, h 84).
function render_selection_vehicle(screen_w, screen_h, vehicle)
	g_ui:begin_window("STATUS##faux", 10, 10, screen_w - 74 - 25, 84, atlas_icons.column_pending, true, 2)
		g_ui:text_basic("STATUS (faux)", color8(255, 255, 255, 255), color8(255, 255, 255, 255))
	g_ui:end_window()
	g_ui:begin_window("LOADOUT##faux", 10 + (screen_w - 74 - 25) + 5, 10, 74, 84, atlas_icons.column_pending, true, 2)
		g_ui:text_basic("LOADOUT (faux)", color8(255, 255, 255, 255), color8(255, 255, 255, 255))
	g_ui:end_window()
	return "selection_ok", vehicle:get_id()
end

function update(screen_w, screen_h, tick_fraction, delta_time)
	if g_vehicule_clique then
		local v = update_get_map_vehicle_by_id(g_vehicule_clique)
		if v:get() then render_selection_vehicle(screen_w, screen_h, v) end
	end
	return "retour_ecran", screen_w + screen_h
end

function begin() begin_load() end
