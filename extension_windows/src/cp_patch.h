/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * Safe patch layer. Pure logic: every access to memory goes through the cp_env callbacks, so the
 * host-side tests run it over a fake memory buffer and the Windows build plugs in VirtualProtect /
 * FlushInstructionCache (cp_win.c).
 *
 * Addresses in the tables are image VAs for the base 0x00400000 (what Ghidra shows), and the
 * `expected` bytes are the bytes of the .exe FILE. At run time the loader may have moved the image
 * (ASLR) and then fixes up every absolute operand in the code, so the layer rebases the operands
 * it knows about (kind abs_float: the disp32; `abs_ops`: more operands) before comparing.
 */
#ifndef CP_PATCH_H
#define CP_PATCH_H

#include "cp_hook.h"
#include "cp_tunables.h"
#include "cp_types.h"

#define CP_MAX_SITE_LEN 16
#define CP_MAX_GROUP_SITES 64
#define CP_MAX_RECS 256

typedef enum cp_site_kind {
    CP_SITE_NONE = 0,
    /* an instruction with a 32-bit ABSOLUTE operand that reads a float constant (movss, mulss,
     * addss, subss, comiss, addps...): the operand is redirected to one of our tunables */
    CP_SITE_ABS_FLOAT,
    /* raw bytes replaced in place (an immediate, an opcode...). With .tunable set, the 4 bytes at
     * .off are filled with the float bits of that tunable instead of using .repl */
    CP_SITE_IMM,
    /* a rel32 branch (E9, E8, 0F 8x) whose target is moved to .target (an image VA) */
    CP_SITE_JUMP,
    /* mid-function hook: the site is overwritten by a jump to an XMM-safe trampoline that calls
     * the C callback .hook (see cp_hook.h) */
    CP_SITE_HOOK
} cp_site_kind;

enum {
    CP_SF_NO_STOCK_CHECK = 1   /* abs_float: do not check the value of the original constant */
};

typedef struct cp_site {
    uint32_t addr;                       /* image VA of the first byte */
    uint8_t len;                         /* number of bytes the site covers (1..CP_MAX_SITE_LEN) */
    uint8_t kind;                        /* cp_site_kind */
    uint8_t tunable;                     /* cp_tunable_id (abs_float, imm with a float) */
    uint8_t off;                         /* abs_float: offset of the disp32; imm: offset of the float; jump: offset of the rel32 */
    uint8_t abs_ops[3];                  /* imm / hook: offsets of image-VA operands inside the bytes (absolute
                                            addresses of the game) to rebase in expected (and repl); 0 = unused */
    uint8_t flags;                       /* CP_SF_* */
    uint16_t hook;                       /* hook id (cp_hooks.h) for CP_SITE_HOOK */
    uint32_t target;                     /* jump: image VA of the new target */
    uint8_t expected[CP_MAX_SITE_LEN];   /* original bytes, as in the .exe file */
    uint8_t repl[CP_MAX_SITE_LEN];       /* imm without tunable: the replacement bytes */
} cp_site;

/* Table helpers. Fields not named are zero. Usage:
 *   CP_ABS_FLOAT(0x00xxxxxx, 8, 4, CP_T_TAXI_ACCEL, CP_BYTES(0xf3,0x0f,0x58,0x25, 0x..,0x..,0x..,0x..))
 *   CP_JUMP(0x00xxxxxx, 6, 2, 0x00yyyyyy, CP_BYTES(0x0f,0x86, 0x..,0x..,0x..,0x..))
 *   CP_HOOK(0x00xxxxxx, 8, CP_HOOK_ID_X, CP_BYTES(...))
 *   { .addr = ..., .len = ..., .kind = CP_SITE_IMM, .expected = CP_BYTES(...), .repl = CP_BYTES(...) } */
#define CP_BYTES(...) { __VA_ARGS__ }
#define CP_ABS_FLOAT(a, n, disp_off, tun, exp_bytes) \
    { .addr = (a), .len = (n), .kind = CP_SITE_ABS_FLOAT, .tunable = (tun), .off = (disp_off), .expected = exp_bytes }
#define CP_JUMP(a, n, rel_off, tgt, exp_bytes) \
    { .addr = (a), .len = (n), .kind = CP_SITE_JUMP, .off = (rel_off), .target = (tgt), .expected = exp_bytes }
