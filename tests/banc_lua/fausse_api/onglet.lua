-- Aides pour piloter l'onglet SPEED (fenetre sous LOADOUT) des scripts library_custom_5 : clic sur un bouton, bouton allume, textes.
local Jeu = require("fausse_api.jeu")
local Contexte = require("fausse_api.contexte")

local O = {}

O.TITRE = "SPEED##cm_speed"
-- couleurs du script (ECO vert, NORMAL cyan, FLANK orange) et couleur d'un bouton eteint
O.COULEURS = { { 16, 255, 127, 255 }, { 16, 255, 255, 255 }, { 255, 176, 32, 255 } }

-- un porte-avions (id 1) + un Albatros (9), un Manta (10), un helicoptere (11), un avion de l'IA (12), un avion allie (13)
function O.monde(jeu)
	jeu:ajouter({ id = 1, def = Jeu.DEFS.chassis_carrier })
	jeu:ajouter({ id = 9, def = Jeu.DEFS.chassis_air_wing_light, fuel = 1.0 })
	jeu:ajouter({ id = 10, def = Jeu.DEFS.chassis_air_wing_heavy, fuel = 1.0 })
	jeu:ajouter({ id = 11, def = Jeu.DEFS.chassis_air_rotor_light, fuel = 1.0 })
	jeu:ajouter({ id = 12, def = Jeu.DEFS.chassis_air_wing_light, team = 0, fuel = 1.0 })
	jeu:ajouter({ id = 13, def = Jeu.DEFS.chassis_air_wing_light, fuel = 0.5 })
end

-- ecran de bord screen_veh_m du porte-avions 1 avec le script d'onglet
function O.ecran(jeu, script, opts)
	opts = opts or {}
	local ctx = Contexte.nouveau(jeu, { nom = opts.nom or "screen_veh_m", profil = "bord", vehicule_ecran = 1,
		cc2x = opts.cc2x, cc2x_instance = opts.cc2x_instance })
	ctx:monter({ ecran = opts.ecran or "bord_controle", libs = { script }, ordre = opts.ordre, commencer = opts.commencer })
	return ctx
end

function O.selectionner(ctx, id) ctx.env.g_vehicule_clique = id end

-- une image (le jeu avance d'un tick) avec, si i est donne, un clic sur le bouton i (1 ECO, 2 NORMAL, 3 FLANK)
function O.image(ctx, i)
	local ui = ctx.ui
	if i then
		-- bouton i : x = 174..241, y = 111 + 13 * (i - 1) (fenetre en (172, 99), contenu a +2, +12)
		ui.pointeur = { x = 180, y = 112 + 13 * (i - 1) }
		ui.input_pointer_1 = true
	else
		ui.pointeur = nil
		ui.input_pointer_1 = false
	end
	ctx.jeu:avancer(1 / 30)
	return ctx:image()
end

-- clic sur le bouton i PUIS image suivante (le script allume le bouton a l'image qui suit le clic : pendant l'image du clic aucun
-- bouton n'est allume, une image de 1/30 s ; ce n'est pas un bug, c'est l'ordre de dessin ECO < NORMAL < FLANK)
function O.cliquer(ctx, i)
	O.image(ctx, i)
	return O.image(ctx)
end

function O.fenetre(ctx) return ctx.ui:fenetre(O.TITRE) end

-- numero (1..3) du bouton allume = rectangle plein de la couleur du mode, a la hauteur du bouton
function O.bouton_allume(ctx)
	for i = 1, 3 do
		local y = 111 + 13 * (i - 1)
		for _, r in ipairs(ctx.dessin.rects) do
			local c = O.COULEURS[i]
			if r.y == y and r.couleur.r == c[1] and r.couleur.g == c[2] and r.couleur.b == c[3] then return i end
		end
	end
	return nil
end

function O.textes(ctx)
	local f = O.fenetre(ctx)
	return f and f.textes or {}
end

function O.couleur_dernier_texte(ctx) return nil end

return O
