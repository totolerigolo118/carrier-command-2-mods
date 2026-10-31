-- Scenarios de tour/etudes_modes_carburant/lua/library_custom_5.lua : onglet SPEED v1 (MAQUETTE SANS EFFET).
-- Trois boutons ECO / NORMAL / FLANK sous la fenetre LOADOUT quand on clique sur un avion de son equipe ; le choix n'est memorise que dans l'ecran.
-- Le script ne doit RIEN envoyer au jeu ni au SDK (aucune commande de vitesse, gaz ou carburant).
local cadre = ...
local Jeu = require("fausse_api.jeu")
local Contexte = require("fausse_api.contexte")
local O = require("fausse_api.onglet")
local A = require("fausse_api.aides")

local SCRIPT = "tour/etudes_modes_carburant/lua/library_custom_5.lua"

local function nouveau(opts)
	local jeu = Jeu.nouveau()
	O.monde(jeu)
	local ctx = O.ecran(jeu, SCRIPT, opts)
	return jeu, ctx
end

cadre.groupe("onglet SPEED v1 (maquette) : lua/library_custom_5.lua", function()

	cadre.scenario("se charge sans erreur dans les 4 ordres de chargement, onglet dessine sous LOADOUT", function(t)
		for _, c in ipairs(A.COMBINAISONS) do
			local jeu = Jeu.nouveau()
			O.monde(jeu)
			local ok, err = pcall(function() O.ecran(jeu, SCRIPT, { ordre = c.ordre, liaison = c.liaison }) end)
			t:verifier(ok, "chargement (" .. A.nom_combinaison(c) .. ")", err)
			local ctx = jeu.contextes[1]
			if ok then
				O.selectionner(ctx, 9)
				O.image(ctx)
				local f = O.fenetre(ctx)
				t:verifier(f ~= nil, "fenetre SPEED dessinee (" .. A.nom_combinaison(c) .. ")")
				t:verifier(#ctx.erreurs == 0 and not ctx.env.g_cm.casse, "aucune erreur (" .. A.nom_combinaison(c) .. ")", ctx.erreurs[1])
			end
		end
	end)

	cadre.scenario("ne cree que ses globales g_cm / g_cm_ui_*", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1 })
		ctx:charger_ecran("bord_controle")
		local avant = A.cles(ctx.env)
		ctx:charger_script(SCRIPT)
		t:egal(A.nouvelles_cles(avant, ctx.env), { "g_cm", "g_cm_ui_begin_load", "g_cm_ui_enveloppe" }, "globales creees au chargement")
	end)

	cadre.scenario("geometrie : sous LOADOUT (y 99), meme x et meme largeur (74), contenu dans la fenetre", function(t)
		local jeu, ctx = nouveau()
		O.selectionner(ctx, 9)
		O.image(ctx)
		local f = O.fenetre(ctx)
		local loadout = ctx.ui:fenetre("LOADOUT##faux")
		t:egal({ f.x, f.y, f.w, f.h }, { 172, 99, 74, 80 }, "fenetre SPEED en (172, 99), 74 x 80")
		t:egal({ f.x, f.w }, { loadout.x, loadout.w }, "meme x et meme largeur que LOADOUT")
		t:verifier(f.y >= loadout.y + loadout.h, "commence sous le bas de LOADOUT", f.y)
		t:verifier(f.cy <= f.y + f.h, "le contenu tient dans la fenetre (pas de barre de defilement)", f.cy)
		t:verifier(f.x + f.w <= 256, "tient dans l'ecran de 256")
		t:egal(f.textes, { "MAQUETTE : SANS EFFET" }, "texte d'avertissement")
		t:egal(f.couleurs[1].r, 255, "avertissement en rouge")
		t:egal(#ctx.ui.window_stack, 0, "pile des fenetres vide apres l'image")
		t:egal(#ctx.ui.region_stack, 0, "pile des regions vide apres l'image")
	end)

	cadre.scenario("seulement les avions (Albatros, Manta) de l'equipe de l'ecran", function(t)
		local jeu, ctx = nouveau()
		for id, attendu in pairs({ [9] = true, [10] = true, [11] = false, [12] = false, [13] = true, [1] = false }) do
			O.selectionner(ctx, id)
			O.image(ctx)
			t:egal(O.fenetre(ctx) ~= nil, attendu, ("vehicule %d : onglet %s"):format(id, attendu and "affiche" or "absent"))
		end
		ctx.env.g_selected_vehicle_ui.confirm_self_destruct = true
		O.selectionner(ctx, 9)
		O.image(ctx)
		t:verifier(O.fenetre(ctx) == nil, "pas d'onglet pendant la confirmation d'autodestruction")
		t:verifier(#ctx.erreurs == 0 and not ctx.env.g_cm.casse, "aucune erreur")
	end)

	cadre.scenario("boutons : NORMAL allume au depart ; un clic allume ECO ou FLANK ; un mode par avion", function(t)
		local jeu, ctx = nouveau()
		O.selectionner(ctx, 9)
		O.image(ctx)
		t:egal(O.bouton_allume(ctx), 2, "NORMAL allume au depart")
		O.image(ctx, 1)
		t:egal(O.bouton_allume(ctx), nil, "image du clic ECO : aucun bouton allume (ECO est dessine avant le clic, NORMAL apres)")
		O.image(ctx)
		t:egal(O.bouton_allume(ctx), 1, "image suivante : ECO allume")
		O.image(ctx)
		t:egal(O.bouton_allume(ctx), 1, "le choix est conserve")
		O.cliquer(ctx, 3)
		t:egal(O.bouton_allume(ctx), 3, "clic FLANK : FLANK allume")
		O.selectionner(ctx, 10)
		O.image(ctx)
		t:egal(O.bouton_allume(ctx), 2, "l'avion 10 est encore en NORMAL (un mode par avion)")
		O.selectionner(ctx, 9)
		O.image(ctx)
		t:egal(O.bouton_allume(ctx), 3, "l'avion 9 a garde FLANK")
		t:egal(ctx.env.g_cm.modes, { [9] = 3 }, "seuls les avions modifies sont memorises")
		t:verifier(ctx.ui.input_pointer_1 == false, "le clic est consomme")
	end)

	cadre.scenario("clic hors des boutons ou fenetre inactive : rien ne change", function(t)
		local jeu, ctx = nouveau()
		O.selectionner(ctx, 9)
		O.image(ctx)
		ctx.ui.pointeur = { x = 10, y = 10 }; ctx.ui.input_pointer_1 = true
		ctx:image()
		t:egal(O.bouton_allume(ctx), 2, "clic ailleurs : toujours NORMAL")
		ctx.ui.fenetre_active = false
		O.image(ctx, 1)
		t:egal(O.bouton_allume(ctx), 2, "fenetre inactive : le clic est ignore")
	end)

	cadre.scenario("la maquette ne commande RIEN : aucun appel au SDK, aucun evenement, aucun ordre", function(t)
		local jeu = Jeu.nouveau()
		O.monde(jeu)
		local ctx = O.ecran(jeu, SCRIPT, { cc2x = { niveau = "0.5", plugin_modes = true } })
		O.selectionner(ctx, 9)
		for i = 1, 3 do O.image(ctx, i) end
		t:egal(#ctx.cc2x.appels_modes, 0, "aucun appel a cc2x.modes.*")
		t:egal(#jeu.evenements, 0, "aucun update_ui_event")
		t:egal(#jeu.journal_ordres, 0, "aucun ordre de vol")
		t:egal(#jeu.journal_cc2x, 0, "rien dans cc2x.log")
		t:verifier(jeu.mot_de_passe_hote == nil and jeu.mot_de_passe_connexion == "", "aucun mot de passe touche")
	end)

	cadre.scenario("erreur de dessin : piles de l'interface remises en ordre, onglet coupe pour cet ecran, le jeu continue", function(t)
		for _, methode in ipairs({ "text_basic", "spacer", "get_region" }) do
			local jeu, ctx = nouveau()
			O.selectionner(ctx, 9)
			O.image(ctx)
			t:verifier(not ctx.env.g_cm.casse, methode .. " : sain au depart")
			ctx.ui.faute = { methode = methode, fenetre = O.TITRE, message = "faute injectee" }
			local ok, a, b = O.image(ctx, 1)
			t:verifier(ok and a == "retour_ecran" and b == 512, methode .. " : l'ecran du jeu continue et rend ses valeurs", tostring(a))
			t:verifier(ctx.env.g_cm.casse == true, methode .. " : onglet desactive")
			t:egal(#ctx.ui.window_stack, 0, methode .. " : pile des fenetres rendue")
			t:egal(#ctx.ui.region_stack, 0, methode .. " : pile des regions rendue")
			t:verifier(#ctx.erreurs == 0, methode .. " : aucune erreur remontee a l'ecran")
			ctx.ui.faute = nil
			O.image(ctx)
			t:verifier(O.fenetre(ctx) == nil, methode .. " : plus d'onglet ensuite (coupe pour cet ecran)")
			t:verifier(#ctx.ui.window_stack == 0, methode .. " : piles toujours saines")
		end
	end)

	cadre.scenario("panne qui laisse une REGION de plus ouverte : le script depile aussi les regions en trop", function(t)
		local jeu, ctx = nouveau()
		O.selectionner(ctx, 9)
		O.image(ctx)
		ctx.ui.faute = { methode = "text_basic", fenetre = O.TITRE, message = "faute injectee", empile_region = true }
		local ok, a = O.image(ctx)
		t:verifier(ok and a == "retour_ecran", "l'ecran du jeu continue")
		t:egal(#ctx.ui.window_stack, 0, "pile des fenetres rendue")
		t:egal(#ctx.ui.region_stack, 0, "pile des regions rendue, region en trop comprise")
		t:verifier(ctx.env.g_cm.casse, "onglet coupe")
	end)

	cadre.scenario("erreur dans begin_window : rien n'est empile, onglet coupe, ligne CC2MODES|UI dans cc2x.log si le SDK est la", function(t)
		local jeu = Jeu.nouveau()
		O.monde(jeu)
		local ctx = O.ecran(jeu, SCRIPT, { cc2x = { niveau = "0.5" } })
		O.selectionner(ctx, 9)
		ctx.ui.faute = { methode = "begin_window", fenetre = "*", message = "faute injectee" }
		-- faute sur TOUT begin_window : le jeu lui-meme (STATUS) tombe aussi ; on la limite a la fenetre SPEED par le titre
		ctx.ui.faute = nil
		local vrai = ctx.ui.begin_window
		ctx.ui.begin_window = function(self, titre, ...)
			if titre == O.TITRE then error("fenetre refusee", 2) end
			return vrai(self, titre, ...)
		end
		local ok, a = O.image(ctx)
		t:verifier(ok and a == "retour_ecran", "l'ecran du jeu continue")
		t:verifier(ctx.env.g_cm.casse, "onglet coupe")
		t:egal(#ctx.ui.window_stack, 0, "pile propre")
		local erreurs = {}
		for _, l in ipairs(jeu.journal_cc2x) do if l:find("CC2MODES|UI|erreur|", 1, true) then erreurs[#erreurs + 1] = l end end
		t:egal(#erreurs, 1, "une ligne CC2MODES|UI|erreur| dans cc2x.log")
		t:verifier(erreurs[1] and erreurs[1]:find("fenetre refusee", 1, true), "avec la cause", erreurs[1])
	end)

	cadre.scenario("g_ui absent ou pas une table : le script se tait", function(t)
		local jeu = Jeu.nouveau()
		O.monde(jeu)
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1 })
		-- ecran sans g_ui : render_selection_vehicle d'origine ne dessine rien
		ctx:charger_texte("function render_selection_vehicle(w, h, v) return 'x' end function update(w, h) render_selection_vehicle(w, h, update_get_map_vehicle_by_id(9)) return 'ok' end function begin() begin_load() end", "ecran_sans_ui")
		ctx:charger_script(SCRIPT)
		ctx:begin()
		ctx.env.g_ui = nil
		local ok, a = ctx:image()
		t:verifier(ok and a == "ok", "l'ecran du jeu continue")
		t:verifier(not ctx.env.g_cm.casse, "pas de panne declaree pour autant")
		ctx.env.g_ui = "pas une table"
		ok, a = ctx:image()
		t:verifier(ok and a == "ok" and not ctx.env.g_cm.casse, "g_ui non table : idem")
	end)

	cadre.scenario("render_selection_vehicle : enveloppe unique et transparente, quel que soit l'ordre de chargement", function(t)
		for _, c in ipairs(A.COMBINAISONS) do
			local jeu = Jeu.nouveau()
			O.monde(jeu)
			local ctx = O.ecran(jeu, SCRIPT, { ordre = c.ordre, liaison = c.liaison })
			O.selectionner(ctx, 9)
			O.image(ctx)
			local n = 0
			for _, f in ipairs(ctx.ui.dessinees) do if f.titre == O.TITRE then n = n + 1 end end
			t:egal(n, 1, "une seule fenetre SPEED par image (" .. A.nom_combinaison(c) .. ")")
			local r = table.pack(ctx.env.render_selection_vehicle(256, 256, ctx.env.update_get_map_vehicle_by_id(9)))
			t:egal({ r.n, r[1], r[2] }, { 2, "selection_ok", 9 }, "valeurs de retour du jeu conservees (" .. A.nom_combinaison(c) .. ")")
		end
	end)

	cadre.scenario("le choix n'est PAS partage entre les 3 ecrans de bord (limite annoncee dans le script)", function(t)
		local jeu = Jeu.nouveau()
		O.monde(jeu)
		local l = O.ecran(jeu, SCRIPT, { nom = "screen_veh_l" })
		local m = O.ecran(jeu, SCRIPT, { nom = "screen_veh_m" })
		O.selectionner(l, 9); O.selectionner(m, 9)
		O.cliquer(l, 1); O.image(m)
		t:egal(O.bouton_allume(l), 1, "ecran L : ECO")
		t:egal(O.bouton_allume(m), 2, "ecran M : toujours NORMAL")
	end)
end)
