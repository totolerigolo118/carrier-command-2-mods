/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Host test of cc2x_modes.c with a fake CC2X API (no game, no SDK DLL). 32-bit Windows console program.
 * Usage: test_modes.exe <empty work folder for modes.ini> */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../cc2x_modes.c"

typedef struct {
    char pad[THR_OFFSET];            /* the plugin reads / writes the float at THR_OFFSET of the vehicle object */
    float thr;
    float pad2[8];
    uint32_t id, def, team, attached, dock, flight;
    int is_wing, is_ai, alive;
    double pos[3], vel[3], fuel;
} FV;

static FV W[64];
static int NW;
static void (*tick_fn)(void *, void *);
static void (*sess_fn)(void *, int, void *);
static char logbuf[1 << 20];
static int pass, fail;
static char ini_dir[MAX_PATH];
static uint8_t site_bytes[8];
static uint8_t fake_pe[256];            /* a minimal PE header: MZ, e_lfanew = 0x80, "PE\0\0", time stamp at +8 */
static uint32_t fake_site_va;           /* the only image VA where the fake game has the throttle store */
static void set_build(uint32_t pe_timestamp, uint32_t site_va) {
    uint32_t nt = 0x80;
    memset(fake_pe, 0, sizeof(fake_pe));
    fake_pe[0] = 'M'; fake_pe[1] = 'Z';
    memcpy(fake_pe + 0x3c, &nt, 4);
    memcpy(fake_pe + nt, "PE\0\0", 4);
    memcpy(fake_pe + nt + 8, &pe_timestamp, 4);
    fake_site_va = site_va;
}

#define CHECK(c, ...) do { if (c) pass++; else { fail++; printf("  FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

static void f_log(const char *who, int level, const char *fmt, ...) {
    char t[400];
    va_list ap;
    va_start(ap, fmt); vsnprintf(t, sizeof(t), fmt, ap); va_end(ap);
    if (strlen(logbuf) + strlen(t) + 8 < sizeof(logbuf)) { strcat(logbuf, t); strcat(logbuf, "\n"); }
    (void)who; (void)level;
}
static int f_count(const void *o, int list) { return !o && list == CC2X_WORLD_VEHICLES ? NW : 0; }
static void *f_ref(const void *o, int f, int i) { return !o && f == CC2X_WORLD_VEHICLES && i >= 0 && i < NW ? &W[i] : NULL; }
static double f_getf(const void *o, int f, int i) {
    const FV *v = o;
    switch (f) {
    case CC2X_VEHICLE_ID: return v->id;
    case CC2X_VEHICLE_DEFINITION: return v->def;
    case CC2X_VEHICLE_TEAM: return v->team;
    case CC2X_VEHICLE_TEAM_IS_AI: return v->is_ai;
    case CC2X_VEHICLE_IS_WING: return v->is_wing;
    case CC2X_VEHICLE_ATTACHED_TO: return v->attached;
    case CC2X_VEHICLE_DOCK_STATE: return v->dock;
    case CC2X_VEHICLE_FLIGHT_STATE: return v->flight;
    case CC2X_VEHICLE_FUEL: return v->fuel;
    case CC2X_VEHICLE_POS: return v->pos[i];
    }
    return 0;
}
static int64_t f_geti(const void *o, int f, int i) { return (int64_t)f_getf(o, f, i); }
static int f_body_get(const void *o, cc2x_body *b) {
    const FV *v = o;
    memset(b, 0, sizeof(*b));
    memcpy(b->pos, v->pos, sizeof(b->pos)); memcpy(b->vel, v->vel, sizeof(b->vel)); b->rot[3] = 1;
    return 1;
}
static uintptr_t f_va(uint32_t va) { return va == fake_site_va ? (uintptr_t)site_bytes : 0; }
static void f_on_tick(void (*fn)(void *, void *), void *u) { tick_fn = fn; (void)u; }
static void f_on_session(void (*fn)(void *, int, void *), void *u) { sess_fn = fn; (void)u; }

static cc2x_api api;

/* ---- fake Lua API: the plugin's cc2x.modes.* functions are called directly ---- */
typedef struct { int type; double num; } LV;
static LV largs[4], lrets[8];
static int nlargs, nlrets;
static struct { char k[40]; int type; double v; } lfld[16];
static int nlfld, nlfn, lfeature;
static cc2x_lua_fn lfn[8];
static char lname[8][40];
#define NUM(x) ((LV){CC2X_LUA_NUMBER, (x)})
#define NIL ((LV){CC2X_LUA_NIL, 0})
#define STR ((LV){CC2X_LUA_STRING, 0})

