/* SPDX-License-Identifier: GPL-3.0-or-later */
/* cc2x_hold.c (v2.1) - CC2X plugin: the copies of the red "Hold On Deck" button added by the mod cc2_hold_copies work like the
 * original, and the original and its copies are kept in the same state: pressing any of them sets the others the same way.
 *
 * What the exe does (read in the 1.5.18 exe, 31/10/2026, see ../RAPPORT_exe_30-10.md and ../PLUGIN_hold.md):
 *   - at the carrier's creation the game binds the hold logic to the FIRST button named exactly "vehicle_control_air_hold"
 *     (0x6ed1c0 -> 0x63f360): a 12-byte reference {index, state, definition} kept at +0x560 of the carrier vehicle;
 *   - every button has an 8-byte state in the vehicle's controls (+0x88: definitions at +0x00, states at +0x4c, count at +0x50),
 *     created as {byte0 = 0, byte2 = 1} (0x84b130); a press on a type-18 button flips byte0 (0x5d5530);
 *   - the carrier's flight deck asks "is Hold on?" in two places (calls of 0x63f570 at 0x6fcd74 and 0x6fd942, both with
 *     ecx = carrier + 0x560 and the argument 1): the answer is byte0 != 0 and byte2 != 0 of the referenced state.
 *   A copy of the button has its own state, which nobody reads: that is why the copies did nothing on 30/10.
 *
 * v1 (kept): two mid-function hooks on the "lea ecx,[esi+0x560]" right before those two calls. If the original is off (and
 * usable: byte2 != 0) and a copy is on, ecx is pointed at a reference to that copy and the lea is skipped: the game's own
 * function then reads the copy's state. Before reading anything it checks, against what the game itself stored in the
 * reference, the offsets it relies on (state array, definition ring, names); on any mismatch it does nothing and logs it once.
 *
 * v2, the synchronisation (read in both exes on 31/10/2026, see ../PLUGIN_hold_v2.md and ../verifier_synchro_v2.py):
 *   - byte0 lives on the server. What the players SEE is each client's own copy (16-byte states, byte +0xc), changed only by the
 *     server's message 20 {vehicle id, button, value, flag}: 0x565ce0 queues one for one player, the client applies it in
 *     0x5ceb10 (and clicks only if flag != 0). Every game path that changes byte0 sends it: the presses (0x779c00, 0x782350,
 *     flag 1) and the carrier's own logic (self-destruct panel 0x6f0950, carrier controls 0x6ebec0, and the 6-button group at
 *     0x705fcd-0x7060da where a press releases the other five, flag 0). A bare write of byte0 would change the game logic but
 *     not what the players see.
 *   - so a third hook sits in the carrier update right after that 6-button group (0x7060e0, "xor ecx,ecx ; mov [esp+0x14],ecx"),
 *     where edi = the carrier and esi = the list of players the group has just used, and it does what the group does: when
 *     exactly one of the original and the copies changed byte0 since the last update, that value is written into byte0 of the
 *     others (never byte2) and message 20 (flag 0, as the group) is queued for each of them to each player of the list. Two
 *     changes in the same update, or the original made unusable by the game (byte2 = 0): nothing is copied. A copy with
 *     byte2 = 0 is neither copied from nor to. The players' queues are checked before anything is written; if a check fails,
 *     nothing is written and the synchronisation stops for the session (the v1 hooks go on).
 *   - the whole 216-byte block of the group (the list, [edi+0x80] = vehicle id, [player+0x64] = his queue, the call) and
 *     0x565ce0 itself (up to its "ret 0x10", its 4 addresses as relocated by Windows, and the type 20 of the message it builds)
 *     are checked byte by byte at load; if they differ, only the v1 hooks are installed. (v2 of 31/10 13:00 compared the
 *     security cookie's address with the file's bytes: in the game, loaded elsewhere than 0x400000, the synchronisation was
 *     refused at 0x565ce0. Fixed in v2.1.)
 *   In the update where a copy is pressed the flight deck runs before the synchronisation: it reads the copy through v1.
 *
 * The exe is recognised by its PE timestamp; the code at every address is checked byte by byte before anything is patched (the
 * SDK checks the displaced bytes again). The new Steam exe (461E1262) has the same code 0x100 to 0x120 bytes further (compared on
 * 31/10): its addresses are in the table, NOT tried in the game (the SDK does not load on that exe yet).
 *
 * xmm0-xmm7: the SDK's relay saves the general registers and the flags but not the SSE registers; the hook bodies call
 * VirtualQuery (and the game's 0x565ce0), which may use them, so the hooks go through the same assembly wrapper as cc2x_frein.c
 * (saves and restores xmm0-xmm7).
 */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>
#include "cc2x.h"

#define LOG(level, ...) A->log("hold", level, __VA_ARGS__)

