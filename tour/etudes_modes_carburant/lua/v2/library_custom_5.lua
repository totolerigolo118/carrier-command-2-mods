-- CC2MODES : ONGLET "SPEED" v2 : trois boutons ECO / NORMAL / FLANK par avion, branches sur le plugin cc2x_modes.dll (v3).
-- Quand tu cliques sur un de tes avions (Albatros ou Manta) dans la carte d'un ecran de controle des vehicules, une petite
-- fenetre SPEED s'ouvre sous la fenetre LOADOUT. Le bouton allume est le mode DEMANDE ; une ligne dessous dit ce qui se passe :
--   (pas de plugin)            MAQUETTE : SANS EFFET        les boutons sont memorises dans l'ecran seulement, comme la v1
--   plugin, enabled=0          OBSERVATION : SANS EFFET     le plugin lit et note, il n'ecrit rien dans le jeu
--   plugin actif, avion en ECO / FLANK et ecrit en ce moment    ACTIF
--   plugin actif, pas encore ecrit (pres du bateau, au sol, en retour)   EN ATTENTE
--   plugin actif, tu pilotes cet avion                           PILOTE : EN PAUSE
-- Dessous, une autonomie estimee (~N min) d'apres les mesures du 28/10 (Albatros : ECO 0,22 / NORMAL 0,282 / FLANK 0,304 de
-- carburant par seconde ; Manta : NORMAL 0,36 / FLANK 0,77 ; ECO du Manta non mesure : « ? »).
--
-- Le choix passe par cc2x.modes.set(id, mode) (0 NORMAL, 1 ECO, 2 FLANK), partage entre les 3 ecrans. Le plugin ne l'applique que
-- si modes.ini a enabled=1. Pour que le plugin ne touche jamais aux gaz de l'avion que TU pilotes, cet ecran appelle
-- cc2x.modes.hold(g_viewing_vehicle_id) a chaque image tant que l'ecran pilote un vehicule (ne rien lister soi-meme).
-- Aucune ecriture de fichier, aucun reseau ; tout appel au plugin est dans un pcall.
--
-- Technique : on enveloppe render_selection_vehicle(screen_w, screen_h, vehicle) de screen_vehicle_control.lua (le jeu dessine
-- ses fenetres, puis on dessine la notre APRES, dans un pcall ; si notre dessin plante, on remet les piles de l'interface en
-- ordre et on se desactive) et update() de cet ecran (pour le garde-fou pilotage). Souris uniquement.
-- Compatible Lua 5.1 a 5.4. A poser comme script de mod (content/scripts/library_custom_N.lua, ici N = 5).

local unpack = table.unpack or unpack

g_cm = g_cm or { modes = {}, casse = false, status = nil, status_age = 0 }

local NOMS = { "ECO", "NORMAL", "FLANK" }
local COULEURS = {
    color8(16, 255, 127, 255),     -- ECO : vert
    color8(16, 255, 255, 255),     -- NORMAL : cyan
    color8(255, 176, 32, 255),     -- FLANK : orange
}
local MODE_PLUGIN = { 1, 0, 2 }    -- bouton 1 (ECO) -> mode 1 ; bouton 2 (NORMAL) -> 0 ; bouton 3 (FLANK) -> 2
local BOUTON_DE_MODE = { [0] = 2, [1] = 1, [2] = 3 }
local BOUTON_DEFAUT = 2            -- NORMAL
local FEN_Y = 99                   -- sous LOADOUT (y 10 + hauteur 84 + 5)
local FEN_W = 74                   -- meme largeur que LOADOUT
local FEN_H = 100
local REAFFICHER_STATUT = 60       -- images entre deux lectures de cc2x.modes.status()

-- carburant brule par seconde de jeu, mesure le 28/10 (avion peu charge) ; nil = non mesure
local DEBIT = {
    [8] = { 0.22, 0.282, 0.304 },  -- Albatros : ECO, NORMAL, FLANK
    [10] = { nil, 0.36, 0.77 },    -- Manta
}
local RESERVOIR = { [8] = 800, [10] = 1200 }

