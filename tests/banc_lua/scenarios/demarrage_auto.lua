-- Scenarios de tour/etudes_demarrage_auto/demarrage_auto.lua : demarrage automatique d'une partie depuis le menu.
-- Etapes attendues (ETUDE.md) : accroche au begin_load du menu principal > lecture de l'interrupteur (mod "Demarrage auto" coche)
-- > compte a rebours affiche 30 s > UNE commande (new_game_custom, ou load_game SLOT) > message "commande envoyee" qui reste affiche.
local cadre = ...
local Jeu = require("fausse_api.jeu")
local Contexte = require("fausse_api.contexte")
local A = require("fausse_api.aides")

local SCRIPT = "tour/etudes_demarrage_auto/demarrage_auto.lua"
local VERROU = "__cc2_demarrage_auto__"
local MOD = "Demarrage auto"

local function mods(arme)
	return {
		{ id = 1, is_enabled = true, manifest = { name = "cc2_modes" } },
		{ id = 2, is_enabled = arme, manifest = { name = MOD } },
	}
end

local function jeu_arme(arme)
	return Jeu.nouveau({ mods = mods(arme ~= false) })
end

-- contexte du menu principal (celui qui definit g_is_menu_active) avec le script ; `prefixe` = lignes g_da_* ajoutees en tete (comme demarrage_auto.py)
local function menu(jeu, prefixe, opts)
	opts = opts or {}
	local ctx = Contexte.nouveau(jeu, { nom = "screen_front", profil = "menu", liaison = opts.liaison })
	ctx:monter({ ecran = opts.ecran or "menu_principal", libs = { { SCRIPT, prefixe = prefixe } }, ordre = opts.ordre })
	return ctx
end

local function compte_a_rebours(ctx)
	local t = ctx:texte_contenant("DEMARRAGE AUTO dans")
	return t and tonumber(t.texte:match("dans (%d+) s")) or nil
end

local function message_envoye(ctx)
	return ctx:texte_contenant("commande envoyee") ~= nil
end

