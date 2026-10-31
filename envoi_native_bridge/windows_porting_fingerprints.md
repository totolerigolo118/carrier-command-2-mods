# Fingerprints for matching macOS functions to the Windows build (objective 4)

Companion of `session_lifecycle_analysis.md` (same source executable, same method: static reading only, nothing run).

**No Windows match is claimed here.** Everything below is a *test to run on the Windows executable*: a distinctive string, a call count, a size, a
call relationship. Mac sizes are x86-64 clang code and Windows x86 code will differ in size, so sizes are used only as loose hints. The Mac build embeds
the string `v1.5.17` (next to the feedback-form code of `process_application_event`); the Windows build is stated to be 1.5.18, so expect small differences.

Windows addresses quoted from the request (image base `0x00400000`): `c_logic_client` vtable `0x00D70358`, constructor `FUN_0083C8C0`, update `FUN_007716C0`, slot 0 `FUN_00770E70`;
`c_logic_server` vtable `0x00D34BC4`, constructor `FUN_00835B50`, update `FUN_0077EE10`, slot 0 `FUN_00772FD0`, slot 2 `FUN_0077EEA0`; others `FUN_00834CD0`, `FUN_00835580`,
`FUN_00835A10`, `FUN_00831750`.

## 1. Quick tests to run first (cheapest, most distinctive)

| # | Search in the Windows executable | Expected, if the structure is the same | Mac reference |
|---|---|---|---|
| 1 | cross-references to the string `abort_load_game` | one hit in the big command dispatcher, one in the server-start function | `process_application_event` `0x100433f4a`, `c_logic_server::begin` `0x1003211e4` |
| 2 | cross-references to `logic_assets_created` | one hit in the client tick, one in the command dispatcher | `c_logic_client::tick` `0x1002f7a7a`, `process_application_event` `0x100435c49` |
| 3 | cross-references to `c_logic_server: loaded game: ` and `c_logic_server: loading saved game... ` | the server-start function (`FUN_00772FD0` if slot 0 is `begin`) | `c_logic_server::begin` |
| 4 | the first three pointers of the vtable at `0x00D34BC4` | `begin`, `loop`, `end` (in that order) | vtable `0x1029cddb8` |
| 5 | callers of the server constructor `FUN_00835B50` | a tiny wrapper (new + constructor + smart-pointer reset), itself called by exactly 2 big functions | `reset_server` `0x10043b338`, 78 bytes, 2 callers |

## 2. Per function

### `process_application_event(mm_string const&)` — probable `FUN_00831750`
Mac `0x100433f4a`, 9,998 bytes, **one caller** (`c_application::on_update`, once per frame, call site `0x10042f4e9`). It is a chain of `c_command_parser::match(string)`
tests, one per event. Strings found in it (all are plain C strings; the exact set is the fingerprint):
`quit_game`, `abort_load_game`, `quit_to_menu`, `force_network_error`, `forced disconnect`, `load_game %u`, `save_game %u %s`, `save_game %u`, `slot_%u`,
`%H:%M:%S %d/%m/%Y`, `new_game_campaign`, `new_game_custom`, `host_game`, `host_game_campaign`, `host_load_game %u`, `join_game_steam_id %s %u %s`, `join_game_token %s %u`,
`request_server_meta_steam_id %s`, `request_server_meta_ip %s`, `request_server_meta_token %s`, `show_message_box %u`, `open_feedback_website`, `copy_to_clipboard %s`, `paste_clipboard`,
`regenerate_host_token`, `host_kick_peer %u`, `host_ban_peer %u`, `character_return_to_bridge %u`, `character_return_to_bridge`, `chat %s`, `chat_team %s`, `refresh_server_list`,
`logic_assets_created`, `scripts/pause_menu.lua`, `reload_asset %u %s`, `enabled_mods_modified`, `skip_splash_sequence`, `restart_server`, `set_peer_muted %u %b`.
Call-count fingerprint of its four session callees (direct calls): `quit_logic_to_menu` ×3, `load_saved_game` ×2, `host_game` ×4, `join_game` ×2.
The request says `FUN_00831750` handles `quit_to_menu`, `load_game`, `new_game_campaign`: all three are in this list.

### `destroy_current_screen_state()` — the teardown function
Mac `0x10043a82c`, 726 bytes, **5 direct callers**: `quit_logic_to_menu`, `load_saved_game`, `host_game`, `join_game`, `on_destroy`.
Shape: compares an integer member with 1 then with 0; in the "1" branch: a thread-object `join()` on the client, a flag test, a second `join()` on the server, then three
smart-pointer resets in the order client → server → HUD, then an audio-manager `clear()` and `clear_temp_mods()`; in the "0" branch: splash-sequence destroy, one `join()`, resets of
message-client manager, menu logic and HUD. Three `join()` calls in total, and no meaningful string literal (the only literal passed on is the argument of `set_host_connect_token`, which is an empty string).
A function with exactly five callers and three calls to the same tiny `join` helper is a strong candidate.

### `reset_server()` and `reset_logic()`
`reset_server` `0x10043b338`, 78 bytes: allocate, construct `c_logic_server`, reset the owning smart pointer (destroying the old server). Callers: `load_saved_game`, `host_game` only.
`reset_logic` `0x10043b260`, 216 bytes: allocate and construct `c_logic_client`, reset its smart pointer, allocate and construct a HUD screen and create it from a string. Callers: `load_saved_game`, `host_game`, `join_game`.
So the server constructor has **two callers up the chain** and the client constructor **three**: `join_game` is the only session function that creates a client without a server.

