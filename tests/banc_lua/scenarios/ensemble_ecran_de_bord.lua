-- Plusieurs scripts du depot sur le MEME ecran de bord, comme dans le jeu quand plusieurs mods sont coches
-- (cc2_mesures : SIM et SORTIES ; cc2_modes : telemetrie et onglet SPEED v2). Chacun enveloppe begin_load puis update : la chaine doit marcher
-- quel que soit l'ordre de chargement, sans collision de noms globaux.
local cadre = ...
local Jeu = require("fausse_api.jeu")
local Contexte = require("fausse_api.contexte")
local C = require("fausse_api.comportements")
local O = require("fausse_api.onglet")
local A = require("fausse_api.aides")

local E = Jeu.ETAT
local L7 = "tour/lua/library_custom_7.lua"
local L9 = "tour/lua/library_custom_9.lua"
local L3 = "tour/etudes_modes_carburant/lua/library_custom_3.lua"
local V1 = "tour/etudes_modes_carburant/lua/library_custom_5.lua"
local V2 = "tour/etudes_modes_carburant/lua/v2/library_custom_5.lua"
local AUTO = "tour/auto/library_custom_5.lua"
local DEMA = "tour/etudes_demarrage_auto/demarrage_auto.lua"

local function permutations(liste)
	local r = {}
	local function rec(k)
		if k > #liste then r[#r + 1] = { table.unpack(liste) }; return end
		for i = k, #liste do
			liste[k], liste[i] = liste[i], liste[k]
			rec(k + 1)
			liste[k], liste[i] = liste[i], liste[k]
		end
	end
	rec(1)
	return r
end

local function globales_du_script(chemin, profil)
	local jeu = Jeu.nouveau()
	local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = profil or "bord", vehicule_ecran = 1, cc2x = { niveau = "0.5", plugin_modes = true } })
	ctx:charger_ecran(profil == "menu" and "menu_principal" or "bord_controle")
	local avant = A.cles(ctx.env)
	ctx:charger_script(chemin)
	local r = {}
	for _, k in ipairs(A.nouvelles_cles(avant, ctx.env)) do r[k] = true end
	return r
end

