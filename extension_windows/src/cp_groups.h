/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * The module table: one entry per group of patches, one on/off switch per group in the ini.
 * The site arrays are EMPTY until the tower (the Windows PC) has found the real addresses in
 * carrier_command.exe 1.5.18-win32: nothing in this repository knows a Windows game address.
 */
#ifndef CP_GROUPS_H
#define CP_GROUPS_H

#include "cp_patch.h"

typedef enum cp_group_id {
    CP_G_ENERGY = 0,       /* energy_lift_crane_taxi   (Mac: ascenseur_x2) */
    CP_G_HELI,             /* helicopters              (Mac: helicos_approche_x2 + helicos_pres_ascenseur) */
    CP_G_RETURN_TAXI,      /* return_taxi              (Mac: pont_retour_x2) */
    CP_G_LANDING,          /* landing_circuit          (Mac: atterrissage) */
    CP_G_SPEED,            /* speed_modes              (Mac: vitesse_escadrille) */
    CP_G_CRANE_CANCEL,     /* crane_cancel             (Mac: grue_annulation) */
    CP_G_CCTV,             /* cctv                     (Mac: cctv_net) */
    CP_G_RECORDER,         /* recorder                 (Mac: ecriture_releve) */
    CP_G_COUNT
} cp_group_id;

typedef struct cp_group {
    const char *ini_key;      /* key in [groups] of cc2_patchs.ini, also the name in the log */
    const char *name;         /* what it does */
    const char *mac_module;   /* Mac module(s), for the notes */
    int tower_step;           /* step of the plan (passation_windows/PASSATION_windows.md, section 5) */
    int mac_sites;            /* number of sites in part 10 of partage/cc2_reference.txt */
    const cp_site *sites;     /* NULL / 0 until the tower fills the table */
    int n_sites;
} cp_group;

extern const cp_group CP_GROUPS[CP_G_COUNT];

/* index of a group by its ini key, -1 if unknown */
int cp_group_by_key(const char *key);

#endif
