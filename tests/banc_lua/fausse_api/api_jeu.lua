-- LA FAUSSE API LUA DU JEU : construit l'environnement global d'un contexte (= un ecran du jeu).
--
-- Principe repris des notes du depot :
--  * le jeu embarque Lua 5.3.5 avec SEULEMENT base, debug, math, string, table, utf8 (partage_detail/07) : pas de io, os, package, coroutine ;
--  * chaque ecran a son PROPRE etat Lua (variables globales separees) ; le monde et le mot de passe de connexion sont communs ;
--  * les fonctions C de l'API (update_*) ne sont liees qu'au begin_load() de l'ecran, pas au chargement du fichier
--    (outil/tests_en_jeu/LISEZ-MOI.txt, "pieges rencontres") : avant, elles valent nil ;
--  * selon le type d'ecran, toute l'API n'est pas presente : les ecrans de bord ont l'API du monde, l'overlay et l'ecran
--    d'indications NON (tour/auto/library_custom_5.lua, "mesure du 27/10") ; le menu a l'API du frontend.
-- Chaque fonction est declaree avec son statut (DOC / SCRIPT / SUPPOSE) : voir inventaire.lua et INVENTAIRE_API.md.

local Inv = require("fausse_api.inventaire")
local Obj = require("fausse_api.objets")
local decl = Inv.decl

local Api = {}

local function copie_superficielle(t)
	local c = {}
	for k, v in pairs(t) do c[k] = v end
	return c
end

local function copie_profonde(t)
	if type(t) ~= "table" then return t end
	local c = {}
	for k, v in pairs(t) do c[k] = copie_profonde(v) end
	return c
end

local function exige_nombre(nom, i, v)
	if type(v) ~= "number" then error(("bad argument #%d to '%s' (number expected, got %s)"):format(i, nom, type(v)), 3) end
end

local function exige_texte(nom, i, v)
	if type(v) ~= "string" then error(("bad argument #%d to '%s' (string expected, got %s)"):format(i, nom, type(v)), 3) end
end

