/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Host test of cc2x_hold.c (v2) with a fake CC2X API and a fake game memory (no game, no SDK DLL). 32-bit Windows console program.
 * The fake game reproduces what was read in the exe: the reference filled by 0x63f360 (first button with the exact name), the
 * 8-byte states created {0, 0, 1, 0} by 0x84b130, the press of a type-18 button (0x5d5530: byte0 flipped) and the reader 0x63f570
 * (byte0 != 0 and (byte2 != 0 or argument == 0)). v2: the code of the carrier's 6-button group and of 0x565ce0 (patterns of the
 * plugin), the list of players {base, capacity, head, count} with each player's queue at +0x64, and a stand-in for 0x565ce0
 * The fake image is NOT at 0x400000 (like the game under ASLR): the 4 absolute addresses of 0x565ce0 are written there relocated,
 * as Windows does, while the file holds them for 0x400000. A stand-in for 0x565ce0
 * written in assembly with the game's convention (ecx = queue, 4 arguments, value and flag read as bytes, "ret 0x10") that
 * records the messages. Usage: test_hold.exe */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../cc2x_hold.c"

static int pass, fail_n;
#define CHECK(c, ...) do { if (c) pass++; else { fail_n++; printf("  FAIL line %d: ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

/* ---------------------------------------------------------------- fake image (the exe's code at its image VAs) */
#define IMG_SIZE 0xa00000u        /* image VAs 0x400000..0xdfffff: the relocated addresses of 0x565ce0 go up to 0xe1db44 */
#define FAKE_TYPE 0x6f0100u       /* a free spot of the fake image: type() of message 20 */
#define GAME_ID 0x80              /* what the exe uses (k_group), written here and not taken from the plugin */
#define GAME_QUEUE 0x64
static uint8_t *img;
static uintptr_t f_va(uint32_t v) { return (uintptr_t)img + (v - 0x400000u); }

static void put(uint32_t v, const uint8_t *b, size_t n) { memcpy(img + (v - 0x400000u), b, n); }
static void put_call(uint32_t at, uint32_t target) {
    uint8_t c[5] = {0xe8};
    int32_t rel = (int32_t)(f_va(target) - (f_va(at) + 5));
    memcpy(c + 1, &rel, 4);
    put(at, c, 5);
}
static void put_hex(uint32_t v, const char *hex) {          /* "??" -> 0x90 */
    size_t i;
    for (i = 0; hex[2 * i]; ++i) img[v - 0x400000u + i] = hex[2 * i] == '?' ? 0x90 : (uint8_t)(hexval(hex[2 * i]) * 16 + hexval(hex[2 * i + 1]));
}
static uint32_t at_hex(const char *hex, const char *what) { return (uint32_t)(strstr(hex, what) - hex) / 2; }
static void make_image(const Build *bd, uint32_t timestamp) {
    uint32_t e = 0x80, p, k;
    memset(img, 0xcc, IMG_SIZE);
    memset(img, 0, 0x200);
    img[0] = 'M'; img[1] = 'Z';
    memcpy(img + 0x3c, &e, 4);
    memcpy(img + e, "PE\0\0", 4);
    memcpy(img + e + 8, &timestamp, 4);
    put(bd->site[0], k_lea, sizeof(k_lea));
    put(bd->next[0], k_after1, sizeof(k_after1));
    put_call(bd->call[0], bd->reader);
    put(bd->site[1] - 2, k_before2, sizeof(k_before2));
    put(bd->site[1], k_lea, sizeof(k_lea));
    put_call(bd->call[1], bd->reader);
    put(bd->reader, k_reader, sizeof(k_reader));
    put_hex(bd->group, k_group);                               /* v2 */
    put_call(bd->group + GROUP_CALL, bd->enqueue);
    put_hex(bd->enqueue, k_enqueue);
    for (k = 0; k < 4; ++k) {                                   /* what Windows writes when it loads the exe elsewhere */
        p = (uint32_t)f_va(bd->enq_abs[k]);
        put(bd->enqueue + k_enq_abs_at[k], (const uint8_t *)&p, 4);
    }
    p = (uint32_t)f_va(FAKE_TYPE);                              /* vtable[1] of message 20 = type() */
    put(bd->enq_abs[ENQ_MSG_VTABLE] + 4, (const uint8_t *)&p, 4);
    put(FAKE_TYPE, k_type20, sizeof(k_type20));
}

/* ---------------------------------------------------------------- fake CC2X API */
static char logbuf[1 << 18];
static int nlog;
static void f_log(const char *who, int level, const char *fmt, ...) {
    char t[600];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(t, sizeof(t), fmt, ap);
    va_end(ap);
    nlog++;
    if (strlen(logbuf) + strlen(t) + 64 < sizeof(logbuf)) { strcat(logbuf, who); strcat(logbuf, ": "); strcat(logbuf, t); strcat(logbuf, "\n"); }
}
static int has(const char *s) { return strstr(logbuf, s) != NULL; }
static int count_of(const char *s) { int n = 0; const char *p = logbuf; while ((p = strstr(p, s))) { n++; p++; } return n; }

static struct { uint32_t site, len; int expected_ok; cc2x_mid_fn fn; void *user; } mids[8];
static int n_mid, n_begin, n_commit, n_abort, mid_fail_at = -1, commit_result = 1;
static void (*tick_fn)(void *, void *);
static void (*sess_fn)(void *, int, void *);

static void f_patch_begin(const char *p) { n_begin++; n_mid = 0; (void)p; }
static int f_patch_mid(uint32_t site, uint32_t len, const uint8_t *expected, cc2x_mid_fn fn, void *user) {
    if (n_mid == mid_fail_at) return 0;
    mids[n_mid].site = site; mids[n_mid].len = len; mids[n_mid].fn = fn; mids[n_mid].user = user;
    mids[n_mid].expected_ok = memcmp((const void *)f_va(site), expected, len) == 0;
    n_mid++;
    return 1;
}
static int f_patch_commit(void) { n_commit++; return commit_result; }
static void f_patch_abort(void) { n_abort++; }
static void f_on_tick(void (*fn)(void *, void *), void *u) { tick_fn = fn; (void)u; }
static void f_on_session(void (*fn)(void *, int, void *), void *u) { sess_fn = fn; (void)u; }

static cc2x_api api;
static void reset_api(void) {
    memset(&api, 0, sizeof(api));
    api.api_version = CC2X_API_VERSION; api.size = sizeof(cc2x_api);
    api.sdk_version = "0.5.0"; api.game_build = "1.5.18-win32";
    api.module_base = (uintptr_t)img;
    api.va = f_va; api.log = f_log;
    api.patch_begin = f_patch_begin; api.patch_mid = f_patch_mid; api.patch_commit = f_patch_commit; api.patch_abort = f_patch_abort;
    api.on_server_tick = f_on_tick; api.on_session = f_on_session;
    n_mid = n_begin = n_commit = n_abort = 0; mid_fail_at = -1; commit_result = 1;
    tick_fn = NULL; sess_fn = NULL;
    logbuf[0] = 0; nlog = 0;
}

