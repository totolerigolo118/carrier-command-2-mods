-- CC2MAP : enregistreur de positions (LECTURE SEULE) pour le timelapse de la carte.
-- Il ne change rien dans le jeu : il lit les unites, les missiles et les iles, et ecrit des lignes
-- "CC2MAP|..." dans cc2x.log (journal du SDK CC2X >= 0.5.0). Sans CC2X, il ne fait rien.
--
-- A poser comme script de mod (content/scripts/library_custom_N.lua, N libre, par exemple 6).
-- Format des lignes (une ligne = au plus 10 elements, pour rester courte) :
--   CC2MAP|H|<tick>|1                          debut de session, version du format
--   CC2MAP|V|<tick>|<p>/<n>|id,def,team,x,z,cap;...     unites (toutes equipes, brouillard compris), toutes les 10 s
--   CC2MAP|T|<tick>|<p>/<n>|id,team,x,z;...             iles, toutes les 60 s
--   CC2MAP|M|<tick>|<p>/<n>|id,def,team,x,z;...         missiles, toutes les 0,5 s tant qu'il y en a
-- x, z en metres (entiers) ; cap en degres (0 = vers +z, sens horaire vu de dessus) ; tick = tick du serveur (30 par seconde).
-- Compatible Lua 5.1 a 5.4 (pas d'operateur entier, pas de goto).

local VERSION = 1
local STEP_V, STEP_T, STEP_M = 300, 1800, 15
local CHUNK = 10
local SCREENS = { holomap_screen = true, screen_veh_m = true, screen_veh_l = true, screen_veh_r = true, screen_veh_top_m = true }

local unpack = table.unpack or unpack
local S = { last_v = -1, last_t = -1, last_m = -1, tick = nil, header = false, had_m = false }

local function cc2x_ok()
    return type(cc2x) == "table" and type(cc2x.api) == "number" and cc2x.api >= 4
end

local function rnd(x) return math.floor((x or 0) + 0.5) end

local function emit(kind, tick, payload)
    cc2x.log("CC2MAP|" .. kind .. "|" .. tick .. "|" .. payload)
end

local function emit_chunks(kind, tick, items)
    local n = #items
    if n == 0 then emit(kind, tick, "1/1|") return end
    local parts = math.ceil(n / CHUNK)
    for p = 1, parts do
        local a, b = (p - 1) * CHUNK + 1, math.min(n, p * CHUNK)
        emit(kind, tick, p .. "/" .. parts .. "|" .. table.concat(items, ";", a, b))
    end
end

local function snap_vehicles(tick)
    local vs = cc2x.vehicles()
    local items = {}
    for i = 1, #vs do
        local v = vs[i]
        local cap = rnd((v.yaw or 0) * 57.29578) % 360
        items[#items + 1] = string.format("%d,%d,%d,%d,%d,%d", v.id, v.definition, v.team, rnd(v.x), rnd(v.z), cap)
    end
    emit_chunks("V", tick, items)
end

local function snap_tiles(tick)
    local ts = cc2x.tiles()
    local items = {}
    for i = 1, #ts do
        local t = ts[i]
        items[#items + 1] = string.format("%d,%d,%d,%d", t.id, t.team, rnd(t.x), rnd(t.z))
    end
    emit_chunks("T", tick, items)
end

-- missiles : lus par l'API des ecrans du jeu (update_get_missile_*), pas par CC2X
local function snap_missiles(tick)
    if type(update_get_missile_count) ~= "function" or type(update_get_missile_by_index) ~= "function" then return end
    local n = update_get_missile_count() or 0
    if n == 0 then
        if S.had_m then S.had_m = false; emit("M", tick, "1/1|") end   -- marque la fin des missiles en vol
        return
    end
    S.had_m = true
    local items = {}
    for i = 0, n - 1 do
        local m = update_get_missile_by_index(i)
        if m and m:get() then
            local p = m:get_position_xz()
            local id = i
            if m.get_id then
                local okid, v = pcall(m.get_id, m)
                if okid and type(v) == "number" then id = v end
            end
            items[#items + 1] = string.format("%d,%d,%d,%d,%d", id, m:get_definition_index(), m:get_team(), rnd(p:x()), rnd(p:y()))
        end
    end
    emit_chunks("M", tick, items)
end

local function record()
    if not cc2x_ok() then return end
    local tick = cc2x.tick()
    if type(tick) ~= "number" or tick <= 0 then return end
    if S.tick and tick < S.tick - 60 then          -- nouvelle partie ou chargement : on repart de zero
        S.last_v, S.last_t, S.last_m, S.header = -1, -1, -1, false
    end
    S.tick = tick
    if not S.header then S.header = true; emit("H", tick, VERSION) end
    local bv = math.floor(tick / STEP_V)
    if bv ~= S.last_v then S.last_v = bv; pcall(snap_vehicles, tick) end
    local bt = math.floor(tick / STEP_T)
    if bt ~= S.last_t then S.last_t = bt; pcall(snap_tiles, tick) end
    local bm = math.floor(tick / STEP_M)
    if bm ~= S.last_m then S.last_m = bm; pcall(snap_missiles, tick) end
end

-- accroche : on enveloppe begin_load, puis update() des ecrans choisis (comme les autres scripts de mesure)
if type(begin_load) == "function" and not g_cc2map_hooked then
    g_cc2map_hooked = true
    local orig = begin_load
    begin_load = function(...)
        local res = table.pack and table.pack(orig(...)) or { orig(...) }
        local name = (type(begin_get_screen_name) == "function") and begin_get_screen_name() or nil
        if name and SCREENS[name] and type(update) == "function" and not g_cc2map_wrapped then
            g_cc2map_wrapped = true
            local uo = update
            update = function(...)
                pcall(record)
                return uo(...)
            end
        end
        return unpack(res, 1, res.n or #res)
    end
end