#define OFF_REF 0x560             /* carrier vehicle -> reference of the hold button, as 0x63f360 fills it */
#define OFF_CTRL 0x88             /* vehicle -> its controls (0x6ed1c0: "add ebx,0x88"; 0x782565: "add ecx,0x88") */
#define OFF_ID 0x80               /* vehicle -> its id, as the group puts it in message 20 ("push [edi+0x80]" in k_group) */
#define CTRL_ARR 0x4c             /* controls -> 8-byte button states */
#define CTRL_COUNT 0x50           /* controls -> number of button states */
#define DEF_RING 0x120            /* chassis definition -> ring of buttons: base, capacity, head, count */
#define DEF_ELEM 0x58             /* size of one button definition; its name is the game's string {data, size, capacity} at +0 */
#define PEER_QUEUE 0x64           /* player -> his queue of messages ("mov ecx,[ecx+0x64]" in k_group) */
#define SITE_LEN 6
#define SYNC_LEN 6
#define MAX_COPIES 4
#define MAX_CARRIERS 16
#define MAX_NAME 64
#define MAX_PEERS 64
#define MAX_EVENTS 8
#define NBTN (1 + MAX_COPIES)     /* the original and its copies */
#define HOOK_SYNC 2               /* user value of the synchronisation hook (0 and 1: the two v1 hooks) */

static const char HOLD_NAME[] = "vehicle_control_air_hold";
static const char COPY_PREFIX[] = "vehicle_control_air_hold_copie";

typedef struct { int32_t idx; const uint8_t *st; const uint8_t *def; } Ref;   /* what 0x63f360 writes, what 0x63f570 reads */

typedef struct {
    uint32_t timestamp;
    const char *label;
    uint32_t site[2];             /* "lea ecx,[esi+0x560]" (6 bytes), hooked */
    uint32_t next[2];             /* the instruction after it */
    uint32_t call[2];             /* the "call reader" that uses ecx */
    uint32_t reader;              /* the game's "is the button on?" function */
    uint32_t group;               /* v2: start of k_group, the carrier's 6-button group (the synchronisation hook is at its end) */
    uint32_t enqueue;             /* v2: the game's "queue message 20 for one player" */
    uint32_t enq_abs[4];          /* v2: image VAs of the 4 addresses in it that Windows relocates (see k_enq_abs_at) */
} Build;

static const Build BUILDS[] = {
    {0x6a36c177u, "1.5.18 (ancien exe 8E7FCBB6)", {0x6fcd62u, 0x6fd93cu}, {0x6fcd68u, 0x6fd942u}, {0x6fcd74u, 0x6fd942u}, 0x63f570u,
     0x70600eu, 0x565ce0u, {0xc97dbdu, 0xe1db44u, 0xd1ee70u, 0xd2523cu}},
    {0x6ae228f3u, "nouvel exe Steam 461E1262 (jamais essaye)", {0x6fce72u, 0x6fda4cu}, {0x6fce78u, 0x6fda52u}, {0x6fce84u, 0x6fda52u},
     0x63f670u, 0x70611eu, 0x565e00u, {0xc97f5du, 0xe1db44u, 0xd1eea0u, 0xd25258u}},
};

#define GROUP_CALL 0xa2           /* in k_group: "call enqueue" */
#define GROUP_SITE 0xd2           /* in k_group: the hooked "xor ecx,ecx ; mov [esp+0x14],ecx", the last 6 bytes */
#define ENQ_MSG_VTABLE 3          /* enq_abs[3]: the vtable of message 20 */
/* Where k_enqueue holds an absolute address: the exe's relocation table lists exactly these four offsets in 0x565ce0..0x565d99
 * (the exception handler, the security cookie, the base vtable, the vtable of message 20), and none in k_group, k_lea, k_after1,
 * k_reader. The exe is loaded wherever Windows wants (ASLR): in memory each one is api->va(enq_abs[i]), not the file's bytes. */
static const uint8_t k_enq_abs_at[4] = {0x06, 0x15, 0x38, 0x45};

static const uint8_t k_lea[SITE_LEN] = {0x8d, 0x8e, 0x60, 0x05, 0x00, 0x00};                     /* lea ecx,[esi+0x560] */
static const uint8_t k_after1[12] = {0x6a, 0x01, 0xc7, 0x82, 0x74, 0x01, 0x00, 0x00, 0x07, 0x00, 0x00, 0x00};   /* push 1 ; mov [edx+0x174],7 */
static const uint8_t k_before2[2] = {0x6a, 0x01};                                                   /* push 1 */
static const uint8_t k_reader[39] = {0x55, 0x8b, 0xec, 0x8b, 0x41, 0x04, 0x85, 0xc0, 0x74, 0x17, 0x80, 0x38, 0x00, 0x74, 0x12,
                                     0x80, 0x78, 0x02, 0x00, 0x75, 0x06, 0x80, 0x7d, 0x08, 0x00, 0x75, 0x06, 0xb0, 0x01, 0x5d,
                                     0xc2, 0x04, 0x00, 0x32, 0xc0, 0x5d, 0xc2, 0x04, 0x00};
static const uint8_t k_sync[SYNC_LEN] = {0x33, 0xc9, 0x89, 0x4c, 0x24, 0x14};                     /* xor ecx,ecx ; mov [esp+0x14],ecx */
static const uint8_t k_type20[6] = {0xb8, 0x14, 0x00, 0x00, 0x00, 0xc3};                          /* the message's type(): mov eax,20 ; ret */

/* "??" = checked apart: the rel32 of a call (it differs between the two exes) or a relocated address (k_enq_abs_at).
 * 0x70600e..0x7060e5 of the old exe: "mov esi,[esp+0x34]",
 * the group (byte0 := this button is the chosen one, "mov dword [eax+4],0"), and for a changed button, for each player i of the
 * list esi {base, capacity, head, count}: "push 0 ; push value ; push [ref.idx] ; push [edi+0x80] ;
 * ecx = [base + ((head+i) mod capacity)*4] ; ecx = [ecx+0x64] ; call enqueue"; then the hooked site. */
