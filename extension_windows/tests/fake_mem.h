/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * A fake 32-bit address space for the host-side tests.
 *   - the "game image" lives at FM_IMG_BASE (deliberately not 0x00400000, so rebasing is exercised)
 *   - an executable arena at FM_ARENA_BASE serves the trampolines
 * Failure injection: fail / corrupt the Nth write, or every write from the Nth on.
 */
#ifndef FAKE_MEM_H
#define FAKE_MEM_H

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "cp_patch.h"

#define FM_IMG_BASE 0x01000000u
#define FM_IMG_SIZE 0x10000u
#define FM_ARENA_BASE 0x30000000u
#define FM_ARENA_SIZE 0x4000u
#define FM_TUN_BASE 0x20000000u          /* made-up address of the tunable table (no backing memory) */
#define FM_LOG_MAX 64

typedef struct fake_mem {
    uint8_t image[FM_IMG_SIZE];
    uint8_t arena[FM_ARENA_SIZE];
    uint32_t arena_next;
    int writes;                       /* number of write() calls */
    int fail_nth_write;               /* 1-based: that write call returns 0 without writing */
    int fail_writes_from;             /* 1-based: that write call and every later one return 0 */
    int corrupt_nth_write;            /* 1-based: that write stores the bytes with the last one flipped */
    char log[FM_LOG_MAX][256];
    int n_log;
} fake_mem;

static inline uint32_t fm_va_to_rt(uint32_t image_va) { return image_va - CP_IMAGE_BASE + FM_IMG_BASE; }

static inline uint8_t *fm_ptr(fake_mem *m, cp_addr a, uint32_t len) {
    if (a >= FM_IMG_BASE && (uint64_t)a + len <= (uint64_t)FM_IMG_BASE + FM_IMG_SIZE) return m->image + (a - FM_IMG_BASE);
    if (a >= FM_ARENA_BASE && (uint64_t)a + len <= (uint64_t)FM_ARENA_BASE + FM_ARENA_SIZE) return m->arena + (a - FM_ARENA_BASE);
    return NULL;
}

static inline int fm_read(void *user, cp_addr a, void *out, uint32_t len) {
    uint8_t *p = fm_ptr(user, a, len);
    if (!p) return 0;
    memcpy(out, p, len);
    return 1;
}

static inline int fm_write(void *user, cp_addr a, const void *data, uint32_t len) {
    fake_mem *m = user;
    uint8_t *p = fm_ptr(m, a, len);
    ++m->writes;
    if (!p) return 0;
    if (m->fail_nth_write == m->writes) return 0;
    if (m->fail_writes_from && m->writes >= m->fail_writes_from) return 0;
    memcpy(p, data, len);
    if (m->corrupt_nth_write == m->writes) p[len - 1] ^= 0xff;
    return 1;
}

static inline cp_addr fm_alloc(void *user, uint32_t len) {
    fake_mem *m = user;
    len = (len + 15u) & ~15u;
    if (m->arena_next + len > FM_ARENA_SIZE) return 0;
    cp_addr a = FM_ARENA_BASE + m->arena_next;
    m->arena_next += len;
    return a;
}

static inline cp_addr fm_va(void *user, uint32_t image_va) { (void)user; return fm_va_to_rt(image_va); }
static inline cp_addr fm_hook_addr(void *user, int id) { (void)user; return id ? 0x70000000u + (cp_addr)id * 0x100u : 0; }

static inline void fm_log(void *user, int level, const char *msg) {
    fake_mem *m = user;
    if (m->n_log < FM_LOG_MAX) snprintf(m->log[m->n_log++], sizeof(m->log[0]), "%d:%s", level, msg);
}

static inline void fm_init(fake_mem *m) {
    memset(m, 0, sizeof(*m));
    memset(m->image, 0xCC, sizeof(m->image));
}

static inline void fm_env(fake_mem *m, cp_env *env) {
    memset(env, 0, sizeof(*env));
    env->user = m;
    env->read = fm_read;
    env->write = fm_write;
    env->alloc_exec = fm_alloc;
    env->va = fm_va;
    env->hook_addr = fm_hook_addr;
    env->log = fm_log;
    env->image_lo = FM_IMG_BASE;
    env->image_size = FM_IMG_SIZE;
}

/* put bytes / a float at an IMAGE VA (the runtime location is rebased) */
static inline void fm_put(fake_mem *m, uint32_t image_va, const void *bytes, uint32_t len) {
    memcpy(m->image + (image_va - CP_IMAGE_BASE), bytes, len);
}
static inline void fm_put_f32(fake_mem *m, uint32_t image_va, float f) { fm_put(m, image_va, &f, 4); }
static inline uint8_t *fm_at(fake_mem *m, uint32_t image_va) { return m->image + (image_va - CP_IMAGE_BASE); }

#endif
