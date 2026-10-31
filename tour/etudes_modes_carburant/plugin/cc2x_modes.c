/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * cc2x_modes.dll v3 - test plugin: ECO throttle cap and FLANK throttle floor for the human team's fixed-wing aircraft
 * (Albatros = definition 8, Manta = definition 10), settable per aircraft from Lua (the SPEED tab) with a "hand-flown" guard.
 * Built against cc2x.h of the CC2X SDK (GPL-3.0-or-later): shared under the same license, see tour/etudes_modes_carburant/.
 *
 * Settings: %APPDATA%\Carrier Command 2\cc2x\modes.ini ([modes], re-read every 3 s, see modes.ini.example).
 * Two stages, so nothing is written unless asked:
 *   - OBSERVE (default, enabled=0): never writes, whatever the modes. Every observe_s seconds it logs, for each flying
 *     aircraft of the human team: the throttle field as the game left it, speed, altitude, fuel.
 *   - ACTIVE (enabled=1): aircraft in ECO get their throttle lowered to a cap if the game left it higher; aircraft in
 *     FLANK get it raised to a floor if the game left it lower. Once per server tick, after the game's tick.
 *
 * Who is in which mode: first the table set from Lua (cc2x.modes.set), then the lists of modes.ini (eco_ids, flank_ids,
 * eco_all, flank_all). An aircraft asked for both ECO and FLANK by the ini stays NORMAL. The Lua table is per game session
 * (aircraft ids are only meaningful inside one session): it is emptied when a session starts or ends.
 *
 * Lua (cc2x.modes.*, any screen; thread-safe, nothing here touches game objects; the server tick does the work):
 *   set(id, mode)  mode 0 = NORMAL, 1 = ECO, 2 = FLANK  -> true, or false (bad arguments or table full: 64 aircraft)
 *   get(id)        -> mode, active, held   mode asked (0..2), active = what is being written now (0 none, 1 ECO, 2 FLANK),
 *                  held = true while the player is flying it by hand (see hold)
 *   hold(id)       "the player is flying this aircraft": the plugin leaves its throttle alone for the next 3 s. A script
 *                  that knows (the screen's g_viewing_vehicle_id > 0) must call it every frame. -> true
 *   status()       -> { version = 3, enabled = bool, eco_cap_light, eco_cap_heavy, flank_floor_light, flank_floor_heavy }
 *   cc2x.has("modes") is true once the plugin is loaded.
 *
 * Where the throttle lives: the wing aircraft's control tick (c_vehicle_server_wing::tick_control, image VA 0x719b80..
 * 0x71e533 in 1.5.18-win32) keeps four control outputs in the vehicle object: +0x308, +0x30c, +0x310 (pitch / roll / yaw,
 * each clamped to -1..1) and +0x314 (clamped to 0..1: the throttle). The regulator adds a step 0.2 x ((T - v)/120 - dv) to
 * +0x314 every tick; the caller copies it to the engine right after, so what the engine gets is OUR value plus that step
 * (measured on 28/10: written 0.65 -> applied ~0.72; confirmed by reading the Mac build). The engine power command +0x1fc
 * (CONTROL_POWER) is NOT used: the game multiplies ALL four outputs by it.
 * The plugin knows two builds of carrier_command.exe, told apart by their PE time stamp (0x6a36c177: 1.5.18 of 20/06/2026,
 * store at image VA 0x71dbbf; 0x6ae228f3: rebuilt 28/10/2026, store at 0x71dcbf) and refuses to load unless the 8 bytes at
 * that address are exactly "movss [edi+0x314], xmm0". It does NOT make the CC2X SDK accept the new build: the SDK (or any other
 * loader) must itself support the build it reports, the accessors used below are the loader's.
 *
 * Measured on 28/10 (throttle -> level speed): Albatros 0.72 -> 80 m/s, 0.93 -> 119 (AI cruise), 1.00 -> 131;
 * Manta 0.466 -> 122 (AI cruise), 0.77 -> 220, 1.00 -> 290. Fuel per second = 0.304 x throttle (Albatros), 0.76 x (Manta).
 * Per kilometre a faster aircraft burns LESS: ECO buys time in the air, not range; FLANK buys speed and range.
 * Not measured: a heavily equipped aircraft may be limited to 0.8 (Albatros) / 0.75 (Manta) of engine demand (Mac, 28/10).
 *
 * Never touched: AI teams, helicopters and everything that is not a wing aircraft, aircraft that are not flying (flight
 * state 2), attached or docking aircraft (a recall sets dock state 5 at once: modes stop), aircraft held by the player,
 * aircraft within eco_free_zone_m (ECO) or flank_free_zone_m (FLANK) of their team's carrier, any aircraft while no carrier
 * of its team exists, non-finite values. Caps are clamped to 0.55..1.0 (Albatros) and 0.30..1.0 (Manta): below that an
 * aircraft cannot hold its altitude. Floors are clamped to 0.50..1.0.
 */
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include "cc2x.h"

