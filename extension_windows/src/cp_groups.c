/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * Module table. Read this before filling a site array:
 *
 *  - A site = { image VA, length, original bytes, kind, tunable / target / hook } (see cp_patch.h).
 *    Addresses are image VAs for base 0x00400000, original bytes are the bytes of the .exe file
 *    (absolute operands included: the patch layer rebases them when the image is moved by ASLR).
 *  - Kinds: abs_float (redirect a float read to a tunable), imm (raw bytes), jump (move a rel32
 *    branch), hook (XMM-safe callback, see cp_hook.h).
 *  - NOTHING below is a Windows game address: every array is empty and marked TODO(tower step N).
 *    The MAC-ONLY blocks describe the Mac build (x86-64, RIP-relative) for orientation only.
 *  - To enable a group the tower fills `sites`, sets n_sites with a sizeof division, and checks
 *    every byte against the disassembly. Keep the group switch OFF in the ini until it is proven.
 *
 * The MAC-ONLY blocks are written by tools/mac_table_to_comments.py from
 * partage/cc2_reference.txt (part 10); do not edit them by hand.
 */
#include "cp_groups.h"

#include <string.h>

/* ============================================================================================
 * energy_lift_crane_taxi   (Mac module ascenseur_x2)            plan step 3
 *
 * Expected on Windows (from part 10): 34 sites on the Mac = 1 IMM + 33 RIP.
 *   1  imm       energy share of the elevator/crane system, an immediate 0.4 -> 0.8
 *                (kind imm with .tunable = CP_T_ENERGY_SHARE, .off = offset of the 4 immediate bytes)
 *   3  abs_float platform step per tick: CP_T_PLATFORM_STEP x2 (min / div), CP_T_PLATFORM_STEP_NEG x1 (max)
 *   4  abs_float crane horizontal: CP_T_CRANE_H x2, CP_T_CRANE_H_NEG x2
 *  10  abs_float crane vertical: CP_T_CRANE_V x5, CP_T_CRANE_V_NEG x5
 *   2  abs_float crane rotation: CP_T_CRANE_ROT x1, CP_T_CRANE_ROT_NEG x1
 *   7  abs_float deck taxi acceleration CP_T_TAXI_ACCEL (addss)
 *   7  abs_float deck taxi speed cap CP_T_TAXI_CAP (movss)
 * The count can differ on Windows: the Microsoft compiler may build -x with an xorps mask (then only
 * the positive read exists: redirect it and drop the *_NEG site) and inlines differently.
 * Do NOT touch: take-off run (addss 0.5), arrival thresholds 0.1 / 0.01, the divps by (1/6, 1/30).
 * Fingerprints to search: passation_windows/PASSATION_windows.md section 6.
 * DONE (tower step 3, 26/10/2026): SITES_ENERGY is filled below (31 sites, generated and re-read with a
 * disassembler by tour/outils/generer_groupe_energie.py). NEVER TRIED IN THE GAME YET; the switch stays off in the ini.
 * ======================================================================================== */
