CARRIER COMMAND 2 - NOTES FROM PATCHING THE MAC BUILD
=====================================================

What this is: working notes, patch tables and source code from patching the MAC executable of Carrier Command 2 directly (not through Lua mods), written to be
useful to someone who works on the Windows build with a DLL. The work was done by one person with an AI assistant; every claim is tagged with how it
was checked (below). Nothing in this folder is a copy of the game: no executable, no game asset, no shader, no save file. The only pieces of the original program
quoted are short instruction sequences (5-70 bytes) at the patched places, so that the same places can be recognised elsewhere.

READ FIRST: 11_porting_and_priorities.txt, section 2. The Mac build is x86-64 and the Windows 1.5.18 build is (according to the public README of a community SDK)
32-bit x86. Addresses, instruction encodings and structure OFFSETS therefore do not carry over. What carries over (very probably) is the logic, the values, the names
and every data file. Offsets in these notes should be read as labels for "the field that holds ...", not as numbers to reuse.


FILES
-----
  01_mac_binary_and_patching_method.txt   the Mac binary, constants pool rule, code caves in dead code, linker, how everything was tested, structure layouts
  02_power_elevator_crane_taxi.txt        energy sharing, elevator platform, hangar crane (5 moves), deck taxi model, how to cancel a launch
  03_docking_states_runway_landing.txt    dock states, the single runway slot, the aircraft holding pattern, landing measurements, why the runway cannot be freed earlier
  04_helicopters.txt                      helicopter landing in the stock game, the two patches kept (-36 %), the failed "land on the elevator" experiment, second elevator study
  05_ai_wing_speed_fuel.txt               why AI aircraft crawl (hard floor speeds), dev values, engines and fuel, the ECO / NORMAL / FLANK mode patch
  06_screens_hud_cctv.txt                 the 256-px pilot UI target, one-image-per-screen ship screens, the CCTV 512 x 512 patch
  07_lua_api_and_hooks.txt                Lua version and libraries, library_custom hooks, functions seen, what Lua can and cannot command
  08_constants_and_multiplayer.txt        constants.txt and how to read engine defaults, mod system, how mods reach joining players, unit type numbers
  09_file_formats.txt                     .mesh, .txtr, .atlas, .cphys, carrier geometry, relevant XML
  10_patch_tables.txt                     EVERY patch: site address, function, bytes before / after, constants before / after
  11_porting_and_priorities.txt           from Mac to a Windows DLL, fingerprints to find the same places, what is worth doing, wish list for a Lua-facing SDK
  12_symbol_index.txt                     function names with Mac addresses (docking managers, airfield manager, power manager, renderer, Lua binding ...)
  workshop/                               source code (see below)


CONVENTIONS
-----------
Evidence tags used in the notes:
  [GAME]  measured or seen in the running game (times are GAME time: update_get_logic_tick() / 30, because a stopwatch is meaningless when the machine slows down)
  [ASM]   read from the disassembly and re-read after patching; not (yet) seen in game
  [EST]   estimate or computed from a model; not measured
  [UNV]   hypothesis not verified
Addresses: virtual addresses of the Mac executable build_mac, md5 b0107170ddaf0245cbfee8a2d876aeb6 (2026-01-05); file offset = address - 0x100000000.
Names: C++ names come from the symbol table (the Mac build is not stripped). Some names are the game's own spelling ("hanger_center", "Albatross"/"Albatros").
Ship frame: x to starboard, z to the bow, y up, metres; the game runs at 30 ticks per second; angles in radians.
Hex bytes are listed in file order (little-endian values).
Unit names: Albatross = light aeroplane, Manta = HEAVY aeroplane, Razorbill = light helicopter, Petrel = heavy helicopter (08, section 4).
"The player" = the person who played and tested.


