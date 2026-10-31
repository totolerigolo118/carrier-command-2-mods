-- TEMPORARY PROBE (installed only for one test, then removed): writes ONE line per Lua context with print()
-- (print goes to releve_cc2.txt thanks to the print-to-file patch).
local NAMES = { "update_get_logic_tick", "update_get_time_ms", "update_get_time_since_epoch", "update_ui_line",
  "update_get_missile_count", "update_get_projectile_count", "update_get_screen_state_active", "update_get_is_focus_local",
  "update_get_screen_vehicle", "update_get_map_vehicle_count", "update_get_tile_count", "update_get_screen_team_id",
  "begin_load", "begin_get_screen_name", "begin", "update", "cc2_vitesse", "dofile", "loadfile", "load", "loadstring",
  "require", "io", "os", "debug", "utf8", "get_is_controller_peer", "update_set_screen_background_type",
  "update_ui_event", "update_get_save_slots", "update_launch_carrier", "update_get_loc", "update_get_screen_team_id" }

local function probe(first_args)
  local out = {}
  local function add(k, v) out[#out + 1] = k .. "=" .. tostring(v) end
  local nm = "?"
  if type(begin_get_screen_name) == "function" then
    local ok, v = pcall(begin_get_screen_name); if ok and v then nm = tostring(v) end
  end
  add("ctx", nm)
  add("ver", _VERSION)
  add("pack", type(string.pack))
  for _, n in ipairs(NAMES) do add(n, type(_G[n])) end
  if type(update) == "function" and debug and debug.getinfo then
    local ok, info = pcall(debug.getinfo, update, "u"); if ok and info then add("update_nparams", info.nparams) end
  end
  if type(update_get_logic_tick) == "function" then
    local ok, v = pcall(update_get_logic_tick); add("tick", ok and tostring(v) or "err")
  end
  if type(update_get_time_since_epoch) == "function" then
    local ok, v = pcall(update_get_time_since_epoch); add("epoch", ok and tostring(v) or "err")
  end
  -- cc2_vitesse tests, only once for the whole game (the mode table is shared by all Lua contexts)
  if type(cc2_vitesse) == "function" and cc2_vitesse(15) == 0 then
    local function c(label, ...)
      local ok, v = pcall(cc2_vitesse, ...)
      add(label, ok and tostring(v) or ("ERR:" .. tostring(v)))
    end
    c("v_read15", 15)       -- 0 expected (no mode yet)
    c("v_set15_3", 15, 3)   -- 3
    c("v_read15b", 15)      -- 3
    c("v_set15_9", 15, 9)   -- invalid mode: stays 3
    c("v_set15_0", 15, 0)   -- invalid mode: stays 3
    c("v_team99", 99)       -- out of range: 0
    c("v_teamneg", -1)      -- out of range: 0
    c("v_teamstr", "x")     -- not a number: team 0
    c("v_noarg")            -- no argument: team 0
    c("v_float", 15.0)      -- float with integer value: team 15 -> 3
    c("v_set15_1", 15, 1)   -- back to ECO
  end
  print("PROBE " .. table.concat(out, " ") .. " ENDPROBE")
end

-- the screen script defines update() AFTER the library files are loaded, so hook begin_load (like the recorder does)
if type(begin_load) == "function" and g_probe_orig_begin_load == nil then
  g_probe_orig_begin_load = begin_load
  begin_load = function(...)
    local r = table.pack(g_probe_orig_begin_load(...))
    if not g_probe_done then g_probe_done = true; pcall(probe) end
    return table.unpack(r, 1, r.n)
  end
elseif not g_probe_done then
  g_probe_done = true; pcall(probe)      -- contexts without begin_load: run right away
end