/* BEGIN MAC-ONLY ascenseur_x2
 * MAC-ONLY (module ascenseur_x2, build_mac, x86-64): 34 sites in part 10 (1 IMM, 33 RIP).
 * These bytes are documentation of the Mac encoding. They are NOT data for Windows: a 32-bit
 * build has other addresses and other encodings. RIP = SSE read of a float constant, IMM = raw
 * bytes / branch, CAVE = code added to the Mac build (no original bytes), DATA = table entry.
 *
 * 0x10019f0ad IMM  movl $0x3ecccccd, 0x118(%r15) ## imm = 0x3ECCCCCD
 *     before: 41c78718010000cdcccc3e
 * 0x10019455a RIP  maxss 0x26d5502(%rip), %xmm1 ## 0x102869a64
 *     before: f30f5f0d02556d02
 * 0x100194562 RIP  minss 0x26d540e(%rip), %xmm1 ## 0x102869978
 *     before: f30f5d0d0e546d02
 * 0x100194583 RIP  divss 0x26d53ed(%rip), %xmm3 ## 0x102869978
 *     before: f30f5e1ded536d02
 * 0x1001ae8bc RIP  movss 0x26bb210(%rip), %xmm7 ## 0x102869ad4
 *     before: f30f103d10b26b02
 * 0x1001aea04 RIP  movss 0x26bb0c8(%rip), %xmm7 ## 0x102869ad4
 *     before: f30f103dc8b06b02
 * 0x1001ae8c8 RIP  movss 0x26bae8c(%rip), %xmm2 ## 0x10286975c
 *     before: f30f10158cae6b02
 * 0x1001aea10 RIP  movss 0x26bad44(%rip), %xmm3 ## 0x10286975c
 *     before: f30f101d44ad6b02
 * 0x1001ae8d4 RIP  maxss 0x26bb0fc(%rip), %xmm6 ## 0x1028699d8
 *     before: f30f5f35fcb06b02
 * 0x1001ae968 RIP  maxss 0x26bb068(%rip), %xmm3 ## 0x1028699d8
 *     before: f30f5f1d68b06b02
 * 0x1001aea1c RIP  maxss 0x26bafb4(%rip), %xmm6 ## 0x1028699d8
 *     before: f30f5f35b4af6b02
 * 0x1001aeab8 RIP  maxss 0x26baf18(%rip), %xmm3 ## 0x1028699d8
 *     before: f30f5f1d18af6b02
 * 0x1001aeba7 RIP  maxss 0x26bae29(%rip), %xmm3 ## 0x1028699d8
 *     before: f30f5f1d29ae6b02
 * 0x1001ae8dc RIP  minss 0x26bb0f0(%rip), %xmm6 ## 0x1028699d4
 *     before: f30f5d35f0b06b02
 * 0x1001ae970 RIP  movss 0x26bb05c(%rip), %xmm1 ## 0x1028699d4
 *     before: f30f100d5cb06b02
 * 0x1001aea24 RIP  minss 0x26bafa8(%rip), %xmm6 ## 0x1028699d4
 *     before: f30f5d35a8af6b02
 * 0x1001aeac0 RIP  movss 0x26baf0c(%rip), %xmm1 ## 0x1028699d4
 *     before: f30f100d0caf6b02
 * 0x1001aebaf RIP  movss 0x26bae1d(%rip), %xmm1 ## 0x1028699d4
 *     before: f30f100d1dae6b02
 * 0x1001aeb2b RIP  maxss 0x26baed1(%rip), %xmm1 ## 0x102869a04
 *     before: f30f5f0dd1ae6b02
 * 0x1001aeb33 RIP  movss 0x26bac95(%rip), %xmm3 ## 0x1028697d0
 *     before: f30f101d95ac6b02
 * 0x1001ad6f9 RIP  addss 0x26bc0a3(%rip), %xmm4 ## 0x1028697a4
 *     before: f30f5825a3c06b02
 * 0x1001adf35 RIP  addss 0x26bb867(%rip), %xmm4 ## 0x1028697a4
 *     before: f30f582567b86b02
 * 0x1001ae02a RIP  addss 0x26bb772(%rip), %xmm4 ## 0x1028697a4
 *     before: f30f582572b76b02
 * 0x1001ae104 RIP  addss 0x26bb698(%rip), %xmm4 ## 0x1028697a4
 *     before: f30f582598b66b02
 * 0x1001ae2c1 RIP  addss 0x26bb4db(%rip), %xmm3 ## 0x1028697a4
 *     before: f30f581ddbb46b02
 * 0x1001ae6e0 RIP  addss 0x26bb0bc(%rip), %xmm4 ## 0x1028697a4
 *     before: f30f5825bcb06b02
 * 0x1001b010f RIP  addss 0x26b968d(%rip), %xmm4 ## 0x1028697a4
 *     before: f30f58258d966b02
 * 0x1001ad701 RIP  movss 0x26bc0b3(%rip), %xmm2 ## 0x1028697bc
 *     before: f30f1015b3c06b02
 * 0x1001adf41 RIP  movss 0x26bb873(%rip), %xmm2 ## 0x1028697bc
 *     before: f30f101573b86b02
 * 0x1001ae036 RIP  movss 0x26bb77e(%rip), %xmm2 ## 0x1028697bc
 *     before: f30f10157eb76b02
 * 0x1001ae110 RIP  movss 0x26bb6a4(%rip), %xmm2 ## 0x1028697bc
 *     before: f30f1015a4b66b02
 * 0x1001ae2cd RIP  movss 0x26bb4e7(%rip), %xmm4 ## 0x1028697bc
 *     before: f30f1025e7b46b02
 * 0x1001ae6e8 RIP  movss 0x26bb0cc(%rip), %xmm2 ## 0x1028697bc
 *     before: f30f1015ccb06b02
 * 0x1001b0117 RIP  movss 0x26b969d(%rip), %xmm2 ## 0x1028697bc
 *     before: f30f10159d966b02
 */ /* END MAC-ONLY ascenseur_x2 */

/* BEGIN WINDOWS SITES energy_lift_crane_taxi
 * Written by tour/outils/generer_groupe_energie.py from carrier_command.exe 1.5.18 (sha256 1C9A01C3...341026):
 * every site was re-read with a disassembler (mnemonic, absolute operand, stock value of the constant).
 * Do not edit by hand: rerun the script. 31 sites (the Mac module has 34: the Microsoft compiler loads
 * 0.025 once into a register, so the platform needs 2 sites instead of 3, and the vertical crane has 8 instead of 10).
 * NOT patched on purpose: 0x006fb3d8 (movss xmm2, [2.5]) = starting speed of a taxi leg, min(2.5, remaining). */