/* ---------------------------------------------------------------- fake game memory */
typedef struct { const char *data; uint32_t size, cap; } GStr;
#define MAXB 300
typedef struct {
    uint8_t veh[0x600];
    uint8_t *states;           /* n * 8 */
    uint32_t n;
} Veh;
typedef struct {
    uint8_t defobj[0x200];
    uint8_t *ring;             /* cap * 0x58 */
    uint32_t cap, head, count;
    char names[MAXB][80];
} Chassis;

static void ch_make(Chassis *c, const char *const *names, uint32_t count, uint32_t cap, uint32_t head) {
    uint32_t i;
    memset(c->defobj, 0, sizeof(c->defobj));
    free(c->ring);
    c->ring = calloc(cap, DEF_ELEM);
    c->cap = cap; c->head = head; c->count = count;
    for (i = 0; i < count; ++i) {
        uint32_t k = head + i >= cap ? head + i - cap : head + i;
        GStr s;
        snprintf(c->names[i], sizeof(c->names[i]), "%s", names[i]);
        s.data = c->names[i]; s.size = (uint32_t)strlen(c->names[i]); s.cap = s.size + 1;
        memcpy(c->ring + (size_t)k * DEF_ELEM, &s, sizeof(s));
    }
    {
        uint8_t *r = c->defobj + DEF_RING;
        memcpy(r, &c->ring, 4); memcpy(r + 4, &cap, 4); memcpy(r + 8, &head, 4); memcpy(r + 12, &count, 4);
    }
}
static uint8_t *ch_elem(Chassis *c, uint32_t i) { uint32_t k = c->head + i >= c->cap ? c->head + i - c->cap : c->head + i; return c->ring + (size_t)k * DEF_ELEM; }

/* the carrier's creation: 0x84b130 (states {0,0,1,0}) then 0x63f360 for "vehicle_control_air_hold" (first exact name) */
static uint32_t next_id = 0x101;
static uint32_t veh_id(const Veh *v) { uint32_t id; memcpy(&id, v->veh + GAME_ID, 4); return id; }
static void veh_make(Veh *v, Chassis *c) {
    uint32_t i;
    Ref r = {-1, NULL, NULL};
    uint8_t *defp = c->defobj;
    memset(v->veh, 0, sizeof(v->veh));
    free(v->states);
    v->n = c->count;
    v->states = calloc(v->n, 8);
    for (i = 0; i < v->n; ++i) v->states[8 * i + 2] = 1;
    memcpy(v->veh + GAME_ID, &next_id, 4);
    next_id++;
    memcpy(v->veh + OFF_CTRL, &defp, 4);
    memcpy(v->veh + OFF_CTRL + CTRL_ARR, &v->states, 4);
    memcpy(v->veh + OFF_CTRL + CTRL_COUNT, &v->n, 4);
    for (i = 0; i < v->n; ++i)
        if (!strcmp(c->names[i], HOLD_NAME)) { r.idx = (int32_t)i; r.st = v->states + 8 * i; r.def = ch_elem(c, i); break; }
    memcpy(v->veh + OFF_REF, &r, sizeof(r));
}
static void press(Veh *v, uint32_t i) { v->states[8 * i] = !v->states[8 * i]; }          /* 0x5d5530, type 18 */
static int reader(const Ref *r, int arg) {                                                 /* 0x63f570 */
    const uint8_t *s = r->st;
    if (!s || !s[0]) return 0;
    if (s[2]) return 1;
    return arg ? 0 : 1;
}

__attribute__((used)) static uint8_t xmm_in[128], xmm_out[128];
/* calls the plugin's hook exactly as the SDK relay does (cdecl, cpu and user on the stack), with xmm0-xmm7 loaded before and saved after */
__attribute__((naked, used)) static void call_hook_xmm(cc2x_cpu *cpu, void *user) {
    __asm__("movups _xmm_in+0x00, %xmm0\n\t" "movups _xmm_in+0x10, %xmm1\n\t" "movups _xmm_in+0x20, %xmm2\n\t" "movups _xmm_in+0x30, %xmm3\n\t"
            "movups _xmm_in+0x40, %xmm4\n\t" "movups _xmm_in+0x50, %xmm5\n\t" "movups _xmm_in+0x60, %xmm6\n\t" "movups _xmm_in+0x70, %xmm7\n\t"
            "pushl 8(%esp)\n\t" "pushl 8(%esp)\n\t"
            "call _hook\n\t"
            "addl $8, %esp\n\t"
            "movups %xmm0, _xmm_out+0x00\n\t" "movups %xmm1, _xmm_out+0x10\n\t" "movups %xmm2, _xmm_out+0x20\n\t" "movups %xmm3, _xmm_out+0x30\n\t"
            "movups %xmm4, _xmm_out+0x40\n\t" "movups %xmm5, _xmm_out+0x50\n\t" "movups %xmm6, _xmm_out+0x60\n\t" "movups %xmm7, _xmm_out+0x70\n\t"
            "ret\n\t");
}

static int redirected;
/* The game reaching hook site w for carrier v: the hook runs, then either the displaced lea (ecx = carrier + 0x560) or the
 * jump the hook asked for; then "push 1 ; call 0x63f570". Returns the game's answer "is Hold on?". */
static int site(const Build *bd, uint8_t *veh, int w) {
    cc2x_cpu cpu;
    memset(&cpu, 0, sizeof(cpu));
    cpu.esi = (uint32_t)(uintptr_t)veh;
    cpu.ecx = 0xdeadbeef;
    call_hook_xmm(&cpu, (void *)(intptr_t)w);
    CHECK(memcmp(xmm_in, xmm_out, sizeof(xmm_in)) == 0, "xmm0-xmm7 kept by the hook");
    CHECK(cpu.esi == (uint32_t)(uintptr_t)veh, "esi untouched");
    redirected = cpu.jump_to != 0;
    if (!cpu.jump_to) return reader((const Ref *)(veh + OFF_REF), 1);
    CHECK(cpu.jump_to == f_va(bd->next[w]), "jump to the instruction after the lea (got %08x)", (unsigned)cpu.jump_to);
    CHECK(cpu.ecx == (uint32_t)(uintptr_t)&g_fake, "ecx = the plugin's reference");
    return reader((const Ref *)(uintptr_t)cpu.ecx, 1);
}
static int both(const Build *bd, uint8_t *veh, int expect) {
    int a = site(bd, veh, 0), r0 = redirected, b = site(bd, veh, 1), r1 = redirected;
    CHECK(a == expect && b == expect, "answer %d/%d, expected %d", a, b, expect);
    CHECK(r0 == r1, "same choice at both sites");
    return r0;
}

