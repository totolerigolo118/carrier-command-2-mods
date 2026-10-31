/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "cp_patch.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

/* ------------------------------------------------------------------------------------ helpers */

static uint32_t rd32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static void wr32(uint8_t *p, uint32_t v) {
    for (int i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (8 * i));
}
static uint32_t float_bits(float f) {
    uint32_t u;
    memcpy(&u, &f, 4);
    return u;
}

static void refuse(cp_result *r, int site, const char *fmt, ...) {
    va_list ap;
    r->status = CP_GRP_REFUSED;
    r->site = site;
    va_start(ap, fmt);
    vsnprintf(r->reason, sizeof(r->reason), fmt, ap);
    va_end(ap);
}

static cp_addr rebase(const cp_env *env, uint32_t image_va) {
    return env->va ? env->va(env->user, image_va) : image_va;
}

static int overlap(cp_addr a, uint32_t alen, cp_addr b, uint32_t blen) {
    return (uint64_t)a < (uint64_t)b + blen && (uint64_t)b < (uint64_t)a + alen;
}

static void hex(const uint8_t *b, uint32_t n, char *out, size_t cap) {
    size_t o = 0;
    for (uint32_t i = 0; i < n && o + 3 < cap; ++i) o += (size_t)snprintf(out + o, cap - o, "%02x", b[i]);
    if (cap) out[o < cap ? o : cap - 1] = 0;
}

const char *cp_status_text(cp_status s) {
    switch (s) {
    case CP_OK: return "written";
    case CP_ALREADY: return "already patched";
    case CP_ERR_ARGS: return "bad arguments";
    case CP_ERR_READ: return "address not readable";
    case CP_ERR_MISMATCH: return "unexpected original bytes";
    case CP_ERR_WRITE: return "write failed";
    case CP_ERR_VERIFY: return "read-back differs";
    }
    return "?";
}

/* ----------------------------------------------------------------------------------- cp_write */

cp_status cp_write(const cp_env *env, cp_addr addr, const uint8_t *expected, const uint8_t *newb, uint32_t len) {
    uint8_t cur[CP_MAX_SITE_LEN], back[CP_MAX_SITE_LEN];
    if (!env || !env->read || !env->write || !expected || !newb || len == 0 || len > CP_MAX_SITE_LEN)
        return CP_ERR_ARGS;
    if (memcmp(expected, newb, len) == 0) return CP_ERR_ARGS;      /* a site that changes nothing is a table error */
    if (!env->read(env->user, addr, cur, len)) return CP_ERR_READ;
    if (memcmp(cur, newb, len) == 0) return CP_ALREADY;
    if (memcmp(cur, expected, len) != 0) return CP_ERR_MISMATCH;
    if (!env->write(env->user, addr, newb, len)) {
        /* a failed write should have changed nothing; make sure */
        if (env->read(env->user, addr, back, len) && memcmp(back, expected, len) != 0)
            env->write(env->user, addr, expected, len);
        return CP_ERR_WRITE;
    }
    if (!env->read(env->user, addr, back, len) || memcmp(back, newb, len) != 0) {
        env->write(env->user, addr, expected, len);
        return CP_ERR_VERIFY;
    }
    return CP_OK;
}

/* --------------------------------------------------------------------------------- group apply */

void cp_session_init(cp_session *s, const cp_env *env, const cp_tunables *tun) {
    memset(s, 0, sizeof(*s));
    s->env = *env;
    s->tun = tun;
}

