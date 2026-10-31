/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * cc2_patchs.ini -> group switches and tunable overrides (pure: works on a memory buffer).
 *
 *   [groups]      one switch per group, default 0 (off)    energy_lift_crane_taxi = 1
 *   [tunables]    float overrides, default = Mac values    platform_step = 0.05
 *   [debug]       lua_speed_stub = 1   registers cc2x.speed.mode even if the speed_modes group is off
 */
#ifndef CP_CONFIG_H
#define CP_CONFIG_H

#include "cp_groups.h"
#include "cp_tunables.h"

typedef struct cp_config {
    uint8_t group_on[CP_G_COUNT];   /* all 0 by default */
    uint8_t lua_speed_stub;
    int n_overrides;                /* tunables changed by the ini */
} cp_config;

void cp_config_init(cp_config *c);

/* Parse an ini buffer into c and t. warn() gets one message per problem (unknown key / section,
 * bad value, malformed line); a problem never enables anything. Returns the number of warnings. */
int cp_config_parse(cp_config *c, cp_tunables *t, const char *buf, size_t len,
                    void (*warn)(void *user, const char *message), void *user);

#endif