static const cp_site SITES_ENERGY[] = {
    /* energie : 5e ecriture de la fonction, part ascenseur / grue presumee (a confirmer par le Mac, Q3), mov [edi+8], 0,4: mov dword ptr [edi + 8], 0x3ecccccd */
    { .addr = 0x006ea09e, .len = 7, .kind = CP_SITE_IMM, .tunable = CP_T_ENERGY_SHARE, .off = 3,
      .expected = CP_BYTES(0xc7, 0x47, 0x08, 0xcd, 0xcc, 0xcc, 0x3e) },
    /* plateforme : pas +0,025 (charge xmm3, sert au minss et au divss): movss xmm3, dword ptr [0xdb71b0], constante 0x00db71b0 = 0.0250000004 */
    CP_ABS_FLOAT(0x00705c10, 8, 4, CP_T_PLATFORM_STEP, CP_BYTES(0xf3, 0x0f, 0x10, 0x1d, 0xb0, 0x71, 0xdb, 0x00)),
    /* plateforme : pas -0,025 (borne basse): maxss xmm1, dword ptr [0xdb7be0], constante 0x00db7be0 = -0.0250000004 */
    CP_ABS_FLOAT(0x00705c3a, 8, 4, CP_T_PLATFORM_STEP_NEG, CP_BYTES(0xf3, 0x0f, 0x5f, 0x0d, 0xe0, 0x7b, 0xdb, 0x00)),
    /* grue horizontale +1/6, bloc A: movss xmm2, dword ptr [0xdb7224], constante 0x00db7224 = 0.166666672 */
    CP_ABS_FLOAT(0x00700f22, 8, 4, CP_T_CRANE_H, CP_BYTES(0xf3, 0x0f, 0x10, 0x15, 0x24, 0x72, 0xdb, 0x00)),
    /* grue horizontale -1/6, bloc A: movss xmm1, dword ptr [0xdb7c14], constante 0x00db7c14 = -0.166666672 */
    CP_ABS_FLOAT(0x00700f2d, 8, 4, CP_T_CRANE_H_NEG, CP_BYTES(0xf3, 0x0f, 0x10, 0x0d, 0x14, 0x7c, 0xdb, 0x00)),
    /* grue verticale -1/30, bloc A: movss xmm1, dword ptr [0xdb7be4], constante 0x00db7be4 = -0.0333333351 */
    CP_ABS_FLOAT(0x00700f7e, 8, 4, CP_T_CRANE_V_NEG, CP_BYTES(0xf3, 0x0f, 0x10, 0x0d, 0xe4, 0x7b, 0xdb, 0x00)),
    /* grue verticale +1/30, bloc A: movss xmm2, dword ptr [0xdb71bc], constante 0x00db71bc = 0.0333333351 */
    CP_ABS_FLOAT(0x00700f96, 8, 4, CP_T_CRANE_V, CP_BYTES(0xf3, 0x0f, 0x10, 0x15, 0xbc, 0x71, 0xdb, 0x00)),
    /* grue horizontale +1/6, bloc B: movss xmm2, dword ptr [0xdb7224], constante 0x00db7224 = 0.166666672 */
    CP_ABS_FLOAT(0x00701031, 8, 4, CP_T_CRANE_H, CP_BYTES(0xf3, 0x0f, 0x10, 0x15, 0x24, 0x72, 0xdb, 0x00)),
    /* grue horizontale -1/6, bloc B: movss xmm1, dword ptr [0xdb7c14], constante 0x00db7c14 = -0.166666672 */
    CP_ABS_FLOAT(0x0070103c, 8, 4, CP_T_CRANE_H_NEG, CP_BYTES(0xf3, 0x0f, 0x10, 0x0d, 0x14, 0x7c, 0xdb, 0x00)),
    /* grue verticale -1/30, bloc B: movss xmm1, dword ptr [0xdb7be4], constante 0x00db7be4 = -0.0333333351 */
    CP_ABS_FLOAT(0x0070107f, 8, 4, CP_T_CRANE_V_NEG, CP_BYTES(0xf3, 0x0f, 0x10, 0x0d, 0xe4, 0x7b, 0xdb, 0x00)),
    /* grue verticale +1/30, bloc B: movss xmm2, dword ptr [0xdb71bc], constante 0x00db71bc = 0.0333333351 */
    CP_ABS_FLOAT(0x007010a2, 8, 4, CP_T_CRANE_V, CP_BYTES(0xf3, 0x0f, 0x10, 0x15, 0xbc, 0x71, 0xdb, 0x00)),
    /* grue verticale +1/30, bloc C (hauteur 12): movss xmm2, dword ptr [0xdb71bc], constante 0x00db71bc = 0.0333333351 */
    CP_ABS_FLOAT(0x00701120, 8, 4, CP_T_CRANE_V, CP_BYTES(0xf3, 0x0f, 0x10, 0x15, 0xbc, 0x71, 0xdb, 0x00)),
    /* grue verticale -1/30, bloc C (hauteur 12): movss xmm1, dword ptr [0xdb7be4], constante 0x00db7be4 = -0.0333333351 */
    CP_ABS_FLOAT(0x00701128, 8, 4, CP_T_CRANE_V_NEG, CP_BYTES(0xf3, 0x0f, 0x10, 0x0d, 0xe4, 0x7b, 0xdb, 0x00)),
    /* grue verticale +1/30, bloc D (hauteur 11): movss xmm2, dword ptr [0xdb71bc], constante 0x00db71bc = 0.0333333351 */
    CP_ABS_FLOAT(0x007011b2, 8, 4, CP_T_CRANE_V, CP_BYTES(0xf3, 0x0f, 0x10, 0x15, 0xbc, 0x71, 0xdb, 0x00)),
    /* grue verticale -1/30, bloc D (hauteur 11): movss xmm1, dword ptr [0xdb7be4], constante 0x00db7be4 = -0.0333333351 */
    CP_ABS_FLOAT(0x007011ba, 8, 4, CP_T_CRANE_V_NEG, CP_BYTES(0xf3, 0x0f, 0x10, 0x0d, 0xe4, 0x7b, 0xdb, 0x00)),
    /* grue rotation +0,04: movss xmm2, dword ptr [0xdb71c4], constante 0x00db71c4 = 0.0399999991 */
    CP_ABS_FLOAT(0x00701215, 8, 4, CP_T_CRANE_ROT, CP_BYTES(0xf3, 0x0f, 0x10, 0x15, 0xc4, 0x71, 0xdb, 0x00)),
    /* grue rotation -0,04: movss xmm1, dword ptr [0xdb7bec], constante 0x00db7bec = -0.0399999991 */
    CP_ABS_FLOAT(0x00701221, 8, 4, CP_T_CRANE_ROT_NEG, CP_BYTES(0xf3, 0x0f, 0x10, 0x0d, 0xec, 0x7b, 0xdb, 0x00)),
    /* roulage : acceleration 0,05, bloc 1: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 */
    CP_ABS_FLOAT(0x006f9841, 8, 4, CP_T_TAXI_ACCEL, CP_BYTES(0xf3, 0x0f, 0x58, 0x05, 0xd0, 0x71, 0xdb, 0x00)),
    /* roulage : acceleration 0,05, bloc 2: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 */
    CP_ABS_FLOAT(0x006fb2ca, 8, 4, CP_T_TAXI_ACCEL, CP_BYTES(0xf3, 0x0f, 0x58, 0x05, 0xd0, 0x71, 0xdb, 0x00)),
    /* roulage : acceleration 0,05, bloc 3: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 */
    CP_ABS_FLOAT(0x006fcba6, 8, 4, CP_T_TAXI_ACCEL, CP_BYTES(0xf3, 0x0f, 0x58, 0x05, 0xd0, 0x71, 0xdb, 0x00)),
    /* roulage : acceleration 0,05, bloc 4: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 */
    CP_ABS_FLOAT(0x006fce4a, 8, 4, CP_T_TAXI_ACCEL, CP_BYTES(0xf3, 0x0f, 0x58, 0x05, 0xd0, 0x71, 0xdb, 0x00)),
    /* roulage : acceleration 0,05, bloc 5: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 */
    CP_ABS_FLOAT(0x006fd8d1, 8, 4, CP_T_TAXI_ACCEL, CP_BYTES(0xf3, 0x0f, 0x58, 0x05, 0xd0, 0x71, 0xdb, 0x00)),
    /* roulage : acceleration 0,05 chargee dans xmm2 avant l'aiguillage (bloc 6): movss xmm2, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 */
    CP_ABS_FLOAT(0x006fddb1, 8, 4, CP_T_TAXI_ACCEL, CP_BYTES(0xf3, 0x0f, 0x10, 0x15, 0xd0, 0x71, 0xdb, 0x00)),
    /* roulage : acceleration 0,05, bloc 7: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 */
    CP_ABS_FLOAT(0x006ffaeb, 8, 4, CP_T_TAXI_ACCEL, CP_BYTES(0xf3, 0x0f, 0x58, 0x05, 0xd0, 0x71, 0xdb, 0x00)),
    /* roulage : plafond 2,5, bloc 1: movss xmm2, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 */
    CP_ABS_FLOAT(0x006f980d, 8, 4, CP_T_TAXI_CAP, CP_BYTES(0xf3, 0x0f, 0x10, 0x15, 0xc8, 0x76, 0xdb, 0x00)),
    /* roulage : plafond 2,5, bloc 2: movss xmm1, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 */
    CP_ABS_FLOAT(0x006fb2e5, 8, 4, CP_T_TAXI_CAP, CP_BYTES(0xf3, 0x0f, 0x10, 0x0d, 0xc8, 0x76, 0xdb, 0x00)),
    /* roulage : plafond 2,5, bloc 3: movss xmm1, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 */
    CP_ABS_FLOAT(0x006fcbae, 8, 4, CP_T_TAXI_CAP, CP_BYTES(0xf3, 0x0f, 0x10, 0x0d, 0xc8, 0x76, 0xdb, 0x00)),
    /* roulage : plafond 2,5, bloc 4: movss xmm3, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 */
    CP_ABS_FLOAT(0x006fce52, 8, 4, CP_T_TAXI_CAP, CP_BYTES(0xf3, 0x0f, 0x10, 0x1d, 0xc8, 0x76, 0xdb, 0x00)),
    /* roulage : plafond 2,5, bloc 5: movss xmm3, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 */
    CP_ABS_FLOAT(0x006fd8ec, 8, 4, CP_T_TAXI_CAP, CP_BYTES(0xf3, 0x0f, 0x10, 0x1d, 0xc8, 0x76, 0xdb, 0x00)),
    /* roulage : plafond 2,5 chargee dans xmm5 avant l'aiguillage (bloc 6, sert au bloc 7): movss xmm5, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 */
    CP_ABS_FLOAT(0x006fddb9, 8, 4, CP_T_TAXI_CAP, CP_BYTES(0xf3, 0x0f, 0x10, 0x2d, 0xc8, 0x76, 0xdb, 0x00)),
    /* roulage : plafond 2,5, bloc 7: movss xmm5, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 */
    CP_ABS_FLOAT(0x006ffa64, 8, 4, CP_T_TAXI_CAP, CP_BYTES(0xf3, 0x0f, 0x10, 0x2d, 0xc8, 0x76, 0xdb, 0x00)),
};
#define N_SITES_ENERGY ((int)(sizeof(SITES_ENERGY) / sizeof(SITES_ENERGY[0])))
/* END WINDOWS SITES energy_lift_crane_taxi */

