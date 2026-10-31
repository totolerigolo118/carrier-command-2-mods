-- Scenarios de tour/lua/library_custom_7.lua : affichage "SIM x1.00" (temps de jeu / temps reel, fenetres de 10 s reelles).
local cadre = ...
local Jeu = require("fausse_api.jeu")
local Contexte = require("fausse_api.contexte")
local A = require("fausse_api.aides")

local SCRIPT = "tour/lua/library_custom_7.lua"

local function ecran_sim(opts)
	opts = opts or {}
	local jeu = Jeu.nouveau()
	local ctx = A.ecran_de_bord(jeu, { SCRIPT }, opts)
	return jeu, ctx
end

local function valeur_sim(ctx)
	local txt = ctx:texte_contenant("SIM x")
	return txt and tonumber(txt.texte:match("SIM x([%d.]+)")) or nil
end

local function texte_sim(ctx)
	local t = ctx:texte_contenant("SIM")
	return t and t.texte or nil
end

cadre.groupe("library_custom_7.lua : vitesse de simulation (SIM)", function()

	cadre.scenario("se charge sans erreur dans les 4 ordres de chargement et affiche SIM ...", function(t)
		for _, c in ipairs(A.COMBINAISONS) do
			local jeu = Jeu.nouveau()
			local ok, err = pcall(function() return A.ecran_de_bord(jeu, { SCRIPT }, c) end)
			t:verifier(ok, "chargement (" .. A.nom_combinaison(c) .. ")", err)
			if ok then
				local ctx = jeu.contextes[1]
				ctx:image(); jeu:avancer(1 / 30)
				t:verifier(#ctx.erreurs == 0, "aucune erreur de l'ecran (" .. A.nom_combinaison(c) .. ")", ctx.erreurs[1])
				t:egal(texte_sim(ctx), "SIM ...", "premiere image : 'SIM ...' (" .. A.nom_combinaison(c) .. ")")
			end
		end
	end)

	cadre.scenario("ne cree que ses propres globales (g_vsim, vsim_*)", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord" })
		ctx:charger_ecran("bord_controle")
		local avant = A.cles(ctx.env)
		ctx:charger_script(SCRIPT)
		t:egal(A.nouvelles_cles(avant, ctx.env), {
			"g_vsim", "g_vsim_begin_load_origine", "vsim_begin_load", "vsim_dessiner", "vsim_observer", "vsim_update",
		}, "globales creees au chargement")
	end)

	cadre.scenario("n'accroche que screen_veh_l / m / r (update intact ailleurs)", function(t)
		for _, nom in ipairs({ "screen_veh_l", "screen_veh_m", "screen_veh_r" }) do
			local jeu, ctx = ecran_sim({ nom = nom })
			t:verifier(ctx.env.g_vsim_update_origine ~= nil, nom .. " : update enveloppe")
			t:verifier(ctx.env.update == ctx.env.vsim_update, nom .. " : update = vsim_update")
		end
		for _, nom in ipairs({ "screen_front", "holomap_screen", "screen_veh_top_m", "screen_veh_top_r", "screen_inv_l" }) do
			local jeu = Jeu.nouveau()
			local ctx = Contexte.nouveau(jeu, { nom = nom, profil = "simple" })
			ctx:monter({ ecran = "simple", libs = { SCRIPT } })
			t:verifier(ctx.env.g_vsim_update_origine == nil, nom .. " : update NON enveloppe")
			local ok, a, b = ctx:image()
			t:verifier(ok and a == "simple_ok", nom .. " : retour de l'ecran inchange")
			t:verifier(texte_sim(ctx) == nil, nom .. " : rien dessine")
		end
	end)

	cadre.scenario("ecran de pilotage sans begin_get_screen_name : pas de crochet, pas d'erreur", function(t)
		-- DOC (partage_detail/07) : "The pilot HUD has no begin_get_screen_name"
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "?", profil = "hud" })
		ctx:monter({ ecran = "indications", libs = { SCRIPT } })
		t:verifier(ctx.env.begin_get_screen_name == nil, "le contexte n'a pas begin_get_screen_name")
		t:verifier(ctx.env.g_vsim_update_origine == nil, "update non enveloppe")
		t:verifier(#ctx.erreurs == 0, "aucune erreur")
	end)

	cadre.scenario("l'enveloppe est transparente : memes parametres, memes retours (y compris nil au milieu)", function(t)
		for _, c in ipairs(A.COMBINAISONS) do
			local jeu = Jeu.nouveau()
			local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", liaison = c.liaison })
			local recu
			local ecran = [[
				function update(...) g_recu = table.pack(...); return 1, nil, 3, nil end
				function begin() begin_load() end
			]]
			if c.ordre == "avant" then ctx:charger_script(SCRIPT); ctx:charger_texte(ecran, "ecran_nil") else ctx:charger_texte(ecran, "ecran_nil"); ctx:charger_script(SCRIPT) end
			ctx:begin()
			local r = ctx:update_brut(300, 200, 0.5, 33.0, "p5", nil, "p7")
			t:verifier(r[1], "update ne leve pas d'erreur (" .. A.nom_combinaison(c) .. ")", r[2])
			t:egal({ r.n, r[2], r[3], r[4], r[5] }, { 5, 1, nil, 3, nil }, "retours (1, nil, 3, nil) conserves (" .. A.nom_combinaison(c) .. ")")
			local g = ctx.env.g_recu
			t:egal({ g.n, g[1], g[2], g[3], g[4], g[5], g[6], g[7] }, { 7, 300, 200, 0.5, 33.0, "p5", nil, "p7" }, "7 parametres retransmis (" .. A.nom_combinaison(c) .. ")")
		end
	end)

	cadre.scenario("mesure x1.00 / x2.00 / x0.50 / x1.33 (fenetres de 10 s reelles)", function(t)
		for _, cas in ipairs({ { 1.0, "SIM x1.00" }, { 2.0, "SIM x2.00" }, { 0.5, "SIM x0.50" }, { 4 / 3, "SIM x1.33" } }) do
			local jeu, ctx = ecran_sim()
			jeu:jouer(5, { vitesse = cas[1], fps = 30 })
			t:egal(texte_sim(ctx), "SIM ...", ("x%.2f : toujours 'SIM ...' avant la fin de la premiere fenetre (5 s)"):format(cas[1]))
			jeu:jouer(7, { vitesse = cas[1], fps = 30 })
			t:egal(texte_sim(ctx), cas[2], ("x%.2f : affiche apres 12 s reelles"):format(cas[1]))
			t:verifier(#ctx.erreurs == 0, "aucune erreur")
			t:verifier(#jeu.avertissements == 0, "aucun avertissement de la fausse API", jeu.avertissements[1])
		end
	end)

	cadre.scenario("la valeur suit un changement de vitesse a la fenetre suivante", function(t)
		local jeu, ctx = ecran_sim()
		jeu:jouer(12, { vitesse = 1.0 })
		t:egal(texte_sim(ctx), "SIM x1.00", "1.00 d'abord (fenetre 0-10 s)")
		jeu:jouer(11, { vitesse = 2.0 })
		-- la fenetre 10-20 s contient 2 s a x1 et 8 s a x2 : (2*1 + 8*2) / 10 = 1.80 (comportement voulu : moyenne sur 10 s)
		local v = valeur_sim(ctx)
		t:verifier(v and math.abs(v - 1.8) < 0.05, "fenetre melangee a 20 s : environ 1.80", v)
		jeu:jouer(10, { vitesse = 2.0 })
		t:egal(texte_sim(ctx), "SIM x2.00", "fenetre 20-30 s entierement a x2 : 2.00")
	end)

	cadre.scenario("jeu en pause : x0.00, sans division par zero", function(t)
		local jeu, ctx = ecran_sim()
		jeu:jouer(12, { vitesse = 0.0 })
		t:egal(texte_sim(ctx), "SIM x0.00", "pause = 0.00")
		t:verifier(#ctx.erreurs == 0, "aucune erreur")
	end)

	cadre.scenario("retour en arriere du tick ou de l'horloge reelle : on repart de zero sans planter", function(t)
		local jeu, ctx = ecran_sim()
		jeu:jouer(12, { vitesse = 1.0 })
		local avant = ctx.env.g_vsim.tick0
		jeu.tick = 5                                   -- chargement d'une autre partie : le tick repart de 5
		jeu:jouer(1)
		t:verifier(ctx.env.g_vsim.tick0 ~= nil and ctx.env.g_vsim.tick0 < avant, "tick0 reinitialise")
		jeu.reel = jeu.reel - 3600                     -- l'horloge systeme recule d'une heure
		jeu:jouer(1)
		t:verifier(#ctx.erreurs == 0, "aucune erreur apres recul de l'horloge")
		t:verifier(ctx.env.g_vsim.reel0 ~= nil and math.abs(ctx.env.g_vsim.reel0 - jeu.reel) < 1, "reel0 reinitialise")
	end)

	cadre.scenario("pas la place (ecran etroit) : rien n'est dessine plutot que de deborder", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", taille = { 180, 256 } })
		ctx:monter({ ecran = "bord_controle", libs = { SCRIPT } })
		ctx:image()
		t:verifier(texte_sim(ctx) == nil, "ecran de 180 de large : pas de texte SIM")
		t:verifier(#ctx.dessin.rects == 0, "pas de fond non plus")
		t:verifier(#ctx.erreurs == 0, "aucune erreur")
		-- et a 256 : texte et fond a droite de l'horloge, dans l'ecran
		local jeu2, ctx2 = ecran_sim()
		ctx2:image()
		local r = ctx2.dessin.rects[1]
		t:verifier(r and r.x + r.w <= 256 - 4, "ecran de 256 : le fond tient dans l'ecran (a 4 unites du bord)", r and (r.x + r.w))
		t:verifier(r and r.x >= 4 + 115 + 16, "a droite du modele de l'horloge 'TEMPS DE JEU  8:88:88.8'")
	end)

	cadre.scenario("echec de dessin ou de lecture d'horloge : l'ecran d'origine continue (pcall)", function(t)
		local jeu, ctx = ecran_sim()
		ctx.erreur_dessin = "police absente"
		local ok, a, b = ctx:image()
		t:verifier(ok and a == "retour_ecran" and b == 512, "dessin en erreur : retours de l'ecran inchanges", tostring(a))
		t:verifier(#ctx.erreurs == 0, "dessin en erreur : aucune erreur remontee")
		ctx.erreur_dessin = nil
		ctx.env.update_get_logic_tick = function() error("boum") end
		ok, a = ctx:image()
		t:verifier(ok and a == "retour_ecran", "lecture du tick en erreur : retours de l'ecran inchanges")
		ctx.env.update_get_logic_tick = nil
		ok, a = ctx:image()
		t:verifier(ok and a == "retour_ecran", "fonction d'API absente : rien ne casse")
	end)

	cadre.scenario("charge deux fois dans le meme etat : une seule enveloppe", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord" })
		ctx:charger_texte("g_compte = 0 function update(...) g_compte = g_compte + 1; return 'ok' end function begin() begin_load() end", "ecran_compte")
		ctx:charger_script(SCRIPT)
		ctx:charger_script(SCRIPT)
		ctx:begin()
		ctx:image()
		t:egal(ctx.env.g_compte, 1, "l'ecran d'origine n'est appele qu'une fois par image")
		ctx:begin()                                    -- begin() relance (rechargement d'ecran) : toujours une seule enveloppe
		ctx:image()
		t:egal(ctx.env.g_compte, 2, "apres un 2e begin() : toujours une seule enveloppe")
	end)

	cadre.scenario("BUG SIM-1 : la valeur de la partie precedente reste affichee apres un retour en arriere du tick", function(t)
		t:bug("SIM-1", "apres un rechargement le script garde 'SIM x...' de l'ancienne partie pendant la 1re fenetre de 10 s", function()
			local jeu, ctx = ecran_sim()
			jeu:jouer(12, { vitesse = 2.0 })                -- ancienne partie tournant a x2
			jeu.tick = 0                                     -- nouvelle partie
			jeu:jouer(3, { vitesse = 1.0 })
			local txt = texte_sim(ctx)
			return txt == "SIM x2.00", "affiche '" .. tostring(txt) .. "' alors que la nouvelle partie n'a pas encore de mesure"
		end)
	end)
end)
