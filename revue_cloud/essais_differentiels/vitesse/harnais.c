#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <math.h>
#include <unistd.h>

struct cpu { uint64_t g[16]; uint8_t x[16][16]; uint64_t rflags; };
extern void run_case(struct cpu *in);
extern char epi_start[], epi_end[];
extern uint64_t target, saved_rsp, rsp_avant_appel, bad_align;
extern int h_gettop(), h_tointegerx(), h_pushinteger(), h_fopen(), h_fgetc(), h_fputs(), h_fclose();
extern long call_sentinel(void *fn, void *arg, uint64_t out[8]);

static uint64_t rs = 0x9e3779b97f4a7c15ULL;
static uint64_t rnd(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }

static void *mapfix(uint64_t addr, size_t len, int prot) {
    void *p = mmap((void *)addr, len, prot, MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
    if (p != (void *)addr) { perror("mmap"); exit(2); }
    return p;
}
static void load(const char *f, uint8_t *dst, size_t n) {
    FILE *h = fopen(f, "rb"); if (!h) { perror(f); exit(2); }
    if (fread(dst, 1, n, h) != n) { fprintf(stderr, "lecture %s\n", f); exit(2); }
    fclose(h);
}
static int nslot = 0;
static void tramp(uint64_t addr, void *fn) {
    uint64_t *slots = (uint64_t *)0x102900000ULL;
    slots[nslot] = (uint64_t)fn;
    int32_t disp = (int32_t)((uint64_t)&slots[nslot] - (addr + 6));
    nslot++;
    uint8_t *p = (uint8_t *)addr;
    p[0] = 0xff; p[1] = 0x25; memcpy(p + 2, &disp, 4);
}

/* --- fausse API Lua / libc --- */
struct fakeL { int n; long long a[4]; long long pushed; int npush; int isnum_nonnull; };
static int fail_read = 0, fail_write = 0;
static const char *redir = "scratch_mode.txt";
static char chemin_vu[512];
int c_gettop(struct fakeL *L) { return L->n; }
long long c_tointegerx(struct fakeL *L, int idx, int *isnum) {
    if (isnum) L->isnum_nonnull++;
    return (idx >= 1 && idx <= L->n && idx <= 4) ? L->a[idx - 1] : 0;
}
void c_pushinteger(struct fakeL *L, long long v) { L->pushed = v; L->npush++; }
FILE *c_fopen(const char *p, const char *m) {
    strncpy(chemin_vu, p, sizeof chemin_vu - 1);
    if (m[0] == 'r' && fail_read) return NULL;
    if (m[0] == 'w' && fail_write) return NULL;
    return fopen(redir, m);
}
int c_fgetc(FILE *f) { return fgetc(f); }
int c_fputs(const char *s, FILE *f) { return fputs(s, f); }
int c_fclose(FILE *f) { return fclose(f); }

static float F(uint32_t bits) { float f; memcpy(&f, &bits, 4); return f; }
static uint32_t B(float f) { uint32_t b; memcpy(&b, &f, 4); return b; }

static int fails = 0;
#define CHECK(cond, ...) do { if (!(cond)) { if (fails < 40) { printf("ECHEC: " __VA_ARGS__); printf("\n"); } fails++; } } while (0)

int main(int argc, char **argv) {
    uint8_t *zone = mapfix(0x10005d000, 0x1000, PROT_READ | PROT_WRITE | PROT_EXEC);
    uint8_t *hook = mapfix(0x1001c2000, 0x2000, PROT_READ | PROT_WRITE | PROT_EXEC);
    uint8_t *cst = mapfix(0x102869000, 0x1000, PROT_READ | PROT_WRITE);
    uint8_t *dat = mapfix(0x1029e5000, 0x1000, PROT_READ | PROT_WRITE);
    mapfix(0x102827000, 0x2000, PROT_READ | PROT_WRITE | PROT_EXEC);
    mapfix(0x102867000, 0x1000, PROT_READ | PROT_WRITE | PROT_EXEC);
    mapfix(0x102900000ULL, 0x1000, PROT_READ | PROT_WRITE);
    uint8_t *out = mapfix(0x20000000, 0x1000, PROT_READ | PROT_WRITE);
    uint8_t *mem = mapfix(0x30000000, 0x10000, PROT_READ | PROT_WRITE);
    uint8_t greffe[671], branch[67], avant[67];
    load("greffe.bin", greffe, 671); load("branch.bin", branch, 67); load("branch_avant.bin", avant, 67);
    memcpy(zone, greffe, 671);
    memcpy(hook + (0x1001c2b8e - 0x1001c2000), epi_start, epi_end - epi_start);
    tramp(0x1028278dc, h_gettop); tramp(0x102827dc4, h_tointegerx); tramp(0x10282801b, h_pushinteger);
    tramp(0x102867e78, h_fopen); tramp(0x102867e60, h_fgetc); tramp(0x102867e84, h_fputs); tramp(0x102867e42, h_fclose);
    uint8_t *modes = dat + 0x680, *etat = dat + 0x690;
    float *k48 = (float *)(cst + 0xaf0), *k144 = (float *)(cst + 0xb2c), *k72 = (float *)(cst + 0xb30);
    *k48 = 48; *k144 = 144; *k72 = 72;
    uint8_t *avion = mem, *equipe = mem + 0x1000; float *vit = (float *)(mem + 0x2000);
    uint8_t *code = hook + (0x1001c2b4b - 0x1001c2000);
    float planchers[4][2] = {{48, 72}, {48, 72}, {61, 91}, {144, 144}};

    /* ================= 1. PLANCHER : equivalence avec le code d'origine ================= */
    uint32_t spec[] = { 0, 0x80000000, 1, 0x007fffff, 0x7fc00000, 0xffc00000, 0x7f800001, 0x7f800000, 0xff800000,
        B(47.9f), B(48), B(48.1f), B(60.9f), B(61), B(71.9f), B(72), B(72.1f), B(90.9f), B(91), B(120), B(143.9f), B(144), B(144.1f),
        B(1e10f), B(-1e10f), B(-5), B(0.1f) };
    long ncas = 0, nmodes_non_orig = 0;
    for (long it = 0; it < 400000; it++) {
        struct cpu in;
        for (int i = 0; i < 16; i++) in.g[i] = rnd();
        for (int i = 0; i < 16; i++) for (int j = 0; j < 16; j++) in.x[i][j] = (uint8_t)rnd();
        in.rflags = 0x202 | (rnd() & 0x8d5);
        for (size_t i = 0; i < 0x400; i++) avion[i] = (uint8_t)rnd();
        for (size_t i = 0; i < 0x40; i++) equipe[i] = (uint8_t)rnd();
        uint32_t vb = (rnd() % 3 == 0) ? (uint32_t)rnd() : spec[rnd() % (sizeof spec / 4)];
        memcpy(vit, &vb, 4);
        int kind = rnd() % 8;            /* 0 null, 1 ia, 2.. joueur */
        uint64_t eqp = (kind == 0) ? 0 : (uint64_t)equipe;
        memcpy(avion + 0x260, &eqp, 8);
        uint32_t types[] = { 10, 10, 9, 8, 0, 11, 0xffffffffu, (uint32_t)rnd() };
        uint32_t typ = types[rnd() % 8]; memcpy(avion + 0x90, &typ, 4);
        if (kind == 1) equipe[0x19] = 1 + rnd() % 255; else if (kind != 0) equipe[0x19] = 0;
        uint32_t nums[] = { 0, 1, 2, 3, 15, 16, 17, 255, 0xffffffffu, 0x80000000u, (uint32_t)rnd(), (uint32_t)(rnd() % 16), (uint32_t)(rnd() % 16) };
        uint32_t num = nums[rnd() % 13]; memcpy(equipe + 0x14, &num, 4);
        for (int i = 0; i < 16; i++) modes[i] = (rnd() % 8 == 0) ? (uint8_t)rnd() : (uint8_t)(rnd() % 4);
        etat[0] = (uint8_t)rnd(); etat[1] = (uint8_t)rnd();
        in.g[3] = (uint64_t)vit; in.g[13] = (uint64_t)avion;
        uint8_t avion0[0x400], eq0[0x40];
        memcpy(avion0, avion, 0x400); memcpy(eq0, equipe, 0x40);
        /* plancher attendu */
        float lg = 48, lo = 72;
        int joueur = kind != 0 && equipe[0x19] == 0 && num < 16;
        if (joueur) { int m = modes[num]; if (m > 3) m = 0; lg = planchers[m][0]; lo = planchers[m][1]; if (m >= 2) nmodes_non_orig++; }
        /* A. reference : code d'origine, constantes = planchers attendus */
        *k48 = lg; *k72 = lo;
        memcpy(code, avant, 67); target = 0x1001c2b4b; bad_align = 0;
        run_case(&in);
        uint8_t ref[0x200], refav[0x400], refeq[0x40]; memcpy(ref, out, 0x200); memcpy(refav, avion, 0x400); memcpy(refeq, equipe, 0x40);
        uint64_t rsp_ref = rsp_avant_appel;
        /* B. greffe */
        memcpy(avion, avion0, 0x400); memcpy(equipe, eq0, 0x40);
        *k48 = 48; *k72 = 72;
        memcpy(code, branch, 67);
        run_case(&in);
        ncas++;
        int ok = 1;
        for (int r = 0; r < 16; r++) { uint64_t a, b; memcpy(&a, ref + 8 * r, 8); memcpy(&b, out + 8 * r, 8);
            if (a != b) { ok = 0; if (fails < 40) printf("  g[%d] ref %lx greffe %lx\n", r, a, b); } }
        for (int r = 0; r < 16; r++) if (memcmp(ref + 0x80 + 16 * r, out + 0x80 + 16 * r, 16)) { ok = 0; if (fails < 40) printf("  xmm%d differe\n", r); }
        uint64_t fa, fb; memcpy(&fa, ref + 0x180, 8); memcpy(&fb, out + 0x180, 8);
        if ((fa & 0x8d5) != (fb & 0x8d5)) { ok = 0; if (fails < 40) printf("  flags ref %lx greffe %lx\n", fa & 0x8d5, fb & 0x8d5); }
        if (memcmp(refav, avion, 0x400)) { ok = 0; if (fails < 40) printf("  memoire avion differe\n"); }
        if (memcmp(refeq, equipe, 0x40)) { ok = 0; if (fails < 40) printf("  memoire equipe differe\n"); }
        uint64_t rspg; memcpy(&rspg, out + 0x20, 8);
        if (rspg != rsp_avant_appel - 8) { ok = 0; if (fails < 40) printf("  rsp desequilibre\n"); }
        if (!ok) { fails++; if (fails < 40) printf("ECHEC plancher it=%ld kind=%d typ=%u num=%u v=%08x mode=%d\n", it, kind, typ, num, vb, num < 16 ? modes[num] : -1); }
    }
    printf("plancher : %ld cas (dont %ld avec plancher != origine), echecs cumules %d\n", ncas, nmodes_non_orig, fails);

    /* ================= 2. vit_lua : octets reels, API Lua simulee ================= */
    unlink(redir);
    memset(modes, 0, 16); etat[0] = etat[1] = 0;
    unsigned char M[16] = {0}, E0 = 0, E1 = 0;
    int fich_present = 0; char fich[8] = {0};       /* modele du fichier */
    long long speca[] = { 0, 1, 2, 3, 15, 16, 17, 100, -1, -2, 1LL << 32, (1LL << 32) + 1, 1LL << 40, (long long)0x8000000000000000ULL, 0x7fffffffffffffffLL };
    long long specb[] = { 0, 1, 2, 3, 4, 7, 9, 255, 256, -1, (1LL << 32) + 2, 1LL << 40, 0x7fffffffffffffffLL, (long long)0x8000000000000000ULL };
    long nlua = 0;
    for (long it = 0; it < 200000; it++) {
        int ev = rnd() % 40;
        if (ev == 0) { memset(modes, 0, 16); etat[0] = etat[1] = 0; memset(M, 0, 16); E0 = E1 = 0; }       /* redemarrage du jeu */
        else if (ev == 1) { unlink(redir); fich_present = 0; memset(fich, 0, sizeof fich); }
        else if (ev == 2) { FILE *f = fopen(redir, "w"); const char *c[] = { "", "2\n", "9\n", "0", "3", "1\n", "\n\n", "x" }; int k = rnd() % 8; fputs(c[k], f); fclose(f); fich_present = 1; strcpy(fich, c[k]); }
        else if (ev == 3) fail_read = rnd() & 1;
        else if (ev == 4) fail_write = rnd() & 1;
        struct fakeL L; memset(&L, 0, sizeof L);
        L.n = rnd() % 4; L.pushed = -99;
        for (int i = 0; i < 4; i++) L.a[i] = (rnd() % 3 == 0) ? (long long)rnd() : (i == 0 ? speca[rnd() % 15] : specb[rnd() % 14]);
        long long a1 = L.n >= 1 ? L.a[0] : 0, a2 = L.n >= 2 ? L.a[1] : 0;
        /* modele */
        int mode = 0;
        if (a1 >= 0 && a1 < 16) {
            if (!E0) { E0 = 1; int c = -1;
                if (!fail_read && fich_present) c = fich[0] ? fich[0] : -1;
                E1 = (c >= '1' && c <= '3') ? c - '0' : 0; }
            if (L.n >= 2) {
                if (a2 >= 1 && a2 <= 3) { M[a1] = a2;
                    if (a2 != E1) { if (!fail_write) { fich_present = 1; fich[0] = '0' + a2; fich[1] = '\n'; fich[2] = 0; } E1 = a2; } }
            } else if (M[a1] == 0) M[a1] = E1;
            mode = M[a1];
        }
        uint64_t sent[8]; bad_align = 0; memset(chemin_vu, 0, sizeof chemin_vu);
        long r = call_sentinel((void *)0x10005d080, &L, sent);
        nlua++;
        CHECK((int)r == 1, "retour %ld != 1", r);
        CHECK(L.npush == 1 && L.pushed == mode, "pousse %lld (x%d) attendu %d (n=%d a1=%lld a2=%lld)", L.pushed, L.npush, mode, L.n, a1, a2);
        CHECK(!bad_align, "pile non alignee a l'appel d'une fonction externe");
        CHECK(sent[0] == 0x1111111111111111ULL && sent[1] == 0x2222222222222222ULL && sent[2] == 0x3333333333333333ULL &&
              sent[3] == 0x4444444444444444ULL && sent[4] == 0x5555555555555555ULL && sent[5] == 0x6666666666666666ULL, "registre callee-saved abime");
        CHECK(sent[6] == rsp_avant_appel, "rsp apres appel");
        CHECK(!memcmp(modes, M, 16) && etat[0] == E0 && etat[1] == E1, "etat memoire != modele (it=%ld)", it);
        CHECK(L.isnum_nonnull == 0, "isnum non NULL");
        if (chemin_vu[0]) CHECK(!strcmp(chemin_vu, "/Users/UTILISATEUR/Library/Application Support/Carrier Command 2/vitesse_escadrille.txt"), "chemin %s", chemin_vu);
        /* le fichier reel == modele */
        FILE *f = fopen(redir, "r"); char buf[8] = {0}; int present = f != NULL; if (f) { size_t nn = fread(buf, 1, 7, f); buf[nn] = 0; fclose(f); }
        CHECK(present == fich_present && !strcmp(buf, fich), "fichier : present %d/%d contenu '%s'/'%s'", present, fich_present, buf, fich);
        if (fails > 40) break;
    }
    printf("vit_lua : %ld appels, echecs cumules %d\n", nlua, fails);
    printf("%s\n", fails ? "ECHECS" : "TOUT EST IDENTIQUE");
    return fails != 0;
}
