# How the 2x lift / crane / deck taxi patch for Carrier Command 2 works

> **Honest note from me:** I'm not a programmer. I described what I wanted to an AI assistant (Claude, by Anthropic). It did the reverse engineering and wrote the tools, and I tested everything in game. The AI wrote this file to explain how it works.

## Short version

The lift, crane and deck taxi speeds are **hard-coded numbers** inside `carrier_command.exe`, not settings in the game's XML or Lua files. The patch finds the 31 instructions that read those numbers and points each one at a number **twice as big**. It's applied to a **copy** of the exe, and the Steam file is never touched.

## Where the speeds live

The carrier's update code reads small floating-point constants stored in the exe's read-only data section, with SSE instructions such as:

```
movss xmm2, dword ptr [0xdb76c8]    ; 2.5  = deck taxi max speed
addss xmm0, dword ptr [0xdb71d0]    ; 0.05 = deck taxi acceleration per tick
```

(Addresses are from the Windows build 1.5.18 of June 2026. The game runs 30 ticks per second.)

## What the patch changes

| Setting | Original value | New value | Instructions changed |
|---|---|---|---|
| Deck taxi max speed | 2.5 | 5.0 | 7 |
| Deck taxi acceleration (per tick) | 0.05 | 0.1 | 7 |
| Lift platform step (per tick) | ±0.025 | ±0.05 | 2 |
| Crane horizontal step | ±1/6 | ±1/3 | 4 |
| Crane vertical step | ±1/30 | ±1/15 | 8 |
| Crane rotation step | ±0.04 | ±0.08 | 2 |
| Lift/crane share of the energy budget (inferred meaning) | 0.4 | 0.8 | 1 |
| **Total** | | | **31 instructions + 1 new value = 32 changes** |

## How it's done without breaking anything else

- **The shared constants themselves are never edited.** A value like 2.5 or 0.05 is also used by unrelated code. Instead, each of the 31 instructions gets its address operand **redirected** to another constant that already exists in the exe with the doubled value (for example, an existing 5.0).
- Only one doubled value didn't exist anywhere (−1/15). It's written into unused padding of the exe header, and the crane instructions point there.
- Every changed operand already has an entry in the exe's relocation table, so the patch stays correct even when Windows loads the exe at a different address.
- The patch checks every byte before changing it. If the exe is not the exact expected version (SHA-256), or if any site doesn't contain the expected bytes, it refuses and changes nothing. It can be undone exactly.

## Faster taxi back to the lift after landing (separate patch)

After a plane lands, the carrier pushes it back along rails on the deck. Each tick, the game advances it by `speed / (path length × 30)`, where 30 is the number of ticks per second. Making that one instruction read **15** instead of 30 doubles the speed (1 change).

## How it's applied

A small Python script works on a **copy** of `carrier_command.exe`:
1. It checks the SHA-256 of the original.
2. It checks the expected bytes at every site.
3. It writes the changes, then re-reads them.

The patched copy is launched directly, next to the Steam exe. Steam's own file is never modified (Steam would overwrite it on the next update anyway). The `capstone` disassembler was used to find and double-check every site.

**Game updates:** after a Steam update, the code moves around. The sites were found again by matching the surrounding instructions (here everything had moved by +0x110 bytes), and each change was re-verified on the new build.

## Results (single player, rough numbers)

- **Lift/crane/taxi x2, 4 planes returning:** 9:58 → 8:03 in total, and deck → hangar went from 1:27 to 0:51 per plane. Only one run of each, so take this as an order of magnitude.
- **Return taxi x2:** deck → hangar from 0:55 to 0:33 per plane. This was measured together with other changes.

## Caveats

- Tested in **single player only**. Multiplayer is untested.
- This patches the exe of a commercial game: private use, no exe is shared, only the description of the changes. Not affiliated with the developer.
- A game update can move the code again. The patch then refuses to apply until it's updated.