/* ============================================================================================
 * helicopters   (Mac modules helicos_approche_x2 + helicos_pres_ascenseur)    plan step 4
 *
 * Expected on Windows: 5 sites on the Mac (1 + 4) = 3 RIP + 1 CAVE + 1 IMM.
 *   3 abs_float  CP_T_HELI_AIM (50 -> 100), CP_T_HELI_AIM_MAX (120 -> 48), CP_T_HELI_GEAR (20 -> 70)
 *   1 hook       CP_HOOK_HELI_HEIGHT replaces the Mac cave + its jmp (2 Mac sites): the hook subtracts
 *                CP_T_HELI_HEIGHT_SHIFT (23.5) from the xmm that holds the target height; the displaced
 *                instruction is the game's own `maxss [-2.0]`, which keeps its absolute operand
 *                (list its offset in .abs_ops so it is rebased). Set cp_hooks.heli_height_xmm.
 * So about 4 sites on Windows (3 abs_float + 1 hook).
 * TODO(tower step 4): fill SITES_HELI.
 * ======================================================================================== */
/* BEGIN MAC-ONLY helicos_approche_x2
 * MAC-ONLY (module helicos_approche_x2, build_mac, x86-64): 1 sites in part 10 (1 RIP).
 * These bytes are documentation of the Mac encoding. They are NOT data for Windows: a 32-bit
 * build has other addresses and other encodings. RIP = SSE read of a float constant, IMM = raw
 * bytes / branch, CAVE = code added to the Mac build (no original bytes), DATA = table entry.
 *
 * 0x1001ad3ef RIP  movss 0x26bc4b5(%rip), %xmm0 ## 0x1028698ac
 *     before: f30f1005b5c46b02
 */ /* END MAC-ONLY helicos_approche_x2 */
