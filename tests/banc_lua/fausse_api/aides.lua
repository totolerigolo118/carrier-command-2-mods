-- Petites aides communes aux fichiers de scenarios.
local Jeu = require("fausse_api.jeu")
local Contexte = require("fausse_api.contexte")

local A = {}

function A.cles(t)
	local r = {}
	for k in pairs(t) do r[k] = true end
	return r
end

-- noms presents dans `apres` mais pas dans `avant`, tries
function A.nouvelles_cles(avant, apres)
	local r = {}
	for k in pairs(apres) do if not avant[k] then r[#r + 1] = tostring(k) end end
	table.sort(r)
	return r
end

function A.contient(liste, valeur)
	for _, v in ipairs(liste) do if v == valeur then return true end end
	return false
end

-- un contexte d'ecran de bord (screen_veh_m par defaut) avec les scripts donnes, dans l'ordre demande
function A.ecran_de_bord(jeu, libs, opts)
	opts = opts or {}
	local ctx = Contexte.nouveau(jeu, { nom = opts.nom or "screen_veh_m", profil = "bord", vehicule_ecran = opts.vehicule_ecran, liaison = opts.liaison })
	ctx:monter({ ecran = opts.ecran or "bord_controle", libs = libs, ordre = opts.ordre, commencer = opts.commencer })
	return ctx
end

-- tous les ordres de chargement a essayer : { ordre, liaison }
A.COMBINAISONS = {
	{ ordre = "apres", liaison = "begin_load" },
	{ ordre = "avant", liaison = "begin_load" },
	{ ordre = "apres", liaison = "chargement" },
	{ ordre = "avant", liaison = "chargement" },
}

function A.nom_combinaison(c)
	return ("libs %s l'ecran, API liee %s"):format(c.ordre == "apres" and "APRES" or "AVANT", c.liaison == "begin_load" and "au begin_load" or "au chargement")
end

-- arrondi pour les comparaisons de flottants
function A.proche(a, b, tol)
	return type(a) == "number" and math.abs(a - b) <= (tol or 1e-6)
end

return A