-- ------------------------------------------------------------------ environnement de base (bibliotheques Lua du jeu)
-- Enumerations et aides ecrites EN LUA dans rom_0/scripts (library_enum.lua, library_ui.lua...) : presentes des le chargement.
function Api.nouvel_env(ctx)
	local env = {}
	env._G = env
	env._VERSION = _VERSION
	-- DOC (partage_detail/07) : bibliotheques ouvertes = base, debug, math, string, table, utf8.
	for _, nom in ipairs({ "assert", "collectgarbage", "error", "getmetatable", "ipairs", "next", "pairs", "pcall", "rawequal",
		"rawget", "rawlen", "rawset", "select", "setmetatable", "tonumber", "tostring", "type", "xpcall" }) do
		env[nom] = _G[nom]
	end
	-- SUPPOSE : dofile / loadfile / load existent dans la bibliotheque de base de Lua 5.3, mais aucun script du depot ne les appelle
	-- et le banc ne veut pas qu'un script lise des fichiers : ils sont retires (la verification statique du lanceur les cherche).
	for _, nom in ipairs({ "string", "table", "math", "utf8" }) do env[nom] = copie_superficielle(_G[nom]) end
	env.debug = debug
	env.print = function(...)
		local m = {}
		for i = 1, select("#", ...) do m[#m + 1] = tostring((select(i, ...))) end
		ctx.prints[#ctx.prints + 1] = table.concat(m, "\t")
	end

	-- library_enum.lua : e_game_object_type (valeurs DOC : partage_detail/08 section 4)
	env.e_game_object_type = copie_superficielle(require("fausse_api.jeu").DEFS)
	-- SUPPOSE : valeurs de e_active_input (seul .keyboard est utilise par les scripts du depot)
	env.e_active_input = { keyboard = 0, gamepad = 1 }
	-- SUPPOSE : atlas_icons (library_ui.lua) ; seul column_pending est utilise ; la valeur exacte est sans importance
	env.atlas_icons = { column_pending = 1 }

	decl("lua du jeu", "color8", "SCRIPT", "color8(r, g, b, a) -> table {r, g, b, a} (le vrai type est inconnu ; les scripts ne font que le transmettre). Disponible des le chargement des fichiers (les onglets carburant l'appellent au chargement)")
	env.color8 = function(r, g, b, a)
		exige_nombre("color8", 1, r); exige_nombre("color8", 2, g); exige_nombre("color8", 3, b); exige_nombre("color8", 4, a)
		if r < 0 or r > 255 or g < 0 or g > 255 or b < 0 or b > 255 or a < 0 or a > 255 then
			ctx.jeu:avertir(("color8 hors 0..255 : %s,%s,%s,%s"):format(r, g, b, a))
		end
		return { r = r, g = g, b = b, a = a }
	end
	decl("lua du jeu", "e_game_object_type", "DOC", "carrier 0, Albatros 8, Manta 10, Razorbill 12, Petrel 14 (partage_detail/08)")
	decl("lua du jeu", "e_active_input", "SUPPOSE", "{ keyboard = 0, gamepad = 1 }")
	decl("lua du jeu", "atlas_icons", "SUPPOSE", "{ column_pending = 1 }")
	decl("lua du jeu", "print", "DOC", "le jeu jette stdout ; le banc le capture dans ctx.prints")
	return env
end

-- ------------------------------------------------------------------ fonctions C : par groupes
local function groupe_dessin(ctx, env)
	decl("dessin", "update_ui_get_text_size", "SUPPOSE", "(texte, largeur, indicateur) -> 5 * #texte, 9 (meme doublure que tests/test_horloge.py ; la vraie police est inconnue)")
	env.update_ui_get_text_size = function(texte, largeur, flag)
		exige_texte("update_ui_get_text_size", 1, texte)
		return #texte * 5, 9
	end
	decl("dessin", "update_ui_text", "SCRIPT", "(x, y, texte, largeur, alignement, couleur, ?) : enregistre le texte dans ctx.dessin.textes ; types verifies comme le ferait une liaison C")
	env.update_ui_text = function(x, y, texte, largeur, align, couleur, extra)
		exige_nombre("update_ui_text", 1, x); exige_nombre("update_ui_text", 2, y)
		exige_texte("update_ui_text", 3, texte)
		exige_nombre("update_ui_text", 4, largeur)
		if type(couleur) ~= "table" then error("bad argument #6 to 'update_ui_text' (color expected)", 2) end
		local t = ctx.dessin.textes
		t[#t + 1] = { x = x, y = y, texte = texte, largeur = largeur, couleur = couleur }
		if ctx.erreur_dessin then error(ctx.erreur_dessin, 2) end
	end
	decl("dessin", "update_ui_rectangle", "SCRIPT", "(x, y, w, h, couleur) : enregistre le rectangle dans ctx.dessin.rects")
	env.update_ui_rectangle = function(x, y, w, h, couleur)
		exige_nombre("update_ui_rectangle", 1, x); exige_nombre("update_ui_rectangle", 2, y)
		exige_nombre("update_ui_rectangle", 3, w); exige_nombre("update_ui_rectangle", 4, h)
		if type(couleur) ~= "table" then error("bad argument #5 to 'update_ui_rectangle' (color expected)", 2) end
		if w < 0 or h < 0 then ctx.jeu:avertir(("update_ui_rectangle de taille negative (%s x %s) par %s"):format(w, h, ctx.nom)) end
		local r = ctx.dessin.rects
		r[#r + 1] = { x = x, y = y, w = w, h = h, couleur = couleur }
	end
	decl("dessin", "update_ui_rectangle_outline", "SCRIPT", "(x, y, w, h, couleur) : enregistre le contour")
	env.update_ui_rectangle_outline = function(x, y, w, h, couleur)
		exige_nombre("update_ui_rectangle_outline", 1, x); exige_nombre("update_ui_rectangle_outline", 2, y)
		exige_nombre("update_ui_rectangle_outline", 3, w); exige_nombre("update_ui_rectangle_outline", 4, h)
		if type(couleur) ~= "table" then error("bad argument #5 to 'update_ui_rectangle_outline' (color expected)", 2) end
		local r = ctx.dessin.contours
		r[#r + 1] = { x = x, y = y, w = w, h = h, couleur = couleur }
	end
end

local EVENEMENTS_CONNUS = {   -- DOC : partage_detail/07 section 3 et tour/etudes_demarrage_auto/ETUDE.md section 2
	new_game_custom = true, new_game_campaign = true, load_game = true, host_load_game = true, host_game = true,
	host_game_campaign = true, save_game = true, quit_game = true, quit_to_menu = true, set_game_setting = true, chat = true,
	character_return_to_bridge = true,
}

local function groupe_evenements(ctx, env)
	decl("evenements", "update_ui_event", "DOC", "(nom, arguments...) : enregistre l'evenement dans jeu.evenements ; AUCUN effet de jeu n'est simule (la partie ne se charge pas) ; nom inconnu = avertissement")
	env.update_ui_event = function(nom, ...)
		exige_texte("update_ui_event", 1, nom)
		if not EVENEMENTS_CONNUS[nom] then ctx.jeu:avertir("update_ui_event : nom inconnu '" .. nom .. "' par " .. ctx.nom) end
		ctx.jeu:evenement(ctx.nom, nom, { ... })
	end
	decl("evenements", "update_set_host_password", "SCRIPT", "(texte) : memorise le mot de passe d'hebergement dans jeu.mot_de_passe_hote (boite aux lettres du script d'essai auto)")
	env.update_set_host_password = function(texte)
		exige_texte("update_set_host_password", 1, texte)
		local j = ctx.jeu
		j.appels_mdp_hote = (j.appels_mdp_hote or 0) + 1
		if j.mot_de_passe_hote ~= texte then j.changements_mdp_hote = (j.changements_mdp_hote or 0) + 1 end
		j.mot_de_passe_hote = texte
	end
end

local function groupe_temps_reel(ctx, env)
	decl("temps", "update_get_time_since_epoch", "DOC", "secondes reelles (flottant) ; SUPPOSE : depuis 1970")
	env.update_get_time_since_epoch = function() return ctx.jeu.reel end
end

local function groupe_monde(ctx, env)
	local jeu = ctx.jeu
	decl("monde", "update_get_logic_tick", "DOC", "tick de simulation entier, 30 par seconde de jeu ; present dans les ecrans de bord")
	env.update_get_logic_tick = function() return jeu.tick end
	decl("monde", "update_get_map_vehicle_count", "DOC", "nombre de vehicules de la carte (y compris caches par le brouillard)")
	env.update_get_map_vehicle_count = function() return #jeu.ordre_ids end
	decl("monde", "update_get_map_vehicle_by_index", "DOC", "poignee du i-eme vehicule, i de 0 a count-1 ; hors limites : poignee dont get() est faux (SUPPOSE)")
	env.update_get_map_vehicle_by_index = function(i)
		exige_nombre("update_get_map_vehicle_by_index", 1, i)
		return Obj.poignee(jeu, jeu.ordre_ids[i + 1] or -1)
	end
	decl("monde", "update_get_map_vehicle_by_id", "DOC", "poignee du vehicule d'identifiant id ; get() faux s'il n'existe pas")
	env.update_get_map_vehicle_by_id = function(id)
		exige_nombre("update_get_map_vehicle_by_id", 1, id)
		return Obj.poignee(jeu, id)
	end
	decl("monde", "update_get_screen_vehicle", "DOC", "le vehicule de l'ecran (le porte-avions) ; get() faux s'il n'y en a pas")
	env.update_get_screen_vehicle = function() return Obj.poignee(jeu, ctx.vehicule_ecran or -1) end
	decl("monde", "update_get_screen_team_id", "DOC", "equipe de l'ecran (= celle du joueur)")
	env.update_get_screen_team_id = function() return jeu.equipe_joueur end
	decl("monde", "update_get_peer_count", "SCRIPT", "nombre de joueurs (pairs) de la partie ; utilise par tour/auto sous pcall")
	env.update_get_peer_count = function() return #jeu.pairs_reseau end
	decl("monde", "update_get_peer_team", "SCRIPT", "equipe du i-eme pair (i a partir de 0)")
	env.update_get_peer_team = function(i)
		exige_nombre("update_get_peer_team", 1, i)
		local p = jeu.pairs_reseau[i + 1]
		return p and p.equipe or nil
	end
	decl("monde", "update_get_is_focus_local", "DOC", "vrai si le joueur local est sur cet ecran (partage_detail/07) ; toujours vrai ici (SUPPOSE)")
	env.update_get_is_focus_local = function() return true end
	decl("monde", "update_get_active_input_type", "SCRIPT", "e_active_input courant ; e_active_input.keyboard par defaut (reglable : ctx.entree)")
	env.update_get_active_input_type = function() return ctx.entree or env.e_active_input.keyboard end
end

local function groupe_menu(ctx, env)
	local jeu = ctx.jeu
	decl("menu (frontend)", "update_get_save_slots", "DOC", "liste de { slot_index, display_name, save_name, time } (partage_detail/07)")
	env.update_get_save_slots = function() return copie_profonde(jeu.sauvegardes) end
	decl("menu (frontend)", "update_get_mod_details", "DOC", "liste de { id, is_enabled, manifest = { name } } (tour/etudes_demarrage_auto/ETUDE.md section 2) ; relue a chaque appel, donc un scenario peut cocher/decocher un mod en cours de route (SUPPOSE : le vrai menu des mods se comporte ainsi)")
	env.update_get_mod_details = function() return copie_profonde(jeu.mods) end
	decl("menu (frontend)", "update_get_join_password", "DOC", "mot de passe de connexion, partage par TOUS les contextes (jeu.mot_de_passe_connexion) ; \"\" au depart (SUPPOSE)")
	env.update_get_join_password = function() return jeu.mot_de_passe_connexion end
	decl("menu (frontend)", "update_set_join_password", "DOC", "change ce mot de passe commun (verrou entre contextes)")
	env.update_set_join_password = function(v)
		exige_texte("update_set_join_password", 1, v)
		jeu.mot_de_passe_connexion = v
	end
end

local function groupe_overlay(ctx, env)
	decl("overlay", "update_set_is_visible", "SCRIPT", "(bool) : memorise la visibilite de la couche dans ctx.visible")
	env.update_set_is_visible = function(v) ctx.visible = v and true or false end
end

local function groupe_nom_ecran(ctx, env)
	decl("ecran", "begin_get_screen_name", "DOC", "nom de l'ecran (ex. screen_veh_m) ; absent de l'ecran de pilotage (partage_detail/07)")
	env.begin_get_screen_name = function() return ctx.nom end
end

-- profils : quels groupes de fonctions C chaque type de contexte possede. SUPPOSE dans le detail :
-- seul est etabli par les notes que l'overlay et l'ecran d'indications n'ont PAS l'API du monde (tour/auto/library_custom_5.lua l. 349-350).
local PROFILS = {
	bord = { groupe_dessin, groupe_evenements, groupe_temps_reel, groupe_monde, groupe_nom_ecran },
	menu = { groupe_dessin, groupe_evenements, groupe_temps_reel, groupe_menu, groupe_nom_ecran },
	overlay = { groupe_dessin, groupe_evenements, groupe_overlay },
	hud = { groupe_dessin, groupe_evenements },
	simple = { groupe_dessin, groupe_nom_ecran },
}
Api.PROFILS = PROFILS

-- lie l'API C dans l'environnement (au begin_load, ou au chargement selon le contexte)
function Api.lier(ctx)
	if ctx.api_liee then return end
	ctx.api_liee = true
	local groupes = PROFILS[ctx.profil]
	if not groupes then error("profil inconnu : " .. tostring(ctx.profil)) end
	for _, g in ipairs(groupes) do g(ctx, ctx.env) end
end

-- declare tous les groupes dans l'inventaire (pour INVENTAIRE_API.md) sans lier quoi que ce soit
function Api.tout_declarer()
	local faux = { jeu = { avertir = function() end }, dessin = { textes = {}, rects = {}, contours = {} }, prints = {}, nom = "?" }
	Api.nouvel_env(faux)
	local env = {}
	faux.env = env
	for _, g in ipairs({ groupe_dessin, groupe_evenements, groupe_temps_reel, groupe_monde, groupe_menu, groupe_overlay, groupe_nom_ecran }) do
		g(faux, env)
	end
end

return Api