/* BEGIN MAC-ONLY helicos_pres_ascenseur
 * MAC-ONLY (module helicos_pres_ascenseur, build_mac, x86-64): 4 sites in part 10 (1 CAVE, 1 IMM, 2 RIP).
 * These bytes are documentation of the Mac encoding. They are NOT data for Windows: a 32-bit
 * build has other addresses and other encodings. RIP = SSE read of a float constant, IMM = raw
 * bytes / branch, CAVE = code added to the Mac build (no original bytes), DATA = table entry.
 *
 * 0x1001ad3fc RIP  movss 0x26bc3b4(%rip), %xmm1 ## 0x1028697b8
 *     before: f30f100db4c36b02
 * 0x1001b1066 RIP  movss 0x26b87ce(%rip), %xmm0 ## 0x10286983c
 *     before: f30f1005ce876b02
 * 0x100061b80 CAVE added code, 28 bytes
 *     before: (none: added code)
 * 0x1001ad57a IMM  maxss 0x26bc2ce(%rip), %xmm1 ## 0x102869850
 *     before: f30f5f0dcec26b02
 */ /* END MAC-ONLY helicos_pres_ascenseur */

/* ============================================================================================
 * return_taxi   (Mac module pont_retour_x2)                     plan step 5
 *
 * Expected on Windows: 3 sites (3 RIP on the Mac): the shared read of 30.0 (mulss) in the three
 * return legs (runway states 5, 6, 7), each redirected to CP_T_TAXI_RETURN_TICKS (15.0).
 *   3 abs_float  CP_T_TAXI_RETURN_TICKS
 * TODO(tower step 5): fill SITES_RETURN_TAXI.
 * ======================================================================================== */
