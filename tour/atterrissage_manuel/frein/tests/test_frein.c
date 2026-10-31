/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Host test of cc2x_frein.c with a fake CC2X API (no game, no SDK DLL). 32-bit Windows console program.
 * Usage: test_frein.exe <empty work folder for frein.ini> [-v]   (-v: on a failure, also print the plugin's key log lines) */
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../cc2x_frein.c"

typedef struct {
    uint32_t id, def, team, attached, dock, flight, mode, dock_vehicle;
    int is_wing, is_rotor, is_ai, taxi, nw, nwp, alive;
    float contact[3];
    double pos[3], vel[3], power, ctrl_speed, target[3];
    double fuel;
    uint8_t pad[0x200];      /* v12: the game's own fields H5 reads, at their offsets (+0xac wheels, +0xb0 wheel count, +0x188 preferred bay) */
} FV;
_Static_assert(offsetof(FV, pad) <= 0xac, "FV: the named fields must end before +0xac");

static FV W[64];
static int NW;
static void (*tick_fn)(void *, void *);
static void (*sess_fn)(void *, int, void *);
static struct { uint32_t id; float b, g; } calls[200000];
static int ncalls;
static char logbuf[1 << 20];
static int pass, fail;
static char ini_dir[MAX_PATH];

static int verbose;          /* argv[2] == "-v": on a failure, also print the plugin's FORCE / VERDICT / HOOK / PROBE / RUNWAY / COMMIT log lines of the scenario */
static void dump_log(void);
#define CHECK(c, ...) do { if (c) pass++; else { fail++; printf("  FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); if (verbose) dump_log(); } } while (0)

static void f_log(const char *who, int level, const char *fmt, ...) {
    char t[600];
    va_list ap;
    va_start(ap, fmt); vsnprintf(t, sizeof(t), fmt, ap); va_end(ap);
    if (strlen(logbuf) + strlen(t) + 8 < sizeof(logbuf)) { strcat(logbuf, t); strcat(logbuf, "\n"); }
    (void)who; (void)level;
}
static void dump_log(void) {
    static const char *keys[] = {"FORCE", "VERDICT", "HOOK", "PROBE", "RUNWAY", "COMMIT", "RECALL start", "RECALL ended", "FOLLOW", "TAKEN", "HANGAR", "REFUEL", "UNEXPECTED", "AFTER THE"};
    const char *s = logbuf;
    while (*s) {
        const char *e = strchr(s, '\n');
        size_t n = e ? (size_t)(e - s) : strlen(s);
        for (unsigned k = 0; k < sizeof(keys) / sizeof(keys[0]); ++k) {
            char line[600];
            size_t m = n < sizeof(line) - 1 ? n : sizeof(line) - 1;
            memcpy(line, s, m); line[m] = 0;
            if (strstr(line, keys[k])) { printf("      | %s\n", line); break; }
        }
        s += n + (e ? 1 : 0);
    }
}
static int f_count(const void *o, int list) {
    const FV *v = o;
    if (!o && list == CC2X_WORLD_VEHICLES) return NW;
    if (o && list == CC2X_VEHICLE_WHEELS) return v->nw;
    if (o && list == CC2X_VEHICLE_WAYPOINTS) return v->nwp;
    return 0;
}
static void *f_ref(const void *o, int f, int i) { return !o && f == CC2X_WORLD_VEHICLES && i >= 0 && i < NW ? &W[i] : NULL; }
static void *f_find(int list, uint32_t id) {
    for (int i = 0; i < NW && list == CC2X_WORLD_VEHICLES; ++i) if (W[i].alive && W[i].id == id) return &W[i];
    return NULL;
}
static double f_getf(const void *o, int f, int i) {
    const FV *v = o;
    switch (f) {
    case CC2X_VEHICLE_ID: return v->id;
    case CC2X_VEHICLE_DEFINITION: return v->def;
    case CC2X_VEHICLE_TEAM: return v->team;
    case CC2X_VEHICLE_TEAM_IS_AI: return v->is_ai;
    case CC2X_VEHICLE_IS_WING: return v->is_wing;
    case CC2X_VEHICLE_IS_ROTOR: return v->is_rotor;
    case CC2X_VEHICLE_ATTACHED_TO: return v->attached;
    case CC2X_VEHICLE_DOCK_STATE: return v->dock;
    case CC2X_VEHICLE_FLIGHT_STATE: return v->flight;
    case CC2X_VEHICLE_CONTROL_MODE: return v->mode;
    case CC2X_VEHICLE_CONTROL_TAXI: return v->taxi;
    case CC2X_VEHICLE_CONTROL_POWER: return v->power;
    case CC2X_VEHICLE_CONTROL_SPEED: return v->ctrl_speed;
    case CC2X_VEHICLE_CONTROL_TARGET: return v->target[i];
    case CC2X_VEHICLE_DOCK_VEHICLE: return v->dock_vehicle;
    case CC2X_VEHICLE_POS: return v->pos[i];
    case CC2X_VEHICLE_WHEEL_CONTACT: return v->contact[i];
    case CC2X_VEHICLE_FUEL: return v->fuel;
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
static void f_brakes(void *o, float b, float g) { calls[ncalls].id = ((FV *)o)->id; calls[ncalls].b = b; calls[ncalls++].g = g; }
static int nset;
static int f_setf(void *o, int f, int i, double val) {
    (void)i;
    if (f != CC2X_VEHICLE_CONTROL_POWER) return 0;
    ((FV *)o)->power = val; nset++;
    return 1;
}
static int n_patch_begin, n_patch_mid, n_patch_commit, n_patch_abort, patch_mid_fail, patch_commit_fail;
static uint32_t pm_site[10], pm_len[10];
static uint8_t pm_exp[10][16];
static cc2x_mid_fn pm_fn[10];
static void *pm_user[10];
static void f_patch_begin(const char *who) { n_patch_begin++; (void)who; }
static int f_patch_mid(uint32_t site, uint32_t len, const uint8_t *expected, cc2x_mid_fn fn, void *user) {
    if (patch_mid_fail || n_patch_mid >= 10) return 0;
    pm_site[n_patch_mid] = site; pm_len[n_patch_mid] = len; memcpy(pm_exp[n_patch_mid], expected, len); pm_fn[n_patch_mid] = fn; pm_user[n_patch_mid] = user;
    n_patch_mid++;
    return 1;
}
static int f_patch_commit(void) { n_patch_commit++; return !patch_commit_fail; }
static void f_patch_abort(void) { n_patch_abort++; }
static uintptr_t f_va(uint32_t image_va) { return (uintptr_t)image_va + 0x10000u; }
static uint8_t t_mgr[0x100] __attribute__((aligned(16))), t_frame[0x400] __attribute__((aligned(16)));
static cc2x_cpu t_cpu;
static int t_untouched, t_zone = 1;
static float t_x = 3.5f, t_y = -6.5f;
static void run_h1(const uint32_t *el) {
    memset(&t_cpu, 0, sizeof(t_cpu)); t_cpu.eax = (uint32_t)(uintptr_t)el; t_cpu.edi = (uint32_t)(uintptr_t)t_mgr;
    pm_fn[0](&t_cpu, NULL);
}
static void run_h2(void) {
    memset(&t_cpu, 0, sizeof(t_cpu)); t_cpu.edi = (uint32_t)(uintptr_t)t_mgr;
    pm_fn[1](&t_cpu, NULL);
}
static void run_h3(const void *plane_ptr, int32_t bay, uint32_t flag, float z, int32_t rstate, uint32_t counter) {
    uint8_t *ebp = t_frame + 0x300, fsnap[sizeof(t_frame)], msnap[sizeof(t_mgr)];
    memset(&t_cpu, 0, sizeof(t_cpu));
    *(uint32_t *)(ebp - 0x1fc) = (uint32_t)(uintptr_t)plane_ptr;
    *(uint32_t *)(ebp - 0x224) = flag;
    memcpy(ebp - 0x278, &z, 4);
    *(uint8_t *)(ebp - 0x205) = (uint8_t)t_zone; memcpy(ebp - 0x2cc, &t_x, 4); memcpy(ebp - 0x270, &t_y, 4);
    *(int32_t *)(t_mgr + 0x1c) = rstate; *(uint32_t *)(t_mgr + 0xd4) = counter;
    t_cpu.ebp = (uint32_t)(uintptr_t)ebp; t_cpu.eax = (uint32_t)bay; t_cpu.edi = (uint32_t)(uintptr_t)t_mgr;
    memcpy(fsnap, t_frame, sizeof(fsnap)); memcpy(msnap, t_mgr, sizeof(msnap));
    pm_fn[2](&t_cpu, NULL);
    t_untouched = memcmp(fsnap, t_frame, sizeof(fsnap)) == 0 && memcmp(msnap, t_mgr, sizeof(msnap)) == 0;
}
static void run_probe(int idx, const void *plane_ptr, float a, float b, float c) {
    uint8_t *ebp = t_frame + 0x300, fsnap[sizeof(t_frame)], msnap[sizeof(t_mgr)];
    memset(&t_cpu, 0, sizeof(t_cpu));
    *(uint32_t *)(ebp - 0x1fc) = (uint32_t)(uintptr_t)plane_ptr;
    memcpy(ebp - 0x294, &a, 4); memcpy(ebp - 0x244, &b, 4); memcpy(ebp - 0x284, &c, 4);
    t_cpu.ebp = (uint32_t)(uintptr_t)ebp; t_cpu.edi = (uint32_t)(uintptr_t)t_mgr; t_cpu.eax = 0x1234; t_cpu.ecx = 0x5678; t_cpu.edx = 0x9abc;
    memcpy(fsnap, t_frame, sizeof(fsnap)); memcpy(msnap, t_mgr, sizeof(msnap));
    pm_fn[idx](&t_cpu, pm_user[idx]);
    t_untouched = memcmp(fsnap, t_frame, sizeof(fsnap)) == 0 && memcmp(msnap, t_mgr, sizeof(msnap)) == 0 &&
                  t_cpu.eax == 0x1234 && t_cpu.ecx == 0x5678 && t_cpu.edx == 0x9abc && t_cpu.jump_to == 0 && t_cpu.eflags == 0 && t_cpu.ebp == (uint32_t)(uintptr_t)ebp;
}
/* v12, H5 at index 7 (the old H4 site) and the take-over probe at index 8. The game's frame at H5: the aircraft at [ebp-0x1fc] (and in edi), the landing manager at
 * [ebp-0x204] ([+0x1c] runway state, [+0x58] lift owner, [+0x5c] runway owner, [+0xd4] approach counter), the carrier at [ebp-0x200], the distance (float) at [ebp-0x25c],
 * the two velocity vectors of the touch test P = [ebp-0x2e4], [ebp-0x234], [ebp-0x23c] and Q = [ebp-0x2dc], [ebp-0x2d4], [ebp-0x2a4]. The fake carrier: model at +0x88
 * ([+0xe0] node table of 64-byte entries, class at +0x3c, [+0xe4] count, [+0xe8] first index, [+0xec] bay limit), bays at +0x154 (0x70 bytes, occupant +0x64), count +0x158.
 * The fake aircraft (an FV) carries the game's fields at their offsets in its padding: +0xac wheels (0x70 bytes each: +0 contact, +4 the second field), +0xb0 count,
 * +0x188 preferred bay. */
static uint8_t t_ship[0x200] __attribute__((aligned(16))), t_model[0x100] __attribute__((aligned(16))), t_nodes[64 * 16] __attribute__((aligned(16))),
    t_bays[0x70 * 12] __attribute__((aligned(16))), t_wheels[0x70 * 3] __attribute__((aligned(16)));
static uintptr_t t_h5_mgr, t_h5_ship;   /* 0 = the fakes; else the pointer the frame holds instead (e.g. an unreadable one) */
static float t_rel = 0.1f;              /* speed of the aircraft relative to the carrier in the game's frame */
static int t_h5_changed;                /* bytes of the game's memory (frame, manager, carrier, model, nodes, bays, wheels) that a hook changed */
static int t_first = 2;                 /* first index of the bays in the model's node table */
static void fake_carrier(int nbays, int first) {
    memset(t_ship, 0, sizeof(t_ship)); memset(t_model, 0, sizeof(t_model)); memset(t_nodes, 0, sizeof(t_nodes)); memset(t_bays, 0, sizeof(t_bays));
    t_first = first;
    *(uint32_t *)(t_ship + 0x88) = (uint32_t)(uintptr_t)t_model; *(uint32_t *)(t_ship + 0x154) = (uint32_t)(uintptr_t)t_bays; *(uint32_t *)(t_ship + 0x158) = (uint32_t)nbays;
    *(uint32_t *)(t_model + 0xe0) = (uint32_t)(uintptr_t)t_nodes; *(uint32_t *)(t_model + 0xe4) = 16; *(uint32_t *)(t_model + 0xe8) = (uint32_t)first;
    *(int32_t *)(t_model + 0xec) = nbays;
    for (int i = 0; i < nbays; ++i) *(uint32_t *)(t_nodes + ((first + i) % 16) * 64 + 0x3c) = 1;
}
static void bay_set(int i, uint32_t occupant, uint32_t cls) {
    *(uint32_t *)(t_bays + i * 0x70 + 0x64) = occupant; *(uint32_t *)(t_nodes + ((t_first + i) % 16) * 64 + 0x3c) = cls;
}
static void plane_raw(FV *v, int pref) {
    uint8_t *r = (uint8_t *)v;
    memset(t_wheels, 0, sizeof(t_wheels));
    for (int i = 0; i < 3; ++i) { float c = 0.05f, s = 0.0f; memcpy(t_wheels + i * 0x70, &c, 4); memcpy(t_wheels + i * 0x70 + 4, &s, 4); }
    *(uint32_t *)(r + 0xac) = (uint32_t)(uintptr_t)t_wheels; *(uint32_t *)(r + 0xb0) = 3; r[0x188] = (uint8_t)pref;
}
static size_t game_mem(uint8_t *dst) {          /* concatenation of every fake block of the game's memory a hook could touch */
    size_t n = 0;
#define GM(b) do { if (dst) memcpy(dst + n, b, sizeof(b)); n += sizeof(b); } while (0)
    GM(t_frame); GM(t_mgr); GM(t_ship); GM(t_model); GM(t_nodes); GM(t_bays); GM(t_wheels);
#undef GM
    return n;
}
static uint8_t t_snap[0x4000], t_after[0x4000];
static int game_mem_changed(void) {
    size_t n = game_mem(t_after);
    int c = 0;
    for (size_t i = 0; i < n; ++i) if (t_snap[i] != t_after[i]) c++;
    return c;
}
static void prep_h5(const void *plane_ptr, uint32_t edi, int32_t rstate, int32_t owner) {
    uint8_t *ebp = t_frame + 0x300;
    float dist = 20.0f, ps[3] = {0.0f, 0.0f, 31.6f}, qs[3] = {0.0f, 0.0f, 31.6f};
    qs[2] += t_rel;
    memset(&t_cpu, 0, sizeof(t_cpu));
    *(uint32_t *)(ebp - 0x1fc) = (uint32_t)(uintptr_t)plane_ptr;
    *(uint32_t *)(ebp - 0x204) = (uint32_t)(t_h5_mgr ? t_h5_mgr : (uintptr_t)t_mgr);
    *(uint32_t *)(ebp - 0x200) = (uint32_t)(t_h5_ship ? t_h5_ship : (uintptr_t)t_ship);
    *(uint8_t *)(ebp - 0x205) = 0;
    memcpy(ebp - 0x25c, &dist, 4);
    memcpy(ebp - 0x2e4, &ps[0], 4); memcpy(ebp - 0x234, &ps[1], 4); memcpy(ebp - 0x23c, &ps[2], 4);
    memcpy(ebp - 0x2dc, &qs[0], 4); memcpy(ebp - 0x2d4, &qs[1], 4); memcpy(ebp - 0x2a4, &qs[2], 4);
    *(int32_t *)(t_mgr + 0x1c) = rstate; *(int32_t *)(t_mgr + 0x5c) = owner; *(int32_t *)(t_mgr + 0x58) = -1; *(uint32_t *)(t_mgr + 0xd4) = 7;
    t_cpu.ebp = (uint32_t)(uintptr_t)ebp; t_cpu.edi = edi; t_cpu.eax = 0x1234; t_cpu.ecx = 0x5678; t_cpu.edx = 0x9abc; t_cpu.esi = 0x1111; t_cpu.ebx = 0x2222;
}
/* Runs H5 and records what changed: t_h5_changed = bytes of the game's memory; t_untouched = eax, ecx, edx, ebx, ebp and the flags as before
 * (H5 may set only edi, esi and jump_to). */
static void run_h5(const void *plane_ptr, uint32_t edi, int32_t rstate, int32_t owner) {
    prep_h5(plane_ptr, edi, rstate, owner);
    game_mem(t_snap);
    pm_fn[7](&t_cpu, pm_user[7]);
    t_h5_changed = game_mem_changed();
    t_untouched = t_cpu.eax == 0x1234 && t_cpu.ecx == 0x5678 && t_cpu.edx == 0x9abc && t_cpu.ebx == 0x2222 && t_cpu.eflags == 0 &&
                  t_cpu.ebp == (uint32_t)(uintptr_t)(t_frame + 0x300);
}
/* The take-over probe (index 8): at 0x6ff379 eax = the bay the game got, edi = the manager, esi = the carrier. t_untouched = nothing changed at all. */
static void run_cap(const void *plane_ptr, int32_t bay) {
    uint8_t *ebp = t_frame + 0x300;
    memset(&t_cpu, 0, sizeof(t_cpu));
    *(uint32_t *)(ebp - 0x1fc) = (uint32_t)(uintptr_t)plane_ptr;
    t_cpu.ebp = (uint32_t)(uintptr_t)ebp; t_cpu.eax = (uint32_t)bay; t_cpu.edi = (uint32_t)(uintptr_t)t_mgr; t_cpu.esi = (uint32_t)(uintptr_t)t_ship;
    t_cpu.ecx = 0x5678; t_cpu.edx = 0x9abc; t_cpu.ebx = 0x2222;
    game_mem(t_snap);
    pm_fn[8](&t_cpu, pm_user[8]);
    t_untouched = game_mem_changed() == 0 && t_cpu.eax == (uint32_t)bay && t_cpu.edi == (uint32_t)(uintptr_t)t_mgr && t_cpu.esi == (uint32_t)(uintptr_t)t_ship &&
                  t_cpu.ecx == 0x5678 && t_cpu.edx == 0x9abc && t_cpu.ebx == 0x2222 && t_cpu.eflags == 0 && t_cpu.jump_to == 0 && t_cpu.ebp == (uint32_t)(uintptr_t)ebp;
}
static uint32_t t_stamp = 0x6a36c177u;  /* the PE timestamp the plugin reads (g_exe_stamp points here in the test) */
static uint32_t fake_stamp(void) { return t_stamp; }
static void clobber_xmm4(cc2x_cpu *cpu, void *user) { (void)cpu; (void)user; __asm__ volatile("xorps %%xmm4, %%xmm4" ::: "xmm4"); }
static uint32_t xp_pat[8][4], xp_out[8][4];
/* Calls fn(cpu, user) exactly like the SDK's relay does (cdecl) with xmm0-xmm7 loaded with patterns, and returns 1 if they are unchanged afterwards. */
static int xmm_survives(cc2x_mid_fn fn, cc2x_cpu *cpu, void *user) {
    uintptr_t ra = (uintptr_t)cpu, rc = (uintptr_t)user, rd = 0;
    for (int i = 0; i < 8; ++i) for (int j = 0; j < 4; ++j) xp_pat[i][j] = 0x01010101u * (uint32_t)(i * 4 + j + 1);
    memset(xp_out, 0, sizeof(xp_out));
    __asm__ volatile(
        "movups 0(%%ebx), %%xmm0\n\t" "movups 16(%%ebx), %%xmm1\n\t" "movups 32(%%ebx), %%xmm2\n\t" "movups 48(%%ebx), %%xmm3\n\t"
        "movups 64(%%ebx), %%xmm4\n\t" "movups 80(%%ebx), %%xmm5\n\t" "movups 96(%%ebx), %%xmm6\n\t" "movups 112(%%ebx), %%xmm7\n\t"
        "pushl %%ecx\n\t" "pushl %%eax\n\t" "call *%%edi\n\t" "addl $8, %%esp\n\t"
        "movups %%xmm0, 0(%%esi)\n\t" "movups %%xmm1, 16(%%esi)\n\t" "movups %%xmm2, 32(%%esi)\n\t" "movups %%xmm3, 48(%%esi)\n\t"
        "movups %%xmm4, 64(%%esi)\n\t" "movups %%xmm5, 80(%%esi)\n\t" "movups %%xmm6, 96(%%esi)\n\t" "movups %%xmm7, 112(%%esi)\n\t"
        : "+a"(ra), "+c"(rc), "+d"(rd)
        : "b"(&xp_pat[0][0]), "S"(&xp_out[0][0]), "D"(fn)
        : "memory", "cc", "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7");
    return memcmp(xp_pat, xp_out, sizeof(xp_pat)) == 0;
}
static void f_on_tick(void (*fn)(void *, void *), void *u) { tick_fn = fn; (void)u; }
static void f_on_session(void (*fn)(void *, int, void *), void *u) { sess_fn = fn; (void)u; }

static cc2x_api api;

static void write_ini(const char *text) {
    char p[MAX_PATH * 2];
    snprintf(p, sizeof(p), "%s\\frein.ini", ini_dir);
    if (!text) { remove(p); return; }
    FILE *f = fopen(p, "wb");
    fputs(text, f);
    fclose(f);
}
static void begin(const char *ini) {          /* new scenario: world, calls, log, plugin state */
    memset(W, 0, sizeof(W)); NW = 0; ncalls = 0; nset = 0; logbuf[0] = 0;
    write_ini(ini);
    sess_fn(NULL, 1, NULL);
}
static FV *add(uint32_t id, uint32_t def, uint32_t team) {
    FV *v = &W[NW++];
    v->id = id; v->def = def; v->team = team; v->alive = 1;
    if (def == 8) { v->is_wing = 1; v->nw = 3; v->flight = 1; }
    return v;
}
static FV *carrier(void) { FV *c = add(1, 0, 1); c->pos[1] = 10; return c; }
static FV *plane(uint32_t id) { FV *p = add(id, 8, 1); p->pos[0] = -30; p->pos[1] = 12; return p; }
static void step(int n) { for (int i = 0; i < n; ++i) tick_fn(NULL, NULL); }
static void wheels(FV *p, float c0, float c1, float c2) { p->contact[0] = c0; p->contact[1] = c1; p->contact[2] = c2; }
static void air(FV *p, int ticks) { wheels(p, 0, 0, 0); p->flight = 2; step(ticks); }
static void ground(FV *p) { wheels(p, 1, 1, 1); p->flight = 1; }
static int nb(uint32_t id) { int n = 0; for (int i = 0; i < ncalls; ++i) if (calls[i].id == id && calls[i].b > 0) n++; return n; }
static int nr(uint32_t id) { int n = 0; for (int i = 0; i < ncalls; ++i) if (calls[i].id == id && calls[i].b == 0 && calls[i].g == 1.0f) n++; return n; }
static int has(const char *s) { return strstr(logbuf, s) != NULL; }
static int count(const char *s) { int n = 0; for (const char *q = logbuf; (q = strstr(q, s)); q += strlen(s)) n++; return n; }

#define ON "[frein]\nbrake_enabled=1\n"

int main(int argc, char **argv) {
    if (argc < 2) { puts("usage: test_frein <folder>"); return 2; }
    snprintf(ini_dir, sizeof(ini_dir), "%s", argv[1]);
    verbose = argc > 2 && !strcmp(argv[2], "-v");
    api.api_version = CC2X_API_VERSION; api.size = sizeof(cc2x_api); api.game_build = "1.5.18-win32"; api.config_dir = ini_dir;
    api.log = f_log; api.count = f_count; api.ref = f_ref; api.find = f_find; api.geti = f_geti; api.getf = f_getf;
    api.setf = f_setf; api.body_get = f_body_get; api.patch_begin = f_patch_begin; api.patch_mid = f_patch_mid; api.patch_commit = f_patch_commit;
    api.patch_abort = f_patch_abort; api.va = f_va; api.vehicle_brakes = f_brakes; api.on_server_tick = f_on_tick; api.on_session = f_on_session;
    g_exe_stamp = fake_stamp;

    puts("load checks");
    api.game_build = "1.5.19-win32"; CHECK(cc2x_plugin_load(&api) == 0, "wrong build must be refused");
    api.game_build = "1.5.18-win32"; api.api_version = 2; CHECK(cc2x_plugin_load(&api) == 0, "API 2 must be refused");
    api.api_version = CC2X_API_VERSION; api.size = 8; CHECK(cc2x_plugin_load(&api) == 0, "short API struct must be refused");
    api.size = sizeof(cc2x_api); write_ini(NULL); CHECK(cc2x_plugin_load(&api) == 1 && tick_fn && sess_fn, "good load");
    CHECK(n_patch_begin == 0 && n_patch_mid == 0 && n_patch_commit == 0 && g_hooks_ok == 0, "v8: without recall_force=1 at start-up NOTHING of the game is patched (%d, %d, %d)", n_patch_begin, n_patch_mid, n_patch_commit);
    t_stamp = 0x6ae228f3u; logbuf[0] = 0;
    CHECK(cc2x_plugin_load(&api) == 0 && has("not loaded: the SDK says build 1.5.18-win32 but the exe has PE timestamp 0x6ae228f3 (expected 0x6a36c177)"), "v12: the 1.5.18 build name on the new exe is refused, and said");
    api.game_build = "1.5.18-win32-6ae228f3"; t_stamp = 0x6a36c177u; logbuf[0] = 0;
    CHECK(cc2x_plugin_load(&api) == 0 && has("expected 0x6ae228f3"), "v12: the new build name on the 1.5.18 exe is refused");
    api.game_build = NULL; CHECK(cc2x_plugin_load(&api) == 0, "v12: no build name: refused");
    api.game_build = "1.5.18-win32"; logbuf[0] = 0;
    CHECK(cc2x_plugin_load(&api) == 1 && S == &k_builds[0] && has("loaded (frein v12, build 1.5.18-win32, exe 0x6a36c177)"), "v12: good load again, table of the 1.5.18 exe");

    puts("T1 no ini: observation only, never brakes");
    begin(NULL); carrier(); FV *p = plane(10);
    air(p, 60); ground(p); step(120);
    CHECK(ncalls == 0, "no brake call without ini (%d)", ncalls);
    CHECK(has("eligible=1"), "the aircraft is seen eligible in the log");
    CHECK(has("brake_enabled=0"), "settings logged as disabled");

    puts("T2 brake on: landing is braked each tick, released when it takes off again");
    begin(ON); carrier(); p = plane(10); p->vel[2] = 40;
    air(p, 60); CHECK(ncalls == 0, "no brake in flight");
    ground(p); step(30);
    CHECK(nb(10) == 30, "brake every tick on the ground (%d)", nb(10));
    CHECK(calls[0].b == 1.0f && calls[0].g == 1.0f, "values 1.0 / 1.0 (%.2f %.2f)", calls[0].b, calls[0].g);
    CHECK(has("BRAKE start"), "start logged");
    air(p, 1);
    CHECK(nr(10) == 1, "released once (0, 1.0) when a wheel leaves the ground (%d)", nr(10));
    CHECK(has("BRAKE released"), "release logged");
    int before = ncalls; step(10); CHECK(ncalls == before, "no more calls after release");

    puts("T3 stop detection");
    begin(ON); carrier(); p = plane(10); air(p, 60); ground(p); p->vel[2] = 20; step(5); p->vel[2] = 0; step(5);
    CHECK(has("STOPPED"), "stop logged");

    puts("T4 takeoff roll is never braked (never flew)");
    begin(ON); carrier(); p = plane(10); ground(p); p->vel[2] = 5; step(200);
    CHECK(ncalls == 0, "no brake on a takeoff roll (%d)", ncalls);
    p->vel[2] = 45; air(p, 100); CHECK(ncalls == 0, "no brake after lift-off (%d)", ncalls);

    puts("T4b need_airborne=0 brakes an aircraft already on the ground");
    begin(ON "need_airborne=0\n"); carrier(); p = plane(10); ground(p); step(5);
    CHECK(nb(10) == 5, "braked without having flown (%d)", nb(10));

    puts("T5 never touch: AI team, attached, docking states, helicopter");
    begin(ON); carrier(); p = plane(10); p->is_ai = 1; air(p, 60); ground(p); step(20); CHECK(ncalls == 0, "AI team");
    begin(ON); carrier(); p = plane(10); air(p, 60); ground(p); p->attached = 1; step(20); CHECK(ncalls == 0, "attached");
    for (uint32_t d = 1; d <= 7; ++d) { begin(ON); carrier(); p = plane(10); air(p, 60); ground(p); p->dock = d; step(10); CHECK(ncalls == 0, "dock state %u", d); }
    begin(ON); carrier(); p = plane(10); p->is_wing = 0; p->is_rotor = 1; air(p, 60); ground(p); step(20); CHECK(ncalls == 0, "helicopter");

    puts("T5b attached / docked aircraft must re-fly before being braked again");
    begin(ON); carrier(); p = plane(10); air(p, 60); ground(p); p->attached = 1; step(5); p->attached = 0; step(20);
    CHECK(ncalls == 0, "disarmed by the game's handling (%d)", ncalls);

    puts("T6 zone and height");
    begin(ON); carrier(); p = plane(10); p->pos[0] = 400; air(p, 60); ground(p); step(20); CHECK(ncalls == 0, "400 m away");
    begin(ON); carrier(); p = plane(10); air(p, 60); ground(p); p->pos[1] = 60; step(20); CHECK(ncalls == 0, "50 m above");
    begin(ON "zone_m=500\n"); carrier(); p = plane(10); p->pos[0] = 400; air(p, 60); ground(p); step(20); CHECK(nb(10) == 20, "zone_m=500 includes 400 m (%d)", nb(10));

    puts("T7 wheels");
    begin(ON); carrier(); p = plane(10); air(p, 60); p->flight = 1; wheels(p, 1, 1, 0); step(20); CHECK(ncalls == 0, "one wheel in the air");
    wheels(p, 1, 1, 0.005f); step(5); CHECK(ncalls == 0, "contact below the game's 0.01 threshold");
    wheels(p, 1, 1, 0.5f); step(5); CHECK(nb(10) == 5, "all wheels touching (%d)", nb(10));

    puts("T8 only_id");
    begin(ON "only_id=11\n"); carrier(); FV *a = plane(10), *b2 = plane(11);
    air(a, 1); wheels(b2, 0, 0, 0); b2->flight = 2; step(60); ground(a); ground(b2); step(10);
    CHECK(nb(10) == 0 && nb(11) == 10, "only aircraft 11 braked (%d / %d)", nb(10), nb(11));

    puts("T9 brake_enabled turned off while braking releases within 3 s");
    begin(ON); carrier(); p = plane(10); air(p, 60); ground(p); step(10); CHECK(nb(10) == 10, "braking");
    write_ini("[frein]\nbrake_enabled=0\n"); step(95);
    CHECK(nr(10) == 1, "released once (%d)", nr(10)); CHECK(has("brake_enabled=0"), "new settings logged");

    puts("T10 settings: clamped, comma accepted");
    begin(ON "brake=5\ngrip=-2\n"); carrier(); p = plane(10); air(p, 60); ground(p); step(3);
    CHECK(calls[0].b == 1.0f && calls[0].g == 0.0f, "brake 5 -> 1, grip -2 -> 0 (%.2f %.2f)", calls[0].b, calls[0].g);
    begin(ON "brake=0,5\ngrip=0,25\n"); carrier(); p = plane(10); air(p, 60); ground(p); step(3);
    CHECK(calls[0].b == 0.5f && calls[0].g == 0.25f, "comma decimals (%.2f %.2f)", calls[0].b, calls[0].g);
    begin("[frein]\nbrake_enabled=abc\n"); carrier(); p = plane(10); air(p, 60); ground(p); step(3); CHECK(ncalls == 0, "garbage = off");

    puts("T11 flight_state requirement");
    begin(ON); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 1, 1); p->flight = 2; step(10); CHECK(ncalls == 0, "flight state 2 refused by default");
    begin(ON "flight_state=-1\n"); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 1, 1); p->flight = 2; step(10); CHECK(nb(10) == 10, "flight_state=-1 accepts it (%d)", nb(10));

    puts("T12 carrier of another team / no carrier");
    begin(ON); FV *c = carrier(); c->team = 2; p = plane(10); air(p, 60); ground(p); step(10); CHECK(ncalls == 0, "enemy carrier");
    begin(ON); p = plane(10); air(p, 60); ground(p); step(10); CHECK(ncalls == 0, "no carrier");
    begin(ON); c = add(1, 1, 1); p = plane(10); air(p, 60); ground(p); step(10); CHECK(ncalls == 0, "broken carrier type is not a carrier");

    puts("T13 aircraft destroyed while braking: no crash, no call on a missing vehicle");
    begin(ON); carrier(); p = plane(10); air(p, 60); ground(p); step(10); p->alive = 0; p->is_wing = 0; int n0 = ncalls; step(3);
    CHECK(ncalls == n0, "no call on a gone vehicle"); CHECK(has("aircraft gone"), "logged");

    puts("T14 carrier moving: relative speed");
    begin(ON); c = carrier(); c->vel[2] = 8; p = plane(10); air(p, 60); ground(p); p->vel[2] = 8; step(3);
    CHECK(has("STOPPED"), "same speed as the carrier = stopped");

    puts("T15 40 human aircraft: no crash");
    begin(ON); carrier(); for (int i = 0; i < 40; ++i) { p = plane(100 + i); air(p, 0); } step(80); for (int i = 1; i <= 40; ++i) ground(&W[i]); step(10);
    CHECK(ncalls > 0 && ncalls <= 40 * 10, "some braked, bounded (%d)", ncalls);

    puts("T16 log cap");
    begin(NULL); carrier(); p = plane(10); air(p, 60); for (int i = 0; i < 20000; ++i) { wheels(p, (float)(i & 1), 1, 1); step(1); }
    CHECK(has("log cap reached"), "cap reached warning"); CHECK(strlen(logbuf) < 1000000, "log buffer bounded");

    puts("T17 min_wheels=2: a normal landing (nose wheel still up) is braked, a takeoff rotation is not");
    begin(ON "min_wheels=2\nflight_state=-1\n"); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 1, 0); p->flight = 2; step(10);
    CHECK(nb(10) == 10, "two main wheels brake with min_wheels=2 (%d)", nb(10));
    begin(ON "min_wheels=2\nflight_state=-1\n"); carrier(); p = plane(10); wheels(p, 1, 1, 0); p->flight = 1; p->vel[2] = 40; step(300);
    CHECK(ncalls == 0, "takeoff rotation on two wheels never arms nor brakes (%d)", ncalls);
    wheels(p, 0, 0, 0); p->flight = 2; step(20); wheels(p, 1, 1, 0); step(10);
    CHECK(ncalls == 0, "less than 1 s in the air after the rotation: still not armed (%d)", ncalls);
    begin(ON "min_wheels=2\nflight_state=-1\n"); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 0, 0); step(10);
    CHECK(ncalls == 0, "one wheel is not enough with min_wheels=2 (%d)", ncalls);
    begin(ON "min_wheels=9\n"); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 1, 0); step(10);
    CHECK(ncalls == 0 && has("min_wheels=8"), "min_wheels clamped to 8, then means every wheel (%d)", ncalls);
    begin(ON); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 1, 0); p->flight = 1; step(10);
    CHECK(ncalls == 0, "default min_wheels=0 still needs every wheel (%d)", ncalls);

    puts("T18 grace_s: the brake is held through a bounce, then released");
    begin(ON "min_wheels=2\ngrace_s=1\nflight_state=-1\n"); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 1, 0); p->flight = 2; step(10);
    CHECK(nb(10) == 10, "braking before the bounce (%d)", nb(10));
    wheels(p, 0, 0, 0); step(20);
    CHECK(nb(10) == 30 && nr(10) == 0, "held 20 ticks through the bounce (%d / %d)", nb(10), nr(10));
    wheels(p, 1, 1, 0); step(5);
    CHECK(nb(10) == 35 && nr(10) == 0 && !has("BRAKE released"), "contact again: still one braking run (%d)", nb(10));
    wheels(p, 0, 0, 0); step(60);
    CHECK(nb(10) == 65 && nr(10) == 1, "held 30 ticks (1 s) then released once (%d / %d)", nb(10), nr(10));
    int held = ncalls; step(20); CHECK(ncalls == held, "nothing after the release");
    begin(ON "min_wheels=2\ngrace_s=1\nflight_state=-1\n"); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 1, 0); p->flight = 2; step(5);
    wheels(p, 0, 0, 0); step(3); p->attached = 1; step(1);
    CHECK(nr(10) == 1, "attached during the grace period: released at once (%d)", nr(10));
    begin(ON "min_wheels=2\ngrace_s=1\nflight_state=-1\n"); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 1, 0); p->flight = 2; step(5);
    wheels(p, 0, 0, 0); p->pos[0] = 400; step(2);
    CHECK(nr(10) == 1, "left the zone during the grace period: released at once (%d)", nr(10));
    begin(ON "min_wheels=2\ngrace_s=99\nflight_state=-1\n"); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 1, 0); p->flight = 2; step(2);
    wheels(p, 0, 0, 0); step(200); CHECK(nr(10) == 1 && has("grace_s=5.0"), "grace_s clamped to 5 s (%d)", nr(10));
    begin(ON); carrier(); p = plane(10); air(p, 60); ground(p); step(5); wheels(p, 0, 0, 0); step(5);
    CHECK(nr(10) == 1 && nb(10) == 5, "default grace_s=0 releases at once (%d / %d)", nr(10), nb(10));

    puts("T19 height_m: a small bounce above the deck (dy 20.2) must not drop the brake");
    begin(ON "min_wheels=2\nflight_state=-1\ngrace_s=1\n"); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 1, 0); p->pos[1] = 10 + 19.8; step(5);
    CHECK(nb(10) == 5, "braking at the deck level (%d)", nb(10));
    wheels(p, 0, 0, 0); p->pos[1] = 10 + 20.2; step(10);
    CHECK(nr(10) == 1 && nb(10) == 5, "default height 20 m: bounce to 20.2 leaves the zone, released at once (%d / %d)", nr(10), nb(10));
    begin(ON "min_wheels=2\nflight_state=-1\ngrace_s=1\nheight_m=40\n"); carrier(); p = plane(10); air(p, 60); wheels(p, 1, 1, 0); p->pos[1] = 10 + 19.8; step(5);
    wheels(p, 0, 0, 0); p->pos[1] = 10 + 20.2; step(10);
    CHECK(nb(10) == 15 && nr(10) == 0 && has("height_m=40"), "height_m=40: the brake is held through the bounce (%d / %d)", nb(10), nr(10));
    wheels(p, 1, 1, 0); step(5);
    CHECK(nb(10) == 20 && nr(10) == 0, "and keeps braking when the wheels touch again (%d)", nb(10));
    p->pos[1] = 10 + 80; step(3);
    CHECK(nr(10) == 1, "far above the zone (70 m): released (%d)", nr(10));
    begin(ON "height_m=1\n"); carrier(); p = plane(10); air(p, 60); ground(p); p->pos[1] = 10 + 7; step(3);
    CHECK(ncalls == 0 && has("height_m=5"), "height_m clamped to 5 m (%d)", ncalls);

    puts("T20 max_speed: no braking above the limit, braking below");
    begin(ON "max_speed=30\n"); c = carrier(); p = plane(10); air(p, 60); ground(p); p->vel[2] = 53; step(10);
    CHECK(ncalls == 0 && has("max_speed=30"), "53 m/s relative with max_speed=30: not braked (%d)", ncalls);
    p->vel[2] = 25; step(10); CHECK(nb(10) == 10, "slowed to 25 m/s relative: braking starts (%d)", nb(10));
    p->vel[2] = 31; step(2); CHECK(nr(10) == 1, "back above the limit: released (%d)", nr(10));
    begin(ON "max_speed=30\n"); c = carrier(); c->vel[2] = 32; p = plane(10); air(p, 60); ground(p); p->vel[2] = 53; step(10);
    CHECK(nb(10) == 10, "the limit is on the speed RELATIVE to the carrier (21 m/s here) (%d)", nb(10));
    begin(ON); c = carrier(); p = plane(10); air(p, 60); ground(p); p->vel[2] = 200; step(5);
    CHECK(nb(10) == 5, "default max_speed=0: no limit (%d)", nb(10));
    begin(ON "max_speed=-5\n"); c = carrier(); p = plane(10); air(p, 60); ground(p); p->vel[2] = 200; step(5);
    CHECK(nb(10) == 5, "negative max_speed = no limit (%d)", nb(10));

    puts("T21 hold_brake: parked on the deck, the brake goes up and stays up (latched)");
    begin(ON "brake=0.1\nhold_brake=0.8\n"); carrier(); p = plane(10); air(p, 60); ground(p); p->vel[2] = 20; step(5);
    CHECK(ncalls == 5 && calls[4].b == 0.1f, "moving: base brake 0.1 (%d, %.2f)", ncalls, calls[4].b);
    p->vel[2] = 0.5; step(3);
    CHECK(ncalls == 8 && calls[7].b == 0.8f && has("HOLD") && has("hold_brake=0.80"), "slower than 1 m/s: hold brake 0.8 (%d, %.2f)", ncalls, calls[7].b);
    p->vel[2] = 4; step(3);
    CHECK(ncalls == 11 && calls[10].b == 0.8f, "pushed again: still held, latched (%.2f)", calls[10].b);
    wheels(p, 0, 0, 0); step(40);
    CHECK(nr(10) == 1, "takes off: released once (%d)", nr(10));
    ground(p); p->vel[2] = 20; step(2);
    CHECK(calls[ncalls - 1].b == 0.1f, "next landing starts again at the base brake (%.2f)", calls[ncalls - 1].b);
    begin(ON "brake=0.1\n"); carrier(); p = plane(10); air(p, 60); ground(p); p->vel[2] = 0.5; step(3);
    CHECK(ncalls == 3 && calls[2].b == 0.1f && !has("HOLD"), "default: no hold brake (%.2f)", calls[2].b);
    begin(ON "brake=0.5\nhold_brake=0.3\n"); carrier(); p = plane(10); air(p, 60); ground(p); p->vel[2] = 0.5; step(3);
    CHECK(ncalls == 3 && calls[2].b == 0.5f && !has("HOLD"), "hold_brake below brake is ignored (%.2f)", calls[2].b);
    begin(ON "brake=0.1\nhold_brake=5\n"); carrier(); p = plane(10); air(p, 60); ground(p); p->vel[2] = 0; step(3);
    CHECK(calls[2].b == 1.0f && has("hold_brake=1.00"), "hold_brake clamped to 1 (%.2f)", calls[2].b);
    begin(ON "brake=0.1\nhold_brake=0.8\n"); carrier(); p = plane(10); air(p, 60); ground(p); p->vel[2] = 0; step(3); p->dock = 5; step(1);
    CHECK(nr(10) == 1, "the game takes it over (dock 5): released at once (%d)", nr(10));

    puts("T22 hold_idle: held aircraft in AI control gets its engine idled, the game's value is given back");
    begin(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 20; step(5);
    CHECK(nset == 0 && p->power == 1.0, "still moving (not held): engine untouched (%d, %.2f)", nset, p->power);
    p->vel[2] = 0.5; p->mode = 1; step(5);
    CHECK(nset == 0 && p->power == 1.0, "held but the pilot is in control (mode 1): engine untouched (%d, %.2f)", nset, p->power);
    p->mode = 0; step(1);
    CHECK(nset == 1 && p->power == 0.0 && has("IDLE (AI in control, engine power 1.00 -> 0)") && has("hold_idle=1"), "pilot gone: power 0 (%d, %.2f)", nset, p->power);
    for (int k = 0; k < 40; ++k) { p->power = 1.0; step(1); }
    CHECK(nset == 41 && p->power == 0.0 && has("IDLE check after 1 s: power read 1.00"), "the game puts 1.0 back each tick: we write 0 each tick (%d, %.2f)", nset, p->power);
    p->mode = 1; step(1);
    CHECK(p->power == 1.0 && has("IDLE ended (no longer in AI control), engine power back to 1.00"), "pilot back: the saved power is restored (%.2f)", p->power);
    step(3); CHECK(nset == 42 && p->power == 1.0, "and nothing more is written (%d)", nset);

    begin(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\n"); carrier(); p = plane(10); p->power = 0.7; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    CHECK(p->power == 0.0 && nr(10) == 0, "held at 0.7 power: idled (%.2f)", p->power);
    p->dock = 5; step(1);
    CHECK(nr(10) == 1 && p->power == 0.0 && has("the game takes over (dock 5, attached 0), engine power read 0.00 and left alone"), "v6 recall (dock 5): brake released, the engine is left to the game (%.2f)", p->power);
    step(5); CHECK(p->power == 0.0, "and nothing is written afterwards (%.2f)", p->power);

    begin(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\n"); carrier(); p = plane(10); p->power = 0.7; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->power = 0.4; p->dock = 5; step(1);
    CHECK(p->power == 0.4, "recall: a power the game set itself is not overwritten (%.2f)", p->power);

    begin(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\nmax_speed=30\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    wheels(p, 0, 0, 0); step(300);
    CHECK(p->power == 0.0 && nr(10) == 0 && !has("IDLE ended") && !has("BRAKE released"), "v6: contact lost for 10 s: still held and idle (%.2f, %d)", p->power, nr(10));
    wheels(p, 1, 1, 1); step(3); CHECK(p->power == 0.0 && nr(10) == 0, "contact back: still the same held run (%.2f)", p->power);
    wheels(p, 0, 0, 0); p->vel[2] = 31; step(2);
    CHECK(nr(10) == 1 && p->power == 1.0 && has("IDLE ended (no longer eligible), engine power back to 1.00"), "it rushes off (31 m/s > max_speed 30): released, engine given back (%.2f)", p->power);

    begin(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\n"); carrier(); p = plane(10); p->power = 0.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    CHECK(has("IDLE (AI in control, engine power 0.00 -> 0)"), "started with a power of 0 (saved game): idle starts");
    p->mode = 1; step(1);
    CHECK(p->power == 1.0 && has("engine power back to 1.00"), "a saved 0 is given back as the game's default 1.0 (%.2f)", p->power);

    begin(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\n"); carrier(); p = plane(10); p->power = 0.7; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    sess_fn(NULL, 0, NULL);
    CHECK(p->power == 0.7 && has("IDLE ended (session ended), engine power back to 0.70"), "session ends while idling: the engine is given back (%.2f)", p->power);

    begin(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\n"); carrier(); p = plane(10); p->power = 0.7; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->attached = 1; step(1);
    CHECK(p->power == 0.0 && has("the game takes over (dock 0, attached 1)"), "attached by the game: nothing put back (%.2f)", p->power);

    begin(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    write_ini(ON "brake=0.1\nhold_brake=0.8\nhold_idle=0\n"); step(100);
    CHECK(p->power == 1.0 && has("IDLE ended (no longer held"), "hold_idle set back to 0 in the ini: engine given back (%.2f)", p->power);
    CHECK(has("hold_idle=0"), "new settings logged");

    begin(ON "brake=0.1\nhold_brake=0.8\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(20);
    CHECK(nset == 0 && p->power == 1.0 && !has("IDLE"), "default hold_idle=0: engine never touched (%d, %.2f)", nset, p->power);

    begin(ON "brake=0.1\nhold_idle=1\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(20);
    CHECK(nset == 0, "hold_idle without hold_brake: nothing held, engine untouched (%d)", nset);

    begin(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\n"); carrier(); p = plane(10); p->power = 1.0; p->is_ai = 1; air(p, 60); ground(p); p->vel[2] = 0; step(20);
    CHECK(nset == 0, "AI team aircraft: never touched (%d)", nset);

    begin(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    W[1].alive = 0; NW = 1; step(2);
    CHECK(has("aircraft gone"), "aircraft gone while idled: no crash, logged");

    puts("T23 v7 recall_hold: a held aircraft is not let go at the recall, the game's demands are logged");
#define HELD "brake=0.1\nhold_brake=0.8\nhold_idle=1\n"
    begin(ON HELD "recall_hold=1\nrecall_hold_s=5\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    CHECK(p->power == 0.0 && has("recall_hold=1 recall_hold_s=5 recall_release=0"), "held and idle before the recall, settings logged (%.2f)", p->power);
    p->dock = 5; p->mode = 3; p->nwp = 0; p->ctrl_speed = -5; p->target[0] = 100; p->target[1] = 200; p->target[2] = 300; p->dock_vehicle = 1; step(1);
    CHECK(nr(10) == 0 && p->power == 0.0 && has("RECALL start (dock 5, mode 3, wp 0)") && !has("BRAKE released") && !has("IDLE ended"),
          "recall: brake and idle kept (%d, %.2f)", nr(10), p->power);
    step(35);
    CHECK(has("RECALL +1.0s: mode=3 speed_ctl=-5.0 target=(100,200,300) taxi=0 dock=5 dock_vehicle=1 attached_to=0 flight=1 wp=0"), "the game's demands are logged");
    CHECK(calls[ncalls - 1].id == 10 && calls[ncalls - 1].b == 0.8f, "the hold brake is still applied (%.2f)", calls[ncalls - 1].b);
    for (int k = 0; k < 40; ++k) { p->power = 1.0; step(1); }
    CHECK(p->power == 0.0 && has("power_read=1.00"), "the game writes 1.0 during the recall: we write 0 each tick and log what we read (%.2f)", p->power);
    step(400);
    CHECK(nr(10) == 0 && p->power == 0.0 && !has("RECALL ended"), "recall_release=0: still held after recall_hold_s (%d)", nr(10));
    write_ini(ON HELD "recall_hold=0\n"); step(100);
    CHECK(nr(10) == 1 && has("RECALL ended"), "recall_hold set back to 0 in the ini: let go (%d)", nr(10));

    begin(ON HELD "recall_hold=1\nrecall_hold_s=5\nrecall_release=1\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->dock = 5; p->mode = 3; step(100);
    CHECK(nr(10) == 0 && p->power == 0.0, "recall_release=1: still held within recall_hold_s (%d)", nr(10));
    step(100);
    CHECK(nr(10) == 1 && p->power == 0.0 && has("RECALL ended after 5.0 s") && has("the game takes over (dock 5, attached 0)"),
          "recall_release=1: let go after recall_hold_s, engine left alone (%d, %.2f)", nr(10), p->power);
    p->dock = 0; p->mode = 0; p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->dock = 5; p->mode = 3; step(60);
    CHECK(nr(10) == 1 && p->power == 0.0 && count("RECALL start") == 2, "a second recall is held again: its timer starts from zero (%d, %d)", nr(10), count("RECALL start"));

    begin(ON HELD "recall_hold=1\nrecall_hold_s=5\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->dock = 5; p->mode = 3; step(40); p->dock = 6; p->attached = 1; step(1);
    CHECK(nr(10) == 1 && p->power == 0.0 && has("RECALL ended") && has("the game takes over (dock 6, attached 1)"), "the game takes over during the recall: let go, engine left alone (%d, %.2f)", nr(10), p->power);

    begin(ON HELD "recall_hold=1\nrecall_hold_s=5\n"); carrier(); p = plane(10); p->power = 0.7; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->dock = 5; p->mode = 3; step(40); p->mode = 1; step(1);
    CHECK(nr(10) == 1 && p->power == 0.7 && has("IDLE ended (no longer eligible), engine power back to 0.70"), "the pilot comes back during the recall: engine given back (%d, %.2f)", nr(10), p->power);

    begin(ON HELD "recall_hold=1\nrecall_hold_s=5\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->dock = 5; p->mode = 3; step(40); p->pos[0] = 400; step(1);
    CHECK(nr(10) == 1 && has("RECALL ended") && p->power == 0.0, "it leaves the zone during the recall: let go (%d, %.2f)", nr(10), p->power);

    begin(ON HELD "recall_hold=1\nrecall_hold_s=5\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->dock = 5; p->mode = 3; step(40); p->dock = 3; step(1);
    CHECK(nr(10) == 1 && has("RECALL ended"), "dock state other than 5 during the recall: let go (%d)", nr(10));

    begin(ON HELD "recall_hold=1\nrecall_hold_s=5\nonly_id=77\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->dock = 5; p->mode = 3; step(40);
    CHECK(nr(10) == 0 && nset == 0 && !has("RECALL"), "only_id=77: aircraft 10 is never held nor recalled-held (%d, %d)", nr(10), nset);

    begin(ON "brake=0.1\nhold_brake=0.8\n" "recall_hold=1\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->dock = 5; p->mode = 3; step(40);
    CHECK(nr(10) == 0 && nset == 0 && has("RECALL +"), "recall_hold=1 without hold_idle: brake kept, engine never written (%d, %d)", nr(10), nset);

    begin(ON HELD); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->dock = 5; p->mode = 3; step(40);
    CHECK(nr(10) == 1 && p->power == 0.0 && !has("RECALL ") && has("recall_hold=0"), "default recall_hold=0: let go at the recall like v6 (%d, %.2f)", nr(10), p->power);

    begin(ON HELD "recall_hold=1\nrecall_hold_s=5\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
    p->dock = 5; p->mode = 3; step(40);
    sess_fn(NULL, 0, NULL);
    CHECK(has("IDLE ended (session ended)") && p->power == 0.0, "session ends during the recall: logged, the game owns the engine (%.2f)", p->power);

    puts("T24 v8 recall_force: the two hooks, only for the flagged aircraft, off unless asked for at start-up");
#define FORCED "brake=0.1\nhold_brake=0.8\nhold_idle=1\nrecall_hold=1\nrecall_force=1\n"
    {
        uint8_t mgr[0x80];
        uint32_t el[3], el_other[3];
        cc2x_cpu cpu;
        memset(mgr, 0, sizeof(mgr));

        /* load with recall_force=1: the two hooks, exact sites and bytes, committed */
        write_ini(ON FORCED);
        n_patch_begin = n_patch_mid = n_patch_commit = n_patch_abort = 0; logbuf[0] = 0;
        CHECK(cc2x_plugin_load(&api) == 1 && g_hooks_ok == 1, "load with recall_force=1 installs the hooks");
        CHECK(n_patch_begin == 1 && n_patch_mid == 9 && n_patch_commit == 1 && n_patch_abort == 0, "one transaction, nine hooks (%d, %d, %d, %d)", n_patch_begin, n_patch_mid, n_patch_commit, n_patch_abort);
        CHECK(pm_site[2] == 0x6ff0fb && pm_len[2] == 6 && memcmp(pm_exp[2], "\x8b\x8d\x04\xfe\xff\xff", 6) == 0, "H3 site and expected bytes (mov ecx,[ebp-0x1fc])");
        CHECK(pm_site[0] == 0x7018ce && pm_len[0] == 6 && memcmp(pm_exp[0], "\x8b\x40\x04\x83\xf8\x05", 6) == 0, "H1 site and expected bytes (mov eax,[eax+4]; cmp eax,5)");
        CHECK(pm_site[1] == 0x701a3d && pm_len[1] == 6 && memcmp(pm_exp[1], "\x8d\x85\x28\xfd\xff\xff", 6) == 0, "H2 site and expected bytes (lea eax,[ebp-0x2d8])");
        CHECK(has("hooks H1 (0x7018ce), H2 (0x701a3d), H3 (0x6ff0fb, read only), 4 commit-gate probes (read only), H5 (0x6fe470, sends the aircraft to the touch test 0x6ff20a) and the take-over probe (0x6ff379, read only) installed"), "installation logged");
        CHECK(pm_site[3] == 0x6febda && pm_len[3] == 8 && pm_site[4] == 0x6febe7 && pm_len[4] == 8 && pm_site[5] == 0x6febc0 && pm_len[5] == 8 && pm_site[6] == 0x6fe788 && pm_len[6] == 6,
              "the four probe sites and lengths");
        CHECK(memcmp(pm_exp[3], "\xf3\x0f\x10\x8d\xa4\xfd\xff\xff", 8) == 0 && memcmp(pm_exp[4], pm_exp[3], 8) == 0 && memcmp(pm_exp[5], pm_exp[3], 8) == 0 &&
              memcmp(pm_exp[6], "\x8b\x8d\xb4\xfd\xff\xff", 6) == 0, "probe expected bytes (movss xmm1,[ebp-0x25c] x3 ; mov ecx,[ebp-0x24c])");
        CHECK((intptr_t)pm_user[3] == 1 && (intptr_t)pm_user[4] == 2 && (intptr_t)pm_user[5] == 3 && (intptr_t)pm_user[6] == 4, "probe identifiers");

        /* hooks do nothing before an aircraft is flagged */
        el[0] = 10; el[1] = 0; el[2] = 7; el_other[0] = 11; el_other[1] = 3; el_other[2] = 0;
        *(int32_t *)mgr = 1; *(int32_t *)(mgr + 0x5c) = -1;
        memset(&cpu, 0, sizeof(cpu)); cpu.eax = (uint32_t)(uintptr_t)el; cpu.edi = (uint32_t)(uintptr_t)mgr;
        begin(ON FORCED "recall_hold_s=30\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        pm_fn[0](&cpu, NULL);
        CHECK(cpu.eax == (uint32_t)(uintptr_t)el && cpu.jump_to == 0 && g_h1_count == 0, "H1 inert while nothing is flagged");

        /* recall: held; after 1 s the aircraft is flagged */
        p->dock = 5; p->mode = 3; step(20);
        CHECK(g_force_id == 0 && nr(10) == 0, "recall held < 1 s: not flagged yet (%u)", (unsigned)g_force_id);
        step(15);
        CHECK(g_force_id == 10 && has("FORCE start") && nr(10) == 0 && p->power == 0.0, "flagged after the recall has been held 1 s, brake and idle kept (%u)", (unsigned)g_force_id);

        /* H1 on its element: the game is shown circuit state 1, the real element is untouched */
        memset(&cpu, 0, sizeof(cpu)); cpu.eax = (uint32_t)(uintptr_t)el; cpu.edi = (uint32_t)(uintptr_t)mgr;
        pm_fn[0](&cpu, NULL);
        CHECK(cpu.eax == (uint32_t)(uintptr_t)g_fake_elem && g_fake_elem[0] == 10 && g_fake_elem[1] == 1 && g_fake_elem[2] == 7, "H1: a copy {10, 1, 7} is shown");
        CHECK(el[0] == 10 && el[1] == 0 && el[2] == 7, "H1: the real queue element is NOT written");
        CHECK(g_h1_ours == 1 && g_h1_real_state == 0 && g_h1_mode == 1 && g_h1_slot == -1, "H1: real state, manager mode and runway slot recorded (read only)");

        /* H2 right after, same iteration: the distance test is skipped */
        memset(&cpu, 0, sizeof(cpu)); cpu.edi = (uint32_t)(uintptr_t)mgr;
        pm_fn[1](&cpu, NULL);
        CHECK(cpu.jump_to == 0x701a8a + 0x10000 && g_h2_count == 1 && g_h1_ours == 0, "H2: continue after the 1000 m test (0x701a8a), once");
        memset(&cpu, 0, sizeof(cpu)); cpu.edi = (uint32_t)(uintptr_t)mgr;
        pm_fn[1](&cpu, NULL);
        CHECK(cpu.jump_to == 0 && g_h2_count == 1, "H2 again without a new H1: nothing");
        step(1);
        CHECK(has("HOOK H1 shown circuit state 1 (real element state 0, manager mode 1, runway slot -1)") && has("HOOK H2 skipped the 1000 m test") && has("(try 1 of 3)"), "events logged");

        /* any other aircraft: never touched */
        memset(&cpu, 0, sizeof(cpu)); cpu.eax = (uint32_t)(uintptr_t)el_other; cpu.edi = (uint32_t)(uintptr_t)mgr;
        pm_fn[0](&cpu, NULL);
        CHECK(cpu.eax == (uint32_t)(uintptr_t)el_other && g_h1_ours == 0, "H1: another aircraft's element is left alone");
        memset(&cpu, 0, sizeof(cpu)); cpu.edi = (uint32_t)(uintptr_t)mgr;
        pm_fn[1](&cpu, NULL);
        CHECK(cpu.jump_to == 0, "H2: another aircraft's iteration is left alone");

        /* defensive: manager not in docking mode / runway taken -> no skip, even if flagged */
        *(int32_t *)mgr = 0;
        memset(&cpu, 0, sizeof(cpu)); cpu.eax = (uint32_t)(uintptr_t)el; cpu.edi = (uint32_t)(uintptr_t)mgr; pm_fn[0](&cpu, NULL);
        memset(&cpu, 0, sizeof(cpu)); cpu.edi = (uint32_t)(uintptr_t)mgr; pm_fn[1](&cpu, NULL);
        CHECK(cpu.jump_to == 0, "H2: manager mode != 1 -> no skip");
        *(int32_t *)mgr = 1; *(int32_t *)(mgr + 0x5c) = 12;
        memset(&cpu, 0, sizeof(cpu)); cpu.eax = (uint32_t)(uintptr_t)el; cpu.edi = (uint32_t)(uintptr_t)mgr; pm_fn[0](&cpu, NULL);
        memset(&cpu, 0, sizeof(cpu)); cpu.edi = (uint32_t)(uintptr_t)mgr; pm_fn[1](&cpu, NULL);
        CHECK(cpu.jump_to == 0, "H2: runway slot taken -> no skip");
        *(int32_t *)(mgr + 0x5c) = -1;

        /* the game gives the runway: dock 1, still held; then it takes the aircraft over: everything is let go, nothing is written to the engine */
        p->dock = 1; step(40);
        CHECK(nr(10) == 0 && p->power == 0.0 && g_force_id == 10 && has("dock=1"), "dock 1 (the game's own approach): still held, hooks still armed (%d, %.2f)", nr(10), p->power);
        p->dock = 6; p->attached = 1; step(1);
        CHECK(nr(10) == 1 && p->power == 0.0 && g_force_id == 0 && has("RECALL ended") && has("the game takes over (dock 6, attached 1)"), "take-over: released, engine left alone, hooks off (%d, %.2f, %u)", nr(10), p->power, (unsigned)g_force_id);
        memset(&cpu, 0, sizeof(cpu)); cpu.eax = (uint32_t)(uintptr_t)el; cpu.edi = (uint32_t)(uintptr_t)mgr; pm_fn[0](&cpu, NULL);
        CHECK(cpu.eax == (uint32_t)(uintptr_t)el, "after the take-over H1 is inert again");

        /* the game aborts the approach (dock 5 again, power 1.0, brake 0): held again, tries counted, gives up after 3 */
        begin(ON FORCED "recall_hold_s=30\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        for (int k = 0; k < 3; ++k) {
            memset(&cpu, 0, sizeof(cpu)); cpu.eax = (uint32_t)(uintptr_t)el; cpu.edi = (uint32_t)(uintptr_t)mgr; pm_fn[0](&cpu, NULL);
            memset(&cpu, 0, sizeof(cpu)); cpu.edi = (uint32_t)(uintptr_t)mgr; pm_fn[1](&cpu, NULL);
            p->dock = 1; step(2);
            p->dock = 5; p->power = 1.0; step(2);                     /* the abort path of the game writes power 1.0 and gives the aircraft back to the queue */
        }
        CHECK(p->power == 0.0 && nr(10) == 0, "after each abort the engine is idled again at the next tick (%.2f, %d)", p->power, nr(10));
        step(2);
        CHECK(has("FORCE gave up after 3 tries") && g_force_id == 0, "3 tries at most, then back to the v7 hold (%u)", (unsigned)g_force_id);
        memset(&cpu, 0, sizeof(cpu)); cpu.eax = (uint32_t)(uintptr_t)el; cpu.edi = (uint32_t)(uintptr_t)mgr; pm_fn[0](&cpu, NULL);
        CHECK(cpu.eax == (uint32_t)(uintptr_t)el, "after giving up H1 is inert");
        step(300);
        CHECK(nr(10) == 0 && p->power == 0.0, "and the aircraft stays held (%d, %.2f)", nr(10), p->power);

        /* timeout without any H2 */
        begin(ON FORCED "force_timeout_s=5\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(35);
        CHECK(g_force_id == 10, "flagged");
        step(160);
        CHECK(has("FORCE timeout after 5 s") && g_force_id == 0 && nr(10) == 0, "window over: hooks off, still held (%u, %d)", (unsigned)g_force_id, nr(10));

        /* an aircraft that moves is never flagged */
        begin(ON FORCED); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; p->vel[2] = 0.5; step(10); p->vel[2] = 3; step(60);
        CHECK(g_force_id == 0 && !has("FORCE start"), "moving at 3 m/s: not flagged (%u)", (unsigned)g_force_id);

        /* only one aircraft at a time */
        begin(ON FORCED); carrier(); p = plane(10); p->power = 1.0; FV *q = plane(11); q->power = 1.0; q->pos[0] = -20;
        air(p, 60); air(q, 0); ground(p); ground(q); p->vel[2] = 0; q->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; q->dock = 5; q->mode = 3; step(60);
        CHECK(g_force_id == 10 && count("FORCE start") == 1, "two recalled aircraft: only the first one is flagged (%u, %d)", (unsigned)g_force_id, count("FORCE start"));

        /* pilot comes back while flagged */
        begin(ON FORCED); carrier(); p = plane(10); p->power = 0.7; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40); p->mode = 1; step(1);
        CHECK(g_force_id == 0 && nr(10) == 1 && p->power == 0.7, "the pilot comes back: hooks off, engine given back (%u, %d, %.2f)", (unsigned)g_force_id, nr(10), p->power);

        /* hot switch off: the hooks stay installed but do nothing */
        begin(ON FORCED); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        CHECK(g_force_id == 10, "flagged");
        write_ini(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\nrecall_hold=1\nrecall_force=0\n"); step(100);
        memset(&cpu, 0, sizeof(cpu)); cpu.eax = (uint32_t)(uintptr_t)el; cpu.edi = (uint32_t)(uintptr_t)mgr; pm_fn[0](&cpu, NULL);
        CHECK(cpu.eax == (uint32_t)(uintptr_t)el && g_h1_ours == 0, "recall_force=0 in the ini: H1 does nothing at once");
        memset(&cpu, 0, sizeof(cpu)); cpu.edi = (uint32_t)(uintptr_t)mgr; pm_fn[1](&cpu, NULL);
        CHECK(cpu.jump_to == 0, "recall_force=0 in the ini: H2 does nothing at once");
        CHECK(nr(10) == 0 && p->power == 0.0, "and the aircraft is still held by the v7 rule (%d, %.2f)", nr(10), p->power);

        /* hooks refused by the game: v8 behaves like v7, nothing is flagged */
        write_ini(ON FORCED);
        n_patch_mid = n_patch_abort = 0; patch_mid_fail = 1; logbuf[0] = 0;
        CHECK(cc2x_plugin_load(&api) == 1 && g_hooks_ok == 0 && n_patch_abort == 1 && has("could NOT be installed"), "patch refused: plugin still loads, hooks off, abort called");
        patch_mid_fail = 0;
        begin(ON FORCED); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(80);
        CHECK(g_force_id == 0 && !has("FORCE start") && nr(10) == 0 && p->power == 0.0, "no hooks: never flagged, v7 hold only (%u)", (unsigned)g_force_id);
        patch_commit_fail = 1; n_patch_abort = 0; logbuf[0] = 0;
        CHECK(cc2x_plugin_load(&api) == 1 && g_hooks_ok == 0 && has("could NOT be installed"), "commit refused: hooks off");
        patch_commit_fail = 0;

        /* recall_force=0 at start-up again: nothing patched */
        write_ini(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\nrecall_hold=1\n");
        n_patch_begin = n_patch_mid = n_patch_commit = 0;
        CHECK(cc2x_plugin_load(&api) == 1 && g_hooks_ok == 0 && n_patch_begin == 0 && n_patch_mid == 0, "reload without recall_force: nothing patched");
        begin(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\nrecall_hold=1\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(80);
        CHECK(g_force_id == 0 && !has("FORCE start") && has("recall_force=0") && has("hooks=0"), "v7 behaviour intact, settings line shows recall_force=0 hooks=0");
    }

    puts("T25 v9: the budget of grants is counted INSIDE the hooks; H3 reads why the game aborts, and writes nothing");
    {
        uint32_t el[3] = {10, 0, 0}, el3[3] = {10, 3, 0};

        /* budget: 2 grants, then H1 shows nothing and H2 skips nothing, whatever the tick does in between */
        write_ini(ON FORCED); n_patch_mid = 0; logbuf[0] = 0;
        CHECK(cc2x_plugin_load(&api) == 1 && g_hooks_ok == 1 && n_patch_mid == 9, "reload with the nine hooks");
        memset(t_mgr, 0, sizeof(t_mgr)); *(int32_t *)t_mgr = 1; *(int32_t *)(t_mgr + 0x5c) = -1;
        begin(ON FORCED "force_tries=2\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        CHECK(g_force_id == 10 && g_force_budget == 2, "flagged with a budget of 2 (%d)", g_force_budget);
        run_h1(el); CHECK(t_cpu.eax == (uint32_t)(uintptr_t)g_fake_elem, "grant 1: H1 shows state 1");
        run_h2();   CHECK(t_cpu.jump_to != 0 && g_force_budget == 1, "grant 1: H2 skips the test (budget %d)", g_force_budget);
        run_h1(el); run_h2();
        CHECK(t_cpu.jump_to != 0 && g_force_budget == 0 && g_h2_count == 2, "grant 2: H2 skips the test (budget %d, %u)", g_force_budget, (unsigned)g_h2_count);
        for (int k = 0; k < 50; ++k) { run_h1(el); run_h2(); }       /* the game's abort + regrant loop, many times inside one tick */
        run_h1(el); CHECK(t_cpu.eax == (uint32_t)(uintptr_t)el && g_h1_ours == 0, "budget 0: H1 shows the real element again");
        run_h2();   CHECK(t_cpu.jump_to == 0 && g_h2_count == 2, "budget 0: 50 more passes through the hooks gave nothing more (%u)", (unsigned)g_h2_count);

        /* a new forcing window gets a new budget */
        begin(ON FORCED "force_tries=2\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        CHECK(g_force_budget == 2 && g_h2_count == 0, "new session, new window: budget 2 again (%d)", g_force_budget);

        /* H3: nothing recorded unless it is the flagged aircraft that aborts */
        memset(t_frame, 0x5a, sizeof(t_frame));
        run_h3(p, -1, 1, -80.0f, 3, 5);
        CHECK(g_h3_count == 1 && g_h3_bay == -1 && g_h3_flag == 1 && g_h3_counter == 5 && g_h3_z == -80.0f && g_h3_state == 3, "H3 records the abort of the flagged aircraft (%u)", (unsigned)g_h3_count);
        CHECK(t_untouched && t_cpu.eax == (uint32_t)-1 && t_cpu.jump_to == 0 && t_cpu.eflags == 0, "H3 writes nothing: manager, game frame, registers and flow untouched");
        FV *other = plane(11);
        run_h3(other, -1, 1, -80.0f, 3, 5);
        CHECK(g_h3_count == 1, "H3: another aircraft's abort is ignored (%u)", (unsigned)g_h3_count);
        run_h3(NULL, -1, 1, -80.0f, 3, 5);
        CHECK(g_h3_count == 1, "H3: no aircraft pointer: ignored");

        /* what the tick logs, with the derived causes (the tick logs the latest record) */
        run_h3(p, -1, 1, -80.0f, 3, 5); step(1);
        CHECK(has("HOOK H3 the game ABORTS the approach") && has("bay=-1 fail=1 zone=1 x=3.5 y=-6.5 z=-80.0 counter=5 runway_state=3 causes: no-free-bay not-committed-in-final-zone"), "no bay, final zone, state 3: both causes listed, with the offsets");
        logbuf[0] = 0; run_h3(p, 4, 1, 12.5f, 3, 9); step(1);
        CHECK(has("bay=4 fail=1 zone=1 x=3.5 y=-6.5 z=12.5 counter=9 runway_state=3 causes: target-passed not-committed-in-final-zone") && !has("no-free-bay") && !has("angle"), "causes: target passed + not committed");
        logbuf[0] = 0; run_h3(p, 4, 1, -100.0f, 3, 9); step(1);
        CHECK(has("causes: not-committed-in-final-zone") && !has("target-passed") && !has("no-free-bay") && !has("angle"), "cause: not committed in the final zone only (no angle claim any more)");
        logbuf[0] = 0; run_h3(p, 4, 1, -100.0f, 3, 4000); step(1);
        CHECK(has("causes: counter>3600 not-committed-in-final-zone") && !has("angle"), "cause: approach counter");

        /* flag set but z within 50 m of the end: no cause can be named; and the log is capped at 5 lines per window */
        begin(ON FORCED); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        t_zone = 0; run_h3(p, 4, 1, -20.0f, 3, 10); step(1); t_zone = 1;
        CHECK(has("zone=0") && has("causes:") && !has("not-committed") && !has("target-passed") && !has("no-free-bay") && !has("counter>3600"), "flag set outside the final zone: no cause listed (unknown)");
        logbuf[0] = 0;
        for (int k = 0; k < 9; ++k) { run_h3(p, -1, 1, -80.0f, 3, 5); step(1); }
        CHECK(count("HOOK H3 the game ABORTS") == 4, "log cap: five H3 lines per window in all (%d more after the first)", count("HOOK H3 the game ABORTS"));


        /* loop breaker: after one grant, the same element back in the queue with REAL state 3 (the game aborted) is never forced again */
        begin(ON FORCED); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        CHECK(g_force_id == 10 && g_grants == 0 && g_force_budget == 3, "new window: no grant yet, budget 3 (%u, %d)", (unsigned)g_grants, g_force_budget);
        run_h1(el3);
        CHECK(t_cpu.eax == (uint32_t)(uintptr_t)g_fake_elem, "before any grant an element in state 3 is still forced once (the recall may start there)");
        run_h2();   CHECK(t_cpu.jump_to != 0 && g_grants == 1, "first grant (%u)", (unsigned)g_grants);
        run_h1(el3);
        CHECK(t_cpu.eax == (uint32_t)(uintptr_t)el3 && g_h1_ours == 0, "after a grant: the element back with state 3 is NOT forced again (loop breaker)");
        run_h2();   CHECK(t_cpu.jump_to == 0 && g_grants == 1 && g_force_budget == 2, "and H2 does nothing (%u grant, budget %d)", (unsigned)g_grants, g_force_budget);
        run_h1(el); CHECK(t_cpu.eax == (uint32_t)(uintptr_t)g_fake_elem, "an element in another state (0) can still be forced while the budget lasts");

        /* the balance line */
        run_h3(p, 4, 1, -100.0f, 3, 9); step(1);
        p->mode = 1; step(1);
        CHECK(has("FORCE balance (no longer eligible): GRANTS 1, ABANDONS 1"), "balance line at the end of the window: GRANTS 1, ABANDONS 1");
        begin(ON FORCED "force_tries=2\n"); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        run_h1(el); run_h2(); run_h1(el); run_h2(); p->dock = 1; step(2); p->dock = 5; step(2);
        CHECK(has("FORCE gave up after 2 tries") && has("FORCE balance (gave up): GRANTS 2, ABANDONS 0"), "balance line when the budget is used up");

        /* switched off: inert */
        write_ini(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\nrecall_hold=1\nrecall_force=0\n"); step(100);
        { unsigned before = (unsigned)g_h3_count; run_h3(p, -1, 1, -80.0f, 3, 5);
          CHECK((unsigned)g_h3_count == before, "recall_force=0 in the ini: H3 does nothing at once"); }
    }

    puts("T26 v10: read-only probes on the commit gates");
    {
        FV *other;
        begin(ON FORCED); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        CHECK(g_force_id == 10, "flagged (%u)", (unsigned)g_force_id);

        /* read-only: nothing of the game's frame, manager or registers changes; nothing for another aircraft or none */
        run_probe(3, p, 0.0f, 0.0f, 0.0f);
        CHECK(t_untouched && g_gate_ab == 1, "probe A/B: read only, counted (%u)", (unsigned)g_gate_ab);
        run_probe(4, p, 0.0f, 0.0f, 0.0f);
        CHECK(t_untouched && g_gate_cd == 1 && g_cd_was_d == 0, "probe C/D without a C-passed probe before: read only, counted, gate C (%u, %d)", (unsigned)g_gate_cd, g_cd_was_d);
        run_probe(6, p, 0.0f, 0.0f, 0.0f);
        CHECK(t_untouched && g_gate_cpass == 1 && g_c_ok == 1, "probe C passed: read only (%u)", (unsigned)g_gate_cpass);
        run_probe(4, p, 0.0f, 0.0f, 0.0f);
        CHECK(t_untouched && g_gate_cd == 2 && g_cd_was_d == 1 && g_c_ok == 0, "probe C/D after C passed: gate D, and the memory is cleared (%u, %d)", (unsigned)g_gate_cd, g_cd_was_d);
        run_probe(5, p, 0.0f, 0.0f, 0.0f);
        CHECK(t_untouched && g_gate_e == 1, "probe E: read only, counted (%u)", (unsigned)g_gate_e);
        other = plane(11);
        { uint32_t a = g_gate_ab, c = g_gate_cd, e = g_gate_e, k = g_gate_cpass;
          for (int i = 3; i <= 6; ++i) { run_probe(i, other, 1, 2, 3); run_probe(i, NULL, 1, 2, 3); }
          CHECK(g_gate_ab == a && g_gate_cd == c && g_gate_e == e && g_gate_cpass == k, "another aircraft or no aircraft: ignored by the four probes"); }

        /* what the tick logs */
        logbuf[0] = 0; run_probe(3, p, 0.0f, 0.0f, 0.0f); step(1);
        CHECK(has("PROBE gate A/B of the commit failed") && has("vector slots (0.000, 0.000, 0.000) -> A: zero-length vector"), "gate A/B logged: A (zero vector)");
        logbuf[0] = 0; run_probe(3, p, -0.5f, 0.1f, -0.86f); step(1);
        CHECK(has("vector slots (-0.500, 0.100, -0.860) -> B: lateral component"), "gate A/B logged: B (lateral)");
        logbuf[0] = 0; run_probe(4, p, 0, 0, 0); step(1);
        CHECK(has("PROBE gate C/D of the commit failed") && has("C: direction dot <= 0.95"), "gate C/D logged: C");
        logbuf[0] = 0; run_probe(6, p, 0, 0, 0); run_probe(4, p, 0, 0, 0); step(1);
        CHECK(has("D: the game's virtual check returned false"), "gate C/D logged: D (C had passed)");
        logbuf[0] = 0; run_probe(5, p, 0, 0, 0); step(1);
        CHECK(has("PROBE gate E of the commit failed") && has("bay index out of range"), "gate E logged");

        /* the log is capped at eight probe lines per window, and the balance gives the counts */
        begin(ON FORCED); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        logbuf[0] = 0;
        for (int k = 0; k < 20; ++k) { run_probe(3, p, 0.0f, 0.0f, 0.0f); step(1); }
        CHECK(count("PROBE gate A/B") == 8, "log cap: eight probe lines per window (%d)", count("PROBE gate A/B"));
        run_probe(6, p, 0, 0, 0); run_probe(4, p, 0, 0, 0); run_probe(5, p, 0, 0, 0);
        p->mode = 1; step(1);
        CHECK(has("FORCE balance (no longer eligible): GRANTS 0, ABANDONS 0, GATES AB 20 CD 1 (C passed 1) E 1"), "the balance line gives the gate counts of the window");

        /* switched off at once */
        begin(ON FORCED); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        write_ini(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\nrecall_hold=1\nrecall_force=0\n"); step(100);
        { uint32_t before = g_gate_ab + g_gate_cd + g_gate_e + g_gate_cpass;
          for (int i = 3; i <= 6; ++i) run_probe(i, p, 0, 0, 0);
          CHECK(g_gate_ab + g_gate_cd + g_gate_e + g_gate_cpass == before, "recall_force=0 in the ini: the four probes do nothing at once"); }
    }

    puts("T27 v10b: every hook keeps xmm0-xmm7 exact (the SDK's relay does not save them and the game keeps live values there)");
    {
        uint32_t el[3] = {10, 0, 0};
        cc2x_cpu c;
        write_ini(ON FORCED); n_patch_mid = 0;
        CHECK(cc2x_plugin_load(&api) == 1 && g_hooks_ok == 1 && n_patch_mid == 9, "reload with the nine hooks");
        memset(t_mgr, 0, sizeof(t_mgr)); *(int32_t *)t_mgr = 1; *(int32_t *)(t_mgr + 0x5c) = -1;
        begin(ON FORCED); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        CHECK(g_force_id == 10, "flagged (%u)", (unsigned)g_force_id);

        /* the aircraft is flagged: the whole body of each hook runs (VirtualQuery, the SDK's find) while the xmm registers hold patterns */
        memset(&c, 0, sizeof(c)); c.eax = (uint32_t)(uintptr_t)el; c.edi = (uint32_t)(uintptr_t)t_mgr;
        CHECK(xmm_survives(pm_fn[0], &c, pm_user[0]) && c.eax == (uint32_t)(uintptr_t)g_fake_elem, "H1 (acts: shows state 1) keeps xmm0-7 and still does its job");
        memset(&c, 0, sizeof(c)); c.edi = (uint32_t)(uintptr_t)t_mgr;
        CHECK(xmm_survives(pm_fn[1], &c, pm_user[1]) && c.jump_to == 0x701a8a + 0x10000, "H2 (acts: skips the test) keeps xmm0-7 and still does its job");
        for (int i = 3; i <= 6; ++i) {
            uint8_t *ebp = t_frame + 0x300;
            memset(&c, 0, sizeof(c));
            *(uint32_t *)(ebp - 0x1fc) = (uint32_t)(uintptr_t)p;
            c.ebp = (uint32_t)(uintptr_t)ebp; c.edi = (uint32_t)(uintptr_t)t_mgr;
            { uint32_t before = g_gate_ab + g_gate_cd + g_gate_e + g_gate_cpass;
              CHECK(xmm_survives(pm_fn[i], &c, pm_user[i]) && g_gate_ab + g_gate_cd + g_gate_e + g_gate_cpass == before + 1, "probe %d keeps xmm0-7 and still counts", i); }
        }
        { uint8_t *ebp = t_frame + 0x300;
          memset(&c, 0, sizeof(c));
          *(uint32_t *)(ebp - 0x1fc) = (uint32_t)(uintptr_t)p; *(uint32_t *)(ebp - 0x224) = 1;
          c.ebp = (uint32_t)(uintptr_t)ebp; c.edi = (uint32_t)(uintptr_t)t_mgr; c.eax = 7;
          { uint32_t before = g_h3_count;
            CHECK(xmm_survives(pm_fn[2], &c, pm_user[2]) && g_h3_count == before + 1 && c.eax == 7, "H3 keeps xmm0-7 and still records"); } }

        /* negative control: a function that DOES clobber xmm4 must be caught by the detector */
        memset(&c, 0, sizeof(c));
        CHECK(!xmm_survives(clobber_xmm4, &c, NULL), "the detector catches a hook that clobbers xmm4 (negative control)");

        /* the same hooks, not flagged / unknown aircraft: still exact */
        memset(&c, 0, sizeof(c)); c.eax = (uint32_t)(uintptr_t)el; c.edi = (uint32_t)(uintptr_t)t_mgr;
        el[0] = 99;
        CHECK(xmm_survives(pm_fn[0], &c, pm_user[0]) && c.eax == (uint32_t)(uintptr_t)el, "H1 on another aircraft keeps xmm0-7 and leaves the element alone");
    }

    /* The scenarios below all start from "the aircraft is parked, held, recalled for 1 s, so it is flagged": */
#define FLAGGED(opts) do { memset(t_mgr, 0, sizeof(t_mgr)); *(int32_t *)t_mgr = 1; *(int32_t *)(t_mgr + 0x5c) = -1;      /* a fresh fake manager: carrier in docking mode, runway free */ \
                           begin(ON FORCED opts); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5); \
                           p->dock = 5; p->mode = 3; step(40); } while (0)
#define FLAGGED5(opts) do { FLAGGED(opts); fake_carrier(12, 2); plane_raw(p, 5); t_rel = 0.1f; t_h5_mgr = t_h5_ship = 0; } while (0)
    puts("T28 v12: H5 (on the H4 site) sends the flagged, parked aircraft to the game's touch test, only while it owns the runway in state 3");
    {
        uint32_t el[3] = {10, 0, 0};
        FV *other;
        int overlap = 0;

        write_ini(ON FORCED); n_patch_begin = n_patch_mid = n_patch_commit = n_patch_abort = 0; patch_mid_fail = patch_commit_fail = 0; logbuf[0] = 0;
        CHECK(cc2x_plugin_load(&api) == 1 && g_hooks_ok == 1 && n_patch_mid == 9 && n_patch_begin == 1 && n_patch_commit == 1 && n_patch_abort == 0, "reload with the nine hooks in one transaction (%d)", n_patch_mid);
        CHECK(pm_site[7] == 0x6fe470 && pm_len[7] == 7 && memcmp(pm_exp[7], "\xc6\x85\xfb\xfd\xff\xff\x01", 7) == 0 && pm_user[7] == NULL, "H5: site 0x6fe470, 7 bytes, expected 'mov byte [ebp-0x205],1'");
        CHECK(pm_site[8] == 0x6ff379 && pm_len[8] == 9 && memcmp(pm_exp[8], "\x89\x47\x6c\x8b\x8e\x88\x00\x00\x00", 9) == 0 && pm_user[8] == NULL,
              "take-over probe: site 0x6ff379, 9 bytes, expected 'mov [edi+0x6c],eax ; mov ecx,[esi+0x88]'");
        for (int i = 0; i < 9; ++i) for (int j = i + 1; j < 9; ++j) if (!(pm_site[i] + pm_len[i] <= pm_site[j] || pm_site[j] + pm_len[j] <= pm_site[i])) overlap++;
        CHECK(overlap == 0, "no two of the nine patched ranges overlap (%d)", overlap);
        CHECK(pm_site[0] == 0x7018ce && pm_site[1] == 0x701a3d && pm_site[2] == 0x6ff0fb && pm_site[3] == 0x6febda && pm_site[4] == 0x6febe7 && pm_site[5] == 0x6febc0 && pm_site[6] == 0x6fe788,
              "the seven v10 sites are unchanged and in the same order (H1, H2, H3, four probes)");
        CHECK(has("H5 (0x6fe470, sends the aircraft to the touch test 0x6ff20a) and the take-over probe (0x6ff379, read only) installed"), "installation logged with the H5 target");

        /* the flagged aircraft, runway state 3, owner = the aircraft, edi = the aircraft: H5 sets edi/esi and continues at the touch test, nothing written */
        FLAGGED5("");
        CHECK(g_force_id == 10 && g_h5_budget == H5_MAX_JUMPS && g_h5_count == 0 && g_h5_reached == 0, "flagged, H5 budget %d", g_h5_budget);
        run_h1(el); run_h2(); p->dock = 1;
        run_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        CHECK(t_cpu.jump_to == 0x6ff20a + 0x10000, "H5 continues at the touch test 0x6ff20a (%#x)", t_cpu.jump_to);
        CHECK(t_cpu.edi == (uint32_t)(uintptr_t)t_mgr && t_cpu.esi == (uint32_t)(uintptr_t)t_ship, "edi = the landing manager, esi = the carrier (what the code at 0x6ff20a expects)");
        CHECK(t_h5_changed == 0 && t_untouched, "NOTHING of the game's memory changed (%d bytes; frame, manager, carrier, bays, wheels), eax ecx edx ebx ebp and the flags untouched", t_h5_changed);
        CHECK(g_h5_count == 1 && g_h5_reached == 1 && g_h5_budget == H5_MAX_JUMPS - 1 && g_mgr == (uintptr_t)t_mgr && g_h5_dist == 20.0f && g_h5_counter == 7,
              "counted: 1 jump, budget one less, manager, distance and counter recorded");
        CHECK(fabsf(g_h5_rel - 0.1f) < 0.01f && g_h5_nw == 3 && g_h5_w0[2] == 0.05f && g_h5_w4[0] == 0.0f && g_h5_pref == 5 && g_h5_pref_free && g_h5_free == 12 &&
              g_h5_lift == -1 && g_h5_owner == 10, "recorded: rel, the two wheel fields, the preferred bay (free), 12 free bays, lift and runway owners (%.3f, %d, %d)",
              (double)g_h5_rel, (int)g_h5_free, (int)g_h5_pref);

        /* every refusal changes nothing at all: the relay then runs the displaced store, exactly like the game */
        { uint32_t r0 = g_h5_reached, c0 = g_h5_count;
          other = plane(11);
          run_h5(other, (uint32_t)(uintptr_t)other, 3, 11);
          CHECK(t_cpu.jump_to == 0 && t_h5_changed == 0 && t_untouched && t_cpu.edi == (uint32_t)(uintptr_t)other && t_cpu.esi == 0x1111 && g_h5_reached == r0 && g_h5_count == c0,
                "another aircraft's pass: ignored, not even counted");
          run_h5(NULL, 0, 3, 10);
          CHECK(t_cpu.jump_to == 0 && t_h5_changed == 0 && t_untouched && t_cpu.esi == 0x1111 && g_h5_reached == r0 && g_h5_count == c0, "no aircraft pointer: ignored");
#define REFUSED(why_, what) CHECK(t_cpu.jump_to == 0 && t_h5_changed == 0 && t_untouched && t_cpu.esi == 0x1111 && g_h5_count == c0 && g_h5_why == (why_), what " (why %d)", (int)g_h5_why)
          run_h5(p, (uint32_t)(uintptr_t)t_mgr, 3, 10); REFUSED(1, "edi is not the aircraft: refused");
          CHECK(t_cpu.edi == (uint32_t)(uintptr_t)t_mgr && g_h5_reached == r0 + 1, "edi left as it was, the visit is counted");
          t_h5_mgr = 0x10; run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); REFUSED(2, "unreadable manager pointer: refused"); CHECK(g_h5_state == -99, "state -99");
          t_h5_mgr = 0; t_h5_ship = 0x10; run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); REFUSED(2, "unreadable carrier pointer: refused"); t_h5_ship = 0;
          for (int st = 0; st <= 7; ++st) {
              if (st == 3) continue;
              run_h5(p, (uint32_t)(uintptr_t)p, st, 10);
              CHECK(t_cpu.jump_to == 0 && t_h5_changed == 0 && t_untouched && g_h5_count == c0 && g_h5_why == 3 && g_h5_state == st, "runway state %d: refused, the game's own code goes on (why %d)", st, (int)g_h5_why);
          }
          run_h5(p, (uint32_t)(uintptr_t)p, 3, 11); REFUSED(4, "the runway belongs to another aircraft: refused");
          run_h5(p, (uint32_t)(uintptr_t)p, 3, -1); REFUSED(4, "the runway belongs to nobody: refused");
          for (int i = 0; i < 12; ++i) bay_set(i, 100 + (uint32_t)i, 1);
          run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); REFUSED(6, "every bay occupied: refused");
          for (int i = 0; i < 12; ++i) bay_set(i, 0, 2);
          run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); REFUSED(6, "free bays, but none of the aircraft class: refused");
          fake_carrier(12, 2);
          t_rel = 2.5f; run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); REFUSED(7, "the aircraft moves at 2.5 m/s: refused");
          t_rel = NAN; run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); REFUSED(7, "speed not a number: refused");
          t_rel = 0.1f;
#undef REFUSED
        }

        /* bays: the preferred one taken but another free = it goes (the game's search takes the first free one); the class table wraps round like the game's */
        bay_set(5, 99, 1);
        run_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        CHECK(t_cpu.jump_to != 0 && !g_h5_pref_free && g_h5_free == 11, "preferred bay 5 taken, 11 others free: H5 goes (%d)", (int)g_h5_free);
        plane_raw(p, 200);
        run_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        CHECK(t_cpu.jump_to != 0 && !g_h5_pref_free && g_h5_pref == 200, "preferred bay out of range: not free, H5 still goes");
        fake_carrier(12, 10); plane_raw(p, 5);
        run_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        CHECK(t_cpu.jump_to != 0 && g_h5_free == 12 && g_h5_pref_free, "node table wrapping round (first index 10 of 16): 12 free bays");

        /* the budget is counted inside the hook: H5_MAX_JUMPS jumps (touch tests), then nothing, whatever the ticks do */
        FLAGGED5("");
        run_h1(el); run_h2(); p->dock = 1;
        { int jumps = 0;
          for (int i = 0; i < H5_MAX_JUMPS; ++i) { run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); jumps += t_cpu.jump_to != 0; if (i == 3) step(1); }
          CHECK(jumps == H5_MAX_JUMPS && g_h5_budget == 0 && g_h5_count == (uint32_t)H5_MAX_JUMPS, "%d jumps of %d", jumps, H5_MAX_JUMPS); }
        run_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        CHECK(t_cpu.jump_to == 0 && t_h5_changed == 0 && g_h5_why == 5, "the next pass: refused, budget used up (why %d): the game takes its own path", (int)g_h5_why);

        /* inert when nothing is flagged, and switched off at once by recall_force=0 in the ini */
        begin(ON FORCED); carrier(); p = plane(10); p->power = 1.0; air(p, 60); ground(p); p->vel[2] = 0; step(5); fake_carrier(12, 2); plane_raw(p, 5);
        run_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        CHECK(t_cpu.jump_to == 0 && t_h5_changed == 0 && g_h5_reached == 0, "no aircraft flagged: inert");
        run_cap(p, 5);
        CHECK(t_untouched && g_cap_count == 0, "the take-over probe too");
        FLAGGED5("");
        write_ini(ON "brake=0.1\nhold_brake=0.8\nhold_idle=1\nrecall_hold=1\nrecall_force=0\n"); step(100);
        run_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        CHECK(t_cpu.jump_to == 0 && t_h5_changed == 0 && g_h5_reached == 0 && g_h5_count == 0, "recall_force=0 in the ini: H5 does nothing at once");

        /* the take-over probe: read only, only for the flagged aircraft */
        FLAGGED5("");
        run_cap(p, 5);
        CHECK(t_untouched && g_cap_count == 1 && g_cap_bay == 5 && g_cap_limit == 12, "probe: bay 5 of 12 recorded, nothing changed (registers, flags, memory)");
        run_cap(other, 5);
        CHECK(t_untouched && g_cap_count == 1, "another aircraft (a helicopter landing, say): ignored");
        run_cap(p, -1);
        CHECK(t_untouched && g_cap_count == 2 && g_cap_bay == -1, "bay -1 recorded as it is");

        /* xmm0-xmm7 exact around H5 and the probe (the SDK's relay does not save them), when they act and when they do not */
        FLAGGED5("");
        run_h1(el); run_h2();
        prep_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        CHECK(xmm_survives(pm_fn[7], &t_cpu, pm_user[7]) && t_cpu.jump_to == 0x6ff20a + 0x10000 && g_h5_count == 1, "H5 (jumps: it computes a float square root) keeps xmm0-7 and still redirects");
        prep_h5(p, (uint32_t)(uintptr_t)p, 4, 10);
        CHECK(xmm_survives(pm_fn[7], &t_cpu, pm_user[7]) && t_cpu.jump_to == 0 && g_h5_count == 1, "H5 (refuses: runway state 4) keeps xmm0-7");
        prep_h5(other, (uint32_t)(uintptr_t)other, 3, 10);
        CHECK(xmm_survives(pm_fn[7], &t_cpu, pm_user[7]) && t_cpu.jump_to == 0, "H5 (another aircraft) keeps xmm0-7");
        { uint8_t *ebp = t_frame + 0x300; cc2x_cpu c;
          memset(&c, 0, sizeof(c)); *(uint32_t *)(ebp - 0x1fc) = (uint32_t)(uintptr_t)p; c.ebp = (uint32_t)(uintptr_t)ebp; c.eax = 4; c.esi = (uint32_t)(uintptr_t)t_ship;
          CHECK(xmm_survives(pm_fn[8], &c, pm_user[8]) && g_cap_bay == 4, "the take-over probe keeps xmm0-7 and still records"); }
        memset(&t_cpu, 0, sizeof(t_cpu));
        CHECK(!xmm_survives(clobber_xmm4, &t_cpu, NULL), "negative control: the detector still catches a hook that clobbers xmm4");
    }

    puts("T29 v12: success = the take-over block, then dock 6 / flight 1 / runway state 5, and the FOLLOW to the hangar");
    {
        uint32_t el[3] = {10, 0, 0};

        FLAGGED5("");
        run_h1(el); run_h2(); p->dock = 1;
        run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); step(1);
        CHECK(has("HOOK H5 sent the aircraft to the game's touch test (1 so far): 20 m from the runway middle, runway state 3, owner 10, approach counter 7, rel 0.10 m/s, "
                  "wheels 3: field +0 = 0.050 0.050 0.050, field +4 = 0.000 0.000 0.000, preferred bay 5 (free), free bays 12, lift owner -1 -> continued at 0x6ff20a"),
              "H5 is logged with everything it read");
        CHECK(g_h5_budget == H5_MAX_JUMPS - 1 && g_force_budget == 2, "the tick does not refill the budgets (%d, %d)", g_h5_budget, g_force_budget);
        CHECK(has("RUNWAY state 3 (3 approach, 4 committed, 5 push-back on the rails), owner slot 10, approach counter 7"), "runway watch: first line");
        run_cap(p, 5); step(1);
        CHECK(t_untouched && has("PROBE take-over block entered: the touch test PASSED, the game got bay 5 (limit 12)") && !has("out of range"), "the probe is logged");
        CHECK(nr(10) == 0 && p->power == 0.0, "still held until the game's state shows the take-over");
        *(int32_t *)(t_mgr + 0x1c) = 5; p->dock = 6; p->flight = 1; p->attached = 1; p->fuel = 40; step(1);
        CHECK(has("FORCE balance (no longer eligible): GRANTS 1, ABANDONS 0, GATES AB 0 CD 0 (C passed 0) E 0, H5 jumps 1 (reached 1), TAKE-OVER block 1"), "balance line");
        CHECK(has("VERDICT: the touch test PASSED and the game ran its take-over block (bay 5); runway state now 5, owner slot 10"), "verdict: take-over");
        CHECK(g_force_id == 0 && g_force_budget == 0 && g_h5_budget == 0 && nr(10) == 1 && p->power == 0.0 && has("the game takes over (dock 6, attached 1)"),
              "released (brake 0 / grip 1, the game's own values), hooks off, engine left to the game");
        CHECK(g_follow_id == 10 && has("TAKEN OVER: dock 6, flight 1, runway state 5 - the game pushes the aircraft back to the lift"), "the follow starts and says TAKEN OVER");
        run_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        CHECK(t_cpu.jump_to == 0 && t_h5_changed == 0, "and H5 is inert afterwards");
        { int b0 = ncalls;
          step(5 * 30); *(int32_t *)(t_mgr + 0x1c) = 6; step(30); *(int32_t *)(t_mgr + 0x1c) = 7; step(30);
          *(int32_t *)(t_mgr + 0x1c) = 0; p->dock = 4; p->flight = 0; step(1);
          CHECK(ncalls == b0, "the follow writes nothing (no brake call, %d)", ncalls - b0); }
        CHECK(has("FOLLOW +0.0s: dock=6 flight=1 attached=1 runway_state=5 fuel=40.0") && has("runway_state=6") && has("runway_state=7"), "the follow logs each change");
        CHECK(has("HANGAR: dock 4 (stowed)") && has("s after the take-over, fuel 40.0"), "stowed: HANGAR line");
        p->fuel = 55; step(20 * 30);
        CHECK(has("REFUEL check: fuel 40.0 at the stowing, 55.0 20 s later (it goes up: refuelling); end of the follow") && g_follow_id == 0, "refuel check, end of the follow");
        CHECK(count("FOLLOW +") >= 4 && count("FOLLOW +") <= 60, "follow lines capped (%d)", count("FOLLOW +"));

        /* the game's state after its block is not the expected one: said at once */
        FLAGGED5("");
        run_h1(el); run_h2(); p->dock = 1; run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); run_cap(p, 5);
        *(int32_t *)(t_mgr + 0x1c) = 3; p->dock = 1; p->attached = 1; step(1);
        CHECK(has("AFTER THE TAKE-OVER BLOCK: not the expected dock 6 / flight 1 / runway state 5 (dock 1, flight 1, attached 1, runway state 3)"), "unexpected state after the block: said");
        /* aircraft gone while followed */
        p->alive = 0; step(1);
        CHECK(has("FOLLOW: the aircraft is gone after") && g_follow_id == 0, "gone: said, follow ended");

        /* never stowed: the follow stops after 5 min */
        FLAGGED5("");
        run_h1(el); run_h2(); p->dock = 1; run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); run_cap(p, 5);
        *(int32_t *)(t_mgr + 0x1c) = 6; p->dock = 6; p->attached = 1; step(1);
        CHECK(g_follow_id == 10, "followed");
        step(300 * 30);
        CHECK(has("FOLLOW stopped after 300 s without dock 4 (last: dock 6, flight 1, runway state 6)") && g_follow_id == 0, "never stowed: stopped after 5 min, last state given");

        /* a runway state 4 after H5 must never happen: warned */
        FLAGGED5("");
        run_h1(el); run_h2(); p->dock = 1; run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); step(1);
        *(int32_t *)(t_mgr + 0x1c) = 4; step(1); step(1);
        CHECK(count("UNEXPECTED: the game's runway state is 4 (committed)") == 1, "state 4: one UNEXPECTED line");
    }

    puts("T30 v12: the VERDICT line when it does not work");
    {
        uint32_t el[3] = {10, 0, 0};

        FLAGGED5("force_timeout_s=5\n");
        step(160);
        CHECK(has("FORCE timeout after 5 s") && has("VERDICT: the runway was never given (H1/H2 did not fire), nothing was forced") && count("FORCE balance") == 1, "no grant: the verdict says so");

        /* the v10 field result: the game aborted and H5 never ran = SILENT */
        FLAGGED5("");
        run_h1(el); run_h2(); p->dock = 1; step(2);
        run_h3(p, 8, 1, -95.2f, 3, 1); p->dock = 5; p->power = 1.0; step(2);
        p->mode = 1; step(1);
        CHECK(has("FORCE balance (no longer eligible): GRANTS 1, ABANDONS 1, GATES AB 0 CD 0 (C passed 0) E 0, H5 jumps 0 (reached 0), TAKE-OVER block 0"), "balance: one grant, one abort, H5 never reached");
        CHECK(has("VERDICT: SILENT - H5 never ran, the game never came to 0x6fe470 for this aircraft (although it aborted the approach, see the H3 line)"), "verdict: SILENT");

        /* reached but refused */
        FLAGGED5("");
        run_h1(el); run_h2(); p->dock = 1;
        run_h5(p, (uint32_t)(uintptr_t)p, 4, 10); step(1);
        CHECK(has("HOOK H5 reached its site (1 visit(s) so far) but did not act: the runway state was not 3 (not given, or already taken over) (runway state seen 4)"), "the refusal is logged with its reason");
        p->mode = 1; step(1);
        CHECK(has("VERDICT: H5 reached its site 1 time(s) but did not act: the runway state was not 3"), "verdict: reached, refused");

        /* H5 jumped, the touch test never passed, then the game aborted: the verdict gives the values the test compared */
        FLAGGED5("");
        run_h1(el); run_h2(); p->dock = 1;
        { float bad = 0.25f; memcpy(t_wheels + 0x70 + 4, &bad, 4); }
        for (int i = 0; i < 3; ++i) run_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        run_h3(p, 8, 1, -95.2f, 3, 1); p->dock = 5; p->power = 1.0; step(2);
        p->mode = 1; step(1);
        CHECK(has("VERDICT: TOUCH TEST NEVER PASSED - H5 sent the aircraft to it 3 time(s); last values: rel 0.10 m/s (game wants <= 10), 3 wheels, "
                  "field +0 = 0.050 0.050 0.050 (game wants >= 0.01), field +4 = 0.000 0.250 0.000 (game wants <= 0.1); then the game aborted the approach (H3 line)"),
              "verdict: touch test never passed, with the wheel fields");

        /* the touch test passed but the game found no bay */
        FLAGGED5("");
        run_h1(el); run_h2(); p->dock = 1; run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); run_cap(p, -1); step(1);
        CHECK(has("PROBE take-over block entered: the touch test PASSED, the game got bay -1 (limit 12) -> out of range, the game skips the take-over"), "probe: out of range");
        p->mode = 1; step(1);
        CHECK(has("VERDICT: the touch test PASSED but the game found no bay for the take-over (bay -1, limit 12): it skipped the take-over block"), "verdict: no bay");
    }

    puts("T31 v12: ONE forcing window per recall (v10 reopened a second one with a fresh budget)");
    {
        uint32_t el[3] = {10, 0, 0};

        /* replay of the v10 big test: grant, the game aborts, the aircraft is nudged, then calm: no second window, no second grant */
        FLAGGED5("");
        CHECK(g_force_id == 10 && count("FORCE start") == 1 && has("hooks H1/H2/H5 armed for this aircraft") && has("the only window of this recall"), "one window opened and it says it is the only one");
        run_h1(el); run_h2(); p->dock = 1; step(2);
        run_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        run_h3(p, 8, 1, -95.2f, 3, 1); p->dock = 5; p->power = 1.0; step(2);
        CHECK(g_force_id == 10 && count("FORCE window closed") == 0 && p->power == 0.0 && g_grants == 1, "after the abort the SAME window goes on and the aircraft is held again");
        CHECK(g_force_budget == 2 && g_h5_budget == H5_MAX_JUMPS - 1 && count("FORCE start") == 1, "the ticks at dock 5 refill nothing and reopen nothing (%d, %d)", g_force_budget, g_h5_budget);
        p->vel[2] = 1.3; step(2); p->vel[2] = 0;
        CHECK(has("FORCE window closed for good (aircraft not parked any more: rel 1.30 m/s") && has("FORCE balance (window closed): GRANTS 1, ABANDONS 1"), "the aircraft moves: the window closes for good, and says so");
        CHECK(g_force_id == 0 && g_force_budget == 0 && g_h5_budget == 0, "the hooks are off (id, grant budget, H5 budget)");
        step(15 * 30);
        CHECK(count("FORCE start") == 1 && g_force_id == 0 && g_force_budget == 0 && g_h5_budget == 0 && g_grants == 1, "15 s of calm later (v10 reopened after 10 s): still ONE window, budgets still 0, grants still 1");
        run_h1(el);   CHECK(t_cpu.eax == (uint32_t)(uintptr_t)el && g_h1_ours == 0, "H1 inert");
        run_h2();     CHECK(t_cpu.jump_to == 0, "H2 inert");
        run_h5(p, (uint32_t)(uintptr_t)p, 3, 10); CHECK(t_cpu.jump_to == 0 && t_h5_changed == 0, "H5 inert");
        CHECK(nr(10) == 0 && p->power == 0.0, "and the aircraft is still held (v7 rule): brake kept, engine at 0");

        /* the recall ends (pilot back): the next recall gets its own, single, window */
        p->mode = 1; step(1);
        CHECK(nr(10) == 1 && track_of(10)->force_done == 0 && track_of(10)->force == 0, "release: the next recall may open one window");
        p->mode = 0; p->dock = 0; p->attached = 0; air(p, 60); ground(p); p->vel[2] = 0; step(5);
        p->dock = 5; p->mode = 3; step(40);
        CHECK(count("FORCE start") == 2 && g_force_id == 10 && g_force_budget == 3 && g_h5_budget == H5_MAX_JUMPS && g_grants == 0, "second recall: window 2 of the session, fresh budgets (%d)", count("FORCE start"));

        /* contact lost for one tick at dock 5 closes it as well, even before any grant */
        FLAGGED5("");
        CHECK(g_force_id == 10, "flagged");
        wheels(p, 0, 0, 0); step(1); wheels(p, 1, 1, 1);
        CHECK(has("FORCE window closed for good (aircraft not parked any more: rel 0.00 m/s, wheels in contact 0") && g_force_id == 0, "one tick without contact: closed for good, before any grant");
        step(600);
        CHECK(count("FORCE start") == 1 && g_force_id == 0 && g_h5_budget == 0 && count("FORCE balance") == 1, "and it stays closed (one start, one balance line)");
        run_h1(el); CHECK(t_cpu.eax == (uint32_t)(uintptr_t)el, "H1 inert");

        /* at dock 1 the game owns the aircraft: a nudge there does not close the window */
        FLAGGED5("");
        run_h1(el); run_h2(); p->dock = 1; step(2); p->vel[2] = 2.0; step(5);
        CHECK(count("FORCE window closed") == 0 && g_force_id == 10 && nr(10) == 0, "dock 1: the window stays open and the aircraft stays held");

        /* the other ways to end a window print exactly one balance line */
        FLAGGED5("force_timeout_s=5\n");
        step(160); p->mode = 1; step(1);
        CHECK(count("FORCE timeout") == 1 && count("FORCE balance") == 1 && count("FORCE window closed") == 0, "timeout: one balance line, no 'closed for good' line");
        FLAGGED5("force_tries=2\n");
        run_h1(el); run_h2(); run_h1(el); run_h2(); p->dock = 1; step(2); p->dock = 5; step(5);
        CHECK(count("FORCE gave up after 2 tries") == 1 && count("FORCE balance") == 1 && count("FORCE window closed") == 0 && count("FORCE start") == 1, "gave up: one balance line, one window");
        step(300);
        CHECK(count("FORCE start") == 1 && g_force_id == 0, "and no new window after giving up");
    }

    puts("T32 v12: the table of the Steam build of 28/10 (PE timestamp 0x6ae228f3, SDK build \"1.5.18-win32-6ae228f3\")");
    {
        static const uint32_t want[9] = {0x7019de, 0x701b4d, 0x6ff20b, 0x6fecea, 0x6fecf7, 0x6fecd0, 0x6fe898, 0x6fe580, 0x6ff489};
        static const uint32_t old[9] = {0x7018ce, 0x701a3d, 0x6ff0fb, 0x6febda, 0x6febe7, 0x6febc0, 0x6fe788, 0x6fe470, 0x6ff379};
        uint32_t el[3] = {10, 0, 0}, len_old[9];
        uint8_t exp_old[9][16];
        int ok = 1, same = 1;

        for (int i = 0; i < 9; ++i) { len_old[i] = pm_len[i]; memcpy(exp_old[i], pm_exp[i], 16); }   /* the last load was the 1.5.18 table */
        api.game_build = "1.5.18-win32-6ae228f3"; t_stamp = 0x6ae228f3u;
        write_ini(ON FORCED); n_patch_begin = n_patch_mid = n_patch_commit = n_patch_abort = 0; logbuf[0] = 0;
        CHECK(cc2x_plugin_load(&api) == 1 && g_hooks_ok == 1 && n_patch_mid == 9 && S == &k_builds[1], "new build: loaded, nine hooks, its own table");
        for (int i = 0; i < 9; ++i) { ok &= pm_site[i] == want[i]; ok &= want[i] == old[i] + 0x110; same &= pm_len[i] == len_old[i] && memcmp(pm_exp[i], exp_old[i], pm_len[i]) == 0; }
        CHECK(ok, "the nine sites are those of the new exe (the 1.5.18 sites + 0x110, checked by outils/verifier_sites_v12.py)");
        CHECK(same, "same lengths and same expected bytes as on the 1.5.18 exe");
        CHECK(has("loaded (frein v12, build 1.5.18-win32-6ae228f3, exe 0x6ae228f3)") &&
              has("H5 (0x6fe580, sends the aircraft to the touch test 0x6ff31a) and the take-over probe (0x6ff489, read only) installed"), "logged with the new build and addresses");
        FLAGGED5("");
        run_h1(el); run_h2();
        CHECK(t_cpu.jump_to == 0x701b9a + 0x10000, "H2 continues at 0x701b9a (%#x)", t_cpu.jump_to);
        p->dock = 1; run_h5(p, (uint32_t)(uintptr_t)p, 3, 10);
        CHECK(t_cpu.jump_to == 0x6ff31a + 0x10000 && t_h5_changed == 0, "H5 continues at 0x6ff31a (%#x)", t_cpu.jump_to);
        api.game_build = "1.5.18-win32"; t_stamp = 0x6a36c177u;
        write_ini(NULL);
        CHECK(cc2x_plugin_load(&api) == 1 && S == &k_builds[0], "back to the 1.5.18 table");
    }

    write_ini(NULL);
    printf("\n%d checks passed, %d failed\n", pass, fail);
    return fail ? 1 : 0;
}