static const char k_group[] =
    "8b74243433c0894424148b0a85c9740c8039007407c644242301eb09c64424230085c974233987e40500000f94c08801"
    "8b02c74004000000008b0285c074098038007404b001eb0232c038442423746933c9894c2418394e0c765e0f1f800000"
    "00008b0285c0740a803800c6442430017505c6442430008b56088b0603d18b4c241c6a00ff742434ff71fc8bca2b4e04"
    "3b5604ffb7800000000f42ca8b0c888b4964e8????????8b4c24188b54241c41894c24183b4e0c72a98b44241483c20c"
    "408954241c8944241483f8060f8238ffffff33c9894c2414";
/* 0x565ce0..0x565d99 of the old exe, thiscall (ecx = queue), "ret 0x10": a new 16-byte message 20 {vtable, vehicle id, button,
 * value byte, flag byte} appended to the queue's ring (+8 base, +0xc capacity, +0x10 head, +0x14 count; grown when full). */
static const char k_enqueue[] =
    "558bec6aff68????????64a10000000050515657a1????????33c5508d45f464a3000000008bf16a10e8????????8bf8"
    "83c404897df0c707????????c745fc00000000c707????????c745fcffffffff8b4e148b560c3bca751c8d0412b92000"
    "00003bc10f42c18d4e0850e8????????8b4e148b560c8b46104148894e1403c18bc82bca3bc20f42c88b4608893c888b"
    "45088947048b450c8947088a451088470c8a451488470d8b4df464890d00000000595f5e8be55dc21000";

typedef void(__attribute__((thiscall)) * Enqueue)(void *queue, uint32_t vehicle_id, uint32_t button, uint32_t value, uint32_t flag);

typedef struct {                  /* the copies found in one chassis definition (shared by every carrier) */
    const uint8_t *defobj, *hold_def;
    uint32_t count;
    int ncopies;
    uint32_t idx[MAX_COPIES];
    const uint8_t *def[MAX_COPIES];
    char name[MAX_COPIES][MAX_NAME];
    int logged;
} Cache;

typedef struct { const uint8_t *veh; int src; int logged_src; } Carrier;   /* src: -1 none, 0 original, 1.. copy n */

/* byte0 (0/1) of the original [0] and of the copies [1..] (buttons idx[]), as the synchronisation left them at the carrier's last update */
typedef struct { const uint8_t *veh; uint32_t id; int nb, unusable; uint32_t idx[NBTN]; uint8_t last[NBTN]; } Memo;

typedef struct { const uint8_t *veh; int kind, src, other, ntargets, value; uint32_t nmsg, n; } Event;   /* logged at the tick */
enum { EV_SYNC = 1, EV_BOTH, EV_UNUSABLE };

typedef struct { const uint8_t *const *base; uint32_t cap, head, count; } Players;   /* the list of players, as k_group reads it */

static const cc2x_api *A;
static const Build *g_build;
static int g_active;
static uint32_t g_next[2];
static Ref g_fake;                /* what ecx points to while a copy answers; used by the very next instruction (the call) */
static Cache g_cache;
static Carrier g_carriers[MAX_CARRIERS];
static uint32_t g_seen[2], g_redirects[2];
static int g_fail, g_fail_logged; /* first reason a check failed (see fail_text), logged once per session */
static Enqueue g_enqueue;
static int g_sync;                /* the synchronisation hook is installed */
static int g_sync_off;            /* stopped for this session after a failed check (the v1 hooks go on) */
static int g_sync_fail, g_sync_fail_logged, g_memo_full, g_memo_full_logged;
static Memo g_memo[MAX_CARRIERS];
static Event g_events[MAX_EVENTS];
static int g_nevents;
static uint32_t g_lost_events, g_sync_seen, g_syncs;

static int region(const void *p, size_t n, DWORD need) {
    MEMORY_BASIC_INFORMATION mbi;
    if (!p || !VirtualQuery(p, &mbi, sizeof(mbi)) || mbi.State != MEM_COMMIT) return 0;
    if (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) return 0;
    if (need && !(mbi.Protect & need)) return 0;
    return (uintptr_t)p + n <= (uintptr_t)mbi.BaseAddress + mbi.RegionSize;
}

static int readable(const void *p, size_t n) { return region(p, n, 0); }
static int writable(const void *p, size_t n) { return region(p, n, PAGE_READWRITE | PAGE_EXECUTE_READWRITE); }

static const char *fail_text(int r) {
    switch (r) {
    case 1: return "porte-avions illisible (+0x560 ou +0x88)";
    case 2: return "le repere du bouton Hold ne correspond pas au tableau des etats (+0x88+0x4c)";
    case 3: return "liste des boutons du chassis inattendue (+0x120) ou bouton Hold introuvable a son numero";
    default: return "?";
    }
}

static const char *sync_fail_text(int r) {
    switch (r) {
    case 4: return "liste des joueurs illisible ou inattendue";
    case 5: return "file de messages d'un joueur illisible ou inattendue";
    case 6: return "etat d'un bouton non modifiable";
    case 7: return "numero du porte-avions illisible (+0x80)";
    default: return "?";
    }
}

