/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * C callbacks of the mid-function hooks (kind CP_SITE_HOOK). A site names its callback by id.
 * The callbacks run inside the XMM-safe trampoline (cp_hook.h): they can read and change every
 * register through the cp_hook_ctx.
 */
#ifndef CP_HOOKS_H
#define CP_HOOKS_H

#include "cp_hook.h"
#include "cp_speed.h"
#include "cp_tunables.h"

typedef enum cp_hook_id {
    CP_HOOK_NONE = 0,
    CP_HOOK_HELI_HEIGHT,     /* helicopters: target height shifted before the floor */
    CP_HOOK_SPEED_FLOOR,     /* speed_modes: floor speed of the squadron */
    CP_HOOK_CRANE_UNDOCK,    /* crane_cancel: entry A (undock request on an aircraft the crane holds) */
    CP_HOOK_CRANE_END,       /* crane_cancel: entry B (end of the crane in launch mode) */
    CP_HOOK_CCTV_A,          /* cctv: image size by screen type */
    CP_HOOK_CCTV_B,          /* cctv: UI camera width / height */
    CP_HOOK_CCTV_C,          /* cctv: scissor rectangle */
    CP_HOOK_CCTV_D,          /* cctv: scale reset after the UI render */
    CP_HOOK_RECORDER_A,      /* recorder: print() output stream, before the arguments */
    CP_HOOK_RECORDER_B,      /* recorder: print() output stream, final newline / flush */
    CP_HOOK_COUNT
} cp_hook_id;

/* What the callbacks need: set once at load. */
typedef struct cp_hooks_cfg {
    const cp_tunables *tun;
    cp_speed *speed;
    /* helicopters: which xmm register holds the target height at the site. -1 = not known yet:
     * TODO(tower step 4) read it from the Windows disassembly; until then the callback does nothing. */
    int heli_height_xmm;
} cp_hooks_cfg;

extern cp_hooks_cfg cp_hooks;

/* Callback of a hook id, NULL if none. */
cp_hook_fn cp_hook_lookup(int id);

#endif