#define LOG(level, ...) A->log("modes", level, __VA_ARGS__)

#define PLUGIN_VERSION 3
#define TICKS_PER_S 30.0
#define CFG_PERIOD 90             /* ticks between two reads of the ini */
#define HOLD_TICKS 90             /* the player-flying guard lasts 3 s after the last hold() */
#define THR_OFFSET 0x314          /* float in the vehicle object: throttle command 0..1 (same in both builds below) */
#define MAX_IDS 16
#define MAX_SET 64                /* aircraft modes set from Lua */
#define MAX_HOLD 8
#define MAX_TRACK 32
#define MAX_CARRIERS 8
#define MAX_EV 16
#define LOG_CAP 4000
#define CHASSIS_CARRIER 0         /* e_game_object_type */
#define CHASSIS_WING_LIGHT 8      /* Albatros */
#define CHASSIS_WING_HEAVY 10     /* Manta */
#define FLOOR_MIN 0.50f

enum { MODE_NORMAL = 0, MODE_ECO = 1, MODE_FLANK = 2 };

static const uint8_t THR_BYTES[8] = {0xF3, 0x0F, 0x11, 0x87, 0x14, 0x03, 0x00, 0x00};

/* The game is recognised by the PE time stamp of carrier_command.exe (the "1.5.18" text did not change), then by the 8 bytes
 * of code at the throttle store: both must match. image VA of the store `movss [edi+0x314], xmm0` in each build: */
static const struct { uint32_t pe_timestamp, thr_site; } BUILDS[] = {
    {0x6a36c177u, 0x71dbbf},      /* 1.5.18 of 20/06/2026 (the build of every test so far) */
    {0x6ae228f3u, 0x71dcbf},      /* rebuilt 28/10/2026 (Steam build 26277078): code shifted by +0x100, object offsets unchanged */
};
static const float CAP_MIN[2] = {0.55f, 0.30f};      /* [0] Albatros, [1] Manta */
static const float CAP_DEFAULT[2] = {0.65f, 0.35f};
static const char *const TYPE_NAME[2] = {"Albatros", "Manta"};

typedef struct {
    int enabled, eco_all, flank_all, n_eco, n_flank, observe_ticks;
    float eco_cap[2], flank_floor[2];
    double eco_free_m, flank_free_m;
    uint32_t eco_ids[MAX_IDS], flank_ids[MAX_IDS];
} Cfg;

typedef struct {
    uint32_t id, last_obs, clamps;
    int used, seen, active, held, conflict_logged;     /* active: MODE_* currently written, 0 = none */
    float max_game_thr;
} Track;

typedef struct { uint32_t id; int mode; } SetEntry;
typedef struct { uint32_t id, until; } HoldEntry;
typedef struct { uint32_t id; int active, held; } PubState;
typedef struct { uint32_t id; int kind, value; } Event;     /* kind 1 = set(mode), 2 = set refused (table full) */

