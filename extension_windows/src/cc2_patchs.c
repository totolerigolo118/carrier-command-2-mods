/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * CC2 patches: CC2X plugin (32-bit Windows DLL) that will carry our Carrier Command 2 patches.
 *
 * STATE: skeleton. The code is written and the host-side tests pass, but every group's site table is
 * still empty (the Windows addresses are to be found by the tower) and NOTHING has run inside the
 * game. With the default ini (all groups off) the plugin only checks the build, reads the ini and
 * logs one line per group.
 *
 * Install (development): cc2x_cc2_patchs.dll next to carrier_command.exe, settings in
 * <api->config_dir>\cc2_patchs.ini (see cc2_patchs.ini.example). Remove the DLL = original game.
 *
 * The SDK's own patch functions are not used: they cannot write raw bytes. Our writes go through
 * cp_patch.c, which verifies the original bytes of every site (so it also refuses sites another
 * plugin already patched) but does not know the SDK's own registry.
 */
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "cc2x.h"
#include "cp_config.h"
#include "cp_groups.h"
#include "cp_hooks.h"
#include "cp_patch.h"
#include "cp_pe.h"
#include "cp_platform.h"
#include "cp_speed.h"

#define WHO "cc2_patchs"

static const cc2x_api *g_api;
static cp_tunables g_tun;         /* 16-byte aligned (first member is aligned) */
static cp_config g_cfg;
static cp_session g_sess;
static cp_speed g_speed;
static char g_speed_file[300];

static void plog(int level, const char *fmt, ...) {
    char msg[400];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(msg, sizeof(msg), fmt, ap);
    va_end(ap);
    g_api->log(WHO, level, "%s", msg);
}

/* ---------------------------------------------------------------- cp_env callbacks */

static void env_log(void *user, int level, const char *msg) { (void)user; plog(level, "%s", msg); }
static cp_addr env_va(void *user, uint32_t image_va) { (void)user; return (cp_addr)g_api->va(image_va); }
static cp_addr env_hook_addr(void *user, int id) {
    (void)user;
    return (cp_addr)(uintptr_t)cp_hook_lookup(id);
}
static void warn_cb(void *user, const char *msg) { (void)user; plog(CC2X_LOG_WARN, "%s", msg); }

/* ---------------------------------------------------------------- Lua: speed-mode contract */

/* last speed mode, kept in a small file like on the Mac */
static int speed_load(void *user) {
    char c = 0;
    (void)user;
    if (!g_speed_file[0] || cp_plat_read_file(g_speed_file, &c, 1) < 1) return 0;
    return (c >= '1' && c <= '0' + CP_SPEED_MODE_MAX) ? c - '0' : 0;
}
static void speed_save(void *user, int mode) {
    char text[3] = { (char)('0' + mode), '\n', 0 };
    (void)user;
    if (g_speed_file[0]) cp_plat_write_file(g_speed_file, text, 2);
}
static const cp_speed_io g_speed_io = { speed_load, speed_save, NULL };

/* cc2x.speed.mode(team [, mode]): same contract as the Mac function cc2_vitesse.
 * Lua threads call this while the game thread may read g_speed.mode in a hook: single bytes only. */
static int lf_speed_mode(cc2x_lua *L) {
    int n = g_api->lua_gettop(L);
    double d = 0;
    int ok = g_api->lua_tonumber(L, 1, &d);
    int64_t team = cp_speed_arg(ok, d);
    d = 0;
    ok = n >= 2 && g_api->lua_tonumber(L, 2, &d);
    int64_t mode = cp_speed_arg(ok, d);
    g_api->lua_pushinteger(L, cp_speed_call(&g_speed, &g_speed_io, n, team, mode));
    return 1;
}

/* ---------------------------------------------------------------- entry point */

static void log_group(int g, const cp_result *r) {
    const cp_group *grp = &CP_GROUPS[g];
    switch (r->status) {
    case CP_GRP_APPLIED:
        plog(CC2X_LOG_INFO, "group %s: applied (%d sites)", grp->ini_key, r->n_sites);
        break;
    case CP_GRP_ALREADY:
        plog(CC2X_LOG_INFO, "group %s: already applied (%d sites), nothing written", grp->ini_key, r->n_sites);
        break;
    case CP_GRP_REFUSED:
        plog(CC2X_LOG_WARN, "group %s: refused: %s [plan step %d]", grp->ini_key, r->reason, grp->tower_step);
        break;
    case CP_GRP_ROLLED_BACK:
        plog(CC2X_LOG_ERROR, "group %s: refused after a failed write, rolled back: %s", grp->ini_key, r->reason);
        break;
    default:
        plog(CC2X_LOG_ERROR, "group %s: BROKEN: %s", grp->ini_key, r->reason);
        break;
    }
}