/* static checks of one site; returns NULL or a reason */
static const char *check_site(const cp_site *st) {
    if (st->len == 0 || st->len > CP_MAX_SITE_LEN) return "length out of range";
    switch (st->kind) {
    case CP_SITE_ABS_FLOAT: {
        const cp_tunable_info *ti = cp_tun_info(st->tunable);
        if (!ti || !ti->has_stock) return "abs_float needs a tunable that has a stock game constant";
        if (st->off == 0 || st->off + 4u > st->len) return "disp32 offset outside the site";
        return NULL;
    }
    case CP_SITE_IMM:
        if (st->tunable != CP_T_NONE) {
            if (!cp_tun_info(st->tunable)) return "unknown tunable";
            if (st->off + 4u > st->len) return "float immediate outside the site";
        }
        for (int k = 0; k < 3; ++k)
            if (st->abs_ops[k] && st->abs_ops[k] + 4u > st->len) return "abs_ops offset outside the site";
        return NULL;
    case CP_SITE_JUMP: {
        const uint8_t *e = st->expected;
        int ok = (st->len == 5 && (e[0] == 0xE9 || e[0] == 0xE8) && st->off == 1) ||
                 (st->len == 6 && e[0] == 0x0F && e[1] >= 0x80 && e[1] <= 0x8F && st->off == 2);
        return ok ? NULL : "jump site must be exactly one rel32 branch (E9 / E8 / 0F 8x)";
    }
    case CP_SITE_HOOK:
        if (st->len < CP_HOOK_MIN_LEN || st->len > CP_HOOK_MAX_LEN) return "hook site needs 5..16 bytes";
        if (st->hook == 0) return "hook id missing";
        for (int k = 0; k < 3; ++k)
            if (st->abs_ops[k] && st->abs_ops[k] + 4u > st->len) return "abs_ops offset outside the site";
        return NULL;
    default:
        return "unknown site kind";
    }
}

int cp_abs_float_redirect(const cp_env *env, const cp_tunables *tun, const cp_site *st, const uint8_t *orig_rt,
                          uint8_t *out, char *why, size_t why_cap) {
    const cp_tunable_info *ti = cp_tun_info(st->tunable);
    if (!ti || !ti->has_stock || st->off == 0 || st->off + 4u > st->len) {
        snprintf(why, why_cap, "not an abs_float site");
        return 0;
    }
    cp_addr old = rd32(orig_rt + st->off), mine = cp_tun_addr(tun, st->tunable);
    if (!mine) {
        snprintf(why, why_cap, "tunable table is not bound to an address");
        return 0;
    }
    if (mine & 15u) {
        snprintf(why, why_cap, "tunable address 0x%08x is not 16-byte aligned", (unsigned)mine);
        return 0;
    }
    if (env->image_size && (uint32_t)(old - env->image_lo) >= env->image_size) {
        snprintf(why, why_cap, "operand 0x%08x points outside the game image", (unsigned)old);
        return 0;
    }
    if (!(st->flags & CP_SF_NO_STOCK_CHECK)) {
        float stock[4];
        int vec_ok = env->read(env->user, old, stock, 16) && memcmp(stock, ti->stock, 16) == 0;
        /* a scalar constant may be followed by anything in memory: only lane 0 counts for scalars */
        int scalar_ok = ti->stock[1] == 0.0f && ti->stock[2] == 0.0f && ti->stock[3] == 0.0f &&
                        env->read(env->user, old, stock, 4) && float_bits(stock[0]) == float_bits(ti->stock[0]);
        if (!vec_ok && !scalar_ok) {
            snprintf(why, why_cap, "constant at 0x%08x does not hold the stock value of %s", (unsigned)old,
                     ti->ini_key ? ti->ini_key : "a derived tunable");
            return 0;
        }
    }
    memcpy(out, orig_rt, st->len);
    wr32(out + st->off, mine);
    return 1;
}

