-- Scenarios de tour/lua/library_custom_9.lua : journal des SORTIES (chronometre les decollages depuis le porte-avions).
local cadre = ...
local Jeu = require("fausse_api.jeu")
local Contexte = require("fausse_api.contexte")
local C = require("fausse_api.comportements")
local A = require("fausse_api.aides")

local E = Jeu.ETAT
local SCRIPT = "tour/lua/library_custom_9.lua"

-- monde de depart : porte-avions 1 (equipe du joueur) avec 4 avions ranges (9, 10, 17, 18) ; ecran de bord du porte-avions 1
local function monde(opts)
	opts = opts or {}
	local jeu = Jeu.nouveau()
	local porte, avions = C.flotte(jeu, opts.flotte)
	if opts.dociles ~= false then C.decollage_docile(jeu, opts.dociles) end
	local ctx = A.ecran_de_bord(jeu, { SCRIPT }, { vehicule_ecran = porte.id, ordre = opts.ordre, liaison = opts.liaison })
	return jeu, ctx, porte, avions
end

-- le joueur ordonne la sortie : memes appels que le script de la carte du jeu (partage_detail/07 section 3)
local function ordonner(ctx, id, x, z)
	local v = ctx.env.update_get_map_vehicle_by_id(id)
	v:clear_waypoints(); v:clear_attack_target(); v:add_waypoint(x or 1000.0, z or 6000.0)
end

local function ligne(ctx, motif)
	for _, tx in ipairs(ctx.dessin.textes) do
		if tx.texte:find(motif) then return tx end
	end
end

