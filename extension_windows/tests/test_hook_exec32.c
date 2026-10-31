/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * Runs the XMM-safe trampoline for real, in a 32-bit process (Linux x86, built with Zig as
 * x86-linux-musl). It checks that a C callback which destroys xmm0-xmm7 and the flags leaves the
 * hooked code's registers intact, that changes made through the context are applied, and that the
 * stack is 16-byte aligned for the callee.
 *
 * What this does NOT prove: that the trampoline works inside carrier_command.exe on Windows. The
 * encodings are the same and the calling convention (cdecl) is the same on both systems, but the
 * game itself has never been seen.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#define SYM "_"                    /* 32-bit Windows prefixes C symbols with an underscore */
#else
#include <sys/mman.h>
#define SYM ""
#endif

#include "cp_hook.h"

typedef struct state {
    float xmm[8][4];
    uint32_t ebx, esi, edi, ecx, edx, eax;
} state;

/* pad_words: extra words pushed before the call, so the hooked code sees every stack alignment */
void run_hooked(const state *in, state *out, void *fn, unsigned pad_words);

__asm__(
    ".text\n"
    ".globl " SYM "run_hooked\n"
    SYM "run_hooked:\n"
    "    pushl %ebp\n"
    "    movl %esp, %ebp\n"
    "    pushl %ebx\n"
    "    pushl %esi\n"
    "    pushl %edi\n"
    "    movl 20(%ebp), %eax\n"
    "    shll $2, %eax\n"
    "    subl %eax, %esp\n"
    "    movl 8(%ebp), %eax\n"
    "    movups 0(%eax), %xmm0\n    movups 16(%eax), %xmm1\n    movups 32(%eax), %xmm2\n    movups 48(%eax), %xmm3\n"
    "    movups 64(%eax), %xmm4\n   movups 80(%eax), %xmm5\n    movups 96(%eax), %xmm6\n    movups 112(%eax), %xmm7\n"
    "    movl 128(%eax), %ebx\n    movl 132(%eax), %esi\n    movl 136(%eax), %edi\n"
    "    movl 140(%eax), %ecx\n    movl 144(%eax), %edx\n    movl 148(%eax), %eax\n"
    "    call *16(%ebp)\n"
    "    leal -12(%ebp), %esp\n"
    "    pushl %eax\n"
    "    movl 12(%ebp), %eax\n"
    "    movups %xmm0, 0(%eax)\n    movups %xmm1, 16(%eax)\n    movups %xmm2, 32(%eax)\n    movups %xmm3, 48(%eax)\n"
    "    movups %xmm4, 64(%eax)\n   movups %xmm5, 80(%eax)\n    movups %xmm6, 96(%eax)\n    movups %xmm7, 112(%eax)\n"
    "    movl %ebx, 128(%eax)\n    movl %esi, 132(%eax)\n    movl %edi, 136(%eax)\n"
    "    movl %ecx, 140(%eax)\n    movl %edx, 144(%eax)\n"
    "    popl %ecx\n"
    "    movl %ecx, 148(%eax)\n"
    "    popl %edi\n    popl %esi\n    popl %ebx\n    popl %ebp\n"
    "    ret\n"
    ".globl " SYM "run_hooked_end\n"
    SYM "run_hooked_end:\n"
);
extern char run_hooked_end[];

static int failed, checks;
#define CHECK(c) do { ++checks; if (!(c)) { ++failed; printf("    FAIL line %d: %s\n", __LINE__, #c); } } while (0)

/* "game code": stc ; std ; [site: lea eax,[eax+1] ; nop dword [eax]] ; addss xmm0,xmm1 ; setc dl ; cld ; ret
 * The site is 6 bytes (lea does not touch the flags, so the CF set by stc must survive the hook, and
 * the direction flag is set at the site: the callback must still run with DF clear, as the C ABI wants). */