static int fail(int r) {
    if (!g_fail) g_fail = r;
    return -1;
}

static int sync_fail(int r) {
    if (!g_sync_fail) g_sync_fail = r;
    g_sync_off = 1;
    return -1;
}

/* The game's string at p: {data, size, capacity}. Copies it to out (NUL-terminated); 0 if unreadable or too long. */
static int read_name(const uint8_t *p, char *out, size_t cap) {
    const char *data;
    uint32_t size;
    if (!readable(p, 8)) return 0;
    memcpy(&data, p, sizeof(data));
    memcpy(&size, p + 4, 4);
    if (size == 0 || size >= cap || !readable(data, size + 1) || data[size] != 0) return 0;
    memcpy(out, data, size + 1);
    return 1;
}

/* the definition of button i, as 0x63f360 finds it: base + ((head + i) mod capacity) * 0x58 */
static const uint8_t *ring_elem(const uint8_t *base, uint32_t cap, uint32_t head, uint32_t i) {
    uint32_t k = head + i;
    if (k >= cap) k -= cap;
    return base + (size_t)k * DEF_ELEM;
}

static const Cache *cache_for(const uint8_t *defobj, const Ref *ref, uint32_t n) {
    const uint8_t *ring = defobj + DEF_RING, *base;
    uint32_t cap, head, count, i;
    char nm[MAX_NAME];
    if (g_cache.defobj && g_cache.defobj == defobj && g_cache.hold_def == ref->def && g_cache.count == n) return &g_cache;
    memset(&g_cache, 0, sizeof(g_cache));
    if (!defobj || !readable(ring, 16)) return NULL;
    memcpy(&base, ring, sizeof(base));
    memcpy(&cap, ring + 4, 4);
    memcpy(&head, ring + 8, 4);
    memcpy(&count, ring + 12, 4);
    if (count != n || count == 0 || cap < count || head >= cap || cap > 100000 || !readable(base, (size_t)cap * DEF_ELEM)) return NULL;
    if (ring_elem(base, cap, head, (uint32_t)ref->idx) != ref->def) return NULL;
    if (!read_name(ref->def, nm, sizeof(nm)) || strcmp(nm, HOLD_NAME) != 0) return NULL;
    for (i = 0; i < count && g_cache.ncopies < MAX_COPIES; ++i) {
        const uint8_t *e = ring_elem(base, cap, head, i);
        if (!read_name(e, nm, sizeof(nm)) || strncmp(nm, COPY_PREFIX, sizeof(COPY_PREFIX) - 1) != 0) continue;
        g_cache.idx[g_cache.ncopies] = i;
        g_cache.def[g_cache.ncopies] = e;
        memcpy(g_cache.name[g_cache.ncopies], nm, sizeof(nm));
        g_cache.ncopies++;
    }
    g_cache.defobj = defobj;
    g_cache.hold_def = ref->def;
    g_cache.count = n;
    return &g_cache;
}

/* The checks of one carrier (see the top): its state array, the reference of the original and the copies; NULL on a mismatch. */
static const Cache *carrier_buttons(const uint8_t *veh, const uint8_t **arr_out, const Ref **ref_out) {
    const Ref *ref;
    const uint8_t *ctrl, *arr, *defobj;
    const Cache *c;
    uint32_t n;
    if (!veh) { fail(1); return NULL; }
    ref = (const Ref *)(veh + OFF_REF);
    ctrl = veh + OFF_CTRL;
    if (!readable(ref, sizeof(Ref)) || !readable(ctrl, CTRL_COUNT + 4)) { fail(1); return NULL; }
    memcpy(&defobj, ctrl, sizeof(defobj));
    memcpy(&arr, ctrl + CTRL_ARR, sizeof(arr));
    memcpy(&n, ctrl + CTRL_COUNT, 4);
    if (!arr || ref->idx < 0 || (uint32_t)ref->idx >= n || n > 100000 || !readable(arr, 8u * n) || ref->st != arr + 8u * (uint32_t)ref->idx) {
        fail(2);
        return NULL;
    }
    if (!(c = cache_for(defobj, ref, n))) { fail(3); return NULL; }
    *arr_out = arr;
    *ref_out = ref;
    return c;
}

static void note(const uint8_t *veh, int src) {
    int i, free_slot = -1;
    for (i = 0; i < MAX_CARRIERS; ++i) {
        if (g_carriers[i].veh == veh) { g_carriers[i].src = src; return; }
        if (!g_carriers[i].veh && free_slot < 0) free_slot = i;
    }
    if (free_slot >= 0) {
        g_carriers[free_slot].veh = veh;
        g_carriers[free_slot].src = src;
        g_carriers[free_slot].logged_src = -2;
    }
}