CC2X_EXPORT int cc2x_plugin_load(const cc2x_api *api) {
    /* config_dir and va() need API 2; we use nothing of API 3 */
    if (!api || api->api_version < 2 || api->size < offsetof(cc2x_api, config_dir) + sizeof(api->config_dir) ||
        !api->va || !api->log)
        return 0;
    g_api = api;
    plog(CC2X_LOG_INFO, "cc2_patchs skeleton starting (SDK %s, game build %s)", api->sdk_version ? api->sdk_version : "?",
         api->game_build ? api->game_build : "?");

    /* BUILD GATE: known build string AND PE timestamp AND SizeOfImage, read from the main module */
    uint8_t header[4096];
    cp_pe_info pe;
    char reason[200];
    if (!cp_plat_read(NULL, (cp_addr)api->module_base, header, sizeof(header))) {
        plog(CC2X_LOG_WARN, "build gate: cannot read the PE header of the game; staying inactive, the game is unchanged");
        return 0;
    }
    cp_pe_status ps = cp_pe_parse(header, sizeof(header), &pe);
    if (ps != CP_PE_OK) {
        plog(CC2X_LOG_WARN, "build gate: PE header unreadable (%s); staying inactive, the game is unchanged",
             cp_pe_status_text(ps));
        return 0;
    }
    if (!cp_build_gate(api->game_build, &pe, reason, sizeof(reason))) {
        plog(CC2X_LOG_WARN, "build gate: %s; staying inactive, the game is unchanged", reason);
        return 0;
    }
    plog(CC2X_LOG_INFO, "build gate: %s, PE timestamp 0x%08x, SizeOfImage 0x%08x: known build", api->game_build,
         (unsigned)pe.timestamp, (unsigned)pe.size_of_image);

    /* tunables: 16-byte aligned table, Mac values */
    cp_tun_init(&g_tun);
    if (!cp_tun_bind(&g_tun, (cp_addr)(uintptr_t)g_tun.v) || !cp_tun_check_alignment(&g_tun)) {
        plog(CC2X_LOG_ERROR, "tunable table is not 16-byte aligned; staying inactive");
        return 0;
    }

    /* ini */
    cp_config_init(&g_cfg);
    const char *dir = (api->config_dir && api->config_dir[0]) ? api->config_dir : NULL;
    if (dir) {
        char path[400];
        static char buf[16384];
        snprintf(path, sizeof(path), "%s\\cc2_patchs.ini", dir);
        snprintf(g_speed_file, sizeof(g_speed_file), "%s\\cc2_vitesse_mode.txt", dir);
        long n = cp_plat_read_file(path, buf, sizeof(buf) - 1);
        if (n < 0) {
            plog(CC2X_LOG_INFO, "no %s: every group stays off", path);
        } else {
            if (n >= (long)sizeof(buf) - 1)
                plog(CC2X_LOG_WARN, "%s is larger than %d bytes: only the beginning is read", path, (int)sizeof(buf) - 1);
            int w = cp_config_parse(&g_cfg, &g_tun, buf, (size_t)n, warn_cb, NULL);
            plog(CC2X_LOG_INFO, "read %s (%ld bytes, %d warning(s), %d tunable(s) overridden)", path, n, w,
                 g_cfg.n_overrides);
        }
    } else {
        plog(CC2X_LOG_WARN, "no config folder from the SDK: every group stays off");
    }

    /* patch layer */
    cp_env env = { 0 };
    env.read = cp_plat_read;
    env.write = cp_plat_write;
    env.alloc_exec = cp_plat_alloc_exec;
    env.va = env_va;
    env.hook_addr = env_hook_addr;
    env.log = env_log;
    env.image_lo = (cp_addr)api->module_base;
    env.image_size = pe.size_of_image;
    cp_session_init(&g_sess, &env, &g_tun);
    cp_speed_init(&g_speed);
    cp_hooks.tun = &g_tun;
    cp_hooks.speed = &g_speed;

    int speed_live = 0;
    for (int g = 0; g < CP_G_COUNT; ++g) {
        const cp_group *grp = &CP_GROUPS[g];
        if (!g_cfg.group_on[g]) {
            plog(CC2X_LOG_INFO, "group %s: skipped (off in the ini, default)", grp->ini_key);
            continue;
        }
        cp_result res;
        cp_group_apply(&g_sess, g, grp->sites, grp->n_sites, &res);
        log_group(g, &res);
        if (g == CP_G_SPEED && (res.status == CP_GRP_APPLIED || res.status == CP_GRP_ALREADY)) speed_live = 1;
    }

    /* Lua: the speed-mode function exists only if the hook is in place (or on explicit request).
     * The SDK registers cc2x.<ns>.<name>, not a global: lua/cc2_vitesse_shim.lua defines the global
     * cc2_vitesse(team [, mode]) that library_custom_6.lua expects. */
    api->lua_feature("cc2_patchs");
    if (speed_live || g_cfg.lua_speed_stub) {
        api->lua_add("speed", "mode", lf_speed_mode);
        api->lua_feature("cc2_patchs_speed");
        if (!speed_live)
            plog(CC2X_LOG_WARN, "Lua speed stub registered (cc2x.speed.mode) but the speed_modes group is not applied: "
                                "the buttons change a number only, no aircraft speed");
    }
    return 1;
}