cadre.groupe("demarrage_auto.lua : demarrage automatique depuis le menu", function()

	cadre.scenario("se charge sans erreur (4 ordres de chargement) et ne cree que ses globales g_da_* / da_*", function(t)
		for _, c in ipairs(A.COMBINAISONS) do
			local jeu = jeu_arme()
			local ctx
			local ok, err = pcall(function() ctx = menu(jeu, nil, c) end)
			t:verifier(ok, "chargement (" .. A.nom_combinaison(c) .. ")", err)
			if ok then
				jeu:jouer(1)
				t:verifier(#ctx.erreurs == 0, "aucune erreur (" .. A.nom_combinaison(c) .. ")", ctx.erreurs[1])
			end
		end
		local jeu = jeu_arme()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_front", profil = "menu" })
		ctx:charger_ecran("menu_principal")
		local avant = A.cles(ctx.env)
		ctx:charger_script(SCRIPT)
		t:egal(A.nouvelles_cles(avant, ctx.env), { "da_accrocher", "da_arme", "da_demarrer", "da_image", "g_da_begin_load_origine", "g_da_installe" }, "globales creees au chargement")
	end)

	cadre.scenario("etapes dans l'ordre : compte a rebours 30 s > UNE commande new_game_custom > message qui reste", function(t)
		local jeu = jeu_arme()
		local ctx = menu(jeu)
		local journal = {}                     -- ce qui est visible a l'ecran, une entree par seconde reelle
		for s = 0, 40 do
			ctx:image(); journal[#journal + 1] = { s = s, rebours = compte_a_rebours(ctx), envoye = message_envoye(ctx), cmds = #jeu.evenements }
			jeu:jouer(1, { fps = 1, contextes = {} })
		end
		t:egal(journal[1].rebours, 30, "t = 0 s : 'dans 30 s'")
		t:egal(journal[11].rebours, 20, "t = 10 s : 'dans 20 s'")
		t:egal(journal[30].rebours, 1, "t = 29 s : 'dans 1 s'")
		t:verifier(journal[30].cmds == 0, "aucune commande a 29 s")
		t:verifier(journal[31].cmds == 1 and journal[31].rebours == nil, "t = 30 s : la commande part et le compte a rebours disparait")
		t:verifier(journal[32].cmds == 1 and journal[32].envoye, "image suivante : le message 'commande envoyee' apparait")
		t:verifier(journal[41].cmds == 1 and journal[41].envoye, "t = 40 s : toujours UNE commande, message toujours la")
		local e = jeu.evenements[1]
		t:verifier(e and e.nom == "new_game_custom" and #e.args == 0, "commande new_game_custom sans argument", e and e.nom)
		t:egal(jeu.mot_de_passe_connexion, VERROU, "verrou pose")
		local m = ctx:texte_contenant("commande envoyee")
		t:verifier(m and m.couleur.r == 255 and m.couleur.g == 120, "message en rouge (diagnostic : s'il reste, la commande a ete ignoree)")
		t:verifier(m and m.y == 1080 - 12 and m.largeur == 1920 - 4, "message en bas de l'ecran, pleine largeur")
		t:verifier(#ctx.erreurs == 0 and #jeu.avertissements == 0, "aucune erreur ni avertissement", ctx.erreurs[1] or jeu.avertissements[1])
		jeu:jouer(300, { fps = 2 })
		t:egal(#jeu.evenements, 1, "toujours une seule commande apres 5 minutes")
	end)

	cadre.scenario("l'enveloppe de l'ecran du menu est transparente (retours conserves)", function(t)
		local jeu = jeu_arme()
		local ctx = menu(jeu)
		local ok, a = ctx:image()
		t:verifier(ok and a == "menu_ok", "update du menu : valeur de retour conservee", tostring(a))
		local r = ctx:update_brut(1920, 1080, 0, 16)
		t:verifier(r[1] and r[2] == "menu_ok", "update_brut")
	end)

	cadre.scenario("interrupteur : mod absent, decoche, liste illisible ou invalide = jamais rien", function(t)
		local cas = {
			{ "mod decoche", function(j) j.mods = mods(false) end },
			{ "mod absent", function(j) j.mods = { { id = 1, is_enabled = true, manifest = { name = "cc2_modes" } } } end },
			{ "liste vide", function(j) j.mods = {} end },
			{ "manifeste manquant", function(j) j.mods = { { id = 2, is_enabled = true } } end },
		}
		for _, c in ipairs(cas) do
			local jeu = Jeu.nouveau()
			c[2](jeu)
			local ctx = menu(jeu)
			jeu:jouer(60, { fps = 2 })
			t:egal(#jeu.evenements, 0, c[1] .. " : aucune commande")
			t:egal(#ctx.dessin.textes, 0, c[1] .. " : rien d'affiche")
			t:egal(jeu.mot_de_passe_connexion, "", c[1] .. " : verrou intact")
		end
		local jeu = jeu_arme()
		local ctx = menu(jeu)
		ctx.env.update_get_mod_details = function() error("boum") end
		jeu:jouer(60, { fps = 2 })
		t:egal(#jeu.evenements, 0, "update_get_mod_details en erreur : aucune commande")
		t:verifier(#ctx.erreurs == 0, "l'erreur est absorbee")
		jeu = jeu_arme()
		ctx = menu(jeu)
		ctx.env.update_get_mod_details = function() return "pas une table" end
		jeu:jouer(60, { fps = 2 })
		t:egal(#jeu.evenements, 0, "update_get_mod_details renvoie autre chose qu'une table : aucune commande")
	end)

	cadre.scenario("seul l'ecran qui definit g_is_menu_active est accroche (les autres 'screen_front' restent muets)", function(t)
		local jeu = jeu_arme()
		local autres = {}
		for i = 1, 3 do
			local c = Contexte.nouveau(jeu, { nom = "screen_front", profil = "menu" })
			c:monter({ ecran = "menu_secondaire", libs = { SCRIPT } })
			autres[i] = c
		end
		jeu:jouer(60, { fps = 2 })
		t:egal(#jeu.evenements, 0, "aucune commande venant d'ecrans sans g_is_menu_active")
		for i, c in ipairs(autres) do t:egal(#c.dessin.textes, 0, "ecran secondaire " .. i .. " : rien d'affiche") end
	end)

	cadre.scenario("plusieurs contextes portant g_is_menu_active : le verrou n'en laisse passer qu'un seul", function(t)
		local jeu = jeu_arme()
		local ctxs = {}
		for i = 1, 4 do ctxs[i] = menu(jeu) end
		jeu:jouer(40, { fps = 5 })
		t:egal(#jeu:evenements_nommes("new_game_custom"), 1, "une seule commande new_game_custom pour 4 contextes")
		local envoyes = 0
		for _, c in ipairs(ctxs) do if c.env.g_da_envoye then envoyes = envoyes + 1 end end
		t:egal(envoyes, 1, "un seul contexte affiche 'commande envoyee'")
	end)

	cadre.scenario("mode charger : load_game SLOT ; sauvegarde absente ou liste illisible = rien", function(t)
		local jeu = jeu_arme()
		menu(jeu, 'g_da_mode = "charger"\ng_da_slot = 19\n')
		jeu:jouer(40, { fps = 5 })
		local e = jeu.evenements[1]
		t:verifier(#jeu.evenements == 1 and e.nom == "load_game" and e.args[1] == 19, "load_game 19")
		jeu = jeu_arme()
		menu(jeu, 'g_da_mode = "charger"\ng_da_slot = 7\n')
		jeu:jouer(40, { fps = 5 })
		t:egal(#jeu.evenements, 0, "slot 7 inconnu : aucune commande")
		jeu = jeu_arme()
		local ctx = menu(jeu, 'g_da_mode = "charger"\ng_da_slot = 19\n')
		ctx.env.update_get_save_slots = function() error("boum") end
		jeu:jouer(40, { fps = 5 })
		t:egal(#jeu.evenements, 0, "update_get_save_slots en erreur : aucune commande")
		t:verifier(#ctx.erreurs == 0, "erreur absorbee")
	end)

	cadre.scenario("delai reglable (g_da_attente) et attente de l'ecran-titre (g_da_attendre_menu)", function(t)
		local jeu = jeu_arme()
		menu(jeu, "g_da_attente = 8")
		jeu:jouer(7, { fps = 5 })
		t:egal(#jeu.evenements, 0, "g_da_attente = 8 : rien a 7 s")
		jeu:jouer(2, { fps = 5 })
		t:egal(#jeu.evenements, 1, "g_da_attente = 8 : commande a 9 s")

		jeu = jeu_arme()
		local ctx = menu(jeu, "g_da_attendre_menu = true")
		jeu:jouer(100, { fps = 2 })                                 -- ecran-titre : g_is_menu_active est faux
		t:egal(#jeu.evenements, 0, "ecran-titre 100 s : aucune commande")
		t:egal(#ctx.dessin.textes, 0, "ecran-titre : pas de compte a rebours")
		ctx.env.g_is_menu_active = true                             -- une touche a ete pressee
		jeu:jouer(20, { fps = 2 })
		t:egal(#jeu.evenements, 0, "20 s apres la touche : pas encore")
		t:verifier(compte_a_rebours(ctx) ~= nil, "compte a rebours affiche apres la touche")
		jeu:jouer(12, { fps = 2 })
		t:egal(#jeu.evenements, 1, "30 s apres la touche : commande")
	end)

	cadre.scenario("horloge illisible : le compte a rebours ne demarre pas, sans erreur", function(t)
		local jeu = jeu_arme()
		local ctx = menu(jeu)
		ctx.env.update_get_time_since_epoch = function() error("boum") end
		jeu:jouer(60, { fps = 2 })
		t:egal(#jeu.evenements, 0, "aucune commande")
		t:verifier(#ctx.erreurs == 0, "aucune erreur")
		ctx.env.update_get_time_since_epoch = function() return "texte" end
		jeu:jouer(60, { fps = 2 })
		t:egal(#jeu.evenements, 0, "horloge non numerique : aucune commande")
	end)

	cadre.scenario("pas de begin_load d'origine (nil) : le script s'installe quand meme", function(t)
		local jeu = jeu_arme()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_front", profil = "menu" })
		ctx.env.begin_load = nil
		ctx:charger_ecran("menu_principal")
		ctx.env.begin_load = nil                       -- le faux ecran n'en definit pas, mais soyons surs
		local ok, err = pcall(function() ctx:charger_script(SCRIPT) end)
		t:verifier(ok, "chargement", err)
		ok, err = pcall(function() ctx.env.begin_load() end)
		t:verifier(ok, "begin_load installe appelable sans original", err)
	end)

	cadre.scenario("RISQUE DEM-R1 : l'unicite 'une partie par lancement' repose sur la survie du mot de passe de connexion", function(t)
		-- on revient au menu (nouvel etat Lua, donc g_da_fini repart a nil) : seul le verrou empeche une 2e partie.
		local jeu = jeu_arme()
		menu(jeu)
		jeu:jouer(40, { fps = 5 })
		t:egal(#jeu.evenements, 1, "premiere partie demandee")
		local retour = menu(jeu)                       -- nouveau contexte du menu, verrou intact
		jeu:jouer(40, { fps = 5 })
		t:egal(#jeu.evenements, 1, "verrou intact : pas de 2e partie")
		t:risque("DEM-R1", "si le jeu remet le mot de passe de connexion a zero en changeant de partie, un retour au menu relance une nouvelle partie", function()
			jeu.mot_de_passe_connexion = ""            -- hypothese : remis a \"\" par le jeu
			local c2 = menu(jeu)
			jeu:jouer(40, { fps = 5 })
			return #jeu.evenements == 2, #jeu.evenements .. " commande(s) au total"
		end)
	end)

	cadre.scenario("RISQUE DEM-R2 : un interrupteur lu 'absent' a la 1re image est memorise pour toujours (liste des mods incomplete au demarrage)", function(t)
		t:risque("DEM-R2", "da_arme() n'est evalue qu'une fois (demarrage_auto.lua:60-61) : si update_get_mod_details() est vide ou incomplet a la 1re image (ecran-titre), le demarrage est abandonne sans message, meme si la liste se remplit ensuite", function()
			local jeu = Jeu.nouveau({ mods = {} })
			local ctx = menu(jeu)
			jeu:jouer(1, { fps = 5 })
			jeu.mods = mods(true)                      -- la liste est enfin complete, mod coche
			jeu:jouer(60, { fps = 5 })
			return #jeu.evenements == 0 and #ctx.dessin.textes == 0, ("%d commande(s), %d texte(s) a l'ecran apres 60 s"):format(#jeu.evenements, #ctx.dessin.textes)
		end)
		local jeu = jeu_arme()
		menu(jeu)
		jeu:jouer(40, { fps = 5 })
		t:egal(#jeu.evenements, 1, "controle : liste complete des la 1re image = une commande")
	end)

	cadre.scenario("BUG DEM-1 : decocher le mod pendant le compte a rebours n'annule PAS le demarrage", function(t)
		t:bug("DEM-1", "le texte promet 'decocher le mod \"Demarrage auto\" pour annuler' mais l'interrupteur n'est lu qu'a la 1re image (g_da_arme est memorise)", function()
			local jeu = jeu_arme()
			local ctx = menu(jeu)
			jeu:jouer(5, { fps = 5 })
			local promesse = ctx:texte_contenant("decocher le mod") ~= nil
			jeu.mods[2].is_enabled = false             -- l'utilisateur decoche le mod dans le menu MODS
			jeu:jouer(30, { fps = 5 })
			return promesse and #jeu.evenements == 1, ("promesse affichee : %s ; commandes envoyees apres decochage : %d"):format(tostring(promesse), #jeu.evenements)
		end)
	end)

	cadre.scenario("BUG DEM-2 : sauvegarde absente = echec totalement silencieux (ni message, ni journal)", function(t)
		t:bug("DEM-2", "mode 'charger' avec un slot absent : le compte a rebours disparait sans aucun message d'erreur et le verrou est quand meme pose", function()
			local jeu = jeu_arme()
			local ctx = menu(jeu, 'g_da_mode = "charger"\ng_da_slot = 7\n')
			jeu:jouer(40, { fps = 5 })
			return #jeu.evenements == 0 and #ctx.dessin.textes == 0 and jeu.mot_de_passe_connexion == VERROU,
				("evenements=%d, textes a l'ecran=%d, verrou='%s'"):format(#jeu.evenements, #ctx.dessin.textes, jeu.mot_de_passe_connexion)
		end)
	end)
end)