/* Which copy should answer for this carrier: its number in g_cache, or -1 to let the game read the original. Fills g_fake. */
static int pick_copy(const uint8_t *veh) {
    const Ref *ref;
    const uint8_t *arr, *orig;
    const Cache *c;
    int i;
    if (!g_active) return -1;
    if (!(c = carrier_buttons(veh, &arr, &ref))) return -1;
    orig = arr + 8u * (uint32_t)ref->idx;
    if (orig[2] == 0) { note(veh, -1); return -1; }          /* the game made the original unusable: the copies do not override it */
    if (orig[0] != 0) { note(veh, 0); return -1; }           /* the original is on: the game reads it as usual */
    for (i = 0; i < c->ncopies; ++i) {
        const uint8_t *st = arr + 8u * c->idx[i];
        if (st[0] != 0 && st[2] != 0) {
            g_fake.idx = (int32_t)c->idx[i];
            g_fake.st = st;
            g_fake.def = c->def[i];
            note(veh, 1 + i);
            return i;
        }
    }
    note(veh, -1);
    return -1;
}

static Memo *memo_for(const uint8_t *veh, uint32_t id, int nb, const uint32_t *idx, int *fresh) {
    Memo *m;
    int i;
    for (i = 0; i < MAX_CARRIERS && g_memo[i].veh != veh; ++i) {}
    if (i == MAX_CARRIERS)
        for (i = 0; i < MAX_CARRIERS && g_memo[i].veh; ++i) {}
    if (i == MAX_CARRIERS) { g_memo_full = 1; return NULL; }
    m = &g_memo[i];
    /* another vehicle at that address, or other buttons: start again */
    *fresh = m->veh != veh || m->id != id || m->nb != nb || memcmp(m->idx, idx, sizeof(*idx) * (size_t)nb) != 0;
    if (*fresh) {
        memset(m, 0, sizeof(*m));
        m->veh = veh;
        m->id = id;
        m->nb = nb;
        memcpy(m->idx, idx, sizeof(*idx) * (size_t)nb);
    }
    return m;
}

static void event(const uint8_t *veh, int kind, int src, int other, int ntargets, int value, uint32_t nmsg) {
    Event *e;
    if (g_nevents >= MAX_EVENTS) { g_lost_events++; return; }
    e = &g_events[g_nevents++];
    e->veh = veh;
    e->kind = kind;
    e->src = src;
    e->other = other;
    e->ntargets = ntargets;
    e->value = value;
    e->nmsg = nmsg;
    e->n = g_syncs;
}

/* The queue of every player of the list, as k_group finds them, checked before anything is written: their number, or -1. */
static int player_queues(const void *list, void **q) {
    Players p;
    uint32_t i, f[4];
    if (!readable(list, sizeof(p))) return sync_fail(4);
    memcpy(&p, list, sizeof(p));
    if (p.count > p.cap || p.cap > MAX_PEERS || (p.cap && (p.head >= p.cap || !readable(p.base, 4u * p.cap)))) return sync_fail(4);
    for (i = 0; i < p.count; ++i) {
        uint32_t k = p.head + i;
        const uint8_t *player;
        if (k >= p.cap) k -= p.cap;
        player = p.base[k];
        if (!player || !readable(player + PEER_QUEUE, sizeof(void *))) return sync_fail(5);
        memcpy(&q[i], player + PEER_QUEUE, sizeof(void *));
        if (!readable(q[i], 0x18)) return sync_fail(5);
        memcpy(f, (const uint8_t *)q[i] + 8, sizeof(f));             /* base, capacity, head, count (k_enqueue) */
        if (f[3] > f[1] || f[1] > (1u << 20) || (f[1] && (f[2] >= f[1] || !readable((const void *)(uintptr_t)f[0], 4u * f[1]))))
            return sync_fail(5);
    }
    return (int)p.count;
}

/* The synchronisation hook: veh = the carrier (edi), list = the players (esi). See the top. */
static void sync_carrier(const uint8_t *veh, const void *list) {
    const Ref *ref;
    const uint8_t *arr;
    const Cache *c;
    Memo *m;
    uint8_t *st[NBTN], cur[NBTN];
    uint32_t idx[NBTN], id, nmsg = 0;
    void *q[MAX_PEERS];
    int i, j, nb, fresh, v, src = -1, other = -1, nchanged = 0, ntargets = 0, nplayers;
    if (!g_active || !g_sync || g_sync_off) return;
    if (!(c = carrier_buttons(veh, &arr, &ref)) || !c->ncopies) return;
    if (!readable(veh + OFF_ID, 4)) { sync_fail(7); return; }
    memcpy(&id, veh + OFF_ID, 4);
    nb = 1 + c->ncopies;
    idx[0] = (uint32_t)ref->idx;
    for (i = 1; i < nb; ++i) idx[i] = c->idx[i - 1];
    for (i = 0; i < nb; ++i) {
        st[i] = (uint8_t *)(uintptr_t)(arr + 8u * idx[i]);
        cur[i] = st[i][0] != 0;
    }
    if (!(m = memo_for(veh, id, nb, idx, &fresh))) return;          /* more than MAX_CARRIERS carriers: this one is not synchronised */
    if (fresh) { memcpy(m->last, cur, (size_t)nb); return; }   /* first update seen: nothing to compare with */
    if (st[0][2] == 0) {                                     /* the game made the original unusable: nothing is copied */
        if (!m->unusable) event(veh, EV_UNUSABLE, 0, -1, 0, 0, 0);
        m->unusable = 1;
        memcpy(m->last, cur, (size_t)nb);
        return;
    }
    m->unusable = 0;
    for (i = 0; i < nb; ++i) {
        if (st[i][2] == 0 || cur[i] == m->last[i]) continue;   /* an unusable copy is neither copied from nor to */
        if (nchanged++) other = i;
        else src = i;
    }
    if (nchanged != 1) {
        if (nchanged > 1) event(veh, EV_BOTH, src, other, 0, 0, 0);
        memcpy(m->last, cur, (size_t)nb);
        return;
    }
    v = cur[src];
    for (i = 0; i < nb; ++i) {
        if (i == src || st[i][2] == 0 || cur[i] == v) continue;
        if (!writable(st[i], 1)) { sync_fail(6); memcpy(m->last, cur, (size_t)nb); return; }
        ntargets++;
    }
    if (ntargets) {
        if ((nplayers = player_queues(list, q)) < 0) { memcpy(m->last, cur, (size_t)nb); return; }
        for (i = 0; i < nb; ++i) {
            if (i == src || st[i][2] == 0 || cur[i] == v) continue;
            st[i][0] = (uint8_t)v;                           /* as the group does; byte1..byte7 are left alone */
            cur[i] = (uint8_t)v;
            for (j = 0; j < nplayers; ++j) {
                g_enqueue(q[j], id, idx[i], (uint32_t)v, 0);
                nmsg++;
            }
        }
    }
    g_syncs++;
    event(veh, EV_SYNC, src, -1, ntargets, v, nmsg);
    memcpy(m->last, cur, (size_t)nb);
}