static int fl_add(const char *ns, const char *name, cc2x_lua_fn fn) {
    snprintf(lname[nlfn], sizeof(lname[nlfn]), "%s.%s", ns ? ns : "", name); lfn[nlfn++] = fn;
    return 1;
}
static void fl_feature(const char *name) { lfeature += strcmp(name, "modes") == 0; }
static int fl_tointeger(cc2x_lua *L, int idx, int64_t *out) {
    (void)L;
    if (idx < 1 || idx > nlargs || largs[idx - 1].type != CC2X_LUA_NUMBER) return 0;
    *out = (int64_t)largs[idx - 1].num;
    return 1;
}
static void fl_push(int type, double v) { lrets[nlrets].type = type; lrets[nlrets++].num = v; }
static void fl_pushnil(cc2x_lua *L) { (void)L; fl_push(CC2X_LUA_NIL, 0); }
static void fl_pushboolean(cc2x_lua *L, int b) { (void)L; fl_push(CC2X_LUA_BOOLEAN, b ? 1 : 0); }
static void fl_pushinteger(cc2x_lua *L, int64_t v) { (void)L; fl_push(CC2X_LUA_NUMBER, (double)v); }
static void fl_pushnumber(cc2x_lua *L, double v) { (void)L; fl_push(CC2X_LUA_NUMBER, v); }
static void fl_newtable(cc2x_lua *L) { (void)L; fl_push(CC2X_LUA_TABLE, 0); nlfld = 0; }
static void fl_setfield(cc2x_lua *L, const char *k) {
    (void)L;
    nlrets--;                                       /* pops the value, which becomes a field of the table below it */
    snprintf(lfld[nlfld].k, sizeof(lfld[nlfld].k), "%s", k); lfld[nlfld].type = lrets[nlrets].type; lfld[nlfld++].v = lrets[nlrets].num;
}
static cc2x_lua_fn lfind(const char *name) {
    for (int i = 0; i < nlfn; ++i) if (!strcmp(lname[i], name)) return lfn[i];
    return NULL;
}
/* calls cc2x.modes.<name>(a0, a1) ; returns the number of results (also in nlrets) */
static int lcall(const char *name, int n, LV a0, LV a1) {
    cc2x_lua_fn f = lfind(name);
    nlargs = n; largs[0] = a0; largs[1] = a1; nlrets = 0;
    return f ? f((cc2x_lua *)1) : -1;
}
static int lok(int n, LV a0, LV a1) { lcall("modes.set", n, a0, a1); return nlrets == 1 && lrets[0].type == CC2X_LUA_BOOLEAN && lrets[0].num == 1; }
static double lfield(const char *k) { for (int i = 0; i < nlfld; ++i) if (!strcmp(lfld[i].k, k)) return lfld[i].v; return -999; }

static void write_ini(const char *text) {
    char p[MAX_PATH * 2];
    snprintf(p, sizeof(p), "%s\\modes.ini", ini_dir);
    if (!text) { remove(p); return; }
    FILE *f = fopen(p, "wb");
    fputs(text, f);
    fclose(f);
}
static void begin(const char *ini) {          /* new scenario: world, log, plugin state */
    memset(W, 0, sizeof(W)); NW = 0; logbuf[0] = 0;
    write_ini(ini);
    sess_fn(NULL, 1, NULL);
}
static FV *add(uint32_t id, uint32_t def, uint32_t team) {
    FV *v = &W[NW++];
    v->id = id; v->def = def; v->team = team; v->alive = 1;
    if (def == 8 || def == 10) { v->is_wing = 1; v->flight = 2; v->thr = 0.93f; v->fuel = 700; v->vel[0] = 119; v->pos[1] = 400; }
    return v;
}
static FV *carrier(void) { FV *c = add(1, 0, 1); c->pos[1] = 10; return c; }
static FV *plane(uint32_t id, double x) { FV *p = add(id, 8, 1); p->pos[0] = x; return p; }
static void step(int n) { for (int i = 0; i < n; ++i) tick_fn(NULL, NULL); }
static int has(const char *s) { return strstr(logbuf, s) != NULL; }
static int near_(float a, float b) { return fabsf(a - b) < 1e-6f; }

#define OBSERVE "[modes]\nobserve_s=1\n"
#define CAP9 "[modes]\neco_enabled=1\neco_cap=0.65\neco_ids=9\nobserve_s=1\n"