static const cc2x_api *A;
static char g_ini[MAX_PATH * 2];
static Cfg g_cfg, g_shown;
static int g_shown_valid;
static Track g_track[MAX_TRACK];
static volatile uint32_t g_tick;
static int g_logged;

/* shared between the server thread and the Lua threads: everything below is guarded by g_lock */
static CRITICAL_SECTION g_lock;
static Cfg g_pub;                                    /* copy of g_cfg for Lua and for mode_of */
static SetEntry g_set[MAX_SET];
static int g_nset;
static HoldEntry g_hold[MAX_HOLD];
static PubState g_state[MAX_TRACK];
static Event g_ev[MAX_EV];
static int g_nev;

static void lock(void) { EnterCriticalSection(&g_lock); }
static void unlock(void) { LeaveCriticalSection(&g_lock); }

static double clampd(double v, double lo, double hi) { return v < lo ? lo : v > hi ? hi : v; }

static double ini_num(const char *key, double def) {
    char buf[32], dflt[32], *c;
    snprintf(dflt, sizeof(dflt), "%g", def);
    GetPrivateProfileStringA("modes", key, dflt, buf, sizeof(buf), g_ini);
    if ((c = strchr(buf, ','))) *c = '.';        /* "0,65" typed by a French keyboard */
    return atof(buf);
}

static int ids_same(const uint32_t *a, const uint32_t *b, int n) {
    for (int i = 0; i < n; ++i) if (a[i] != b[i]) return 0;
    return 1;
}

static int cfg_same(const Cfg *a, const Cfg *b) {
    return a->enabled == b->enabled && a->eco_all == b->eco_all && a->flank_all == b->flank_all && a->n_eco == b->n_eco &&
           a->n_flank == b->n_flank && a->observe_ticks == b->observe_ticks && a->eco_cap[0] == b->eco_cap[0] &&
           a->eco_cap[1] == b->eco_cap[1] && a->flank_floor[0] == b->flank_floor[0] && a->flank_floor[1] == b->flank_floor[1] &&
           a->eco_free_m == b->eco_free_m && a->flank_free_m == b->flank_free_m && ids_same(a->eco_ids, b->eco_ids, a->n_eco) &&
           ids_same(a->flank_ids, b->flank_ids, a->n_flank);
}

static int read_ids(const char *key, uint32_t *out) {
    char buf[256], *p;
    int n = 0;
    GetPrivateProfileStringA("modes", key, "", buf, sizeof(buf), g_ini);
    for (p = buf; *p && n < MAX_IDS;) {
        while (*p == ' ' || *p == ',' || *p == ';') ++p;
        if (*p >= '0' && *p <= '9') out[n++] = (uint32_t)strtoul(p, &p, 10);
        else if (*p) ++p;
    }
    return n;
}

static void note(int level, const char *fmt, ...) {
    char text[300];
    va_list ap;
    if (g_logged >= LOG_CAP && level < CC2X_LOG_WARN) return;
    if (++g_logged == LOG_CAP) LOG(CC2X_LOG_WARN, "log cap reached: only warnings from now on");
    va_start(ap, fmt);
    vsnprintf(text, sizeof(text), fmt, ap);
    va_end(ap);
    LOG(level, "%s", text);
}

static void list_text(char *out, size_t size, const uint32_t *ids, int n) {
    out[0] = 0;
    for (int i = 0; i < n; ++i) snprintf(out + strlen(out), size - strlen(out), "%s%u", i ? "," : "", ids[i]);
}

