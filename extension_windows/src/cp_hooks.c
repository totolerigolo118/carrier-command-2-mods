/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "cp_hooks.h"

cp_hooks_cfg cp_hooks = { 0, 0, -1 };

/* helicopters (Mac module helicos_pres_ascenseur, the 21-byte cave): the Mac cave did
 *   subss [23.5], xmm1 ; maxss [-2.0], xmm1 ; jmp back
 * Here the hook only does the subtraction; the displaced game instruction (the maxss) then runs
 * unchanged on the restored registers. Which xmm register holds the height on Windows is a
 * TODO(tower step 4): cp_hooks.heli_height_xmm. */
static void hook_heli_height(cp_hook_ctx *ctx, void *user) {
    (void)user;
    int r = cp_hooks.heli_height_xmm;
    if (r < 0 || r > 7 || !cp_hooks.tun) return;
    ctx->xmm[r][0] -= cp_tun_get(cp_hooks.tun, CP_T_HELI_HEIGHT_SHIFT);
}

/* Callbacks of the groups that are not ported yet: they do nothing, so a site table filled in by
 * mistake before the logic exists cannot change the game's behaviour.
 *  - speed_modes   TODO(tower step 6): read team / aircraft type from the registers named by the
 *                  tower, then raise the xmm that holds the target speed to
 *                  cp_speed_floor(tun, cp_hooks.speed->mode[team], is_manta)
 *  - crane_cancel  TODO(tower step 7): port outil/generateurs/grue_annulation.c (SysV, Mac offsets)
 *  - cctv          TODO(tower step 8): port outil/generateurs/cctv_net.s
 *  - recorder      TODO(tower step 8): or use cc2x.log from library_custom_5.lua instead */
static void hook_todo(cp_hook_ctx *ctx, void *user) {
    (void)ctx;
    (void)user;
}

cp_hook_fn cp_hook_lookup(int id) {
    switch (id) {
    case CP_HOOK_HELI_HEIGHT: return hook_heli_height;
    case CP_HOOK_SPEED_FLOOR:
    case CP_HOOK_CRANE_UNDOCK:
    case CP_HOOK_CRANE_END:
    case CP_HOOK_CCTV_A:
    case CP_HOOK_CCTV_B:
    case CP_HOOK_CCTV_C:
    case CP_HOOK_CCTV_D:
    case CP_HOOK_RECORDER_A:
    case CP_HOOK_RECORDER_B: return hook_todo;
    default: return NULL;
    }
}
