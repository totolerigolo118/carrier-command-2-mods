-- TEMPORARY IN-FLIGHT SPEED TEST (installed for one test only; see the test script).
-- Menu context (screen_front): loads a save by itself. Ship context (screen_veh_m): launches 4 aircraft by waypoints, recalls
-- them when the 4th is airborne, and times everything in GAME ticks (30 per second). Results go to releve_cc2.txt with print().
local SLOT = 18
local N_AIR = 4
local AHEAD = 4000          -- metres ahead (world z) for the launch waypoint
local FLAG_TEAM = 14        -- cross-context "already done" flag stored in cc2_vitesse's table (team 14)

local function safe(f, ...)
  local ok, v = pcall(f, ...)
  if ok then return v end
  return nil
end

-- ---------------------------------------------------------------- menu part
local function try_load()
  if type(cc2_vitesse) == "function" then
    if cc2_vitesse(FLAG_TEAM) == 1 then return end     -- mode 1 = ECO = original speeds: changes nothing for the aircraft
    cc2_vitesse(FLAG_TEAM, 1)
  end
  local slots = update_get_save_slots()
  local found = false
  for _, v in ipairs(slots) do if v.slot_index == SLOT then found = true end end
  if found then
    update_ui_event("load_game", SLOT)
    print("AUTO load_game requested slot=" .. SLOT)
  else
    print("AUTO slot not found")
  end
end


local function carrier()
  local c = update_get_screen_vehicle()
  if c and c:get() then return c end
  return nil
end