/* Compute the bytes a site must contain after patching. `exp_rt` = expected bytes with operands rebased. */
static int build_new(cp_session *s, int gid, int idx, const cp_site *st, cp_addr rt_addr,
                     const uint8_t *exp_rt, uint8_t *out, cp_result *r) {
    const cp_env *env = &s->env;
    memcpy(out, exp_rt, st->len);
    switch (st->kind) {
    case CP_SITE_ABS_FLOAT: {
        char why[160];
        if (!cp_abs_float_redirect(env, s->tun, st, exp_rt, out, why, sizeof(why))) {
            refuse(r, idx, "site %d: %s", idx, why);
            return 0;
        }
        return 1;
    }
    case CP_SITE_IMM:
        if (st->tunable != CP_T_NONE) {
            wr32(out + st->off, float_bits(cp_tun_get(s->tun, st->tunable)));
        } else {
            memcpy(out, st->repl, st->len);
            for (int k = 0; k < 3; ++k)
                if (st->abs_ops[k]) wr32(out + st->abs_ops[k], rebase(env, rd32(st->repl + st->abs_ops[k])));
        }
        return 1;
    case CP_SITE_JUMP:
        wr32(out + st->off, st->target - (st->addr + st->len));    /* both inside the image: no rebase */
        return 1;
    case CP_SITE_HOOK: {
        cp_addr cb = env->hook_addr ? env->hook_addr(env->user, st->hook) : 0;
        uint8_t tramp[CP_HOOK_MAX_SIZE];
        size_t used = 0;
        if (!cb) { refuse(r, idx, "site %d: hook id %u has no implementation", idx, (unsigned)st->hook); return 0; }
        if (!env->alloc_exec) { refuse(r, idx, "site %d: no executable memory available", idx); return 0; }
        cp_addr at = env->alloc_exec(env->user, CP_HOOK_MAX_SIZE);
        if (!at) { refuse(r, idx, "site %d: executable memory allocation failed", idx); return 0; }
        cp_hook_status hs = cp_hook_emit(tramp, sizeof(tramp), &used, at, rt_addr, exp_rt, st->len, cb,
                                         ((cp_addr)gid << 16) | (cp_addr)idx);
        if (hs != CP_HOOK_OK) { refuse(r, idx, "site %d: trampoline refused (code %d: short branch or bad length)", idx, (int)hs); return 0; }
        uint8_t back[CP_HOOK_MAX_SIZE];
        if (!env->write(env->user, at, tramp, (uint32_t)used) || !env->read(env->user, at, back, (uint32_t)used) ||
            memcmp(back, tramp, used) != 0) {
            refuse(r, idx, "site %d: cannot write the trampoline", idx);
            return 0;
        }
        cp_hook_site_bytes(out, rt_addr, at, st->len);
        return 1;
    }
    default:
        return 0;
    }
}

/* put the original bytes back on sites[0..count) in reverse order; returns 1 if all restored */
static int restore_recs(cp_session *s, const cp_rec *recs, int count) {
    int ok = 1;
    for (int i = count - 1; i >= 0; --i) {
        uint8_t back[CP_MAX_SITE_LEN];
        if (!s->env.write(s->env.user, recs[i].addr, recs[i].orig, recs[i].len) ||
            !s->env.read(s->env.user, recs[i].addr, back, recs[i].len) || memcmp(back, recs[i].orig, recs[i].len) != 0)
            ok = 0;
    }
    return ok;
}

