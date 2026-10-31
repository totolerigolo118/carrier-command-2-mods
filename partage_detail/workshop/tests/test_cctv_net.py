#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the 'cctv_net' module (sharper CCTV camera screen) without launching the game.

1. Applies the module to a COPY of the original executable: md5, the 4 jumps read back with objdump (and
   the original instruction right after), every exit of the patch code, the scale cell, no game jump
   into the middle of the replaced bytes, no other access to the cell.
2. RUNS the patch code (same assembly source, x86_64 via Rosetta) in a small test program that
   imitates the 4 places in the game: image size depending on type and script, UI camera, glScissor rectangle
   with and without scale, reset to zero.
Usage: python3 tests/test_cctv_net.py
"""
import collections, hashlib, importlib.util, os, re, shutil, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
OUTIL = os.path.join(os.path.dirname(ICI), "outil")
sys.path.insert(0, OUTIL)
sys.path.insert(0, os.path.join(OUTIL, "generateurs"))
import patchs_cc2 as P
import generer_cctv_net as G

ok = True
def verifier(nom, condition, detail=""):
    global ok
    ok = ok and condition
    print("  %-66s %s %s" % (nom, "OK" if condition else "FAIL", detail if not condition else ""))


def instructions(chemin, debut, fin):
    sortie = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "--start-address=%#x" % debut,
                             "--stop-address=%#x" % fin, chemin], capture_output=True, text=True).stdout
    lignes = []
    for l in sortie.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+(.*)", l)
        if m:
            lignes.append((int(m.group(1), 16), re.sub(r"\s*<[^>]*>", "", m.group(2)).strip()))
    return lignes


# (jump, original instruction that follows, its address)
SITES = [(0x1000ad74f, "movq\t0xc8(%rbx), %rdi", 0x1000ad77c), (0x10021ce70, "movl\t$0x2, (%rbx)", 0x10021ce85),
         (0x10015e662, "callq\t0x10286807c", 0x10015e6a8), (0x10021cf13, "callq\t0x102867fe6", 0x10021cf18)]

HARNAIS = r"""
.text
.globl _essai_a
_essai_a:
    pushq %rbp
    movq %rsp, %rbp
    movq %rdi, %rax
    movq %rsi, %rcx
    movl $0xdead, %r8d
    movl $0xdead, %r9d
    jmp _cctv_a
.globl g_ret_a
g_ret_a:
    movl %r8d, _res_larg(%rip)
    movl %r9d, _res_haut(%rip)
    popq %rbp
    ret
.globl _essai_b
_essai_b:
    pushq %rbp
    movq %rsp, %rbp
    pushq %r14
    pushq %rbx
    movq %rdi, %r14
    xorps %xmm0, %xmm0
    xorps %xmm2, %xmm2
    jmp _cctv_b
.globl g_ret_b
g_ret_b:
    movss %xmm0, _res_f0(%rip)
    movss %xmm2, _res_f2(%rip)
    popq %rbx
    popq %r14
    popq %rbp
    ret
.globl _essai_c
_essai_c:
    pushq %rbp
    movq %rsp, %rbp
    jmp _cctv_c
.globl g_ret_c
g_ret_c:
    movl %edi, _res_x(%rip)
    movl %esi, _res_y(%rip)
    movl %edx, _res_w(%rip)
    movl %ecx, _res_h(%rip)
    popq %rbp
    ret
.globl _essai_d
_essai_d:
    pushq %rbp
    movq %rsp, %rbp
    xorl %edi, %edi
    jmp _cctv_d
.globl g_ret_d
g_ret_d:
    movl %edi, _res_x(%rip)
    popq %rbp
    ret
