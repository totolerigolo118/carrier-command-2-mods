-- Scenarios de tour/auto/library_custom_5.lua : ESSAI AUTOMATIQUE (mod cc2_auto).
-- Menu : charge la sauvegarde SLOT toute seule (verrou commun = mot de passe de connexion). Partie : ordonne la sortie de 4 avions,
-- les rappelle, chronometre en ticks, affiche/ecrit le bilan, puis quitte le jeu (update_ui_event "quit_game").
local cadre = ...
local Jeu = require("fausse_api.jeu")
local Contexte = require("fausse_api.contexte")
local C = require("fausse_api.comportements")
local A = require("fausse_api.aides")

local E = Jeu.ETAT
local SCRIPT = "tour/auto/library_custom_5.lua"
local VERROU = "__cc2_auto_verrou__"

-- contexte de menu : principal = avec g_is_menu_active (le seul ecran qui le definit), sinon autre ecran du frontend (meme nom screen_front)
local function menu(jeu, principal, prefixe)
	local ctx = Contexte.nouveau(jeu, { nom = "screen_front", profil = "menu" })
	ctx:monter({ ecran = principal and "menu_principal" or "menu_secondaire", libs = { { SCRIPT, prefixe = prefixe } } })
	return ctx
end

-- ecran de bord screen_veh_m du porte-avions 1
local function bord(jeu, opts)
	opts = opts or {}
	local ctx = Contexte.nouveau(jeu, { nom = opts.nom or "screen_veh_m", profil = "bord", vehicule_ecran = (opts.sans_vehicule and nil) or opts.vehicule_ecran or 1, liaison = opts.liaison })
	ctx:monter({ ecran = "bord_controle", libs = { { SCRIPT, prefixe = opts.prefixe } }, ordre = opts.ordre })
	return ctx
end

