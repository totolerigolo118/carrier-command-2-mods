/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "cp_speed.h"

#include <math.h>
#include <string.h>

void cp_speed_init(cp_speed *s) {
    memset((void *)s, 0, sizeof(*s));
}

int64_t cp_speed_arg(int is_number, double value) {
    if (!is_number || !isfinite(value) || value != floor(value) || fabs(value) > 9e15) return 0;
    return (int64_t)value;
}

int cp_speed_call(cp_speed *s, const cp_speed_io *io, int nargs, int64_t team, int64_t mode_arg) {
    int mode = 0;
    if (team < 0 || team >= CP_SPEED_TEAMS) return 0;
    if (!s->file_read) {
        s->file_read = 1;
        s->file_mode = (uint8_t)((io && io->load) ? io->load(io->user) : 0);
        if (s->file_mode > CP_SPEED_MODE_MAX) s->file_mode = 0;
    }
    if (nargs >= 2) {
        if (mode_arg >= 1 && mode_arg <= CP_SPEED_MODE_MAX) {
            s->mode[team] = (uint8_t)mode_arg;
            if (mode_arg != s->file_mode) {
                if (io && io->save) io->save(io->user, (int)mode_arg);
                s->file_mode = (uint8_t)mode_arg;
            }
        }
    } else if (s->mode[team] == 0) {
        s->mode[team] = s->file_mode;
    }
    mode = s->mode[team];
    return mode;
}

float cp_speed_floor(const cp_tunables *t, int mode, int is_manta) {
    switch (mode) {
    case 2: return cp_tun_get(t, is_manta ? CP_T_SPEED_NORMAL_MANTA : CP_T_SPEED_NORMAL_WING);
    case 3: return cp_tun_get(t, CP_T_SPEED_FLANK);
    default: return is_manta ? CP_SPEED_STOCK_MANTA : CP_SPEED_STOCK_WING;
    }
}