cadre.groupe("library_custom_9.lua : journal des sorties", function()

	cadre.scenario("se charge sans erreur (4 ordres de chargement) et reste muet tant qu'aucune sortie n'est en cours", function(t)
		for _, c in ipairs(A.COMBINAISONS) do
			local jeu, ctx = monde({ ordre = c.ordre, liaison = c.liaison, dociles = false })
			jeu:jouer(3)
			t:verifier(#ctx.erreurs == 0, "aucune erreur (" .. A.nom_combinaison(c) .. ")", ctx.erreurs[1])
			t:verifier(#ctx.dessin.textes == 0, "rien dessine (" .. A.nom_combinaison(c) .. ")")
		end
	end)

	cadre.scenario("ne cree que ses propres globales", function(t)
		local jeu = Jeu.nouveau()
		local ctx = Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord" })
		ctx:charger_ecran("bord_controle")
		local avant = A.cles(ctx.env)
		ctx:charger_script(SCRIPT)
		t:egal(A.nouvelles_cles(avant, ctx.env), {
			"g_sorties", "g_sorties_begin_load_origine", "sorties_begin_load", "sorties_dessiner", "sorties_duree", "sorties_genre",
			"sorties_lignes", "sorties_nouveau", "sorties_observer", "sorties_update",
		}, "globales creees au chargement")
	end)

	cadre.scenario("sortie de 4 avions : etapes dans l'ordre, chronometre, ligne verte FINI en 2:15", function(t)
		local jeu, ctx = monde()
		jeu:jouer_jusqu_au_tick(100)
		for _, id in ipairs({ 9, 10, 17, 18 }) do ordonner(ctx, id) end
		local s = ctx.env.g_sorties
		jeu:jouer(1)
		t:egal(s.debut, 110, "la sortie commence au tick 110 (premier appareil vu en 'demande')")
		t:egal(#s.ordre, 4, "4 appareils suivis")
		t:verifier(ligne(ctx, "en cours") ~= nil, "ligne 'en cours' affichee")
		t:verifier(ligne(ctx, "0/4 EN L'AIR") ~= nil, "0/4 en l'air au debut")
		-- jalons : 1 en l'air a 1112, 2 a 2124, 3 a 3136, 4 a 4148
		local attendus = { { 1113, 1 }, { 2125, 2 }, { 3137, 3 }, { 4149, 4 } }
		for _, a in ipairs(attendus) do
			jeu:jouer_jusqu_au_tick(a[1])
			local n = 0
			for _, ap in ipairs(s.ordre) do if ap.vol then n = n + 1 end end
			t:egal(n, a[2], ("au tick %d : %d en l'air"):format(a[1], a[2]))
		end
		t:verifier(s.fini, "sortie terminee quand le 4e est en l'air")
		t:egal(s.fin, 4148, "fin = tick du dernier decollage")
		local l = ligne(ctx, "FINI en")
		t:verifier(l ~= nil and l.texte == "4/4 EN L'AIR : FINI en 2:15", "ligne finale '4/4 EN L'AIR : FINI en 2:15' (4038 ticks = 2:15)", l and l.texte)
		t:verifier(l and l.couleur.r == 110 and l.couleur.g == 255 and l.couleur.b == 140, "ligne finale en vert")
		local e = ligne(ctx, "ecart moyen")
		t:verifier(e ~= nil and e.texte == "ecart moyen entre decollages 0:34", "ecart moyen entre decollages 0:34 (1012 ticks)", e and e.texte)
		for k, ap in ipairs(s.ordre) do
			t:verifier(ap.demande == 110 and ap.sortie ~= nil and ap.vol ~= nil, ("avion %d : demande, sortie, vol notes dans l'ordre"):format(k))
		end
		-- l'ordre des lignes : titre, en-tete, 4 appareils, FINI, ecart
		local textes = ctx:textes()
		t:egal(#textes, 8, "8 lignes affichees")
		t:verifier(textes[1] == "SORTIES (temps de jeu)", "titre en premiere ligne", textes[1])
		t:verifier(#ctx.erreurs == 0 and #jeu.avertissements == 0, "aucune erreur ni avertissement", ctx.erreurs[1] or jeu.avertissements[1])
	end)

	cadre.scenario("le resultat reste 2 minutes de jeu (3600 ticks) apres la fin, puis disparait", function(t)
		local jeu, ctx = monde()
		jeu:jouer_jusqu_au_tick(100)
		for _, id in ipairs({ 9, 10 }) do ordonner(ctx, id) end
		jeu:jouer_jusqu_au_tick(2200)
		local s = ctx.env.g_sorties
		t:verifier(s.fini, "sortie de 2 avions terminee")
		local fin = s.fin
		jeu:jouer_jusqu_au_tick(fin + 3590)
		t:verifier(#ctx.dessin.textes > 0, "encore affiche 3590 ticks apres la fin")
		jeu:jouer_jusqu_au_tick(fin + 3602)
		t:egal(#ctx.dessin.textes, 0, "plus rien 3602 ticks apres la fin")
	end)

	cadre.scenario("avions et helicopteres : etiquettes 'avion' / 'helico' ; les vehicules terrestres sont ignores", function(t)
		local jeu = Jeu.nouveau()
		local porte, avions = C.flotte(jeu, { n = 2 })
		local helico = jeu:ajouter({ id = 30, def = Jeu.DEFS.chassis_air_rotor_light, dock_state = E.HANGAR, dock_parent = 1, attached_parent = 1 })
		local gros = jeu:ajouter({ id = 31, def = Jeu.DEFS.chassis_air_rotor_heavy, dock_state = E.HANGAR, dock_parent = 1, attached_parent = 1 })
		local terrestre = jeu:ajouter({ id = 40, def = Jeu.DEFS.chassis_land_wheel_light, dock_state = E.SORTIE, dock_parent = 1, attached_parent = 1 })
		C.decollage_docile(jeu)
		local ctx = A.ecran_de_bord(jeu, { SCRIPT }, { vehicule_ecran = 1 })
		for _, id in ipairs({ 9, 30, 31 }) do ordonner(ctx, id) end
		jeu:jouer(2)
		local s = ctx.env.g_sorties
		t:egal(#s.ordre, 3, "3 aeronefs suivis (le vehicule terrestre en sortie est ignore)")
		local genres = {}
		for _, a in ipairs(s.ordre) do genres[a.id] = a.genre end
		t:egal(genres, { [9] = "avion", [30] = "helico", [31] = "helico" }, "genres")
		t:verifier(ligne(ctx, "non reconnu") == nil, "le vehicule terrestre ne declenche pas le message 'non reconnu'")
	end)

	cadre.scenario("ordre annule (retour au hangar) : 'abandon', et la sortie se termine avec les autres", function(t)
		local jeu, ctx = monde()
		jeu:jouer_jusqu_au_tick(100)
		for _, id in ipairs({ 9, 10, 17 }) do ordonner(ctx, id) end
		jeu:jouer(1)
		-- le joueur annule l'ordre de 17 : il reste au hangar
		local v17 = jeu.vehicules[17]
		v17.decollage_prevu = nil
		v17.dock_state = E.HANGAR
		jeu:jouer_jusqu_au_tick(3300)
		local s = ctx.env.g_sorties
		t:verifier(s.fini, "sortie terminee malgre l'abandon")
		local abandon = 0
		for _, a in ipairs(s.ordre) do if a.abandon then abandon = abandon + 1 end end
		t:egal(abandon, 1, "1 appareil marque abandon")
		t:verifier(ligne(ctx, " abandon") ~= nil, "ligne de l'appareil abandonne avec ' abandon'")
		t:verifier(ligne(ctx, "2/3 EN L'AIR : FINI") ~= nil, "bilan 2/3")
	end)

	cadre.scenario("ordre redonne apres annulation, pendant la meme sortie : l'abandon est leve", function(t)
		local jeu, ctx = monde()
		jeu:jouer_jusqu_au_tick(100)
		ordonner(ctx, 9); ordonner(ctx, 10)
		jeu:jouer(1)
		local v10 = jeu.vehicules[10]
		v10.decollage_prevu = nil; v10.dock_state = E.HANGAR
		jeu:jouer(1)
		local a10
		for _, a in ipairs(ctx.env.g_sorties.ordre) do if a.id == 10 then a10 = a end end
		t:verifier(a10 and a10.abandon, "10 est marque abandon")
		v10.dock_state = E.DEMANDE                     -- le joueur redonne l'ordre
		jeu:jouer(1)
		t:verifier(a10 and a10.abandon == false, "abandon leve par le nouvel ordre")
	end)

	cadre.scenario("appareil detruit pendant la sortie : abandon, les autres terminent", function(t)
		local jeu, ctx = monde()
		jeu:jouer_jusqu_au_tick(100)
		ordonner(ctx, 9); ordonner(ctx, 10)
		jeu:jouer_jusqu_au_tick(500)
		jeu:retirer(10)
		jeu:jouer_jusqu_au_tick(1200)
		local s = ctx.env.g_sorties
		t:verifier(s.fini, "sortie terminee")
		t:verifier(ligne(ctx, "1/2 EN L'AIR : FINI") ~= nil, "bilan 1/2")
		t:verifier(#ctx.erreurs == 0, "aucune erreur quand un vehicule suivi disparait", ctx.erreurs[1])
	end)

	cadre.scenario("rattache OU accoste : les deux liens sont acceptes", function(t)
		local jeu = Jeu.nouveau()
		local porte = jeu:ajouter({ id = 1, def = Jeu.DEFS.chassis_carrier, x = 0, z = 0 })
		jeu:ajouter({ id = 50, def = Jeu.DEFS.chassis_air_wing_light, dock_state = E.SORTIE, attached_parent = 1, dock_parent = -1 })
		jeu:ajouter({ id = 51, def = Jeu.DEFS.chassis_air_wing_light, dock_state = E.SORTIE, attached_parent = -1, dock_parent = 1 })
		local ctx = A.ecran_de_bord(jeu, { SCRIPT }, { vehicule_ecran = 1 })
		jeu:jouer(1)
		t:egal(#ctx.env.g_sorties.ordre, 2, "les deux appareils sont suivis (lien 'rattache' et lien 'accoste')")
	end)

	cadre.scenario("appareil en sortie rattache a un AUTRE bateau de l'equipe : message 'non reconnu' en rouge", function(t)
		local jeu = Jeu.nouveau()
		jeu:ajouter({ id = 1, def = Jeu.DEFS.chassis_carrier })
		jeu:ajouter({ id = 2, def = Jeu.DEFS.chassis_carrier })
		jeu:ajouter({ id = 60, def = Jeu.DEFS.chassis_air_wing_light, dock_state = E.SORTIE, attached_parent = 2, dock_parent = 2 })
		jeu:ajouter({ id = 61, def = Jeu.DEFS.chassis_air_wing_light, team = 0, dock_state = E.SORTIE, attached_parent = 99, dock_parent = 99 })   -- IA : ignore
		local ctx = A.ecran_de_bord(jeu, { SCRIPT }, { vehicule_ecran = 1 })
		jeu:jouer(1)
		local l = ligne(ctx, "SORTIES %?")
		t:verifier(l ~= nil and l.texte == "SORTIES ? 1 en sortie, non reconnu(s)", "message de secours (1 appareil de l'equipe, pas relie a ce bateau ; celui de l'IA est ignore)", l and l.texte)
		t:verifier(l and l.couleur.r == 255 and l.couleur.g == 120, "en rouge")
		t:egal(ctx.env.g_sorties.debut, nil, "aucune sortie demarree pour autant")
	end)

	cadre.scenario("ecran sans vehicule (get() faux) ou lecture en erreur : aucune erreur, l'ecran d'origine continue", function(t)
		local jeu = Jeu.nouveau()
		C.flotte(jeu)
		local ctx = A.ecran_de_bord(jeu, { SCRIPT }, { vehicule_ecran = nil })
		local ok, a, b = ctx:image()
		t:verifier(ok and a == "retour_ecran" and b == 512, "retours de l'ecran inchanges sans vehicule d'ecran")
		t:verifier(#ctx.dessin.textes == 0, "rien dessine")
		ctx.env.update_get_screen_vehicle = function() error("boum") end
		ok, a = ctx:image()
		t:verifier(ok and a == "retour_ecran", "lecture qui plante : l'ecran d'origine continue")
		ctx.erreur_dessin = "police absente"
		ctx.env.update_get_screen_vehicle = nil
		ok, a = ctx:image()
		t:verifier(ok and a == "retour_ecran" and #ctx.erreurs == 0, "dessin qui plante : l'ecran d'origine continue")
	end)

	cadre.scenario("piege de Lua 5.3 : tick renvoye en flottant a valeur entiere (1800.0) : memes resultats, aucune erreur", function(t)
		local jeu, ctx = monde()
		ctx.env.update_get_logic_tick = function() return jeu.tick + 0.0 end
		jeu:jouer_jusqu_au_tick(100)
		ordonner(ctx, 9); ordonner(ctx, 10)
		jeu:jouer_jusqu_au_tick(2300)
		local l = ligne(ctx, "FINI en")
		t:verifier(l and l.texte == "2/2 EN L'AIR : FINI en 1:07", "ligne finale identique au cas entier (2014 ticks = 1:07)", l and l.texte)
		t:verifier(#ctx.erreurs == 0, "aucune erreur")
	end)

	cadre.scenario("RISQUE SORT-R2 : pas de reinitialisation quand le tick recule (contrairement a library_custom_7 et _3)", function(t)
		t:risque("SORT-R2", "si l'etat Lua survit au chargement d'une autre partie, le resultat de l'ancienne sortie reste affiche jusqu'a ce que le nouveau tick depasse fin + 3600", function()
			local jeu, ctx = monde()
			jeu:jouer_jusqu_au_tick(100)
			ordonner(ctx, 9); ordonner(ctx, 10)
			jeu:jouer_jusqu_au_tick(2300)
			local fin = ctx.env.g_sorties.fin
			jeu.tick = 100                                   -- nouvelle partie : le tick repart
			jeu:jouer(1)
			local encore = ligne(ctx, "FINI en") ~= nil
			return encore, ("fin = %d ; apres retour du tick a 100, ligne 'FINI en' encore affichee : %s"):format(fin, tostring(encore))
		end)
	end)

	cadre.scenario("BUG SORT-1 : si tous les ordres sont annules, la ligne verte annonce quand meme 'FINI'", function(t)
		t:bug("SORT-1", "0/N en l'air mais 'FINI' en vert (rien n'a decolle)", function()
			local jeu, ctx = monde()
			jeu:jouer_jusqu_au_tick(100)
			ordonner(ctx, 9); ordonner(ctx, 10)
			jeu:jouer(1)
			for _, id in ipairs({ 9, 10 }) do
				jeu.vehicules[id].decollage_prevu = nil
				jeu.vehicules[id].dock_state = E.HANGAR
			end
			jeu:jouer(2)
			local l = ligne(ctx, "FINI")
			return l ~= nil and l.texte:find("^0/2 EN L'AIR : FINI") ~= nil and l.couleur.g == 255 and l.couleur.r == 110,
				l and l.texte
		end)
	end)
end)
