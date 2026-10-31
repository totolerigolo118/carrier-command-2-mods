CARRIER COMMAND 2 - WHAT I DID ON THE MAC BUILD
===============================================

I patched the Mac executable directly (no Lua mod, no DLL), with AI help for the reverse-engineering. The Mac build is x86-64 and is not stripped, so the function
names are readable. These files are my notes, in case they help your work on Windows. They contain no game files.


RESULTS (game time, same save, same place)
------------------------------------------
  Elevator + crane + deck taxi x2 (elevator/crane energy share 0.4 -> 0.8)      launching 4 aircraft:  3:50 -> 2:15
  Helicopters: approach x2 + touchdown near the elevator                          4 helicopters:         6:52 -> 4:22
  Aircraft landing pattern: wider runway slot + circular holding pattern          4 aircraft stored in 7:28, one runway grant every 1:31 (stock not measured)
  Deck taxi x2 on return                                                          deck -> hangar 0:51 -> 0:32 per aircraft; 4 returns 7:28 -> 5:49 (one run each, not the same aircraft mix)


INSTALLED, NOT SEEN IN GAME YET
-------------------------------
  Cancel a launch already taken by the crane (2nd press of the bay button)
  AI aircraft speed modes ECO / NORMAL / FLANK: the Lua function works in game; but the modes only act NEAR a waypoint (far away every aircraft cruises at ~120 m/s, measured)
  Sharper CCTV screen (512 x 512 instead of 128 x 128)


LUA TOOLS
---------
  Game clock and landing journal: used in game.
  Performance recorder and print() written to a file: seen working in a loaded game session.


TRIED AND DROPPED
-----------------
  Helicopters landing on the elevator (two collided in the test)
  A second elevator (not worth it: the single runway slot is the bottleneck, not the elevator)
  Freeing the runway earlier (collision risk)
  A sharper pilot UI (rejected)


IF YOU ONLY READ THREE THINGS
-----------------------------
  1. XML mods for elevator / crane / taxi speed never worked: those speeds are hard-coded in the program, and the XML settings that look like speeds do not control them.   (notes, part 02)
  2. The runway is ONE slot, held from the moment it is granted until the aircraft is on the elevator. That is the real bottleneck of the carrier.   (notes, part 03)
  3. AI aircraft fly at hard floor speeds (48 and 72 m/s). The "cruise speed" setting looks like the control but is never read.   (notes, part 05)


THE FILES
---------
  cc2_notes.txt       the explanations, in parts 00-09 and 11. Start with part 11 (Mac build vs Windows build).
  cc2_reference.txt   every patch: address, function, bytes before / after; and function names with their Mac addresses.
  cc2_sources.txt     all the source code: code caves in C and assembly, generators and mini-linker, patch tool, Lua modules, off-game tests.


READ THIS FIRST
---------------
Your Windows build is probably 32-bit, while the Mac one is 64-bit. Addresses and structure offsets will NOT match. What carries over is the logic, the values, the
names and the data files. Part 11 explains how to find the same places on a build without function names (float values, groups of constants, strings, the parsers
that read the saved state), and ends with a wish list of what a Lua-facing SDK could expose.


WHAT IS NOT KNOWN
-----------------
Nothing was tested on Windows. Gains tagged [EST] in the notes are estimates. Multiplayer was never tested with a second player. Each claim in the notes carries a tag:
[GAME] seen in the running game, [ASM] read from the disassembly, [EST] estimate, [UNV] not verified.