/* BEGIN MAC-ONLY pont_retour_x2
 * MAC-ONLY (module pont_retour_x2, build_mac, x86-64): 3 sites in part 10 (3 RIP).
 * These bytes are documentation of the Mac encoding. They are NOT data for Windows: a 32-bit
 * build has other addresses and other encodings. RIP = SSE read of a float constant, IMM = raw
 * bytes / branch, CAVE = code added to the Mac build (no original bytes), DATA = table entry.
 *
 * 0x1001b0824 RIP  mulss 0x26b906c(%rip), %xmm1 ## 0x102869898
 *     before: f30f590d6c906b02
 * 0x1001ae07c RIP  mulss 0x26bb814(%rip), %xmm1 ## 0x102869898
 *     before: f30f590d14b86b02
 * 0x1001b0831 RIP  mulss 0x26b905f(%rip), %xmm1 ## 0x102869898
 *     before: f30f590d5f906b02
 */ /* END MAC-ONLY pont_retour_x2 */

/* ============================================================================================
 * landing_circuit   (Mac module atterrissage)                   plan step 5
 *
 * Expected on Windows: 10 sites on the Mac = 4 IMM + 6 RIP.
 *   3 jump       the rel32 branches that skip the runway-grant block, redirected to the grant block
 *                (.target = image VA of the grant block; E9 / 0F 8x forms only, see check_site)
 *   1 imm        addss -> subss (opcode byte 0x58 -> 0x5c): the target stays 1800 m ahead
 *   4 abs_float  addps reads of a vector of FOUR floats (16-byte aligned operand required):
 *                CP_T_CIRCLE_FWD_VEC x2, CP_T_CIRCLE_BACK_VEC x2
 *   2 abs_float  scalar reads 600 -> -1800: CP_T_CIRCLE_CZ x2
 * Setting A of the sheet = the 3 jump sites alone (wide runway slot, no circle). A split into two
 * groups is a TODO if the simulation says setting B is slower.
 * TODO(tower step 5): fill SITES_LANDING.
 * ======================================================================================== */
/* BEGIN MAC-ONLY atterrissage
 * MAC-ONLY (module atterrissage, build_mac, x86-64): 10 sites in part 10 (4 IMM, 6 RIP).
 * These bytes are documentation of the Mac encoding. They are NOT data for Windows: a 32-bit
 * build has other addresses and other encodings. RIP = SSE read of a float constant, IMM = raw
 * bytes / branch, CAVE = code added to the Mac build (no original bytes), DATA = table entry.
 *
 * 0x1001af900 IMM  jbe 0x1001afb05
 *     before: 0f86ff010000
 * 0x1001af85b IMM  jbe 0x1001afb05
 *     before: 0f86a4020000
 * 0x1001af867 IMM  jmp 0x1001afb05
 *     before: e999020000
 * 0x1001af785 RIP  addps 0x26bc134(%rip), %xmm1 ## 0x10286b8c0
 *     before: 0f580d34c16b02
 * 0x1001af7d4 RIP  addps 0x26bc125(%rip), %xmm4 ## 0x10286b900
 *     before: 0f582525c16b02
 * 0x1001afa98 RIP  addps 0x26bbe21(%rip), %xmm1 ## 0x10286b8c0
 *     before: 0f580d21be6b02
 * 0x1001afae7 RIP  addps 0x26bbe12(%rip), %xmm4 ## 0x10286b900
 *     before: 0f582512be6b02
 * 0x1001af870 RIP  movss 0x26b9f5c(%rip), %xmm1 ## 0x1028697d4
 *     before: f30f100d5c9f6b02
 * 0x1001afaf2 RIP  movss 0x26b9cda(%rip), %xmm1 ## 0x1028697d4
 *     before: f30f100dda9c6b02
 * 0x1001af87b IMM  addss %xmm1, %xmm0
 *     before: f30f58c1
 */ /* END MAC-ONLY atterrissage */

