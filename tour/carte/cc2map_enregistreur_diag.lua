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
--
-- VARIANTE DIAGNOSTIC (tour, 27/10/2026) : meme enregistrement CC2MAP, plus des lignes "CC2DIAG|..." (que la page ne voit pas) :
--   CC2DIAG|E|<tick>|<V|T|M|S|U|MM>|<ligne> <message>   une erreur que le script avalait en silence (1re fois seulement)
--   CC2DIAG|S|<tick>|ecran=..;cc2x=..;missile_count=..;..;fonctions=..   une fois par ecran : types des fonctions, vraies fonctions "missile"
--   CC2DIAG|MM|<tick>|n=..;<accesseur>(ok,type,methodes)                 au 1er missile vu : vrai accesseur et methodes de l'objet
--   CC2DIAG|U|<tick>|moi=..;cc2x[n]=t0=..,..;jeu[n]=..;iles_chargees=id:equipe,..   toutes les 60 s : equipes vues par CC2X et par le jeu
-- Toujours en lecture seule : aucun io / os / reseau, seulement cc2x.log.

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

-- ---- diagnostic (lecture seule) : lignes CC2DIAG|..., jamais CC2MAP| ----
local function diag(kind, tick, payload)
    cc2x.log("CC2DIAG|" .. kind .. "|" .. tick .. "|" .. string.sub(payload, 1, 800))
end

local function safe(f, ...)                        -- appelle sans jamais lever d'erreur
    if type(f) ~= "function" then return nil end
    local ok, v = pcall(f, ...)
    if ok then return v end
    return nil
end

local function sorted_keys(t)
    local r = {}
    for k in pairs(t) do r[#r + 1] = tostring(k) end
    table.sort(r)
    return r
end

local seen_err = {}
local function guarded(name, f, tick)              -- remplace pcall(f, tick) : note chaque erreur nouvelle (sans chemin)
    local ok, err = pcall(f, tick)
    if ok then return end
    local line, rest = tostring(err):match(":(%d+): (.*)$")
    local msg = (string.gsub(line and (line .. " " .. rest) or tostring(err), "%a:[\\/][^%s]*", "<chemin>")):sub(1, 200)
    if not seen_err[name .. msg] then
        seen_err[name .. msg] = true
        pcall(diag, "E", tick, name .. "|" .. msg)
    end
end

local function describe_api(tick)                  -- une fois par ecran
    local names = {}
    for k, v in pairs(_G) do
        if type(k) == "string" and type(v) == "function" and (k:find("missile", 1, true) or k:find("projectile", 1, true)) then
            names[#names + 1] = k
        end
    end
    table.sort(names)
    diag("S", tick, string.format("ecran=%s;cc2x=%s/api%s;missile_count=%s;missile_by_index=%s;fonctions=%s",
        tostring(safe(begin_get_screen_name)), tostring(cc2x.version), tostring(cc2x.api),
        type(update_get_missile_count), type(update_get_missile_by_index), table.concat(names, ",")))
end

local probed = false
local function probe_missile(tick)                 -- au 1er missile vu : vrai nom de l'accesseur et methodes de l'objet
    if probed or (safe(update_get_missile_count) or 0) < 1 then return end
    probed = true
    local out = {}
    for k, f in pairs(_G) do
        if type(k) == "string" and type(f) == "function" and k:find("^update_get_.*missile.*_by_index$") then
            local ok, m = pcall(f, 0)
            local mt = ok and m ~= nil and getmetatable(m)
            local idx = type(mt) == "table" and mt.__index
            out[#out + 1] = k .. "(ok=" .. tostring(ok) .. ",type=" .. type(m) .. ",methodes="
                .. table.concat(type(idx) == "table" and sorted_keys(idx) or {}, "/") .. ")"
        end
    end
    diag("MM", tick, "n=" .. tostring(safe(update_get_missile_count)) .. ";" .. table.concat(out, ";"))
end

local function census(tick)                        -- toutes les 60 s : equipes vues par CC2X et par le jeu, iles chargees
    local cc, ai, n_cc, gj = {}, {}, 0, {}
    for _, v in ipairs(cc2x.vehicles() or {}) do
        n_cc = n_cc + 1
        cc[v.team] = (cc[v.team] or 0) + 1
        ai[v.team] = v.team_is_ai
    end
    local n_gj = safe(update_get_map_vehicle_count) or 0
    for i = 0, n_gj - 1 do
        local v = safe(update_get_map_vehicle_by_index, i)
        if v ~= nil and safe(v.get, v) then
            local t = safe(v.get_team, v)
            if t ~= nil then gj[t] = (gj[t] or 0) + 1 end
        end
    end
    local function fmt(h, extra)
        local r = {}
        for _, k in ipairs(sorted_keys(h)) do
            local kk = tonumber(k) or k
            r[#r + 1] = "t" .. k .. "=" .. tostring(h[kk]) .. (extra and ("/ia" .. tostring(extra[kk])) or "")
        end
        return table.concat(r, ",")
    end
    local loaded = {}
    for _, t in ipairs(cc2x.tiles() or {}) do
        if t.island then loaded[#loaded + 1] = t.id .. ":" .. t.team end
    end
    diag("U", tick, string.format("moi=%s;cc2x[%s]=%s;jeu[%s]=%s;iles_chargees=%s",
        tostring(safe(update_get_screen_team_id)), n_cc, fmt(cc, ai), tostring(n_gj), fmt(gj), table.concat(loaded, ",")))
end

local function record()
    if not cc2x_ok() then return end
    local tick = cc2x.tick()
    if type(tick) ~= "number" or tick <= 0 then return end
    if S.tick and tick < S.tick - 60 then          -- nouvelle partie ou chargement : on repart de zero
        S.last_v, S.last_t, S.last_m, S.header, S.diag = -1, -1, -1, false, false
        probed = false
    end
    S.tick = tick
    if not S.header then S.header = true; emit("H", tick, VERSION) end
    if not S.diag then S.diag = true; guarded("S", describe_api, tick) end
    local bv = math.floor(tick / STEP_V)
    if bv ~= S.last_v then S.last_v = bv; guarded("V", snap_vehicles, tick) end
    local bt = math.floor(tick / STEP_T)
    if bt ~= S.last_t then S.last_t = bt; guarded("T", snap_tiles, tick); guarded("U", census, tick) end
    local bm = math.floor(tick / STEP_M)
    if bm ~= S.last_m then S.last_m = bm; guarded("M", snap_missiles, tick); guarded("MM", probe_missile, tick) end
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