MODULE NAMES (French; they appear in the tables, the sources and the notes)
---------------------------------------------------------------------------
  ascenseur_x2             elevator x2 (with crane and deck taxi)        grue_annulation           crane: cancel a launch
  atterrissage             landing (pattern)                             pont_retour_x2            deck taxi x2 on return ("pont" = deck)
  helicos_approche_x2      helicopters: approach x2                      helicos_pres_ascenseur    helicopters: touch down near the elevator
  helicos_ascenseur        helicopters landing on the elevator           vitesse_escadrille        squadron speed (the executable part)
  vitesse_boutons          speed buttons (the Lua bar)                   cctv_net                  sharper CCTV ("net" = sharp)
  ecriture_releve          write the log (print() into a file)           releve                    recorder (log of performance data)
  horloge                  clock                                         journal                   landing journal
  effet_tele               TV effect (the shader variant)                interface_x2              pilot UI x2
Tags inside the scripts: "programme" = executable patch, "fichier" = data-file module; actif / retire / abime = active / removed / damaged.


WHAT WAS DONE, AT A GLANCE (details and status in 10 and 11)
------------------------------------------------------------
  elevator + crane + deck taxi x2, energy share 0.4 -> 0.8         launches -41 % [GAME]            34 float redirects
  helicopters: approach x2 and touchdown near the elevator          -36 % [GAME]                      4 sites
  aircraft landing pattern (wide runway slot + circle)              4 aircraft in 7:28 [GAME]; stock not measured   10 sites
  deck taxi x2 on return                                            deck -> hangar 0:51 -> 0:32 per aircraft [GAME, one run]   3 sites
  cancel a crane launch (2nd press of the bay button)               installed, [ASM] + host test      cave 932 bytes + 2 hooks
  AI aircraft speed modes ECO / NORMAL / FLANK                      Lua function seen working in game; effect only NEAR waypoints (cruise is ~120 m/s in every mode, measured)   cave 671 bytes + Lua bar
  CCTV screen 512 x 512 (4 hooks, 1 cave)                           installed, [ASM] + host test
  Lua print() to a file; game clock; landing journal; recorder      all seen working in game [GAME] (recorder and print-to-file in a loaded session on 2026-10-25)
  shader without the old-TV effect (data file)                      works on any platform
  rejected / abandoned: pilot UI 512 px (cosmetic choice), helicopters landing on the elevator (collision), second elevator (not worth it), runway released earlier (collision risk)


THE workshop/ FOLDER
--------------------
It mirrors the layout of the original working folder, so that the relative paths inside the scripts still make sense. The folder names are French:
outil = tool, generateurs = generators, fichiers = files (data-file modules), sauvegarde = backup, etudes = studies, modules_en_reserve = modules held in reserve.
  workshop/outil/patchs_cc2.py                 the patch tool: modules of type "programme" (RETOUCHES = "imm" / "rip" rows) and "fichier" (file replacement); all safety checks
  workshop/outil/generateurs/*.c *.s           SOURCE OF THE CODE CAVES: grue_annulation.c, vitesse_escadrille.c, cctv_net.s, ecriture_releve.s, helicos_ascenseur.c (abandoned experiment)
  workshop/outil/generateurs/generer_*.py      generators: compile a cave with clang, link it themselves at its address (generer_helicos_ascenseur.py holds the mini-linker and the table of
                                               game addresses), and write the patch tables from the disassembly (generer_atterrissage.py, generer_pont_retour.py, generer_cctv_net.py ...)
  workshop/outil/generateurs/simuler_file_atterrissage.py     simulation of the landing queue (gate, window, lap, landing duration)
  workshop/fichiers/<module>/library_custom_N.lua            the four Lua modules (clock, landing journal, recorder, speed bar)
  workshop/tests/                              off-game tests (disassembly re-read, caves executed on a fake manager under Rosetta, Lua under lupa)
The scripts need a copy of the ORIGINAL executable at sauvegarde/build_mac_origine (not included), clang, objdump and, for the Lua tests, Python with `lupa`. They have only been
run on macOS. Do not run the tools or tests against a game folder you care about without reading them first: they are written to refuse unknown arguments and a game that is
running, but they do patch files.
Generated modules (outil/modules/*.py in the original folder) are not included: 10_patch_tables.txt is their readable form.
Some names inside the scripts are still French (variables, labels, tags such as "programme", "fichier", "actif", "retire"); comments and messages are in English.
