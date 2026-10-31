-- ============================================================================
--  ESSAI AUTOMATIQUE  (mod cc2_auto : a activer SEULEMENT pour un essai sans personne devant l'ecran)
--
--  Adapte du banc du Mac (outil/tests_en_jeu/mesure_sorties_retours.lua). Sur la tour, print() est jete par le jeu :
--  les resultats sont donc AFFICHES sur la couche d'affichage toujours visible (overlay, en haut a gauche), et
--  l'orchestrateur (tour/outils/essai_auto.py) en prend une capture de la fenetre du jeu.
--
--  Deroulement : dans le menu, charge la sauvegarde SLOT toute seule ; en partie, repere le porte-avions de
--  l'equipe avec des avions en baie, ordonne la sortie de 4 avions (un waypoint devant le bateau), chronometre en
--  TICKS de jeu (30 par seconde), les rappelle quand les 4 sont en l'air (waypoint sur le porte-avions), chronometre
--  le retour jusqu'au hangar, affiche le bilan, puis quitte le jeu (update_ui_event "quit_game") apres un maintien.
--  Les durees sont en temps de jeu, donc independantes de la vitesse reelle de la simulation.
--
--  Ne modifie ni les fichiers ni les reglages : il ne fait que donner des ordres de vol et lire des etats.
--  Fichier SEPARE des autres scripts du mod de mesures ; tout est protege par pcall.
-- ============================================================================

local SLOT = g_ca_slot_voulu or 18   -- sauvegarde a charger (l'orchestrateur la fixe par --partie ; 18 = ancienne partie du Mac, plante le chargement sur la tour)
local MODE = g_ca_mode or "complet"   -- "menu_seul" : seulement le chargement automatique depuis le menu (aucune accroche en partie) ; sert a isoler un plantage
local HUD = g_ca_hud or false      -- true : panneau aussi sur l'ecran d'indications (interactions.lua). Cet ecran n'a PAS l'API du monde (mesure le 27/10) : defaut false
local NB_AVIONS = 4
local DEVANT = 4000                -- metres devant le bateau (z) pour le waypoint de sortie
local ATTENTE_MENU_S = g_ca_attente_menu or 28          -- secondes REELLES de menu avant l'UNIQUE demande de chargement (laisse le temps de passer l'ecran-titre)
local ATTENTE_JEU = 1800           -- ticks de jeu avant de commencer (60 s de jeu : le pont d'envol d'une partie neuve n'est pas pret a 10 s)
local ABANDON_RECHERCHE = 3000     -- ticks : plus d'avion en baie trouve apres 100 s de jeu -> echec
local DELAI_SORTIE = 9000          -- ticks : les avions ne sont pas tous en l'air apres 5 min de jeu -> echec
local DELAI_RETOUR = 24000         -- ticks : tous les avions ne sont pas rentres apres 13 min de jeu -> bilan partiel
local MAINTIEN_TICKS = 1500        -- ticks de jeu pendant lesquels le bilan reste affiche avant de quitter (~40 s reels a x1,33)
local AFFICHER_NOMS = true         -- calibrage : bande rouge + repere "ca:<nom de l'ecran>" en bas de chaque ecran accroche
local SONDE_QUIT = false           -- calibrage : quitte le jeu depuis le menu si la partie ne s'est pas chargee (voir ca_accrocher)

local VERROU = "__cc2_auto_verrou__"
local ETAT_HANGAR, ETAT_VOL = 4, 0
local ETAT_DEMANDE, ETAT_SORTIE = 2, 3
local ETAT_FILE, ETAT_PISTE, ETAT_PONT = 5, 1, 6

g_ca = g_ca or { etat = "attente", ms = 0, rec = {}, err = nil, info = "", scan = 0, quit = false }

function ca_ticks()
	local ok, t = pcall(update_get_logic_tick)
	if ok and type(t) == "number" then return t end
	return nil
end

function ca_mmss(ticks)
	if ticks == nil then return "--:--" end
	local s = math.floor(ticks / 30 + 0.5)
	if s < 0 then s = 0 end
	return string.format("%d:%02d", math.floor(s / 60), s % 60)
end

function ca_moyenne(liste)
	if #liste == 0 then return nil end
	local somme = 0
	for _, x in ipairs(liste) do somme = somme + x end
	return somme / #liste
end

-- ---------------------------------------------------------------- menu : charger la sauvegarde
function ca_charger()
	local ok, slots = pcall(update_get_save_slots)
	if not ok or type(slots) ~= "table" then g_ca.menu = "slots illisibles"; return end
	for _, v in ipairs(slots) do
		if v.slot_index == SLOT then
			g_ca.menu = "load_game demande"
			update_ui_event("load_game", SLOT)
			return
		end
	end
	g_ca.menu = "slot " .. SLOT .. " absent"
end

-- ---------------------------------------------------------------- partie : reperer porte-avions et avions en baie
function ca_en_baie(c)
	local liste = {}
	for b = 0, 15 do
		local ok, id = pcall(function() return c:get_attached_vehicle_id(b) end)
		if ok and type(id) == "number" and id >= 0 then
			local v = update_get_map_vehicle_by_id(id)
			if v:get() and v:get_dock_state() == ETAT_HANGAR then
				local d = v:get_definition_index()
				if d == e_game_object_type.chassis_air_wing_light or d == e_game_object_type.chassis_air_wing_heavy then
					table.insert(liste, { id = id, def = d })
				end
			end
		end
	end
	return liste
end

-- equipe du joueur : celle de l'ecran, sinon l'unique joueur de la partie. Jamais de supposition : equipe inconnue = aucun ordre.
function ca_equipe()
	local ok, e = pcall(update_get_screen_team_id)
	if ok and type(e) == "number" then return e, "ecran" end
	local okn, n = pcall(update_get_peer_count)
	if okn and n == 1 then
		local okt, team = pcall(update_get_peer_team, 0)
		if okt and type(team) == "number" then return team, "joueur" end
	end
	return nil, "inconnue"
end

function ca_chercher()
	local equipe, source = ca_equipe()
	if equipe == nil then
		g_ca.info = "equipe du joueur inconnue : aucun ordre donne"
		return nil, {}
	end
	if g_ca.chef then            -- ecran de bord : le porte-avions de CET ecran
		local okc, c = pcall(update_get_screen_vehicle)
		if okc and c ~= nil and c:get() then
			local liste_c = ca_en_baie(c)
			g_ca.info = string.format("equipe %s (%s)  porte-avions id %d  avions en baie %d", tostring(equipe), source, c:get_id(), #liste_c)
			return c, liste_c
		end
	end
	local meilleur, meilleure_liste, nb_bateaux = nil, {}, 0
	for i = 0, update_get_map_vehicle_count() - 1 do
		local v = update_get_map_vehicle_by_index(i)
		if v:get() and v:get_definition_index() == e_game_object_type.chassis_carrier and v:get_team() == equipe then
			nb_bateaux = nb_bateaux + 1
			local liste = ca_en_baie(v)
			if meilleur == nil or #liste > #meilleure_liste then meilleur, meilleure_liste = v, liste end
		end
	end
	g_ca.info = string.format("equipe %s (%s)  porte-avions %d  avions en baie %d", tostring(equipe), source, nb_bateaux, #meilleure_liste)
	return meilleur, meilleure_liste
end

-- ---------------------------------------------------------------- suivi
function ca_note(a, cle, t)
	if a[cle] == nil then a[cle] = t end
end

function ca_suivre(t, phase)
	local en_vol, ranges = 0, 0
	for _, a in ipairs(g_ca.rec) do
		local v = update_get_map_vehicle_by_id(a.id)
		if v:get() then
			local s = v:get_dock_state()
			if phase == "sortie" then
				if s == ETAT_DEMANDE then ca_note(a, "t_demande", t)
				elseif s == ETAT_SORTIE then ca_note(a, "t_sortie", t) end
				if s == ETAT_VOL then ca_note(a, "t_air", t) end
			else
				if s == ETAT_FILE then ca_note(a, "t_file", t)
				elseif s == ETAT_PISTE then ca_note(a, "t_piste", t)
				elseif s == ETAT_PONT then ca_note(a, "t_pont", t)
				elseif s == ETAT_HANGAR then ca_note(a, "t_hangar", t) end
			end
		end
		if a.t_air then en_vol = en_vol + 1 end
		if a.t_hangar then ranges = ranges + 1 end
	end
	return en_vol, ranges
end

function ca_terminer(t, etat, message)
	local s = g_ca
	s.etat, s.t_fin, s.message, s.ms_fin = etat, t, message, s.ms
end

function ca_pas(t)
	local s = g_ca
	if s.etat == "attente" then
		if t < ATTENTE_JEU then return end
		if s.scan ~= 0 and t - s.scan < 30 then return end
		s.scan = t
		local c, liste = ca_chercher()
		if c == nil or #liste == 0 then
			if t > ABANDON_RECHERCHE then ca_terminer(t, "echec", "aucun avion en baie trouve") end
			return
		end
		s.porte = c:get_id()
		local pos = c:get_position_xz()
		local px, pz = pos:x(), pos:y()
		s.t_cmd = t
		for i = 1, math.min(NB_AVIONS, #liste) do s.rec[i] = { id = liste[i].id, def = liste[i].def } end
		local refus = 0
		for _, a in ipairs(s.rec) do
			local v = update_get_map_vehicle_by_id(a.id)
			local ok, err = pcall(function()
				v:clear_waypoints(); v:clear_attack_target(); v:add_waypoint(px, pz + DEVANT)
			end)
			if not ok then refus = refus + 1; s.err = "ordre refuse : " .. tostring(err) end
		end
		if refus == #s.rec then
			ca_terminer(t, "echec", "tous les ordres de sortie refuses depuis cette couche")
		else
			s.etat = "sortie"
		end
		return
	end

	if s.etat == "sortie" then
		local en_vol = ca_suivre(t, "sortie")
		-- Constate le 27/10 en partie neuve : les 4 avions recoivent bien leur waypoint (w1) mais restent au hangar (etat 4). On renouvelle donc
		-- l'ordre toutes les 20 s de jeu tant qu'aucun avion n'a bouge (8 fois au plus) ; le chrono de sortie repart du dernier ordre.
		local bouge = false
		for _, a in ipairs(s.rec) do if a.t_demande or a.t_sortie or a.t_air then bouge = true end end
		if not bouge and (s.essais_ordre or 1) < 9 and t - (s.t_ordre or s.t_cmd) >= 600 then
			s.essais_ordre, s.t_ordre, s.t_cmd = (s.essais_ordre or 1) + 1, t, t
			local cb = update_get_map_vehicle_by_id(s.porte)
			local posb = cb:get_position_xz()
			for _, a in ipairs(s.rec) do
				local vb = update_get_map_vehicle_by_id(a.id)
				pcall(function() vb:clear_waypoints(); vb:clear_attack_target(); vb:add_waypoint(posb:x(), posb:y() + DEVANT) end)
			end
		end
		if en_vol == #s.rec then
			local c = update_get_map_vehicle_by_id(s.porte)
			local pos = c:get_position_xz()
			s.t_rappel = t
			for _, a in ipairs(s.rec) do
				local v = update_get_map_vehicle_by_id(a.id)
				local ok, err = pcall(function()
					v:clear_waypoints(); v:clear_attack_target()
					local wp = v:add_waypoint(pos:x(), pos:y())
					v:set_target_vehicle(wp, s.porte)
				end)
				if not ok then s.err = "rappel refuse : " .. tostring(err) end
			end
			s.etat = "retour"
		elseif t - s.t_cmd > DELAI_SORTIE then
			ca_terminer(t, "echec", "sortie : tous les avions ne sont pas en l'air a temps")
		end
		return
	end

	if s.etat == "retour" then
		local _, rentres = ca_suivre(t, "retour")
		if rentres == #s.rec then
			ca_terminer(t, "fin", "retours termines")
		elseif t - s.t_rappel > DELAI_RETOUR then
			ca_terminer(t, "fin", "retours : delai depasse (bilan partiel)")
		end
		return
	end
end

-- ---------------------------------------------------------------- affichage
function ca_bilan()
	local s = g_ca
	local sortie_max, retour_max, approches, ponts, pistes = nil, nil, {}, {}, {}
	for _, a in ipairs(s.rec) do
		if a.t_air and s.t_cmd and (sortie_max == nil or a.t_air - s.t_cmd > sortie_max) then sortie_max = a.t_air - s.t_cmd end
		if a.t_hangar and s.t_rappel and (retour_max == nil or a.t_hangar - s.t_rappel > retour_max) then retour_max = a.t_hangar - s.t_rappel end
		if a.t_piste and a.t_pont then table.insert(approches, a.t_pont - a.t_piste) end
		if a.t_pont and a.t_hangar then table.insert(ponts, a.t_hangar - a.t_pont) end
		if a.t_piste then table.insert(pistes, a.t_piste) end
	end
	table.sort(pistes)
	local ecarts = {}
	for i = 2, #pistes do table.insert(ecarts, pistes[i] - pistes[i - 1]) end
	return sortie_max, retour_max, ca_moyenne(approches), ca_moyenne(ponts), ca_moyenne(ecarts)
end

-- resultat BRUT d'un appel de l'API depuis cet ecran (valeur ou ERR) : sert a savoir ce qui est disponible depuis l'ecran d'indications
function ca_sonde(nom)
	local court = string.gsub(nom, "^update_get_", "")
	local f = _G[nom]                       -- lecture normale (l'API peut passer par une metatable), pas rawget
	if type(f) ~= "function" then return court .. "=" .. type(f) end
	local ok, v = pcall(f)
	if ok then return court .. "=" .. tostring(v) end
	return court .. "=ERR(" .. string.sub(tostring(v), 1, 40) .. ")"
end

function ca_lignes()
	local s = g_ca
	local blanc, orange, vert, rouge = color8(255, 255, 255, 255), color8(255, 200, 80, 255), color8(110, 255, 140, 255), color8(255, 120, 120, 255)
	local t = ca_ticks() or 0
	local lignes = {}
	local sim = ""
	if s.tick0 and s.ms - s.ms0 > 5000 then
		sim = string.format("   SIM x%.2f", ((t - s.tick0) / 30) / ((s.ms - s.ms0) / 1000))
	end
	table.insert(lignes, { string.format("ESSAI AUTO cc2_auto : %s   tick %d (%s)   reel %s%s", s.etat, t, ca_mmss(t), ca_mmss(s.ms / 1000 * 30), sim), orange })
	table.insert(lignes, { (s.info ~= "" and s.info or "en attente de la partie") .. "   [slots charges : " .. tostring(g_ca_slots) .. "]", blanc })
	table.insert(lignes, { "api : " .. ca_sonde("update_get_logic_tick") .. "  " .. ca_sonde("update_get_map_vehicle_count") .. "  "
		.. ca_sonde("update_get_screen_team_id") .. "  " .. ca_sonde("update_get_peer_count") .. "  " .. ca_sonde("update_get_time_since_epoch"), blanc })
	table.insert(lignes, { "api : " .. ca_sonde("update_get_join_password") .. "  " .. ca_sonde("update_get_screen_vehicle") .. "  "
		.. ca_sonde("begin_get_screen_name") .. "  ui_event=" .. type(update_ui_event) .. "  save_slots=" .. type(update_get_save_slots)
		.. "  by_index=" .. type(update_get_map_vehicle_by_index), blanc })
	if #s.rec > 0 then
		table.insert(lignes, { "av        decol(depuis ordre)   file   piste   pont   hangar  (retour depuis rappel)", blanc })
		for k, a in ipairs(s.rec) do
			local function rel(x, base) if x and base then return ca_mmss(x - base) end return "--:--" end
			table.insert(lignes, { string.format("%d id%-5d   %s         %s   %s   %s   %s", k, a.id,
				rel(a.t_air, s.t_cmd), rel(a.t_file, s.t_rappel), rel(a.t_piste, s.t_rappel), rel(a.t_pont, s.t_rappel), rel(a.t_hangar, s.t_rappel)), blanc })
		end
	end
	if s.etat == "fin" or s.etat == "echec" then
		local sortie, retour, approche, pont, ecart = ca_bilan()
		table.insert(lignes, { string.format("%s : %s", s.etat == "fin" and "BILAN" or "ECHEC", s.message or ""), s.etat == "fin" and vert or rouge })
		table.insert(lignes, { string.format("SORTIE : %d avions en l'air en %s", #s.rec, ca_mmss(sortie)), vert })
		table.insert(lignes, { string.format("RETOUR : FINI en %s   piste toutes les %s   approche %s   pont>hangar %s",
			ca_mmss(retour), ca_mmss(ecart), ca_mmss(approche), ca_mmss(pont)), vert })
		table.insert(lignes, { string.format("fin des mesures, le jeu se ferme dans %d s", math.max(0, math.floor((MAINTIEN_TICKS - (t - (s.t_fin or t))) / 30))), orange })
	end
	if s.err then table.insert(lignes, { s.err, rouge }) end
	return lignes
end

function ca_dessiner(screen_w, screen_h)
	local lignes = ca_lignes()
	local w, th = 0, 0
	for _, l in ipairs(lignes) do
		local tw, h = update_ui_get_text_size(l[1], 1400, 0)
		if tw > w then w = tw end
		th = h
	end
	w = math.min(w + 8, screen_w - 16)
	local h = #lignes * (th + 1) + 4
	local x, y = 8, 8
	update_ui_rectangle(x, y, w, h, color8(0, 0, 0, 225))
	for k, l in ipairs(lignes) do
		update_ui_text(x + 4, y + 2 + (k - 1) * (th + 1), l[1], w - 8, 0, l[2], 0)
	end
end

-- appele a chaque image de la couche d'affichage
function ca_image(screen_w, screen_h, delta_time)
	local s = g_ca
	s.ms = s.ms + (delta_time or 0)
	-- La couche est cachee par son propre script (update_set_is_visible(g_loading_alpha > 0)) : sans forcage, rien ne s'affiche en partie.
	-- Mais forcer la visibilite AVANT la fin du chargement a coincide avec 4 plantages sur 4 au demarrage d'une partie : on ne la force
	-- donc qu'apres avoir vu un chargement se terminer (g_is_loading vrai puis faux), plus 300 images (~2 s).
	if rawget(_G, "g_is_loading") then
		s.vu_chargement, s.images_apres = true, 0
	elseif s.vu_chargement then
		s.images_apres = (s.images_apres or 0) + 1
		if s.images_apres > 300 then pcall(update_set_is_visible, true) end
	end
	local t = ca_ticks()
	if t ~= nil and t > 0 and s.tick0 == nil then s.tick0, s.ms0 = t, s.ms end
	if t ~= nil and s.etat ~= "fin" and s.etat ~= "echec" then
		local ok, err = pcall(ca_pas, t)
		if not ok then s.err = "erreur : " .. tostring(err) end
	end
	local ok, err = pcall(ca_dessiner, screen_w, screen_h)
	if not ok then s.err = "affichage : " .. tostring(err) end
	if (s.etat == "fin" or s.etat == "echec") and t ~= nil and s.t_fin and t - s.t_fin > MAINTIEN_TICKS and not s.quit then
		s.quit = true
		pcall(update_ui_event, "quit_game")
	end
end

-- ---------------------------------------------------------------- logique dans screen_veh_m (ecran de bord : il a l'API du monde)
-- Mesure du 27/10 : l'ecran d'indications ET la couche overlay n'ont PAS l'API du monde (update_get_logic_tick, map_vehicle_*, screen_team_id... = nil).
-- Seuls les ecrans de bord l'ont (comme le chronometre du mod de mesures). La logique tourne donc ici ; les resultats sortent sur cet ecran
-- et dans le chat du jeu (update_ui_event "chat"), que l'ecran d'indications dessine en permanence.

-- le "chef" : parmi les porte-avions de l'equipe, celui dont l'identifiant est le plus petit ; les ecrans des autres porte-avions restent passifs
function ca_est_chef()
	local s = g_ca
	if s.chef ~= nil then return s.chef end
	local ok, c = pcall(update_get_screen_vehicle)
	if not ok or c == nil or not c:get() then return false end
	local equipe, min_id = c:get_team(), c:get_id()
	for i = 0, update_get_map_vehicle_count() - 1 do
		local v = update_get_map_vehicle_by_index(i)
		if v:get() and v:get_definition_index() == e_game_object_type.chassis_carrier and v:get_team() == equipe and v:get_id() < min_id then
			s.chef = false
			return false
		end
	end
	s.chef = true
	return true
end

-- Boite aux lettres lisible SANS capture : le mot de passe d'hebergement du jeu est enregistre dans persistent_data.xml, que
-- l'orchestrateur lit pendant la partie. Ticks de jeu bruts (30 par seconde) ; "-" = pas encore.
function ca_mail(t)
	local s = g_ca
	local function n(x) return x and tostring(x) or "-" end
	local p = { "CA", s.etat, "t=" .. tostring(t), "cmd=" .. n(s.t_cmd), "rap=" .. n(s.t_rappel), "fin=" .. n(s.t_fin), "o=" .. n(s.essais_ordre) }
	do
		-- vitesse lue sur l'objet "vehicule de l'ecran" (comme screen_propulsion.lua), puis sur celui de la carte ; focus = le joueur est-il sur cet ecran ?
		local okc, cv = pcall(update_get_screen_vehicle)
		local okv, vit = false, nil
		if okc and cv ~= nil and cv:get() then okv, vit = pcall(function() return cv:get_velocity_magnitude() end) end
		if okv and type(vit) == "number" then table.insert(p, string.format("noeuds=%.1f", vit * 1.94)) else table.insert(p, "noeuds=?") end
		local okf, foc = pcall(update_get_is_focus_local)
		table.insert(p, "foc=" .. (okf and tostring(foc) or "?"))
	end
	for k, a in ipairs(s.rec) do
		-- air/file/piste/pont/hangar (ticks) puis etat d'accostage actuel, carburant, munitions, nombre de waypoints, demande/sortie vus
		local v = update_get_map_vehicle_by_id(a.id)
		local st, fu, am, wp = "?", "?", "?", "?"
		if v:get() then
			st = tostring(v:get_dock_state())
			local okf, f = pcall(function() return v:get_fuel_factor() end)
			if okf and type(f) == "number" then fu = string.format("%.2f", f) end
			local oka, m = pcall(function() return v:get_ammo_factor() end)
			if oka and type(m) == "number" then am = string.format("%.2f", m) end
			local okw, w = pcall(function() return v:get_waypoint_count() end)
			if okw and type(w) == "number" then wp = tostring(w) end
			local okb, bf = pcall(function() return v:get_is_fuel_blocked() end)
			local okm, bm = pcall(function() return v:get_is_ammo_blocked() end)
			wp = wp .. "/bf" .. (okb and tostring(bf) or "?") .. "/bm" .. (okm and tostring(bm) or "?")
		end
		table.insert(p, string.format("a%d=%s/%s/%s/%s/%s/st%s/f%s/m%s/w%s/d%s/s%s", k, n(a.t_air), n(a.t_file), n(a.t_piste), n(a.t_pont), n(a.t_hangar),
			st, fu, am, wp, n(a.t_demande), n(a.t_sortie)))
	end
	table.insert(p, (string.gsub(s.info or "", "[;\"<>&]", " ")))
	if s.err then table.insert(p, "ERR " .. string.sub((string.gsub(tostring(s.err), "[;\"<>&]", " ")), 1, 60)) end
	local texte = string.sub(table.concat(p, ";"), 1, 480)
	pcall(update_set_host_password, texte)
	return texte
end

function ca_chat(t)
	local s = g_ca
	pcall(ca_mail, t)
	-- le chat du jeu n'affiche un message que ~5 s : un message court (battement de coeur) toutes les 5 s de jeu, le detail toutes les 15 s
	if s.t_chat and t - s.t_chat < 150 then return end
	s.t_chat = t
	s.n_chat = (s.n_chat or 0) + 1
	if s.n_chat % 3 ~= 1 and s.etat ~= "fin" and s.etat ~= "echec" then
		pcall(update_ui_event, "chat", string.sub(string.format("CA %s t=%s #%d", s.etat, ca_mmss(t), s.n_chat), 1, 120))
		return
	end
	local function rel(x, base) if x and base then return ca_mmss(x - base) end return "--" end
	local msgs = {}
	table.insert(msgs, string.format("CA %s t=%s %s", s.etat, ca_mmss(t), s.info or ""))
	if not s.sonde_dite then
		s.sonde_dite = true
		table.insert(msgs, "CA api " .. ca_sonde("update_get_logic_tick") .. " " .. ca_sonde("update_get_map_vehicle_count") .. " " .. ca_sonde("update_get_screen_team_id"))
	end
	for k, a in ipairs(s.rec) do
		table.insert(msgs, string.format("CA av%d air=%s file=%s piste=%s pont=%s hangar=%s", k,
			rel(a.t_air, s.t_cmd), rel(a.t_file, s.t_rappel), rel(a.t_piste, s.t_rappel), rel(a.t_pont, s.t_rappel), rel(a.t_hangar, s.t_rappel)))
	end
	if s.etat == "fin" or s.etat == "echec" then
		local sortie, retour, approche, pont, ecart = ca_bilan()
		table.insert(msgs, string.format("CA BILAN %s : sortie %s retour %s piste/%s approche %s pont>hangar %s",
			s.etat, ca_mmss(sortie), ca_mmss(retour), ca_mmss(ecart), ca_mmss(approche), ca_mmss(pont)))
	end
	if s.err then table.insert(msgs, "CA ERR " .. string.sub(s.err, 1, 100)) end
	for _, m in ipairs(msgs) do pcall(update_ui_event, "chat", string.sub(m, 1, 120)) end
end

function ca_logique(screen_w, screen_h)
	local s = g_ca
	local t = ca_ticks()
	if t == nil then return end
	local okt, e = pcall(update_get_time_since_epoch)
	if okt and type(e) == "number" then s.e_debut = s.e_debut or e; s.ms = (e - s.e_debut) * 1000 end
	if t > 0 and s.tick0 == nil then s.tick0, s.ms0 = t, s.ms end
	if t >= ATTENTE_JEU and not ca_est_chef() then s.etat = "passif"; return end
	if s.etat ~= "fin" and s.etat ~= "echec" and s.etat ~= "passif" then
		local ok, err = pcall(ca_pas, t)
		if not ok then s.err = "erreur : " .. tostring(err) end
	end
	pcall(ca_dessiner, screen_w, screen_h)
	pcall(ca_chat, t)
	if (s.etat == "fin" or s.etat == "echec") and s.t_fin and t - s.t_fin > MAINTIEN_TICKS and not s.quit then
		s.quit = true
		pcall(update_ui_event, "quit_game")
	end
end

-- ---------------------------------------------------------------- greffe (comme le journal des sorties et la Boite noire)
-- petit texte de reperage en bas de chaque ecran accroche (calibrage : nom de l'ecran, ecran du menu, nombre d'images)
function ca_nom(screen_w, screen_h, nom, est_menu, n)
	local texte = string.format("ca[%s]:%s%s #%d %s", tostring(g_ca_slots), nom, est_menu and " MENU" or "", n, g_ca.menu or "")
	update_ui_rectangle(0, screen_h - 14, screen_w, 14, color8(200, 0, 0, 255))       -- bande rouge : preuve visible que l'accroche tourne
	update_ui_text(2, screen_h - 12, texte, screen_w - 4, 0, color8(255, 255, 255, 255), 0)
end

-- ecrans "ordinaires" (menu, ecrans de bord) : le jeu appelle begin() puis begin_load() (library_util), qu'on a enveloppe
function ca_accrocher()
	if type(update) ~= "function" or g_ca_accroche then return end
	-- ecran d'indications du jeu (interactions.lua : "p/esc pause", "e interact") : dessine en permanence sur toute la fenetre, menu comme
	-- partie ; il appelle begin_load comme les autres ecrans, donc accroche legere (pas de surveillance des variables globales)
	if HUD and MODE ~= "menu_seul" and rawget(_G, "g_interactions") ~= nil then
		g_ca_accroche = true
		local origine_hud = update
		update = function(screen_w, screen_h, delta_time, ...)
			origine_hud(screen_w, screen_h, delta_time, ...)
			pcall(ca_image, screen_w, screen_h, delta_time)
		end
		return
	end
	if MODE == "menu_seul" and rawget(_G, "g_is_menu_active") == nil then return end
	g_ca_accroche = true
	local nom = "?"
	if type(begin_get_screen_name) == "function" then
		local ok, valeur = pcall(begin_get_screen_name)
		if ok and valeur ~= nil then nom = tostring(valeur) end
	end
	if nom == "screen_veh_m" and MODE ~= "menu_seul" then
		local origine_veh = update
		update = function(screen_w, screen_h, ...)
			local retours = table.pack(origine_veh(screen_w, screen_h, ...))
			pcall(ca_logique, screen_w, screen_h)
			return table.unpack(retours, 1, retours.n)
		end
		return
	end
	local est_menu = rawget(_G, "g_is_menu_active") ~= nil      -- defini en tete de screen_menu_main.lua seulement
	local origine = update
	local n = 0
	update = function(screen_w, screen_h, ...)
		local retours = table.pack(origine(screen_w, screen_h, ...))
		n = n + 1
		if est_menu and not g_ca.charge_fait then
			local ok, e = pcall(update_get_time_since_epoch)
			if ok and type(e) == "number" then
				g_ca.e0 = g_ca.e0 or e
				if e - g_ca.e0 >= ATTENTE_MENU_S then
					-- Le menu a PLUSIEURS ecrans (au moins 4) qui executent chacun ce script dans leur propre contexte Lua : sans verrou,
					-- chacun demande le chargement en meme temps et le jeu plante (0xC0000005 dans la meme fonction, constate 4 fois le 27/10).
					-- Verrou commun = le mot de passe de connexion du jeu (valeur unique, partagee, non enregistree sur disque) :
					-- le premier ecran qui passe ici le change et charge, les autres voient le verrou et ne font rien.
					g_ca.charge_fait = true
					local okp, mdp = pcall(update_get_join_password)
					if okp and mdp ~= VERROU then
						pcall(update_set_join_password, VERROU)
						pcall(ca_charger)
					end
				end
			end
		end
		if AFFICHER_NOMS then pcall(ca_nom, screen_w, screen_h, nom, est_menu, n) end
		-- sonde de calibrage : si l'ecran du menu tourne encore ~30 s apres le debut sans que la partie se charge, on quitte le jeu
		-- (preuve que ce script s'execute, meme si load_game n'a rien fait)
		if SONDE_QUIT and est_menu and n == 4500 then pcall(update_ui_event, "quit_game") end
		return table.unpack(retours, 1, retours.n)
	end
end

-- couche d'affichage (overlay.lua) : le jeu n'y appelle jamais begin_load. Comme la Boite noire, on guette la creation de
-- la globale "update" (les bibliotheques sont chargees AVANT le script de l'etat) et on l'enveloppe si l'etat est l'overlay.
function ca_est_overlay(t)
	return rawget(t, "g_is_loading") ~= nil or rawget(t, "g_loading_text") ~= nil
end

function ca_envelopper_overlay(update_jeu)
	g_ca_accroche = true
	return function(screen_w, screen_h, tick_fraction, delta_time)
		update_jeu(screen_w, screen_h, tick_fraction, delta_time)
		pcall(ca_image, screen_w, screen_h, delta_time)
	end
end

function ca_guetter()
	if rawget(_G, "update") ~= nil then          -- script de l'etat deja charge
		if ca_est_overlay(_G) and not g_ca_accroche then rawset(_G, "update", ca_envelopper_overlay(rawget(_G, "update"))) end
		return
	end
	local mt_avant = getmetatable(_G)
	if mt_avant ~= nil and type(mt_avant) ~= "table" then return end
	local mt = {}
	local suivant = nil
	if mt_avant ~= nil then
		for k, v in pairs(mt_avant) do mt[k] = v end
		suivant = mt_avant.__newindex
	end
	mt.__newindex = function(t, k, v)
		if k == "update" and type(v) == "function" then
			if not g_ca_accroche and ca_est_overlay(t) then v = ca_envelopper_overlay(v) end
			pcall(setmetatable, t, mt_avant)         -- "update" defini : on rend la main
		end
		if type(suivant) == "function" then
			suivant(t, k, v)
		elseif type(suivant) == "table" then
			suivant[k] = v
		else
			rawset(t, k, v)
		end
	end
	setmetatable(_G, mt)
end

if not g_ca_installe then
	g_ca_installe = true
	g_ca_begin_load_origine = begin_load
	begin_load = function(...)
		local retours = { n = 0 }
		if g_ca_begin_load_origine ~= nil then retours = table.pack(g_ca_begin_load_origine(...)) end
		pcall(ca_accrocher)
		return table.unpack(retours, 1, retours.n)
	end
	-- couche overlay.lua : la seule qui voie le monde ET s'affiche partout (c'est ou se dessine la Boite noire du moddeur)
	if MODE ~= "menu_seul" then pcall(ca_guetter) end
end
