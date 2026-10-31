-- ============================================================================
--  DEMARRAGE AUTO  (source du script ; etude tour/etudes_demarrage_auto/ETUDE.md ; jamais essaye en jeu a ce jour)
--
--  Pose par demarrage_auto.py dans un fichier VIDE d'origine de rom_0\scripts (library_custom_0.lua par defaut ; l'outil ajoute en
--  tete les lignes g_da_* qui fixent MODE, SLOT, ATTENTE_S et ATTENDRE_MENU). Dans le menu du jeu, il lance TOUT SEUL la meme commande
--  que le bouton « START » de NEW GAME > CUSTOM (update_ui_event("new_game_custom") : les reglages de partie sont ceux que le jeu a
--  memorises dans persistent_data.xml), ou charge une sauvegarde (MODE = "charger").
--
--  Interrupteur : il ne fait RIEN tant que le mod « Demarrage auto » n'est pas COCHE dans le menu des mods du jeu.
--  Un seul essai par lancement du jeu : si on revient au menu (quit_to_menu), il ne relance pas de partie.
--  Il ne modifie aucun fichier ni aucun reglage (il n'appelle jamais update_set_is_mod_enabled) ; tout est protege par pcall.
-- ============================================================================

local MODE = g_da_mode or "nouvelle"          -- "nouvelle" : new_game_custom ;  "charger" : load_game SLOT
local SLOT = g_da_slot or 19                  -- utilise seulement si MODE == "charger"
local ATTENTE_S = g_da_attente or 30          -- secondes REELLES de menu avant la demande (l'ancien essai de chargement attendait 28 s)
local ATTENDRE_MENU = g_da_attendre_menu or false   -- true : le compte a rebours ne demarre qu'une fois l'ecran-titre « PRESS ANY KEY » passe (une touche)
local NOM_MOD = "Demarrage auto"              -- nom (mod.xml, attribut name) du mod interrupteur
local VERROU = "__cc2_demarrage_auto__"       -- verrou commun a tous les contextes Lua du menu (mot de passe de connexion : jamais ecrit sur disque)

-- le mod interrupteur est-il coche ?
function da_arme()
	local ok, mods = pcall(update_get_mod_details)
	if not ok or type(mods) ~= "table" then return false end
	for _, m in ipairs(mods) do
		if m.is_enabled and m.manifest ~= nil and m.manifest.name == NOM_MOD then return true end
	end
	return false
end

function da_demarrer()
	-- Le menu fait tourner ce script dans PLUSIEURS contextes Lua (constate le 27/10 : au moins 4) : sans verrou, chacun
	-- demanderait la partie en meme temps. Le premier qui passe ici prend le verrou ; les autres ne font rien.
	local okp, mdp = pcall(update_get_join_password)
	if okp and mdp == VERROU then return end
	pcall(update_set_join_password, VERROU)
	if MODE == "charger" then
		local ok, slots = pcall(update_get_save_slots)
		if not ok or type(slots) ~= "table" then return end
		for _, v in ipairs(slots) do
			if v.slot_index == SLOT then
				update_ui_event("load_game", SLOT)
				g_da_envoye = true
				return
			end
		end
	else
		update_ui_event("new_game_custom")
		g_da_envoye = true
	end
end

function da_image(screen_w, screen_h)
	if g_da_envoye then
		-- si ce message RESTE affiche, la commande a ete ignoree (le menu n'a pas ete remplace par la partie)
		update_ui_text(2, screen_h - 12, "DEMARRAGE AUTO : commande envoyee (si ce message reste affiche, elle a ete ignoree : appuie sur une touche)", screen_w - 4, 0, color8(255, 120, 120, 255), 0)
		return
	end
	if g_da_fini then return end
	if g_da_arme == nil then g_da_arme = da_arme() end
	if not g_da_arme then g_da_fini = true; return end
	if ATTENDRE_MENU and not rawget(_G, "g_is_menu_active") then return end
	local ok, e = pcall(update_get_time_since_epoch)
	if not ok or type(e) ~= "number" then return end
	g_da_e0 = g_da_e0 or e
	local reste = ATTENTE_S - (e - g_da_e0)
	if reste > 0 then
		local texte = string.format("DEMARRAGE AUTO dans %d s  (decocher le mod \"%s\" pour annuler)", math.ceil(reste), NOM_MOD)
		update_ui_text(2, screen_h - 12, texte, screen_w - 4, 0, color8(255, 200, 80, 255), 0)
		return
	end
	g_da_fini = true
	pcall(da_demarrer)
end

-- seul l'ecran du menu principal definit g_is_menu_active ; begin_load() est appele par begin() de chaque ecran
function da_accrocher()
	if type(update) ~= "function" or g_da_accroche then return end
	if rawget(_G, "g_is_menu_active") == nil then return end
	g_da_accroche = true
	local origine = update
	update = function(screen_w, screen_h, ...)
		local retours = table.pack(origine(screen_w, screen_h, ...))
		pcall(da_image, screen_w, screen_h)
		return table.unpack(retours, 1, retours.n)
	end
end

if not g_da_installe then
	g_da_installe = true
	g_da_begin_load_origine = begin_load
	begin_load = function(...)
		local retours = { n = 0 }
		if g_da_begin_load_origine ~= nil then retours = table.pack(g_da_begin_load_origine(...)) end
		pcall(da_accrocher)
		return table.unpack(retours, 1, retours.n)
	end
end
