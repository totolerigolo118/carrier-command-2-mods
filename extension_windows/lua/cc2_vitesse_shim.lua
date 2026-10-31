-- SPDX-License-Identifier: GPL-3.0-or-later
-- ============================================================================
--  cc2_vitesse_shim.lua
--
--  library_custom_6.lua (the ECO / NORMAL / FLANK bar) calls a GLOBAL function
--      cc2_vitesse(team [, mode])
--  On the Mac the program itself provided it. With CC2X a plugin cannot create a
--  global from C: it registers cc2x.<namespace>.<name>. This tiny shim defines the
--  global on top of the plugin's function cc2x.speed.mode (same contract):
--
--      cc2_vitesse(team)        -> mode of the team (0 = never chosen)
--      cc2_vitesse(team, mode)  -> sets the mode (1 ECO, 2 NORMAL, 3 FLANK), returns it
--
--  The plugin only registers cc2x.speed.mode when the speed_modes group is applied
--  (or with  lua_speed_stub = 1  under [debug] in cc2_patchs.ini, a test mode where the
--  buttons change a number but no aircraft speed). Without it this file does nothing,
--  so library_custom_6.lua keeps hiding the bar, as on the Mac without the program module.
--
--  Where to put it: at the top of library_custom_6.lua, or in any script of the same Lua
--  state loaded before the bar is drawn (the global is looked up at call time).
--  NOT TESTED IN THE GAME: written from the contract, checked with a stand-in for cc2x.
-- ============================================================================

if type(cc2_vitesse) ~= "function"
        and type(cc2x) == "table"
        and type(cc2x.speed) == "table"
        and type(cc2x.speed.mode) == "function" then
    -- "..." keeps the number of arguments: one argument reads, two arguments set
    function cc2_vitesse(...)
        return cc2x.speed.mode(...)
    end
end