-- enregistre les changements d'etat de g_ca.etat et verifie, a chaque image, les proprietes qui doivent toujours etre vraies
local function observateur(jeu, ctx, props)
	local o = { etats = {}, dernier = nil, mails = 0 }
	o.fonction = function()
		local g = ctx.env.g_ca
		if g.etat ~= o.dernier then
			o.etats[#o.etats + 1] = { g.etat, jeu.tick }
			o.dernier = g.etat
		end
		local mdp = jeu.mot_de_passe_hote
		if mdp then
			o.mails = o.mails + 1
			if #mdp > 480 then o.trop_long = (o.trop_long or 0) + 1 end
			if mdp:find('[<>&"]') then o.interdit = mdp end
		end
		if props and props(jeu, ctx) then return true end
		return false
	end
	return o
end

local function noms_etats(o)
	local r = {}
	for _, e in ipairs(o.etats) do r[#r + 1] = e[1] end
	return r
end

local function ordres_de(jeu, nom, id)
	local r = {}
	for _, o in ipairs(jeu.journal_ordres) do
		if o.nom == nom and (id == nil or o.id == id) then r[#r + 1] = o end
	end
	return r
end

local function mission(opts)
	opts = opts or {}
	local jeu = Jeu.nouveau()
	local porte, avions = C.flotte(jeu, opts.flotte)
	if opts.dociles ~= false then C.avions_dociles(jeu, opts.dociles) end
	local ctx = bord(jeu, opts)
	local obs = observateur(jeu, ctx, function() return ctx.env.g_ca.quit end)
	jeu:jouer_jusqu_au_tick(opts.jusqu_a or 22000, { jusqu_a = obs.fonction })
	return jeu, ctx, obs, porte, avions
end

cadre.groupe("tour/auto/library_custom_5.lua : essai automatique (menu)", function()

	cadre.scenario("se charge sans erreur dans les 4 ordres de chargement, hors double crochet", function(t)
		for _, c in ipairs(A.COMBINAISONS) do
			local jeu = Jeu.nouveau()
			local ctx = Contexte.nouveau(jeu, { nom = "screen_front", profil = "menu", liaison = c.liaison })
			local ok, err = pcall(function() ctx:monter({ ecran = "menu_principal", libs = { SCRIPT }, ordre = c.ordre }) end)
			t:verifier(ok, "chargement (" .. A.nom_combinaison(c) .. ")", err)
			jeu:jouer(1)
			t:verifier(#ctx.erreurs == 0, "aucune erreur sur 1 s (" .. A.nom_combinaison(c) .. ")", ctx.erreurs[1])
			t:egal(#jeu.evenements, 0, "aucune commande envoyee avant le delai (" .. A.nom_combinaison(c) .. ")")
		end
		-- charge deux fois : un seul crochet begin_load
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_front", profil = "menu" })
		ctx:charger_texte("g_n = 0 function update() g_n = g_n + 1 end function begin() begin_load() end g_is_menu_active = false", "menu_compte")
		ctx:charger_script(SCRIPT); ctx:charger_script(SCRIPT)
		ctx:begin()
		ctx:image()
		t:egal(ctx.env.g_n, 1, "double chargement : l'ecran d'origine n'est appele qu'une fois par image")
	end)

	cadre.scenario("menu : load_game 18 demande UNE fois, apres 28 s reelles, pas avant", function(t)
		local jeu = Jeu.nouveau()
		local ctx = menu(jeu, true)
		jeu:jouer(27, { fps = 10 })
		t:egal(#jeu.evenements, 0, "rien a 27 s")
		jeu:jouer(3, { fps = 10 })
		t:egal(#jeu.evenements, 1, "une seule commande a 30 s")
		local e = jeu.evenements[1]
		t:verifier(e and e.nom == "load_game" and e.args[1] == 18, "load_game 18", e and (e.nom .. ":" .. tostring(e.args[1])))
		t:egal(jeu.mot_de_passe_connexion, VERROU, "verrou pose dans le mot de passe de connexion")
		jeu:jouer(60, { fps = 10 })
		t:egal(#jeu.evenements, 1, "toujours une seule commande apres 90 s")
		t:egal(ctx.env.g_ca.menu, "load_game demande", "etat 'menu' du script")
		t:verifier(#ctx.erreurs == 0 and #jeu.avertissements == 0, "aucune erreur ni avertissement", ctx.erreurs[1] or jeu.avertissements[1])
	end)

	cadre.scenario("plusieurs contextes de menu : le verrou n'autorise qu'UN chargement", function(t)
		local jeu = Jeu.nouveau()
		menu(jeu, true); menu(jeu, true); menu(jeu, true); menu(jeu, false)    -- 3 contextes avec g_is_menu_active + 1 autre
		jeu:jouer(40, { fps = 10 })
		t:egal(#jeu:evenements_nommes("load_game"), 1, "un seul load_game parmi 4 contextes")
	end)

	cadre.scenario("verrou deja pris par un autre contexte / script : aucune commande", function(t)
		local jeu = Jeu.nouveau()
		jeu.mot_de_passe_connexion = VERROU
		menu(jeu, true)
		jeu:jouer(40, { fps = 10 })
		t:egal(#jeu.evenements, 0, "aucune commande")
	end)

	cadre.scenario("sauvegarde absente, illisible, ou autre numero choisi (g_ca_slot_voulu)", function(t)
		local jeu = Jeu.nouveau({ sauvegardes = { { slot_index = 3 }, { slot_index = 19 } } })
		local ctx = menu(jeu, true)
		jeu:jouer(40, { fps = 10 })
		t:egal(#jeu.evenements, 0, "slot 18 absent : aucune commande")
		t:egal(ctx.env.g_ca.menu, "slot 18 absent", "diagnostic affiche")
		jeu = Jeu.nouveau({ sauvegardes = { { slot_index = 3 }, { slot_index = 19 } } })
		menu(jeu, true, "g_ca_slot_voulu = 19")
		jeu:jouer(40, { fps = 10 })
		local e = jeu.evenements[1]
		t:verifier(e and e.nom == "load_game" and e.args[1] == 19, "g_ca_slot_voulu = 19 : load_game 19")
		jeu = Jeu.nouveau()
		local c3 = Contexte.nouveau(jeu, { nom = "screen_front", profil = "menu" })
		c3:monter({ ecran = "menu_principal", libs = { SCRIPT } })
		c3.env.update_get_save_slots = function() error("boum") end
		jeu:jouer(40, { fps = 10 })
		t:egal(#jeu.evenements, 0, "update_get_save_slots en erreur : aucune commande")
		t:egal(c3.env.g_ca.menu, "slots illisibles", "diagnostic")
		t:verifier(#c3.erreurs == 0, "l'erreur est absorbee (pas de plantage de l'ecran)")
		jeu = Jeu.nouveau()
		menu(jeu, true, "g_ca_attente_menu = 5")
		jeu:jouer(6, { fps = 10 })
		t:egal(#jeu.evenements, 1, "g_ca_attente_menu = 5 : commande a 5 s")
	end)

	cadre.scenario("mode menu_seul : aucune accroche en partie, mais le chargement du menu marche", function(t)
		local jeu = Jeu.nouveau()
		local ctx = bord(jeu, { prefixe = "g_ca_mode = 'menu_seul'" })
		t:verifier(ctx.env.g_ca_accroche ~= true, "ecran de bord : pas accroche")
		t:verifier(getmetatable(ctx.env) == nil, "pas de surveillance de la globale update (pas de metatable)")
		jeu = Jeu.nouveau()
		local m = menu(jeu, true, "g_ca_mode = 'menu_seul'")
		jeu:jouer(30, { fps = 10 })
		t:egal(#jeu:evenements_nommes("load_game"), 1, "menu_seul : load_game demande")
	end)

	cadre.scenario("BUG AUTO-1 : bande rouge de calibrage (AFFICHER_NOMS = true) dessinee en bas de TOUS les ecrans accroches", function(t)
		t:bug("AUTO-1", "AFFICHER_NOMS = true : un rectangle rouge (200, 0, 0) et un texte 'ca[...]' sont dessines sur chaque ecran, comme au calibrage", function()
			local jeu = Jeu.nouveau()
			local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_l", profil = "bord", vehicule_ecran = 1 })
			ctx:monter({ ecran = "bord_controle", libs = { SCRIPT } })
			ctx:image()
			local rouge
			for _, r in ipairs(ctx.dessin.rects) do if r.couleur.r == 200 and r.couleur.g == 0 and r.couleur.b == 0 then rouge = r end end
			local nom = ctx:texte_contenant("ca[")
			return rouge ~= nil and nom ~= nil, rouge and ("rectangle " .. rouge.w .. "x" .. rouge.h .. " en bas, texte '" .. (nom and nom.texte or "?") .. "'")
		end)
	end)
end)

cadre.groupe("tour/auto/library_custom_5.lua : essai automatique (partie)", function()

	cadre.scenario("mission complete : attente > sortie > retour > fin, ordres exacts, une seule commande quit_game", function(t)
		local jeu, ctx, obs = mission()
		local g = ctx.env.g_ca
		t:egal(noms_etats(obs), { "attente", "sortie", "retour", "fin" }, "etapes dans l'ordre")
		t:egal(obs.etats[2][2], 1800, "la sortie est ordonnee des le tick 1800 (ATTENTE_JEU)")
		t:egal(#g.rec, 4, "4 avions suivis")
		-- ordres de sortie : clear_waypoints, clear_attack_target, add_waypoint(x, z + 4000)
		for _, id in ipairs({ 9, 10, 17, 18 }) do
			local ajouts = ordres_de(jeu, "add_waypoint", id)
			t:egal(#ajouts, 2, ("avion %d : 2 add_waypoint (sortie, rappel)"):format(id))
			t:egal({ ajouts[1].tick, ajouts[1].args[1], ajouts[1].args[2] }, { 1800, 1000.0, 6000.0 }, ("avion %d : sortie vers (x, z + 4000)"):format(id))
			t:egal({ ajouts[2].args[1], ajouts[2].args[2] }, { 1000.0, 2000.0 }, ("avion %d : rappel sur la position du porte-avions"):format(id))
			local cibles = ordres_de(jeu, "set_target_vehicle", id)
			t:verifier(#cibles == 1 and cibles[1].args[2] == 1, ("avion %d : rappel = set_target_vehicle(waypoint, porte-avions 1)"):format(id))
			t:verifier(cibles[1] and cibles[1].tick == g.t_rappel, ("avion %d : rappel donne au tick t_rappel"):format(id))
		end
		t:verifier(g.t_rappel and g.t_rappel >= 5848 and g.t_rappel <= 5850, "rappel quand le 4e est en l'air (tick ~5848)", g.t_rappel)
		for _, a in ipairs(g.rec) do
			t:verifier(a.t_demande and a.t_sortie and a.t_air and a.t_file and a.t_piste and a.t_pont and a.t_hangar, ("avion %d : tous les jalons notes"):format(a.id))
			t:verifier(a.t_demande <= a.t_sortie and a.t_sortie <= a.t_air and a.t_air <= a.t_file and a.t_file <= a.t_piste and a.t_piste <= a.t_pont and a.t_pont <= a.t_hangar,
				("avion %d : jalons dans l'ordre chronologique"):format(a.id))
		end
		t:egal(g.message, "retours termines", "fin normale")
		local sortie, retour = ctx.env.ca_bilan()
		t:verifier(sortie and math.abs(sortie - 4048) <= 2, "bilan : sortie de 4 avions en ~4048 ticks (2:15)", sortie)
		t:verifier(retour and math.abs(retour - 11790) <= 2, "bilan : retour en ~11790 ticks", retour)
		-- quit_game : une seule fois, apres le maintien
		local q = jeu:evenements_nommes("quit_game")
		t:egal(#q, 1, "quit_game envoye une seule fois")
		t:verifier(q[1] and q[1].tick > g.t_fin + 1500 and q[1].tick <= g.t_fin + 1502, "quit_game 1500 ticks apres la fin", q[1] and (q[1].tick - g.t_fin))
		t:verifier(#ctx.erreurs == 0 and not g.err, "aucune erreur", ctx.erreurs[1] or g.err)
		t:verifier(#jeu.avertissements == 0, "aucun avertissement de la fausse API", jeu.avertissements[1])
		t:verifier(not obs.trop_long, "boite aux lettres : jamais plus de 480 caracteres")
		t:verifier(obs.interdit == nil, "boite aux lettres : aucun caractere < > & \" (le mot de passe est ecrit dans un XML)", obs.interdit)
		t:verifier(obs.mails > 1000, "boite aux lettres mise a jour a chaque image")
	end)

	cadre.scenario("piege de Lua 5.3 : tick renvoye en flottant a valeur entiere : meme mission, aucune erreur", function(t)
		local jeu = Jeu.nouveau()
		C.flotte(jeu); C.avions_dociles(jeu)
		local ctx = bord(jeu)
		ctx.env.update_get_logic_tick = function() return jeu.tick + 0.0 end
		local obs = observateur(jeu, ctx, function() return ctx.env.g_ca.quit end)
		jeu:jouer_jusqu_au_tick(22000, { jusqu_a = obs.fonction })
		t:egal(noms_etats(obs), { "attente", "sortie", "retour", "fin" }, "memes etapes")
		t:verifier(not ctx.env.g_ca.err and #ctx.erreurs == 0, "aucune erreur", ctx.env.g_ca.err or ctx.erreurs[1])
		t:egal(#jeu:evenements_nommes("quit_game"), 1, "quit_game une fois")
	end)

	cadre.scenario("messages du chat : au plus 120 caracteres, jamais plus d'un paquet toutes les 5 s de jeu", function(t)
		local jeu, ctx = mission()
		local par_tick, trop_longs, max_paquet = {}, 0, 0
		for _, e in ipairs(jeu:evenements_nommes("chat")) do
			par_tick[e.tick] = (par_tick[e.tick] or 0) + 1
			if #e.args[1] > 120 then trop_longs = trop_longs + 1 end
		end
		local ticks = {}
		for tk, n in pairs(par_tick) do ticks[#ticks + 1] = tk; if n > max_paquet then max_paquet = n end end
		table.sort(ticks)
		local ecart_min = math.huge
		for i = 2, #ticks do ecart_min = math.min(ecart_min, ticks[i] - ticks[i - 1]) end
		t:egal(trop_longs, 0, "aucun message de plus de 120 caracteres")
		t:verifier(ecart_min >= 150, "au moins 150 ticks (5 s) entre deux paquets de messages", ecart_min)
		t:verifier(max_paquet <= 12, "paquet de messages raisonnable (<= 12)", max_paquet)
		t:verifier(#ticks > 100, "le chat sert bien de canal de suivi", #ticks)
	end)

	cadre.scenario("fonctionne dans les 4 ordres de chargement", function(t)
		for _, c in ipairs(A.COMBINAISONS) do
			local jeu, ctx, obs = mission({ ordre = c.ordre, liaison = c.liaison, jusqu_a = 9000 })
			t:egal(noms_etats(obs), { "attente", "sortie", "retour" }, "etapes (" .. A.nom_combinaison(c) .. ")")
			t:verifier(#ctx.erreurs == 0, "aucune erreur (" .. A.nom_combinaison(c) .. ")", ctx.erreurs[1])
		end
	end)

	cadre.scenario("six avions en baie : seuls les 4 premiers sont envoyes ; helicopteres et avions deja sortis ignores", function(t)
		local jeu = Jeu.nouveau()
		local porte, avions = C.flotte(jeu, { ids = { 9, 10, 17, 18, 21, 22 }, defs = { 8, 8, 10, 10, 8, 8 } })
		porte.baies[6] = 30
		jeu:ajouter({ id = 30, def = Jeu.DEFS.chassis_air_rotor_light, dock_state = E.HANGAR, dock_parent = 1, attached_parent = 1 })
		avions[2].dock_state = E.VOL                    -- le 2e avion est deja dehors
		C.avions_dociles(jeu)
		local ctx = bord(jeu)
		jeu:jouer_jusqu_au_tick(1900)
		local ids = {}
		for _, a in ipairs(ctx.env.g_ca.rec) do ids[#ids + 1] = a.id end
		t:egal(ids, { 9, 17, 18, 21 }, "les 4 premiers avions de BAIE en etat hangar (l'helico et l'avion deja en vol sont sautes)")
	end)

	cadre.scenario("ecrans des autres porte-avions : passifs (le plus petit identifiant de l'equipe commande) ; une autre equipe ne compte pas", function(t)
		local jeu = Jeu.nouveau()
		local porte, avions = C.flotte(jeu, { id_porte = 5, ids = { 9, 10, 17, 18 } })
		jeu:ajouter({ id = 2, def = Jeu.DEFS.chassis_carrier, team = 2 })              -- porte-avions ennemi, id plus petit : ignore
		jeu:ajouter({ id = 7, def = Jeu.DEFS.chassis_carrier, team = 1, baies = {} })   -- autre porte-avions allie, id plus grand
		C.avions_dociles(jeu)
		local c5 = bord(jeu, { vehicule_ecran = 5 })
		local c7 = bord(jeu, { vehicule_ecran = 7 })
		jeu:jouer_jusqu_au_tick(2000)
		t:egal(c5.env.g_ca.etat, "sortie", "l'ecran du porte-avions 5 (le plus petit allie) commande")
		t:egal(c7.env.g_ca.etat, "passif", "l'ecran du porte-avions 7 reste passif")
		t:egal(#ordres_de(jeu, "add_waypoint"), 4, "4 ordres seulement (pas de doublon entre les ecrans)")
	end)

	cadre.scenario("aucun avion en baie : echec apres 3000 ticks, puis quit_game", function(t)
		local jeu = Jeu.nouveau()
		jeu:ajouter({ id = 1, def = Jeu.DEFS.chassis_carrier, baies = {} })
		local ctx = bord(jeu)
		local obs = observateur(jeu, ctx, function() return ctx.env.g_ca.quit end)
		jeu:jouer_jusqu_au_tick(6000, { jusqu_a = obs.fonction })
		local g = ctx.env.g_ca
		t:egal(noms_etats(obs), { "attente", "echec" }, "attente puis echec")
		t:verifier(g.t_fin and g.t_fin > 3000 and g.t_fin <= 3030, "echec juste apres 3000 ticks (la recherche a lieu toutes les 30 ticks)", g.t_fin)
		t:egal(g.message, "aucun avion en baie trouve", "message")
		t:egal(#jeu.journal_ordres, 0, "aucun ordre donne")
		t:egal(#jeu:evenements_nommes("quit_game"), 1, "quit_game apres le maintien")
	end)

	cadre.scenario("ordres refuses (tous) : echec immediat, erreur memorisee", function(t)
		local jeu = Jeu.nouveau()
		C.flotte(jeu)
		jeu.refuser_ordres = true
		local ctx = bord(jeu)
		jeu:jouer_jusqu_au_tick(1900)
		local g = ctx.env.g_ca
		t:egal(g.etat, "echec", "echec")
		t:egal(g.message, "tous les ordres de sortie refuses depuis cette couche", "message")
		t:verifier(g.err and g.err:find("ordre refuse"), "erreur memorisee", g.err)
		t:verifier(#ctx.erreurs == 0, "aucune erreur remontee a l'ecran")
	end)

	cadre.scenario("les avions ne quittent pas le hangar (constat du 27/10) : ordre renouvele toutes les 20 s, 8 fois, puis echec", function(t)
		local jeu = Jeu.nouveau()
		C.flotte(jeu)                                          -- avions SANS comportement : ils restent au hangar
		local ctx = bord(jeu)
		local obs = observateur(jeu, ctx, function() return ctx.env.g_ca.etat == "echec" end)
		jeu:jouer_jusqu_au_tick(20000, { jusqu_a = obs.fonction })
		local g = ctx.env.g_ca
		t:egal(noms_etats(obs), { "attente", "sortie", "echec" }, "attente, sortie, echec")
		t:egal(#ordres_de(jeu, "add_waypoint", 9), 9, "1 ordre initial + 8 renouvellements")
		local ordres = ordres_de(jeu, "add_waypoint", 9)
		t:egal(ordres[2].tick - ordres[1].tick >= 600 and ordres[2].tick - ordres[1].tick <= 601, true, "renouvelement 600 ticks (20 s) apres")
		t:egal(g.message, "sortie : tous les avions ne sont pas en l'air a temps", "message d'echec")
		-- DELAI_SORTIE (9000) compte depuis le DERNIER ordre (t_cmd est remis a jour) : 1800 + 8 * 600 + 9000
		t:verifier(g.t_fin >= 15600 and g.t_fin <= 15640, "echec 9000 ticks apres le dernier renouvellement (tick ~15600)", g.t_fin)
		for _, id in ipairs({ 9, 10, 17, 18 }) do
			t:egal(#jeu.vehicules[id].waypoints, 1, ("avion %d : toujours UN seul waypoint (clear_waypoints avant chaque ordre)"):format(id))
		end
	end)

	cadre.scenario("un seul ordre refuse sur 4 : la sortie continue puis echoue au delai ; les 3 avions sortis ne sont PAS rappeles", function(t)
		local jeu = Jeu.nouveau()
		C.flotte(jeu)
		C.avions_dociles(jeu)
		jeu.refuser_ids = { [18] = true }
		local ctx = bord(jeu)
		local obs = observateur(jeu, ctx, function() return ctx.env.g_ca.quit end)
		jeu:jouer_jusqu_au_tick(14000, { jusqu_a = obs.fonction })
		local g = ctx.env.g_ca
		t:egal(noms_etats(obs), { "attente", "sortie", "echec" }, "etapes")
		t:egal(g.message, "sortie : tous les avions ne sont pas en l'air a temps", "echec au delai (le 4e avion n'a jamais recu d'ordre)")
		t:egal(#ordres_de(jeu, "set_target_vehicle"), 0, "aucun rappel des 3 avions deja en l'air")
		t:risque("AUTO-R2", "apres un echec de sortie les avions deja sortis restent en vol (aucun rappel)", function()
			local en_vol = 0
			for _, id in ipairs({ 9, 10, 17 }) do if jeu.vehicules[id].dock_state == E.VOL then en_vol = en_vol + 1 end end
			return en_vol == 3, en_vol .. " avion(s) encore en l'air a la fin de l'essai"
		end)
	end)

	cadre.scenario("erreur interne pendant le suivi : memorisee (g_ca.err), affichee, l'ecran du jeu continue et le chat la signale", function(t)
		local jeu = Jeu.nouveau()
		C.flotte(jeu); C.avions_dociles(jeu)
		local ctx = bord(jeu)
		jeu:jouer_jusqu_au_tick(1850)
		t:egal(ctx.env.g_ca.etat, "sortie", "la sortie est lancee")
		local vrai = ctx.env.update_get_map_vehicle_by_id
		ctx.env.update_get_map_vehicle_by_id = function(id)
			local h = vrai(id)
			return setmetatable({ get_dock_state = function() error("etat illisible") end }, { __index = h })
		end
		local ok, a = ctx:image()
		jeu:avancer(1 / 30)
		ok, a = ctx:image()
		t:verifier(ok and a == "retour_ecran", "update de l'ecran du jeu : retours conserves")
		local g = ctx.env.g_ca
		t:verifier(g.err and g.err:find("^erreur : "), "erreur memorisee avec le prefixe 'erreur :'", g.err)
		t:verifier(ctx:texte_contenant("erreur :") ~= nil, "affichee dans le panneau")
		jeu:jouer(20)                                     -- le detail (avec 'CA ERR') part un paquet sur trois, soit toutes les 15 s de jeu
		local signale = false
		for _, e in ipairs(jeu:evenements_nommes("chat")) do if e.args[1]:find("CA ERR", 1, true) then signale = true end end
		t:verifier(signale, "signalee dans le chat du jeu")
		t:verifier(#ctx.erreurs == 0, "aucune erreur remontee a l'ecran")
	end)

	cadre.scenario("RISQUE AUTO-R3 : le mot de passe d'hebergement (enregistre dans persistent_data.xml) change a CHAQUE image", function(t)
		t:risque("AUTO-R3", "ca_mail() appelle update_set_host_password a chaque image avec un texte qui contient le tick : ~30 valeurs differentes par seconde ; si le jeu reecrit persistent_data.xml a chaque changement, c'est une ecriture disque par image (jamais verifie en partie)", function()
			local jeu = Jeu.nouveau()
			C.flotte(jeu); C.avions_dociles(jeu)
			bord(jeu)
			jeu:jouer(10)
			local par_s = (jeu.changements_mdp_hote or 0) / 10
			return par_s >= 25, ("%d changements en 10 s reelles de jeu, soit %.0f par seconde"):format(jeu.changements_mdp_hote or 0, par_s)
		end)
	end)

	cadre.scenario("equipe du joueur : repli sur l'unique pair ; inconnue = aucun ordre", function(t)
		local jeu = Jeu.nouveau()
		C.flotte(jeu); C.avions_dociles(jeu)
		local ctx = bord(jeu, { vehicule_ecran = 1 })
		ctx.env.update_get_screen_team_id = nil
		jeu:jouer_jusqu_au_tick(1900)
		t:egal(ctx.env.g_ca.etat, "sortie", "update_get_screen_team_id absent : repli sur le pair unique, la sortie est ordonnee")
		t:verifier(ctx.env.g_ca.info:find("joueur", 1, true), "source 'joueur' indiquee", ctx.env.g_ca.info)

		jeu = Jeu.nouveau({ pairs_reseau = { { equipe = 1 }, { equipe = 2 } } })
		C.flotte(jeu)
		ctx = bord(jeu, { vehicule_ecran = 1 })
		ctx.env.update_get_screen_team_id = nil
		jeu:jouer_jusqu_au_tick(3100)
		t:egal(#jeu.journal_ordres, 0, "deux pairs et pas d'equipe d'ecran : AUCUN ordre (jamais de supposition)")
		t:verifier(ctx.env.g_ca.info:find("inconnue", 1, true), "cause indiquee", ctx.env.g_ca.info)
		t:egal(ctx.env.g_ca.etat, "echec", "echec apres 3000 ticks")
	end)

	cadre.scenario("BUG AUTO-2 : une lecture transitoire invalide du vehicule d'ecran a 1800 ticks rend l'ecran 'passif' pour toujours", function(t)
		t:bug("AUTO-2", "etat 'passif' non reversible : si update_get_screen_vehicle():get() est faux au tick 1800, ca_est_chef() renvoie false sans le memoriser, mais l'etat passe a 'passif' et ca_pas() ne tourne plus jamais", function()
			local jeu = Jeu.nouveau()
			C.flotte(jeu); C.avions_dociles(jeu)
			local ctx = bord(jeu, { vehicule_ecran = 99 })     -- vehicule d'ecran momentanement invalide (id inexistant)
			jeu:jouer_jusqu_au_tick(1850)
			ctx.vehicule_ecran = 1                             -- l'ecran retrouve son porte-avions
			jeu:jouer_jusqu_au_tick(4000)
			return ctx.env.g_ca.etat == "passif" and #jeu.journal_ordres == 0, "etat final '" .. tostring(ctx.env.g_ca.etat) .. "', " .. #jeu.journal_ordres .. " ordre(s) donne(s)"
		end)
	end)
end)

cadre.groupe("tour/auto/library_custom_5.lua : essai automatique (couche overlay et ecran d'indications)", function()

	local function overlay(jeu, ordre, prefixe)
		local ctx = Contexte.nouveau(jeu, { nom = "overlay", profil = "overlay" })
		ctx:monter({ ecran = "overlay", libs = { { SCRIPT, prefixe = prefixe } }, ordre = ordre, commencer = false })
		return ctx
	end

	cadre.scenario("overlay : l'update est enveloppee quelle que soit la place du script (avant ou apres), puis la surveillance se retire", function(t)
		for _, ordre in ipairs({ "avant", "apres" }) do
			local jeu = Jeu.nouveau()
			local ctx = overlay(jeu, ordre)
			t:verifier(ctx.env.g_ca_accroche == true, "overlay accroche (libs " .. ordre .. ")")
			t:verifier(getmetatable(ctx.env) == nil, "metatable de surveillance retiree (libs " .. ordre .. ")")
			local ok = ctx:image()
			t:verifier(ok and ctx.env.g_appels_overlay == 1, "update d'origine appelee (libs " .. ordre .. ")")
			t:verifier(#ctx.dessin.textes > 0, "panneau dessine (libs " .. ordre .. ")")
			t:verifier(#ctx.erreurs == 0, "aucune erreur (libs " .. ordre .. ")", ctx.erreurs[1])
			t:verifier(#jeu.evenements == 0, "aucune commande depuis l'overlay (il n'a pas l'API du monde)")
		end
	end)

	cadre.scenario("overlay : la couche n'est forcee visible qu'apres avoir vu un chargement finir + 300 images", function(t)
		local jeu = Jeu.nouveau()
		local ctx = overlay(jeu, "avant")
		for _ = 1, 400 do ctx:image() end
		t:egal(ctx.visible, false, "sans chargement vu : jamais forcee (le jeu la cache lui-meme)")
		ctx.env.g_is_loading = true
		for _ = 1, 3 do ctx:image() end
		ctx.env.g_is_loading = false
		for _ = 1, 300 do ctx:image() end
		t:egal(ctx.visible, false, "300 images apres la fin du chargement : pas encore")
		ctx:image(); ctx:image()
		t:egal(ctx.visible, true, "au-dela de 300 images : forcee visible")
	end)

	cadre.scenario("BUG AUTO-3 : le panneau de l'overlay affiche 'attente tick 0' en permanence, force visible", function(t)
		t:bug("AUTO-3", "l'overlay n'a pas l'API du monde (mesure du 27/10, commentaire l. 349-350) donc ca_pas n'y tourne jamais, mais le panneau y est dessine et force visible a chaque image", function()
			local jeu = Jeu.nouveau()
			local ctx = overlay(jeu, "avant")
			ctx.env.g_is_loading = true
			for _ = 1, 3 do ctx:image() end
			ctx.env.g_is_loading = false
			for _ = 1, 310 do jeu:avancer(1 / 30); ctx:image() end
			local l1 = ctx:textes()[1] or ""
			return ctx.visible == true and l1:find("ESSAI AUTO cc2_auto : attente   tick 0", 1, true) ~= nil, "visible=" .. tostring(ctx.visible) .. ", 1re ligne : '" .. l1 .. "'"
		end)
	end)

	cadre.scenario("RISQUE AUTO-R4 : si quit_game est ignore, le chat recoit un paquet de messages toutes les 5 s indefiniment", function(t)
		t:risque("AUTO-R4", "apres s.quit = true l'etat reste fin/echec, donc ca_chat() continue d'envoyer le detail complet toutes les 150 ticks tant que le jeu ne se ferme pas (le faux quit_game n'a aucun effet de jeu, comme un quit_game refuse)", function()
			local jeu = Jeu.nouveau()
			jeu:ajouter({ id = 1, def = Jeu.DEFS.chassis_carrier, baies = {} })      -- aucun avion : echec vers 3000 ticks
			local ctx = bord(jeu)
			jeu:jouer_jusqu_au_tick(4700)
			local q = jeu:evenements_nommes("quit_game")
			if #q ~= 1 then return false, "quit_game non envoye (" .. #q .. ")" end
			jeu:jouer_jusqu_au_tick(q[1].tick + 3000)                                 -- 100 s de jeu de plus : le jeu est toujours la
			local ticks, total = {}, 0
			for _, e in ipairs(jeu:evenements_nommes("chat")) do
				if e.tick > q[1].tick then ticks[e.tick] = true; total = total + 1 end
			end
			local paquets = 0
			for _ in pairs(ticks) do paquets = paquets + 1 end
			return paquets >= 19, ("%d paquets de chat (%d messages) dans les 100 s qui suivent quit_game"):format(paquets, total)
		end)
	end)

	cadre.scenario("script charge AVANT un ecran ordinaire : la surveillance de 'update' se retire sans rien envelopper", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1 })
		ctx:monter({ ecran = "bord_controle", libs = { SCRIPT }, ordre = "avant" })
		t:verifier(getmetatable(ctx.env) == nil, "metatable retiree apres la definition de update")
		t:verifier(rawget(ctx.env, "update") ~= nil, "update definie")
		t:verifier(ctx.env.g_ca_accroche == true, "accroche ensuite par begin_load (ecran de bord)")
	end)

	cadre.scenario("RISQUE AUTO-R1 : branche HUD (g_ca_hud = true) : ca_image recoit tick_fraction a la place de delta_time", function(t)
		t:risque("AUTO-R1", "HUD : update = function(screen_w, screen_h, delta_time, ...) transmet le 3e parametre ; si l'ecran d'indications a la signature (w, h, tick_fraction, delta_time) comme l'overlay, le chrono s.ms n'avance presque pas", function()
			local jeu = Jeu.nouveau()
			local ctx = Contexte.nouveau(jeu, { nom = "?", profil = "hud" })
			ctx:monter({ ecran = "indications", libs = { { SCRIPT, prefixe = "g_ca_hud = true" } } })
			for _ = 1, 300 do jeu:avancer(1 / 30); ctx:image(1 / 30) end        -- 10 s reelles
			local ms = ctx.env.g_ca.ms
			return ms < 1000, ("apres 10 s reelles, s.ms = %.1f (devrait valoir ~10000)"):format(ms)
		end)
	end)

	cadre.scenario("ecran d'indications avec g_ca_hud = false (defaut) : pas d'enveloppe", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "?", profil = "hud" })
		ctx:monter({ ecran = "indications", libs = { SCRIPT } })
		jeu:jouer(2)
		t:verifier(#ctx.erreurs == 0, "aucune erreur")
		t:egal(ctx.env.g_appels_indications, ctx.images, "l'ecran d'origine est appele a chaque image")
	end)
end)
