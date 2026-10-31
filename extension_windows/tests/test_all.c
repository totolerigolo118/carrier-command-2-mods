/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * Host-side tests (Linux). Nothing here runs the game: the patch layer works over a fake 32-bit
 * address space (fake_mem.h) and the plugin entry over a fake CC2X API.
 */
#include <math.h>
#include <stddef.h>
#include <stdint.h>

#include "cc2x.h"
#include "cp_config.h"
#include "cp_groups.h"
#include "cp_hooks.h"
#include "cp_ini.h"
#include "cp_patch.h"
#include "cp_pe.h"
#include "cp_speed.h"
#include "cp_test.h"
#include "fake_mem.h"
#include "fake_platform.h"

/* the plugin's one export (CC2X_EXPORT is empty on the host) */
int cc2x_plugin_load(const cc2x_api *api);

/* ============================================================================ fixture */

typedef struct fx {
    fake_mem m;
    cp_env env;
    cp_tunables tun;      /* 16-aligned */
    cp_session s;
} fx;

static fx F;
static uint8_t snap[FM_IMG_SIZE];

static void fx_init(void) {
    fm_init(&F.m);
    fm_env(&F.m, &F.env);
    cp_tun_init(&F.tun);
    CHECK(cp_tun_bind(&F.tun, FM_TUN_BASE));
    cp_session_init(&F.s, &F.env, &F.tun);
}
static void snapshot(void) { memcpy(snap, F.m.image, sizeof(snap)); }
static int unchanged(void) { return memcmp(snap, F.m.image, sizeof(snap)) == 0; }

static uint32_t bits(float f) { uint32_t u; memcpy(&u, &f, 4); return u; }
static uint32_t le32(const uint8_t *p) { return p[0] | (p[1] << 8) | (p[2] << 16) | ((uint32_t)p[3] << 24); }

#define SITE_VA(i) (0x00401000u + 0x10u * (unsigned)(i))

/* five 4-byte raw-bytes sites; memory holds the expected bytes */
static cp_site imm5[5];
static void make_imm5(void) {
    for (int i = 0; i < 5; ++i) {
        memset(&imm5[i], 0, sizeof(imm5[i]));
        imm5[i].addr = SITE_VA(i);
        imm5[i].len = 4;
        imm5[i].kind = CP_SITE_IMM;
        for (int k = 0; k < 4; ++k) {
            imm5[i].expected[k] = (uint8_t)(0x10 * (k + 1) + i);
            imm5[i].repl[k] = (uint8_t)(0x90 + 0x10 * k + i);
        }
        fm_put(&F.m, SITE_VA(i), imm5[i].expected, 4);
    }
}

/* ============================================================================ cp_write */

static void test_write_basic(void) {
    fx_init();
    const uint8_t e[4] = { 1, 2, 3, 4 }, n[4] = { 9, 8, 7, 6 };
    fm_put(&F.m, 0x00402000, e, 4);
    cp_addr a = fm_va_to_rt(0x00402000);
    CHECK_EQ(cp_write(&F.env, a, e, n, 4), CP_OK);
    CHECK(memcmp(fm_at(&F.m, 0x00402000), n, 4) == 0);
    CHECK_EQ(F.m.writes, 1);
    CHECK_EQ(cp_write(&F.env, a, e, e, 4), CP_ERR_ARGS);               /* expected == new */
    CHECK_EQ(cp_write(&F.env, 0x0badf00d, e, n, 4), CP_ERR_READ);      /* unreadable address */
    CHECK_EQ(cp_write(&F.env, a, e, n, 0), CP_ERR_ARGS);
    CHECK_EQ(cp_write(&F.env, a, e, n, CP_MAX_SITE_LEN + 1), CP_ERR_ARGS);
}

static void test_write_wrong_expected_refused(void) {
    fx_init();
    const uint8_t actual[4] = { 1, 2, 3, 4 }, wrong[4] = { 1, 2, 3, 5 }, n[4] = { 9, 8, 7, 6 };
    fm_put(&F.m, 0x00402000, actual, 4);
    snapshot();
    CHECK_EQ(cp_write(&F.env, fm_va_to_rt(0x00402000), wrong, n, 4), CP_ERR_MISMATCH);
    CHECK_EQ(F.m.writes, 0);                 /* nothing written */
    CHECK(unchanged());
}

static void test_write_idempotent(void) {
    fx_init();
    const uint8_t e[4] = { 1, 2, 3, 4 }, n[4] = { 9, 8, 7, 6 };
    fm_put(&F.m, 0x00402000, e, 4);
    cp_addr a = fm_va_to_rt(0x00402000);
    CHECK_EQ(cp_write(&F.env, a, e, n, 4), CP_OK);
    int w = F.m.writes;
    CHECK_EQ(cp_write(&F.env, a, e, n, 4), CP_ALREADY);
    CHECK_EQ(F.m.writes, w);                 /* second call wrote nothing */
    CHECK(memcmp(fm_at(&F.m, 0x00402000), n, 4) == 0);
}

static void test_write_failures_restore(void) {
    fx_init();
    const uint8_t e[4] = { 1, 2, 3, 4 }, n[4] = { 9, 8, 7, 6 };
    cp_addr a = fm_va_to_rt(0x00402000);
    fm_put(&F.m, 0x00402000, e, 4);
    F.m.fail_nth_write = 1;                  /* VirtualProtect fails */
    CHECK_EQ(cp_write(&F.env, a, e, n, 4), CP_ERR_WRITE);
    CHECK(memcmp(fm_at(&F.m, 0x00402000), e, 4) == 0);
    F.m.fail_nth_write = 0;
    F.m.writes = 0;
    F.m.corrupt_nth_write = 1;               /* memory ends up different from what was written */
    CHECK_EQ(cp_write(&F.env, a, e, n, 4), CP_ERR_VERIFY);
    CHECK(memcmp(fm_at(&F.m, 0x00402000), e, 4) == 0);   /* original bytes written back */
}

/* ============================================================================ groups */

static void test_group_all_sites_ok(void) {
    fx_init();
    make_imm5();
    cp_result r;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    CHECK_EQ(r.n_sites, 5);
    for (int i = 0; i < 5; ++i) CHECK(memcmp(fm_at(&F.m, SITE_VA(i)), imm5[i].repl, 4) == 0);
    CHECK_EQ(F.m.writes, 5);
}

static void test_group_wrong_bytes_refused_nothing_written(void) {
    fx_init();
    make_imm5();
    imm5[2].expected[1] ^= 0x55;             /* table says something else than the memory holds */
    snapshot();
    cp_result r;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    CHECK_EQ(r.site, 2);
    CHECK_STR_HAS(r.reason, "expected");
    CHECK_EQ(F.m.writes, 0);                 /* all-or-none: even sites 0 and 1 were not touched */
    CHECK(unchanged());
}

static void test_group_write_failure_rolls_back(void) {
    fx_init();
    make_imm5();
    snapshot();
    F.m.fail_nth_write = 4;                  /* the 4th site cannot be written */
    cp_result r;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_ROLLED_BACK);
    CHECK_EQ(r.site, 3);
    CHECK(unchanged());                      /* the 3 sites written before it were restored */
    CHECK_EQ(F.s.n_recs, 0);
    /* and a later retry works */
    F.m.fail_nth_write = 0;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
}

static void test_group_verify_failure_rolls_back(void) {
    fx_init();
    make_imm5();
    snapshot();
    F.m.corrupt_nth_write = 3;
    cp_result r;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_ROLLED_BACK);
    CHECK(unchanged());
}

static void test_group_rollback_failure_reported(void) {
    fx_init();
    make_imm5();
    F.m.fail_writes_from = 3;                /* from the 3rd write nothing can be written, restores included */
    cp_result r;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_BROKEN);
    CHECK_STR_HAS(r.reason, "RESTORE FAILED");
}

static void test_group_overlap_refused(void) {
    fx_init();
    make_imm5();
    imm5[2].addr = imm5[1].addr + 2;         /* sites 1 and 2 share two bytes */
    snapshot();
    cp_result r;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    CHECK_STR_HAS(r.reason, "overlap");
    CHECK_EQ(F.m.writes, 0);
    CHECK(unchanged());
}

static void test_group_overlap_with_other_group_refused(void) {
    fx_init();
    make_imm5();
    cp_result r;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    cp_site other = imm5[3];                 /* a site of ANOTHER group on bytes group 0 already patched */
    other.addr += 1;
    memcpy(other.expected, fm_at(&F.m, other.addr), 4);
    int w = F.m.writes;
    cp_group_apply(&F.s, 1, &other, 1, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    CHECK_STR_HAS(r.reason, "overlaps a site of group 0");
    CHECK_EQ(F.m.writes, w);
}

static void test_group_second_apply_idempotent(void) {
    fx_init();
    make_imm5();
    cp_result r;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    int w = F.m.writes, recs = F.s.n_recs;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_ALREADY);
    CHECK_EQ(F.m.writes, w);                 /* not one byte written the second time */
    CHECK_EQ(F.s.n_recs, recs);
    for (int i = 0; i < 5; ++i) CHECK(memcmp(fm_at(&F.m, SITE_VA(i)), imm5[i].repl, 4) == 0);
    /* if someone changed a patched byte meanwhile, the second call refuses instead of lying */
    fm_at(&F.m, SITE_VA(2))[0] ^= 1;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
}