/* ============================================================================================
 * speed_modes   (Mac module vitesse_escadrille)                 plan step 6
 *
 * Expected on Windows: 3 sites on the Mac = 1 CAVE + 1 IMM hook + 1 DATA entry. On Windows:
 *   1-2 hook     CP_HOOK_SPEED_FLOOR at the max(48.0)/max(72.0) floor of the aircraft control code
 *                (look for 48.0 then 144.0 then 72.0 then 144.0 around a test "type 10"). The hook
 *                raises the xmm that holds the target speed to cp_speed_floor(); the displaced game
 *                instruction then applies the stock floor and the cap as before.
 *   0 data       the Mac replaced the Lua `dofile` entry; here the Lua function is registered by
 *                the plugin (cc2x.speed.mode, see cc2_patchs.c and lua/cc2_vitesse_shim.lua).
 * Vehicle layout hints from the public SDK (to verify, not used by this code): team number at +0x108,
 * team object at +0x1a8 (its team_is_ai byte at +0x19), definition at +0x84.
 * Alternative for a first try: write CONTROL_SPEED each server tick (the sheet expects it to be overwritten).
 * TODO(tower step 6): fill SITES_SPEED and the body of the hook in cp_hooks.c.
 * ======================================================================================== */
/* BEGIN MAC-ONLY vitesse_escadrille
 * MAC-ONLY (module vitesse_escadrille, build_mac, x86-64): 3 sites in part 10 (1 CAVE, 1 DATA, 1 IMM).
 * These bytes are documentation of the Mac encoding. They are NOT data for Windows: a 32-bit
 * build has other addresses and other encodings. RIP = SSE read of a float constant, IMM = raw
 * bytes / branch, CAVE = code added to the Mac build (no original bytes), DATA = table entry.
 *
 * 0x10005d000 CAVE added code, 671 bytes
 *     before: (none: added code)
 * 0x1001c2b4b IMM  movss (%rbx), %xmm0
 *     before: f30f10030f28c8f30f5f0d966f6a02f30f5d0dca6f6a02f3410f118dc80200004183bd900000
 *     000a7519f30f5f05b36f6a02f30f5d05a76f6a02f3410f1185c8020000
 * 0x1029dd310 DATA DATA (base_funcs[] entry of the Lua base library: { "dofile", luaB_dofile } -> { "cc2_vitesse", vit_lua }; 8-byte unslid pointers)
 *     before: 0e979702010000008caa830201000000
 */ /* END MAC-ONLY vitesse_escadrille */

/* ============================================================================================
 * crane_cancel   (Mac module grue_annulation)                   plan step 7
 *
 * Expected on Windows: 3 sites on the Mac = 1 CAVE + 2 IMM hooks. On Windows:
 *   2 hook       CP_HOOK_CRANE_UNDOCK (aircraft already held by the crane when undock is requested)
 *                CP_HOOK_CRANE_END    (end of the crane in launch mode)
 *   + the C logic of outil/generateurs/grue_annulation.c, rewritten (SysV -> thiscall / cdecl, 32-bit
 *     offsets found through the saved-state parsers). A stuck crane blocks every launch and landing.
 * Only after steps 3 to 6 are validated.
 * TODO(tower step 7): fill SITES_CRANE_CANCEL and write the callbacks.
 * ======================================================================================== */
/* BEGIN MAC-ONLY grue_annulation
 * MAC-ONLY (module grue_annulation, build_mac, x86-64): 3 sites in part 10 (1 CAVE, 2 IMM).
 * These bytes are documentation of the Mac encoding. They are NOT data for Windows: a 32-bit
 * build has other addresses and other encodings. RIP = SSE read of a float constant, IMM = raw
 * bytes / branch, CAVE = code added to the Mac build (no original bytes), DATA = table entry.
 *
 * 0x100061200 CAVE added code, 932 bytes
 *     before: (none: added code)
 * 0x1001a8c01 IMM  cmpl $0x7, 0x220(%r14)
 *     before: 4183be20020000077503895f28
 * 0x1001ad9ad IMM  cmpl $0x0, 0x18(%r14)
 *     before: 41837e1800
 */ /* END MAC-ONLY grue_annulation */

/* ============================================================================================
 * cctv   (Mac module cctv_net)                                  plan step 8
 *
 * Expected on Windows: 5 sites on the Mac = 1 CAVE + 4 IMM (4 jumps into one cave). On Windows:
 *   4 hook       CP_HOOK_CCTV_A..D: image size by screen type, UI camera size, scissor rectangle,
 *                scale reset (cosmetic gain, only if the modder asks).
 * TODO(tower step 8): fill SITES_CCTV and port outil/generateurs/cctv_net.s.
 * ======================================================================================== */