#define SITE_OFF 2
static const uint8_t GAME[] = {
    0xf9,                         /* 0: stc */
    0xfd,                         /* 1: std */
    0x8d, 0x40, 0x01,             /* 2: lea eax,[eax+1] */
    0x0f, 0x1f, 0x00,             /* 5: nop dword [eax] */
    0xf3, 0x0f, 0x58, 0xc1,       /* 8: addss xmm0,xmm1 */
    0x0f, 0x92, 0xc2,             /* c: setc dl */
    0xfc,                         /* f: cld (the C caller expects DF clear) */
    0xc3,                         /* 10: ret */
};
/* cld ; mov eax,0x1234 ; ret. The cld matters: the site runs with DF set (std), the trampoline restores
 * it, and the C code we return to must see DF clear. The Windows C runtime copies memory with string
 * instructions and crashed here without it (musl on Linux happened not to). */
static const uint8_t ALT[] = { 0xfc, 0xb8, 0x34, 0x12, 0x00, 0x00, 0xc3 };

static int mode;
static int calls;
static cp_hook_ctx seen;
static uintptr_t frame_mod16, ret_addr, last_user;
static uint32_t df_in_callback;
static uint8_t *alt_code;

static void callback(cp_hook_ctx *ctx, void *user) {
    seen = *ctx;
    ++calls;
    last_user = (uintptr_t)user;
    frame_mod16 = (uintptr_t)__builtin_frame_address(0) & 15u;
    ret_addr = CP_HOOK_STACK(ctx)[0];
    {
        uint32_t fl;
        __asm__ volatile("pushfl\n\tpopl %0" : "=r"(fl));
        df_in_callback = (fl >> 10) & 1u;
    }
    /* destroy everything the game might still need */
    __asm__ volatile("pxor %%xmm0,%%xmm0\n\tpxor %%xmm1,%%xmm1\n\tpxor %%xmm2,%%xmm2\n\tpxor %%xmm3,%%xmm3\n\t"
                     "pxor %%xmm4,%%xmm4\n\tpxor %%xmm5,%%xmm5\n\tpxor %%xmm6,%%xmm6\n\tpxor %%xmm7,%%xmm7\n\t"
                     "xorl %%eax,%%eax\n\tcmpl $1,%%eax"
                     ::: "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7", "eax", "ecx", "edx", "cc");
    volatile int x = 5;
    x = x - 7;                                    /* more flag noise from compiled code */
    if (mode == 1) {
        ctx->eax = 40;
        ctx->ebx = 0x77777777u;
        ctx->xmm[1][0] = 10.0f;
        ctx->eflags &= ~1u;                       /* clear CF: the game's setc must see 0 */
    } else if (mode == 2) {
        ctx->jump_to = (uint32_t)(uintptr_t)alt_code;   /* skip the displaced instructions */
    }
}

static void fill(state *s) {
    for (int r = 0; r < 8; ++r)
        for (int l = 0; l < 4; ++l) s->xmm[r][l] = (float)(100 * r + l) + 0.25f;
    s->ebx = 0x11111111u; s->esi = 0x22222222u; s->edi = 0x33333333u;
    s->ecx = 0xcafe0001u; s->edx = 0xbeef0000u; s->eax = 5;
}

