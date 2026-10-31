-- Registre des fonctions de la FAUSSE API : chaque fonction declaree dit d'ou vient ce qu'on en sait.
--   DOC      decrit dans la documentation du depot (LUA_API.md, WORLD_API.md, partage_detail/, notes de passation)
--   SCRIPT   non documente, mais appele par un script du depot : la FORME de l'appel est connue, le comportement est DEVINE
--   SUPPOSE  rien ne l'etablit : choix du banc pour pouvoir faire tourner le script (a confirmer en jeu)
-- `python lancer.py --inventaire` ecrit INVENTAIRE_API.md a partir de ce registre.

local Inv = { lignes = {}, vus = {} }

function Inv.decl(famille, nom, statut, note)
	assert(statut == "DOC" or statut == "SCRIPT" or statut == "SUPPOSE", "statut inconnu : " .. tostring(statut))
	local cle = famille .. "." .. nom
	if Inv.vus[cle] then return end
	Inv.vus[cle] = true
	Inv.lignes[#Inv.lignes + 1] = { famille = famille, nom = nom, statut = statut, note = note }
end

function Inv.markdown()
	local out = {
		"# Inventaire de la fausse API (généré par `python lancer.py --inventaire`, ne pas éditer à la main)",
		"",
		"Statuts : **DOC** = décrit dans la documentation du dépôt ; **SCRIPT** = non documenté, appelé par un script du dépôt (forme de l'appel connue,",
		"comportement deviné) ; **SUPPOSÉ** = rien ne l'établit, choix du banc (à confirmer en jeu).",
		"",
	}
	local par_famille, ordre = {}, {}
	for _, l in ipairs(Inv.lignes) do
		if not par_famille[l.famille] then par_famille[l.famille] = {}; ordre[#ordre + 1] = l.famille end
		table.insert(par_famille[l.famille], l)
	end
	for _, fam in ipairs(ordre) do
		out[#out + 1] = "## " .. fam
		out[#out + 1] = ""
		out[#out + 1] = "| Nom | Statut | Ce que fait la fausse version |"
		out[#out + 1] = "|---|---|---|"
		for _, l in ipairs(par_famille[fam]) do
			out[#out + 1] = string.format("| `%s` | %s | %s |", l.nom, l.statut == "SUPPOSE" and "SUPPOSÉ" or l.statut, (l.note or ""):gsub("|", "\\|"))
		end
		out[#out + 1] = ""
	end
	return table.concat(out, "\n")
end

return Inv