static void read_cfg(void) {
    Cfg c;
    double en;
    memset(&c, 0, sizeof(c));
    en = ini_num("enabled", -1);                                       /* master switch; v1 name eco_enabled still read */
    if (en < 0) en = ini_num("eco_enabled", 0);
    c.enabled = g_ini[0] && en != 0;
    c.eco_all = ini_num("eco_all", 0) != 0;
    c.flank_all = ini_num("flank_all", 0) != 0;
    c.eco_cap[0] = (float)clampd(ini_num("eco_cap_light", ini_num("eco_cap", CAP_DEFAULT[0])), CAP_MIN[0], 1.0);   /* v1: eco_cap */
    c.eco_cap[1] = (float)clampd(ini_num("eco_cap_heavy", CAP_DEFAULT[1]), CAP_MIN[1], 1.0);
    c.flank_floor[0] = (float)clampd(ini_num("flank_floor_light", 1.0), FLOOR_MIN, 1.0);
    c.flank_floor[1] = (float)clampd(ini_num("flank_floor_heavy", 1.0), FLOOR_MIN, 1.0);
    c.eco_free_m = clampd(ini_num("eco_free_zone_m", ini_num("free_zone_m", 1500)), 0, 20000);   /* v1: free_zone_m */
    c.flank_free_m = clampd(ini_num("flank_free_zone_m", 6000), 0, 30000);
    c.observe_ticks = (int)(clampd(ini_num("observe_s", 5), 0, 600) * TICKS_PER_S + 0.5);
    c.n_eco = read_ids("eco_ids", c.eco_ids);
    c.n_flank = read_ids("flank_ids", c.flank_ids);
    g_cfg = c;
    lock();
    g_pub = c;
    unlock();
    if (!g_shown_valid || !cfg_same(&g_cfg, &g_shown)) {
        char le[160], lf[160];
        list_text(le, sizeof(le), c.eco_ids, c.n_eco);
        list_text(lf, sizeof(lf), c.flank_ids, c.n_flank);
        g_shown = g_cfg;
        g_shown_valid = 1;
        note(CC2X_LOG_INFO, "settings: enabled=%d eco_ids=[%s] eco_all=%d eco_cap=%.2f/%.2f (Albatros/Manta) eco_free_zone_m=%.0f "
             "flank_ids=[%s] flank_all=%d flank_floor=%.2f/%.2f flank_free_zone_m=%.0f observe_s=%.1f%s",
             c.enabled, le, c.eco_all, c.eco_cap[0], c.eco_cap[1], c.eco_free_m, lf, c.flank_all, c.flank_floor[0], c.flank_floor[1],
             c.flank_free_m, c.observe_ticks / TICKS_PER_S, c.enabled ? "" : " (observe only: nothing is written)");
    }
}

static Track *track_of(uint32_t id) {
    Track *free_slot = NULL;
    for (int i = 0; i < MAX_TRACK; ++i) {
        if (g_track[i].used && g_track[i].id == id) return &g_track[i];
        if (!g_track[i].used && !free_slot) free_slot = &g_track[i];
    }
    if (free_slot) { memset(free_slot, 0, sizeof(Track)); free_slot->used = 1; free_slot->id = id; free_slot->last_obs = g_tick; }
    return free_slot;
}

static int in_list(const uint32_t *ids, int n, uint32_t id) {
    for (int i = 0; i < n; ++i) if (ids[i] == id) return 1;
    return 0;
}

/* the mode asked for: the Lua table first, then modes.ini; ini asking ECO and FLANK = NORMAL (*conflict set). Any thread. */
static int mode_of(uint32_t id, int *conflict) {
    int m = -1, e, f;
    *conflict = 0;
    lock();
    for (int i = 0; i < g_nset; ++i) if (g_set[i].id == id) { m = g_set[i].mode; break; }
    e = g_pub.eco_all || in_list(g_pub.eco_ids, g_pub.n_eco, id);
    f = g_pub.flank_all || in_list(g_pub.flank_ids, g_pub.n_flank, id);
    unlock();
    if (m >= 0) return m;
    *conflict = e && f;
    if (e && f) return MODE_NORMAL;
    return f ? MODE_FLANK : e ? MODE_ECO : MODE_NORMAL;
}

static const char *mode_name(int m) { return m == MODE_ECO ? "ECO" : m == MODE_FLANK ? "FLANK" : "NORMAL"; }

