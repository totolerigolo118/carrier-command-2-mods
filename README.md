# Carrier Command 2 — mods, plugins and tools (made with an AI)

> **Honest note from me:** I'm not a programmer. I described what I wanted to an AI assistant (Claude, by Anthropic).
> It did the reverse engineering, wrote the code and almost all the documents, and I tested everything in game myself.
> I'm sharing it to help other modders and to show what can be done. Most documents are in **French**
> (`LISEZ-MOI.md` is the French version of this page); the C plugin sources are commented in English.

This is **not a ready-to-install mod**. It is the full working folder: plugin sources, Python tools, Lua scripts,
studies, procedures and measurements. Personal names and paths were replaced (`C:\Users\UTILISATEUR\…`, "le moddeur" =
me, "la tour" = my Windows PC, `[branche]`, `[session]`).

## What works (tested in game, single player unless noted)

| Result | Old exe 1.5.18 | New Steam exe (update of 28 Oct 2026) | Where |
|---|---|---|---|
| **Land a plane or a helicopter by hand, then it goes back to the hangar by itself**: plugin `cc2x_frein` v15 brakes the hand-landed aircraft and holds it (a helicopter is held on the deck, engine off); 5 s after you leave it or press R, it asks the carrier for the usual recall and sends the aircraft down the path the game uses for helicopters, and the game stores it in the hangar and refuels it (settings `recall_force`, `heli_recall`, `auto_recall` in `frein.ini`) | v12, planes only, recall ordered by hand: **3 out of 3** (31 Oct) | v14/v15: **Albatross, Manta, Razorbill and Petrel, 4 out of 4** back in the hangar by themselves and refuelled (2 Nov) | `tour/atterrissage_manuel/` (`JOURNAL_atterrissage.md`), `tour/essai_nouvel_exe/` |
| **Approach gates** in the aircraft HUD: 6 rectangles along the glide slope behind your carrier; the next one turns green, orange or red for axis, height and speed (Lua mod `aide_approche`, no SDK needed) | — | works (2 Nov) | `tour/aide_approche/` |
| **Copies of the red Hold button** near the helm, **synchronised** with the original (mod `cc2_hold_copies` + plugin `cc2x_hold` v2.1) | works: the three buttons move together | works | `tour/etude_bouton_hold/` (`PLUGIN_hold_v2.md`) |
| **Lift, crane and deck taxi ×2** (exe patch `ascenseur_x2`, explained in [`cc2_lift_crane_taxi_x2.md`](cc2_lift_crane_taxi_x2.md)) | 4 planes returning 9:58 → 8:03; deck → hangar 1:27 → 0:51 (one run each) | works (seen in game, not re-measured) | `tour/outils/patch_exe.py`, `tour/outils/modules_exe*/` |
| **Return taxi ×2** (`pont_retour_x2`) | deck → hangar 0:55 → 0:33 (measured together with other changes) | in the patched copy, not measured alone | same |
| **Time ×2** (`temps_x2`, a test mode: the whole simulation runs faster, SIM ×1.33 on screen) | works | works | same |
| **Faster landing pattern** (circle + wider runway slot) | 4 planes stored in 7:09, runway every 1:28, 0 missed approach (one run) | ported, **not tested** | `tour/etudes_circuit_atterrissage/` |
| **Fuel modes ECO** per aircraft (plugin `cc2x_modes` v3.1 + a Lua "SPEED" tab) | ECO ≈ 80 m/s, −21 to −22 % fuel per second; FLANK not satisfactory | loads, not measured | `tour/etudes_modes_carburant/` |
| **Map videos** of a game (Lua recorder + Python/ffmpeg renderer) | works | not tested | `tour/carte/` (example videos without game icons) |
| **Measurement screens** (game clock, landing log), English version available | used for all the measurements above | — | `tour/outils/mod_mesures.py`, `tour/etude_mesures_en/` |
| **Mac build** (another binary, 64-bit, with symbols) | lift ×2 3:50 → 2:15; helicopters 6:52 → 4:22 | — | `outil/patchs_cc2.py`, English notes in `partage/` and `partage_detail/` |

