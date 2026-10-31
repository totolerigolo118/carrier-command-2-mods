-- TEMPORARY session test (installed for one test only): from the main-menu context, loads a save by itself, with the same
-- event as the menu's "Load" button, then lets the game run. Output goes to releve_cc2.txt through print().
local SLOT = 18
local function try_load()
  -- the menu has several Lua contexts: use cc2_vitesse's team 14 as a cross-context "already done" flag
  if type(cc2_vitesse) == "function" then
    if cc2_vitesse(14) == 2 then return end
    cc2_vitesse(14, 2)
  end
  local slots = update_get_save_slots()
  local list = {}
  local found = false
  for _, v in ipairs(slots) do
    list[#list + 1] = tostring(v.slot_index) .. ":" .. tostring(v.save_name) .. ":" .. tostring(v.time)
    if v.slot_index == SLOT then found = true end
  end
  print("SESSTEST slots=" .. table.concat(list, ","))
  if found then
    update_ui_event("load_game", SLOT)
    print("SESSTEST load_game requested slot=" .. SLOT)
  else
    print("SESSTEST slot not found")
  end
end

-- the functions of the screen API are only bound by the time begin_load runs, so test them there, not at file load
if type(begin_load) == "function" and g_sess_orig == nil then
  g_sess_orig = begin_load
  begin_load = function(...)
    local r = table.pack(g_sess_orig(...))
    local nm = (type(begin_get_screen_name) == "function") and begin_get_screen_name() or "?"
    if nm == "screen_front" and type(update) == "function" and type(update_ui_event) == "function"
       and type(update_get_save_slots) == "function" and not g_sess_wrapped then
      g_sess_wrapped = true
      print("SESSTEST hooked ctx=" .. nm)
      local orig = update
      local n = 0
      update = function(...)
        n = n + 1
        if n == 900 and not g_sess_done then g_sess_done = true; pcall(try_load) end
        return orig(...)
      end
    end
    return table.unpack(r, 1, r.n)
  end
end