static int is_held(uint32_t id) {
    int r = 0;
    lock();
    for (int i = 0; i < MAX_HOLD; ++i) if (g_hold[i].id == id && g_hold[i].until > g_tick) { r = 1; break; }
    unlock();
    return r;
}

static void publish_state(uint32_t id, int active, int held) {
    lock();
    for (int i = 0; i < MAX_TRACK; ++i)
        if (g_state[i].id == id) { g_state[i].active = active; g_state[i].held = held; unlock(); return; }
    for (int i = 0; i < MAX_TRACK; ++i)
        if (!g_state[i].id) { g_state[i].id = id; g_state[i].active = active; g_state[i].held = held; break; }
    unlock();
}

static void forget_state(uint32_t id) {
    lock();
    for (int i = 0; i < MAX_TRACK; ++i) if (g_state[i].id == id) memset(&g_state[i], 0, sizeof(PubState));
    unlock();
}

static void drain_events(void) {
    Event ev[MAX_EV];
    int n;
    lock();
    n = g_nev;
    memcpy(ev, g_ev, sizeof(Event) * (size_t)n);
    g_nev = 0;
    unlock();
    for (int i = 0; i < n; ++i) {
        if (ev[i].kind == 1) note(CC2X_LOG_INFO, "Lua: id %u set to %s", ev[i].id, mode_name(ev[i].value));
        else note(CC2X_LOG_WARN, "Lua: id %u mode not stored (table full)", ev[i].id);
    }
}

static void check_aircraft(void *v, const double *cpos, int have_carrier) {
    uint32_t id = (uint32_t)A->geti(v, CC2X_VEHICLE_ID, 0);
    Track *t = track_of(id);
    float *thr = (float *)((char *)v + THR_OFFSET);
    float game_thr = *thr;                           /* as the game left it after its tick */
    int def = (int)A->geti(v, CC2X_VEHICLE_DEFINITION, 0), ti = def == CHASSIS_WING_HEAVY;
    int flight = (int)A->geti(v, CC2X_VEHICLE_FLIGHT_STATE, 0);
    int attached = A->geti(v, CC2X_VEHICLE_ATTACHED_TO, 0) != 0;
    int dock = (int)A->geti(v, CC2X_VEHICLE_DOCK_STATE, 0);
    double dist = -1;
    int conflict = 0, mode, held, free_zone, now = MODE_NORMAL;

    if (!t) return;
    t->seen = 1;
    mode = mode_of(id, &conflict);
    held = is_held(id);
    if (have_carrier) {
        double dx = A->getf(v, CC2X_VEHICLE_POS, 0) - cpos[0], dz = A->getf(v, CC2X_VEHICLE_POS, 2) - cpos[2];
        dist = sqrt(dx * dx + dz * dz);
    }
    if (conflict && !t->conflict_logged) {
        t->conflict_logged = 1;
        note(CC2X_LOG_WARN, "id %u is in both the ECO and the FLANK settings: left NORMAL", id);
    } else if (!conflict) {
        t->conflict_logged = 0;
    }
    if (held != t->held) {
        t->held = held;
        note(CC2X_LOG_INFO, "id %u: %s (the player is flying it by hand)", id, held ? "HELD, modes paused" : "no longer held");
    }
    free_zone = !have_carrier || dist <= (mode == MODE_FLANK ? g_cfg.flank_free_m : g_cfg.eco_free_m);
    if (g_cfg.enabled && mode != MODE_NORMAL && !held && flight == CC2X_FLIGHT_FLYING && !attached && dock == 0 && !free_zone) now = mode;

    if (flight == CC2X_FLIGHT_FLYING && isfinite(game_thr) && game_thr > t->max_game_thr) t->max_game_thr = game_thr;
    if (now != MODE_NORMAL && isfinite(game_thr) && game_thr >= 0.0f && game_thr <= 1.0001f) {
        if (now == MODE_ECO && game_thr > g_cfg.eco_cap[ti]) { *thr = g_cfg.eco_cap[ti]; t->clamps++; }
        else if (now == MODE_FLANK && game_thr < g_cfg.flank_floor[ti]) { *thr = g_cfg.flank_floor[ti]; t->clamps++; }
    }
    if (now != t->active) {
        if (t->active != MODE_NORMAL) {
            note(CC2X_LOG_INFO, "id %u: %s off after %u writes (flight=%d attached=%d dock=%d free_zone=%d held=%d asked=%s enabled=%d)", id,
                 mode_name(t->active), t->clamps, flight, attached, dock, free_zone, held, mode_name(mode), g_cfg.enabled);
            t->clamps = 0;
        }
        if (now != MODE_NORMAL)
            note(CC2X_LOG_INFO, "id %u (%s): %s %s %.2f on (game throttle %.3f, %.0f m from the carrier)", id, TYPE_NAME[ti], mode_name(now),
                 now == MODE_ECO ? "cap" : "floor", now == MODE_ECO ? g_cfg.eco_cap[ti] : g_cfg.flank_floor[ti], game_thr, dist);
        t->active = now;
    }
    publish_state(id, now, held);
    if (g_cfg.observe_ticks && flight == CC2X_FLIGHT_FLYING && g_tick - t->last_obs >= (uint32_t)g_cfg.observe_ticks) {
        cc2x_body b;
        double speed = 0;
        char label[16];
        if (A->body_get(v, &b)) speed = sqrt(b.vel[0] * b.vel[0] + b.vel[1] * b.vel[1] + b.vel[2] * b.vel[2]);
        if (now != MODE_NORMAL) snprintf(label, sizeof(label), "%s", mode_name(now));
        else if (mode != MODE_NORMAL) snprintf(label, sizeof(label), "%s(idle)", mode_name(mode));
        else snprintf(label, sizeof(label), "NORMAL");
        note(CC2X_LOG_INFO, "id %u t=%.1f def=%d %s game_thr=%.3f max=%.3f written=%.3f speed=%.1f alt=%.0f fuel=%.1f dist=%.0f clamps=%u",
             id, g_tick / TICKS_PER_S, def, label, game_thr, t->max_game_thr, *thr, speed, A->getf(v, CC2X_VEHICLE_POS, 1),
             A->getf(v, CC2X_VEHICLE_FUEL, 0), dist, t->clamps);
        t->last_obs = g_tick;
        t->max_game_thr = 0;
    }
}