local DIAG = {}
local function candidates(c)
  local cid, team = c:get_id(), update_get_screen_team_id()
  local list, seen = {}, {}
  local function consider(v, how)
    if v and v:get() and not seen[v:get_id()] then
      seen[v:get_id()] = true
      local d = v:get_definition_index()
      if v:get_dock_state() == 4 and (d == 8 or d == 10) then list[#list + 1] = { id = v:get_id(), def = d, how = how } end
    end
  end
  -- 1. by bay: the hangar has bays 0..15 (A1..A8 are 8..15)
  local bays = 0
  for b = 0, 15 do
    local id = safe(c.get_attached_vehicle_id, c, b)
    if id and id >= 0 then bays = bays + 1; consider(update_get_map_vehicle_by_id(id), "bay" .. b) end
  end
  -- 2. by the attached-parent relation, then by the dock-parent relation
  local n_total, n_team, n_dock4, n_att, n_dockp = 0, 0, 0, 0, 0
  for i = 0, update_get_map_vehicle_count() - 1 do
    local v = update_get_map_vehicle_by_index(i)
    if v:get() then
      n_total = n_total + 1
      if v:get_team() == team then
        n_team = n_team + 1
        local s = v:get_dock_state()
        if s == 4 then n_dock4 = n_dock4 + 1 end
        local ap = safe(v.get_attached_parent_id, v)
        if ap == cid then n_att = n_att + 1; consider(v, "att") end
        if v:get_dock_parent_id() == cid then n_dockp = n_dockp + 1; consider(v, "dockp") end
      end
    end
  end
  DIAG = { total = n_total, team = n_team, dock4 = n_dock4, att = n_att, dockp = n_dockp, bays = bays, cid = cid, myteam = team }
  return list
end

-- ---------------------------------------------------------------- ship part (speed test)
local FAR = 20000            -- metres: far waypoint (world z) so the aircraft keep cruising during the whole test
local SETTLE, WINDOW = 600, 600   -- ticks: wait after a mode change, then measure over this window
local MODES = { { 1, "ECO" }, { 2, "NORMAL" }, { 3, "FLANK" } }
local H = { st = "wait", rec = {}, ph = 0, t_ph = nil, samples = {}, res = {}, fin = 0, tgt = nil }

local function now() return update_get_logic_tick() end

local function xz(v)
  local p = v:get_position_xz()
  return p:x(), p:y()
end

local function airborne_all()
  for _, a in ipairs(H.rec) do
    local v = update_get_map_vehicle_by_id(a.id)
    if not v:get() or v:get_dock_state() ~= 0 then return false end
  end
  return true
end

local function begin_phase(t)
  H.ph = H.ph + 1
  local m = MODES[H.ph]
  H.t_ph = t
  H.samples = {}
  cc2_vitesse(H.team, m[1])
  H.cur = m
end

local function sample(t)
  for _, a in ipairs(H.rec) do
    local v = update_get_map_vehicle_by_id(a.id)
    if v:get() then
      local x, z = xz(v)
      local s = H.samples[a.id]
      if s == nil then s = {}; H.samples[a.id] = s end
      local last = s[#s]
      if last == nil or t - last.t >= 30 then s[#s + 1] = { t = t, x = x, z = z } end
    end
  end
end

local function phase_result()
  local parts = { "AUTOSPD phase=" .. H.cur[2] .. " mode=" .. H.cur[1] .. " t_start=" .. H.t_ph }
  for i, a in ipairs(H.rec) do
    local s = H.samples[a.id] or {}
    local t0, t1 = H.t_ph + SETTLE, H.t_ph + SETTLE + WINDOW
    local pts = {}
    for _, p in ipairs(s) do if p.t >= t0 and p.t <= t1 then pts[#pts + 1] = p end end
    if #pts >= 2 then
      local d = math.sqrt((pts[#pts].x - pts[1].x) ^ 2 + (pts[#pts].z - pts[1].z) ^ 2)
      local dt = (pts[#pts].t - pts[1].t) / 30
      local vmin, vmax = 1e9, 0
      for k = 2, #pts do
        local dd = math.sqrt((pts[k].x - pts[k - 1].x) ^ 2 + (pts[k].z - pts[k - 1].z) ^ 2)
        local vv = dd / ((pts[k].t - pts[k - 1].t) / 30)
        if vv < vmin then vmin = vv end
        if vv > vmax then vmax = vv end
      end
      local dist_tgt = H.tgt and math.sqrt((pts[#pts].x - H.tgt.x) ^ 2 + (pts[#pts].z - H.tgt.z) ^ 2) or -1
      parts[#parts + 1] = string.format("a%d(id=%d,def=%d,v=%.1f,vmin=%.1f,vmax=%.1f,n=%d,to_target=%.0f)", i, a.id, a.def, d / dt, vmin, vmax, #pts, dist_tgt)
    else
      parts[#parts + 1] = string.format("a%d(id=%d,def=%d,nosample=%d)", i, a.id, a.def, #pts)
    end
  end
  parts[#parts + 1] = "ENDAUTOSPD"
  local line = table.concat(parts, " ")
  H.res[#H.res + 1] = line
  print(line)
end

local function step()
  local t = now()
  local c = carrier()
  if not c then return end
  if H.st == "wait" then
    if t < 900 then return end
    local cand = candidates(c)
    local pick = {}
    for _, k in ipairs(cand) do
      local have = false
      for _, a in ipairs(pick) do if a.def == k.def then have = true end end
      if not have then pick[#pick + 1] = k end
    end
    if #pick < 1 then
      if t > 3000 then H.st = "fail"; print("AUTOSPD FAIL no docked aircraft: total=" .. tostring(DIAG.total) .. " bays=" .. tostring(DIAG.bays)) end
      return
    end
    H.team = update_get_screen_team_id()
    cc2_vitesse(H.team, 1)
    local px, pz = xz(c)
    H.tgt = { x = px, z = pz + FAR }
    for _, k in ipairs(pick) do
      H.rec[#H.rec + 1] = { id = k.id, def = k.def }
      local v = update_get_map_vehicle_by_id(k.id)
      v:clear_waypoints(); v:clear_attack_target()
      v:add_waypoint(H.tgt.x, H.tgt.z)
    end
    H.st = "climb"; H.t_cmd = t
    local ids = {}
    for _, a in ipairs(H.rec) do ids[#ids + 1] = tostring(a.id) .. "/" .. tostring(a.def) end
    print("AUTOSPD launched tick=" .. t .. " team=" .. tostring(H.team) .. " ids=" .. table.concat(ids, ",") .. " target=" .. string.format("%.0f,%.0f", H.tgt.x, H.tgt.z))
    return
  end
  if H.st == "climb" then
    if airborne_all() then
      if not H.t_air then H.t_air = t; print("AUTOSPD all airborne tick=" .. t .. " after " .. (t - H.t_cmd) .. " ticks") end
      if t - H.t_air >= 900 then H.st = "phase"; begin_phase(t) end
    elseif t - H.t_cmd > 12000 then H.st = "fail"; print("AUTOSPD FAIL launch timeout")
    end
    return
  end
  if H.st == "phase" then
    sample(t)
    if t - H.t_ph >= SETTLE + WINDOW then
      phase_result()
      if H.ph >= #MODES then
        H.st = "done"; H.fin = t
        print("AUTOSPD RESULT " .. #H.res .. " phases measured ENDAUTOSPD")
      else
        begin_phase(t)
      end
    end
    return
  end
  if H.st == "done" and H.fin ~= 0 and t - H.fin > 240 then
    H.fin = 0
    for _, l in ipairs(H.res) do print(l) end
    print("AUTOSPD RESULT repeat ENDAUTOSPD")
  end
end

-- ---------------------------------------------------------------- hooks
if type(begin_load) == "function" and g_auto_orig == nil then
  g_auto_orig = begin_load
  begin_load = function(...)
    local r = table.pack(g_auto_orig(...))
    local nm = (type(begin_get_screen_name) == "function") and begin_get_screen_name() or "?"
    if type(update) == "function" and not g_auto_wrapped then
      if nm == "screen_front" and type(update_ui_event) == "function" and type(update_get_save_slots) == "function" then
        g_auto_wrapped = true
        local orig = update
        local n = 0
        update = function(...)
          n = n + 1
          if n == 900 and not g_auto_done then g_auto_done = true; pcall(try_load) end
          return orig(...)
        end
      elseif nm == "screen_veh_m" then
        g_auto_wrapped = true
        local orig = update
        update = function(...)
          pcall(step)
          return orig(...)
        end
        print("AUTOSPD harness hooked on " .. nm)
      end
    end
    return table.unpack(r, 1, r.n)
  end
end