int main(int argc, char **argv) {
    if (argc < 2) { puts("usage: test_modes <folder>"); return 2; }
    snprintf(ini_dir, sizeof(ini_dir), "%s", argv[1]);
    memcpy(site_bytes, THR_BYTES, 8);
    api.api_version = CC2X_API_VERSION; api.size = sizeof(cc2x_api); api.game_build = "1.5.18-win32"; api.config_dir = ini_dir;
    api.log = f_log; api.count = f_count; api.ref = f_ref; api.geti = f_geti; api.getf = f_getf; api.body_get = f_body_get;
    api.va = f_va; api.on_server_tick = f_on_tick; api.on_session = f_on_session;
    api.lua_add = fl_add; api.lua_feature = fl_feature; api.lua_tointeger = fl_tointeger; api.lua_pushnil = fl_pushnil;
    api.lua_pushboolean = fl_pushboolean; api.lua_pushinteger = fl_pushinteger; api.lua_pushnumber = fl_pushnumber;
    api.lua_newtable = fl_newtable; api.lua_setfield = fl_setfield;

    puts("load checks: two known builds, told apart by the PE time stamp");
    api.module_base = (uintptr_t)fake_pe;
    set_build(0x12345678u, 0x71dbbf);  CHECK(cc2x_plugin_load(&api) == 0, "unknown PE time stamp must be refused");
    set_build(0u, 0x71dbbf);           CHECK(cc2x_plugin_load(&api) == 0, "no time stamp must be refused");
    fake_pe[0] = 0;                    CHECK(cc2x_plugin_load(&api) == 0, "no MZ header must be refused");
    api.module_base = 0;               CHECK(cc2x_plugin_load(&api) == 0, "no module base must be refused");
    api.module_base = (uintptr_t)fake_pe;
    set_build(0x6a36c177u, 0x71dbbf);  api.api_version = 2; CHECK(cc2x_plugin_load(&api) == 0, "API 2 must be refused");
    api.api_version = CC2X_API_VERSION;
    site_bytes[4] = 0x15;              CHECK(cc2x_plugin_load(&api) == 0, "other bytes at the throttle site must be refused");
    site_bytes[4] = 0x14;
    set_build(0x6a36c177u, 0x71dcbf);  CHECK(cc2x_plugin_load(&api) == 0, "old time stamp with the code of the NEW address must be refused");
    set_build(0x6ae228f3u, 0x71dbbf);  CHECK(cc2x_plugin_load(&api) == 0, "new time stamp with the code of the OLD address must be refused");
    set_build(0x6ae228f3u, 0x71dcbf);  CHECK(cc2x_plugin_load(&api) == 1, "new build (28/10/2026): loads");
    nlfn = 0; lfeature = 0;            /* forget those registrations: the real load below is the one the tests use */
    set_build(0x6a36c177u, 0x71dbbf);  CHECK(cc2x_plugin_load(&api) == 1, "old build (1.5.18): loads");
    CHECK(tick_fn && sess_fn, "events subscribed");

    puts("observe only (no ini, then eco_enabled=0): never writes");
    begin(NULL);
    carrier(); FV *a = plane(9, 5000); FV *b = plane(10, 6000);
    step(200);
    CHECK(near_(a->thr, 0.93f) && near_(b->thr, 0.93f), "no ini: thr unchanged (%.3f)", a->thr);
    CHECK(has("observe only") && has("id 9 t=") && has("NORMAL"), "observe lines logged:\n%s", logbuf);
    begin("[modes]\neco_enabled=0\neco_ids=9\neco_all=1\nobserve_s=1\n");
    carrier(); a = plane(9, 5000); step(200);
    CHECK(near_(a->thr, 0.93f), "eco_enabled=0: thr unchanged even with eco_all=1");

    puts("cap: only the listed aircraft, only the excess");
    begin(CAP9);
    carrier(); a = plane(9, 5000); b = plane(10, 6000); FV *c = plane(11, 7000);
    a->thr = 0.93f; b->thr = 0.93f; c->thr = 1.0f;
    step(5);
    CHECK(near_(a->thr, 0.65f), "id 9 capped to 0.65 (got %.3f)", a->thr);
    CHECK(near_(b->thr, 0.93f) && near_(c->thr, 1.0f), "id 10 and 11 untouched (%.3f %.3f)", b->thr, c->thr);
    CHECK(has("id 9 (Albatros): ECO cap 0.65 on"), "start logged");
    a->thr = 0.5f; step(3);
    CHECK(near_(a->thr, 0.5f), "below the cap: untouched (got %.3f)", a->thr);
    a->thr = 1.0f; step(3);
    CHECK(near_(a->thr, 0.65f), "full throttle capped (got %.3f)", a->thr);
    a->thr = 0.0f; step(3);
    CHECK(near_(a->thr, 0.0f), "zero stays zero");
    a->thr = NAN; step(3);
    CHECK(isnan(a->thr), "NaN is never written over");
    a->thr = 1.7f; step(3);
    CHECK(near_(a->thr, 1.7f), "garbage above 1 is left alone");
    a->thr = 0.9f; step(3);
    CHECK(near_(a->thr, 0.65f), "capped again");
    step(60);
    CHECK(has("ECO game_thr="), "ECO observe line");

    puts("eco_all, cap range");
    begin("[modes]\neco_enabled=1\neco_all=1\neco_cap=0,7\n");
    carrier(); a = plane(9, 5000); b = plane(10, 6000);
    step(5);
    CHECK(near_(a->thr, 0.7f) && near_(b->thr, 0.7f), "eco_all, decimal comma: 0.7 (got %.3f %.3f)", a->thr, b->thr);
    begin("[modes]\neco_enabled=1\neco_all=1\neco_cap=0.2\n");
    carrier(); a = plane(9, 5000); step(5);
    CHECK(near_(a->thr, CAP_MIN[0]), "cap below 0.55 raised to 0.55 (got %.3f)", a->thr);
    begin("[modes]\neco_enabled=1\neco_all=1\neco_cap=3\n");
    carrier(); a = plane(9, 5000); step(5);
    CHECK(near_(a->thr, 0.93f), "cap above 1 = no effect (got %.3f)", a->thr);

    puts("never capped: free zone, state, team, type, no carrier");
    begin(CAP9);
    carrier(); a = plane(9, 800); step(5);
    CHECK(near_(a->thr, 0.93f), "within 1500 m of the carrier: untouched (got %.3f)", a->thr);
    a->pos[0] = 1600; step(5);
    CHECK(near_(a->thr, 0.65f), "beyond 1500 m: capped");
    a->pos[0] = 1400; a->thr = 0.93f; step(5);
    CHECK(near_(a->thr, 0.93f) && has("ECO off after"), "back inside the zone: released");
    a->pos[0] = 5000; a->flight = 1; a->thr = 0.93f; step(5);
    CHECK(near_(a->thr, 0.93f), "not flying (flight 1): untouched");
    a->flight = 2; a->attached = 1; step(5);
    CHECK(near_(a->thr, 0.93f), "attached: untouched");
    a->attached = 0; a->dock = 5; step(5);
    CHECK(near_(a->thr, 0.93f), "docking queue: untouched");
    a->dock = 0; step(5);
    CHECK(near_(a->thr, 0.65f), "free again: capped");
    a->is_ai = 1; a->thr = 0.93f; step(5);
    CHECK(near_(a->thr, 0.93f), "AI team: never touched");
    a->is_ai = 0; a->def = 12; step(5);
    CHECK(near_(a->thr, 0.93f), "not a wing definition: untouched");
    a->def = 10; step(5);
    CHECK(near_(a->thr, 0.35f), "Manta (10) capped with its own cap 0.35 (got %.3f)", a->thr);
    a->team = 2; a->thr = 0.93f; step(5);
    CHECK(near_(a->thr, 0.93f), "no carrier of its own team: untouched");
    begin(CAP9);
    a = plane(9, 5000); step(5);
    CHECK(near_(a->thr, 0.93f), "no carrier in the world: untouched");

    puts("settings change while running, session reset");
    begin(CAP9);
    carrier(); a = plane(9, 5000); step(5);
    CHECK(near_(a->thr, 0.65f), "capped");
    write_ini("[modes]\neco_enabled=0\n");
    step(200);                                      /* the old cap still applies until the next read (3 s) ... */
    a->thr = 0.93f; step(3);                        /* ... then the fake game recomputes its throttle: it must be left alone */
    CHECK(near_(a->thr, 0.93f) && has("ECO off after"), "ini switched off within 3 s: released, untouched (got %.3f)", a->thr);
    write_ini("[modes]\neco_enabled=1\neco_ids=9,10 ; 11\neco_cap=0.8\n");
    a->thr = 0.93f; step(200);
    CHECK(near_(a->thr, 0.8f), "new cap 0.8 read (got %.3f)", a->thr);
    a->alive = 0; NW = 1; step(3);
    CHECK(has("aircraft gone"), "aircraft gone logged");
    sess_fn(NULL, 0, NULL);
    CHECK(has("session ended"), "session event");

    puts("v2: ECO cap per aircraft type");
    begin("[modes]\nenabled=1\neco_ids=9,11\nobserve_s=1\n");
    carrier(); a = plane(9, 5000); FV *m = add(11, 10, 1); m->pos[0] = 6000;
    a->thr = 0.93f; m->thr = 0.466f; step(5);
    CHECK(near_(a->thr, 0.65f), "Albatros cap 0.65 (got %.3f)", a->thr);
    CHECK(near_(m->thr, 0.35f), "Manta cap 0.35 (got %.3f)", m->thr);
    CHECK(has("id 11 (Manta): ECO cap 0.35 on"), "Manta start logged");
    begin("[modes]\nenabled=1\neco_ids=11\neco_cap_heavy=0.1\n");
    carrier(); m = add(11, 10, 1); m->pos[0] = 6000; m->thr = 0.466f; step(5);
    CHECK(near_(m->thr, 0.30f), "Manta cap raised to its minimum 0.30 (got %.3f)", m->thr);
    begin("[modes]\nenabled=1\neco_ids=11\neco_cap_heavy=0.9\n");
    carrier(); m = add(11, 10, 1); m->pos[0] = 6000; m->thr = 0.466f; step(5);
    CHECK(near_(m->thr, 0.466f), "cap above the game's value: untouched (got %.3f)", m->thr);
    m->thr = 1.0f; step(3);
    CHECK(near_(m->thr, 0.9f), "full throttle capped to 0.9 (got %.3f)", m->thr);

    puts("v2: FLANK floor");
    begin("[modes]\nenabled=1\nflank_ids=9,11\nobserve_s=1\n");
    carrier(); a = plane(9, 8000); m = add(11, 10, 1); m->pos[0] = 9000; b = plane(10, 8000);
    a->thr = 0.5f; m->thr = 0.466f; b->thr = 0.5f; step(5);
    CHECK(near_(a->thr, 1.0f) && near_(m->thr, 1.0f), "floors 1.0 on both types (got %.3f %.3f)", a->thr, m->thr);
    CHECK(near_(b->thr, 0.5f), "not listed: untouched (got %.3f)", b->thr);
    CHECK(has("id 9 (Albatros): FLANK floor 1.00 on") && has("id 11 (Manta): FLANK floor 1.00 on"), "start logged:\n%s", logbuf);
    a->thr = 0.99f; step(3);
    CHECK(near_(a->thr, 1.0f), "0.99 raised to 1.0 (got %.3f)", a->thr);
    a->thr = NAN; step(3);
    CHECK(isnan(a->thr), "NaN is never written over");
    a->thr = 1.7f; step(3);
    CHECK(near_(a->thr, 1.7f), "garbage above 1 is left alone");
    a->thr = -0.2f; step(3);
    CHECK(near_(a->thr, -0.2f), "negative is left alone");
    step(60);
    CHECK(has("FLANK game_thr="), "FLANK observe line");
    begin("[modes]\nenabled=1\nflank_ids=9,11\nflank_floor_light=0.9\nflank_floor_heavy=0.8\n");
    carrier(); a = plane(9, 8000); m = add(11, 10, 1); m->pos[0] = 9000;
    a->thr = 0.5f; m->thr = 0.5f; step(5);
    CHECK(near_(a->thr, 0.9f) && near_(m->thr, 0.8f), "per-type floors 0.9 / 0.8 (got %.3f %.3f)", a->thr, m->thr);
    a->thr = 0.95f; step(3);
    CHECK(near_(a->thr, 0.95f), "above the floor: untouched");
    begin("[modes]\nenabled=1\nflank_ids=9\nflank_floor_light=0.1\n");
    carrier(); a = plane(9, 8000); a->thr = 0.2f; step(5);
    CHECK(near_(a->thr, 0.5f), "floor below 0.50 raised to 0.50 (got %.3f)", a->thr);

    puts("v2: FLANK free zone, other conditions");
    begin("[modes]\nenabled=1\nflank_ids=9\n");
    carrier(); a = plane(9, 5000); a->thr = 0.5f; step(5);
    CHECK(near_(a->thr, 0.5f), "within the 6000 m FLANK free zone: untouched (got %.3f)", a->thr);
    a->pos[0] = 7000; step(5);
    CHECK(near_(a->thr, 1.0f), "beyond 6000 m: floor");
    begin("[modes]\nenabled=1\nflank_ids=9\nflank_free_zone_m=2000\n");
    carrier(); a = plane(9, 5000); a->thr = 0.5f; step(5);
    CHECK(near_(a->thr, 1.0f), "flank_free_zone_m=2000: floor at 5000 m");
    a->flight = 1; a->thr = 0.5f; step(5);
    CHECK(near_(a->thr, 0.5f), "not flying: untouched");
    a->flight = 2; a->dock = 5; step(5);
    CHECK(near_(a->thr, 0.5f), "recalled (dock 5): FLANK stops at once");
    a->dock = 0; a->attached = 1; step(5);
    CHECK(near_(a->thr, 0.5f), "attached: untouched");
    a->attached = 0; a->is_ai = 1; step(5);
    CHECK(near_(a->thr, 0.5f), "AI team: never touched");
    a->is_ai = 0; a->def = 12; step(5);
    CHECK(near_(a->thr, 0.5f), "not a wing definition: untouched");
    a->def = 8; a->team = 2; step(5);
    CHECK(near_(a->thr, 0.5f), "no carrier of its own team: untouched");

    puts("v2: conflicts, *_all, mode switch, v1 names");
    begin("[modes]\nenabled=1\neco_ids=9\nflank_ids=9\n");
    carrier(); a = plane(9, 8000); a->thr = 0.8f; step(5);
    CHECK(near_(a->thr, 0.8f) && has("both the ECO and the FLANK"), "in both lists: NORMAL + warning");
    begin("[modes]\nenabled=1\neco_all=1\nflank_all=1\n");
    carrier(); a = plane(9, 8000); a->thr = 0.8f; step(5);
    CHECK(near_(a->thr, 0.8f), "both *_all: NORMAL");
    begin("[modes]\nenabled=1\nflank_all=1\n");
    carrier(); a = plane(9, 8000); b = plane(10, 9000); a->thr = 0.5f; b->thr = 0.6f; step(5);
    CHECK(near_(a->thr, 1.0f) && near_(b->thr, 1.0f), "flank_all: every human wing aircraft");
    begin("[modes]\nenabled=1\neco_ids=9\n");
    carrier(); a = plane(9, 8000); a->thr = 0.9f; step(5);
    CHECK(near_(a->thr, 0.65f), "ECO");
    write_ini("[modes]\nenabled=1\nflank_ids=9\n");
    step(200); a->thr = 0.5f; step(3);
    CHECK(near_(a->thr, 1.0f) && has("ECO off after") && has("FLANK floor 1.00 on"), "ECO -> FLANK at runtime (got %.3f)", a->thr);
    begin("[modes]\neco_enabled=1\neco_ids=9\neco_cap=0.7\nfree_zone_m=100\n");
    carrier(); a = plane(9, 800); a->thr = 0.9f; step(5);
    CHECK(near_(a->thr, 0.7f), "v1 names (eco_enabled, eco_cap, free_zone_m) still work (got %.3f)", a->thr);
    begin("[modes]\nenabled=0\neco_enabled=1\neco_ids=9\n");
    carrier(); a = plane(9, 8000); a->thr = 0.9f; step(5);
    CHECK(near_(a->thr, 0.9f), "enabled=0 wins over eco_enabled=1");
    begin("[modes]\nflank_ids=9\n");
    carrier(); a = plane(9, 8000); a->thr = 0.5f; step(5);
    CHECK(near_(a->thr, 0.5f), "no enabled: observe only");

    puts("v3: Lua bridge, registration and arguments");
    CHECK(lfind("modes.set") && lfind("modes.get") && lfind("modes.hold") && lfind("modes.status"), "four functions registered");
    CHECK(lfeature == 1, "cc2x.has(\"modes\") announced once");
    begin("[modes]\nenabled=1\nobserve_s=1\n");
    CHECK(lok(2, NUM(9), NUM(1)) && lok(2, NUM(9), NUM(0)) && lok(2, NUM(9), NUM(2)), "valid set calls return true");
    lcall("modes.set", 2, NIL, NUM(1));       CHECK(nlrets == 1 && lrets[0].num == 0, "nil id refused");
    lcall("modes.set", 2, STR, NUM(1));       CHECK(lrets[0].num == 0, "string id refused");
    lcall("modes.set", 2, NUM(0), NUM(1));    CHECK(lrets[0].num == 0, "id 0 refused");
    lcall("modes.set", 2, NUM(-5), NUM(1));   CHECK(lrets[0].num == 0, "negative id refused");
    lcall("modes.set", 2, NUM(1099511627776.0), NUM(1)); CHECK(lrets[0].num == 0, "id above 2^31 refused");
    lcall("modes.set", 2, NUM(9), NUM(3));    CHECK(lrets[0].num == 0, "mode 3 refused");
    lcall("modes.set", 2, NUM(9), NUM(-1));   CHECK(lrets[0].num == 0, "mode -1 refused");
    lcall("modes.set", 1, NUM(9), NIL);       CHECK(lrets[0].num == 0, "missing mode refused");
    lcall("modes.set", 0, NIL, NIL);          CHECK(lrets[0].num == 0, "no arguments refused");
    lcall("modes.get", 1, NIL, NIL);          CHECK(nlrets == 1 && lrets[0].type == CC2X_LUA_NIL, "get(nil) = nil");
    lcall("modes.get", 1, NUM(777), NIL);     CHECK(nlrets == 3 && lrets[0].num == 0 && lrets[1].num == 0 && lrets[2].num == 0, "unknown id: mode 0, not active, not held");
    lcall("modes.hold", 1, NIL, NIL);         CHECK(lrets[0].type == CC2X_LUA_BOOLEAN && lrets[0].num == 0, "hold(nil) refused");

    puts("v3: Lua modes drive the plugin (only when enabled)");
    begin("[modes]\nenabled=1\nobserve_s=1\n");
    carrier(); a = plane(9, 8000); a->thr = 0.93f;
    CHECK(lok(2, NUM(9), NUM(1)), "set ECO");
    step(5);
    CHECK(near_(a->thr, 0.65f), "Lua ECO caps (got %.3f)", a->thr);
    lcall("modes.get", 1, NUM(9), NIL);
    CHECK(nlrets == 3 && lrets[0].num == 1 && lrets[1].num == 1 && lrets[2].num == 0, "get: asked ECO, active ECO, not held (%d %g %g %g)", nlrets, lrets[0].num, lrets[1].num, lrets[2].num);
    CHECK(has("Lua: id 9 set to ECO"), "event logged on the server thread:\n%s", logbuf);
    CHECK(lok(2, NUM(9), NUM(2)), "set FLANK");
    a->thr = 0.5f; step(5);
    CHECK(near_(a->thr, 1.0f), "Lua FLANK raises (got %.3f)", a->thr);
    lcall("modes.get", 1, NUM(9), NIL);
    CHECK(lrets[0].num == 2 && lrets[1].num == 2, "get: asked FLANK, active FLANK");
    CHECK(lok(2, NUM(9), NUM(0)), "set NORMAL");
    a->thr = 0.5f; step(5);
    CHECK(near_(a->thr, 0.5f), "Lua NORMAL: untouched");
    lcall("modes.get", 1, NUM(9), NIL);
    CHECK(lrets[0].num == 0 && lrets[1].num == 0, "get: NORMAL, not active");

    begin("[modes]\nenabled=1\neco_ids=9\n");
    carrier(); a = plane(9, 8000); a->thr = 0.93f; step(5);
    CHECK(near_(a->thr, 0.65f), "ini ECO caps");
    CHECK(lok(2, NUM(9), NUM(0)), "Lua says NORMAL for an id the ini lists as ECO");
    a->thr = 0.93f; step(5);
    CHECK(near_(a->thr, 0.93f), "the Lua table wins over the ini lists (got %.3f)", a->thr);
    begin("[modes]\nenabled=1\neco_ids=9\nflank_ids=9\n");
    carrier(); a = plane(9, 8000); a->thr = 0.8f; step(5);
    CHECK(near_(a->thr, 0.8f), "ini conflict = NORMAL");
    CHECK(lok(2, NUM(9), NUM(1)), "Lua ECO resolves the ini conflict");
    a->thr = 0.8f; step(5);
    CHECK(near_(a->thr, 0.65f), "Lua ECO applies (got %.3f)", a->thr);

    begin("[modes]\nenabled=0\n");
    carrier(); a = plane(9, 8000); a->thr = 0.93f;
    CHECK(lok(2, NUM(9), NUM(1)), "set ECO while disabled");
    step(5);
    CHECK(near_(a->thr, 0.93f), "enabled=0: nothing is written whatever Lua asked (got %.3f)", a->thr);
    lcall("modes.get", 1, NUM(9), NIL);
    CHECK(lrets[0].num == 1 && lrets[1].num == 0, "get: asked ECO, not active");
    lcall("modes.status", 0, NIL, NIL);
    CHECK(lrets[0].type == CC2X_LUA_TABLE && lfield("version") == 3 && lfield("enabled") == 0, "status: version 3, enabled false");

    begin("[modes]\nenabled=1\neco_cap_heavy=0.4\nflank_floor_light=0.8\n");
    step(1);
    lcall("modes.status", 0, NIL, NIL);
    CHECK(lfield("enabled") == 1 && near_((float)lfield("eco_cap_heavy"), 0.4f) && near_((float)lfield("flank_floor_light"), 0.8f) &&
          near_((float)lfield("eco_cap_light"), 0.65f) && near_((float)lfield("flank_floor_heavy"), 1.0f), "status: published settings");

    puts("v3: hand-flown guard (hold)");
    begin("[modes]\nenabled=1\nobserve_s=1\n");
    carrier(); a = plane(9, 8000);
    lok(2, NUM(9), NUM(1));
    a->thr = 0.93f; step(5);
    CHECK(near_(a->thr, 0.65f), "capped before the hold");
    a->thr = 0.93f;
    lcall("modes.hold", 1, NUM(9), NIL);
    CHECK(lrets[0].type == CC2X_LUA_BOOLEAN && lrets[0].num == 1, "hold accepted");
    step(3);
    CHECK(near_(a->thr, 0.93f), "held: the pilot's throttle is left alone (got %.3f)", a->thr);
    lcall("modes.get", 1, NUM(9), NIL);
    CHECK(lrets[0].num == 1 && lrets[1].num == 0 && lrets[2].num == 1, "get: asked ECO, not active, held");
    CHECK(has("id 9: HELD") && has("ECO off after"), "held and released-from-ECO logged:\n%s", logbuf);
    for (int k = 0; k < 10; ++k) { lcall("modes.hold", 1, NUM(9), NIL); step(30); a->thr = 0.93f; }    /* 10 s of continuous hold() */
    step(1);
    CHECK(near_(a->thr, 0.93f), "continuous hold(): never written");
    step(100);                                                /* the script stopped calling hold(): 3 s later it resumes */
    a->thr = 0.93f; step(3);
    CHECK(near_(a->thr, 0.65f), "hold expired: ECO resumes (got %.3f)", a->thr);
    CHECK(has("no longer held"), "release logged");
    begin("[modes]\nenabled=1\n");
    carrier(); a = plane(9, 8000); a->thr = 0.5f;
    lok(2, NUM(9), NUM(2)); lcall("modes.hold", 1, NUM(9), NIL);
    step(5);
    CHECK(near_(a->thr, 0.5f), "held FLANK aircraft: floor not applied");
    for (int k = 1; k <= 12; ++k) lcall("modes.hold", 1, NUM(k), NIL);     /* more ids than slots: the oldest expired ones are reused */
    CHECK(lrets[0].type == CC2X_LUA_BOOLEAN, "many hold() calls do not break");

    puts("v3: table size and session reset");
    begin("[modes]\nenabled=1\n");
    int allok = 1;
    for (int k = 1; k <= 64; ++k) allok &= lok(2, NUM(k), NUM(1));
    CHECK(allok, "64 aircraft stored");
    lcall("modes.set", 2, NUM(65), NUM(1));
    CHECK(lrets[0].num == 0, "65th aircraft refused");
    CHECK(lok(2, NUM(3), NUM(2)), "an aircraft already stored can still be changed");
    carrier(); a = plane(3, 8000); a->thr = 0.5f; step(5);
    CHECK(has("table full") && near_(a->thr, 1.0f), "refusal logged; stored aircraft works (got %.3f)", a->thr);
    sess_fn(NULL, 1, NULL);
    lcall("modes.get", 1, NUM(3), NIL);
    CHECK(lrets[0].num == 0, "a new session empties the Lua table");
    lok(2, NUM(5), NUM(1)); sess_fn(NULL, 0, NULL);
    lcall("modes.get", 1, NUM(5), NIL);
    CHECK(lrets[0].num == 0, "the end of a session empties it too");
    write_ini(NULL);

    printf("\n%d passed, %d failed\n", pass, fail);
    return fail ? 1 : 0;
}
