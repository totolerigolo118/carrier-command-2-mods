/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "cp_hook.h"

#include <string.h>

_Static_assert(sizeof(cp_hook_ctx) == 128 + 32 + 4 + 4, "cp_hook_ctx must mirror the trampoline frame");
_Static_assert(offsetof(cp_hook_ctx, edi) == 128, "pushad block follows the 8 xmm slots");
_Static_assert(offsetof(cp_hook_ctx, eflags) == 160, "eflags follows the pushad block");
_Static_assert(offsetof(cp_hook_ctx, jump_to) == 164, "jump_to is the first thing pushed");

typedef struct emitter {
    uint8_t *p;
    size_t n, cap;
    int overflow;
} emitter;

static void put8(emitter *e, unsigned v) {
    if (e->n < e->cap) e->p[e->n] = (uint8_t)v;
    else e->overflow = 1;
    ++e->n;
}
static void put32(emitter *e, uint32_t v) {
    for (int i = 0; i < 4; ++i) put8(e, (v >> (8 * i)) & 0xff);
}
static void bytes(emitter *e, const uint8_t *b, size_t n) {
    for (size_t i = 0; i < n; ++i) put8(e, b[i]);
}
#define BYTES(e, ...) bytes((e), (const uint8_t[]){ __VA_ARGS__ }, sizeof((const uint8_t[]){ __VA_ARGS__ }))

/* movups [esp+16*i], xmm_i  (0F 11 /r, ModRM 01 reg 100, SIB 24, disp8; i = 0 has no disp) */
static void save_xmm(emitter *e, int i) {
    if (i == 0) BYTES(e, 0x0f, 0x11, 0x04, 0x24);
    else BYTES(e, 0x0f, 0x11, (unsigned)(0x44 | (i << 3)), 0x24, (unsigned)(16 * i));
}
/* movups xmm_i, [esp+16*i]  (0F 10 /r) */
static void load_xmm(emitter *e, int i) {
    if (i == 0) BYTES(e, 0x0f, 0x10, 0x04, 0x24);
    else BYTES(e, 0x0f, 0x10, (unsigned)(0x44 | (i << 3)), 0x24, (unsigned)(16 * i));
}

cp_hook_status cp_hook_emit(uint8_t *out, size_t cap, size_t *used, cp_addr base, cp_addr site,
                            const uint8_t *displaced, uint32_t len, cp_addr callback, cp_addr user_arg) {
    if (!out || !displaced || !callback) return CP_HOOK_BAD_ARGS;
    if (len < CP_HOOK_MIN_LEN) return CP_HOOK_TOO_SHORT;
    if (len > CP_HOOK_MAX_LEN) return CP_HOOK_BAD_ARGS;
    uint8_t first = displaced[0];
    if (first == 0xEB || (first >= 0x70 && first <= 0x7F) || (first >= 0xE0 && first <= 0xE3))
        return CP_HOOK_SHORT_BRANCH;
    if (cap < CP_HOOK_DISPLACED_OFF + len + 5) return CP_HOOK_NO_SPACE;

    emitter e = { out, 0, cap, 0 };
    put8(&e, 0x68);                                        /* push imm32 = default jump_to */
    put32(&e, base + CP_HOOK_DISPLACED_OFF);
    put8(&e, 0x9c);                                        /* pushfd */
    put8(&e, 0x60);                                        /* pushad */
    BYTES(&e, 0x81, 0xec, 0x80, 0x00, 0x00, 0x00);         /* sub esp, 128 */
    for (int i = 0; i < 8; ++i) save_xmm(&e, i);
    BYTES(&e, 0x89, 0xe6);                                 /* mov esi, esp */
    put8(&e, 0xfc);                                        /* cld */
    BYTES(&e, 0x83, 0xe4, 0xf0);                           /* and esp, -16 */
    BYTES(&e, 0x83, 0xec, 0x08);                           /* sub esp, 8 */
    put8(&e, 0x68);                                        /* push user */
    put32(&e, user_arg);
    put8(&e, 0x56);                                        /* push esi (= ctx) */
    put8(&e, 0xb8);                                        /* mov eax, callback */
    put32(&e, callback);
    BYTES(&e, 0xff, 0xd0);                                 /* call eax */
    BYTES(&e, 0x89, 0xf4);                                 /* mov esp, esi */
    for (int i = 0; i < 8; ++i) load_xmm(&e, i);
    BYTES(&e, 0x81, 0xc4, 0x80, 0x00, 0x00, 0x00);         /* add esp, 128 */
    put8(&e, 0x61);                                        /* popad */
    put8(&e, 0x9d);                                        /* popfd */
    put8(&e, 0xc3);                                        /* ret -> ctx->jump_to */
    if (e.n != CP_HOOK_DISPLACED_OFF) return CP_HOOK_BAD_ARGS;   /* the constant and the code disagree */

    /* displaced instructions, first one relocated if it is a rel32 call / jmp / jcc */
    size_t copy = e.n;
    bytes(&e, displaced, len);
    int rel_off = -1;
    uint32_t insn_len = 0;
    if (first == 0xE8 || first == 0xE9) { rel_off = 1; insn_len = 5; }
    else if (first == 0x0F && displaced[1] >= 0x80 && displaced[1] <= 0x8F) { rel_off = 2; insn_len = 6; }
    if (rel_off >= 0 && len >= insn_len) {
        uint32_t rel = (uint32_t)displaced[rel_off] | ((uint32_t)displaced[rel_off + 1] << 8) |
                       ((uint32_t)displaced[rel_off + 2] << 16) | ((uint32_t)displaced[rel_off + 3] << 24);
        cp_addr target = site + insn_len + rel;
        uint32_t moved = target - (base + (uint32_t)copy + insn_len);
        for (int i = 0; i < 4; ++i) out[copy + (size_t)rel_off + (size_t)i] = (uint8_t)(moved >> (8 * i));
    }
    put8(&e, 0xe9);                                        /* jmp site + len */
    put32(&e, (site + len) - (base + (uint32_t)e.n + 4));
    if (e.overflow) return CP_HOOK_NO_SPACE;
    if (used) *used = e.n;
    return CP_HOOK_OK;
}

void cp_hook_site_bytes(uint8_t *out, cp_addr site, cp_addr trampoline, uint32_t len) {
    uint32_t rel = trampoline - (site + 5);
    out[0] = 0xe9;
    for (int i = 0; i < 4; ++i) out[1 + i] = (uint8_t)(rel >> (8 * i));
    for (uint32_t i = 5; i < len; ++i) out[i] = 0x90;
}