/* BEGIN MAC-ONLY cctv_net
 * MAC-ONLY (module cctv_net, build_mac, x86-64): 5 sites in part 10 (1 CAVE, 4 IMM).
 * These bytes are documentation of the Mac encoding. They are NOT data for Windows: a 32-bit
 * build has other addresses and other encodings. RIP = SSE read of a float constant, IMM = raw
 * bytes / branch, CAVE = code added to the Mac build (no original bytes), DATA = table entry.
 *
 * 0x100061800 CAVE added code, 439 bytes
 *     before: (none: added code)
 * 0x1000ad74f IMM  movslq 0x60(%rax,%rcx), %rax
 *     before: 486344086041b98000000041b8800000004883f8057716488d0d033d8002448b0c81488d0d10
 *     3d8002448b0481
 * 0x10021ce70 IMM  movl 0x20(%r14), %ecx
 *     before: 418b4e200f57c0f3480f2ac1418b4e24f3480f2ad1
 * 0x10015e662 IMM  movss 0x270b0e2(%rip), %xmm0 ## 0x10286974c
 *     before: f30f1005e2b07002f30f104f14f30f58c8660f3a0ac909f30f2cc9f30f584710660f3a0ac009
 *     f30f2cd00f57c0660f3a0a470c09f30f2cf00f57c0660f3a0a470809f30f2cf8
 * 0x10021cf13 IMM  movl $0xb44, %edi ## imm = 0xB44
 *     before: bf440b0000
 */ /* END MAC-ONLY cctv_net */

/* ============================================================================================
 * recorder   (Mac module ecriture_releve)                       plan step 8
 *
 * Expected on Windows: 3 sites on the Mac = 1 CAVE + 2 IMM (two loads of the stdout stream in print()).
 * On Windows print() is not redirected by the SDK; two options: 2 hook sites (CP_HOOK_RECORDER_A/B)
 * or, simpler, adapt library_custom_5.lua to call cc2x.log when it exists (no site at all).
 * TODO(tower step 8): decide, then fill SITES_RECORDER or leave empty.
 * ======================================================================================== */
/* BEGIN MAC-ONLY ecriture_releve
 * MAC-ONLY (module ecriture_releve, build_mac, x86-64): 3 sites in part 10 (1 CAVE, 2 IMM).
 * These bytes are documentation of the Mac encoding. They are NOT data for Windows: a 32-bit
 * build has other addresses and other encodings. RIP = SSE read of a float constant, IMM = raw
 * bytes / branch, CAVE = code added to the Mac build (no original bytes), DATA = table entry.
 *
 * 0x100061a00 CAVE added code, 165 bytes
 *     before: (none: added code)
 * 0x10283aed0 IMM  movq 0x163119(%rip), %r12 ## 0x10299dff0
 *     before: 4c8b2519311600
 * 0x10283af78 IMM  movq 0x163071(%rip), %rbx ## 0x10299dff0
 *     before: 488b1d71301600
 */ /* END MAC-ONLY ecriture_releve */

/* ------------------------------------------------------------------------------------------ */

const cp_group CP_GROUPS[CP_G_COUNT] = {
    [CP_G_ENERGY] = { "energy_lift_crane_taxi", "energy, elevator, crane and deck taxi x2", "ascenseur_x2", 3, 34, SITES_ENERGY,
                      N_SITES_ENERGY },
    [CP_G_HELI] = { "helicopters", "helicopter approach x2 and touch-down near the elevator",
                    "helicos_approche_x2 + helicos_pres_ascenseur", 4, 5, NULL, 0 },
    [CP_G_RETURN_TAXI] = { "return_taxi", "deck taxi x2 after landing", "pont_retour_x2", 5, 3, NULL, 0 },
    [CP_G_LANDING] = { "landing_circuit", "wide runway slot and circular holding pattern", "atterrissage", 5, 10, NULL, 0 },
    [CP_G_SPEED] = { "speed_modes", "squadron speed modes ECO / NORMAL / FLANK", "vitesse_escadrille", 6, 3, NULL, 0 },
    [CP_G_CRANE_CANCEL] = { "crane_cancel", "cancel a launch already taken by the hangar crane", "grue_annulation", 7, 3, NULL, 0 },
    [CP_G_CCTV] = { "cctv", "CCTV screen image 512 x 512", "cctv_net", 8, 5, NULL, 0 },
    [CP_G_RECORDER] = { "recorder", "Lua print() written to a file", "ecriture_releve", 8, 3, NULL, 0 },
};

int cp_group_by_key(const char *key) {
    if (!key) return -1;
    for (int i = 0; i < CP_G_COUNT; ++i)
        if (strcmp(CP_GROUPS[i].ini_key, key) == 0) return i;
    return -1;
}