/* The three hooks. user 0 (0x6fcd62) and 1 (0x6fd93c): esi = the carrier vehicle, the displaced code is "lea ecx,[esi+0x560]".
 * user 2 (0x7060e0): edi = the carrier, esi = the list of players; nothing is changed in the registers. */
__attribute__((used, noinline)) static void hook_body(cc2x_cpu *cpu, void *user) {
    int w = (int)(intptr_t)user;
    if (w == HOOK_SYNC) {
        g_sync_seen++;
        sync_carrier((const uint8_t *)(uintptr_t)cpu->edi, (const void *)(uintptr_t)cpu->esi);
        return;
    }
    w &= 1;
    g_seen[w]++;
    if (pick_copy((const uint8_t *)(uintptr_t)cpu->esi) < 0) return;
    cpu->ecx = (uint32_t)(uintptr_t)&g_fake;
    cpu->jump_to = g_next[w];
    g_redirects[w]++;
}

/* Assembly wrapper (as in cc2x_frein.c): what the SDK's relay calls (cdecl, cpu and user on the stack); keeps xmm0-xmm7 exact. */
__attribute__((naked, used)) static void hook(cc2x_cpu *cpu, void *user) {
    __asm__("subl $0x80, %esp\n\t"
            "movups %xmm0, 0x00(%esp)\n\t" "movups %xmm1, 0x10(%esp)\n\t" "movups %xmm2, 0x20(%esp)\n\t" "movups %xmm3, 0x30(%esp)\n\t"
            "movups %xmm4, 0x40(%esp)\n\t" "movups %xmm5, 0x50(%esp)\n\t" "movups %xmm6, 0x60(%esp)\n\t" "movups %xmm7, 0x70(%esp)\n\t"
            "pushl 0x88(%esp)\n\t" "pushl 0x88(%esp)\n\t"
            "call _hook_body\n\t"
            "addl $8, %esp\n\t"
            "movups 0x00(%esp), %xmm0\n\t" "movups 0x10(%esp), %xmm1\n\t" "movups 0x20(%esp), %xmm2\n\t" "movups 0x30(%esp), %xmm3\n\t"
            "movups 0x40(%esp), %xmm4\n\t" "movups 0x50(%esp), %xmm5\n\t" "movups 0x60(%esp), %xmm6\n\t" "movups 0x70(%esp), %xmm7\n\t"
            "addl $0x80, %esp\n\t"
            "ret\n\t");
}

static const Build *which_build(uintptr_t base, uint32_t *ts) {
    const uint8_t *b = (const uint8_t *)base;
    uint32_t e;
    size_t i;
    *ts = 0;
    if (!readable(b, 0x40)) return NULL;
    memcpy(&e, b + 0x3c, 4);
    if (e > 0x1000 || !readable(b + e, 12) || memcmp(b + e, "PE\0\0", 4) != 0) return NULL;
    memcpy(ts, b + e + 8, 4);
    for (i = 0; i < sizeof(BUILDS) / sizeof(BUILDS[0]); ++i)
        if (BUILDS[i].timestamp == *ts) return &BUILDS[i];
    return NULL;
}

static int same(uint32_t image_va, const uint8_t *bytes, size_t n) {
    const void *p = (const void *)A->va(image_va);
    return readable(p, n) && memcmp(p, bytes, n) == 0;
}

static int hexval(char c) { return c >= '0' && c <= '9' ? c - '0' : c >= 'a' && c <= 'f' ? c - 'a' + 10 : -1; }

/* same() for a pattern written in hex, "??" = any byte */
static int same_hex(uint32_t image_va, const char *hex) {
    const uint8_t *p = (const uint8_t *)A->va(image_va);
    size_t i, n = strlen(hex) / 2;
    if (!readable(p, n)) return 0;
    for (i = 0; i < n; ++i) {
        int hi = hexval(hex[2 * i]), lo = hexval(hex[2 * i + 1]);
        if (hex[2 * i] == '?' && hex[2 * i + 1] == '?') continue;
        if (hi < 0 || lo < 0 || p[i] != (uint8_t)(hi * 16 + lo)) return 0;
    }
    return 1;
}

