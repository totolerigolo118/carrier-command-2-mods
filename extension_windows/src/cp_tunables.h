/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * Our own float constants.
 *
 * The game's float constants are SHARED (the same 0.05 is read by code we do not want to touch), so
 * a patch never edits them: it redirects the 32-bit absolute operand of one instruction to a slot of
 * this table instead (see cp_patch.h, kind CP_SITE_ABS_FLOAT).
 *
 * Every slot is 16 bytes and the table is 16-byte aligned: some game reads are `addps` on a vector of
 * four floats, which faults on a misaligned operand. A scalar uses lane 0 only.
 *
 * Defaults are the values validated on the Mac build (the "doubled" values of part 10 of
 * partage/cc2_reference.txt). `stock` is what the game holds at the redirected constant; the patch
 * layer reads the original constant and refuses the site if it does not hold the stock value.
 */
#ifndef CP_TUNABLES_H
#define CP_TUNABLES_H

#include "cp_types.h"

typedef enum cp_tunable_id {
    CP_T_NONE = 0,

    /* group energy_lift_crane_taxi (Mac: ascenseur_x2) */
    CP_T_ENERGY_SHARE,      /* elevator/crane share of the energy, an immediate (not redirected) */
    CP_T_PLATFORM_STEP,     /* elevator platform step per tick, m */
    CP_T_PLATFORM_STEP_NEG, /* derived: -CP_T_PLATFORM_STEP (a separate game constant on the Mac) */
    CP_T_CRANE_H,           /* crane horizontal step */
    CP_T_CRANE_H_NEG,
    CP_T_CRANE_V,           /* crane vertical step */
    CP_T_CRANE_V_NEG,
    CP_T_CRANE_ROT,         /* crane rotation step */
    CP_T_CRANE_ROT_NEG,
    CP_T_TAXI_ACCEL,        /* deck taxi acceleration per tick */
    CP_T_TAXI_CAP,          /* deck taxi speed cap, m/s */

    /* group helicopters (Mac: helicos_approche_x2 + helicos_pres_ascenseur) */
    CP_T_HELI_AIM,          /* aim distance ahead of a landing helicopter, m */
    CP_T_HELI_AIM_MAX,      /* aim point at most runway_start + this, m */
    CP_T_HELI_GEAR,         /* gear-down threshold, m */
    CP_T_HELI_HEIGHT_SHIFT, /* subtracted from the target height before the floor (used by a hook, no game constant) */

    /* group return_taxi (Mac: pont_retour_x2) */
    CP_T_TAXI_RETURN_TICKS, /* ticks per second in t += v / (L x ticks) on the three return legs */

    /* group landing_circuit (Mac: atterrissage) */
    CP_T_CIRCLE_CX,         /* centre x of the holding circle, ship coordinates, m (only used to derive the vectors) */
    CP_T_CIRCLE_CZ,         /* centre z of the circle: also the scalar the game compares z with (2 reads) */
    CP_T_CIRCLE_FWD_VEC,    /* derived: (-cx, -cz, 0, 0), read by addps */
    CP_T_CIRCLE_BACK_VEC,   /* derived: ( cx,  cz, 0, 0), read by addps */

    /* group speed_modes (Mac: vitesse_escadrille); read by a hook, no game constant */
    CP_T_SPEED_NORMAL_WING, /* NORMAL floor for aircraft other than the Manta, m/s */
    CP_T_SPEED_NORMAL_MANTA,/* NORMAL floor for the Manta, m/s */
    CP_T_SPEED_FLANK,       /* FLANK floor (= the cap, full throttle), m/s */

    CP_T_COUNT
} cp_tunable_id;

typedef struct cp_tunable_info {
    const char *ini_key;    /* key in [tunables] of cc2_patchs.ini; NULL for derived slots */
    const char *group;      /* ini key of the group that uses it */
    float stock[4];         /* value held by the game constant that gets redirected */
    float def[4];           /* default (Mac value) */
    uint8_t has_stock;      /* 0 = no game constant behind it (immediate / hook-only) */
    uint8_t derived;        /* 1 = computed by cp_tun_derive(), not settable from the ini */
} cp_tunable_info;

typedef struct cp_tunables {
    CP_ALIGN16 float v[CP_T_COUNT][4];  /* slot i = 16 bytes; first member, so the struct is 16-aligned */
    cp_addr base;                       /* address of v[0] in the target address space (0 = not bound) */
} cp_tunables;

/* Fill every slot with its default and compute the derived ones. */
void cp_tun_init(cp_tunables *t);
/* Recompute the derived slots from the settable ones (call after changing a value). */
void cp_tun_derive(cp_tunables *t);
/* Tell the table where it lives in the target address space (Windows: the DLL data address).
 * Returns 0 and leaves it unbound if the address is not 16-byte aligned. */
int cp_tun_bind(cp_tunables *t, cp_addr base);
/* The table is bound, and both the real memory and the bound address are 16-byte aligned. */
int cp_tun_check_alignment(const cp_tunables *t);
/* Address of slot id in the target address space; 0 if unbound or id out of range. */
cp_addr cp_tun_addr(const cp_tunables *t, int id);

const cp_tunable_info *cp_tun_info(int id);       /* NULL for CP_T_NONE / out of range */
float cp_tun_get(const cp_tunables *t, int id);   /* lane 0 */
/* Set a settable tunable by its ini key. Returns 1 if set, 0 if the key is unknown or derived,
 * -1 if the value is not finite or absurd (|v| > 1e6). Calls cp_tun_derive on success. */
int cp_tun_set_by_key(cp_tunables *t, const char *key, double value);

#endif