void cp_group_apply(cp_session *s, int gid, const cp_site *sites, int n, cp_result *res) {
    const cp_env *env = &s->env;
    uint8_t exp_rt[CP_MAX_GROUP_SITES][CP_MAX_SITE_LEN], now[CP_MAX_GROUP_SITES][CP_MAX_SITE_LEN];
    cp_addr rt[CP_MAX_GROUP_SITES];
    cp_rec pending[CP_MAX_GROUP_SITES];
    memset(res, 0, sizeof(*res));
    res->site = -1;

    if (!sites || n <= 0) { refuse(res, -1, "site table is empty (not ported yet)"); return; }
    if (n > CP_MAX_GROUP_SITES) { refuse(res, -1, "too many sites (%d, max %d)", n, CP_MAX_GROUP_SITES); return; }
    if (!env->read || !env->write) { refuse(res, -1, "no memory access"); return; }

    /* 1. static checks, runtime addresses, rebased expected bytes */
    for (int i = 0; i < n; ++i) {
        const cp_site *st = &sites[i];
        const char *why = check_site(st);
        if (why) { refuse(res, i, "site %d (0x%08x): %s", i, (unsigned)st->addr, why); return; }
        rt[i] = rebase(env, st->addr);
        memcpy(exp_rt[i], st->expected, st->len);
        if (st->kind == CP_SITE_ABS_FLOAT) wr32(exp_rt[i] + st->off, rebase(env, rd32(st->expected + st->off)));
        if (st->kind == CP_SITE_IMM || st->kind == CP_SITE_HOOK)
            for (int k = 0; k < 3; ++k)
                if (st->abs_ops[k]) wr32(exp_rt[i] + st->abs_ops[k], rebase(env, rd32(st->expected + st->abs_ops[k])));
    }

    /* 2. overlaps: inside the group */
    for (int i = 0; i < n; ++i)
        for (int j = i + 1; j < n; ++j)
            if (overlap(rt[i], sites[i].len, rt[j], sites[j].len)) {
                refuse(res, i, "sites %d (0x%08x) and %d (0x%08x) overlap", i, (unsigned)sites[i].addr, j, (unsigned)sites[j].addr);
                return;
            }

    /* 3. already applied by this group in this session? then verify and do nothing */
    int mine = 0;
    for (int k = 0; k < s->n_recs; ++k) if (s->recs[k].group == gid) ++mine;
    if (mine) {
        int same = (mine == n);
        for (int i = 0; same && i < n; ++i) {
            uint8_t cur[CP_MAX_SITE_LEN];
            int found = 0;
            for (int k = 0; k < s->n_recs && !found; ++k)
                if (s->recs[k].group == gid && s->recs[k].addr == rt[i] && s->recs[k].len == sites[i].len) {
                    found = env->read(env->user, rt[i], cur, sites[i].len) && memcmp(cur, s->recs[k].now, sites[i].len) == 0;
                }
            same = found;
        }
        if (same) { res->status = CP_GRP_ALREADY; res->n_sites = n; return; }
        refuse(res, -1, "group was applied earlier but its bytes changed since (or the table changed)");
        return;
    }

    /* 3b. overlaps with other groups already applied */
    for (int i = 0; i < n; ++i)
        for (int k = 0; k < s->n_recs; ++k)
            if (overlap(rt[i], sites[i].len, s->recs[k].addr, s->recs[k].len)) {
                refuse(res, i, "site %d (0x%08x) overlaps a site of group %d already applied", i, (unsigned)sites[i].addr, s->recs[k].group);
                return;
            }
    if (s->n_recs + n > CP_MAX_RECS) { refuse(res, -1, "internal registry full"); return; }

    /* 4. every site must hold its original bytes (nothing is written before all are checked) */
    for (int i = 0; i < n; ++i) {
        uint8_t cur[CP_MAX_SITE_LEN];
        if (!env->read(env->user, rt[i], cur, sites[i].len)) {
            refuse(res, i, "site %d (0x%08x): address not readable", i, (unsigned)sites[i].addr);
            return;
        }
        if (memcmp(cur, exp_rt[i], sites[i].len) != 0) {
            char a[64], b[64];
            hex(cur, sites[i].len, a, sizeof(a));
            hex(exp_rt[i], sites[i].len, b, sizeof(b));
            refuse(res, i, "site %d (0x%08x): bytes are %s, expected %s (other game build, or already patched)", i,
                   (unsigned)sites[i].addr, a, b);
            return;
        }
    }

    /* 5. build the new bytes (this may allocate and fill trampolines: that is not game code) */
    for (int i = 0; i < n; ++i) {
        if (!build_new(s, gid, i, &sites[i], rt[i], exp_rt[i], now[i], res)) return;
        if (memcmp(now[i], exp_rt[i], sites[i].len) == 0) {
            refuse(res, i, "site %d (0x%08x): the patch would change nothing", i, (unsigned)sites[i].addr);
            return;
        }
        pending[i].addr = rt[i];
        pending[i].group = (uint8_t)gid;
        pending[i].len = sites[i].len;
        memcpy(pending[i].orig, exp_rt[i], sites[i].len);
        memcpy(pending[i].now, now[i], sites[i].len);
    }

    /* 6. write, with rollback */
    for (int i = 0; i < n; ++i) {
        cp_status st = cp_write(env, rt[i], exp_rt[i], now[i], sites[i].len);
        if (st == CP_OK) continue;
        int restored = restore_recs(s, pending, i);
        res->site = i;
        res->status = restored ? CP_GRP_ROLLED_BACK : CP_GRP_BROKEN;
        snprintf(res->reason, sizeof(res->reason), "site %d (0x%08x): %s; %s", i, (unsigned)sites[i].addr,
                 cp_status_text(st), restored ? "the sites already written were restored" : "RESTORE FAILED, game code is inconsistent");
        return;
    }

    memcpy(&s->recs[s->n_recs], pending, sizeof(cp_rec) * (size_t)n);
    s->n_recs += n;
    res->status = CP_GRP_APPLIED;
    res->n_sites = n;
}

int cp_group_revert(cp_session *s, int gid) {
    cp_rec mine[CP_MAX_RECS];
    int n = 0, keep = 0;
    for (int k = 0; k < s->n_recs; ++k) {
        if (s->recs[k].group == gid) mine[n++] = s->recs[k];
        else s->recs[keep++] = s->recs[k];
    }
    if (!n) return 0;
    s->n_recs = keep;
    return restore_recs(s, mine, n) ? n : -1;
}