local function cm_plugin()
    return type(cc2x) == "table" and type(cc2x.modes) == "table" and type(cc2x.modes.set) == "function"
        and type(cc2x.modes.get) == "function"
end

-- garde-fou pilotage : cet ecran controle un vehicule (g_viewing_vehicle_id > 0) -> le plugin n'y touche pas
local function cm_hold()
    if not cm_plugin() or type(cc2x.modes.hold) ~= "function" then return end
    local id = g_viewing_vehicle_id
    if type(id) == "number" and id > 0 then cc2x.modes.hold(id) end
end

local function cm_statut()
    g_cm.status_age = g_cm.status_age + 1
    if g_cm.status == nil or g_cm.status_age >= REAFFICHER_STATUT then
        g_cm.status_age = 0
        local ok, s = pcall(cc2x.modes.status)
        g_cm.status = (ok and type(s) == "table") and s or { enabled = false }
    end
    return g_cm.status
end

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

-- minutes d'autonomie estimees pour un mode (bouton 1..3), ou nil
local function cm_autonomie(vehicle, def, bouton)
    local debit = DEBIT[def] and DEBIT[def][bouton]
    local reservoir = RESERVOIR[def]
    if not debit or not reservoir then return nil end
    local ok, f = pcall(vehicle.get_fuel_factor, vehicle)
    if not ok or type(f) ~= "number" then return nil end
    return math.floor(f * reservoir / debit / 60 + 0.5)
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
    local plugin = cm_plugin()
    local bouton, actif, pilote = g_cm.modes[id] or BOUTON_DEFAUT, 0, false
    if plugin then
        local ok, m, a, h = pcall(cc2x.modes.get, id)
        if ok and type(m) == "number" then
            bouton = BOUTON_DE_MODE[m] or BOUTON_DEFAUT
            actif = (type(a) == "number") and a or 0
            pilote = (h == true)
        end
    end
    local souris = update_get_active_input_type() == e_active_input.keyboard
    local x = 10 + (screen_w - 74 - 25) + 5          -- meme x que LOADOUT dans render_selection_vehicle

    ui:begin_window("SPEED##cm_speed", x, FEN_Y, FEN_W, FEN_H, atlas_icons.column_pending, souris, 2)
        for i = 1, 3 do
            if cm_bouton(ui, NOMS[i], bouton == i, COULEURS[i]) then
                if plugin then
                    pcall(cc2x.modes.set, id, MODE_PLUGIN[i])
                else
                    g_cm.modes[id] = i
                end
                bouton = i
            end
        end
        ui:spacer(3)
        local texte, couleur
        if not plugin then
            texte, couleur = "MAQUETTE : SANS EFFET", color8(255, 90, 60, 255)
        elseif not cm_statut().enabled then
            texte, couleur = "OBSERVATION : SANS EFFET", color8(255, 176, 32, 255)
        elseif pilote then
            texte, couleur = "PILOTE : EN PAUSE", color8(190, 204, 204, 255)
        elseif actif ~= 0 then
            texte, couleur = "ACTIF", COULEURS[BOUTON_DE_MODE[actif] or 2]
        elseif bouton ~= BOUTON_DEFAUT then
            texte, couleur = "EN ATTENTE", color8(190, 204, 204, 255)
        else
            texte, couleur = "", color8(190, 204, 204, 255)
        end
        if texte ~= "" then ui:text_basic(texte, couleur, couleur) end
        if plugin then
            local min = cm_autonomie(vehicle, def, bouton)
            local ligne = min and ("AUTONOMIE ~" .. min .. " min") or "AUTONOMIE ?"
            ui:text_basic(ligne, color8(150, 170, 170, 255), color8(150, 170, 170, 255))
        end
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

-- le garde-fou pilotage : update() des ecrans qui ont un vehicule controle (ceux de screen_vehicle_control.lua)
local function envelopper_update()
    if g_cm_update_enveloppe or type(update) ~= "function" or type(g_viewing_vehicle_id) ~= "number" then return end
    g_cm_update_enveloppe = true
    local origine = update
    update = function(...)
        pcall(cm_hold)
        return origine(...)
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
        envelopper_update()
        return unpack(res, 1, res.n)
    end
end
