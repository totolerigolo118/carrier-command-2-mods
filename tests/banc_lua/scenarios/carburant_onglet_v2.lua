-- Scenarios de tour/etudes_modes_carburant/lua/v2/library_custom_5.lua : onglet SPEED v2, branche sur le plugin cc2x_modes.dll (v3).
-- Le script envoie au plugin cc2x.modes.set(id, mode) avec mode 0 NORMAL / 1 ECO / 2 FLANK, et cc2x.modes.hold(id) a chaque image tant que
-- l'ecran montre un vehicule (garde-fou "le joueur pilote"). Ce que le banc verifie : ce qui est ENVOYE (types, bornes, correspondance des boutons),
-- l'affichage et la reprise sur erreur. Ce que le plugin FAIT des gaz dans le moteur n'est pas verifiable ici.
local cadre = ...
local Jeu = require("fausse_api.jeu")
local Contexte = require("fausse_api.contexte")
local Cc2x = require("fausse_api.cc2x")
local O = require("fausse_api.onglet")
local A = require("fausse_api.aides")

local SCRIPT = "tour/etudes_modes_carburant/lua/v2/library_custom_5.lua"
local ORANGE, VERT = { 255, 176, 32 }, { 16, 255, 127 }

local function nouveau(opts_cc2x, opts)
	local jeu = Jeu.nouveau()
	O.monde(jeu)
	opts = opts or {}
	opts.cc2x = opts_cc2x
	local ctx = O.ecran(jeu, SCRIPT, opts)
	return jeu, ctx
end

local PLUGIN = { niveau = "0.5", plugin_modes = true }

