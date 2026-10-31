-- Comportements de monde reutilisables par les scenarios : une flotte de test et des avions "dociles"
-- qui reagissent aux ordres de vol comme les notes du depot disent que le vrai jeu le fait.
-- TOUS les delais sont des repères tires des mesures du depot, pas des simulations du moteur :
--   decollage : 4 avions en l'air 4048 ticks apres l'ordre (partage_detail/07 section 3, teste en jeu le 25/10/2026) -> un toutes les ~1012 ticks ;
--   retour    : piste accordee toutes les 1:31, approche 0:49, pont -> hangar 0:51 (partage_detail/03 section 3, mesure avec l'ascenseur x2).

local Jeu = require("fausse_api.jeu")
local E = Jeu.ETAT

local C = {}

-- Un porte-avions (id 1, equipe du joueur) avec `n` avions dans ses baies (ids 9, 10, 17, 18 comme dans la partie du 27/10 : JOURNAL_atterrissage.md l. 86)
function C.flotte(jeu, opts)
	opts = opts or {}
	local ids = opts.ids or { 9, 10, 17, 18 }
	local n = opts.n or #ids
	local defs = opts.defs or { Jeu.DEFS.chassis_air_wing_light, Jeu.DEFS.chassis_air_wing_light, Jeu.DEFS.chassis_air_wing_heavy, Jeu.DEFS.chassis_air_wing_heavy }
	local porte = jeu:ajouter({ id = opts.id_porte or 1, def = Jeu.DEFS.chassis_carrier, team = opts.equipe, dock_state = E.VOL, x = 1000.0, z = 2000.0, baies = {} })
	local avions = {}
	for i = 1, n do
		local a = jeu:ajouter({ id = ids[i], def = defs[i] or defs[1], team = opts.equipe, dock_state = E.HANGAR,
			dock_parent = porte.id, attached_parent = porte.id, x = 1000.0, y = 20.0, z = 2000.0 })
		porte.baies[i - 1] = a.id
		avions[i] = a
	end
	return porte, avions
end

-- Les avions rangés au hangar partent quand ils recoivent un waypoint : DEMANDE tout de suite, SORTIE un peu avant le decollage, VOL ensuite.
-- Ceux qui sont deja partis ne bougent pas. opts.espacement (1012), opts.premier (1012), opts.sans_decollage_ids = { [id]=true } : n'avancent jamais.
function C.decollage_docile(jeu, opts)
	opts = opts or {}
	local espacement, premier = opts.espacement or 1012, opts.premier or 1012
	local file_attente = 0
	local ancien = jeu.au_ordre
	jeu.au_ordre = function(j, v, ordre, ...)
		if ancien then ancien(j, v, ordre, ...) end
		if ordre ~= "add_waypoint" or v.dock_state ~= E.HANGAR or v.decollage_prevu then return end
		if opts.sans_decollage_ids and opts.sans_decollage_ids[v.id] then return end
		v.decollage_prevu = true
		file_attente = file_attente + 1
		local t_vol = premier + (file_attente - 1) * espacement
		j:dans(10, function() if j.vehicules[v.id] and j.vehicules[v.id].decollage_prevu then v.dock_state = E.DEMANDE end end)
		j:dans(math.max(11, t_vol - 600), function() if j.vehicules[v.id] and v.decollage_prevu then v.dock_state = E.SORTIE end end)
		j:dans(t_vol, function()
			if j.vehicules[v.id] and v.decollage_prevu then
				v.dock_state, v.attached_parent, v.decollage_prevu = E.VOL, -1, nil
				v.vitesse = 100.0
			end
		end)
	end
end

-- Un avion en l'air qui recoit un waypoint avec set_target_vehicle(porte-avions) revient : FILE, PISTE, PONT, HANGAR.
-- opts.piste_apres (600), opts.espacement (2730 = 1:31), opts.approche (1470 = 0:49), opts.pont (1530 = 0:51)
function C.retour_docile(jeu, opts)
	opts = opts or {}
	local ancien = jeu.au_ordre
	local nb = 0
	jeu.au_ordre = function(j, v, ordre, wp, cible)
		if ancien then ancien(j, v, ordre, wp, cible) end
		if ordre ~= "set_target_vehicle" or v.dock_state ~= E.VOL or v.retour_prevu then return end
		local porte = j.vehicules[cible]
		if not porte or porte.def ~= Jeu.DEFS.chassis_carrier then return end
		v.retour_prevu = true
		nb = nb + 1
		local piste = (opts.piste_apres or 600) + (nb - 1) * (opts.espacement or 2730)
		j:dans(30, function() v.dock_state = E.FILE end)
		j:dans(piste, function() v.dock_state = E.ATTERRIT end)
		j:dans(piste + (opts.approche or 1470), function() v.dock_state, v.attached_parent = E.PONT, porte.id end)
		j:dans(piste + (opts.approche or 1470) + (opts.pont or 1530), function() v.dock_state, v.retour_prevu, v.vitesse = E.HANGAR, nil, 0.0 end)
	end
end

-- active la sortie ET le retour dociles
function C.avions_dociles(jeu, opts)
	C.decollage_docile(jeu, opts)
	C.retour_docile(jeu, opts)
end

-- transitions "a la main" pour les scenarios fins
function C.mettre_etat(jeu, id, etat, extra)
	local v = assert(jeu.vehicules[id], "vehicule inconnu " .. tostring(id))
	v.dock_state = etat
	for k, x in pairs(extra or {}) do v[k] = x end
	return v
end

return C
