# Game-session lifecycle in the macOS build of Carrier Command 2 (objectives 2 and 3)

Source: original macOS x86-64 `build_mac`, MD5 `b0107170ddaf0245cbfee8a2d876aeb6` (hashes and extraction commands: `README.txt`).
Method: static reading only (`objdump -d`, symbol table, strings and vtables read from the file). **The game was not run for this
analysis. Nothing below was observed at function level in a running game.**
All addresses are macOS virtual addresses and must not be assumed to carry over to the Windows build (see `windows_porting_fingerprints.md`).
The string `v1.5.17` is embedded in this build (in `c_application::process_application_event`, at `0x100435324`): the Mac build is 1.5.17 and the
request names a Windows 1.5.18. Code may have changed between the two. Treat every conclusion as "true for 1.5.17 on macOS".

## Legend

| Tag | Meaning |
|---|---|
| **CONFIRMED BY DISASSEMBLY** | read directly in instructions, data or strings of this executable |
| **OBSERVED IN GAME** | seen while the game was running. **Nothing at function level.** One earlier whole-game test is mentioned in section 8 |
| **INFERRED / NOT YET VERIFIED** | deduced from names, structure or adjacency; needs a runtime check |

## 1. Short answers to the questions of the request

| Question | Answer | Tag |
|---|---|---|
| Does the logic server exist in the main menu? | **No.** The menu runs a different class, `c_logic_main_menu`. A `c_logic_server` object is created only by `c_application::reset_server()`, whose only callers are `load_saved_game` and `host_game`. | CONFIRMED |
| Is `c_logic_client` a session boundary? | **Not by itself.** `join_game` creates a client and no server; `load_saved_game` / `host_game` create both. A hosted or local game ends when the **server** is destroyed; a remote game ends when the **client** is destroyed. | CONFIRMED (call graph) |
| What starts a session? | An application event string (for example `load_game 7`, `new_game_campaign`, `host_game`, `join_game_token ...`) handled by `c_application::process_application_event`, called once per frame from `c_application::on_update`. | CONFIRMED |
| What ends one? | `c_application::destroy_current_screen_state()`, called first by every transition: quit to menu, load another save, host, join, and process exit (`on_destroy`). | CONFIRMED |
| Can another save be loaded without restarting? | **Yes, and without passing through the menu.** `load_saved_game` begins with `destroy_current_screen_state()`, which tears down the current client and server, then builds new ones. | CONFIRMED |
| Which threads? | Server logic, client logic and menu logic are each an `mm_thread_object` on their own thread (profiler names `"Server"` and `"Logic"`). The application events and `destroy_current_screen_state` run on the application thread (`on_update`). | CONFIRMED (structure); thread identity of Lua screens NOT established |

## 2. The object model (CONFIRMED BY DISASSEMBLY)

`c_logic_server`, `c_logic_client` and `c_logic_main_menu` all derive from `mm_thread_object`. The first three virtual slots of each vtable are
`begin()`, `loop()`, `end()` (vtable contents read from the file):

```
vtable for c_logic_server    0x1029cddb8:  +0x10 -> 0x1003211e4 begin   +0x18 -> 0x100321ac0 loop   +0x20 -> 0x100321b56 end
vtable for c_logic_client    0x1029cd7f8:  +0x10 -> 0x1002e5c1a begin   +0x18 -> 0x1002e623e loop   +0x20 -> 0x1002e62b6 end
vtable for c_logic_main_menu 0x1029cbef0:  +0x10 -> 0x1002aa81e begin   +0x18 -> 0x1002ab272 loop   +0x20 -> 0x1002ab2f4 end
```

The thread body is the shared `mm_thread_object::thread_execute()` (`0x1002b846e`): call slot 0 once, then call slot 1 repeatedly while the stop flag at
`this+0x50` is clear (read under the mutex at `this+0x10`), then tail-call slot 2.