.data
.p2align 4
.globl g_tab_haut, g_tab_larg, g_128, g_demi, g_echelle
g_tab_haut: .long 128, 128, 256, 256, 192, 32
g_tab_larg: .long 128, 256, 512, 256, 256, 64
g_128: .float 128.0
g_demi: .float 0.5
g_echelle: .long 0
.globl _res_larg, _res_haut, _res_f0, _res_f2, _res_x, _res_y, _res_w, _res_h
_res_larg: .long 0
_res_haut: .long 0
_res_f0: .float 0
_res_f2: .float 0
_res_x: .long 0
_res_y: .long 0
_res_w: .long 0
_res_h: .long 0
"""

ESSAI = r"""
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
extern void essai_a(void *defs, long off); extern void essai_b(void *img); extern void essai_c(void *el); extern void essai_d(void);
extern unsigned res_larg, res_haut; extern float res_f0, res_f2; extern int res_x, res_y, res_w, res_h;
extern float echelle __asm__("g_echelle");
static int ok = 1;
static void verif(const char *nom, int c) { ok &= c; printf("%s|%s\n", c ? "OK" : "ECHEC", nom); }
struct mm_string { char *p; unsigned len; unsigned pad; };
static void def(unsigned char *defs, int i, int type, const char *script) {
    unsigned char *e = defs + i * 0x78;
    memset(e, 0x55, 0x78);
    struct mm_string s = { NULL, 0, 0 };
    if (script) { s.len = strlen(script); s.p = malloc(s.len + 1); memcpy(s.p, script, s.len + 1); }
    memcpy(e + 0x18, &s, 16);
    memcpy(e + 0x60, &type, 4);
}
int main(void) {
    static unsigned char defs[16 * 0x78];
    struct { int type; const char *script; unsigned larg, haut; const char *nom; } A[] = {
        {0, "scripts/screen_navigation.lua", 128, 128, "A type 0, other script -> 128 x 128"},
        {0, "scripts/screen_cctv.lua", COTE, COTE, "A type 0, screen_cctv.lua -> enlarged image"},
        {2, "scripts/screen_holomap.lua", 512, 256, "A type 2 -> 512 x 256 (original table)"},
        {1, "scripts/screen_landing.lua", 256, 128, "A type 1 -> 256 x 128"},
        {4, "", 256, 192, "A type 4, empty script -> 256 x 192"},
        {5, "scripts/screen_carrier_camera.lua", 64, 32, "A type 5 -> 64 x 32"},
        {7, "scripts/x.lua", 128, 128, "A type 7 (> 5) -> 128 x 128 by default"},
        {0, NULL, 128, 128, "A type 0, no script (null text) -> 128"},
        {0, "scripts/screen_cctv.lux", 128, 128, "A same length, last character different -> 128"},
        {0, "Scripts/screen_cctv.lua", 128, 128, "A same length, first character different -> 128"},
        {0, "scripts/screen_cXtv.lua", 128, 128, "A same length, middle different -> 128"},
        {0, "scripts/screen_cctv.lua2", 128, 128, "A longer -> 128"},
    };
    int n = sizeof A / sizeof A[0];
    for (int i = 0; i < n; i++) def(defs, i, A[i].type, A[i].script);
    for (int i = 0; i < n; i++) {
        essai_a(defs, i * 0x78L);
        char t[140]; snprintf(t, sizeof t, "%s [%u x %u]", A[i].nom, res_larg, res_haut);
        verif(t, res_larg == A[i].larg && res_haut == A[i].haut);
    }
    struct { unsigned w, h; float f0, f2, ech; } B[] = {
        {COTE, COTE, 128, 128, COTE / 128.0f}, {128, 128, 128, 128, 0}, {512, 256, 512, 256, 0},
        {256, 256, 256, 256, 0}, {COTE, 128, COTE, 128, 0}, {64, 32, 64, 32, 0}};
    for (int i = 0; i < 6; i++) {
        unsigned char img[0x40]; memset(img, 0x77, sizeof img);
        memcpy(img + 0x20, &B[i].w, 4); memcpy(img + 0x24, &B[i].h, 4);
        echelle = 99.0f;
        essai_b(img);
        char t[140]; snprintf(t, sizeof t, "B image %u x %u -> camera %g x %g, scale %g", B[i].w, B[i].h, res_f0, res_f2, echelle);
        verif(t, res_f0 == B[i].f0 && res_f2 == B[i].f2 && echelle == B[i].ech);
    }
    float R[][4] = {{5, 5, 118, 118}, {0, 0, 128, 128}, {5.3f, 2.7f, 117.6f, 20.2f}, {12, 100, 40.49f, 0.5f}};
    for (int k = 0; k < 2; k++) {
        float s = k ? COTE / 128.0f : 0;
        for (int i = 0; i < 4; i++) {
            float el[6] = {0, 0, R[i][0], R[i][1], R[i][2], R[i][3]};
            echelle = s;
            essai_c(el);
            float m = k ? s : 1;
            int x = (int)floorf(R[i][0] * m), y = (int)floorf(R[i][1] * m);
            int w = (int)floorf(R[i][2] * m + 0.5f), h = (int)floorf(R[i][3] * m + 0.5f);
            char t[140]; snprintf(t, sizeof t, "C scale %g: (%g,%g,%g,%g) -> (%d,%d,%d,%d)", s, R[i][0], R[i][1], R[i][2], R[i][3], res_x, res_y, res_w, res_h);
            verif(t, res_x == x && res_y == y && res_w == w && res_h == h);
        }
    }
    echelle = 4.0f; essai_d();
    verif("D scale reset to 0, edi = 0xb44 (original instruction)", echelle == 0 && res_x == 0xb44);
    return !ok;
}
"""


tmp = tempfile.mkdtemp(prefix="test_cctv_")
try:
    # 1. the module on a copy
    print("Module cctv_net applied to a copy of the original executable:")
    chemin_module = os.path.join(OUTIL, "modules", "cctv_net.py")
    spec = importlib.util.spec_from_file_location("cctv_net", chemin_module)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    md5_attendu = re.search(r"md5 of the executable with this module alone: ([0-9a-f]{32})", open(chemin_module).read()).group(1)  # literal text written into the module file by its generator (do not translate)
    origine = os.path.join(os.path.dirname(OUTIL), "sauvegarde", "build_mac_origine")
    prog = os.path.join(tmp, "build_mac")
    shutil.copyfile(origine, prog)
    d = bytearray(open(prog, "rb").read())
    verifier("copy = original executable", hashlib.md5(d).hexdigest() == G.MD5_ORIGINE)
    for _, va, avant, apres in m.RETOUCHES:
        o = va - P.BASE
        assert d[o:o + len(avant) // 2].hex() == avant
        d[o:o + len(apres) // 2] = bytes.fromhex(apres)
    open(prog, "wb").write(d)
    verifier("md5 of the copy = md5 announced by the module", hashlib.md5(d).hexdigest() == md5_attendu)

    greffe = bytes.fromhex(m.RETOUCHES[0][3])
    debut, fin = G.ZONE_DEBUT, G.ZONE_DEBUT + len(greffe)
    verifier("patch code in its zone (0x100061800..0x100061a00, before ecriture_releve)",
             m.RETOUCHES[0][1] == G.ZONE_DEBUT and fin <= G.ZONE_FIN)
    verifier('compared text: "scripts/screen_cctv.lua" at the end of the patch code', greffe.endswith(b"scripts/screen_cctv.lua"))

    zone = instructions(prog, debut, fin - 23)
    entrees = {}
    with tempfile.TemporaryDirectory() as dd:
        _, _, points, _, _ = G.generer(open(origine, "rb").read(), dd)
    for (va, suite, va_suite), nom in zip(SITES, ("_cctv_a", "_cctv_b", "_cctv_c", "_cctv_d")):
        site = instructions(prog, va, va_suite + 8)
        apres_saut = [x for x in site[1:] if not x[1].startswith("nop")]
        verifier("%#x: jmp %s (%#x), then the original instruction at %#x" % (va, nom, points[nom], va_suite),
                 site[0][1] == "jmp\t%#x" % points[nom] and apres_saut and apres_saut[0] == (va_suite, suite),
                 str(site[:2]) + str(apres_saut[:1]))
    sorties = collections.Counter(i.split("\t")[1] for _, i in zone if i.startswith("jmp\t") and not debut <= int(i.split("\t")[1], 16) < fin)
    attendu = collections.Counter({"%#x" % G.JEU["g_ret_a"]: 2, "%#x" % G.JEU["g_ret_b"]: 2,
                                   "%#x" % G.JEU["g_ret_c"]: 2, "%#x" % G.JEU["g_ret_d"]: 1})
    verifier("patch code: 7 returns to the game, right after the 4 jumps", sorties == attendu, str(sorties))
    cibles = collections.Counter(int(x, 16) for x in re.findall(r"## (0x[0-9a-f]+)",
                                 subprocess.run(["objdump", "-d", "--start-address=%#x" % debut, "--stop-address=%#x" % (fin - 23), prog],
                                                capture_output=True, text=True).stdout))
    permis = {G.JEU[k] for k in ("g_tab_haut", "g_tab_larg", "g_128", "g_echelle", "g_demi")} | {fin - 23, fin - 15, fin - 8}
    verifier("patch code: reads only the tables, 128.0, 0.5, the cell and the text", set(cibles) <= permis, str(sorted(map(hex, cibles))))
    verifier("patch code: the scale cell is written 3 times (B x 2, D) and read 1 time (C)", cibles[G.JEU["g_echelle"]] == 4)
    verifier("patch code: a single hard-coded size (%d) in A and B" % G.TAILLE,
             sum(("$%#x," % G.TAILLE) in i for _, i in zone) == 4, str([i for _, i in zone if "$%#x" % G.TAILLE in i]))

    nm = subprocess.run(["nm", "-m", origine], capture_output=True, text=True).stdout
    verifier("cell 0x102a2a864 = ShowExampleAppSimpleOverlay::corner, in __bss (0 at start)",
             re.search(r"0000000102a2a864 \(__DATA,__bss\) non-external __ZZL27ShowExampleAppSimpleOverlayPbE6corner", nm) is not None)

    print("  (re-reading the whole executable: jumps, calls and accesses to the cell...)")
    tout = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "--start-address=0x100001000",
                           "--stop-address=0x102858000", prog], capture_output=True, text=True).stdout
    milieux = []
    vers_greffe = []
    case = []
    for l in tout.splitlines():
        mm = re.match(r"\s*([0-9a-f]+):\s+(j[a-z]+|callq)\s+(0x[0-9a-f]+)", l)
        if mm:
            src, cible = int(mm.group(1), 16), int(mm.group(3), 16)
            for va, _, va_suite in SITES:
                if va < cible < va_suite:
                    milieux.append((hex(src), hex(cible)))
            if debut <= cible < fin and not 0x10005af39 <= src < 0x100061c00:   # outside dead ImGui code
                vers_greffe.append((hex(src), hex(cible)))
        if "## 0x102a2a86" in l and re.search(r"## 0x102a2a86[4-7]", l):
            mm = re.match(r"\s*([0-9a-f]+):", l)
            if mm:
                case.append(int(mm.group(1), 16))
    verifier("no game jump into the middle of the replaced bytes", not milieux, str(milieux))
    verifier("outside dead ImGui code, only the 4 jumps lead to the patch code",
             sorted(vers_greffe) == sorted((hex(va), hex(points[n])) for (va, _, _), n in zip(SITES, ("_cctv_a", "_cctv_b", "_cctv_c", "_cctv_d"))),
             str(vers_greffe))
    verifier("the cell is used only by the patch code and dead ImGui code",
             case and all(0x10005af39 <= a < 0x100061c00 for a in case), str([hex(a) for a in case if not 0x10005af39 <= a < 0x100061c00]))

    # 2. the patch code running
    print("Patch code executed (x86_64 via Rosetta) in a test program that imitates the 4 places:")
    s = os.path.join(tmp, "greffe.s")
    echelle = __import__("struct").unpack("<I", __import__("struct").pack("<f", G.TAILLE / 128.0))[0]
    open(s, "w").write(".set TAILLE, %d\n.set ECHELLE, 0x%08x\n" % (G.TAILLE, echelle) + open(G.SOURCE).read())
    open(os.path.join(tmp, "harnais.s"), "w").write(HARNAIS)
    open(os.path.join(tmp, "essai.c"), "w").write(ESSAI)
    exe = os.path.join(tmp, "essai")
    r = subprocess.run(["clang", "-arch", "x86_64", "-O1", "-DCOTE=%d" % G.TAILLE, "-c", "-o", os.path.join(tmp, "essai.o"),
                        os.path.join(tmp, "essai.c")], capture_output=True, text=True)
    r2 = subprocess.run(["clang", "-arch", "x86_64", "-o", exe, os.path.join(tmp, "essai.o"), os.path.join(tmp, "harnais.s"), s],
                        capture_output=True, text=True)
    verifier("test program built", r.returncode == 0 and r2.returncode == 0, r.stderr + r2.stderr)
    r = subprocess.run([exe], capture_output=True, text=True)
    lignes = [l.split("|", 1) for l in r.stdout.splitlines() if "|" in l]
    for etat, nom in lignes:
        verifier(nom, etat == "OK")
    verifier("27 cases run, program ended without error", len(lignes) == 27 and r.returncode == 0, r.stderr.strip())
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\nRESULT: " + ("ALL PASSED" if ok else "THERE ARE FAILURES"))
sys.exit(0 if ok else 1)
