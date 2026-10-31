-- FAUX screen_menu_main.lua (menu principal). Les notes disent : g_is_menu_active est defini EN TETE de ce seul script
-- (tour/auto/library_custom_5.lua l. 501) ; faux tant que l'ecran-titre "PRESS ANY KEY" est affiche, vrai ensuite
-- (tour/etudes_demarrage_auto/ETUDE.md section 2). Le vrai menu a au moins 4 contextes Lua, tous nommes screen_front (outil/tests_en_jeu/LISEZ-MOI.txt).
g_is_menu_active = false
g_images_menu = 0

function update(screen_w, screen_h, tick_fraction, delta_time)
	g_images_menu = g_images_menu + 1
	return "menu_ok"
end

function begin() begin_load() end
