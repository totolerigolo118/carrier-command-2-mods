-- TEMPORARY AUTOMATIC MEASUREMENT (installed for one test only; see the test script).
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

-- ---------------------------------------------------------------- ship part
local H = { st = "wait", ids = {}, rec = {}, log = {}, t_cmd = nil, t_air = nil, t_recall = nil, hb = 0, fin = 0 }

local function now() return update_get_logic_tick() end

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

local function note(a, key, t)
  if a[key] == nil then a[key] = t end
end

local function track(t)
  local airborne, stored, n = 0, 0, 0
  for _, a in ipairs(H.rec) do
    local v = update_get_map_vehicle_by_id(a.id)
    if v:get() then
      n = n + 1
      local s = v:get_dock_state()
      if a.last == 1 and s == 5 then a.fail = (a.fail or 0) + 1 end
      a.last = s
      if H.st == "launch" then
        if s == 2 then note(a, "t_pending", t) elseif s == 3 then note(a, "t_undock", t) end
        if s == 0 then note(a, "t_air", t); airborne = airborne + 1 end
      else
        if s == 5 then note(a, "t_queue", t) elseif s == 1 then note(a, "t_runway", t)
        elseif s == 6 then note(a, "t_deck", t) elseif s == 4 then note(a, "t_stored", t); stored = stored + 1 end
      end
    end
  end
  return airborne, stored, n
end

local function fmt(t, base) if t == nil then return "--" end return tostring(t - base) end

local function summary(tag)
  local parts = { "AUTO " .. tag, "t_cmd=" .. tostring(H.t_cmd), "t_recall=" .. tostring(H.t_recall) }
  for i, a in ipairs(H.rec) do
    parts[#parts + 1] = string.format("a%d(id=%d,def=%d,pend=%s,undock=%s,air=%s,q=%s,rw=%s,deck=%s,stored=%s,fail=%d)", i, a.id, a.def,
      fmt(a.t_pending, H.t_cmd), fmt(a.t_undock, H.t_cmd), fmt(a.t_air, H.t_cmd),
      fmt(a.t_queue, H.t_cmd), fmt(a.t_runway, H.t_cmd), fmt(a.t_deck, H.t_cmd), fmt(a.t_stored, H.t_cmd), a.fail or 0)
  end
  parts[#parts + 1] = "ENDAUTO"
  print(table.concat(parts, " "))
end

local function step()
  local t = now()
  local c = carrier()
  if not c then return end
  if H.st == "wait" then
    if t < 900 then return end
    local cand = candidates(c)
    if #cand < 1 then
      if t > 3000 then
        H.st = "fail"
        print("AUTO FAIL no docked aircraft found diag: total=" .. tostring(DIAG.total) .. " team=" .. tostring(DIAG.team) .. " dock4=" .. tostring(DIAG.dock4)
          .. " attached=" .. tostring(DIAG.att) .. " dockparent=" .. tostring(DIAG.dockp) .. " bays=" .. tostring(DIAG.bays)
          .. " carrier=" .. tostring(DIAG.cid) .. " myteam=" .. tostring(DIAG.myteam))
      end
      return
    end
    for i = 1, math.min(N_AIR, #cand) do
      H.rec[#H.rec + 1] = { id = cand[i].id, def = cand[i].def }
    end
    local px, pz = c:get_position_xz():x(), c:get_position_xz():y()
    H.t_cmd = t
    local ids = {}
    for _, a in ipairs(H.rec) do
      local v = update_get_map_vehicle_by_id(a.id)
      v:clear_waypoints(); v:clear_attack_target()
      v:add_waypoint(px, pz + AHEAD)
      ids[#ids + 1] = tostring(a.id) .. "/" .. tostring(a.def)
    end
    H.st = "launch"
    print("AUTO launch ordered tick=" .. t .. " n=" .. #H.rec .. " ids=" .. table.concat(ids, ",") .. " candidates=" .. #cand
      .. " carrier=" .. tostring(c:get_id()) .. " pos=" .. string.format("%.0f,%.0f", px, pz))
    return
  end
  if H.st == "launch" then
    local airborne = track(t)
    local any = false
    for _, a in ipairs(H.rec) do if a.t_pending or a.t_undock or a.t_air then any = true end end
    if not any and t - H.t_cmd > 1500 then H.st = "fail"; summary("FAIL no response to launch orders"); return end
    if airborne == #H.rec then
      H.t_air = t
      H.st = "recall"
      local px, pz = c:get_position_xz():x(), c:get_position_xz():y()
      H.t_recall = t
      for _, a in ipairs(H.rec) do
        local v = update_get_map_vehicle_by_id(a.id)
        v:clear_waypoints(); v:clear_attack_target()
        local wp = v:add_waypoint(px, pz)
        v:set_target_vehicle(wp, c:get_id())
      end
      summary("LAUNCHED all airborne")
      return
    end
    if t - H.t_cmd > 9000 then H.st = "fail"; summary("FAIL launch timeout") end
    return
  end
  if H.st == "recall" then
    local _, stored = track(t)
    if stored == #H.rec then H.st = "done"; H.fin = t; summary("RESULT returns finished") ; return end
    if t - H.t_recall > 24000 then H.st = "done"; H.fin = t; summary("RESULT returns timeout") end
    if t - H.hb > 1800 then H.hb = t; summary("hb tick=" .. t) end
    return
  end
  if H.st == "done" and t - H.fin > 300 and H.fin ~= 0 then
    H.fin = 0; summary("RESULT repeat")          -- print the result a second time, in case of rate limiting
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
        print("AUTO harness hooked on " .. nm)
      end
    end
    return table.unpack(r, 1, r.n)
  end
end
