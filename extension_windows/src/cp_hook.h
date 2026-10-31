/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * XMM-safe mid-function hook.
 *
 * Why: the SDK's patch_mid() saves the general registers only. Our Mac caves broke on exactly this:
 * a C callback called from the middle of a computation overwrites xmm0-xmm7 that the game still
 * needs. The trampoline built here saves and restores EFLAGS, the general registers AND xmm0-xmm7
 * around a C callback, and exposes all of them in a cp_hook_ctx the callback may change.
 *
 * What the trampoline looks like (x86-32, built by cp_hook_emit; code size CP_HOOK_DISPLACED_OFF bytes,
 * then the displaced instructions, then a jump back):
 *
 *     push  <default continuation>      ; becomes ctx->jump_to
 *     pushfd ; pushad                   ; ctx->eflags, general registers
 *     sub   esp, 128 ; movups [esp+16*i], xmm<i>   (i = 0..7)
 *     mov   esi, esp                    ; esi = ctx (callee-saved in cdecl: survives the callback)
 *     cld ; and esp, -16 ; sub esp, 8   ; DF clear, stack 16-byte aligned for the C callee
 *     push  <user> ; push esi ; mov eax, <callback> ; call eax      ; callback(ctx, user)
 *     mov   esp, esi ; movups xmm<i>, [esp+16*i] ; add esp, 128
 *     popad ; popfd ; ret               ; "ret" jumps to ctx->jump_to
 *     <displaced instructions> ; jmp <site + len>
 *
 * CONSTRAINTS on the displaced instructions (the bytes of the site, copied into the trampoline):
 *  - They must be whole instructions, at least 5 bytes in total (the site is overwritten by a
 *    5-byte "jmp rel32" plus nops).
 *  - They are executed AFTER the callback and after every register has been restored (with the
 *    callback's changes), at a different address. So they must be position independent: no relative
 *    jump or call, EXCEPT a first instruction that is a rel32 call / jmp / jcc, which is relocated
 *    (its target is kept). A short branch (EB, 7x, E0-E3) as first instruction is refused. A
 *    relative branch anywhere else in the displaced bytes is NOT detected (no disassembler here):
 *    whoever fills the site table must check it. Absolute operands (disp32) are fine.
 *  - No other code of the game may jump into the middle of the overwritten bytes (check the
 *    references to the addresses site+1 .. site+len-1 in Ghidra).
 *  - The callback may set ctx->jump_to to another absolute (rebased) address to skip the displaced
 *    instructions and continue there; it must then keep the stack as the game expects.
 *
 * NOT saved: the x87 stack / control words and MXCSR. Do not hook code in the middle of x87 float
 * arithmetic (live st(i) would be lost). The callback is plain C (cdecl) and must not change esp.
 * Nothing here has run inside the game: it is only verified on the host (see tests/).
 */
#ifndef CP_HOOK_H
#define CP_HOOK_H

#include "cp_types.h"

/* Registers at the hook site. Layout = the trampoline's stack frame, lowest address first. */
typedef struct cp_hook_ctx {
    float xmm[8][4];                  /* xmm0..xmm7, lane 0 first: ctx->xmm[1][0] is the scalar in xmm1 */
    uint32_t edi, esi, ebp, esp_unused, ebx, edx, ecx, eax;   /* pushad order */
    uint32_t eflags;
    uint32_t jump_to;                 /* default: the displaced instructions; may be changed */
} cp_hook_ctx;

/* The stack of the hooked code: CP_HOOK_STACK(ctx)[0] is [esp] at the site, [1] is [esp+4]... */
#define CP_HOOK_STACK(ctx) ((uint32_t *)((uint8_t *)(ctx) + sizeof(cp_hook_ctx)))

typedef void (*cp_hook_fn)(cp_hook_ctx *ctx, void *user);

#define CP_HOOK_MIN_LEN 5              /* bytes overwritten at the site: jmp rel32 + nops */
#define CP_HOOK_MAX_LEN 16
#define CP_HOOK_DISPLACED_OFF 124      /* offset of the displaced copy inside the trampoline */
#define CP_HOOK_MAX_SIZE (CP_HOOK_DISPLACED_OFF + CP_HOOK_MAX_LEN + 5)

typedef enum cp_hook_status {
    CP_HOOK_OK = 0,
    CP_HOOK_BAD_ARGS,
    CP_HOOK_TOO_SHORT,       /* fewer than CP_HOOK_MIN_LEN displaced bytes */
    CP_HOOK_SHORT_BRANCH,    /* first displaced instruction is a rel8 branch: cannot be relocated */
    CP_HOOK_NO_SPACE
} cp_hook_status;

/* Build the trampoline into out[cap] for a site at `site` whose first `len` bytes are `displaced`.
 * `base` is the address the trampoline will have (needed for the relocation and the jump back).
 * `callback` and `user_arg` are 32-bit values (a function address and the second argument). */
cp_hook_status cp_hook_emit(uint8_t *out, size_t cap, size_t *used, cp_addr base, cp_addr site,
                            const uint8_t *displaced, uint32_t len, cp_addr callback, cp_addr user_arg);

/* The bytes written over the site: jmp rel32 to the trampoline, then nops up to len. */
void cp_hook_site_bytes(uint8_t *out, cp_addr site, cp_addr trampoline, uint32_t len);

#endif
