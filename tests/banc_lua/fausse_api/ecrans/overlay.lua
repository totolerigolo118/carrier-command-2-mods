-- FAUX overlay.lua (couche d'affichage toujours visible). Les notes disent : le jeu n'y appelle JAMAIS begin_load ; il definit
-- g_is_loading / g_loading_text ; sa fonction update() a 4 parametres (screen_w, screen_h, tick_fraction, delta_time) ; il se cache
-- lui-meme par update_set_is_visible(g_loading_alpha > 0) (tour/auto/library_custom_5.lua l. 325 et 533-545 ; partage_detail/07).
g_is_loading = false
g_loading_text = ""
g_loading_alpha = 0
g_appels_overlay = 0

function update(screen_w, screen_h, tick_fraction, delta_time)
	g_appels_overlay = g_appels_overlay + 1
	update_set_is_visible(g_loading_alpha > 0)
end