static int calls(uint32_t image_va, uint32_t target_va) {
    const uint8_t *p = (const uint8_t *)A->va(image_va);
    int32_t rel;
    if (!readable(p, 5) || p[0] != 0xe8) return 0;
    memcpy(&rel, p + 1, 4);
    return (uintptr_t)p + 5 + rel == A->va(target_va);
}

/* 0 = all the code we rely on is there, else the image VA where it differs */
static uint32_t check_code(const Build *bd) {
    int w;
    for (w = 0; w < 2; ++w) {
        if (!same(bd->site[w], k_lea, sizeof(k_lea))) return bd->site[w];
        if (!calls(bd->call[w], bd->reader)) return bd->call[w];
    }
    if (!same(bd->next[0], k_after1, sizeof(k_after1))) return bd->next[0];
    if (bd->next[0] + sizeof(k_after1) != bd->call[0]) return bd->call[0];
    if (!same(bd->site[1] - 2, k_before2, sizeof(k_before2))) return bd->site[1] - 2;
    if (bd->next[1] != bd->call[1]) return bd->call[1];
    if (!same(bd->reader, k_reader, sizeof(k_reader))) return bd->reader;
    return 0;
}

/* 0 = the synchronisation can be installed, else the image VA where the code differs */
static uint32_t check_sync(const Build *bd) {
    const uint8_t *e = (const uint8_t *)A->va(bd->enqueue), *vt, *type;
    uint32_t a, msg = bd->enqueue + k_enq_abs_at[ENQ_MSG_VTABLE];
    int i;
    if (!same_hex(bd->group, k_group)) return bd->group;
    if (!same(bd->group + GROUP_SITE, k_sync, sizeof(k_sync))) return bd->group + GROUP_SITE;
    if (!calls(bd->group + GROUP_CALL, bd->enqueue)) return bd->group + GROUP_CALL;
    if (!same_hex(bd->enqueue, k_enqueue)) return bd->enqueue;
    for (i = 0; i < 4; ++i) {                                        /* each relocated address, as Windows wrote it */
        memcpy(&a, e + k_enq_abs_at[i], 4);
        if (a != (uint32_t)A->va(bd->enq_abs[i])) return bd->enqueue + k_enq_abs_at[i];
    }
    vt = (const uint8_t *)A->va(bd->enq_abs[ENQ_MSG_VTABLE]);
    if (!readable(vt, 8)) return msg;
    memcpy(&a, vt + 4, 4);                                           /* vtable[1] = type(), an address in the running exe */
    type = (const uint8_t *)(uintptr_t)a;
    if (!readable(type, sizeof(k_type20)) || memcmp(type, k_type20, sizeof(k_type20)) != 0) return msg;
    return 0;
}

static void reset_session(void) {
    memset(&g_cache, 0, sizeof(g_cache));
    memset(g_carriers, 0, sizeof(g_carriers));
    memset(&g_fake, 0, sizeof(g_fake));
    memset(g_memo, 0, sizeof(g_memo));
    g_seen[0] = g_seen[1] = g_redirects[0] = g_redirects[1] = 0;
    g_fail = g_fail_logged = 0;
    g_sync_off = g_sync_fail = g_sync_fail_logged = g_memo_full = g_memo_full_logged = 0;
    g_nevents = 0;
    g_lost_events = g_sync_seen = g_syncs = 0;
}

static const char *src_text(int src) {
    if (src < 0) return "aucun bouton enclenche";
    if (src == 0) return "l'original";
    return src - 1 < g_cache.ncopies ? g_cache.name[src - 1] : "une copie";
}

static void log_event(const Event *e) {
    switch (e->kind) {
    case EV_SYNC:
        LOG(CC2X_LOG_INFO, "porte-avions %p : %s %s ; recopie sur %d autre(s) bouton(s), %u message(s) aux joueurs (synchronisation n. %u)",
            (const void *)e->veh, src_text(e->src), e->value ? "enclenche" : "desenclenche", e->ntargets, (unsigned)e->nmsg, (unsigned)e->n);
        break;
    case EV_BOTH:
        LOG(CC2X_LOG_WARN, "porte-avions %p : %s et %s ont change au meme instant : rien n'est recopie (appuyer de nouveau sur l'un d'eux)",
            (const void *)e->veh, src_text(e->src), src_text(e->other));
        break;
    case EV_UNUSABLE:
        LOG(CC2X_LOG_WARN, "porte-avions %p : le jeu a rendu le bouton Hold d'origine inutilisable (octet 2 = 0) : pas de synchronisation tant qu'il l'est",
            (const void *)e->veh);
        break;
    }
}