int main(void) {
#ifdef _WIN32
    uint8_t *page = VirtualAlloc(NULL, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!page) {
        printf("VirtualAlloc RWX failed: cannot run this test here\n");
        return 2;
    }
#else
    uint8_t *page = mmap(NULL, 4096, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (page == MAP_FAILED) {
        printf("mmap RWX failed: cannot run this test here\n");
        return 2;
    }
#endif
    printf("== trampoline executed in a 32-bit process (pointer size %zu) ==\n", sizeof(void *));
    if (sizeof(void *) != 4) { printf("not a 32-bit process\n"); return 2; }
    uint8_t *game = page, *tramp = page + 256;
    alt_code = page + 128;
    memcpy(game, GAME, sizeof(GAME));
    memcpy(alt_code, ALT, sizeof(ALT));

    /* build the hook exactly as the patch layer does */
    uint8_t buf[CP_HOOK_MAX_SIZE], site_bytes[6];
    size_t used = 0;
    cp_addr site = (cp_addr)(uintptr_t)(game + SITE_OFF);
    CHECK(cp_hook_emit(buf, sizeof(buf), &used, (cp_addr)(uintptr_t)tramp, site, game + SITE_OFF, 6,
                       (cp_addr)(uintptr_t)callback, 0x00050007u) == CP_HOOK_OK);
    memcpy(tramp, buf, used);
    cp_hook_site_bytes(site_bytes, site, (cp_addr)(uintptr_t)tramp, 6);
    memcpy(game + SITE_OFF, site_bytes, 6);

    state in, out;
    fill(&in);

    /* 0: the callback destroys xmm0-7 and flags, changes nothing: the game must not notice */
    mode = 0; calls = 0;
    for (int round = 0; round < 8; ++round) {          /* several times, with 4 different stack alignments */
        memset(&out, 0, sizeof(out));
        run_hooked(&in, &out, game, (unsigned)round & 3u);
        CHECK(calls == round + 1);
        CHECK(frame_mod16 == 8);                       /* stack was 16-byte aligned at the call, whatever it was at the site */
        CHECK(out.eax == 6);                           /* lea eax,[eax+1] ran after the hook */
        CHECK(out.xmm[0][0] == in.xmm[0][0] + in.xmm[1][0]);   /* addss on the ORIGINAL xmm0 / xmm1 */
        CHECK(memcmp(&out.xmm[0][1], &in.xmm[0][1], 12) == 0);
        for (int r = 1; r < 8; ++r) CHECK(memcmp(out.xmm[r], in.xmm[r], 16) == 0);   /* xmm1..7 intact */
        CHECK(out.ebx == in.ebx && out.esi == in.esi && out.edi == in.edi && out.ecx == in.ecx);
        CHECK((out.edx & 0xff) == 1);                  /* CF set by stc before the hook survived */
        CHECK((out.edx & 0xffffff00u) == (in.edx & 0xffffff00u));
    }
    /* what the callback saw */
    CHECK(memcmp(seen.xmm, in.xmm, sizeof(in.xmm)) == 0);
    CHECK(seen.ebx == in.ebx && seen.esi == in.esi && seen.edi == in.edi);
    CHECK(seen.ecx == in.ecx && seen.edx == in.edx && seen.eax == in.eax);
    CHECK(seen.eflags & 1u);                           /* CF visible in the saved flags */
    CHECK(seen.eflags & 0x400u);                       /* DF was set at the site and is saved ... */
    CHECK(df_in_callback == 0);                        /* ... but the callback runs with DF clear (cld) */
    CHECK(seen.jump_to == (uint32_t)(uintptr_t)tramp + CP_HOOK_DISPLACED_OFF);   /* default continuation */
    CHECK(last_user == 0x00050007u);                   /* second argument */
    CHECK(ret_addr >= (uintptr_t)run_hooked && ret_addr < (uintptr_t)run_hooked_end);   /* CP_HOOK_STACK(ctx)[0] = game's return address */
    printf("  mode 0 (callback clobbers all xmm and flags, changes nothing): %s\n", failed ? "FAIL" : "ok");

    /* 1: the callback changes registers through the context */
    int before = failed;
    mode = 1;
    memset(&out, 0, sizeof(out));
    run_hooked(&in, &out, game, 1);
    CHECK(out.eax == 41);                              /* 40 set by the callback, +1 by the displaced lea */
    CHECK(out.xmm[0][0] == in.xmm[0][0] + 10.0f);      /* xmm1 lane 0 changed by the callback */
    CHECK(out.xmm[1][0] == 10.0f);                     /* ...and restored with that change */
    CHECK(out.ebx == 0x77777777u);                     /* a callee-saved register changed through the context */
    CHECK((out.edx & 0xff) == 0);                      /* CF cleared through ctx->eflags */
    printf("  mode 1 (callback edits eax, ebx, xmm1, CF through the context): %s\n", failed == before ? "ok" : "FAIL");

    /* 2: jump_to skips the displaced instructions */
    before = failed;
    mode = 2;
    memset(&out, 0, sizeof(out));
    run_hooked(&in, &out, game, 3);
    CHECK(out.eax == 0x1234);
    CHECK(out.xmm[0][0] == in.xmm[0][0]);              /* addss did not run */
    CHECK(out.ebx == in.ebx && out.esi == in.esi && out.edi == in.edi);
    printf("  mode 2 (callback redirects with jump_to): %s\n", failed == before ? "ok" : "FAIL");

    printf("\n%d checks, %d failed\n%s\n", checks, failed, failed ? "RESULT: FAIL" : "RESULT: ALL PASS");
    return failed ? 1 : 0;
}
