-- FAUX interactions.lua (ecran d'indications "p/esc pause, e interact") : dessine en permanence sur toute la fenetre.
-- SUPPOSE : signature update(screen_w, screen_h, tick_fraction, delta_time) comme l'overlay ; appelle begin_load comme les autres ecrans
-- (tour/auto/library_custom_5.lua l. 474-476).
g_interactions = {}
g_appels_indications = 0

function update(screen_w, screen_h, tick_fraction, delta_time)
	g_appels_indications = g_appels_indications + 1
end

function begin() begin_load() end
