/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * Speed modes of the squadron (group speed_modes; Mac module vitesse_escadrille).
 *
 * Pure logic, same contract as the Mac function cc2_vitesse (checked in game on the Mac on 25/10):
 *   cc2_vitesse(team)        -> the mode of the team (0 = never chosen)
 *   cc2_vitesse(team, mode)  -> sets the mode (1 ECO, 2 NORMAL, 3 FLANK) and returns the team's mode
 *   - an argument that is not a number counts as 0 (so a missing team means team 0)
 *   - a team outside 0..15 answers 0 and changes nothing
 *   - mode outside 1..3 is ignored (the call then only reads)
 *   - a team without a mode adopts the LAST mode that was set (kept in a small file), on a read
 *   - the last mode is written to a file only when it changes
 */
#ifndef CP_SPEED_H
#define CP_SPEED_H

#include "cp_tunables.h"
#include "cp_types.h"

#define CP_SPEED_TEAMS 16
#define CP_SPEED_MODE_MAX 3

/* Stock floors of the game (ECO): Albatross / any aircraft 48 m/s, Manta 72 m/s. */
#define CP_SPEED_STOCK_WING 48.0f
#define CP_SPEED_STOCK_MANTA 72.0f

typedef struct cp_speed_io {
    int (*load)(void *user);            /* last mode kept in the file, 0 if none */
    void (*save)(void *user, int mode); /* write the file */
    void *user;
} cp_speed_io;

typedef struct cp_speed {
    volatile uint8_t mode[CP_SPEED_TEAMS];   /* read by the game thread (hook), written by the Lua thread */
    uint8_t file_read;
    uint8_t file_mode;
} cp_speed;

void cp_speed_init(cp_speed *s);

/* Decode a Lua argument the way lua_tointegerx does for a number: integral value or 0.
 * is_number = 0 (absent or not a number) gives 0. */
int64_t cp_speed_arg(int is_number, double value);

/* The Lua function. nargs = number of arguments of the call. Returns the value to push. */
int cp_speed_call(cp_speed *s, const cp_speed_io *io, int nargs, int64_t team, int64_t mode_arg);

/* Floor speed (m/s) the hook must enforce for an aircraft of a human team.
 * mode 0 or 1 = ECO = the game's own floor. */
float cp_speed_floor(const cp_tunables *t, int mode, int is_manta);

#endif
