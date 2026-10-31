/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "cp_tunables.h"

#include <math.h>
#include <string.h>

#define SC(x) { (x), 0.0f, 0.0f, 0.0f }

/* Order = cp_tunable_id. Stock and default values: part 10 of partage/cc2_reference.txt and the table
 * of section 6 of passation_windows/PASSATION_windows.md (the float bits are checked by the host tests). */
static const cp_tunable_info INFO[CP_T_COUNT] = {
    [CP_T_NONE] = { 0 },
    [CP_T_ENERGY_SHARE] = { "energy_share", "energy_lift_crane_taxi", SC(0.4f), SC(0.8f), 0, 0 },
    [CP_T_PLATFORM_STEP] = { "platform_step", "energy_lift_crane_taxi", SC(0.025f), SC(0.05f), 1, 0 },
    [CP_T_PLATFORM_STEP_NEG] = { NULL, "energy_lift_crane_taxi", SC(-0.025f), SC(-0.05f), 1, 1 },
    [CP_T_CRANE_H] = { "crane_horizontal", "energy_lift_crane_taxi", SC(1.0f / 6.0f), SC(1.0f / 3.0f), 1, 0 },
    [CP_T_CRANE_H_NEG] = { NULL, "energy_lift_crane_taxi", SC(-1.0f / 6.0f), SC(-1.0f / 3.0f), 1, 1 },
    [CP_T_CRANE_V] = { "crane_vertical", "energy_lift_crane_taxi", SC(1.0f / 30.0f), SC(1.0f / 15.0f), 1, 0 },
    [CP_T_CRANE_V_NEG] = { NULL, "energy_lift_crane_taxi", SC(-1.0f / 30.0f), SC(-1.0f / 15.0f), 1, 1 },
    [CP_T_CRANE_ROT] = { "crane_rotation", "energy_lift_crane_taxi", SC(0.04f), SC(0.08f), 1, 0 },
    [CP_T_CRANE_ROT_NEG] = { NULL, "energy_lift_crane_taxi", SC(-0.04f), SC(-0.08f), 1, 1 },
    [CP_T_TAXI_ACCEL] = { "taxi_accel", "energy_lift_crane_taxi", SC(0.05f), SC(0.1f), 1, 0 },
    [CP_T_TAXI_CAP] = { "taxi_cap", "energy_lift_crane_taxi", SC(2.5f), SC(5.0f), 1, 0 },

    [CP_T_HELI_AIM] = { "heli_aim_distance", "helicopters", SC(50.0f), SC(100.0f), 1, 0 },
    [CP_T_HELI_AIM_MAX] = { "heli_aim_max", "helicopters", SC(120.0f), SC(48.0f), 1, 0 },
    [CP_T_HELI_GEAR] = { "heli_gear_distance", "helicopters", SC(20.0f), SC(70.0f), 1, 0 },
    [CP_T_HELI_HEIGHT_SHIFT] = { "heli_height_shift", "helicopters", SC(0.0f), SC(23.5f), 0, 0 },

    [CP_T_TAXI_RETURN_TICKS] = { "taxi_return_ticks", "return_taxi", SC(30.0f), SC(15.0f), 1, 0 },

    [CP_T_CIRCLE_CX] = { "circle_center_x", "landing_circuit", SC(-1000.0f), SC(-1000.0f), 0, 0 },
    [CP_T_CIRCLE_CZ] = { "circle_center_z", "landing_circuit", SC(600.0f), SC(-1800.0f), 1, 0 },
    [CP_T_CIRCLE_FWD_VEC] = { NULL, "landing_circuit", { 1000.0f, -600.0f, 0.0f, 0.0f },
                              { 1000.0f, 1800.0f, 0.0f, 0.0f }, 1, 1 },
    [CP_T_CIRCLE_BACK_VEC] = { NULL, "landing_circuit", { -1000.0f, 600.0f, 0.0f, 0.0f },
                               { -1000.0f, -1800.0f, 0.0f, 0.0f }, 1, 1 },

    [CP_T_SPEED_NORMAL_WING] = { "speed_normal_wing", "speed_modes", SC(48.0f), SC(61.0f), 0, 0 },
    [CP_T_SPEED_NORMAL_MANTA] = { "speed_normal_manta", "speed_modes", SC(72.0f), SC(91.0f), 0, 0 },
    [CP_T_SPEED_FLANK] = { "speed_flank", "speed_modes", SC(144.0f), SC(144.0f), 0, 0 },
};

const cp_tunable_info *cp_tun_info(int id) {
    return (id > CP_T_NONE && id < CP_T_COUNT) ? &INFO[id] : NULL;
}

void cp_tun_derive(cp_tunables *t) {
    static const struct { int neg, src; } NEG[] = {
        { CP_T_PLATFORM_STEP_NEG, CP_T_PLATFORM_STEP }, { CP_T_CRANE_H_NEG, CP_T_CRANE_H },
        { CP_T_CRANE_V_NEG, CP_T_CRANE_V },             { CP_T_CRANE_ROT_NEG, CP_T_CRANE_ROT },
    };
    for (size_t i = 0; i < sizeof(NEG) / sizeof(NEG[0]); ++i) {
        memset(t->v[NEG[i].neg], 0, sizeof(t->v[0]));
        t->v[NEG[i].neg][0] = -t->v[NEG[i].src][0];
    }
    float cx = t->v[CP_T_CIRCLE_CX][0], cz = t->v[CP_T_CIRCLE_CZ][0];
    memset(t->v[CP_T_CIRCLE_FWD_VEC], 0, sizeof(t->v[0]));
    memset(t->v[CP_T_CIRCLE_BACK_VEC], 0, sizeof(t->v[0]));
    t->v[CP_T_CIRCLE_FWD_VEC][0] = -cx;
    t->v[CP_T_CIRCLE_FWD_VEC][1] = -cz;
    t->v[CP_T_CIRCLE_BACK_VEC][0] = cx;
    t->v[CP_T_CIRCLE_BACK_VEC][1] = cz;
}

void cp_tun_init(cp_tunables *t) {
    cp_addr keep = t->base;
    memset(t->v, 0, sizeof(t->v));
    for (int id = 1; id < CP_T_COUNT; ++id)
        if (!INFO[id].derived) memcpy(t->v[id], INFO[id].def, sizeof(INFO[id].def));
    t->base = keep;
    cp_tun_derive(t);
}

int cp_tun_bind(cp_tunables *t, cp_addr base) {
    if (base & 15u) {
        t->base = 0;
        return 0;
    }
    t->base = base;
    return 1;
}

int cp_tun_check_alignment(const cp_tunables *t) {
    return t->base != 0 && (((uintptr_t)t->v) & 15u) == 0 && (t->base & 15u) == 0;
}

cp_addr cp_tun_addr(const cp_tunables *t, int id) {
    if (!t->base || id <= CP_T_NONE || id >= CP_T_COUNT) return 0;
    return t->base + 16u * (cp_addr)id;
}

float cp_tun_get(const cp_tunables *t, int id) {
    return (id > CP_T_NONE && id < CP_T_COUNT) ? t->v[id][0] : 0.0f;
}

int cp_tun_set_by_key(cp_tunables *t, const char *key, double value) {
    if (!key) return 0;
    for (int id = 1; id < CP_T_COUNT; ++id) {
        if (INFO[id].derived || !INFO[id].ini_key || strcmp(INFO[id].ini_key, key) != 0) continue;
        if (!isfinite(value) || fabs(value) > 1e6) return -1;
        t->v[id][0] = (float)value;
        cp_tun_derive(t);
        return 1;
    }
    return 0;
}