cadre.groupe("ensemble : plusieurs scripts sur le meme ecran de bord", function()

	cadre.scenario("aucune collision de noms globaux entre les scripts (sauf onglet v1 / v2, qui sont deux versions du meme)", function(t)
		local scripts = { L7, L9, L3, V1, V2, AUTO, DEMA }
		local noms = {}
		for _, s in ipairs(scripts) do noms[s] = globales_du_script(s) end
		for i = 1, #scripts do
			for j = i + 1, #scripts do
				local commun = {}
				for k in pairs(noms[scripts[i]]) do if noms[scripts[j]][k] then commun[#commun + 1] = k end end
				table.sort(commun)
				local v1v2 = (scripts[i] == V1 and scripts[j] == V2)
				if v1v2 then
					t:verifier(#commun > 0, "v1 et v2 partagent des noms (g_cm...) : ce sont deux versions d'un meme onglet, a ne pas charger ensemble")
				else
					t:egal(commun, {}, ("%s / %s : aucun nom global en commun"):format(scripts[i]:match("[^/]+/[^/]+$"), scripts[j]:match("[^/]+/[^/]+$")))
				end
			end
		end
	end)

	cadre.scenario("SIM + SORTIES + telemetrie + onglet v2 charges ensemble : toutes les permutations (24) x 2 ordres, une sortie complete", function(t)
		local mauvais = {}
		for _, ordre in ipairs({ "apres", "avant" }) do
			for _, perm in ipairs(permutations({ L7, L9, L3, V2 })) do
				local jeu = Jeu.nouveau()
				local porte, avions = C.flotte(jeu)
				C.decollage_docile(jeu)
				local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1, cc2x = { niveau = "0.5", plugin_modes = true } })
				ctx:monter({ ecran = "bord_controle", libs = perm, ordre = ordre })
				local etiquette = ordre .. ":" .. table.concat((function() local n = {}; for _, p in ipairs(perm) do n[#n + 1] = p:match("library_custom_(%d)") .. (p:find("/v2/") and "v2" or "") end return n end)(), "+")
				O.selectionner(ctx, 9)
				jeu:jouer(12, { fps = 30 })
				local v = ctx.env.update_get_map_vehicle_by_id
				for _, id in ipairs({ 9, 10 }) do
					local h = v(id); h:clear_waypoints(); h:add_waypoint(1000.0, 6000.0)
				end
				jeu:jouer(80, { fps = 30 })
				local texte_sim = ctx:texte_contenant("SIM x") ~= nil
				local texte_sorties = ctx:texte_contenant("EN L'AIR") ~= nil
				local onglet = ctx.ui:fenetre(O.TITRE) ~= nil
				local ok = #ctx.erreurs == 0 and texte_sim and texte_sorties and onglet and ctx.env.g_sorties.fini == true
				local r = ctx.dernier_retour
				ok = ok and r and r[1] == "retour_ecran" and r[2] == 512
				local telem = 0
				for _, l in ipairs(jeu.journal_cc2x) do if l:find("CC2MODES|A|", 1, true) then telem = telem + 1 end end
				ok = ok and telem > 0
				if not ok then mauvais[#mauvais + 1] = etiquette .. (" (erreurs=%s sim=%s sorties=%s onglet=%s telem=%d)"):format(tostring(ctx.erreurs[1]), tostring(texte_sim), tostring(texte_sorties), tostring(onglet), telem) end
			end
		end
		t:egal(mauvais, {}, "toutes les combinaisons fonctionnent")
	end)

	cadre.scenario("les enveloppes n'alterent pas les valeurs de retour de l'ecran quand 4 scripts sont empiles", function(t)
		local jeu = Jeu.nouveau()
		O.monde(jeu)
		local ctx = O.ecran(jeu, L7, {})
		-- ajoute les autres scripts sur le meme etat Lua
		local jeu2 = Jeu.nouveau(); O.monde(jeu2)
		local c2 = Contexte.nouveau(jeu2, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1, cc2x = { niveau = "0.5", plugin_modes = true } })
		c2:charger_texte("g_viewing_vehicle_id = 0 function update(...) g_recu = table.pack(...); return 1, nil, 3, nil end function begin() begin_load() end", "ecran_nil")
		for _, s in ipairs({ L7, L9, L3, V2 }) do c2:charger_script(s) end
		c2:begin()
		local r = c2:update_brut(300, 200, 0.5, 33.0, "p5", nil, "p7")
		t:egal({ r.n, r[2], r[3], r[4], r[5] }, { 5, 1, nil, 3, nil }, "retours (1, nil, 3, nil) conserves a travers 4 enveloppes")
		t:egal(c2.env.g_recu.n, 7, "les 7 parametres arrivent a l'ecran")
	end)

	cadre.scenario("un script qui plante ne prive pas les autres de leur affichage", function(t)
		local jeu = Jeu.nouveau()
		local porte, avions = C.flotte(jeu)
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1 })
		ctx:monter({ ecran = "bord_controle", libs = { L7, L9 } })
		-- le journal des sorties plante a chaque image : SIM doit continuer
		ctx.env.sorties_observer = function() error("boum") end
		jeu:jouer(12)
		t:verifier(ctx:texte_contenant("SIM x") ~= nil, "SIM toujours affiche")
		t:egal(#ctx.erreurs, 0, "aucune erreur remontee")
	end)

	cadre.scenario("RISQUE ENS-R1 : demarrage_auto.lua et tour/auto/library_custom_5.lua n'ont PAS le meme verrou", function(t)
		t:risque("ENS-R1", "installes ensemble dans le menu, chacun envoie sa commande (load_game a 28 s, new_game_custom a 30 s) : le verrou de l'un n'arrete pas l'autre", function()
			local jeu = Jeu.nouveau({ mods = { { id = 2, is_enabled = true, manifest = { name = "Demarrage auto" } } } })
			local ctx = Contexte.nouveau(jeu, { nom = "screen_front", profil = "menu" })
			ctx:monter({ ecran = "menu_principal", libs = { AUTO, DEMA } })
			jeu:jouer(40, { fps = 5 })
			local noms = {}
			for _, e in ipairs(jeu.evenements) do noms[#noms + 1] = e.nom end
			return #jeu.evenements == 2, "commandes : " .. table.concat(noms, ", ")
		end)
	end)

	cadre.scenario("RISQUE ENS-R3 : le panneau SORTIES (haut a droite) recouvre la fenetre LOADOUT quand les deux sont a l'ecran", function(t)
		t:risque("ENS-R3", "library_custom_9.lua l. 167 dessine son fond en (screen_w - 4 - w, 4) APRES le jeu ; LOADOUT est en (172, 10, 74 x 84) ; avec plus de 4 appareils le panneau atteint aussi SPEED (y >= 99)", function()
			local jeu = Jeu.nouveau()
			O.monde(jeu)
			local porte = jeu.vehicules[1]
			porte.baies = {}
			for i, id in ipairs({ 9, 10 }) do
				porte.baies[i - 1] = id
				local v = jeu.vehicules[id]
				v.dock_state, v.attached_parent, v.dock_parent = E.SORTIE, 1, 1
			end
			local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1, cc2x = { niveau = "0.5", plugin_modes = true } })
			ctx:monter({ ecran = "bord_controle", libs = { L9, V2 } })
			O.selectionner(ctx, 13)
			O.image(ctx)
			local fond
			for _, r in ipairs(ctx.dessin.rects) do if r.couleur.a == 210 and r.y == 4 then fond = r end end
			local lo = ctx.ui:fenetre("LOADOUT##faux")
			if not fond or not lo then return false, "fond ou LOADOUT introuvable" end
			local recouvre = fond.x < lo.x + lo.w and fond.x + fond.w > lo.x and fond.y < lo.y + lo.h and fond.y + fond.h > lo.y
			return recouvre, ("fond SORTIES (%d,%d) %dx%d ; LOADOUT (%d,%d) %dx%d"):format(fond.x, fond.y, fond.w, fond.h, lo.x, lo.y, lo.w, lo.h)
		end)
	end)
end)
