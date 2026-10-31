-- Mini cadre de test pour le banc Lua de Carrier Command 2 (Lua 5.3 pur, aucune dependance).
--
-- Un FICHIER de scenarios appelle  cadre.groupe("nom", function() ... end)  puis, dedans,
--   cadre.scenario("nom", function(t) ... end)
-- et dans un scenario :
--   t:verifier(condition, "message" [, detail])      une verification
--   t:egal(obtenu, attendu, "message")                egalite (tables comparees en profondeur)
--   t:bug("B-01", "titre", function() return reproduit, detail end)
--        BUG CONNU DANS UN SCRIPT SOURCE (voir BUGS_TROUVES.md). Le test PASSE tant que le bug se reproduit.
--        Si le script source est corrige un jour, le test devient ROUGE : "bug non reproduit, mettre a jour BUGS_TROUVES.md".
--   t:risque("R-01", "hypothese sur le vrai moteur", function() return conforme_a_la_description, detail end)
--        RISQUE qui depend d'une hypothese NON verifiable hors du jeu. Meme logique que t:bug.
--
-- Sortie : une ligne par scenario, puis un bilan ; code de sortie 1 s'il y a un echec.

local Cadre = { resultats = {}, groupe_courant = "?", verbeux = false, filtre = nil }

local function copie_texte(v)
	if type(v) == "string" then return string.format("%q", v) end
	return tostring(v)
end

local function egal_profond(a, b)
	if type(a) ~= type(b) then return false end
	if type(a) ~= "table" then return a == b end
	for k, v in pairs(a) do if not egal_profond(v, b[k]) then return false end end
	for k in pairs(b) do if a[k] == nil then return false end end
	return true
end

local function decrire(v, profondeur)
	profondeur = profondeur or 0
	if type(v) ~= "table" then return copie_texte(v) end
	if profondeur > 2 then return "{...}" end
	local morceaux, n = {}, 0
	for k, x in pairs(v) do
		n = n + 1
		if n > 12 then morceaux[#morceaux + 1] = "..."; break end
		morceaux[#morceaux + 1] = tostring(k) .. "=" .. decrire(x, profondeur + 1)
	end
	table.sort(morceaux)
	return "{" .. table.concat(morceaux, ", ") .. "}"
end
Cadre.decrire = decrire

local T = {}
T.__index = T

function T:verifier(condition, message, detail)
	self.nb = self.nb + 1
	if not condition then
		self.echecs[#self.echecs + 1] = message .. ((detail ~= nil) and (" -- " .. tostring(detail)) or "")
	end
	return condition and true or false
end

function T:egal(obtenu, attendu, message)
	local ok = egal_profond(obtenu, attendu)
	return self:verifier(ok, message, ok and nil or ("obtenu " .. decrire(obtenu) .. " ; attendu " .. decrire(attendu)))
end

function T:note(message)
	self.notes[#self.notes + 1] = message
end

-- bug connu / risque : le test passe tant que le constat est reproduit
local function constat(self, genre, id, titre, fn)
	self.nb = self.nb + 1
	local ok, reproduit, detail = pcall(fn)
	if not ok then
		self.echecs[#self.echecs + 1] = string.format("%s %s : le constat a plante : %s", genre, id, tostring(reproduit))
	elseif not reproduit then
		self.echecs[#self.echecs + 1] = string.format(
			"%s %s NON REPRODUIT (%s)%s -- le script source a-t-il ete corrige ? Mettre a jour BUGS_TROUVES.md et ce test.",
			genre, id, titre, detail and (" : " .. tostring(detail)) or "")
	else
		self.constats[#self.constats + 1] = string.format("%s %s reproduit : %s%s", genre, id, titre, detail and (" (" .. tostring(detail) .. ")") or "")
	end
end
function T:bug(id, titre, fn) constat(self, "BUG", id, titre, fn) end
function T:risque(id, titre, fn) constat(self, "RISQUE", id, titre, fn) end

-- le groupe enregistre ses scenarios (fn() les declare) ; ils sont executes ensuite, apres filtrage
function Cadre.groupe(nom, fn)
	Cadre.groupe_courant = nom
	Cadre.en_cours = Cadre.en_cours or {}
	Cadre.en_cours[#Cadre.en_cours + 1] = { nom = nom, scenarios = {} }
	fn()
end

function Cadre.scenario(nom, fn)
	local g = Cadre.en_cours[#Cadre.en_cours]
	g.scenarios[#g.scenarios + 1] = { nom = nom, fn = fn }
end

function Cadre.executer(filtre)
	local total_ok, total_echec, total_verif, total_constats = 0, 0, 0, 0
	for _, g in ipairs(Cadre.en_cours or {}) do
		print(("\n== %s"):format(g.nom))
		for _, s in ipairs(g.scenarios) do
			if not filtre or (g.nom .. " " .. s.nom):find(filtre, 1, true) then
				local t = setmetatable({ nb = 0, echecs = {}, constats = {}, notes = {} }, T)
				local ok, err = xpcall(s.fn, function(e) return debug.traceback(tostring(e), 2) end, t)
				if not ok then t.echecs[#t.echecs + 1] = "le scenario a plante : " .. tostring(err) end
				total_verif = total_verif + t.nb
				total_constats = total_constats + #t.constats
				if #t.echecs == 0 then
					total_ok = total_ok + 1
					print(("  OK      %-62s %d verif."):format(s.nom, t.nb))
				else
					total_echec = total_echec + 1
					print(("  ECHEC   %s"):format(s.nom))
					for _, e in ipairs(t.echecs) do print("            - " .. e) end
				end
				for _, c in ipairs(t.constats) do print("            * " .. c) end
				if Cadre.verbeux then for _, n in ipairs(t.notes) do print("            . " .. n) end end
			end
		end
	end
	print(("\nBILAN : %d scenario(s) OK, %d en echec, %d verification(s), %d constat(s) de bug/risque reproduit(s)")
		:format(total_ok, total_echec, total_verif, total_constats))
	return total_echec == 0
end

-- enregistre un fichier de scenarios : il appelle cadre.groupe(...) a son chargement
function Cadre.charger_fichier(chemin)
	local f, err = loadfile(chemin)
	if not f then error("scenario illisible : " .. tostring(err), 0) end
	f(Cadre)
end

return Cadre