static void on_tick(void *server, void *user) {
    int ncar = 0, n = A->count(NULL, CC2X_WORLD_VEHICLES);
    double cpos[MAX_CARRIERS][3];
    uint32_t cteam[MAX_CARRIERS];

    memset(cpos, 0, sizeof(cpos));
    if (g_tick % CFG_PERIOD == 0) read_cfg();
    g_tick = g_tick + 1;
    drain_events();
    for (int i = 0; i < MAX_TRACK; ++i) g_track[i].seen = 0;
    for (int i = 0; i < n && ncar < MAX_CARRIERS; ++i) {
        void *v = A->ref(NULL, CC2X_WORLD_VEHICLES, i);
        if (v && A->geti(v, CC2X_VEHICLE_DEFINITION, 0) == CHASSIS_CARRIER) {
            for (int k = 0; k < 3; ++k) cpos[ncar][k] = A->getf(v, CC2X_VEHICLE_POS, k);
            cteam[ncar] = (uint32_t)A->geti(v, CC2X_VEHICLE_TEAM, 0);
            ncar++;
        }
    }
    for (int i = 0; i < n; ++i) {
        void *v = A->ref(NULL, CC2X_WORLD_VEHICLES, i);
        int def, best = -1;
        uint32_t team;
        double best_d = 1e30;
        if (!v || !A->geti(v, CC2X_VEHICLE_IS_WING, 0) || A->geti(v, CC2X_VEHICLE_TEAM_IS_AI, 0)) continue;
        def = (int)A->geti(v, CC2X_VEHICLE_DEFINITION, 0);
        if (def != CHASSIS_WING_LIGHT && def != CHASSIS_WING_HEAVY) continue;
        team = (uint32_t)A->geti(v, CC2X_VEHICLE_TEAM, 0);
        for (int k = 0; k < ncar; ++k) {                         /* nearest carrier of its own team */
            double d = fabs(A->getf(v, CC2X_VEHICLE_POS, 0) - cpos[k][0]) + fabs(A->getf(v, CC2X_VEHICLE_POS, 2) - cpos[k][2]);
            if (cteam[k] == team && d < best_d) { best_d = d; best = k; }
        }
        check_aircraft(v, best >= 0 ? cpos[best] : cpos[0], best >= 0);
    }
    for (int i = 0; i < MAX_TRACK; ++i)
        if (g_track[i].used && !g_track[i].seen) {                /* gone, or no longer a human wing aircraft */
            if (g_track[i].active) note(CC2X_LOG_INFO, "id %u: %s off (aircraft gone) after %u writes", g_track[i].id, mode_name(g_track[i].active), g_track[i].clamps);
            forget_state(g_track[i].id);
            g_track[i].used = 0;
        }
}