static void test_group_empty_and_malformed_refused(void) {
    fx_init();
    cp_result r;
    cp_group_apply(&F.s, 0, NULL, 0, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    CHECK_STR_HAS(r.reason, "empty");
    make_imm5();
    imm5[0].len = 0;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    make_imm5();
    imm5[4].kind = 99;
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    make_imm5();
    imm5[1].repl[0] = imm5[1].expected[0];   /* a patch that changes nothing in a 1-byte-wide sense is fine... */
    imm5[1].repl[1] = imm5[1].expected[1];
    imm5[1].repl[2] = imm5[1].expected[2];
    imm5[1].repl[3] = imm5[1].expected[3];   /* ...but one that changes nothing at all is a table error */
    cp_group_apply(&F.s, 0, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    CHECK_STR_HAS(r.reason, "change nothing");
}

static void test_group_revert(void) {
    fx_init();
    make_imm5();
    snapshot();
    cp_result r;
    cp_group_apply(&F.s, 3, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    CHECK(!unchanged());
    CHECK_EQ(cp_group_revert(&F.s, 3), 5);
    CHECK(unchanged());
    CHECK_EQ(F.s.n_recs, 0);
    cp_group_apply(&F.s, 3, imm5, 5, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
}

/* ============================================================================ site kinds */

/* addss xmm4, [abs32]: f3 0f 58 25 <abs32>; the table holds the image VA of the constant */
static cp_site abs_site(uint32_t site_va, uint32_t const_va, int tunable) {
    cp_site s;
    memset(&s, 0, sizeof(s));
    s.addr = site_va;
    s.len = 8;
    s.kind = CP_SITE_ABS_FLOAT;
    s.tunable = (uint8_t)tunable;
    s.off = 4;
    const uint8_t op[4] = { 0xf3, 0x0f, 0x58, 0x25 };
    memcpy(s.expected, op, 4);
    for (int i = 0; i < 4; ++i) s.expected[4 + i] = (uint8_t)(const_va >> (8 * i));
    return s;
}
/* what the loader leaves in memory when the image is not at its preferred base: operand rebased */
static void put_abs_site_in_memory(const cp_site *s) {
    uint8_t b[8];
    memcpy(b, s->expected, 8);
    uint32_t rt = fm_va_to_rt(le32(s->expected + s->off));
    for (int i = 0; i < 4; ++i) b[s->off + i] = (uint8_t)(rt >> (8 * i));
    fm_put(&F.m, s->addr, b, 8);
}

static void test_kind_abs_float_redirect_and_rebase(void) {
    fx_init();
    fm_put_f32(&F.m, 0x0040F000, 0.05f);
    cp_site s = abs_site(0x00401100, 0x0040F000, CP_T_TAXI_ACCEL);
    put_abs_site_in_memory(&s);
    cp_result r;
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    const uint8_t *p = fm_at(&F.m, 0x00401100);
    CHECK(memcmp(p, s.expected, 4) == 0);                                     /* opcode bytes unchanged */
    CHECK_EQ(le32(p + 4), FM_TUN_BASE + 16 * CP_T_TAXI_ACCEL);                /* operand = our tunable */
    CHECK_EQ(le32(p + 4) & 15u, 0);                                           /* 16-byte aligned */
    /* the game's own constant is never modified */
    float c;
    memcpy(&c, fm_at(&F.m, 0x0040F000), 4);
    CHECK(bits(c) == bits(0.05f));
}

static void test_kind_abs_float_unrebased_operand_refused(void) {
    /* if the image sits at another base, memory holds the REBASED operand; a table compared without
     * rebasing would never match. Here memory holds the un-rebased operand: must be refused. */
    fx_init();
    fm_put_f32(&F.m, 0x0040F000, 0.05f);
    cp_site s = abs_site(0x00401100, 0x0040F000, CP_T_TAXI_ACCEL);
    fm_put(&F.m, s.addr, s.expected, 8);
    snapshot();
    cp_result r;
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    CHECK(unchanged());
}

static void test_kind_abs_float_stock_value_checked(void) {
    fx_init();
    fm_put_f32(&F.m, 0x0040F000, 0.06f);                       /* not the stock 0.05 */
    cp_site s = abs_site(0x00401100, 0x0040F000, CP_T_TAXI_ACCEL);
    put_abs_site_in_memory(&s);
    snapshot();
    cp_result r;
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    CHECK_STR_HAS(r.reason, "stock value");
    CHECK(unchanged());
    /* explicit opt-out of the check */
    s.flags = CP_SF_NO_STOCK_CHECK;
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
}

static void test_kind_abs_float_operand_outside_image_refused(void) {
    fx_init();
    cp_site s = abs_site(0x00401100, 0x00500000, CP_T_TAXI_ACCEL);   /* beyond SizeOfImage */
    put_abs_site_in_memory(&s);
    snapshot();
    cp_result r;
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    CHECK_STR_HAS(r.reason, "outside the game image");
    CHECK(unchanged());
}

static void test_kind_abs_float_vec4_needs_aligned_table(void) {
    fx_init();
    const float stock[4] = { 1000.0f, -600.0f, 0.0f, 0.0f };
    fm_put(&F.m, 0x0040F020, stock, 16);
    cp_site s;                                                 /* addps xmm1, [abs32]: 0f 58 0d <abs32> */
    memset(&s, 0, sizeof(s));
    s.addr = 0x00401200; s.len = 7; s.kind = CP_SITE_ABS_FLOAT; s.tunable = CP_T_CIRCLE_FWD_VEC; s.off = 3;
    const uint8_t op[3] = { 0x0f, 0x58, 0x0d };
    memcpy(s.expected, op, 3);
    s.expected[3] = 0x20; s.expected[4] = 0xf0; s.expected[5] = 0x40; s.expected[6] = 0x00;
    put_abs_site_in_memory(&s);
    cp_result r;
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    CHECK_EQ(le32(fm_at(&F.m, 0x00401200) + 3), FM_TUN_BASE + 16 * CP_T_CIRCLE_FWD_VEC);
    /* a vector constant whose other lanes differ is not the stock vector: refused */
    fx_init();
    const float odd[4] = { 1000.0f, -600.0f, 1.0f, 2.0f };
    fm_put(&F.m, 0x0040F020, odd, 16);
    put_abs_site_in_memory(&s);
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    /* a table bound to a misaligned address is refused up front */
    fx_init();
    CHECK(!cp_tun_bind(&F.tun, FM_TUN_BASE + 4));
    fm_put(&F.m, 0x0040F020, stock, 16);
    put_abs_site_in_memory(&s);
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    CHECK_STR_HAS(r.reason, "not bound");
}

static void test_kind_imm_with_float_from_tunable(void) {
    fx_init();
    /* mov dword [edi+0x118], imm32 0.4f : c7 87 18 01 00 00 <imm32> */
    cp_site s;
    memset(&s, 0, sizeof(s));
    s.addr = 0x00401300; s.len = 10; s.kind = CP_SITE_IMM; s.tunable = CP_T_ENERGY_SHARE; s.off = 6;
    const uint8_t e[10] = { 0xc7, 0x87, 0x18, 0x01, 0, 0, 0xcd, 0xcc, 0xcc, 0x3e };
    memcpy(s.expected, e, 10);
    fm_put(&F.m, s.addr, e, 10);
    cp_result r;
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    const uint8_t *p = fm_at(&F.m, 0x00401300);
    CHECK(memcmp(p, e, 6) == 0);
    CHECK_EQ(le32(p + 6), 0x3F4CCCCDu);                        /* 0.8f, the Mac default */
    /* overridden from the ini: 0.6 */
    fx_init();
    CHECK_EQ(cp_tun_set_by_key(&F.tun, "energy_share", 0.6), 1);
    fm_put(&F.m, s.addr, e, 10);
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    CHECK_EQ(le32(fm_at(&F.m, 0x00401300) + 6), bits(0.6f));
}

static void test_kind_imm_rebases_absolute_operands(void) {
    fx_init();
    cp_site s;                                                 /* mov eax, [abs32] -> mov eax, [other abs32] */
    memset(&s, 0, sizeof(s));
    s.addr = 0x00401400; s.len = 5; s.kind = CP_SITE_IMM; s.abs_ops[0] = 1;
    const uint8_t e[5] = { 0xa1, 0x00, 0x80, 0x40, 0x00 }, n[5] = { 0xa1, 0x04, 0x80, 0x40, 0x00 };
    memcpy(s.expected, e, 5);
    memcpy(s.repl, n, 5);
    const uint8_t rt_e[5] = { 0xa1, 0x00, 0x80, 0x00, 0x01 };   /* runtime operand = image base + 0x8000 */
    fm_put(&F.m, s.addr, rt_e, 5);
    cp_result r;
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    const uint8_t rt_n[5] = { 0xa1, 0x04, 0x80, 0x00, 0x01 };
    CHECK(memcmp(fm_at(&F.m, 0x00401400), rt_n, 5) == 0);
}

static void test_kind_jump_retargets_rel32(void) {
    fx_init();
    cp_site j, c;
    memset(&j, 0, sizeof(j));
    memset(&c, 0, sizeof(c));
    /* jmp 0x00401300 at 0x00401200: e9 fb 00 00 00 -> target 0x00401400: e9 fb 01 00 00 */
    j = (cp_site)CP_JUMP(0x00401200, 5, 1, 0x00401400, CP_BYTES(0xe9, 0xfb, 0x00, 0x00, 0x00));
    /* jbe 0x00401500 at 0x00401220 (0f 86 rel32, 6 bytes) -> target 0x00401600 */
    c = (cp_site)CP_JUMP(0x00401220, 6, 2, 0x00401600, CP_BYTES(0x0f, 0x86, 0xda, 0x02, 0x00, 0x00));
    fm_put(&F.m, j.addr, j.expected, 5);
    fm_put(&F.m, c.addr, c.expected, 6);
    cp_site both[2] = { j, c };
    cp_result r;
    cp_group_apply(&F.s, 0, both, 2, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    const uint8_t want_j[5] = { 0xe9, 0xfb, 0x01, 0x00, 0x00 };
    CHECK(memcmp(fm_at(&F.m, 0x00401200), want_j, 5) == 0);
    CHECK_EQ(le32(fm_at(&F.m, 0x00401220) + 2), 0x3dau);          /* 0x00401600 - (0x00401220 + 6) */
    CHECK(memcmp(fm_at(&F.m, 0x00401220), "\x0f\x86", 2) == 0);   /* opcode bytes untouched */
}

static void test_kind_jump_malformed_refused(void) {
    fx_init();
    cp_site s = CP_JUMP(0x00401200, 4, 1, 0x00401400, CP_BYTES(0xe9, 0xfb, 0x00, 0x00));    /* 4 bytes: not a rel32 branch */
    fm_put(&F.m, s.addr, s.expected, 4);
    cp_result r;
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    CHECK_STR_HAS(r.reason, "rel32");
    s = (cp_site)CP_JUMP(0x00401200, 5, 1, 0x00401300, CP_BYTES(0xe9, 0xfb, 0x00, 0x00, 0x00));  /* same target: no-op */
    fm_put(&F.m, s.addr, s.expected, 5);
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    CHECK_STR_HAS(r.reason, "change nothing");
}

static void test_kind_hook_builds_trampoline(void) {
    fx_init();
    /* lea eax,[eax+1] ; nop dword [eax]  = 6 bytes, position independent */
    cp_site s = CP_HOOK(0x00401300, 6, CP_HOOK_HELI_HEIGHT, CP_BYTES(0x8d, 0x40, 0x01, 0x0f, 0x1f, 0x00));
    fm_put(&F.m, s.addr, s.expected, 6);
    cp_result r;
    cp_group_apply(&F.s, 2, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    cp_addr site_rt = fm_va_to_rt(0x00401300);
    const uint8_t *p = fm_at(&F.m, 0x00401300);
    CHECK_EQ(p[0], 0xe9);
    CHECK_EQ(le32(p + 1), FM_ARENA_BASE - (site_rt + 5));      /* jmp to the first allocation */
    CHECK_EQ(p[5], 0x90);                                      /* padded with a nop */
    /* the trampoline is exactly what cp_hook_emit builds for these arguments */
    uint8_t want[CP_HOOK_MAX_SIZE];
    size_t used = 0;
    CHECK_EQ(cp_hook_emit(want, sizeof(want), &used, FM_ARENA_BASE, site_rt, s.expected, 6,
                          fm_hook_addr(NULL, CP_HOOK_HELI_HEIGHT), (2u << 16) | 0u), CP_HOOK_OK);
    CHECK(memcmp(F.m.arena, want, used) == 0);
    CHECK(memcmp(F.m.arena + CP_HOOK_DISPLACED_OFF, s.expected, 6) == 0);   /* displaced copy */
    /* second apply: nothing allocated, nothing written */
    int w = F.m.writes;
    uint32_t arena = F.m.arena_next;
    cp_group_apply(&F.s, 2, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_ALREADY);
    CHECK_EQ(F.m.writes, w);
    CHECK_EQ(F.m.arena_next, arena);
}

static void test_kind_hook_displaced_absolute_operand(void) {
    fx_init();
    /* maxss xmm1,[abs32] : f3 0f 5f 0d <abs32>; the copy in the trampoline must hold the RUNTIME operand */
    cp_site s = CP_HOOK(0x00401400, 8, CP_HOOK_HELI_HEIGHT, CP_BYTES(0xf3, 0x0f, 0x5f, 0x0d, 0x00, 0xf0, 0x40, 0x00));
    s.abs_ops[0] = 4;
    const uint8_t rt[8] = { 0xf3, 0x0f, 0x5f, 0x0d, 0x00, 0xf0, 0x00, 0x01 };
    fm_put(&F.m, s.addr, rt, 8);
    cp_result r;
    cp_group_apply(&F.s, 0, &s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_APPLIED);
    CHECK(memcmp(F.m.arena + CP_HOOK_DISPLACED_OFF, rt, 8) == 0);
}

static void refused_untouched(const cp_site *s, const char *needle) {
    cp_result r;
    fm_put(&F.m, s->addr, s->expected, s->len);
    snapshot();
    cp_group_apply(&F.s, 0, s, 1, &r);
    CHECK_EQ(r.status, CP_GRP_REFUSED);
    if (needle) CHECK_STR_HAS(r.reason, needle);
    CHECK(unchanged());                       /* the game code was not touched */
    CHECK_EQ(F.s.n_recs, 0);
}

static void test_kind_hook_refusals_leave_game_untouched(void) {
    fx_init();
    cp_site s = CP_HOOK(0x00401300, 6, CP_HOOK_HELI_HEIGHT, CP_BYTES(0xeb, 0x10, 0x01, 0x0f, 0x1f, 0x00));   /* short jmp first */
    refused_untouched(&s, "trampoline refused");
    s = (cp_site)CP_HOOK(0x00401300, 4, CP_HOOK_HELI_HEIGHT, CP_BYTES(0x8d, 0x40, 0x01, 0x90));            /* too short */
    refused_untouched(&s, "5..16 bytes");
    s = (cp_site)CP_HOOK(0x00401300, 6, 0, CP_BYTES(0x8d, 0x40, 0x01, 0x0f, 0x1f, 0x00));                   /* no hook id */
    refused_untouched(&s, "hook id missing");
    s = (cp_site)CP_HOOK(0x00401300, 17, CP_HOOK_HELI_HEIGHT, CP_BYTES(0x90));                              /* too long */
    refused_untouched(&s, "length out of range");
    /* an id that has no callback */
    fx_init();
    F.env.hook_addr = NULL;
    cp_session_init(&F.s, &F.env, &F.tun);
    s = (cp_site)CP_HOOK(0x00401300, 6, CP_HOOK_HELI_HEIGHT, CP_BYTES(0x8d, 0x40, 0x01, 0x0f, 0x1f, 0x00));
    refused_untouched(&s, "no implementation");
    /* trampoline memory that cannot be written */
    fx_init();
    F.m.fail_writes_from = 1;
    refused_untouched(&s, "trampoline");
    /* no executable memory at all */
    fx_init();
    F.env.alloc_exec = NULL;
    cp_session_init(&F.s, &F.env, &F.tun);
    refused_untouched(&s, "executable memory");
}

/* ============================================================================ hook emitter */

static void test_hook_emit_relocation_and_limits(void) {
    uint8_t out[CP_HOOK_MAX_SIZE];
    size_t used = 0;
    const cp_addr base = 0x30000000u, site = 0x01001000u;
    /* leading call rel32 is relocated: it must still reach the same target */
    const uint8_t call[6] = { 0xe8, 0x10, 0x02, 0x00, 0x00, 0x90 };         /* call site+5+0x210, nop */
    CHECK_EQ(cp_hook_emit(out, sizeof(out), &used, base, site, call, 6, 0x70000100u, 0), CP_HOOK_OK);
    cp_addr target = site + 5 + 0x210u;
    cp_addr moved = base + CP_HOOK_DISPLACED_OFF + 5 + le32(out + CP_HOOK_DISPLACED_OFF + 1);
    CHECK_EQ(moved, target);
    CHECK_EQ(out[CP_HOOK_DISPLACED_OFF + 5], 0x90);                        /* the rest is copied as is */
    cp_addr back = base + CP_HOOK_DISPLACED_OFF + 6 + 5 + le32(out + CP_HOOK_DISPLACED_OFF + 7);
    CHECK_EQ(back, site + 6);                                              /* jmp back after the site */
    /* leading jcc rel32 (0f 8x) relocated too */
    const uint8_t jcc[6] = { 0x0f, 0x84, 0x00, 0x01, 0x00, 0x00 };
    CHECK_EQ(cp_hook_emit(out, sizeof(out), &used, base, site, jcc, 6, 0x70000100u, 0), CP_HOOK_OK);
    moved = base + CP_HOOK_DISPLACED_OFF + 6 + le32(out + CP_HOOK_DISPLACED_OFF + 2);
    CHECK_EQ(moved, site + 6 + 0x100u);
    /* short branches as first instruction, too-short sites, bad sizes */
    const uint8_t jmp8[6] = { 0xeb, 0x05, 0x90, 0x90, 0x90, 0x90 };
    CHECK_EQ(cp_hook_emit(out, sizeof(out), &used, base, site, jmp8, 6, 0x70000100u, 0), CP_HOOK_SHORT_BRANCH);
    const uint8_t jz8[6] = { 0x74, 0x05, 0x90, 0x90, 0x90, 0x90 };
    CHECK_EQ(cp_hook_emit(out, sizeof(out), &used, base, site, jz8, 6, 0x70000100u, 0), CP_HOOK_SHORT_BRANCH);
    CHECK_EQ(cp_hook_emit(out, sizeof(out), &used, base, site, call, 4, 0x70000100u, 0), CP_HOOK_TOO_SHORT);
    CHECK_EQ(cp_hook_emit(out, 100, &used, base, site, call, 6, 0x70000100u, 0), CP_HOOK_NO_SPACE);
    CHECK_EQ(cp_hook_emit(out, sizeof(out), &used, base, site, call, 6, 0, 0), CP_HOOK_BAD_ARGS);
    CHECK_EQ(cp_hook_emit(out, sizeof(out), &used, base, site, call, CP_HOOK_MAX_LEN + 1, 0x70000100u, 0), CP_HOOK_BAD_ARGS);
}

static void test_hook_emit_layout(void) {
    uint8_t out[CP_HOOK_MAX_SIZE];
    size_t used = 0;
    const uint8_t disp[6] = { 0x8d, 0x40, 0x01, 0x0f, 0x1f, 0x00 };
    CHECK_EQ(cp_hook_emit(out, sizeof(out), &used, 0x30000000u, 0x01001000u, disp, 6, 0x70000100u, 0x00020003u), CP_HOOK_OK);
    CHECK_EQ(used, CP_HOOK_DISPLACED_OFF + 6 + 5);
    CHECK_EQ(out[0], 0x68);                                                /* push default jump_to */
    CHECK_EQ(le32(out + 1), 0x30000000u + CP_HOOK_DISPLACED_OFF);
    CHECK_EQ(out[5], 0x9c);                                                /* pushfd */
    CHECK_EQ(out[6], 0x60);                                                /* pushad */
    CHECK_EQ(out[CP_HOOK_DISPLACED_OFF - 1], 0xc3);                        /* ret */
    CHECK_EQ(out[CP_HOOK_DISPLACED_OFF - 2], 0x9d);                        /* popfd */
    CHECK_EQ(out[CP_HOOK_DISPLACED_OFF - 3], 0x61);                        /* popad */
    /* every one of xmm0..7 is stored and reloaded: movups [esp(+disp8)], xmm_r  (0f 11)  and back (0f 10) */
    unsigned stores = 0, loads = 0;
    for (size_t i = 0; i + 3 < CP_HOOK_DISPLACED_OFF; ++i) {
        if (out[i] != 0x0f || (out[i + 1] != 0x11 && out[i + 1] != 0x10) || out[i + 3] != 0x24) continue;
        unsigned mod_rm = out[i + 2], reg = (mod_rm >> 3) & 7;
        if ((mod_rm & 0xc7) != 0x04 && (mod_rm & 0xc7) != 0x44) continue;
        if (out[i + 1] == 0x11) stores |= 1u << reg; else loads |= 1u << reg;
    }
    CHECK_EQ(stores, 0xff);
    CHECK_EQ(loads, 0xff);
    /* user argument and callback address are embedded */
    int found_user = 0, found_cb = 0;
    for (size_t i = 0; i + 5 <= CP_HOOK_DISPLACED_OFF; ++i) {
        if (out[i] == 0x68 && le32(out + i + 1) == 0x00020003u) found_user = 1;
        if (out[i] == 0xb8 && le32(out + i + 1) == 0x70000100u) found_cb = 1;
    }
    CHECK(found_user && found_cb);
    /* dump for objdump (see run_tests.sh): built at address 0 for a site at 0x1000 so the addresses read easily */
    uint8_t dump[CP_HOOK_MAX_SIZE];
    size_t dump_len = 0;
    CHECK_EQ(cp_hook_emit(dump, sizeof(dump), &dump_len, 0, 0x1000, disp, 6, 0x70000100u, 0x00020003u), CP_HOOK_OK);
    FILE *f = fopen("build/trampoline.bin", "wb");
    if (f) { fwrite(dump, 1, dump_len, f); fclose(f); }
}

_Static_assert(offsetof(cp_hook_ctx, xmm) == 0, "xmm block first");
_Static_assert(sizeof(((cp_hook_ctx *)0)->xmm) == 128, "8 xmm of 16 bytes");

/* ============================================================================ tunables */

static void test_tunables_alignment(void) {
    cp_tunables *t = &F.tun;
    cp_tun_init(t);
    CHECK(cp_tun_bind(t, FM_TUN_BASE));
    CHECK(cp_tun_check_alignment(t));
    CHECK_EQ(((uintptr_t)t->v) & 15u, 0);
    for (int i = 1; i < CP_T_COUNT; ++i) {
        CHECK_EQ(((uintptr_t)&t->v[i]) & 15u, 0);             /* real memory */
        CHECK_EQ(cp_tun_addr(t, i) & 15u, 0);                 /* address handed to the game */
        CHECK_EQ(cp_tun_addr(t, i), FM_TUN_BASE + 16u * (unsigned)i);
    }
    CHECK_EQ(sizeof(t->v[0]), 16);
    CHECK(!cp_tun_bind(t, FM_TUN_BASE + 8));                  /* misaligned base refused */
    CHECK_EQ(cp_tun_addr(t, CP_T_TAXI_CAP), 0);
    CHECK(!cp_tun_check_alignment(t));
    CHECK_EQ(cp_tun_addr(t, 0), 0);
    CHECK_EQ(cp_tun_addr(t, CP_T_COUNT), 0);
    /* the plugin's own table is a static of the same type: checked at load time too */
    static cp_tunables st;
    cp_tun_init(&st);
    CHECK_EQ(((uintptr_t)st.v) & 15u, 0);
}

static void test_tunables_defaults_are_mac_values(void) {
    cp_tunables *t = &F.tun;
    cp_tun_init(t);
    const struct { int id; uint32_t def, stock; } W[] = {            /* passation_windows/PASSATION_windows.md section 6 */
        { CP_T_ENERGY_SHARE, 0x3F4CCCCD, 0x3ECCCCCD },
        { CP_T_PLATFORM_STEP, 0x3D4CCCCD, 0x3CCCCCCD }, { CP_T_PLATFORM_STEP_NEG, 0xBD4CCCCD, 0xBCCCCCCD },
        { CP_T_CRANE_H, 0x3EAAAAAB, 0x3E2AAAAB },        { CP_T_CRANE_H_NEG, 0xBEAAAAAB, 0xBE2AAAAB },
        { CP_T_CRANE_V, 0x3D888889, 0x3D088889 },        { CP_T_CRANE_V_NEG, 0xBD888889, 0xBD088889 },
        { CP_T_CRANE_ROT, 0x3DA3D70A, 0x3D23D70A },      { CP_T_CRANE_ROT_NEG, 0xBDA3D70A, 0xBD23D70A },
        { CP_T_TAXI_ACCEL, 0x3DCCCCCD, 0x3D4CCCCD },     { CP_T_TAXI_CAP, 0x40A00000, 0x40200000 },
        { CP_T_TAXI_RETURN_TICKS, 0x41700000, 0x41F00000 },
        { CP_T_HELI_AIM, 0x42C80000, 0x42480000 },       { CP_T_HELI_AIM_MAX, 0x42400000, 0x42F00000 },
        { CP_T_HELI_GEAR, 0x428C0000, 0x41A00000 },
        { CP_T_CIRCLE_CZ, 0xC4E10000, 0x44160000 },
        { CP_T_SPEED_NORMAL_WING, bits(61.0f), 0x42400000 }, { CP_T_SPEED_NORMAL_MANTA, bits(91.0f), 0x42900000 },
        { CP_T_SPEED_FLANK, 0x43100000, 0x43100000 },
    };
    for (size_t i = 0; i < sizeof(W) / sizeof(W[0]); ++i) {
        CHECK_EQ(bits(t->v[W[i].id][0]), W[i].def);
        CHECK_EQ(bits(cp_tun_info(W[i].id)->stock[0]), W[i].stock);
    }
    /* vectors: (1000, 1800, 0, 0) / (-1000, -1800, 0, 0), stock (1000, -600) / (-1000, 600) */
    CHECK_EQ(bits(t->v[CP_T_CIRCLE_FWD_VEC][0]), 0x447A0000);
    CHECK_EQ(bits(t->v[CP_T_CIRCLE_FWD_VEC][1]), 0x44E10000);
    CHECK_EQ(bits(t->v[CP_T_CIRCLE_BACK_VEC][0]), 0xC47A0000);
    CHECK_EQ(bits(t->v[CP_T_CIRCLE_BACK_VEC][1]), 0xC4E10000);
    CHECK_EQ(bits(cp_tun_info(CP_T_CIRCLE_FWD_VEC)->stock[1]), 0xC4160000);
    CHECK_EQ(bits(cp_tun_info(CP_T_CIRCLE_BACK_VEC)->stock[1]), 0x44160000);
    CHECK(t->v[CP_T_CIRCLE_FWD_VEC][2] == 0.0f && t->v[CP_T_CIRCLE_FWD_VEC][3] == 0.0f);
    /* each derived "negative" really is the negation of its positive */
    CHECK_EQ(bits(t->v[CP_T_CRANE_V_NEG][0]), bits(t->v[CP_T_CRANE_V][0]) ^ 0x80000000u);
}

static void test_tunables_derive_follows_overrides(void) {
    cp_tunables *t = &F.tun;
    cp_tun_init(t);
    CHECK_EQ(cp_tun_set_by_key(t, "platform_step", 0.07), 1);
    CHECK_EQ(bits(t->v[CP_T_PLATFORM_STEP_NEG][0]), bits(-0.07f));
    CHECK_EQ(cp_tun_set_by_key(t, "circle_center_z", -2500.0), 1);
    CHECK_EQ(bits(t->v[CP_T_CIRCLE_FWD_VEC][1]), bits(2500.0f));
    CHECK_EQ(bits(t->v[CP_T_CIRCLE_BACK_VEC][1]), bits(-2500.0f));
    CHECK_EQ(cp_tun_set_by_key(t, "circle_center_x", -1500.0), 1);
    CHECK_EQ(bits(t->v[CP_T_CIRCLE_FWD_VEC][0]), bits(1500.0f));
    CHECK_EQ(cp_tun_set_by_key(t, "nope", 1.0), 0);                    /* unknown */
    CHECK_EQ(cp_tun_set_by_key(t, "taxi_cap", 1e9), -1);               /* absurd */
    CHECK_EQ(cp_tun_set_by_key(t, "taxi_cap", NAN), -1);
    CHECK_EQ(cp_tun_set_by_key(t, "taxi_cap", INFINITY), -1);
    CHECK_EQ(bits(t->v[CP_T_TAXI_CAP][0]), bits(5.0f));                /* refused values changed nothing */
    cp_tun_init(t);                                                    /* init restores the Mac values */
    CHECK_EQ(bits(t->v[CP_T_PLATFORM_STEP][0]), bits(0.05f));
}

/* ============================================================================ ini */

typedef struct got {
    int n, errors;
    char item[16][3][64];
    int line[16];
} got;
static void got_item(void *u, int line, const char *s, const char *k, const char *v) {
    got *g = u;
    if (g->n < 16) {
        snprintf(g->item[g->n][0], 64, "%s", s);
        snprintf(g->item[g->n][1], 64, "%s", k);
        snprintf(g->item[g->n][2], 64, "%s", v);
        g->line[g->n] = line;
    }
    ++g->n;
}
static void got_err(void *u, int line, const char *what) { (void)line; (void)what; ((got *)u)->errors++; }

static void test_ini_parser(void) {
    static const char text[] =
        "\xEF\xBB\xBF; comment\r\n"
        "# another\r\n"
        "orphan = 1\r\n"
        "[Groups]\r\n"
        "Energy_Lift_Crane_Taxi = 1   ; inline comment\r\n"
        "  helicopters\t=\ton # other inline\n"
        "\n"
        "[tunables]\r"
        "platform_step=0.05\r"
        "url = a;b ; real comment\n"
        "no equals sign here\n"
        "[unterminated\n"
        "= novalue_key\n"
        "[debug]\n"
        "lua_speed_stub = 1";                          /* no final newline */
    got g;
    memset(&g, 0, sizeof(g));
    cp_ini_handler h = { got_item, got_err, &g };
    int errors = cp_ini_parse(text, sizeof(text) - 1, &h);
    CHECK_EQ(errors, 3);                               /* "no equals", "[unterminated", "= novalue_key" */
    CHECK_EQ(g.errors, 3);
    CHECK_EQ(g.n, 6);
    CHECK(!strcmp(g.item[0][0], "") && !strcmp(g.item[0][1], "orphan") && !strcmp(g.item[0][2], "1"));
    CHECK_EQ(g.line[0], 3);                            /* BOM and CRLF do not disturb line numbers */
    CHECK(!strcmp(g.item[1][0], "groups") && !strcmp(g.item[1][1], "energy_lift_crane_taxi") && !strcmp(g.item[1][2], "1"));
    CHECK(!strcmp(g.item[2][1], "helicopters") && !strcmp(g.item[2][2], "on"));
    CHECK(!strcmp(g.item[3][0], "tunables") && !strcmp(g.item[3][1], "platform_step") && !strcmp(g.item[3][2], "0.05"));
    CHECK(!strcmp(g.item[4][2], "a;b"));               /* ';' not preceded by a blank is part of the value */
    CHECK(!strcmp(g.item[5][0], "debug") && !strcmp(g.item[5][2], "1"));
    /* a line longer than the limit is reported and skipped, the next line is fine */
    char big[600];
    memset(big, 'a', sizeof(big));
    memcpy(big + 400, "\nk = v\n", 7);
    memset(&g, 0, sizeof(g));
    errors = cp_ini_parse(big, 407, &h);
    CHECK_EQ(errors, 1);
    CHECK_EQ(g.n, 1);
    CHECK(!strcmp(g.item[0][1], "k"));
    memset(&g, 0, sizeof(g));
    CHECK_EQ(cp_ini_parse("", 0, &h), 0);
    CHECK_EQ(g.n, 0);
}

static void test_number_and_bool_parsing(void) {
    double d;
    float f;
    CHECK(cp_parse_double("0.8", &d)); f = (float)d; CHECK_EQ(bits(f), bits(0.8f));
    CHECK(cp_parse_double("0.05", &d)); f = (float)d; CHECK_EQ(bits(f), bits(0.05f));
    CHECK(cp_parse_double("0.333333", &d)); CHECK(fabs(d - 0.333333) < 1e-12);
    CHECK(cp_parse_double("-1800", &d)); CHECK(d == -1800.0);
    CHECK(cp_parse_double("  +23.5  ", &d)); CHECK(d == 23.5);
    CHECK(cp_parse_double("1e3", &d)); CHECK(d == 1000.0);
    CHECK(cp_parse_double("2.5E-1", &d)); CHECK(d == 0.25);
    CHECK(cp_parse_double(".5", &d)); CHECK(d == 0.5);
    CHECK(cp_parse_double("5.", &d)); CHECK(d == 5.0);
    CHECK(cp_parse_double("0", &d)); CHECK(d == 0.0);
    CHECK(cp_parse_double("123456789012345678901234567890", &d)); CHECK(fabs(d / 1.2345678901234568e29 - 1) < 1e-9);
    const char *bad[] = { "", " ", ".", "-", "abc", "1e", "1e+", "1.2.3", "nan", "inf", "0x10", "1,5", "1 2", "--1", "1e999" };
    for (size_t i = 0; i < sizeof(bad) / sizeof(bad[0]); ++i) CHECK(!cp_parse_double(bad[i], &d));
    int b;
    const char *yes[] = { "1", "on", "ON", "True", "yes", " Yes " }, *no[] = { "0", "off", "False", "NO" };
    for (size_t i = 0; i < 6; ++i) { CHECK(cp_parse_bool(yes[i], &b)); CHECK_EQ(b, 1); }
    for (size_t i = 0; i < 4; ++i) { CHECK(cp_parse_bool(no[i], &b)); CHECK_EQ(b, 0); }
    CHECK(!cp_parse_bool("2", &b));
    CHECK(!cp_parse_bool("", &b));
    CHECK(!cp_parse_bool("enable", &b));
    CHECK(!cp_parse_bool("on off", &b));
}

typedef struct warns { int n; char text[8][200]; } warns;
static void collect(void *u, const char *msg) {
    warns *w = u;
    if (w->n < 8) snprintf(w->text[w->n], 200, "%s", msg);
    ++w->n;
}

static void test_config_defaults_all_off(void) {
    cp_config c;
    cp_config_init(&c);
    for (int g = 0; g < CP_G_COUNT; ++g) CHECK_EQ(c.group_on[g], 0);
    CHECK_EQ(c.lua_speed_stub, 0);
    cp_tun_init(&F.tun);
    warns w = { 0 };
    CHECK_EQ(cp_config_parse(&c, &F.tun, "", 0, collect, &w), 0);      /* an empty ini changes nothing */
    for (int g = 0; g < CP_G_COUNT; ++g) CHECK_EQ(c.group_on[g], 0);
}

static void test_config_groups_and_tunables(void) {
    static const char ini[] =
        "[groups]\n"
        "energy_lift_crane_taxi = 1\n"
        "helicopters = off\n"
        "landing_circuit = maybe\n"          /* invalid -> off + warning */
        "speed_modes = true\n"
        "warp_drive = 1\n"                   /* unknown group */
        "[tunables]\n"
        "platform_step = 0.06\n"
        "taxi_cap = lots\n"                  /* not a number */
        "crane_vertical = 1e12\n"            /* absurd */
        "plasma = 3\n"                       /* unknown tunable */
        "[debug]\n"
        "lua_speed_stub = 1\n"
        "[other]\n"
        "x = 1\n";
    cp_config c;
    cp_config_init(&c);
    cp_tun_init(&F.tun);
    warns w = { 0 };
    int n = cp_config_parse(&c, &F.tun, ini, sizeof(ini) - 1, collect, &w);
    CHECK_EQ(n, 6);
    CHECK_EQ(w.n, 6);
    CHECK_EQ(c.group_on[CP_G_ENERGY], 1);
    CHECK_EQ(c.group_on[CP_G_HELI], 0);
    CHECK_EQ(c.group_on[CP_G_LANDING], 0);
    CHECK_EQ(c.group_on[CP_G_SPEED], 1);
    CHECK_EQ(c.group_on[CP_G_CCTV], 0);
    CHECK_EQ(c.lua_speed_stub, 1);
    CHECK_EQ(c.n_overrides, 1);
    CHECK_EQ(bits(F.tun.v[CP_T_PLATFORM_STEP][0]), bits(0.06f));
    CHECK_EQ(bits(F.tun.v[CP_T_PLATFORM_STEP_NEG][0]), bits(-0.06f));
    CHECK_EQ(bits(F.tun.v[CP_T_TAXI_CAP][0]), bits(5.0f));             /* bad values left the defaults */
    CHECK_EQ(bits(F.tun.v[CP_T_CRANE_V][0]), bits(1.0f / 15.0f));
    CHECK_STR_HAS(w.text[0], "ini line 4");                             /* line numbers are reported */
    CHECK_STR_HAS(w.text[0], "maybe");
}

/* The example ini shipped next to the plugin must stay in step with the code: it parses without a warning,
 * every group is off, and every settable tunable appears with its default value. */
static void test_ini_example_matches_code(void) {
    FILE *f = fopen("../cc2_patchs.ini.example", "rb");
    CHECK(f != NULL);
    if (!f) return;
    static char text[8192];
    size_t n = fread(text, 1, sizeof(text) - 1, f);
    fclose(f);
    cp_config c;
    cp_config_init(&c);
    cp_tun_init(&F.tun);
    warns w = { 0 };
    CHECK_EQ(cp_config_parse(&c, &F.tun, text, n, collect, &w), 0);
    if (w.n) printf("    first warning: %s\n", w.text[0]);
    for (int g = 0; g < CP_G_COUNT; ++g) CHECK_EQ(c.group_on[g], 0);
    int settable = 0;
    cp_tunables defaults;
    cp_tun_init(&defaults);
    for (int id = 1; id < CP_T_COUNT; ++id) {
        const cp_tunable_info *ti = cp_tun_info(id);
        if (ti->derived) continue;
        ++settable;
        CHECK(strstr(text, ti->ini_key) != NULL);                      /* every tunable is documented */
        CHECK_EQ(bits(F.tun.v[id][0]), bits(defaults.v[id][0]));        /* and the example shows the default */
    }
    CHECK_EQ(c.n_overrides, settable);
    for (int g = 0; g < CP_G_COUNT; ++g) CHECK(strstr(text, CP_GROUPS[g].ini_key) != NULL);
    CHECK(strstr(text, "SPDX-License-Identifier: GPL-3.0-or-later") != NULL);
}

/* ============================================================================ PE + build gate */

static void make_pe(uint8_t *b, size_t len, uint32_t ts, uint32_t size_of_image, uint16_t machine, uint16_t magic, uint32_t lfanew) {
    memset(b, 0, len);
    b[0] = 'M'; b[1] = 'Z';
    memcpy(b + 0x3c, &lfanew, 4);
    memcpy(b + lfanew, "PE\0\0", 4);
    uint8_t *fh = b + lfanew + 4;
    memcpy(fh, &machine, 2);
    uint16_t nsec = 1, opt = 0xe0, chars = 0x0102;
    memcpy(fh + 2, &nsec, 2);
    memcpy(fh + 4, &ts, 4);
    memcpy(fh + 16, &opt, 2);
    memcpy(fh + 18, &chars, 2);
    uint8_t *o = fh + 20;
    memcpy(o, &magic, 2);
    uint32_t ib = 0x00400000;
    memcpy(o + 28, &ib, 4);
    memcpy(o + 56, &size_of_image, 4);
}

static void test_pe_parse_and_gate(void) {
    uint8_t b[4096];
    cp_pe_info pe;
    char why[200];
    make_pe(b, sizeof(b), CP_KNOWN_PE_TIMESTAMP, CP_KNOWN_IMAGE_SIZE, 0x014c, 0x010b, 0x100);
    CHECK_EQ(cp_pe_parse(b, sizeof(b), &pe), CP_PE_OK);
    CHECK_EQ(pe.timestamp, 0x6a36c177u);
    CHECK_EQ(pe.size_of_image, 0x00af7000u);
    CHECK_EQ(pe.image_base, 0x00400000u);
    CHECK(cp_build_gate("1.5.18-win32", &pe, why, sizeof(why)));
    /* each of the three conditions alone is enough to refuse */
    CHECK(!cp_build_gate("1.5.19-win32", &pe, why, sizeof(why)));      CHECK_STR_HAS(why, "1.5.19-win32");
    CHECK(!cp_build_gate("1.5.18-mac", &pe, why, sizeof(why)));
    CHECK(!cp_build_gate(NULL, &pe, why, sizeof(why)));                CHECK_STR_HAS(why, "(null)");
    make_pe(b, sizeof(b), 0x6a36c178, CP_KNOWN_IMAGE_SIZE, 0x014c, 0x010b, 0x100);
    CHECK_EQ(cp_pe_parse(b, sizeof(b), &pe), CP_PE_OK);
    CHECK(!cp_build_gate("1.5.18-win32", &pe, why, sizeof(why)));      CHECK_STR_HAS(why, "timestamp");  CHECK_STR_HAS(why, "0x6a36c178");
    make_pe(b, sizeof(b), CP_KNOWN_PE_TIMESTAMP, 0x00af7001, 0x014c, 0x010b, 0x100);
    CHECK_EQ(cp_pe_parse(b, sizeof(b), &pe), CP_PE_OK);
    CHECK(!cp_build_gate("1.5.18-win32", &pe, why, sizeof(why)));      CHECK_STR_HAS(why, "SizeOfImage");
    CHECK(!cp_build_gate("1.5.18-win32", NULL, why, sizeof(why)));
    CHECK(!cp_build_gate("1.5.18-win32", &pe, NULL, 0));
}

static void test_pe_malformed(void) {
    uint8_t b[4096];
    cp_pe_info pe;
    make_pe(b, sizeof(b), 1, 2, 0x014c, 0x010b, 0x100);
    CHECK_EQ(cp_pe_parse(b, 0x30, &pe), CP_PE_TOO_SMALL);
    CHECK_EQ(cp_pe_parse(NULL, 4096, &pe), CP_PE_TOO_SMALL);
    b[0] = 'Z';
    CHECK_EQ(cp_pe_parse(b, sizeof(b), &pe), CP_PE_NO_MZ);
    make_pe(b, sizeof(b), 1, 2, 0x014c, 0x010b, 0x100);
    uint32_t bad = 0xfffffff0u;
    memcpy(b + 0x3c, &bad, 4);
    CHECK_EQ(cp_pe_parse(b, sizeof(b), &pe), CP_PE_BAD_LFANEW);
    bad = 0x10;                                                        /* inside the DOS header */
    memcpy(b + 0x3c, &bad, 4);
    CHECK_EQ(cp_pe_parse(b, sizeof(b), &pe), CP_PE_BAD_LFANEW);
    make_pe(b, sizeof(b), 1, 2, 0x014c, 0x010b, 0x100);
    b[0x100] = 'X';
    CHECK_EQ(cp_pe_parse(b, sizeof(b), &pe), CP_PE_NO_PE_SIGNATURE);
    make_pe(b, sizeof(b), 1, 2, 0x8664, 0x020b, 0x100);                /* 64-bit PE */
    CHECK_EQ(cp_pe_parse(b, sizeof(b), &pe), CP_PE_NOT_I386);
    make_pe(b, sizeof(b), 1, 2, 0x014c, 0x020b, 0x100);                /* i386 machine but PE32+ magic */
    CHECK_EQ(cp_pe_parse(b, sizeof(b), &pe), CP_PE_NOT_PE32);
    static uint8_t big[8192];
    make_pe(big, sizeof(big), 1, 2, 0x014c, 0x010b, 0xfc0);            /* headers run past the first 4096 bytes */
    CHECK_EQ(cp_pe_parse(big, 0x1000, &pe), CP_PE_OPTIONAL_TOO_SHORT);
    make_pe(b, sizeof(b), 1, 2, 0x014c, 0x010b, 0x100);
    CHECK_EQ(cp_pe_parse(b, 0x100 + 4 + 20, &pe), CP_PE_OPTIONAL_TOO_SHORT);
    CHECK_EQ(cp_pe_parse(b, 0x100 + 4 + 20 + 40, &pe), CP_PE_OPTIONAL_TOO_SHORT);
    CHECK(strlen(cp_pe_status_text(CP_PE_NOT_PE32)) > 3);
}

/* ============================================================================ speed modes (Lua contract) */

static int io_file_mode, io_saves, io_last_save;
static int io_load(void *u) { (void)u; return io_file_mode; }
static void io_save(void *u, int m) { (void)u; ++io_saves; io_last_save = m; }

static void test_speed_contract(void) {
    static cp_speed s;
    cp_speed_io io = { io_load, io_save, NULL };
    cp_speed_init(&s);
    io_file_mode = 0; io_saves = 0;
    CHECK_EQ(cp_speed_call(&s, &io, 1, 1, 0), 0);                      /* read, no mode yet */
    CHECK_EQ(cp_speed_call(&s, &io, 2, 1, 3), 3);                      /* set 3 -> 3 */
    CHECK_EQ(io_saves, 1);
    CHECK_EQ(io_last_save, 3);
    CHECK_EQ(cp_speed_call(&s, &io, 2, 1, 9), 3);                      /* invalid mode ignored */
    CHECK_EQ(cp_speed_call(&s, &io, 2, 1, 0), 3);
    CHECK_EQ(cp_speed_call(&s, &io, 2, 1, -1), 3);
    CHECK_EQ(cp_speed_call(&s, &io, 2, 1, 3), 3);
    CHECK_EQ(io_saves, 1);                                             /* the file is written only when the mode changes */
    CHECK_EQ(cp_speed_call(&s, &io, 2, 99, 2), 0);                     /* team out of range: 0, nothing set */
    CHECK_EQ(cp_speed_call(&s, &io, 2, -1, 2), 0);
    CHECK_EQ(cp_speed_call(&s, &io, 1, 99, 0), 0);
    CHECK_EQ(io_saves, 1);
    CHECK_EQ(cp_speed_call(&s, &io, 1, 7, 0), 3);                      /* a team without mode adopts the last set mode */
    CHECK_EQ(cp_speed_call(&s, &io, 2, 7, 2), 2);
    CHECK_EQ(io_saves, 2);
    CHECK_EQ(cp_speed_call(&s, &io, 1, 1, 0), 3);                      /* team 1 keeps its own */
    CHECK_EQ(cp_speed_call(&s, &io, 1, 12, 0), 2);                     /* newcomer adopts the newest */
    /* argument decoding: text / absent -> team 0 ; integral float accepted ; fractional -> 0 */
    CHECK_EQ(cp_speed_arg(0, 5.0), 0);
    CHECK_EQ(cp_speed_arg(1, 2.0), 2);
    CHECK_EQ(cp_speed_arg(1, 2.5), 0);
    CHECK_EQ(cp_speed_arg(1, -3.0), -3);
    CHECK_EQ(cp_speed_arg(1, NAN), 0);
    CHECK_EQ(cp_speed_arg(1, INFINITY), 0);
    CHECK_EQ(cp_speed_call(&s, &io, 0, cp_speed_arg(0, 0), 0), s.mode[0]);   /* no argument = team 0 */
    /* the file of an earlier session is adopted on first use */
    cp_speed_init(&s);
    io_file_mode = 2;
    CHECK_EQ(cp_speed_call(&s, &io, 1, 4, 0), 2);
    cp_speed_init(&s);
    io_file_mode = 7;                                                  /* garbage in the file is ignored */
    CHECK_EQ(cp_speed_call(&s, &io, 1, 4, 0), 0);
    cp_speed_init(&s);
    CHECK_EQ(cp_speed_call(&s, NULL, 2, 4, 3), 3);                     /* no io at all is fine */
}

static void test_speed_floors(void) {
    cp_tunables *t = &F.tun;
    cp_tun_init(t);
    CHECK(cp_speed_floor(t, 0, 0) == 48.0f && cp_speed_floor(t, 0, 1) == 72.0f);     /* never chosen = stock */
    CHECK(cp_speed_floor(t, 1, 0) == 48.0f && cp_speed_floor(t, 1, 1) == 72.0f);     /* ECO = stock */
    CHECK(cp_speed_floor(t, 2, 0) == 61.0f && cp_speed_floor(t, 2, 1) == 91.0f);     /* NORMAL */
    CHECK(cp_speed_floor(t, 3, 0) == 144.0f && cp_speed_floor(t, 3, 1) == 144.0f);   /* FLANK */
    CHECK(cp_speed_floor(t, 9, 0) == 48.0f);                                          /* unknown = stock */
    CHECK_EQ(cp_tun_set_by_key(t, "speed_normal_wing", 70.0), 1);
    CHECK(cp_speed_floor(t, 2, 0) == 70.0f);
}

/* ============================================================================ hooks, tables */

static void test_hook_callbacks(void) {
    static cp_hook_ctx ctx;
    cp_tun_init(&F.tun);
    cp_hooks.tun = &F.tun;
    cp_hooks.heli_height_xmm = -1;                                     /* default: not configured -> does nothing */
    memset(&ctx, 0, sizeof(ctx));
    ctx.xmm[1][0] = 100.0f;
    cp_hook_lookup(CP_HOOK_HELI_HEIGHT)(&ctx, NULL);
    CHECK(ctx.xmm[1][0] == 100.0f);
    cp_hooks.heli_height_xmm = 1;                                      /* configured: subtracts 23.5 */
    cp_hook_lookup(CP_HOOK_HELI_HEIGHT)(&ctx, NULL);
    CHECK(ctx.xmm[1][0] == 76.5f);
    CHECK(ctx.xmm[0][0] == 0.0f && ctx.xmm[2][0] == 0.0f);             /* other registers untouched */
    cp_tun_set_by_key(&F.tun, "heli_height_shift", 10.0);
    cp_hook_lookup(CP_HOOK_HELI_HEIGHT)(&ctx, NULL);
    CHECK(ctx.xmm[1][0] == 66.5f);
    cp_hooks.heli_height_xmm = 9;                                      /* out of range: ignored */
    cp_hook_lookup(CP_HOOK_HELI_HEIGHT)(&ctx, NULL);
    CHECK(ctx.xmm[1][0] == 66.5f);
    cp_hooks.heli_height_xmm = -1;
    for (int id = 1; id < CP_HOOK_COUNT; ++id) CHECK(cp_hook_lookup(id) != NULL);
    CHECK(cp_hook_lookup(0) == NULL && cp_hook_lookup(CP_HOOK_COUNT) == NULL);
    /* the not-ported callbacks must not change anything */
    memset(&ctx, 0x5a, sizeof(ctx));
    static cp_hook_ctx copy;
    memcpy(&copy, &ctx, sizeof(ctx));
    for (int id = CP_HOOK_SPEED_FLOOR; id < CP_HOOK_COUNT; ++id) cp_hook_lookup(id)(&ctx, NULL);
    CHECK(memcmp(&ctx, &copy, sizeof(ctx)) == 0);
}

static void test_group_table(void) {
    static const char *keys[] = { "energy_lift_crane_taxi", "helicopters", "return_taxi", "landing_circuit", "speed_modes",
                                  "crane_cancel", "cctv", "recorder" };
    CHECK_EQ(CP_G_COUNT, 8);
    int mac_total = 0;
    for (int g = 0; g < CP_G_COUNT; ++g) {
        CHECK(!strcmp(CP_GROUPS[g].ini_key, keys[g]));
        CHECK_EQ(cp_group_by_key(keys[g]), g);
        CHECK(CP_GROUPS[g].tower_step >= 3 && CP_GROUPS[g].tower_step <= 8);
        mac_total += CP_GROUPS[g].mac_sites;
        for (int h = g + 1; h < CP_G_COUNT; ++h) CHECK(strcmp(CP_GROUPS[g].ini_key, CP_GROUPS[h].ini_key) != 0);
    }
    CHECK_EQ(cp_group_by_key("nope"), -1);
    CHECK_EQ(cp_group_by_key(NULL), -1);
    CHECK_EQ(mac_total, 34 + 5 + 3 + 10 + 3 + 3 + 5 + 3);              /* part 10 of cc2_reference.txt */
    CHECK_EQ(CP_GROUPS[CP_G_ENERGY].mac_sites, 34);
    CHECK_EQ(CP_GROUPS[CP_G_LANDING].mac_sites, 10);
}

/* Today every table is empty: this checks the state (no Windows address invented) and, once the
 * tower fills a table, that it is well formed and never overlaps another group. */
static void test_group_tables_wellformed(void) {
    int total = 0;
    for (int g = 0; g < CP_G_COUNT; ++g) {
        const cp_group *grp = &CP_GROUPS[g];
        CHECK((grp->sites == NULL) == (grp->n_sites == 0));
        total += grp->n_sites;
        for (int i = 0; i < grp->n_sites; ++i) {
            const cp_site *s = &grp->sites[i];
            CHECK(s->addr >= CP_IMAGE_BASE && s->addr + s->len <= CP_IMAGE_BASE + CP_KNOWN_IMAGE_SIZE);
            CHECK(s->len >= 1 && s->len <= CP_MAX_SITE_LEN);
            CHECK(s->kind >= CP_SITE_ABS_FLOAT && s->kind <= CP_SITE_HOOK);
            for (int h = g; h < CP_G_COUNT; ++h)
                for (int j = (h == g ? i + 1 : 0); j < CP_GROUPS[h].n_sites; ++j) {
                    const cp_site *o = &CP_GROUPS[h].sites[j];
                    CHECK(!(s->addr < o->addr + o->len && o->addr < s->addr + s->len));
                }
        }
    }
    printf("    (site tables hold %d site(s) in total: 0 = nothing ported yet)\n", total);
    /* applying an empty table is refused with a clear reason, for every group */
    fx_init();
    for (int g = 0; g < CP_G_COUNT; ++g) {
        if (CP_GROUPS[g].n_sites) continue;
        cp_result r;
        cp_group_apply(&F.s, g, CP_GROUPS[g].sites, CP_GROUPS[g].n_sites, &r);
        CHECK_EQ(r.status, CP_GRP_REFUSED);
        CHECK_STR_HAS(r.reason, "empty");
    }
}

/* ============================================================================ plugin entry, end to end */

/* a fake CC2X API: logs and Lua are recorded */
static char api_log[64][400];
static int api_nlog;
static void fake_log(const char *plugin, int level, const char *fmt, ...) {
    char msg[360];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(msg, sizeof(msg), fmt, ap);
    va_end(ap);
    if (api_nlog < 64) snprintf(api_log[api_nlog++], sizeof(api_log[0]), "%d [%s] %s", level, plugin, msg);
}
static uintptr_t fake_api_va(uint32_t image_va) { return fm_va_to_rt(image_va); }
static char lua_names[8][64];
static int lua_nfn, lua_nfeat;
static char lua_feats[8][64];
static cc2x_lua_fn lua_registered;
static int fake_lua_add(const char *ns, const char *name, cc2x_lua_fn fn) {
    snprintf(lua_names[lua_nfn++], 64, "%s.%s", ns ? ns : "", name);
    lua_registered = fn;
    return 1;
}
static void fake_lua_feature(const char *name) { snprintf(lua_feats[lua_nfeat++], 64, "%s", name); }
/* fake Lua stack: nargs, each argument is a number or not */
static int fl_nargs, fl_isnum[4];
static double fl_val[4];
static int64_t fl_result;
static int fl_gettop(cc2x_lua *L) { (void)L; return fl_nargs; }
static int fl_tonumber(cc2x_lua *L, int idx, double *out) {
    (void)L;
    if (idx < 1 || idx > fl_nargs || !fl_isnum[idx - 1]) return 0;
    *out = fl_val[idx - 1];
    return 1;
}
static void fl_pushinteger(cc2x_lua *L, int64_t v) { (void)L; fl_result = v; }

static cc2x_api api;
static const char *CONFIG_DIR = "C:\\Users\\x\\AppData\\Roaming\\Carrier Command 2\\cc2x";
static const char *INI_PATH = "C:\\Users\\x\\AppData\\Roaming\\Carrier Command 2\\cc2x\\cc2_patchs.ini";

static void e2e_setup(const char *build, uint32_t ts, uint32_t size) {
    fx_init();
    g_plat_mem = &F.m;
    make_pe(F.m.image, 0x1000, ts, size, 0x014c, 0x010b, 0x100);
    fp_reset_files();
    memset(&api, 0, sizeof(api));
    api.api_version = 3;
    api.size = sizeof(cc2x_api);
    api.sdk_version = "0.4.0";
    api.game_build = build;
    api.module_base = FM_IMG_BASE;
    api.va = fake_api_va;
    api.log = fake_log;
    api.lua_add = fake_lua_add;
    api.lua_feature = fake_lua_feature;
    api.lua_gettop = fl_gettop;
    api.lua_tonumber = fl_tonumber;
    api.lua_pushinteger = fl_pushinteger;
    api.config_dir = CONFIG_DIR;
    api_nlog = 0;
    lua_nfn = lua_nfeat = 0;
    lua_registered = NULL;
}
static int log_count(const char *needle) {
    int n = 0;
    for (int i = 0; i < api_nlog; ++i) if (strstr(api_log[i], needle)) ++n;
    return n;
}
static void print_log(void) {
    for (int i = 0; i < api_nlog; ++i) printf("      | %s\n", api_log[i]);
}

static void test_entry_refuses_unknown_builds(void) {
    e2e_setup("1.5.19-win32", CP_KNOWN_PE_TIMESTAMP, CP_KNOWN_IMAGE_SIZE);
    CHECK_EQ(cc2x_plugin_load(&api), 0);
    CHECK_EQ(log_count("build gate:"), 1);
    CHECK_EQ(log_count("game build is '1.5.19-win32', this plugin only knows '1.5.18-win32'"), 1);
    CHECK_EQ(log_count("staying inactive, the game is unchanged"), 1);
    CHECK_EQ(log_count("group "), 0);                                  /* nothing else ran */
    CHECK_EQ(lua_nfn + lua_nfeat, 0);
    e2e_setup("1.5.18-win32", 0x6a36c178, CP_KNOWN_IMAGE_SIZE);
    CHECK_EQ(cc2x_plugin_load(&api), 0);
    CHECK_EQ(log_count("timestamp"), 1);
    e2e_setup("1.5.18-win32", CP_KNOWN_PE_TIMESTAMP, 0x00af7001);
    CHECK_EQ(cc2x_plugin_load(&api), 0);
    CHECK_EQ(log_count("SizeOfImage"), 1);
    e2e_setup("1.5.18-win32", CP_KNOWN_PE_TIMESTAMP, CP_KNOWN_IMAGE_SIZE);
    F.m.image[0] = 'X';                                                /* header unreadable as PE */
    CHECK_EQ(cc2x_plugin_load(&api), 0);
    CHECK_EQ(log_count("PE header unreadable"), 1);
    e2e_setup("1.5.18-win32", CP_KNOWN_PE_TIMESTAMP, CP_KNOWN_IMAGE_SIZE);
    api.module_base = 0x0badf00d;                                      /* nothing mapped there */
    CHECK_EQ(cc2x_plugin_load(&api), 0);
    CHECK_EQ(log_count("cannot read"), 1);
    e2e_setup("1.5.18-win32", CP_KNOWN_PE_TIMESTAMP, CP_KNOWN_IMAGE_SIZE);
    api.api_version = 1;                                               /* too old an SDK */
    CHECK_EQ(cc2x_plugin_load(&api), 0);
}

static void test_entry_known_build_no_ini_everything_off(void) {
    e2e_setup("1.5.18-win32", CP_KNOWN_PE_TIMESTAMP, CP_KNOWN_IMAGE_SIZE);
    snapshot();
    CHECK_EQ(cc2x_plugin_load(&api), 1);
    print_log();
    CHECK_EQ(log_count("known build"), 1);
    CHECK_EQ(log_count("skipped (off in the ini, default)"), 8);       /* one line per group */
    CHECK_EQ(log_count("applied"), 0);
    CHECK_EQ(F.m.writes, 0);                                           /* the game is untouched */
    CHECK(unchanged());
    CHECK_EQ(lua_nfn, 0);                                              /* no Lua speed function by default */
    CHECK_EQ(lua_nfeat, 1);                                            /* only the "cc2_patchs" feature */
}

static void test_entry_group_on_but_table_empty_is_refused(void) {
    e2e_setup("1.5.18-win32", CP_KNOWN_PE_TIMESTAMP, CP_KNOWN_IMAGE_SIZE);
    const char ini[] = "[groups]\nenergy_lift_crane_taxi = 1\nlanding_circuit = 1\ncctv = 0\nbogus = 1\n[tunables]\ntaxi_cap = 4.0\n";
    fp_set_file(INI_PATH, ini, (long)sizeof(ini) - 1);
    CHECK_EQ(cc2x_plugin_load(&api), 1);
    print_log();
    CHECK_EQ(log_count("read C:\\Users\\x\\AppData\\Roaming\\Carrier Command 2\\cc2x\\cc2_patchs.ini"), 1);
    CHECK_EQ(log_count("1 warning(s), 1 tunable(s) overridden"), 1);
    /* the energy table is filled since the tower's step 3: on the fake memory it is refused at its first site */
    CHECK_EQ(log_count("group energy_lift_crane_taxi: refused: site 0 (0x006ea09e)"), 1);
    CHECK_EQ(log_count("group landing_circuit: refused: site table is empty (not ported yet) [plan step 5]"), 1);
    CHECK_EQ(log_count("skipped (off in the ini, default)"), 6);
    CHECK_EQ(log_count("unknown group 'bogus'"), 1);
    CHECK_EQ(F.m.writes, 0);
}

static void test_entry_oversized_ini_warns(void) {
    e2e_setup("1.5.18-win32", CP_KNOWN_PE_TIMESTAMP, CP_KNOWN_IMAGE_SIZE);
    static char big[16384];
    memset(big, ' ', sizeof(big));
    memcpy(big, "[groups]\ncctv = 0\n", 18);
    fp_set_file(INI_PATH, big, (long)sizeof(big));
    CHECK_EQ(cc2x_plugin_load(&api), 1);
    CHECK_EQ(log_count("is larger than 16383 bytes"), 1);
}

static void test_entry_lua_speed_stub_contract(void) {
    e2e_setup("1.5.18-win32", CP_KNOWN_PE_TIMESTAMP, CP_KNOWN_IMAGE_SIZE);
    const char ini[] = "[debug]\nlua_speed_stub = 1\n";
    fp_set_file(INI_PATH, ini, (long)sizeof(ini) - 1);
    CHECK_EQ(cc2x_plugin_load(&api), 1);
    CHECK_EQ(lua_nfn, 1);
    CHECK(!strcmp(lua_names[0], "speed.mode"));                        /* cc2x.speed.mode, not a global */
    CHECK(lua_registered != NULL);
    CHECK_EQ(log_count("stub registered"), 1);
    CHECK_EQ(log_count("no aircraft speed"), 1);
    /* the contract, through the fake Lua stack (what library_custom_6.lua relies on) */
    const char *SPEED_FILE = "C:\\Users\\x\\AppData\\Roaming\\Carrier Command 2\\cc2x\\cc2_vitesse_mode.txt";
    fl_nargs = 1; fl_isnum[0] = 1; fl_val[0] = 0;
    CHECK_EQ(lua_registered(NULL), 1);  CHECK_EQ(fl_result, 0);        /* read, never chosen */
    fl_nargs = 2; fl_isnum[1] = 1; fl_val[1] = 3;
    CHECK_EQ(lua_registered(NULL), 1);  CHECK_EQ(fl_result, 3);        /* set 3 */
    long n = 0;
    const char *f = fp_get_file(SPEED_FILE, &n);
    CHECK(f != NULL && n == 2 && f[0] == '3' && f[1] == '\n');         /* the file holds the last mode */
    fl_val[1] = 9;
    lua_registered(NULL);  CHECK_EQ(fl_result, 3);                     /* invalid mode ignored */
    fl_nargs = 1; fl_val[0] = 99;
    lua_registered(NULL);  CHECK_EQ(fl_result, 0);                     /* team out of range */
    fl_isnum[0] = 0;                                                   /* text instead of a team -> team 0 */
    lua_registered(NULL);  CHECK_EQ(fl_result, 3);
    fl_nargs = 0;                                                      /* no argument -> team 0 */
    lua_registered(NULL);  CHECK_EQ(fl_result, 3);
    fl_nargs = 1; fl_isnum[0] = 1; fl_val[0] = 5;
    lua_registered(NULL);  CHECK_EQ(fl_result, 3);                     /* a team without mode adopts the last mode */
    fl_nargs = 2; fl_val[0] = 2.0; fl_val[1] = 1;                      /* a float with an integer value is accepted: team 2 -> ECO */
    lua_registered(NULL);  CHECK_EQ(fl_result, 1);
    fl_nargs = 1; fl_val[0] = 2.0;
    lua_registered(NULL);  CHECK_EQ(fl_result, 1);
    fl_val[0] = 2.5;                                                   /* a fractional number is not a team: team 0 (still NORMAL..FLANK 3) */
    lua_registered(NULL);  CHECK_EQ(fl_result, 3);
}

/* ============================================================================ main */

int main(void) {
    printf("== cc2_patchs host tests ==\n");
    RUN(test_write_basic);
    RUN(test_write_wrong_expected_refused);
    RUN(test_write_idempotent);
    RUN(test_write_failures_restore);
    RUN(test_group_all_sites_ok);
    RUN(test_group_wrong_bytes_refused_nothing_written);
    RUN(test_group_write_failure_rolls_back);
    RUN(test_group_verify_failure_rolls_back);
    RUN(test_group_rollback_failure_reported);
    RUN(test_group_overlap_refused);
    RUN(test_group_overlap_with_other_group_refused);
    RUN(test_group_second_apply_idempotent);
    RUN(test_group_empty_and_malformed_refused);
    RUN(test_group_revert);
    RUN(test_kind_abs_float_redirect_and_rebase);
    RUN(test_kind_abs_float_unrebased_operand_refused);
    RUN(test_kind_abs_float_stock_value_checked);
    RUN(test_kind_abs_float_operand_outside_image_refused);
    RUN(test_kind_abs_float_vec4_needs_aligned_table);
    RUN(test_kind_imm_with_float_from_tunable);
    RUN(test_kind_imm_rebases_absolute_operands);
    RUN(test_kind_jump_retargets_rel32);
    RUN(test_kind_jump_malformed_refused);
    RUN(test_kind_hook_builds_trampoline);
    RUN(test_kind_hook_displaced_absolute_operand);
    RUN(test_kind_hook_refusals_leave_game_untouched);
    RUN(test_hook_emit_layout);
    RUN(test_hook_emit_relocation_and_limits);
    RUN(test_tunables_alignment);
    RUN(test_tunables_defaults_are_mac_values);
    RUN(test_tunables_derive_follows_overrides);
    RUN(test_ini_parser);
    RUN(test_number_and_bool_parsing);
    RUN(test_config_defaults_all_off);
    RUN(test_config_groups_and_tunables);
    RUN(test_ini_example_matches_code);
    RUN(test_pe_parse_and_gate);
    RUN(test_pe_malformed);
    RUN(test_speed_contract);
    RUN(test_speed_floors);
    RUN(test_hook_callbacks);
    RUN(test_group_table);
    RUN(test_group_tables_wellformed);
    RUN(test_entry_refuses_unknown_builds);
    RUN(test_entry_known_build_no_ini_everything_off);
    RUN(test_entry_group_on_but_table_empty_is_refused);
    RUN(test_entry_oversized_ini_warns);
    RUN(test_entry_lua_speed_stub_contract);
    return TEST_SUMMARY();
}
