-- UN CONTEXTE = un ecran du jeu avec son propre etat Lua (environnement global separe).
--
-- Sequence imitee (partage_detail/07, outil/tests_en_jeu/LISEZ-MOI.txt, tour/auto/library_custom_5.lua) :
--   1. etat Lua neuf ; bibliotheques du jeu (library_util.lua : begin_load() vide ; enumerations ; color8) ;
--   2. le script de l'ecran (ici un FAUX, dans ecrans/) et les library_custom_N.lua du mod, dans un ordre qui varie :
--        ordre = "apres" : script d'ecran PUIS libs   (partage_detail/07 : "loaded AFTER the screen script")
--        ordre = "avant" : libs PUIS script d'ecran   (commentaires de sonde_api_lua.lua et de tour/auto : "chargees AVANT")
--      Les docs se contredisent : les scripts doivent marcher dans les deux cas, donc les scenarios essaient les deux.
--   3. le jeu appelle begin(), qui appelle begin_load() : c'est la que l'API C est liee (sauf overlay : liee au chargement) ;
--   4. puis update(screen_w, screen_h, tick_fraction, delta_time) a chaque image.

local Api = require("fausse_api.api_jeu")
local UI = require("fausse_api.ui")
local Cc2x = require("fausse_api.cc2x")

local Contexte = { racine = ".", racine_banc = "." }
Contexte.__index = Contexte

local function lire(chemin)
	local f, err = io.open(chemin, "rb")
	if not f then error("fichier illisible : " .. tostring(err), 0) end
	local t = f:read("a")
	f:close()
	return t
end

-- comme luaL_loadfile : saute un BOM UTF-8 et une premiere ligne commencant par '#'
local function nettoyer(texte)
	if texte:sub(1, 3) == "\239\187\191" then texte = texte:sub(4) end
	if texte:sub(1, 1) == "#" then texte = "--" .. texte end
	return texte
end

-- opts : nom (nom d'ecran), profil (bord|menu|overlay|hud|simple), liaison, taille {w, h}, vehicule_ecran (id), unite_delta ("ms"|"s")
function Contexte.nouveau(jeu, opts)
	opts = opts or {}
	local profil = opts.profil or "bord"
	local ctx = setmetatable({
		jeu = jeu, nom = opts.nom or "screen_veh_m", profil = profil,
		prints = {}, erreurs = {}, images = 0, api_liee = false,
		dessin = { textes = {}, rects = {}, contours = {} },
		taille = opts.taille or ((profil == "bord") and { 256, 256 } or { 1920, 1080 }),
		vehicule_ecran = opts.vehicule_ecran,
		liaison = opts.liaison or ((profil == "overlay") and "chargement" or "begin_load"),
		-- SUPPOSE : delta_time en millisecondes (le script d'essai auto le suppose ; l'unite reelle n'est pas etablie)
		unite_delta = opts.unite_delta or "ms",
	}, Contexte)
	ctx.env = Api.nouvel_env(ctx)
	-- le SDK CC2X met sa table `cc2x` dans TOUS les etats Lua du jeu des leur creation (LUA_API.md) ; opts.cc2x = options de la fausse table
	if opts.cc2x_instance then                       -- plusieurs ecrans partagent le MEME plugin (comme dans le jeu : un seul cc2x_modes.dll)
		ctx.cc2x = opts.cc2x_instance
		ctx.env.cc2x = ctx.cc2x.table
	elseif opts.cc2x then
		ctx.cc2x = Cc2x.nouveau(jeu, opts.cc2x)
		ctx.env.cc2x = ctx.cc2x.table
	end
	if profil == "bord" then
		ctx.ui = UI.nouvelle(ctx)
		ctx.env.g_ui = ctx.ui          -- SUPPOSE : g_ui existe des le chargement (library_ui.lua), pas seulement apres begin()
	end
	-- library_util.lua : begin_load() ; c'est ici que le jeu lie l'API C (SUPPOSE : a l'interieur de begin_load)
	ctx.env.begin_load = function() Api.lier(ctx) end
	if ctx.liaison == "chargement" then Api.lier(ctx) end
	if opts.enregistrer ~= false then jeu.contextes[#jeu.contextes + 1] = ctx end
	return ctx
end

function Contexte:charger_texte(texte, nom)
	local fn, err = load(nettoyer(texte), "@" .. nom, "t", self.env)
	if not fn then error("erreur de syntaxe : " .. tostring(err), 0) end
	return fn()
end

-- chemin relatif a la racine du DEPOT (ex. "tour/lua/library_custom_7.lua")
function Contexte:charger_script(chemin_relatif, prefixe)
	local texte = lire(Contexte.racine .. "/" .. chemin_relatif)
	if prefixe then texte = prefixe .. "\n" .. texte end
	return self:charger_texte(texte, chemin_relatif)
end

function Contexte:charger_ecran(nom)
	return self:charger_texte(lire(Contexte.racine_banc .. "/fausse_api/ecrans/" .. nom .. ".lua"), "FAUX_ECRAN/" .. nom .. ".lua")
end

-- opts : ecran (nom du faux script d'ecran), libs ({chemin} ou {chemin, prefixe=...}), ordre ("apres"|"avant"), commencer (defaut vrai : appelle begin())
function Contexte:monter(opts)
	local ordre = opts.ordre or "apres"
	local function ecran() if opts.ecran then self:charger_ecran(opts.ecran) end end
	local function libs()
		for _, l in ipairs(opts.libs or {}) do
			if type(l) == "string" then self:charger_script(l) else self:charger_script(l[1], l.prefixe) end
		end
	end
	if ordre == "avant" then libs(); ecran() else ecran(); libs() end
	if opts.commencer ~= false then self:begin() end
	return self
end

function Contexte:begin()
	local f = self.env.begin
	if type(f) == "function" then return f() end
end

-- une image : update(screen_w, screen_h, tick_fraction, delta_time). Une erreur levee par update est CAPTUREE (ctx.erreurs)
-- et renvoyee ; le vrai jeu la journalise probablement et continue (SUPPOSE).
function Contexte:image(dt)
	dt = dt or (1 / 30)
	self.images = self.images + 1
	self.dessin = { textes = {}, rects = {}, contours = {} }
	if self.ui then self.ui:nouvelle_image() end
	local f = self.env.update
	if type(f) ~= "function" then return true end
	local delta = (self.unite_delta == "s") and dt or (dt * 1000.0)
	local r = table.pack(pcall(f, self.taille[1], self.taille[2], self.jeu.reste_ticks, delta))
	if not r[1] then
		self.erreurs[#self.erreurs + 1] = tostring(r[2])
		return false, r[2]
	end
	self.dernier_retour = table.pack(table.unpack(r, 2, r.n))
	return true, table.unpack(r, 2, r.n)
end

-- appelle update avec des arguments choisis (test de transparence des enveloppes) ; renvoie pack(ok, retours...)
function Contexte:update_brut(...)
	self.dessin = { textes = {}, rects = {}, contours = {} }
	if self.ui then self.ui:nouvelle_image() end
	return table.pack(pcall(self.env.update, ...))
end

-- ------------------------------------------------------------------ lecture de ce qui a ete dessine
function Contexte:textes()
	local r = {}
	for _, t in ipairs(self.dessin.textes) do r[#r + 1] = t.texte end
	return r
end

function Contexte:texte_contenant(sous_chaine)
	for _, t in ipairs(self.dessin.textes) do
		if t.texte:find(sous_chaine, 1, true) then return t end
	end
end

return Contexte