static void on_session(void *server, int started, void *user) {
    memset(g_track, 0, sizeof(g_track));
    g_tick = 0;
    g_logged = 0;
    g_shown_valid = 0;                                         /* log the settings again at the first read */
    lock();                                                    /* aircraft ids only mean something inside one session */
    g_nset = 0;
    memset(g_set, 0, sizeof(g_set));
    memset(g_hold, 0, sizeof(g_hold));
    memset(g_state, 0, sizeof(g_state));
    g_nev = 0;
    unlock();
    LOG(CC2X_LOG_INFO, "session %s", started ? "started" : "ended");
}

/* ---------------------------------------------------------------- Lua (screens' threads) */
static int lua_id(cc2x_lua *L, int idx, uint32_t *id) {
    int64_t v;
    if (!A->lua_tointeger(L, idx, &v) || v <= 0 || v > 0x7fffffff) return 0;
    *id = (uint32_t)v;
    return 1;
}

static int lua_set(cc2x_lua *L) {
    uint32_t id;
    int64_t mode;
    int ok = 0, changed = 0;
    if (!lua_id(L, 1, &id) || !A->lua_tointeger(L, 2, &mode) || mode < MODE_NORMAL || mode > MODE_FLANK) {
        A->lua_pushboolean(L, 0);
        return 1;
    }
    lock();
    for (int i = 0; i < g_nset && !ok; ++i)
        if (g_set[i].id == id) { changed = g_set[i].mode != (int)mode; g_set[i].mode = (int)mode; ok = 1; }
    if (!ok && g_nset < MAX_SET) { g_set[g_nset].id = id; g_set[g_nset].mode = (int)mode; g_nset++; ok = changed = 1; }
    if (changed || !ok) {                                       /* only real changes and refusals are logged */
        int slot = g_nev < MAX_EV ? g_nev++ : (!ok ? MAX_EV - 1 : -1);     /* a full queue still keeps the latest refusal */
        if (slot >= 0) { g_ev[slot].id = id; g_ev[slot].kind = ok ? 1 : 2; g_ev[slot].value = (int)mode; }
    }
    unlock();
    A->lua_pushboolean(L, ok);
    return 1;
}

static int lua_get(cc2x_lua *L) {
    uint32_t id;
    int mode, conflict, active = 0, held = 0;
    if (!lua_id(L, 1, &id)) {
        A->lua_pushnil(L);
        return 1;
    }
    mode = mode_of(id, &conflict);
    lock();
    for (int i = 0; i < MAX_TRACK; ++i) if (g_state[i].id == id) { active = g_state[i].active; held = g_state[i].held; break; }
    unlock();
    A->lua_pushinteger(L, mode);
    A->lua_pushinteger(L, active);
    A->lua_pushboolean(L, held);
    return 3;
}

