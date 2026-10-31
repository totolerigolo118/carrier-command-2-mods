-- FAUSSE g_ui : l'objet d'interface que les ecrans de controle des vehicules (library_ui.lua) fournissent aux scripts.
-- Rien de ce fichier n'est dans la documentation du depot : tout est deduit de l'USAGE qu'en font
-- tour/etudes_modes_carburant/lua/library_custom_5.lua et v2/library_custom_5.lua (statut SCRIPT ou SUPPOSE).
-- Ce que ces scripts ont besoin de la pile d'interface : window_stack / region_stack (tableaux), begin_window / end_window,
-- get_window() (champs cx, cy, is_active), get_region() (largeur), hoverable, spacer, text_basic, input_pointer_1.

local Inv = require("fausse_api.inventaire")
local decl = Inv.decl

local UI = {}

function UI.nouvelle(ctx)
	local ui = {
		window_stack = {},          -- SCRIPT : les scripts lisent #ui.window_stack et rappellent end_window pour reparer
		region_stack = {},          -- SCRIPT : idem, et ils depilent a la main (ui.region_stack[#...] = nil)
		input_pointer_1 = false,    -- SCRIPT : clic gauche de cette image ; le script le remet a false quand il le consomme
		pointeur = nil,             -- BANC : { x =, y = } position de la souris en coordonnees d'ecran (nil = hors ecran)
		fenetre_active = true,      -- BANC : valeur donnee a window.is_active des fenetres ouvertes
		dessinees = {},             -- BANC : fenetres ouvertes pendant l'image courante (pour les assertions)
		faute = nil,                -- BANC : { methode = "text_basic", message = "..." } -> cette methode LEVE une erreur
		appels = 0,
	}

	-- ui.faute = { methode = "text_basic", fenetre = "SPEED##cm_speed" (facultatif : seulement quand cette fenetre est au dessus), message = "...", empile_region = true (facultatif) }
	local function piege(nom)
		ui.appels = ui.appels + 1
		local f = ui.faute
		if f and f.methode == nom then
			local dessus = ui.window_stack[#ui.window_stack]
			if not f.fenetre or (dessus and dessus.titre == f.fenetre) or (nom == "begin_window" and f.fenetre == "*") then
				if f.empile_region then ui.region_stack[#ui.region_stack + 1] = { w = 1 } end     -- panne qui laisse une region ouverte de plus
				error(f.message or ("faute injectee dans " .. nom), 2)
			end
		end
	end

	decl("g_ui", "begin_window", "SCRIPT", "empile une fenetre (titre, x, y, w, h, icone, flag, niveau) sur window_stack ET region_stack (SUPPOSE) ; contenu a x+2, y+12")
	function ui:begin_window(titre, x, y, w, h, icone, souris, niveau)
		piege("begin_window")
		if type(titre) ~= "string" then error("begin_window : titre attendu", 2) end
		for i, v in ipairs({ x, y, w, h }) do
			if type(v) ~= "number" then error("begin_window : argument numerique attendu (" .. i .. ")", 2) end
		end
		local fen = { titre = titre, x = x, y = y, w = w, h = h, icone = icone, souris = souris, niveau = niveau,
			cx = x + 2, cy = y + 12, is_active = self.fenetre_active, textes = {}, couleurs = {}, boutons = 0 }
		self.window_stack[#self.window_stack + 1] = fen
		self.region_stack[#self.region_stack + 1] = { w = w - 4 }
		self.dessinees[#self.dessinees + 1] = fen
		return fen
	end

	decl("g_ui", "end_window", "SCRIPT", "depile la fenetre ET sa region ; erreur si la pile est vide")
	function ui:end_window()
		piege("end_window")
		if #self.window_stack == 0 then error("end_window : aucune fenetre ouverte", 2) end
		self.window_stack[#self.window_stack] = nil
		self.region_stack[#self.region_stack] = nil
	end

	decl("g_ui", "get_window", "SCRIPT", "fenetre du dessus (cx, cy = curseur de mise en page en coordonnees d'ecran, is_active)")
	function ui:get_window()
		piege("get_window")
		local f = self.window_stack[#self.window_stack]
		if not f then error("get_window : aucune fenetre ouverte", 2) end
		return f
	end

	decl("g_ui", "get_region", "SCRIPT", "largeur utile de la region courante (nombre)")
	function ui:get_region()
		piege("get_region")
		local r = self.region_stack[#self.region_stack]
		if not r then error("get_region : aucune region", 2) end
		return r.w
	end

	decl("g_ui", "hoverable", "SCRIPT", "vrai si le pointeur du banc est dans le rectangle (x, y, w, h) ; 5e argument ignore")
	function ui:hoverable(x, y, w, h)
		piege("hoverable")
		local p = self.pointeur
		return p ~= nil and p.x >= x and p.x < x + w and p.y >= y and p.y < y + h
	end

	decl("g_ui", "spacer", "SCRIPT", "descend le curseur de mise en page de n unites")
	function ui:spacer(n)
		piege("spacer")
		local f = self:get_window()
		f.cy = f.cy + (n or 0)
	end

	decl("g_ui", "text_basic", "SCRIPT", "ecrit une ligne (texte, couleur1, couleur2) dans la fenetre et descend de 11 unites (SUPPOSE)")
	function ui:text_basic(texte, c1, c2)
		piege("text_basic")
		if type(texte) ~= "string" then error("text_basic : texte attendu", 2) end
		local f = self:get_window()
		f.textes[#f.textes + 1] = texte
		f.couleurs[#f.textes] = c1
		f.cy = f.cy + 11
	end

	-- BANC : debut d'image
	function ui:nouvelle_image()
		self.dessinees = {}
	end

	-- BANC : textes de toutes les fenetres dessinees pendant l'image, concatenes (pour des assertions simples)
	function ui:tous_les_textes()
		local out = {}
		for _, f in ipairs(self.dessinees) do for _, t in ipairs(f.textes) do out[#out + 1] = t end end
		return out
	end

	function ui:fenetre(titre)
		for _, f in ipairs(self.dessinees) do if f.titre == titre then return f end end
	end

	return ui
end

return UI
