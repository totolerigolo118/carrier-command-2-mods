-- CC2MODES : ONGLET "SPEED" (MAQUETTE, SANS EFFET) pour l'etude des modes ECO / NORMAL / FLANK.
-- Quand tu cliques sur un de tes avions (Albatros ou Manta) dans la carte d'un ecran de controle des vehicules,
-- une petite fenetre SPEED s'ouvre sous la fenetre LOADOUT, avec trois boutons ECO / NORMAL / FLANK.
-- Elle ne commande RIEN : le choix est seulement memorise dans l'ecran (pas partage entre les 3 ecrans, pas
-- garde d'une partie a l'autre) pour juger la place, la taille et la lisibilite. Elle le dit : "MAQUETTE : SANS EFFET".
-- Aucune ecriture de fichier, aucun reseau, aucune commande au jeu (ni vitesse, ni gaz, ni carburant).
--
-- Technique : on enveloppe render_selection_vehicle(screen_w, screen_h, vehicle) de screen_vehicle_control.lua :
-- le jeu dessine ses fenetres comme d'habitude, puis on dessine la notre APRES, dans un pcall. Si notre dessin
-- plante, on remet les piles de l'interface du jeu en ordre et on se desactive (le jeu continue normalement).
-- Souris uniquement pour l'instant (la fenetre n'est pas active a la manette).
-- Compatible Lua 5.1 a 5.4. A poser comme script de mod (content/scripts/library_custom_N.lua, ici N = 5).

local unpack = table.unpack or unpack

g_cm = g_cm or { modes = {}, casse = false }

local NOMS = { "ECO", "NORMAL", "FLANK" }
local COULEURS = {
    color8(16, 255, 127, 255),     -- ECO : vert
    color8(16, 255, 255, 255),     -- NORMAL : cyan
    color8(255, 176, 32, 255),     -- FLANK : orange
}
local MODE_DEFAUT = 2               -- NORMAL
local FEN_Y = 99                    -- sous LOADOUT (y 10 + hauteur 84 + 5)
local FEN_W = 74                    -- meme largeur que LOADOUT
local FEN_H = 80                    -- assez haut pour que le jeu n'ajoute pas de barre de defilement

-- un bouton comme ceux de la barre de vitesse du Mac : allume = plein de la couleur du mode
local function cm_bouton(ui, label, allume, couleur)
    local window = ui:get_window()
    local x, y = window.cx, window.cy
    local w = ui:get_region()
    local hovered = ui:hoverable(x, y, w, 13, true)
    if allume then
        update_ui_rectangle(x + 1, y, w - 2, 12, couleur)
    else
        update_ui_rectangle(x + 1, y, w - 2, 12, color8(4, 12, 12, 255))
        update_ui_rectangle_outline(x + 1, y, w - 2, 12,
            (hovered and window.is_active) and couleur or color8(63, 63, 63, 255))
    end
    update_ui_text(x + 5, y + 2, label, w - 10, 0,
        allume and color8(0, 0, 0, 255) or color8(190, 204, 204, 255), 0)
    local clic = false
    if window.is_active and hovered and ui.input_pointer_1 then
        clic = true
        ui.input_pointer_1 = false
    end
    window.cy = window.cy + 13
    return clic
end

local function cm_dessiner(ui, screen_w, screen_h, vehicle)
    -- memes gardes que le jeu pour ses propres fenetres (equipe de l'ecran, pas de boite "etes-vous sur")
    local screen_vehicle = update_get_screen_vehicle()
    if not screen_vehicle:get() or screen_vehicle:get_team() ~= vehicle:get_team() then return end
    if type(g_selected_vehicle_ui) == "table" and g_selected_vehicle_ui.confirm_self_destruct then return end

    local def = vehicle:get_definition_index()
    if def ~= e_game_object_type.chassis_air_wing_light and def ~= e_game_object_type.chassis_air_wing_heavy then
        return                      -- seulement les avions (Albatros, Manta)
    end

    local id = vehicle:get_id()
    local mode = g_cm.modes[id] or MODE_DEFAUT
    local souris = update_get_active_input_type() == e_active_input.keyboard
    local x = 10 + (screen_w - 74 - 25) + 5          -- meme x que LOADOUT dans render_selection_vehicle

    ui:begin_window("SPEED##cm_speed", x, FEN_Y, FEN_W, FEN_H, atlas_icons.column_pending, souris, 2)
        for i = 1, 3 do
            if cm_bouton(ui, NOMS[i], mode == i, COULEURS[i]) then
                g_cm.modes[id] = i
                mode = i
            end
        end
        ui:spacer(3)
        ui:text_basic("MAQUETTE : SANS EFFET", color8(255, 90, 60, 255), color8(255, 90, 60, 255))
    ui:end_window()
end

local function taille(t)
    if type(t) == "table" then return #t end
    return 0
end

local function cm_afficher(screen_w, screen_h, vehicle)
    if g_cm.casse or type(g_ui) ~= "table" then return end
    local ui = g_ui
    local n_fen, n_reg = taille(ui.window_stack), taille(ui.region_stack)
    local ok, err = pcall(cm_dessiner, ui, screen_w, screen_h, vehicle)
    if ok then return end
    -- erreur : on referme ce que notre fenetre a ouvert, puis on se desactive pour cet ecran
    local garde = 0
    while taille(ui.window_stack) > n_fen and garde < 4 do
        pcall(ui.end_window, ui)
        garde = garde + 1
    end
    while taille(ui.region_stack) > n_reg do
        ui.region_stack[#ui.region_stack] = nil
    end
    g_cm.casse = true
    if type(cc2x) == "table" and type(cc2x.log) == "function" then
        pcall(cc2x.log, "CC2MODES|UI|erreur|" .. string.sub(tostring(err), 1, 200))
    end
end

local function envelopper()
    if g_cm_ui_enveloppe or type(render_selection_vehicle) ~= "function" then return end
    g_cm_ui_enveloppe = true
    local origine = render_selection_vehicle
    render_selection_vehicle = function(screen_w, screen_h, vehicle, ...)
        local res = table.pack(origine(screen_w, screen_h, vehicle, ...))
        cm_afficher(screen_w, screen_h, vehicle)
        return unpack(res, 1, res.n)
    end
end

-- soit la fonction du jeu existe deja ici, soit elle apparait quand l'ecran demarre (begin_load)
envelopper()
if type(begin_load) == "function" and not g_cm_ui_begin_load then
    g_cm_ui_begin_load = true
    local orig = begin_load
    begin_load = function(...)
        local res = table.pack(orig(...))
        envelopper()
        return unpack(res, 1, res.n)
    end
end