### The session functions
| Function | Mac address | Size | Direct calls worth matching |
|---|---|---|---|
| `quit_logic_to_menu` | `0x100438f22` | 350 | `destroy_current_screen_state`, mod-mode set, `reload_assets`, menu-logic constructor + reset, local server/client message managers, local link, thread start, splash `create` |
| `load_saved_game` | `0x100439080` | 886 | `destroy_current_screen_state`, `reload_assets`, `reset_logic`, `reset_server`, network managers, `c_logic_server::create`, `c_logic_client::create` |
| `host_game` | `0x100439a4c` | 1510 | same as `load_saved_game`, plus tutorial-data reads |
| `join_game` | `0x10043a032` | 586 | `destroy_current_screen_state`, `reset_logic`, `c_network_util::get_hostname_port_from_address`, client message manager, `c_logic_client::create`, `set_host_connect_token`; **no** `reset_server`, **no** `c_logic_server::create` |
Address order on the Mac (same translation unit): `process_application_event` `0x433f4a` … `quit_logic_to_menu` `0x438f22`, `load_saved_game`, `host_game`, `join_game`, `reload_asset`,
`destroy_current_screen_state`, `reset_logic`, `reset_server`, then `c_logic_client::create`. Do not rely on address order alone: the Windows functions you listed between
`FUN_00831750` and `FUN_00835B50` span 0xD40 bytes, far less than the Mac span of these functions, so only some of them are session functions.

### `c_logic_server` — vtable, `begin`, `loop`, `end`
- The first three virtual slots are `begin`, `loop`, `end` (data read from the file). The base class `mm_thread_object` has the same three slots; the thread body is a shared function that calls slot 0 once, slot 1 in a loop until a stop flag, then slot 2.
- **`FUN_0077EE10` ("update") is probably `loop()`, not `tick()`** (INFERRED): on the Mac `loop()` is 150 bytes, sits right before `end()` and contains exactly one game call (`tick()`), plus two time reads (and possibly a sleep stub). `FUN_0077EE10` is `0x90` = 144 bytes before `FUN_0077EEA0` (slot 2). The real `tick()` should then be its main callee.
- `begin` (Mac `0x1003211e4`, 2,268 bytes) fingerprints: profiler thread name string `Server`; log strings `c_logic_server: loading saved game... `, `c_logic_server: server world seed: `, `c_logic_server: failed to load game: `, `c_logic_server: loaded game: `, `, quitting to menu...`; event string `abort_load_game`; a sleep with the constant `1500000` (`0x16e360`, microseconds on the Mac; expect `1500` if the Windows sleep takes milliseconds) before that event; a call to `load_game` with the integer argument `4`; a second branch calling `generate`; then creation of a task processor, a weather simulation (with its own thread), an ocean-currents simulation, two `update_simulation` calls; a flag stored under the object lock just before returning.
- `end` (Mac `0x100321b56`, 196 bytes) call sequence, in order: peer manager destroy; three thread joins (weather, ocean, ocean currents); tile container destroy; scene-region container destroy; vehicle container destroy; missile container destroy; tile-definition container destroy; object-definition container destroy; profiler thread end. No strings.
- `load_game` (Mac `0x100327436`, 3,572 bytes) strings: `saved_games/`, `save.xml`, `c_logic_server: reading save file...`, `c_logic_server: save file read`, `c_logic_server: failed to read save file`, `c_logic_server: parsing scene data...`, `c_logic_server: parsed scene data`, `c_logic_server: failed to parse scene data`, `c_logic_server: proceding with game` (sic). `post_load_saved_game` (`0x10032a122`): `c_logic_server: post-loading saved game...`, `c_logic_server: finished post-loading saved game`.
- Serialization / initialisation operations by name: `parse_xml`, `parse_saved_game`, `post_load_saved_game`, `generate(e_scenario_type)`, `initialise_world_magnitude_data`, `spawn_team_vehicles`, `create_team_logistics`.

### `c_logic_client` — vtable, `begin`, `tick`
- Slots 0-2 are `begin` (`0x1002e5c1a`, 1,572 bytes), `loop` (`0x1002e623e`, 120 bytes), `end` (`0x1002e62b6`, 532 bytes). `begin` calls `begin_game_state(0)` first (`0x1002e5c46`).
- `begin` strings: `Logic` (profiler thread name), `meshes/spaceship/spaceship/mask_box.mesh`, `textures/icons/icons_index.atlas`, `placeholder`. Test: `FUN_00770E70` (slot 0) should reference them.
- `begin_game_state(e_game_state)` (`0x1002e6f68`, 308 bytes): switch with 6 cases (values 0-5); the case for `loading` sets the loading text `loading`.
- `tick()` (`0x1002f74ce`, 10,794 bytes) is the function that pushes the application event `logic_assets_created`.
- The distance between slot 0 and the update function does not match (Mac `begin`→`loop` is 0x624 bytes, Windows `FUN_00770E70`→`FUN_007716C0` is 0x850): inconclusive, so no claim about `FUN_007716C0`.

## 3. What this cannot tell you

- Sizes differ between compilers; use strings and call counts first.
- A hit on a string proves a reference, not the function's identity: two functions may share a string (the Mac has `skip_splash_sequence` both in the dispatcher and in the menu logic).
- Lock/unlock helpers and `operator new`/`delete` are the same few imports and stubs everywhere; do not use them to identify anything.
- Nothing in this file has been checked against the Windows executable.