```
1002b847c  movq (%rdi),%rax ; callq *(%rax)        ; begin()
1002b848e  movb 0x50(%r12),%r15b                    ; stop flag (read under lock)
1002b84a7  callq *0x8(%rax)                         ; loop()   (repeated until the flag is set)
1002b84d2  jmpq  *0x10(%rax)                        ; end()
```

`mm_thread_object::join()` (`0x100326e34`) sets that flag under the lock and then blocks on the thread: it is the "please stop and wait" call.

```
100326e4a  movb $0x1,0x50(%rbx)                     ; request stop
100326e61  jmp  <thread join stub>                  ; wait for the thread to finish (end() has run)
```

`c_logic_server::create(unsigned, mm_string const&, c_application_event_container*)` (`0x10043fe22`) ends by starting that thread with
`thread_execute` as the entry point (`0x10043ff23` .. `0x10043ff2f`). `c_logic_server::loop()` is only a timing wrapper around `c_logic_server::tick()`:
the single call is at `0x100321b22`; `tick()` is `0x10033ce58`.

## 3. Sequences (CONFIRMED BY DISASSEMBLY unless stated)

All call sites below are direct calls found in the disassembly of `0x100380000`-`0x100452000` (indirect calls were not searched). The call sites of `load_saved_game`, `host_game` and `join_game` each sit right after the string comparison they belong to (CONFIRMED by address order). For the three quit events the string-to-call-site pairing was **not traced** (the handlers lie in `0x100433fda`-`0x100434188`; INFERRED that all three end in `quit_logic_to_menu`).

```
c_application::on_update()  0x10042e044            (application thread, once per frame)
 └─ process_application_event(string)  0x100433f4a   call site 0x10042f4e9
      "abort_load_game", "quit_to_menu", "force_network_error"      -> quit_logic_to_menu   (3 call sites: 0x100434151, 0x10043417e, 0x10043426b)
      "load_game %u" , "host_load_game %u"                          -> load_saved_game      (call sites 0x100434251, 0x1004347db)
      "new_game_campaign" "new_game_custom" "host_game" "host_game_campaign" -> host_game   (0x1004345ed, 0x100434646, 0x1004346a2, 0x100434701)
      "join_game_steam_id %s %u %s" , "join_game_token %s %u"      -> join_game            (0x1004348b9, 0x1004349f7)
```

