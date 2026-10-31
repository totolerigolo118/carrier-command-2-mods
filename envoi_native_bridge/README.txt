README - symbol tables of the macOS build of Carrier Command 2 (objective 1 of the request)
=======================================================================================

WHAT THIS IS
  The complete symbol table of the macOS x86-64 build, a filtered index of names related to the game-session lifecycle,
  and a static analysis of that lifecycle with candidate events and matching fingerprints for the Windows build.
  Names, addresses and short disassembly excerpts only: no game code, no assets, no executable.
  The analysis is static reading only. NOTHING in these files was observed in a running game at function level.
  The Mac build embeds the version string v1.5.17; the Windows build discussed in the request is 1.5.18: code may differ.

SOURCE EXECUTABLE (verified)
  file    : build_mac   (Mach-O 64-bit x86_64, not stripped, not signed), 59,482,272 bytes
  MD5     : b0107170ddaf0245cbfee8a2d876aeb6      <- the build named in the request: it matches
  SHA-256 : 53d8bb02e0fb2b3be764f5d49f8a0e60cf83819ba704e31f3ce75cdef66fd823
  build   : 2026-01-05 (as stated in the request)
  This is the original, unmodified file. Both hashes were computed on the file that was read.

FILES
  symbols_raw.txt                  58,354 lines. Output of `nm -n`, mangled names, sorted by address.
                                   Columns: <virtual address> <type letter> <mangled name>.
                                   Undefined (imported) symbols have no address.
  symbols_demangled.txt            The same 58,354 lines in the same order, demangled by `c++filt -_`.
                                   Line N of this file is line N of symbols_raw.txt.
  symbols_lifecycle_candidates.txt 629 symbols picked by NAME. Six sections (A-F), each symbol listed once, with
                                   its mangled name after "<=". A name match means "worth reading",
                                   not "is the lifecycle event".
  session_lifecycle_analysis.md    Objectives 2 and 3: object model, call sequences (load a save, quit to menu, load another
                                   save while in game, join), candidate WORLD_READY / WORLD_TEARDOWN_BEGIN / WORLD_DESTROYED
                                   points with evidence, thread context, failure cases, confidence tags, runtime test points.
  windows_porting_fingerprints.md  Objective 4: strings, call counts and structure to test on the Windows executable. No match is claimed.

EXTRACTION COMMANDS (Apple developer tools, macOS)
  nm -n build_mac > symbols_raw.txt
  c++filt -_ < symbols_raw.txt > symbols_demangled.txt
  The candidate index is a regular-expression filter on symbols_demangled.txt (patterns are written at the
  top of each section title; the suggested words of the request were all used).

TYPE LETTERS (nm)
  t / T  code (local / exported)      s / S  read-only data (constants, strings, vtables, typeinfo)
  d / D  initialised data             b / B  zero-initialised data        U  undefined (imported)
  Counts in this file: t 28,925   T 15,673   s 6,352   b 3,060   D 2,305   S 718   d 715   (the rest: undefined imports).

LIMITATIONS - READ BEFORE USING
  - Addresses are macOS x86-64 virtual addresses (image base 0x100000000). The Windows build is x86 PE, a different
    and later build: do not assume addresses, object offsets, calling conventions or instruction encodings carry over.
    Only names, class structure, strings, constants and call relationships can be compared.
  - The table also contains third-party libraries linked into the executable (ImGui, PhysX, Steam networking wrappers, rapidxml...).
    Game classes use the prefix c_ (c_logic_server, c_logic_client, c_logic_main_menu, c_application, c_map_server, ...).
  - Mach-O symbols carry no sizes. A function length can only be estimated from the next symbol's address.
  - Names are what the compiler kept. Inlined functions have no symbol; "(.cold.N)" entries are split-off cold paths.
  - The candidate index is a name filter: it can miss events that have unremarkable names, and section F is deliberately loose.

READ NEXT
  session_lifecycle_analysis.md first (section 1 has the short answers), then windows_porting_fingerprints.md.