#define CP_HOOK(a, n, hook_id, exp_bytes) \
    { .addr = (a), .len = (n), .kind = CP_SITE_HOOK, .hook = (hook_id), .expected = exp_bytes }

/* ------------------------------------------------------------------------------------------ */

typedef struct cp_env {
    void *user;
    /* copy len bytes at a into out; 1 = readable */
    int (*read)(void *user, cp_addr a, void *out, uint32_t len);
    /* write len bytes at a: Windows = VirtualProtect + copy + restore protection + FlushInstructionCache */
    int (*write)(void *user, cp_addr a, const void *data, uint32_t len);
    /* executable, writable memory for trampolines; 0 = failure */
    cp_addr (*alloc_exec)(void *user, uint32_t len);
    /* image VA (base 0x400000) -> runtime address (api->va); NULL = identity */
    cp_addr (*va)(void *user, uint32_t image_va);
    /* address of the C callback of a hook id; 0 = unknown id */
    cp_addr (*hook_addr)(void *user, int hook_id);
    void (*log)(void *user, int level, const char *message);
    /* runtime image range, used to refuse an absolute operand that points outside the game
     * (0 = not checked) */
    cp_addr image_lo;
    uint32_t image_size;
} cp_env;

typedef enum cp_status {
    CP_OK = 0,          /* written and verified */
    CP_ALREADY,         /* the new bytes are already there: nothing written */
    CP_ERR_ARGS,
    CP_ERR_READ,        /* target not readable */
    CP_ERR_MISMATCH,    /* bytes are neither the expected nor the new ones: refused, nothing written */
    CP_ERR_WRITE,
    CP_ERR_VERIFY       /* read-back differs: the original bytes were written back */
} cp_status;

/* Single patch: verify the original bytes, write, read back. Idempotent: a second call finds the
 * new bytes and returns CP_ALREADY without writing. expected and new must differ. */
cp_status cp_write(const cp_env *env, cp_addr addr, const uint8_t *expected, const uint8_t *newb, uint32_t len);
const char *cp_status_text(cp_status s);

/* FLOAT REDIRECT HELPER (kind abs_float). `orig_rt` holds the original instruction with its absolute
 * operand already rebased (it is what memory contains). On success `out` receives the same
 * instruction with the 32-bit operand at site->off replaced by the address of our tunable; the game's
 * constant is never written. Refuses (returns 0 and fills `why`) if: the tunable table is not bound or
 * not 16-byte aligned; the old operand points outside the game image; the original constant does not
 * hold the stock value of the tunable (unless CP_SF_NO_STOCK_CHECK). */
int cp_abs_float_redirect(const cp_env *env, const cp_tunables *tun, const cp_site *site, const uint8_t *orig_rt,
                          uint8_t *out, char *why, size_t why_cap);

/* ------------------------------------------------------------------------------------------ */

typedef enum cp_group_status {
    CP_GRP_APPLIED = 0,
    CP_GRP_ALREADY,       /* applied earlier in this session, bytes still in place: nothing written */
    CP_GRP_REFUSED,       /* nothing was written */
    CP_GRP_ROLLED_BACK,   /* a write failed; every site written before it was restored */
    CP_GRP_BROKEN         /* a write failed AND a restore failed: the game code is inconsistent */
} cp_group_status;

typedef struct cp_result {
    cp_group_status status;
    int site;             /* index of the site that caused a refusal / failure, -1 if none */
    int n_sites;          /* sites written (APPLIED) */
    char reason[192];
} cp_result;

typedef struct cp_rec {
    cp_addr addr;         /* runtime address */
    uint8_t group, len;
    uint8_t orig[CP_MAX_SITE_LEN], now[CP_MAX_SITE_LEN];
} cp_rec;

typedef struct cp_session {
    cp_env env;
    const cp_tunables *tun;
    cp_rec recs[CP_MAX_RECS];
    int n_recs;
} cp_session;

void cp_session_init(cp_session *s, const cp_env *env, const cp_tunables *tun);

/* Apply all sites of a group or none (see cp_group_status). Refuses empty tables, malformed
 * sites, overlaps (inside the group and with sites of other groups applied before), bytes that
 * differ from `expected`, abs_float constants that do not hold the stock value. Idempotent. */
void cp_group_apply(cp_session *s, int group_id, const cp_site *sites, int n, cp_result *res);
/* Put the original bytes back (tests, emergency). Returns the number of sites restored, -1 on error. */
int cp_group_revert(cp_session *s, int group_id);

#endif