**Load a save (from the menu or from inside a game)** — `c_application::load_saved_game` (`0x100439080`):
1. `destroy_current_screen_state()` (`0x1004390a8`): tears down whatever exists (menu, or client and server).
2. `c_mod_manager::set_mod_mode`, `reload_assets()`.
3. `reset_logic()` (`0x1004390da`): `operator new` + `c_logic_client::c_logic_client()` + `mm_scoped_ptr<c_logic_client>::reset(new)` (replaces the old client), then a new HUD.
4. `reset_server()` (`0x1004390e2`): `operator new` + `c_logic_server::c_logic_server()` + `mm_scoped_ptr<c_logic_server>::reset(new)`.
5. Network managers (`create_network_local` or `create_network_internet`).
6. `c_logic_server::create(...)` (`0x1004392c6`) — starts the **server thread** — then `c_logic_client::create(...)` (`0x1004392fa`).
`host_game` (`0x100439a4c`) has the same shape (a new campaign takes the `generate` path instead of `load_game` inside the server's `begin()`).
`join_game` (`0x10043a032`) does steps 1, 3, 5 and `c_logic_client::create` only: **no server**.

**Server thread, `c_logic_server::begin()` (`0x1003211e4`, 2268 bytes):** profiler thread name `"Server"`; loading texts; definition containers
(`c_game_object_definition_container::create`, `c_environment_tile_definition_container::create`); `c_application_constants::load()`; `c_resource_inventory_table::build()`;
then **either** `c_logic_server::load_game(string, 4)` (call `0x1003214ad`) **or** `c_logic_server::generate(e_scenario_type)` (call `0x10032177a`);
then `mm_thread_task_processor::create`, `c_fluid_sim_weather::create` (+ its thread), `c_fluid_sim_ocean_currents::create`, `c_ocean::update_simulation` ×2, a debug render buffer;
**finally a flag is published under the object lock and the function returns** (section 5, R1).
Log strings in this function and its callees (useful as runtime markers): `"c_logic_server: loading saved game... "`, `"c_logic_server: server world seed: "`,
`"c_logic_server: failed to load game: "`, `"c_logic_server: loaded game: "`, `", quitting to menu..."`; in `load_game`: `"reading save file..."`, `"save file read"`,
`"parsing scene data..."`, `"parsed scene data"`, `"proceding with game"` (sic); in `post_load_saved_game`: `"post-loading saved game..."`, `"finished post-loading saved game"`.

**Failed load (important):** if `load_game` returns non-zero, `begin()` stores the code at `this+0x550`, sleeps (a sleep stub called with `0x16e360` = 1,500,000, which is 1.5 s if the unit is microseconds; the unit is INFERRED from the 1 ms sleep in `mm_thread_object::loop()`), pushes the event string
`"abort_load_game"` to the application (`push_event` at `0x10032167d`), and then **continues to the same tail** (jumps to `0x100321883`), including the flag store. The
application then handles `"abort_load_game"` as quit-to-menu.

**Server thread, `loop()` / `end()`:** `loop()` = timing + `tick()`. `end()` (`0x100321b56`, 196 bytes) calls, in order: `c_server_peer_manager::destroy`, joins of the weather,
ocean and ocean-currents threads, `c_tile_container_server::destroy`, `c_scene_region_container::destroy`, `c_vehicle_container_server::destroy`, `c_missile_container_server::destroy`,
`c_environment_tile_definition_container::destroy`, `c_game_object_definition_container::destroy`, `mm_profiler::end_thread`.

**Teardown, `c_application::destroy_current_screen_state()` (`0x10043a82c`, 726 bytes)** branches on an application state integer (`this+0x1340`: `0` and `1`; the meaning menu / in game is INFERRED from what each branch tears down):
- state 0 (menu): `c_splash_sequence::destroy`, `join()` on the menu logic, reset of the message client manager, of `c_logic_main_menu` and of the HUD.
- state 1 (in game), in order:
```
10043a949  callq mm_thread_object::join()           ; the CLIENT thread (object at this+0x1c98): stop + wait (client end() runs)
10043a99c  cmpb $0x0,0x1cd8(%rbx) ; je skip          ; flag: a LOCAL server exists
10043a9a5  callq mm_thread_object::join()           ; the SERVER thread (object at this+0x1c90): stop + wait (server end() runs)
10043aa35  callq mm_scoped_ptr<c_logic_client>::reset(nullptr)   ; ~c_logic_client + delete
10043aa43  callq mm_scoped_ptr<c_logic_server>::reset(nullptr)   ; ~c_logic_server + delete
10043aa51  callq mm_scoped_ptr<c_screen_hud>::reset(nullptr)
10043aa75  callq c_audio_manager::clear()
10043aabb  callq c_mod_manager::clear_temp_mods()
```
`mm_scoped_ptr<c_logic_server>::reset` (`0x100320dbc`) calls `~c_logic_server()` (`0x100320dfa`, at `0x100320dd7`) and then `operator delete` (`0x100320ddf`).
Other callers of `destroy_current_screen_state`: `quit_logic_to_menu` (`0x100438f4d`), `load_saved_game`, `host_game`, `join_game`, `on_destroy` (`0x10044e4eb`, process exit).
`quit_logic_to_menu` (`0x100438f22`) then builds a new `c_logic_main_menu`, local `c_message_server_manager` / `c_message_client_manager` (not a `c_logic_server`), and starts the splash.

## 4. The three scenarios the request names

| Scenario | What happens (CONFIRMED) |
|---|---|
| Quit to menu from a game | event `quit_to_menu` → `quit_logic_to_menu` → `destroy_current_screen_state` (state 1 path: join client, join server if local, delete both) → new `c_logic_main_menu`. |
| Load a save from the menu | event `load_game N` → `load_saved_game` → `destroy_current_screen_state` (state 0 path) → new client, new server, `c_logic_server::create` starts the server thread → `begin()` loads the file. |
| Load another save while in a game | the same event; `destroy_current_screen_state` takes the state 1 path, **then** the new objects are built in the same call. No menu in between. The old server thread has been joined (its `end()` finished) before the new `c_logic_server` is constructed. |

## 5. Candidate events

Thread context: R1, R2, T3, D1 are about the **server thread**; T1, T2, D2 run on the **application thread**; R3 is on the client thread, handled on the application thread.

### WORLD_READY

**R1 — `c_logic_server::begin()` completing (the flag store)** — best candidate on the server side.
- Function: `c_logic_server::begin()`, macOS `0x1003211e4`; the store is at `0x100321970`, the return at `0x100321991`.
- Caller: `mm_thread_object::thread_execute()` (`0x1002b846e`) through vtable slot 0. Callees: see section 3.
- Evidence:
```
100321968  movq %r13,%rdi ; callq <lock>            ; take the object lock
100321970  movb $0x1,0xd8(%r14)                      ; publish "ready" (this+0xd8 = 1)
10032197b  movq %r13,%rdi ; callq <unlock>
10032198e..100321991  popq ... ; retq                 ; back into thread_execute, which then calls loop() repeatedly
```
- Execution conditions: normal path, **and also after a failed load** (see "Failed load" above). A caller must read the error code at `this+0x550` (non-zero = failure) or listen for `"abort_load_game"`.
- Confidence: HIGH that this is the last act of `begin()` and that it is published under the lock (CONFIRMED). MEDIUM that `+0xd8` means "world ready": **no reader of `+0xd8` was found** among the 62 functions of `c_logic_server`, `c_server_peer_manager`, `c_message_*_manager` and `c_network_interface_local` that were scanned (INFERRED).
- Failure cases: failed load (above); a save that loads but whose `post_load_saved_game` found problems is not distinguishable here.

**R2 — first `c_logic_server::tick()` after `begin()` returned.**
- Function `c_logic_server::tick()`, `0x10033ce58`, called from `c_logic_server::loop()` at `0x100321b22`; `loop()` is slot 1 of the vtable.
- Evidence: `thread_execute` calls slot 1 only after `begin()` has returned and the stop flag is clear (CONFIRMED). Same failed-load caveat.
- Confidence: HIGH for ordering (CONFIRMED); "safe for gameplay operations" is INFERRED. Easy to hook because it already exists as a per-tick event: take the first tick after a new server object.

**R3 — client-side signal `"logic_assets_created"`** (for the client UI side, not for world content).
- Pushed by `c_logic_client::tick()` (`0x1002f74ce`) at `0x1002f7a97` (`c_application_event_container::push_event`), after the client's pending resource events are processed, `build_render_buffer_resources()` ran, a `c_message_client_to_server_request_mod_file_download` message was sent and client field `+0x250` was set to `4`.
- Consumed by `process_application_event` (`0x100435c49`): if the client exists (`this+0x1c98 != 0`) it calls `reload_assets()` and creates the pause menu from `"scripts/pause_menu.lua"` (`c_screen_pause_menu::create`, `0x100435d04`).
- Confidence: HIGH for the mechanism (CONFIRMED); that it equals "world ready" for gameplay is INFERRED (it says the **client's** assets exist). The client state machine `c_logic_client::begin_game_state(e_game_state)` (`0x1002e6f68`, values 0-5, state 0 = `"loading"`) was only partly read: the later states are not mapped.

### WORLD_TEARDOWN_BEGIN

**T1 — entry of `c_application::destroy_current_screen_state()`** (application thread) — recommended for "stop accepting mod operations".
- `0x10043a82c`. Callers: `quit_logic_to_menu`, `load_saved_game`, `host_game`, `join_game`, `on_destroy`. Execution condition for a real world teardown: state integer `this+0x1340 == 1` (INFERRED to mean "in game").
- Confidence: HIGH (CONFIRMED call graph). Caveat: it also runs when there is nothing but the menu (state 0), and the `this+0x1340` offset is Mac-specific.

**T2 — `mm_thread_object::join()` on the server** (call site `0x10043a9a5`, only if a flag at `this+0x1cd8` is set, presumably "a local server exists").
- Sets the stop flag `server+0x50` under the lock. The server thread finishes its current `tick()`, reads the flag before the next `loop()`, and runs `end()`: **at most one more tick can complete after T2**.
- Confidence: HIGH (CONFIRMED). `join()` is shared by every thread object, so a hook must identify the object as a `c_logic_server` (vtable pointer `0x1029cddc8`).

**T3 — entry of `c_logic_server::end()`** (server thread, `0x100321b56`): first call is `c_server_peer_manager::destroy`. Confidence HIGH (CONFIRMED); from this point objects are being destroyed on the server thread, so mod operations must already have stopped (T1/T2).

### WORLD_DESTROYED

**D1 — return of `join()` on the server** (instruction after `0x10043a9a5`, i.e. `0x10043a9aa`). The server thread has run `end()`; tile, scene-region, vehicle and missile containers and the definition containers are destroyed. The `c_logic_server` object itself is still allocated.
**D2 — `mm_scoped_ptr<c_logic_server>::reset(nullptr)`** (call `0x10043aa43`; `~c_logic_server` at `0x100320dfa`, `operator delete` at `0x100320ddf`): the whole server object is gone — the strongest "previous session's objects are no longer valid". It is also the point after which `reset_server()` (for the next session) can create a new one.
Confidence HIGH for both (CONFIRMED order); D2 is the best single point.

## 6. Failure cases and edge cases

- **Client-only session** (`join_game`): no server object, no server thread. Server-side events never fire; use the client object (`c_logic_client::end()`, `mm_scoped_ptr<c_logic_client>::reset`, `0x10043aa35`).
- **Failed load** reaches the ready flag (R1/R2) with an invalid world; the `"abort_load_game"` event follows after about 1.5 s.
- **Load while in a game**: old server fully joined, deleted, then a new one constructed in the same call; hooks keyed on "server exists" must treat that as destroy-then-create.
- **Process exit**: `on_destroy` also calls `destroy_current_screen_state`.
- Direct-call scan only: tail calls or calls through function pointers into these functions could exist and were not searched.
- The application state integer, the local-server flag and the object offsets above are macOS 64-bit values and will differ on x86.

## 7. If nothing here can be trusted without running the game: the best instrumentation points

1. **The game's own log lines** (they exist in this build as strings): `"c_logic_server: loading saved game... "`, `"c_logic_server: loaded game: "`, `"c_logic_server: failed to load game: "`, `"post-loading saved game..."`, `"finished post-loading saved game"`. If the Windows build writes them to its log, a single save load gives a free runtime timeline.
2. **`mm_thread_object::thread_execute`** (`0x1002b846e`): one hook covers every thread object; identify `c_logic_server` by its vtable pointer; the return of the first indirect call is R1, the tail call is T3.
3. **`mm_thread_object::join`** (`0x100326e34`): T2 when the object is a `c_logic_server`; its return is D1.
4. **`mm_scoped_ptr<c_logic_server>::reset`** (`0x100320dbc`): D2 (argument `nullptr` = destruction) and creation (non-null argument).

## 8. What was and was not observed

- OBSERVED IN GAME (earlier whole-game test, not function-level): loading a save from the menu with the Lua call `update_ui_event("load_game", 18)` worked on this build, about 4 minutes of play, 123 vehicles, no crash. This is consistent with the `"load_game %u"` handler above. It says nothing about which function runs when.
- Not done: breakpoints, hooks or logs of any function named in this document; the client state machine beyond state 0; the Lua-side session callbacks (where Lua screens are created and destroyed); the reader of the server flag `+0xd8`.
