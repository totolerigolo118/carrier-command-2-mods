-- POINT D'ENTREE DU BANC LUA (a lancer avec Lua 5.3, de preference via lancer.py) :
--   lua5.3 banc.lua RACINE_DU_DEPOT [--filtre texte] [--seulement f1,f2] [--verbeux] [--inventaire] [--noms]
-- RACINE_DU_DEPOT = dossier qui contient tour/, outil/, passation_windows/ ...
-- Ce fichier est executable PAR LE LANCEUR ; il ne lit que des fichiers du depot et n'ecrit rien sauf sur la sortie standard.

local ici = (arg[0] or "banc.lua"):match("^(.*)[/\\][^/\\]*$") or "."
package.path = ici .. "/?.lua;" .. package.path

local racine = arg[1]
if not racine or racine:sub(1, 2) == "--" then
	io.stderr:write("usage : lua5.3 banc.lua RACINE_DU_DEPOT [--filtre texte] [--seulement f1,f2] [--verbeux] [--inventaire] [--noms]\n")
	os.exit(2)
end

if _VERSION ~= "Lua 5.3" then
	io.stderr:write(("ATTENTION : ce banc vise Lua 5.3 (celui du jeu) ; interpreteur trouve : %s\n"):format(_VERSION))
	if not os.getenv("BANC_LUA_TOLERER_VERSION") then
		io.stderr:write("Arret. (BANC_LUA_TOLERER_VERSION=1 pour passer outre, a vos risques : les entiers et string.format('%d') different avant 5.3.)\n")
		os.exit(2)
	end
end

local Contexte = require("fausse_api.contexte")
Contexte.racine, Contexte.racine_banc = racine, ici

local filtre, verbeux, inventaire, noms, seulement = nil, false, false, false, nil
local i = 2
while arg[i] do
	if arg[i] == "--filtre" then filtre = arg[i + 1]; i = i + 1
	elseif arg[i] == "--seulement" then seulement = arg[i + 1]; i = i + 1
	elseif arg[i] == "--verbeux" then verbeux = true
	elseif arg[i] == "--inventaire" then inventaire = true
	elseif arg[i] == "--noms" then noms = true
	else io.stderr:write("option inconnue : " .. arg[i] .. "\n"); os.exit(2) end
	i = i + 1
end

-- ------------------------------------------------------------------ --inventaire : tableau des fonctions de la fausse API
if inventaire or noms then
	local Api = require("fausse_api.api_jeu")
	local Inv = require("fausse_api.inventaire")
	local Jeu = require("fausse_api.jeu")
	local Cc2x = require("fausse_api.cc2x")
	local UI = require("fausse_api.ui")
	local jeu = Jeu.nouveau()
	require("fausse_api.objets")
	Api.tout_declarer()
	Cc2x.nouveau(jeu, { niveau = "0.5", plugin_modes = true })
	UI.nouvelle({ jeu = jeu })
	if inventaire then
		io.write(Inv.markdown(), "\n")
		return
	end
	-- --noms : tous les noms globaux que la fausse API met a disposition des scripts (pour le controle statique des noms inconnus)
	local vus = { cc2x = true }
	for profil in pairs(Api.PROFILS) do
		for _, ecran in ipairs({ "bord_controle", "menu_principal", "menu_secondaire", "overlay", "indications", "simple" }) do
			local j = Jeu.nouveau()
			local ctx = Contexte.nouveau(j, { nom = "x", profil = profil })
			Api.lier(ctx)
			pcall(function() ctx:charger_ecran(ecran) end)
			for k in pairs(ctx.env) do vus[k] = true end
		end
	end
	local liste = {}
	for k in pairs(vus) do liste[#liste + 1] = k end
	table.sort(liste)
	io.write(table.concat(liste, "\n"), "\n")
	return
end

-- ------------------------------------------------------------------ scenarios
local cadre = require("fausse_api.cadre")
cadre.verbeux = verbeux
local fichiers = {
	"sim_lib7", "sorties_lib9", "essai_auto_lib5", "demarrage_auto", "carburant_mesure_lib3",
	"carburant_onglet_v1", "carburant_onglet_v2", "ensemble_ecran_de_bord", "fausse_api_elle_meme",
}
if seulement then   -- --seulement sim_lib7,sorties_lib9 : ne charge que ces fichiers de scenarios
	fichiers = {}
	for f in seulement:gmatch("[^,]+") do fichiers[#fichiers + 1] = f end
end
for _, f in ipairs(fichiers) do
	cadre.charger_fichier(ici .. "/scenarios/" .. f .. ".lua")
end
local ok = cadre.executer(filtre)
os.exit(ok and 0 or 1)