/* ---------------------------------------------------------------- v2: players, their queues, the stand-in for 0x565ce0 */
typedef struct { uint32_t vt, pad; void **base; uint32_t cap, head, count; } FQueue;   /* ring of messages at +8 (k_enqueue) */
typedef struct { uint8_t pad[GAME_QUEUE]; FQueue *queue; uint32_t more[8]; } FPeer;
typedef struct { FPeer **base; uint32_t cap, head, count; } FList;                     /* what esi points to at the hook */
static FQueue fq[8];
static void *fq_slots[8][8];
static FPeer fp[8];
static FPeer *fl_slots[MAX_PEERS + 8];
static FList fl;
/* n players in a list of capacity cap starting at head (it wraps): player k sits in slot (head + k) mod cap */
static void players(uint32_t n, uint32_t cap, uint32_t head) {
    uint32_t k;
    memset(fq, 0, sizeof(fq)); memset(fp, 0, sizeof(fp)); memset(fl_slots, 0, sizeof(fl_slots));
    for (k = 0; k < 8; ++k) { fq[k].base = fq_slots[k]; fq[k].cap = 8; fp[k].queue = &fq[k]; }
    for (k = 0; k < n; ++k) fl_slots[(head + k) % cap] = &fp[k];
    fl.base = fl_slots; fl.cap = cap; fl.head = head; fl.count = n;
}

__attribute__((used)) static uint32_t enq_rec[64][5];      /* queue, vehicle id, button, value, flag */
__attribute__((used)) static uint32_t enq_n;
/* also trashes xmm0-xmm7, as any game function may: the hooks' wrapper must give them back to the game */
__attribute__((naked, used)) static void fake_enqueue(void) {
    __asm__("pcmpeqb %xmm0, %xmm0\n\t" "pcmpeqb %xmm1, %xmm1\n\t" "pcmpeqb %xmm2, %xmm2\n\t" "pcmpeqb %xmm3, %xmm3\n\t"
            "pcmpeqb %xmm4, %xmm4\n\t" "pcmpeqb %xmm5, %xmm5\n\t" "pcmpeqb %xmm6, %xmm6\n\t" "pcmpeqb %xmm7, %xmm7\n\t"
            "pushl %ebx\n\t"
            "movl _enq_n, %eax\n\t"
            "cmpl $64, %eax\n\t"
            "jae 1f\n\t"
            "imull $20, %eax, %ebx\n\t"
            "movl %ecx, _enq_rec(%ebx)\n\t"
            "movl 8(%esp), %edx\n\t" "movl %edx, _enq_rec+4(%ebx)\n\t"
            "movl 12(%esp), %edx\n\t" "movl %edx, _enq_rec+8(%ebx)\n\t"
            "movzbl 16(%esp), %edx\n\t" "movl %edx, _enq_rec+12(%ebx)\n\t"
            "movzbl 20(%esp), %edx\n\t" "movl %edx, _enq_rec+16(%ebx)\n\t"
            "incl _enq_n\n\t"
            "1: popl %ebx\n\t"
            "ret $16\n\t");
}
static int sent(uint32_t k, const FQueue *q, const Veh *v, uint32_t button, uint32_t value) {
    return k < enq_n && enq_rec[k][0] == (uint32_t)(uintptr_t)q && enq_rec[k][1] == veh_id(v) && enq_rec[k][2] == button &&
           enq_rec[k][3] == value && enq_rec[k][4] == 0;
}

/* The game reaching the synchronisation site for carrier v with the list of players `list`: the hook changes no register. */
static void sync_tick(Veh *v, const void *list) {
    cc2x_cpu cpu, before;
    memset(&cpu, 0, sizeof(cpu));
    cpu.edi = (uint32_t)(uintptr_t)v->veh;
    cpu.esi = (uint32_t)(uintptr_t)list;
    cpu.eax = 0x11111111; cpu.ebx = 0x22222222; cpu.ecx = 0x33333333; cpu.edx = 0x44444444; cpu.ebp = 0x55555555; cpu.eflags = 0x246;
    before = cpu;
    call_hook_xmm(&cpu, (void *)(intptr_t)HOOK_SYNC);
    CHECK(memcmp(xmm_in, xmm_out, sizeof(xmm_in)) == 0, "xmm0-xmm7 kept by the synchronisation");
    CHECK(memcmp(&cpu, &before, sizeof(cpu)) == 0, "registers untouched, no jump");
}
static int st0(const Veh *v, uint32_t i) { return v->states[8 * i]; }
static int untouched_except_byte0(const Veh *v, uint32_t i) {       /* {byte0, 0, 1, 0, 0, 0, 0, 0} */
    static const uint8_t z[7] = {0, 1, 0, 0, 0, 0, 0};
    return memcmp(v->states + 8 * i + 1, z, 7) == 0;
}

static const char *const NAMES_AB[] = {"carrier_control_engine_start", "mast_nav_lights", "vehicle_control_air_hold",
                                       "vehicle_control_air_hold_copie_moteur", "vehicle_control_air_hold_copie_feux"};