**Multiplayer: hosted, not yet played with a second player.** On 2 Nov I hosted a multiplayer game alone with a patched
copy *without* the time patch (`tour/essai_nouvel_exe/outils/lancer_multi_5.py`): the SDK and the three plugins loaded,
and the brake, the automatic return to the hangar and the Hold sync worked for my own plane (one run). Windows asks for
firewall access the first time a patched copy hosts a game. From reading the code only: the exe patches and the SDK act
on the host only (so the other players' aircraft probably get the same brake and return), and `temps_x2` speeds up the
game for everybody.

Check your exe (PowerShell): `Get-FileHash "…\Carrier Command 2\carrier_command.exe"`.
Old exe: `1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026` (no longer on Steam; no exe is shared here).
New exe: `461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A`.

## What you need

- Windows, Python 3 (3.12 used); `capstone` for some analyses; `Pillow` and `ffmpeg` for the videos.
- For the plugins: the **CC2X SDK 0.5.0** by Dioramawhois (<https://github.com/Dioramawhois/Carrier-Command-2-extender>,
  commit `7ab05c79357e0cdb5bfaa2866bd3a81a101a09da`) and **Zig 0.15.2** to compile. For the new Steam exe the SDK needs a
  second profile: our patch is `tour/etude_port_nouvel_exe/sdk/profil_nouvel_exe.diff` (independent review:
  `tour/revue_sdk_deux_profils/VERDICT.md`). **No DLL is provided**: you build them yourself.

## Install and remove

**Important:** the install scripts were written for my own PC. They check the exact SHA-256 of *my* compiled DLLs and
patched copies, and use my folders. On your PC they will refuse until you adapt the paths and fingerprints, or you do
the steps by hand. They never write anything they don't recognise, and never touch Steam's own exe.

Always with the game closed, on a throw-away game, after backing up the game folder's DLLs and `%APPDATA%\Carrier Command 2`:

1. Build `dinput8.dll` (SDK) and the plugins (`frein/construire.py`, `plugin/construire_hold.py`, `tour/etudes_modes_carburant/plugin/`).
2. Put `dinput8.dll` and `cc2x_frein.dll` next to the game exe; the Hold and modes plugins go in their mod's `content\cc2x\`
   folder. Settings: `%APPDATA%\Carrier Command 2\cc2x\*.ini` (start from the `*.ini.example` files).
3. Exe patches: make a **copy** of `carrier_command.exe` under a new name, patch the copy with `tour/outils/patch_exe.py`
   (it knows both exes and refuses any other), and launch the copy directly (Steam running). Steam's exe is never modified.
4. Reference procedures and their rollback: `tour/essai_nouvel_exe/` (new exe, `RETOURS_ARRIERE.md`),
   `tour/atterrissage_manuel/PROCEDURE_partie_v14_retour_auto.md` (automatic return),
   `tour/atterrissage_manuel/PROCEDURE_partie_v13_helicos.md` (helicopters),
   `tour/atterrissage_manuel/PROCEDURE_partie_v12.md` (old exe), `tour/etude_bouton_hold/LISEZ-MOI.md`.
5. Approach gates: copy `tour/aide_approche/mod/` as a mod folder and enable it (Lua only, works without the SDK).
   Delete its `library_custom_0.lua` first: it is an automatic take-off at the start of a new game, never tested.

**Remove everything:** delete `dinput8.dll` and the `cc2x_*.dll` files, remove our mods from `mods.xml`, delete the patched
copies. Steam's "Verify integrity of game files" restores Steam's own files.

## Risks

- 🔴 Native code runs inside the game (plugins, exe patches): crashes are possible. Use a throw-away game.
- 🔴 The SDK loads **any** DLL found in `content\cc2x\` of an enabled mod, Workshop mods included: only enable trusted mods
  while the SDK is installed.
- 🟡 `frein.ini.example` has `brake=1.0`, which crashed a plane once; the setting that worked is `brake=0.1`
  (see `PROCEDURE_partie_v12.md`). The take-over can't be undone, and the carrier must be slow.
- 🟡 With `auto_recall=1`, an aircraft you leave on the deck goes back to the hangar after 5 s (longer in rough sea: the
  countdown restarts while the aircraft slides). In multiplayer this probably applies to the other players' aircraft too
  (not tested): set `auto_recall=0` if it gets in their way (re-read in 3 s).
- 🟡 A Steam update replaces the exe: the patched copy then no longer matches and the plugins refuse an unknown build.
- 🟡 Loading old saves crashed (probably saves made with another mod): start new games.
- AI-written code, tested and reviewed, but **not audited**: use it at your own risk.

## Folder map

| Folder | Content |
|---|---|
| `tour/` | all the Windows work: `atterrissage_manuel/` (brake v12 → v15), `aide_approche/` (approach gates), `etude_bouton_hold/`, `essai_nouvel_exe/`, `outils/` (exe patcher, measurement mods, map recorder), `etudes_*` and `etude_*` (studies, e.g. `etude_vitesse_altitude/`), `carte/` (videos), `etude_port_nouvel_exe/` (porting to the new exe) |
| `passation_windows/` | hand-over from the Mac to Windows, including `JOURNAL_tour.md` (measurement log) |
| `outil/`, `fichiers/`, `tests/`, `etudes/` | the Mac patch workshop (`patchs_cc2.py`; `LISEZ-MOI.txt` is its own notice) |
| `partage/`, `partage_detail/` | English notes on the Mac build (method, patch tables, symbol index) |
| `doc/`, `revues/`, `revue_cloud/` | overview, glossary, independent reviews |

Each study tags its claims **LU** (read in a file), **MESURÉ** (measured), **INFÉRÉ** (inferred) or **RAPPORTÉ** (reported).

## Licence and credits

Everything here is under **GPL-3.0-or-later** (full text in `LICENSE`): reuse it, change it, share it. The plugins are
built on the CC2X SDK by **Dioramawhois** (GPL-3.0) — many thanks. *Carrier Command 2* is a game by **Geometa**; no game
file, exe, icon or font is included, and this project is not affiliated with the developer. Details: `CREDITS_ET_LICENCE.md`.