local function appels(ctx, nom)
	local r = {}
	for _, a in ipairs(ctx.cc2x.appels_modes) do if a[1] == nom then r[#r + 1] = a end end
	return r
end

local function lit(ctx) return ctx.cc2x.plugin end

local function rgb(c) return c and { c.r, c.g, c.b } or nil end

-- texte d'etat (premiere ligne sous les boutons) et son rgb
local function etat(ctx)
	local f = O.fenetre(ctx)
	if not f then return nil end
	for i, tx in ipairs(f.textes) do
		if not tx:find("AUTONOMIE", 1, true) then return tx, rgb(f.couleurs[i]) end
	end
end

local function autonomie(ctx)
	local f = O.fenetre(ctx)
	if not f then return nil end
	for _, tx in ipairs(f.textes) do if tx:find("AUTONOMIE", 1, true) then return tx end end
end

cadre.groupe("onglet SPEED v2 (branche sur le plugin) : lua/v2/library_custom_5.lua", function()

	cadre.scenario("se charge sans erreur (4 ordres de chargement x 3 etats du SDK) et affiche l'onglet", function(t)
		for _, c in ipairs(A.COMBINAISONS) do
			for _, cas in ipairs({ { "sans cc2x", nil }, { "cc2x sans plugin", { niveau = "0.5" } }, { "avec plugin", PLUGIN } }) do
				local jeu = Jeu.nouveau()
				O.monde(jeu)
				local ctx
				local ok, err = pcall(function() ctx = O.ecran(jeu, SCRIPT, { cc2x = cas[2], ordre = c.ordre, liaison = c.liaison }) end)
				t:verifier(ok, ("%s : chargement (%s)"):format(cas[1], A.nom_combinaison(c)), err)
				if ok then
					O.selectionner(ctx, 9)
					O.image(ctx)
					t:verifier(O.fenetre(ctx) ~= nil and #ctx.erreurs == 0 and not ctx.env.g_cm.casse, ("%s : onglet dessine, aucune erreur (%s)"):format(cas[1], A.nom_combinaison(c)), ctx.erreurs[1])
				end
			end
		end
	end)

	cadre.scenario("ne cree que ses globales g_cm / g_cm_*", function(t)
		local jeu = Jeu.nouveau()
		O.monde(jeu)
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1, cc2x = PLUGIN })
		ctx:charger_ecran("bord_controle")
		local avant = A.cles(ctx.env)
		ctx:charger_script(SCRIPT)
		t:egal(A.nouvelles_cles(avant, ctx.env), { "g_cm", "g_cm_ui_begin_load", "g_cm_ui_enveloppe" }, "globales creees au chargement")
		ctx:begin()
		local apres = {}
		for _, k in ipairs(A.nouvelles_cles(avant, ctx.env)) do if k:sub(1, 5) == "g_cm_" then apres[#apres + 1] = k end end
		t:egal(apres, { "g_cm_ui_begin_load", "g_cm_ui_enveloppe", "g_cm_update_enveloppe" }, "globales g_cm_* apres begin()")
	end)

	cadre.scenario("sans plugin : MAQUETTE SANS EFFET, rien n'est envoye, pas de ligne d'autonomie", function(t)
		for _, cas in ipairs({ { "sans cc2x", nil }, { "cc2x sans plugin", { niveau = "0.5" } }, { "plugin v1 (set seul)", { niveau = "0.5", plugin_modes = true, plugin_v1 = true } } }) do
			local jeu, ctx = nouveau(cas[2])
			O.selectionner(ctx, 9)
			O.image(ctx)
			t:egal(O.fenetre(ctx).textes, { "MAQUETTE : SANS EFFET" }, cas[1] .. " : texte MAQUETTE, pas d'autonomie")
			O.cliquer(ctx, 1)
			t:egal(O.bouton_allume(ctx), 1, cas[1] .. " : le choix est memorise dans l'ecran")
			t:egal(ctx.env.g_cm.modes, { [9] = 1 }, cas[1] .. " : memorise par avion")
			t:egal(#((ctx.cc2x and ctx.cc2x.appels_modes) or {}), 0, cas[1] .. " : aucun appel au plugin")
			t:verifier(#jeu.evenements == 0 and #jeu.journal_ordres == 0, cas[1] .. " : rien envoye au jeu")
		end
	end)

	cadre.scenario("avec plugin : ECO > set(id, 1), NORMAL > set(id, 0), FLANK > set(id, 2) ; l'etat affiche vient du plugin", function(t)
		local jeu, ctx = nouveau(PLUGIN)
		O.selectionner(ctx, 9)
		O.image(ctx)
		t:egal(O.bouton_allume(ctx), 2, "NORMAL allume au depart (mode 0 du plugin)")
		for _, cas in ipairs({ { 1, 1, "ECO" }, { 3, 2, "FLANK" }, { 2, 0, "NORMAL" } }) do
			ctx.cc2x.appels_modes = {}; ctx.cc2x.plugin.appels = ctx.cc2x.appels_modes
			O.cliquer(ctx, cas[1])
			local s = appels(ctx, "set")
			t:egal(#s, 1, cas[3] .. " : un seul set()")
			t:verifier(s[1] and s[1][2] == 9 and s[1][3] == cas[2] and math.type(s[1][2]) == "integer" and math.type(s[1][3]) == "integer",
				cas[3] .. " : set(9, " .. cas[2] .. ") avec deux entiers", s[1] and (tostring(s[1][2]) .. "," .. tostring(s[1][3])))
			t:egal(O.bouton_allume(ctx), cas[1], cas[3] .. " : bouton allume d'apres cc2x.modes.get")
			t:egal(lit(ctx).table_modes[9], cas[2], cas[3] .. " : le plugin a bien memorise ce mode")
		end
		t:verifier(#ctx.erreurs == 0, "aucune erreur")
	end)

	cadre.scenario("valeurs ENVOYEES bornees : 600 clics au hasard, set(id entier > 0, mode dans {0,1,2}) uniquement", function(t)
		local jeu, ctx = nouveau(PLUGIN)
		local graine = 12345
		local function alea(n) graine = (graine * 1103515245 + 12345) % 2147483648; return graine % n + 1 end
		local ids = { 9, 10, 13, 11, 12, 1 }       -- Albatros, Manta, Albatros, helico, avion IA, porte-avions : seuls 9, 10, 13 ont un onglet
		local clics = 0
		for _ = 1, 600 do
			O.selectionner(ctx, ids[alea(#ids)])
			local i = alea(4)                        -- 1..3 = bouton, 4 = pas de clic
			if i <= 3 then O.image(ctx, i) else O.image(ctx) end
			if i <= 3 and O.fenetre(ctx) then clics = clics + 1 end
		end
		local s = appels(ctx, "set")
		t:egal(#s, clics, "un set() par clic sur un bouton (ni plus, ni moins)")
		local mauvais = 0
		local vus = { [9] = true, [10] = true, [13] = true }
		for _, a in ipairs(s) do
			local ok = math.type(a[2]) == "integer" and a[2] > 0 and a[2] <= 0x7fffffff and vus[a[2]]
				and math.type(a[3]) == "integer" and a[3] >= 0 and a[3] <= 2
			if not ok then mauvais = mauvais + 1 end
		end
		t:egal(mauvais, 0, "tous les set() ont un id d'avion valide et un mode 0, 1 ou 2")
		for _, a in ipairs(ctx.cc2x.appels_modes) do
			t:verifier(a[1] == "set" or a[1] == "get" or a[1] == "status" or a[1] == "hold", "seules les 4 fonctions du plugin sont appelees", a[1])
		end
		local refus = 0
		for _ in pairs(lit(ctx).table_modes) do refus = refus + 1 end
		t:verifier(refus <= 3, "le plugin ne connait que les 3 avions qui ont un onglet", refus)
		t:verifier(#ctx.erreurs == 0 and not ctx.env.g_cm.casse, "aucune erreur")
	end)

	cadre.scenario("ligne d'etat : OBSERVATION / ACTIF / PILOTE : EN PAUSE / EN ATTENTE / rien", function(t)
		local jeu, ctx = nouveau(PLUGIN)
		local p = lit(ctx)
		O.selectionner(ctx, 9)
		local function rafraichir() for _ = 1, 61 do O.image(ctx) end end      -- le statut est relu toutes les 60 images
		rafraichir()
		t:egal({ etat(ctx) }, { "OBSERVATION : SANS EFFET", ORANGE }, "enabled = 0 : observation, en orange")
		p.enabled = true
		p.table_modes[9] = 1                                                    -- ECO demande
		rafraichir()
		t:egal({ etat(ctx) }, { "EN ATTENTE", { 190, 204, 204 } }, "enabled = 1, ECO demande, rien d'ecrit encore : en attente")
		p.actif[9] = 1
		rafraichir()
		t:egal({ etat(ctx) }, { "ACTIF", VERT }, "ECO ecrit en ce moment : ACTIF en vert")
		p.table_modes[9] = 2; p.actif[9] = 2
		rafraichir()
		t:egal({ etat(ctx) }, { "ACTIF", ORANGE }, "FLANK ecrit : ACTIF en orange")
		ctx.cc2x.table.modes.hold(9)
		O.image(ctx)
		t:egal((etat(ctx)), "PILOTE : EN PAUSE", "avion tenu par le joueur : PILOTE : EN PAUSE")
		p.table_modes[9] = 0; p.actif[9] = 0; p.tenus[9] = nil
		rafraichir()
		t:egal((etat(ctx)), nil, "NORMAL, rien d'ecrit : aucune ligne d'etat")
	end)

	cadre.scenario("le statut du plugin n'est relu que toutes les 60 images", function(t)
		local jeu, ctx = nouveau(PLUGIN)
		O.selectionner(ctx, 9)
		for _ = 1, 600 do O.image(ctx) end
		t:verifier(#appels(ctx, "status") <= 11, "600 images : au plus 11 appels a status()", #appels(ctx, "status"))
		t:verifier(#appels(ctx, "status") >= 9, "mais il est bien relu", #appels(ctx, "status"))
	end)

	cadre.scenario("autonomie estimee : valeurs attendues et toujours entre 0 et 120 minutes", function(t)
		local jeu, ctx = nouveau(PLUGIN)
		O.selectionner(ctx, 9)
		O.image(ctx)
		t:egal(autonomie(ctx), "AUTONOMIE ~47 min", "Albatros plein, NORMAL : 800 / 0,282 / 60 = 47 min")
		O.cliquer(ctx, 1)
		t:egal(autonomie(ctx), "AUTONOMIE ~61 min", "Albatros plein, ECO : 61 min")
		O.cliquer(ctx, 3)
		t:egal(autonomie(ctx), "AUTONOMIE ~44 min", "Albatros plein, FLANK : 44 min")
		O.selectionner(ctx, 10)
		O.image(ctx)
		t:egal(autonomie(ctx), "AUTONOMIE ~56 min", "Manta plein, NORMAL : 1200 / 0,36 / 60 = 56 min")
		O.cliquer(ctx, 3)
		t:egal(autonomie(ctx), "AUTONOMIE ~26 min", "Manta plein, FLANK : 26 min")
		O.cliquer(ctx, 1)
		t:egal(autonomie(ctx), "AUTONOMIE ?", "Manta ECO non mesure : '?'")
		O.selectionner(ctx, 13)                                                  -- Albatros a moitie plein
		O.image(ctx)
		t:egal(autonomie(ctx), "AUTONOMIE ~24 min", "Albatros a 50 %, NORMAL : 24 min")
		-- balayage : carburant de 0 a 1 par pas de 0,05, 2 avions x 3 boutons
		local hors = 0
		for _, id in ipairs({ 9, 10 }) do
			for b = 1, 3 do
				for k = 0, 20 do
					jeu.vehicules[id].fuel = k / 20
					lit(ctx).table_modes[id] = ({ 1, 0, 2 })[b]
					O.selectionner(ctx, id)
					O.image(ctx)
					local a = autonomie(ctx)
					local n = a and tonumber(a:match("~(%d+) min"))
					if a ~= "AUTONOMIE ?" and not (n and n >= 0 and n <= 120) then hors = hors + 1 end
				end
			end
		end
		t:egal(hors, 0, "balayage fuel 0..1 x 2 avions x 3 modes : toujours '?' ou 0..120 min")
	end)

	cadre.scenario("autonomie : lecture du carburant impossible = '?', sans erreur", function(t)
		local jeu, ctx = nouveau(PLUGIN)
		local faux = {
			get = function() return true end, get_team = function() return 1 end, get_definition_index = function() return 8 end, get_id = function() return 9 end,
			get_fuel_factor = function() error("boum") end,
		}
		ctx.env.render_selection_vehicle(256, 256, faux)
		t:egal(autonomie(ctx), "AUTONOMIE ?", "get_fuel_factor qui plante")
		faux.get_fuel_factor = function() return "texte" end
		ctx.env.render_selection_vehicle(256, 256, faux)
		t:egal(autonomie(ctx), "AUTONOMIE ?", "get_fuel_factor non numerique")
		t:verifier(not ctx.env.g_cm.casse and #ctx.erreurs == 0, "onglet non coupe, aucune erreur")
	end)

	cadre.scenario("garde-fou pilotage : hold(id) a chaque image tant que g_viewing_vehicle_id > 0, jamais sinon", function(t)
		local jeu, ctx = nouveau(PLUGIN)
		O.selectionner(ctx, 9)
		for _ = 1, 100 do O.image(ctx) end
		t:egal(#appels(ctx, "hold"), 0, "g_viewing_vehicle_id = 0 : aucun hold")
		for _, v in ipairs({ -1, "9", true }) do
			ctx.env.g_viewing_vehicle_id = v
			for _ = 1, 10 do O.image(ctx) end
		end
		ctx.env.g_viewing_vehicle_id = nil
		for _ = 1, 10 do O.image(ctx) end
		t:egal(#appels(ctx, "hold"), 0, "valeurs negatives, texte, booleen, nil : aucun hold")
		ctx.env.g_viewing_vehicle_id = 9
		for _ = 1, 30 do O.image(ctx) end
		local h = appels(ctx, "hold")
		t:egal(#h, 30, "g_viewing_vehicle_id = 9 : un hold par image")
		for _, a in ipairs(h) do t:verifier(a[2] == 9 and math.type(a[2]) == "integer", "hold(9) avec un entier > 0", a[2]) end
		t:egal(({ ctx.cc2x.table.modes.get(9) })[3], true, "le plugin voit l'avion 9 comme tenu")
		ctx.env.g_viewing_vehicle_id = 0
		jeu:avancer_ticks(89)
		t:egal(({ ctx.cc2x.table.modes.get(9) })[3], true, "89 ticks apres le dernier hold : encore tenu (garde de 90 ticks)")
		jeu:avancer_ticks(2)
		t:egal(({ ctx.cc2x.table.modes.get(9) })[3], false, "91 ticks apres : relache")
	end)

	cadre.scenario("pas de plugin ou plugin sans hold : aucun hold, aucune erreur", function(t)
		local jeu, ctx = nouveau({ niveau = "0.5" })
		ctx.env.g_viewing_vehicle_id = 9
		for _ = 1, 10 do O.image(ctx) end
		t:verifier(#ctx.erreurs == 0, "sans plugin : aucune erreur")
		jeu = Jeu.nouveau(); O.monde(jeu)
		ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1 })
		ctx.env.cc2x = { api = 4, modes = { set = function() return true end, get = function() return 0, 0, false end } }   -- plugin sans status ni hold
		ctx:monter({ ecran = "bord_controle", libs = { SCRIPT } })
		O.selectionner(ctx, 9)
		ctx.env.g_viewing_vehicle_id = 9
		for _ = 1, 70 do O.image(ctx) end
		t:egal((etat(ctx)), "OBSERVATION : SANS EFFET", "plugin sans status() : traite comme 'enabled = faux'")
		t:verifier(#ctx.erreurs == 0 and not ctx.env.g_cm.casse, "aucune erreur")
	end)

	cadre.scenario("set() refuse (table de 64 avions pleine) : l'onglet ne ment pas, le bouton allume reste celui du plugin", function(t)
		local jeu, ctx = nouveau(PLUGIN)
		local p = lit(ctx)
		for i = 1000, 1063 do p.table_modes[i] = 1; p.nb = p.nb + 1 end
		O.selectionner(ctx, 9)
		O.image(ctx)
		O.cliquer(ctx, 1)
		t:egal(#appels(ctx, "set"), 1, "set() appele")
		t:egal(p.table_modes[9], nil, "refuse par le plugin")
		t:egal(O.bouton_allume(ctx), 2, "NORMAL reste allume (l'ecran relit le plugin a chaque image)")
	end)

	cadre.scenario("BUG ONG-1 : le retour de set() est ignore : refus du plugin = bouton qui clignote puis revient, sans aucun message", function(t)
		t:bug("ONG-1", "v2/library_custom_5.lua l. 132-136 : pcall(cc2x.modes.set, ...) puis bouton = i sans lire le resultat ; la table du plugin (64 avions) se remplit meme avec des clics NORMAL", function()
			local jeu, ctx = nouveau(PLUGIN)
			local p = lit(ctx)
			for i = 1000, 1063 do p.table_modes[i] = 0; p.nb = p.nb + 1 end        -- 64 avions deja vus dans la session
			O.selectionner(ctx, 9)
			O.image(ctx)
			O.image(ctx, 1)
			local allume_pendant_le_clic = O.bouton_allume(ctx)
			O.image(ctx); O.image(ctx)
			local revenu = O.bouton_allume(ctx) == 2
			local message = false
			for _, tx in ipairs(O.textes(ctx)) do if tx:find("REFUS", 1, true) or tx:find("PLEIN", 1, true) or tx:find("ERREUR", 1, true) then message = true end end
			return p.table_modes[9] == nil and revenu and not message and allume_pendant_le_clic == nil,
				("set refuse par le plugin, bouton revenu a NORMAL : %s, message d'erreur affiche : %s"):format(tostring(revenu), tostring(message))
		end)
	end)

	cadre.scenario("fonctions du plugin qui plantent : aucune erreur, repli sur la memoire de l'ecran", function(t)
		local jeu, ctx = nouveau(PLUGIN)
		local m = ctx.env.cc2x.modes
		m.get = function() error("boum") end
		m.status = function() error("boum") end
		m.hold = function() error("boum") end
		m.set = function() error("boum") end
		O.selectionner(ctx, 9)
		ctx.env.g_viewing_vehicle_id = 9
		O.image(ctx)
		O.cliquer(ctx, 3)
		t:verifier(#ctx.erreurs == 0 and not ctx.env.g_cm.casse, "aucune erreur ; onglet toujours actif")
		t:egal((etat(ctx)), "OBSERVATION : SANS EFFET", "statut illisible = enabled faux")
	end)

	cadre.scenario("reponses etranges du plugin (mode 7, actif texte) : pas d'erreur, bouton par defaut", function(t)
		local jeu, ctx = nouveau(PLUGIN)
		ctx.env.cc2x.modes.get = function() return 7, "x", 1 end
		O.selectionner(ctx, 9)
		O.image(ctx)
		t:egal(O.bouton_allume(ctx), 2, "mode inconnu : NORMAL par defaut")
		t:verifier(#ctx.erreurs == 0 and not ctx.env.g_cm.casse, "aucune erreur")
		ctx.env.cc2x.modes.get = function() return nil end
		O.image(ctx)
		t:verifier(#ctx.erreurs == 0 and not ctx.env.g_cm.casse, "get() renvoie nil : aucune erreur")
	end)

	cadre.scenario("le choix est PARTAGE entre les 3 ecrans de bord (un seul plugin)", function(t)
		local jeu = Jeu.nouveau()
		O.monde(jeu)
		local sdk = Cc2x.nouveau(jeu, PLUGIN)
		local l = O.ecran(jeu, SCRIPT, { nom = "screen_veh_l", cc2x_instance = sdk })
		local m = O.ecran(jeu, SCRIPT, { nom = "screen_veh_m", cc2x_instance = sdk })
		local r = O.ecran(jeu, SCRIPT, { nom = "screen_veh_r", cc2x_instance = sdk })
		for _, c in ipairs({ l, m, r }) do O.selectionner(c, 9) end
		O.cliquer(l, 3)
		O.image(m); O.image(r)
		t:egal({ O.bouton_allume(l), O.bouton_allume(m), O.bouton_allume(r) }, { 3, 3, 3 }, "FLANK choisi sur L : allume sur M et R")
	end)

	cadre.scenario("erreur de dessin en mode plugin : piles rendues, onglet coupe, ligne CC2MODES|UI|erreur, rien d'envoye apres", function(t)
		local jeu, ctx = nouveau(PLUGIN)
		O.selectionner(ctx, 9)
		O.image(ctx)
		ctx.ui.faute = { methode = "text_basic", fenetre = O.TITRE, message = "faute injectee" }
		local ok, a = O.image(ctx)
		t:verifier(ok and a == "retour_ecran", "l'ecran du jeu continue")
		t:verifier(ctx.env.g_cm.casse, "onglet coupe")
		t:egal({ #ctx.ui.window_stack, #ctx.ui.region_stack }, { 0, 0 }, "piles rendues")
		ctx.ui.faute = nil
		ctx.cc2x.appels_modes = {}; ctx.cc2x.plugin.appels = ctx.cc2x.appels_modes
		O.cliquer(ctx, 1)
		t:egal(#appels(ctx, "set"), 0, "plus aucun set() une fois l'onglet coupe")
		local n = 0
		for _, l in ipairs(jeu.journal_cc2x) do if l:find("CC2MODES|UI|erreur|", 1, true) then n = n + 1 end end
		t:egal(n, 1, "une ligne d'erreur dans cc2x.log")
	end)

	cadre.scenario("update enveloppee une seule fois et de facon transparente (retours, parametres)", function(t)
		local jeu = Jeu.nouveau()
		O.monde(jeu)
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1, cc2x = PLUGIN })
		ctx:charger_texte("g_viewing_vehicle_id = 0 function update(...) g_recu = table.pack(...); g_n = (g_n or 0) + 1; return 1, nil, 3, nil end function begin() begin_load() end", "ecran_nil")
		ctx:charger_script(SCRIPT)
		ctx:begin(); ctx:begin()
		ctx.env.g_viewing_vehicle_id = 9
		local r = ctx:update_brut(300, 200, 0.5, 33.0, "p5", nil, "p7")
		t:egal({ r.n, r[2], r[3], r[4], r[5] }, { 5, 1, nil, 3, nil }, "retours conserves")
		t:egal(ctx.env.g_recu.n, 7, "7 parametres retransmis")
		t:egal(ctx.env.g_n, 1, "l'ecran d'origine n'est appele qu'une fois")
		t:egal(#appels(ctx, "hold"), 1, "un seul hold pour cette image")
	end)

	cadre.scenario("RISQUE ONG-R1 : g_viewing_vehicle_id absent au begin_load = le garde-fou pilotage n'est JAMAIS installe", function(t)
		t:risque("ONG-R1", "envelopper_update() exige type(g_viewing_vehicle_id) == 'number' au moment de begin_load ; si le vrai ecran ne le definit qu'au premier update, hold() n'est jamais appele", function()
			local jeu = Jeu.nouveau(); O.monde(jeu)
			local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1, cc2x = PLUGIN })
			ctx:charger_texte("function update() g_viewing_vehicle_id = g_viewing_vehicle_id or 9 return 'ok' end function begin() begin_load() end", "ecran_tardif")
			ctx:charger_script(SCRIPT)
			ctx:begin()
			for _ = 1, 50 do O.image(ctx) end
			return #appels(ctx, "hold") == 0 and ctx.env.g_viewing_vehicle_id == 9, "g_viewing_vehicle_id = 9 pendant 50 images, hold() appele " .. #appels(ctx, "hold") .. " fois"
		end)
	end)

	cadre.scenario("RISQUE ONG-R2 : hold() est appele AVANT l'update du jeu, donc avec une image de retard a la prise en main", function(t)
		t:risque("ONG-R2", "la 1re image ou g_viewing_vehicle_id passe a l'avion ne le tient pas encore : le plugin peut ecrire les gaz de cette image", function()
			local jeu = Jeu.nouveau(); O.monde(jeu)
			local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1, cc2x = PLUGIN })
			ctx:charger_texte("g_viewing_vehicle_id = 0 function update() if g_prise_en_main then g_viewing_vehicle_id = 9 end return 'ok' end function begin() begin_load() end", "ecran_prise")
			ctx:charger_script(SCRIPT)
			ctx:begin()
			lit(ctx).table_modes[9] = 1; lit(ctx).actif[9] = 1                 -- 9 est en ECO, ecrit en ce moment
			for _ = 1, 10 do O.image(ctx) end
			ctx.env.g_prise_en_main = true                                       -- le joueur prend l'avion 9 en main pendant cette image
			O.image(ctx)
			local tenu_fin_image = ({ ctx.cc2x.table.modes.get(9) })[3]
			O.image(ctx)
			local tenu_image_suivante = ({ ctx.cc2x.table.modes.get(9) })[3]
			return tenu_fin_image == false and tenu_image_suivante == true, ("tenu a la fin de l'image de prise en main : %s ; a l'image suivante : %s"):format(tostring(tenu_fin_image), tostring(tenu_image_suivante))
		end)
	end)
end)