/* Logging is done here, on the server thread after the tick, never inside the hooks. */
static void on_tick(void *server, void *user) {
    int i;
    if (!g_active) return;
    if (g_fail && !g_fail_logged) {
        g_fail_logged = 1;
        LOG(CC2X_LOG_ERROR, "verification ratee : %s. Les copies n'agissent pas (le bouton d'origine marche comme avant).", fail_text(g_fail));
    }
    if (g_sync_fail && !g_sync_fail_logged) {
        g_sync_fail_logged = 1;
        LOG(CC2X_LOG_ERROR, "synchronisation arretee pour cette partie : %s. Rien n'a ete ecrit ; les copies marchent encore comme en v1.",
            sync_fail_text(g_sync_fail));
    }
    if (g_memo_full && !g_memo_full_logged) {
        g_memo_full_logged = 1;
        LOG(CC2X_LOG_WARN, "plus de %d porte-avions : les suivants ne sont pas synchronises", MAX_CARRIERS);
    }
    if (g_cache.defobj && !g_cache.logged) {
        g_cache.logged = 1;
        if (!g_cache.ncopies) LOG(CC2X_LOG_WARN, "aucune copie du bouton Hold dans le chassis (mod cc2_hold_copies absent ?) : rien a faire");
        for (i = 0; i < g_cache.ncopies; ++i) LOG(CC2X_LOG_INFO, "copie trouvee : %s (bouton n. %u)", g_cache.name[i], (unsigned)g_cache.idx[i]);
    }
    for (i = 0; i < g_nevents; ++i) log_event(&g_events[i]);
    g_nevents = 0;
    if (g_lost_events) {
        LOG(CC2X_LOG_WARN, "%u evenement(s) de synchronisation non journalise(s)", (unsigned)g_lost_events);
        g_lost_events = 0;
    }
    for (i = 0; i < MAX_CARRIERS; ++i) {
        Carrier *k = &g_carriers[i];
        if (!k->veh || k->src == k->logged_src) continue;
        k->logged_src = k->src;
        LOG(CC2X_LOG_INFO, "porte-avions %p : Hold demande par le jeu, repond %s (appels %u+%u, dont par une copie %u+%u)", (const void *)k->veh,
            src_text(k->src), (unsigned)g_seen[0], (unsigned)g_seen[1], (unsigned)g_redirects[0], (unsigned)g_redirects[1]);
    }
}

static void on_session(void *server, int started, void *user) {
    if (!g_active) return;
    LOG(CC2X_LOG_INFO, "session %s (appels %u+%u, dont par une copie %u+%u ; synchronisations %u)", started ? "commencee" : "finie",
        (unsigned)g_seen[0], (unsigned)g_seen[1], (unsigned)g_redirects[0], (unsigned)g_redirects[1], (unsigned)g_syncs);
    reset_session();
}

CC2X_EXPORT int cc2x_plugin_load(const cc2x_api *a) {
    uint32_t ts = 0, bad, sync_bad;
    if (!a || a->api_version < 3 || a->size < sizeof(cc2x_api) || !a->log || !a->va || !a->patch_begin || !a->patch_mid ||
        !a->patch_commit || !a->on_server_tick || !a->on_session)
        return 0;
    A = a;
    g_active = g_sync = 0;
    g_enqueue = NULL;
    g_build = NULL;
    reset_session();
    if (!(g_build = which_build(a->module_base, &ts))) {
        LOG(CC2X_LOG_WARN, "exe inconnu (horodatage PE %08x) : rien n'est installe", (unsigned)ts);
        return 0;
    }
    if ((bad = check_code(g_build))) {
        LOG(CC2X_LOG_ERROR, "%s : le code du jeu differe de l'attendu en 0x%08x : rien n'est installe", g_build->label, (unsigned)bad);
        return 0;
    }
    sync_bad = check_sync(g_build);
    g_next[0] = (uint32_t)a->va(g_build->next[0]);
    g_next[1] = (uint32_t)a->va(g_build->next[1]);
    a->patch_begin("hold");
    if (!a->patch_mid(g_build->site[0], SITE_LEN, k_lea, hook, (void *)(intptr_t)0) ||
        !a->patch_mid(g_build->site[1], SITE_LEN, k_lea, hook, (void *)(intptr_t)1) ||
        (!sync_bad && !a->patch_mid(g_build->group + GROUP_SITE, SYNC_LEN, k_sync, hook, (void *)(intptr_t)HOOK_SYNC))) {
        if (a->patch_abort) a->patch_abort();
        LOG(CC2X_LOG_ERROR, "%s : les crochets n'ont pas pu etre prepares : rien n'est installe", g_build->label);
        return 0;
    }
    if (!a->patch_commit()) {
        LOG(CC2X_LOG_ERROR, "%s : les crochets ont ete refuses par le SDK : rien n'est installe", g_build->label);
        return 0;
    }
    if (!sync_bad) g_enqueue = (Enqueue)a->va(g_build->enqueue);
    g_sync = !sync_bad;
    g_active = 1;
    a->on_server_tick(on_tick, NULL);
    a->on_session(on_session, NULL);
    LOG(CC2X_LOG_INFO, "%s : crochets poses en 0x%x et 0x%x ; une copie enclenchee du bouton Hold retient les avions comme l'original",
        g_build->label, (unsigned)g_build->site[0], (unsigned)g_build->site[1]);
    if (g_sync)
        LOG(CC2X_LOG_INFO, "%s : synchronisation posee en 0x%x : l'original et ses copies prennent le meme etat, ecran des joueurs compris",
            g_build->label, (unsigned)(g_build->group + GROUP_SITE));
    else
        LOG(CC2X_LOG_WARN, "%s : synchronisation NON installee (le code du jeu differe en 0x%08x) : les copies marchent comme en v1",
            g_build->label, (unsigned)sync_bad);
    return 1;
}