static int lua_hold(cc2x_lua *L) {
    uint32_t id;
    int done = 0;
    if (!lua_id(L, 1, &id)) {
        A->lua_pushboolean(L, 0);
        return 1;
    }
    lock();
    for (int i = 0; i < MAX_HOLD && !done; ++i)                    /* same aircraft, or a free / expired slot */
        if (g_hold[i].id == id || g_hold[i].until <= g_tick) { g_hold[i].id = id; g_hold[i].until = g_tick + HOLD_TICKS; done = 1; }
    unlock();
    A->lua_pushboolean(L, done);
    return 1;
}

static void set_n(cc2x_lua *L, const char *k, double v) { A->lua_pushnumber(L, v); A->lua_setfield(L, k); }

static int lua_status(cc2x_lua *L) {
    Cfg c;
    lock();
    c = g_pub;
    unlock();
    A->lua_newtable(L);
    set_n(L, "version", PLUGIN_VERSION);
    A->lua_pushboolean(L, c.enabled);
    A->lua_setfield(L, "enabled");
    set_n(L, "eco_cap_light", c.eco_cap[0]);
    set_n(L, "eco_cap_heavy", c.eco_cap[1]);
    set_n(L, "flank_floor_light", c.flank_floor[0]);
    set_n(L, "flank_floor_heavy", c.flank_floor[1]);
    return 1;
}

/* PE time stamp of the running executable (0 if the header is not what we expect) */
static uint32_t pe_timestamp(uintptr_t base) {
    const uint8_t *p = (const uint8_t *)base;
    uint32_t nt, ts;
    if (!p || p[0] != 'M' || p[1] != 'Z') return 0;
    memcpy(&nt, p + 0x3c, 4);
    if (nt < 0x40 || nt > 0x1000 || memcmp(p + nt, "PE\0\0", 4) != 0) return 0;
    memcpy(&ts, p + nt + 8, 4);
    return ts;
}

CC2X_EXPORT int cc2x_plugin_load(const cc2x_api *a) {
    const uint8_t *site;
    uint32_t ts, thr_site = 0;
    if (a->api_version < 3 || a->size < sizeof(cc2x_api)) return 0;
    A = a;
    ts = pe_timestamp(a->module_base);
    for (size_t i = 0; i < sizeof(BUILDS) / sizeof(BUILDS[0]); ++i) if (BUILDS[i].pe_timestamp == ts) thr_site = BUILDS[i].thr_site;
    if (!thr_site) {                                                    /* a build the offset was never read from: do nothing */
        a->log("modes", CC2X_LOG_WARN, "unknown game build (PE time stamp 0x%08x): plugin not loaded", ts);
        return 0;
    }
    site = (const uint8_t *)a->va(thr_site);
    if (!site || memcmp(site, THR_BYTES, sizeof(THR_BYTES)) != 0) {      /* the code is not what we read: do nothing */
        a->log("modes", CC2X_LOG_WARN, "unexpected code at the throttle site (image VA 0x%x): plugin not loaded", thr_site);
        return 0;
    }
    InitializeCriticalSection(&g_lock);
    g_ini[0] = 0;
    if (a->config_dir && a->config_dir[0]) snprintf(g_ini, sizeof(g_ini), "%s\\modes.ini", a->config_dir);
    g_shown_valid = 0;
    a->on_server_tick(on_tick, NULL);
    a->on_session(on_session, NULL);
    if (a->lua_add && a->lua_feature) {
        a->lua_add("modes", "set", lua_set);
        a->lua_add("modes", "get", lua_get);
        a->lua_add("modes", "hold", lua_hold);
        a->lua_add("modes", "status", lua_status);
        a->lua_feature("modes");
    }
    LOG(CC2X_LOG_INFO, "loaded v%d; ini %s; observe only unless enabled=1; Lua cc2x.modes.set/get/hold/status", PLUGIN_VERSION,
        g_ini[0] ? g_ini : "(none)");
    return 1;
}
