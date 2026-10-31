# SPDX-License-Identifier: GPL-3.0-or-later
"""Checks lua/cc2_vitesse_shim.lua with a real Lua 5.3 (package lupa: pip install lupa).

The plugin's C function is replaced by a Python stand-in that follows the same contract, so this
tests the SHIM and the way library_custom_6.lua uses cc2_vitesse, not the C code (that one is
tested by test_all.c). Nothing here runs in the game.
"""
from pathlib import Path
from lupa.lua53 import LuaRuntime

ROOT = Path(__file__).resolve().parent.parent
shim = (ROOT / 'lua' / 'cc2_vitesse_shim.lua').read_text()

def make(with_plugin):
    lua = LuaRuntime(unpack_returned_tuples=True)
    modes = {}
    state = {'file': 0}
    calls = []
    def mode(*args):
        # python stand-in of the C function: same contract as cp_speed_call
        calls.append(args)
        team = args[0] if args and isinstance(args[0], (int, float)) and args[0] == int(args[0]) else 0
        team = int(team)
        if not (0 <= team < 16): return 0
        if len(args) >= 2:
            m = args[1] if isinstance(args[1], (int, float)) and args[1] == int(args[1]) else 0
            if 1 <= m <= 3:
                modes[team] = int(m); state['file'] = int(m)
        elif modes.get(team, 0) == 0:
            modes[team] = state['file']
        return modes.get(team, 0)
    g = lua.globals()
    if with_plugin:
        lua.execute("cc2x = { speed = {} }")
        g.cc2x.speed.mode = lua.eval('function(f) return function(...) return f(...) end end')(mode)   # a real Lua function, like the C one
    else:
        lua.execute("cc2x = nil")
    lua.execute(shim)
    return lua, calls

# 1. the plugin function exists: the global appears and keeps the contract
lua, calls = make(True)
assert lua.eval("type(cc2_vitesse)") == "function"
assert lua.eval("cc2_vitesse(1)") == 0
assert lua.eval("cc2_vitesse(1, 3)") == 3
assert lua.eval("cc2_vitesse(1, 9)") == 3
assert lua.eval("cc2_vitesse(7)") == 3          # a team without mode adopts the last mode
assert lua.eval("cc2_vitesse(99)") == 0
# argument count is preserved: one argument = read, two = set
assert [len(c) for c in calls] == [1, 2, 2, 1, 1], [len(c) for c in calls]
print("shim with plugin: global cc2_vitesse defined, contract and argument count kept")

# 2. no plugin function: nothing is defined, the bar of library_custom_6.lua stays hidden
lua, _ = make(False)
assert lua.eval("type(cc2_vitesse)") == "nil"
print("shim without plugin: no global (type(cc2_vitesse) == 'nil'), as library_custom_6.lua expects")

# 3. a cc2_vitesse that already exists (the Mac program) is not replaced
lua = LuaRuntime(); lua.execute("function cc2_vitesse() return 42 end; cc2x = {speed={mode=function() return 1 end}}"); lua.execute(shim)
assert lua.eval("cc2_vitesse()") == 42
print("shim with an existing cc2_vitesse: left alone")

# 4. library_custom_6.lua's own calling pattern (vit_lire) on top of the shim
lib6 = (ROOT.parent / 'passation_windows' / 'lua_a_installer' / 'library_custom_6.lua').read_text()
lua, _ = make(True)
lua.execute("function update_get_screen_team_id() return 1 end; function color8(...) return 0 end; e_input={pointer_1=1}; e_input_action={press=1,release=2}")
lua.execute(lib6)
assert lua.eval("vit_lire()") == 2              # first call: mode 0 -> sets NORMAL (g_vit_mode_defaut = 2)
assert lua.eval("vit_lire()") == 2
lua.execute("vit_choisir(3)")
assert lua.eval("vit_lire()") == 3
print("library_custom_6.lua vit_lire / vit_choisir work through the shim (NORMAL by default, then FLANK)")
lua, _ = make(False)
lua.execute("function update_get_screen_team_id() return 1 end; function color8(...) return 0 end; e_input={pointer_1=1}; e_input_action={press=1,release=2}")
lua.execute(lib6)
assert lua.eval("vit_lire()") == 0
print("library_custom_6.lua without the plugin: vit_lire() == 0 (bar hidden)")
print("LUA SHIM CHECK: ALL PASS")