int main(void) {
    static Chassis ch, ch2;
    static Veh v1, v2;
    const Build *old = &BUILDS[0], *nw = &BUILDS[1];
    int i;
    for (i = 0; i < 128; ++i) xmm_in[i] = (uint8_t)(i * 7 + 3);
    img = calloc(1, IMG_SIZE);
    if (!img) return 2;

    printf("1. chargement\n");
    make_image(old, old->timestamp);
    reset_api(); api.api_version = 2; CHECK(cc2x_plugin_load(&api) == 0 && n_begin == 0, "API 2 refused");
    reset_api(); api.size = 8; CHECK(cc2x_plugin_load(&api) == 0 && n_begin == 0, "short API refused");
    reset_api(); api.patch_mid = NULL; CHECK(cc2x_plugin_load(&api) == 0 && n_begin == 0, "missing patch_mid refused");
    CHECK(cc2x_plugin_load(NULL) == 0, "NULL api refused");
    make_image(old, 0x12345678);
    reset_api(); CHECK(cc2x_plugin_load(&api) == 0 && n_begin == 0 && has("exe inconnu (horodatage PE 12345678)"), "unknown exe refused, nothing patched");
    reset_api(); api.module_base = 0; CHECK(cc2x_plugin_load(&api) == 0 && n_begin == 0, "no module refused");
    {   /* every byte we rely on, changed one at a time: refused, nothing patched */
        uint32_t spots[] = {old->site[0], old->site[0] + 5, old->site[1], old->site[1] + 2, old->next[0], old->next[0] + 8, old->call[0],
                            old->call[0] + 1, old->call[1] + 2, old->site[1] - 2, old->reader, old->reader + 17, old->reader + 38};
        size_t k;
        for (k = 0; k < sizeof(spots) / sizeof(spots[0]); ++k) {
            make_image(old, old->timestamp);
            img[spots[k] - 0x400000u] ^= 0x5a;
            reset_api();
            CHECK(cc2x_plugin_load(&api) == 0 && n_begin == 0 && has("differe de l'attendu"), "changed byte at %08x refused", (unsigned)spots[k]);
        }
    }
    make_image(old, old->timestamp);
    reset_api(); mid_fail_at = 1;
    CHECK(cc2x_plugin_load(&api) == 0 && n_abort == 1 && n_commit == 0 && !tick_fn && !g_active, "second hook refused: abort, inactive");
    reset_api(); mid_fail_at = 2;
    CHECK(cc2x_plugin_load(&api) == 0 && n_abort == 1 && n_commit == 0 && !tick_fn && !g_active && !g_sync, "synchronisation hook refused: abort, inactive");
    reset_api(); commit_result = 0;
    CHECK(cc2x_plugin_load(&api) == 0 && !tick_fn && !g_active && !g_sync && !g_enqueue, "commit refused: inactive, no events");
    make_image(nw, nw->timestamp);
    reset_api();
    CHECK(cc2x_plugin_load(&api) == 1 && g_active && mids[0].site == 0x6fce72u && mids[1].site == 0x6fda4cu && has("nouvel exe"), "new exe: hooks at the new addresses");
    CHECK(n_mid == 3 && mids[2].site == 0x7061f0u && mids[2].expected_ok && g_sync && (uintptr_t)g_enqueue == f_va(0x565e00u),
          "new exe: synchronisation at 0x7061f0, message function 0x565e00");
    make_image(old, old->timestamp);
    reset_api();
    CHECK(cc2x_plugin_load(&api) == 1 && g_active && tick_fn && sess_fn, "old exe: loaded");
    CHECK(n_begin == 1 && n_mid == 3 && n_commit == 1 && n_abort == 0, "one transaction, three hooks");
    CHECK(mids[0].site == 0x6fcd62u && mids[1].site == 0x6fd93cu && mids[0].len == 6 && mids[1].len == 6, "sites and lengths");
    CHECK(mids[2].site == 0x7060e0u && mids[2].len == 6 && mids[2].expected_ok && mids[2].fn == hook && mids[2].user == (void *)2,
          "synchronisation hook at 0x7060e0 (6 bytes, user 2, the xmm wrapper)");
    CHECK(g_sync && (uintptr_t)g_enqueue == f_va(0x565ce0u) && has("synchronisation posee en 0x7060e0"), "synchronisation on, message function 0x565ce0");
    CHECK(mids[0].expected_ok && mids[1].expected_ok, "expected bytes = the image");
    CHECK(mids[0].user == (void *)0 && mids[1].user == (void *)1 && mids[0].fn == hook, "user 0/1, the xmm wrapper");

    printf("2. copies A et B apres l'original\n");
    ch_make(&ch, NAMES_AB, 5, 8, 0);
    veh_make(&v1, &ch);
    sess_fn(NULL, 1, NULL);
    both(old, v1.veh, 0);
    CHECK(!redirected, "nothing on: the game reads the original");
    tick_fn(NULL, NULL);
    CHECK(has("copie trouvee : vehicle_control_air_hold_copie_moteur (bouton n. 3)") && has("copie_feux (bouton n. 4)"), "copies logged");
    press(&v1, 2); CHECK(both(old, v1.veh, 1) == 0, "original on: held, no redirect");
    press(&v1, 2); press(&v1, 3); CHECK(both(old, v1.veh, 1) == 1, "copy A on: held through the copy");
    CHECK(g_fake.idx == 3 && g_fake.st == v1.states + 24 && g_fake.def == ch_elem(&ch, 3), "fake reference = copy A");
    press(&v1, 3); CHECK(both(old, v1.veh, 0) == 0, "copy A off again: released");
    press(&v1, 4); CHECK(both(old, v1.veh, 1) == 1 && g_fake.idx == 4, "copy B on: held");
    press(&v1, 2); CHECK(both(old, v1.veh, 1) == 0, "original and copy B on: the original answers");
    press(&v1, 2); press(&v1, 4);
    v1.states[8 * 2 + 2] = 0; press(&v1, 3);
    CHECK(both(old, v1.veh, 0) == 0, "original unusable (byte2 = 0): a copy does not override it");
    v1.states[8 * 2 + 2] = 1;
    v1.states[8 * 3 + 2] = 0; CHECK(both(old, v1.veh, 0) == 0, "copy unusable (byte2 = 0): not on");
    v1.states[8 * 3 + 2] = 1; CHECK(both(old, v1.veh, 1) == 1, "copy usable again: held");
    press(&v1, 3);
    {
        uint8_t before[8 * 5];
        memcpy(before, v1.states, sizeof(before));
        press(&v1, 4); both(old, v1.veh, 1); press(&v1, 4); both(old, v1.veh, 0);
        CHECK(memcmp(before, v1.states, sizeof(before)) == 0, "the plugin wrote no game memory");
    }
    press(&v1, 4); both(old, v1.veh, 1);
    nlog = 0; logbuf[0] = 0;
    tick_fn(NULL, NULL);
    CHECK(count_of("Hold demande par le jeu") == 1 && has("repond vehicle_control_air_hold_copie_feux"), "one line per change of answer, at the tick");
    tick_fn(NULL, NULL);
    CHECK(count_of("Hold demande par le jeu") == 1, "no repeat without change");
    press(&v1, 4); press(&v1, 3); both(old, v1.veh, 1); tick_fn(NULL, NULL);
    CHECK(has("repond vehicle_control_air_hold_copie_moteur"), "the copy is named in the log");
    press(&v1, 3);

    printf("3. deux porte-avions, meme chassis\n");
    veh_make(&v2, &ch);
    press(&v2, 4);
    CHECK(both(old, v2.veh, 1) == 1, "carrier 2: copy B held");
    CHECK(both(old, v1.veh, 0) == 0, "carrier 1: not held");

    printf("4. anneau qui tourne, copies avant l'original\n");
    {
        static const char *const names[] = {"vehicle_control_air_hold_copie_feux", "a", "b", "vehicle_control_air_hold", "c", "vehicle_control_air_hold_copie_moteur"};
        sess_fn(NULL, 0, NULL);
        ch_make(&ch2, names, 6, 7, 5);
        veh_make(&v1, &ch2);
        CHECK(((const Ref *)(v1.veh + OFF_REF))->idx == 3, "the game binds the first exact name");
        press(&v1, 0); CHECK(both(old, v1.veh, 1) == 1 && g_fake.idx == 0, "wrapped ring: copy at 0 found");
        press(&v1, 0); press(&v1, 5); CHECK(both(old, v1.veh, 1) == 1 && g_fake.idx == 5, "wrapped ring: copy at 5 found");
    }

    printf("5. sans copie, plus de 4 copies, noms bizarres\n");
    {
        static const char *const none[] = {"x", "vehicle_control_air_hold", "vehicle_control_air_hold_2", "vehicle_control_air_holdcopie"};
        static const char *const many[] = {"vehicle_control_air_hold", "vehicle_control_air_hold_copie_1", "vehicle_control_air_hold_copie_2",
                                           "vehicle_control_air_hold_copie_3", "vehicle_control_air_hold_copie_4", "vehicle_control_air_hold_copie_5"};
        sess_fn(NULL, 0, NULL); logbuf[0] = 0;
        ch_make(&ch2, none, 4, 4, 0); veh_make(&v1, &ch2);
        press(&v1, 2); press(&v1, 3);
        CHECK(both(old, v1.veh, 0) == 0, "no copy: nothing happens");
        tick_fn(NULL, NULL); CHECK(has("aucune copie du bouton Hold"), "logged: no copy");
        sess_fn(NULL, 0, NULL);
        ch_make(&ch2, many, 6, 6, 0); veh_make(&v1, &ch2);
        press(&v1, 5); CHECK(both(old, v1.veh, 0) == 0, "5th copy ignored (4 at most)");
        press(&v1, 5); press(&v1, 4); CHECK(both(old, v1.veh, 1) == 1, "4th copy used");
        press(&v1, 4);
        {   /* a name that is not NUL-terminated or too long is skipped, nothing crashes */
            GStr s; static char longname[100];
            memset(longname, 'a', 99);
            s.data = longname; s.size = 99; s.cap = 100;
            memcpy(ch_elem(&ch2, 1), &s, sizeof(s));
            s.data = "vehicle_control_air_hold_copie_2X"; s.size = 31; s.cap = 40;     /* data[31] != 0 */
            memcpy(ch_elem(&ch2, 2), &s, sizeof(s));
            sess_fn(NULL, 0, NULL);
            press(&v1, 1); press(&v1, 2);
            CHECK(both(old, v1.veh, 0) == 0, "broken names skipped");
            press(&v1, 3); CHECK(both(old, v1.veh, 1) == 1 && g_fake.idx == 3, "the other copies still found");
        }
    }

    printf("6. verifications du plugin\n");
    {
        Ref r;
        ch_make(&ch, NAMES_AB, 5, 8, 0);
        sess_fn(NULL, 0, NULL); logbuf[0] = 0;
        veh_make(&v1, &ch); press(&v1, 3);
        memcpy(&r, v1.veh + OFF_REF, sizeof(r));
        r.idx = -1; memcpy(v1.veh + OFF_REF, &r, sizeof(r));
        CHECK(both(old, v1.veh, 0) == 0 && g_fail == 2, "original not found by the game (index -1): nothing, reason 2");
        tick_fn(NULL, NULL); tick_fn(NULL, NULL);
        CHECK(count_of("verification ratee") == 1, "failure logged once");
        veh_make(&v1, &ch); press(&v1, 3); sess_fn(NULL, 0, NULL);
        memcpy(&r, v1.veh + OFF_REF, sizeof(r)); r.st += 8; memcpy(v1.veh + OFF_REF, &r, sizeof(r));
        site(old, v1.veh, 0); CHECK(!redirected && g_fail == 2, "state pointer not at index: nothing");
        veh_make(&v1, &ch); press(&v1, 3); sess_fn(NULL, 0, NULL);
        memcpy(&r, v1.veh + OFF_REF, sizeof(r)); r.def += DEF_ELEM; memcpy(v1.veh + OFF_REF, &r, sizeof(r));
        site(old, v1.veh, 0); CHECK(!redirected && g_fail == 3, "definition not at index: nothing");
        veh_make(&v1, &ch); press(&v1, 3); sess_fn(NULL, 0, NULL);
        { uint32_t n = 4; memcpy(v1.veh + OFF_CTRL + CTRL_COUNT, &n, 4); }
        site(old, v1.veh, 0); CHECK(!redirected && g_fail, "count different from the chassis: nothing");
        veh_make(&v1, &ch); press(&v1, 3); sess_fn(NULL, 0, NULL);
        { uint32_t bad = 0; memcpy(ch.defobj + DEF_RING + 4, &bad, 4); }
        site(old, v1.veh, 0); CHECK(!redirected && g_fail == 3, "ring capacity 0: nothing");
        ch_make(&ch, NAMES_AB, 5, 8, 0);
        {   /* the reference points at a button with another name */
            static const char *const other[] = {"vehicle_control_air_hold_copie_moteur", "vehicle_control_air_hold"};
            ch_make(&ch2, other, 2, 2, 0); veh_make(&v1, &ch2); sess_fn(NULL, 0, NULL);
            memcpy(&r, v1.veh + OFF_REF, sizeof(r)); r.idx = 0; r.st = v1.states; r.def = ch_elem(&ch2, 0); memcpy(v1.veh + OFF_REF, &r, sizeof(r));
            press(&v1, 1); site(old, v1.veh, 0); CHECK(!redirected && g_fail == 3, "reference on a wrong name: nothing");
        }
        sess_fn(NULL, 0, NULL);
        {   /* unreadable carrier memory */
            cc2x_cpu cpu; memset(&cpu, 0, sizeof(cpu)); cpu.esi = 0x10; call_hook_xmm(&cpu, (void *)0);
            CHECK(cpu.jump_to == 0 && cpu.ecx == 0 && g_fail == 1, "carrier pointer 0x10: nothing, reason 1");
            {   /* a carrier whose +0x88 is past the end of a readable region */
                uint8_t *page = VirtualAlloc(NULL, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
                cpu.esi = (uint32_t)(uintptr_t)(page + 0x1000 - 0x90); cpu.jump_to = 0; g_fail = 0;
                call_hook_xmm(&cpu, (void *)1);
                CHECK(cpu.jump_to == 0 && g_fail == 1, "carrier at the end of a page: nothing");
                VirtualFree(page, 0, MEM_RELEASE);
            }
        }
        sess_fn(NULL, 1, NULL);
        CHECK(g_fail == 0 && g_cache.defobj == NULL && g_seen[0] == 0, "session start: everything reset");
        veh_make(&v1, &ch); press(&v1, 3);
        CHECK(both(old, v1.veh, 1) == 1, "after the reset it works again");
        g_active = 0; CHECK(both(old, v1.veh, 0) == 0, "inactive plugin: nothing");
        g_active = 1;
    }

    printf("7. synchronisation dans les deux sens\n");
    {
        uint8_t before[8 * 5];
        CHECK(g_sync && (uintptr_t)g_enqueue == f_va(0x565ce0u), "loaded with the synchronisation");
        g_enqueue = (Enqueue)(uintptr_t)fake_enqueue;            /* 0x565ce0 of the fake image is not code */
        ch_make(&ch, NAMES_AB, 5, 8, 0);
        sess_fn(NULL, 1, NULL); logbuf[0] = 0;
        veh_make(&v1, &ch);
        players(2, 4, 3);                                         /* two players, slots 3 and 0: the list wraps */
        enq_n = 0;
        press(&v1, 2);                                            /* before the first update seen */
        memcpy(before, v1.states, sizeof(before));
        sync_tick(&v1, &fl);
        CHECK(enq_n == 0 && memcmp(before, v1.states, sizeof(before)) == 0, "first update seen: nothing written, nothing sent");
        press(&v1, 2);                                            /* original off again */
        sync_tick(&v1, &fl);
        CHECK(enq_n == 0 && st0(&v1, 3) == 0 && st0(&v1, 4) == 0, "original off: the copies stay off");
        press(&v1, 2); sync_tick(&v1, &fl);
        CHECK(st0(&v1, 2) == 1 && st0(&v1, 3) == 1 && st0(&v1, 4) == 1, "original on -> both copies on");
        CHECK(enq_n == 4 && sent(0, &fq[0], &v1, 3, 1) && sent(1, &fq[1], &v1, 3, 1) && sent(2, &fq[0], &v1, 4, 1) && sent(3, &fq[1], &v1, 4, 1),
              "message 20 for each copy to each player (vehicle id, button, value 1, flag 0)");
        CHECK(untouched_except_byte0(&v1, 2) && untouched_except_byte0(&v1, 3) && untouched_except_byte0(&v1, 4) &&
              untouched_except_byte0(&v1, 0) && st0(&v1, 0) == 0 && st0(&v1, 1) == 0, "only byte0 of the copies written (byte2 stays 1)");
        enq_n = 0; sync_tick(&v1, &fl); sync_tick(&v1, &fl);
        CHECK(enq_n == 0, "no change: nothing sent");
        tick_fn(NULL, NULL);
        CHECK(has("l'original enclenche ; recopie sur 2 autre(s) bouton(s), 4 message(s) aux joueurs") && !has("meme instant"),
              "logged at the tick: who, what, how many");
        CHECK(both(old, v1.veh, 1) == 0, "all on: the original answers itself");
        enq_n = 0; press(&v1, 4); sync_tick(&v1, &fl);           /* copy B off */
        CHECK(st0(&v1, 2) == 0 && st0(&v1, 3) == 0 && st0(&v1, 4) == 0, "copy B off -> original and copy A off");
        CHECK(enq_n == 4 && sent(0, &fq[0], &v1, 2, 0) && sent(1, &fq[1], &v1, 2, 0) && sent(2, &fq[0], &v1, 3, 0) && sent(3, &fq[1], &v1, 3, 0),
              "messages for the original and copy A, value 0");
        enq_n = 0; press(&v1, 3); sync_tick(&v1, &fl);           /* copy A on */
        CHECK(st0(&v1, 2) == 1 && st0(&v1, 4) == 1 && enq_n == 4 && sent(0, &fq[0], &v1, 2, 1) && sent(2, &fq[0], &v1, 4, 1),
              "copy A on -> original and copy B on");
        logbuf[0] = 0; tick_fn(NULL, NULL);
        CHECK(has("vehicle_control_air_hold_copie_moteur enclenche ; recopie sur 2"), "the copy is named in the log");
        press(&v1, 3); sync_tick(&v1, &fl);                       /* all off */
        CHECK(st0(&v1, 2) == 0 && st0(&v1, 4) == 0, "copy A off -> all off");
        press(&v1, 4);                                            /* copy B on, the flight deck runs before the synchronisation */
        CHECK(both(old, v1.veh, 1) == 1, "same update, before the synchronisation: held through copy B (v1)");
        sync_tick(&v1, &fl);
        CHECK(both(old, v1.veh, 1) == 0 && st0(&v1, 2) == 1, "after the synchronisation: held by the original itself");
        press(&v1, 4); sync_tick(&v1, &fl);
        CHECK(st0(&v1, 2) == 0 && st0(&v1, 3) == 0 && both(old, v1.veh, 0) == 0, "copy B off -> released");

        printf("8. cas particuliers de la synchronisation\n");
        logbuf[0] = 0; enq_n = 0;
        press(&v1, 2); press(&v1, 3);                             /* two changes in the same update */
        memcpy(before, v1.states, sizeof(before));
        sync_tick(&v1, &fl);
        CHECK(enq_n == 0 && memcmp(before, v1.states, sizeof(before)) == 0, "two changes in the same update: nothing copied, nothing sent");
        tick_fn(NULL, NULL);
        CHECK(has("l'original et vehicle_control_air_hold_copie_moteur ont change au meme instant"), "logged");
        sync_tick(&v1, &fl);
        CHECK(enq_n == 0 && st0(&v1, 4) == 0, "and not copied later either");
        press(&v1, 4); sync_tick(&v1, &fl);                       /* copy B on: one change again, the others are on already */
        CHECK(st0(&v1, 2) == 1 && st0(&v1, 3) == 1 && st0(&v1, 4) == 1 && enq_n == 0, "next single change: the others already on, nothing to send");
        press(&v1, 4); sync_tick(&v1, &fl);                       /* copy B off */
        CHECK(st0(&v1, 2) == 0 && st0(&v1, 3) == 0 && enq_n == 4, "and the next one is copied");
        enq_n = 0; press(&v1, 2); press(&v1, 3); press(&v1, 4); sync_tick(&v1, &fl);   /* three changes */
        CHECK(enq_n == 0, "three changes: nothing");

        logbuf[0] = 0; enq_n = 0;
        v1.states[8 * 2 + 2] = 0;                                 /* the game makes the original unusable */
        press(&v1, 3); memcpy(before, v1.states, sizeof(before));
        sync_tick(&v1, &fl); sync_tick(&v1, &fl);
        CHECK(enq_n == 0 && memcmp(before, v1.states, sizeof(before)) == 0, "original unusable (byte2 = 0): nothing copied, nothing sent");
        press(&v1, 3); sync_tick(&v1, &fl);
        CHECK(enq_n == 0 && v1.states[8 * 2 + 2] == 0, "still nothing; byte2 never written");
        tick_fn(NULL, NULL);
        CHECK(count_of("inutilisable (octet 2 = 0)") == 1, "logged once");
        v1.states[8 * 2 + 2] = 1; sync_tick(&v1, &fl);
        CHECK(enq_n == 0, "usable again: no change, nothing");
        press(&v1, 4); sync_tick(&v1, &fl);
        CHECK(enq_n == 4 && st0(&v1, 2) == st0(&v1, 4) && st0(&v1, 3) == st0(&v1, 4), "usable again: the next press is copied");

        enq_n = 0;
        v1.states[8 * 4 + 2] = 0;                                 /* copy B unusable */
        press(&v1, 2); sync_tick(&v1, &fl);
        CHECK(st0(&v1, 3) == st0(&v1, 2) && st0(&v1, 4) != st0(&v1, 2) && enq_n == 2 && enq_rec[0][2] == 3 && enq_rec[1][2] == 3,
              "unusable copy: not written, no message for it");
        enq_n = 0; press(&v1, 4); sync_tick(&v1, &fl);
        CHECK(enq_n == 0, "unusable copy pressed: not copied from");
        v1.states[8 * 4 + 2] = 1; sync_tick(&v1, &fl);
        CHECK(enq_n == 0, "usable again: nothing until the next press");
        press(&v1, 4); sync_tick(&v1, &fl);
        CHECK(st0(&v1, 2) == st0(&v1, 4) && st0(&v1, 3) == st0(&v1, 4), "then copied");

        enq_n = 0; players(0, 4, 0);                              /* no player in the list */
        press(&v1, 2); sync_tick(&v1, &fl);
        CHECK(enq_n == 0 && st0(&v1, 3) == st0(&v1, 2) && st0(&v1, 4) == st0(&v1, 2), "no player: written, nothing sent (as the game)");
        players(3, 3, 1); enq_n = 0;
        press(&v1, 3); sync_tick(&v1, &fl);
        CHECK(enq_n == 6 && sent(0, &fq[0], &v1, 2, (uint32_t)st0(&v1, 3)) && sent(1, &fq[1], &v1, 2, (uint32_t)st0(&v1, 3)) &&
              sent(2, &fq[2], &v1, 2, (uint32_t)st0(&v1, 3)), "three players: in the order of the list");

        veh_make(&v2, &ch);                                       /* a second carrier, same chassis */
        sync_tick(&v2, &fl); enq_n = 0;
        press(&v2, 4); sync_tick(&v2, &fl);
        CHECK(st0(&v2, 2) == 1 && st0(&v2, 3) == 1 && enq_n == 6 && enq_rec[0][1] == veh_id(&v2), "carrier 2: its own buttons, its own id");
        sync_tick(&v1, &fl);
        CHECK(enq_n == 6, "carrier 1 untouched");

        {   /* the chassis without copies, then with one copy */
            static const char *const none[] = {"x", "vehicle_control_air_hold", "y"};
            static const char *const one[] = {"vehicle_control_air_hold", "z", "vehicle_control_air_hold_copie_feux"};
            ch_make(&ch2, none, 3, 3, 0); veh_make(&v2, &ch2);
            enq_n = 0; sync_tick(&v2, &fl); press(&v2, 1); sync_tick(&v2, &fl);
            CHECK(enq_n == 0 && st0(&v2, 0) == 0 && st0(&v2, 2) == 0, "no copy: nothing");
            ch_make(&ch2, one, 3, 3, 0); veh_make(&v2, &ch2);
            sync_tick(&v2, &fl); press(&v2, 2); sync_tick(&v2, &fl);
            CHECK(st0(&v2, 0) == 1 && st0(&v2, 1) == 0 && enq_n == 3 && enq_rec[0][2] == 0, "one copy: copy -> original");
            enq_n = 0; press(&v2, 0); sync_tick(&v2, &fl);
            CHECK(st0(&v2, 2) == 0 && enq_n == 3 && enq_rec[0][2] == 2, "one copy: original -> copy");
        }
        {   /* more carriers than MAX_CARRIERS */
            static Veh many[MAX_CARRIERS + 1];
            int k;
            sess_fn(NULL, 1, NULL); logbuf[0] = 0; enq_n = 0;
            for (k = 0; k <= MAX_CARRIERS; ++k) { veh_make(&many[k], &ch); sync_tick(&many[k], &fl); press(&many[k], 2); sync_tick(&many[k], &fl); }
            CHECK(st0(&many[0], 3) == 1 && st0(&many[MAX_CARRIERS - 1], 4) == 1 && st0(&many[MAX_CARRIERS], 3) == 0,
                  "16 carriers synchronised, the 17th not (no crash)");
            tick_fn(NULL, NULL);
            CHECK(has("plus de 16 porte-avions"), "logged");
            for (k = 0; k <= MAX_CARRIERS; ++k) { free(many[k].states); many[k].states = NULL; }
        }
        sess_fn(NULL, 1, NULL); veh_make(&v1, &ch); enq_n = 0;
        press(&v1, 3); sync_tick(&v1, &fl);
        CHECK(enq_n == 0 && st0(&v1, 2) == 0, "new session: the first update seen copies nothing");
        g_sync = 0; press(&v1, 3); press(&v1, 3); press(&v1, 4); sync_tick(&v1, &fl);
        CHECK(enq_n == 0 && st0(&v1, 2) == 0, "synchronisation not installed: nothing");
        g_sync = 1; g_active = 0; sync_tick(&v1, &fl);
        CHECK(enq_n == 0 && st0(&v1, 2) == 0, "inactive plugin: nothing");
        g_active = 1;
        sync_tick(&v1, &fl);
        CHECK(enq_n == 3 && st0(&v1, 2) == 1, "back on: copy B's press (seen as a change) is copied (copy A was on already)");
    }

    printf("9. listes de joueurs abimees, etats non modifiables : rien n'est ecrit\n");
    {
        struct { const char *what; int reason; } cases[] = {
            {"liste illisible", 4}, {"liste : plus de joueurs que de places", 4}, {"liste trop grande", 4}, {"liste : tete hors limites", 4},
            {"joueur nul", 5}, {"file nulle", 5}, {"file : plus de messages que de places", 5}, {"file : tete hors limites", 5}};
        size_t k;
        for (k = 0; k < sizeof(cases) / sizeof(cases[0]); ++k) {
            const void *list = &fl;
            uint8_t before[8 * 5];
            sess_fn(NULL, 1, NULL); logbuf[0] = 0; enq_n = 0;
            veh_make(&v1, &ch); players(2, 4, 3);
            sync_tick(&v1, &fl);
            switch (k) {
            case 0: list = (const void *)0x10; break;
            case 1: fl.count = 5; break;
            case 2: fl.cap = MAX_PEERS + 1; fl.count = 0; break;
            case 3: fl.head = 4; break;
            case 4: fl_slots[0] = NULL; break;
            case 5: fp[1].queue = NULL; break;
            case 6: fq[0].count = 9; break;
            case 7: fq[1].head = 8; break;
            }
            press(&v1, 2); memcpy(before, v1.states, sizeof(before));
            sync_tick(&v1, list);
            CHECK(enq_n == 0 && memcmp(before, v1.states, sizeof(before)) == 0 && g_sync_off && g_sync_fail == cases[k].reason,
                  "%s: nothing written, nothing sent, stopped (reason %d)", cases[k].what, cases[k].reason);
            players(2, 4, 3); press(&v1, 2); press(&v1, 2); press(&v1, 3); sync_tick(&v1, &fl);
            CHECK(enq_n == 0 && st0(&v1, 2) == 1 && st0(&v1, 4) == 0, "%s: stays stopped for the session", cases[k].what);
            tick_fn(NULL, NULL); tick_fn(NULL, NULL);
            CHECK(count_of("synchronisation arretee pour cette partie") == 1, "%s: logged once", cases[k].what);
        }
        press(&v1, 2); press(&v1, 3);
        CHECK(both(old, v1.veh, 0) == 0, "stopped synchronisation: all off, released");
        press(&v1, 4);
        CHECK(both(old, v1.veh, 1) == 1, "stopped synchronisation: the copies still work (v1)");
        press(&v1, 4);
        sess_fn(NULL, 1, NULL);
        CHECK(!g_sync_off && !g_sync_fail, "next session: on again");
        {   /* the states in a page the game could not write */
            uint8_t *page = VirtualAlloc(NULL, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
            uint8_t *heap_states;
            DWORD old_prot;
            veh_make(&v1, &ch);
            heap_states = v1.states;
            memcpy(page, heap_states, 8 * 5);
            v1.states = page;
            memcpy(v1.veh + OFF_CTRL + CTRL_ARR, &v1.states, 4);
            { Ref r; memcpy(&r, v1.veh + OFF_REF, sizeof(r)); r.st = page + 16; memcpy(v1.veh + OFF_REF, &r, sizeof(r)); }
            enq_n = 0;
            sync_tick(&v1, &fl);
            press(&v1, 2);
            VirtualProtect(page, 0x1000, PAGE_READONLY, &old_prot);
            sync_tick(&v1, &fl);
            CHECK(enq_n == 0 && st0(&v1, 3) == 0 && st0(&v1, 4) == 0 && g_sync_off && g_sync_fail == 6, "read-only states: nothing written, nothing sent, stopped");
            VirtualProtect(page, 0x1000, PAGE_READWRITE, &old_prot);
            v1.states = heap_states;
            VirtualFree(page, 0, MEM_RELEASE);
        }
        sess_fn(NULL, 1, NULL);
        {   /* a carrier whose +0x80 is unreadable cannot be: +0x88 follows it; the v1 checks still refuse a broken carrier */
            Ref r;
            veh_make(&v1, &ch); sync_tick(&v1, &fl);
            memcpy(&r, v1.veh + OFF_REF, sizeof(r)); r.st += 8; memcpy(v1.veh + OFF_REF, &r, sizeof(r));
            press(&v1, 3); enq_n = 0; sync_tick(&v1, &fl);
            CHECK(enq_n == 0 && st0(&v1, 2) == 0 && g_fail == 2, "carrier failing the v1 checks: nothing written, reason 2");
        }
    }

    printf("10. code du jeu different : synchronisation non installee, la v1 reste\n");
    {
        uint32_t spots[] = {old->group, old->group + at_hex(k_group, "ffb780000000") + 2, old->group + at_hex(k_group, "8b4964") + 2,
                            old->group + at_hex(k_group, "6a00ff7424") + 1, old->group + GROUP_SITE, old->group + GROUP_SITE + 5,
                            old->group + GROUP_CALL + 1, old->enqueue, old->enqueue + at_hex(k_enqueue, "8a451088470c") + 2,
                            old->enqueue + 0xb7, FAKE_TYPE + 1, old->enqueue + 0x06, old->enqueue + 0x15 + 3, old->enqueue + 0x38 + 1,
                            old->enqueue + 0x45, old->enqueue + 0x45 + 3};
        size_t k;
        for (k = 0; k < sizeof(spots) / sizeof(spots[0]); ++k) {
            make_image(old, old->timestamp);
            img[spots[k] - 0x400000u] ^= 0x5a;
            reset_api();
            CHECK(cc2x_plugin_load(&api) == 1 && g_active && !g_sync && !g_enqueue && n_mid == 2 && has("synchronisation NON installee"),
                  "changed byte at %08x: loaded without the synchronisation", (unsigned)spots[k]);
        }
        g_enqueue = (Enqueue)(uintptr_t)fake_enqueue;
        sess_fn(NULL, 1, NULL); veh_make(&v1, &ch); enq_n = 0;
        sync_tick(&v1, &fl); press(&v1, 3); sync_tick(&v1, &fl);
        CHECK(enq_n == 0 && st0(&v1, 2) == 0, "without the synchronisation the hook site is not even patched; a call does nothing");
        CHECK(both(old, v1.veh, 1) == 1, "and copy A still holds (v1)");
        make_image(old, old->timestamp);
        img[old->enqueue + 0x2b - 0x400000u] ^= 0x5a;             /* inside the rel32 of "call new", it differs between the exes */
        reset_api();
        CHECK(cc2x_plugin_load(&api) == 1 && g_sync && n_mid == 3, "a byte of a call's rel32 under \"??\" may differ");
        make_image(old, old->timestamp);
        put(old->enqueue + 0x15, (const uint8_t *)&old->enq_abs[1], 4);   /* the cookie's address as in the file (not relocated) */
        reset_api();
        CHECK(cc2x_plugin_load(&api) == 1 && !g_sync && n_mid == 2 && has("differe en 0x00565cf5"),
              "an address left as in the file while the exe is loaded elsewhere: refused (the 13:14 bug, now a test)");
        make_image(old, old->timestamp);
        reset_api();
        CHECK(cc2x_plugin_load(&api) == 1 && g_sync && n_mid == 3, "the 4 addresses relocated as Windows does: accepted");
        make_image(nw, nw->timestamp);
        reset_api();
        CHECK(cc2x_plugin_load(&api) == 1 && g_sync && mids[2].site == 0x7061f0u, "new exe loaded with the synchronisation");
        g_enqueue = (Enqueue)(uintptr_t)fake_enqueue;
        sess_fn(NULL, 1, NULL); veh_make(&v1, &ch); players(1, 2, 1); enq_n = 0;
        sync_tick(&v1, &fl); press(&v1, 4); sync_tick(&v1, &fl);
        CHECK(st0(&v1, 2) == 1 && st0(&v1, 3) == 1 && enq_n == 2 && sent(0, &fq[0], &v1, 2, 1) && sent(1, &fq[0], &v1, 3, 1),
              "new exe: copy B -> original and copy A, one player");
    }

    printf("\n%d controles, %d echec(s)\n", pass + fail_n, fail_n);
    return fail_n ? 1 : 0;
}
