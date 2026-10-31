-- ============================================================================
--  RELEVE DES PERFORMANCES  --  note pendant la partie, dans un fichier, de
--  quoi tracer apres coup les courbes du lag (outil/courbes/faire_courbes.py).
--  N'affiche rien et ne change rien au jeu : il ne fait que lire des etats.
--
--  Chaque ecran (et l'affichage de pilotage) ecrit avec print() :
--    - toutes les 10 s, une ligne « E » (battement) : heure reelle, top du jeu,
--      nom de l'ecran, nombre d'appels a update depuis le battement precedent,
--      ecran allume ou non, joueur sur cet ecran ou non ;
--    - pour quelques ecrans seulement (DONNEES), toutes les 5 s, une ligne « D »
--      ecrite des que la seconde reelle change (le top du jeu y est donc precis) :
--      unites par equipe et par type, missiles et obus en vol, epaves.
--  Le jeu d'origine jette ce que print() ecrit ; le module « ecriture_releve »
--  (retouche du programme) l'envoie dans
--  ~/Library/Application Support/Carrier Command 2/releve_cc2.txt.
--  Les print() des mods (Revolution en a beaucoup) passent aussi, mais au plus
--  20 par minute et par ecran ; le reste est seulement compte (x= dans « E »).
-- ============================================================================

local PREFIXE = "CC2R1"
local DONNEES = { holomap_screen = true, screen_veh_m = true, screen_nav_m = true, hud = true }
local CATEGORIE = {                 -- e_game_object_type -> colonne de q<equipe>=
	[0] = 1,                        -- porte-avions
	[2] = 2, [4] = 2, [6] = 2, [58] = 2,     -- terrestres (roues, robot-chien)
	[8] = 3, [10] = 3,              -- avions
	[12] = 4, [14] = 4,             -- helicos
	[16] = 5, [57] = 5, [77] = 5, [79] = 5,  -- barges, canots, navires
	[59] = 6,                       -- tourelles des iles
}
local AUTRE, HANGAR, CACHES, COLONNES = 7, 8, 9, 9
local DOCK_HANGAR = 4
local MAX_PRINT_MODS = 20

local function lire(f, ...)
	if type(f) ~= "function" then return nil end
	local ok, v = pcall(f, ...)
	if ok then return v end
	return nil
end

local function num(v)
	if v == true then return 1 elseif v == false then return 0 end
	if type(v) == "number" then return math.floor(v) end
	return -1
end

function releve_ecrire(ligne)
	g_releve_print_origine(PREFIXE .. " " .. ligne .. " FIN")
end

-- print() des mods : laisse passer, mais limite (le fichier ne doit pas exploser)
function releve_print(...)
	local r = g_releve
	if r ~= nil and r.e ~= nil then
		local minute = r.e // 60
		if minute ~= r.minute_mods then r.minute_mods, r.print_mods = minute, 0 end
		if r.print_mods >= MAX_PRINT_MODS then
			r.print_mods_jetes = r.print_mods_jetes + 1
			return
		end
		r.print_mods = r.print_mods + 1
	end
	return g_releve_print_origine(...)
end

function releve_donnees(e, t)
	local r = g_releve
	local equipes = {}
	local n = lire(update_get_map_vehicle_count) or 0
	for i = 0, n - 1 do
		local v = update_get_map_vehicle_by_index(i)
		if v ~= nil and v:get() then
			local equipe = num(lire(v.get_team, v))
			local q = equipes[equipe]
			if q == nil then
				q = {}
				for k = 1, COLONNES do q[k] = 0 end
				equipes[equipe] = q
			end
			local col = CATEGORIE[lire(v.get_definition_index, v)] or AUTRE
			if col ~= AUTRE and lire(v.get_dock_state, v) == DOCK_HANGAR then col = HANGAR end
			q[col] = q[col] + 1
			if lire(v.get_is_visible, v) == false then q[CACHES] = q[CACHES] + 1 end
		end
	end
	local morceaux = { string.format("D e=%d t=%d s=%s moi=%d nv=%d mis=%d pro=%d epa=%d", e, t, r.nom,
		num(lire(update_get_screen_team_id)), n, num(lire(update_get_missile_count)),
		num(lire(update_get_projectile_count)), num(lire(update_get_map_destroyed_vehicle_count))) }
	if r.vehicule ~= nil then
		local pil = lire(r.vehicule.get_definition_index, r.vehicule)
		if pil ~= nil then table.insert(morceaux, "pil=" .. num(pil)) end
	end
	local ids = {}
	for equipe in pairs(equipes) do table.insert(ids, equipe) end
	table.sort(ids)
	for _, equipe in ipairs(ids) do
		table.insert(morceaux, string.format("q%d=%s", equipe, table.concat(equipes[equipe], ",")))
	end
	releve_ecrire(table.concat(morceaux, " "))
end

function releve_battement(e, t)
	local r = g_releve
	releve_ecrire(string.format("E e=%d t=%d s=%s n=%d a=%d f=%d x=%d", e, t, r.nom, r.appels,
		num(lire(update_get_screen_state_active)), num(lire(update_get_is_focus_local)), r.print_mods_jetes))
	r.appels, r.print_mods_jetes = 0, 0
end

function releve_observer()
	local r = g_releve
	r.appels = r.appels + 1
	if not r.donnees and r.appels % 8 ~= 1 then return end      -- les autres ecrans regardent l'heure 1 fois sur 8
	local e = update_get_time_since_epoch()
	if type(e) ~= "number" then return end
	e = math.floor(e)
	if e == r.e then return end
	local premiere = (r.e == nil)
	r.e = e
	local t = update_get_logic_tick()
	if premiere then
		if r.donnees then releve_ecrire(string.format("S e=%d t=%d s=%s", e, t, r.nom)) end
		r.prochain = e
	end
	if r.donnees and e % 5 == 0 then releve_donnees(e, t) end
	if e >= r.prochain then
		releve_battement(e, t)
		r.prochain = e + 10 - ((e - r.decalage) % 10)
	end
end

local function releve_passe(...)
	pcall(releve_observer)
	return ...
end

-- enveloppe transparente : memes parametres, memes retours ; une erreur du
-- releve ne peut pas casser l'ecran (pcall)
function releve_update(...)
	if g_releve.nom == "hud" then g_releve.vehicule = select(6, ...) end
	return releve_passe(g_releve_update_origine(...))
end

function releve_begin_load(...)
	local retours = table.pack(g_releve_begin_load_origine(...))

	local nom = lire(begin_get_screen_name)
	if type(nom) ~= "string" then
		nom = "autre"
		if type(update) == "function" and debug ~= nil and debug.getinfo ~= nil then
			local ok, info = pcall(debug.getinfo, update, "u")
			if ok and info and info.nparams and info.nparams >= 7 then nom = "hud" end
		end
	end

	if type(update) == "function" and g_releve_update_origine == nil
		and type(update_get_time_since_epoch) == "function" and type(update_get_logic_tick) == "function"
		and type(g_releve_print_origine) == "function" then
		local somme = 0
		for k = 1, #nom do somme = somme + nom:byte(k) end
		g_releve = { nom = nom, donnees = DONNEES[nom] == true, appels = 0, decalage = somme % 10,
			print_mods = 0, print_mods_jetes = 0 }
		g_releve_update_origine = update
		update = releve_update
	end

	return table.unpack(retours, 1, retours.n)
end

if type(print) == "function" and g_releve_print_origine == nil then
	g_releve_print_origine = print
	print = releve_print
end

if type(begin_load) == "function" and g_releve_begin_load_origine == nil then
	g_releve_begin_load_origine = begin_load
	begin_load = releve_begin_load
end
