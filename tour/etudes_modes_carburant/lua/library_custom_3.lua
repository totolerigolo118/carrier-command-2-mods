-- CC2MODES : TELEMETRIE des avions (LECTURE SEULE) pour l'etude des modes ECO / NORMAL / FLANK.
-- Il ne change rien dans le jeu : il lit la vitesse, les gaz et le carburant de tes avions en l'air et ecrit
-- des lignes "CC2MODES|..." dans cc2x.log (journal du SDK CC2X >= 0.5.0). Sans CC2X, il ne fait rien.
-- Aucun io / os / reseau : seulement cc2x.log.
--
-- Format (une ligne = au plus 6 avions) :
--   CC2MODES|H|<tick>|<ecran>|1|cc2x=<version>/api<n>        debut de session, version du format
--   CC2MODES|A|<tick>|<ecran>|<p>/<n>|<avion>;<avion>;...    toutes les 5 s, avions de TON equipe en l'air
--     <avion> = id,def,x,y,z,vitesse,carburant,control_speed,control_power,jeu_carb,jeu_vitesse,jeu_gaz
--       les 9 premiers viennent de CC2X (x,y,z en m ; vitesse en m/s ; "-" si absent)
--       jeu_* = lecture par l'API des ecrans du jeu (get_fuel_factor / get_linear_speed / get_throttle_factor) ;
--       "-" si la fonction n'existe pas pour ce vehicule (c'est justement ce que l'on veut savoir)
--   CC2MODES|E|<tick>|<ecran>|<message>                      une erreur avalee (1re fois seulement)
-- Chaque ecran du jeu a son propre Lua : une meme mesure peut donc apparaitre 2 ou 3 fois (ecrans differents) ;
-- il suffit d'en garder une par tick.
-- Compatible Lua 5.1 a 5.4. A poser comme script de mod (content/scripts/library_custom_N.lua, ici N = 3).

local VERSION = 1
local PAS = 150          -- ticks (30 par seconde) : une mesure toutes les 5 s
local PAR_LIGNE = 6

local unpack = table.unpack or unpack
local S = { last = -1, tick = nil, header = false }
local erreurs = {}

local function cc2x_ok()
    return type(cc2x) == "table" and type(cc2x.api) == "number" and cc2x.api >= 4
end

local function f(x, n)
    if type(x) ~= "number" then return "-" end
    return string.format("%." .. (n or 1) .. "f", x)
end

local function nom_ecran()
    if type(begin_get_screen_name) ~= "function" then return "?" end
    local ok, v = pcall(begin_get_screen_name)
    return (ok and v) and tostring(v) or "?"
end

local function emit(kind, tick, payload)
    cc2x.log("CC2MODES|" .. kind .. "|" .. tick .. "|" .. nom_ecran() .. "|" .. payload)
end

-- lecture d'un nombre par l'API des ecrans du jeu ; "-" si la methode manque ou echoue
local function jeu(objet, methode, n)
    if objet == nil then return "-" end
    local ok, r = pcall(function() return objet[methode](objet) end)
    if ok and type(r) == "number" then return f(r, n) end
    return "-"
end

local function objet_jeu(id)
    if type(update_get_map_vehicle_by_id) ~= "function" then return nil end
    local ok, v = pcall(update_get_map_vehicle_by_id, id)
    if not ok or v == nil then return nil end
    local ok2, present = pcall(function() return v:get() end)
    if not ok2 or not present then return nil end
    return v
end

local function snap(tick)
    local equipe = nil
    if type(update_get_screen_team_id) == "function" then
        local ok, t = pcall(update_get_screen_team_id)
        if ok then equipe = t end
    end
    local vs = (equipe ~= nil) and cc2x.vehicles(equipe) or cc2x.vehicles()
    local items = {}
    for i = 1, #vs do
        local v = vs[i]
        if v.is_wing and v.flight_state == 2 then
            local o = objet_jeu(v.id)
            items[#items + 1] = table.concat({
                tostring(v.id), tostring(v.definition),
                f(v.x, 0), f(v.y, 0), f(v.z, 0),
                f(v.speed, 1), f(v.fuel, 3), f(v.control_speed, 1), f(v.control_power, 3),
                jeu(o, "get_fuel_factor", 3), jeu(o, "get_linear_speed", 1), jeu(o, "get_throttle_factor", 3),
            }, ",")
        end
    end
    local n = #items
    if n == 0 then return end
    local parts = math.ceil(n / PAR_LIGNE)
    for p = 1, parts do
        local a, b = (p - 1) * PAR_LIGNE + 1, math.min(n, p * PAR_LIGNE)
        emit("A", tick, p .. "/" .. parts .. "|" .. table.concat(items, ";", a, b))
    end
end

local function noter_erreur(tick, err)
    local msg = string.sub((string.gsub(tostring(err), "%a:[\\/][^%s]*", "<chemin>")), 1, 200)
    if not erreurs[msg] then
        erreurs[msg] = true
        pcall(emit, "E", tick, msg)
    end
end

local function record()
    if not cc2x_ok() then return end
    local tick = cc2x.tick()
    if type(tick) ~= "number" or tick <= 0 then return end
    if S.tick and tick < S.tick - 60 then          -- nouvelle partie ou chargement : on repart de zero
        S.last, S.header = -1, false
    end
    S.tick = tick
    if not S.header then
        S.header = true
        emit("H", tick, VERSION .. "|cc2x=" .. tostring(cc2x.version) .. "/api" .. tostring(cc2x.api))
    end
    local b = math.floor(tick / PAS)
    if b ~= S.last then
        S.last = b
        local ok, err = pcall(snap, tick)
        if not ok then noter_erreur(tick, err) end
    end
end

-- accroche : on enveloppe begin_load, puis update() de l'ecran (meme technique que les autres scripts de mesure)
if type(begin_load) == "function" and not g_cm_mesure_accroche then
    g_cm_mesure_accroche = true
    local orig = begin_load
    begin_load = function(...)
        local res = table.pack and table.pack(orig(...)) or { orig(...) }
        if type(update) == "function" and not g_cm_mesure_update then
            g_cm_mesure_update = true
            local uo = update
            update = function(...)
                pcall(record)
                return uo(...)
            end
        end
        return unpack(res, 1, res.n or #res)
    end
end
