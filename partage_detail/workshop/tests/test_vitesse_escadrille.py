#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test of the 'vitesse_escadrille' module (executable), without the game.

1. Applies the generated module to a COPY of the original executable and reads it back with objdump: branch in
   tick_control, patch code, "cc2_vitesse" entry of base_funcs.
2. RUNS the patch code (same C source, x86_64 via Rosetta) in a small test program that provides
   fake Lua functions and a fake plane:
   - speed floor for each mode, Albatros / Manta, player team / AI / no team, speed
     of the tracked object above the floor or the ceiling; rax/rcx registers returned intact;
   - Lua function: read, set, mode file (created, re-read at the next start), invalid values.
Usage: python3 tests/test_vitesse_escadrille.py
"""
import importlib.util, os, re, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
ATELIER = os.path.dirname(ICI)
sys.path.insert(0, os.path.join(ATELIER, "outil", "generateurs"))
import generer_helicos_ascenseur as G
import generer_vitesse_escadrille as V

ok = True


def verifier(nom, condition, detail=""):
    global ok
    print(("  OK   " if condition else "  FAIL ") + nom + ("" if condition or not detail else " : " + str(detail)))
    ok = ok and bool(condition)


def instructions(chemin, debut, fin):
    sortie = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "--start-address=%#x" % debut,
                             "--stop-address=%#x" % fin, chemin], capture_output=True, text=True).stdout
    return [re.sub(r"\s+", " ", l.split(":", 1)[1]).strip() for l in sortie.splitlines()
            if re.match(r"^\s*[0-9a-f]+:", l)]


HARNAIS_C = r"""
#include <stdio.h>
#include <string.h>
typedef struct lua_State lua_State;
struct lua_State { int n; long long args[4]; long long pousse; int nb_pousse; };
unsigned char g_vit_modes[16];
unsigned char g_vit_etat[2];
int g_lua_gettop(lua_State *L) { return L->n; }
long long g_lua_tointegerx(lua_State *L, int i, int *isnum) { (void)isnum; return (i >= 1 && i <= L->n) ? L->args[i - 1] : 0; }
void g_lua_pushinteger(lua_State *L, long long v) { L->pousse = v; L->nb_pousse++; }
FILE *g_fopen(const char *c, const char *m) { return fopen(c, m); }
int g_fgetc(FILE *f) { return fgetc(f); }
int g_fputs(const char *s, FILE *f) { return fputs(s, f); }
int g_fclose(FILE *f) { return fclose(f); }
int vit_lua(lua_State *L);
void essai_plancher(const float *vitesse, unsigned char *avion, unsigned long long *sortie);

static long long appel(long long equipe, long long mode, int n) {
    lua_State L = { n, { equipe, mode, 0, 0 }, -99, 0 };
    int r = vit_lua(&L);
    if (r != 1 || L.nb_pousse != 1) return -1000;
    return L.pousse;
}

int main(int argc, char **argv) {
    (void)argc;
    /* --- Lua function --- */
    printf("L read_empty %lld\n", appel(1, 0, 1));
    printf("L set3 %lld\n", appel(1, 3, 2));
    printf("L read %lld\n", appel(1, 0, 1));
    printf("L other_team %lld\n", appel(2, 0, 1));
    printf("L bad_mode %lld\n", appel(1, 7, 2));
    printf("L zero_mode %lld\n", appel(1, 0, 2));
    printf("L team_16 %lld\n", appel(16, 2, 2));
    printf("L team_neg %lld\n", appel(-1, 2, 2));
    printf("L set1 %lld\n", appel(1, 1, 2));
    FILE *f = fopen(argv[1], "r"); char t[8] = {0}; if (f) { fgets(t, sizeof t, f); fclose(f); }
    printf("F contents %c\n", t[0] ? t[0] : '-');
    /* next start: memory reset to zero, the file remains */
    memset(g_vit_modes, 0, sizeof g_vit_modes); memset(g_vit_etat, 0, sizeof g_vit_etat);
    printf("L restart %lld\n", appel(1, 0, 1));
    printf("L restart_other %lld\n", appel(3, 0, 1));

    /* --- speed floor --- */
    unsigned char equipe_joueur[0x20] = {0}, equipe_ia[0x20] = {0};
    equipe_joueur[0x14] = 1; equipe_ia[0x14] = 2; equipe_ia[0x19] = 1;
    float vitesses[] = { 0.0f, 50.0f, 100.0f, 500.0f };
    int types[] = { 8, 10 };
    for (int m = 0; m <= 4; m++) {
        memset(g_vit_modes, 0, sizeof g_vit_modes);
        g_vit_modes[1] = (unsigned char)m; g_vit_modes[2] = 3;
        for (int e = 0; e < 3; e++)
        for (int k = 0; k < 2; k++)
        for (int v = 0; v < 4; v++) {
            unsigned char avion[0x300] = {0};
            unsigned char *eq = e == 0 ? equipe_joueur : e == 1 ? equipe_ia : NULL;
            memcpy(avion + 0x260, &eq, 8);
            memcpy(avion + 0x90, &types[k], 4);
            unsigned long long s[4] = {0};
            essai_plancher(&vitesses[v], avion, s);
            float x0, x1, c; memcpy(&x0, &s[0], 4); memcpy(&x1, &s[1], 4); memcpy(&c, avion + 0x2c8, 4);
            printf("P %d %d %d %g %g %g %g %llx %llx\n", m, e, types[k], vitesses[v], c, x0, x1, s[2], s[3]);
        }
    }
    return 0;
}
"""

HARNAIS_S = r"""
.text
.globl _essai_plancher
_essai_plancher:                 # rdi = &speed, rsi = plane, rdx = output[4]
    pushq %rbx
    pushq %r13
    pushq %r12
    movq %rdi, %rbx
    movq %rsi, %r13
    movq %rdx, %r12
    movabsq $0x1111111111111111, %rax
    movabsq $0x2222222222222222, %rcx
    xorps %xmm0, %xmm0
    xorps %xmm1, %xmm1
    call _vit_plancher           # the patch code ends with "jmp _g_ret_2b8e" = ret here
    movss %xmm0, (%r12)
    movss %xmm1, 8(%r12)
    movq %rax, 16(%r12)
    movq %rcx, 24(%r12)
    popq %r12
    popq %r13
    popq %rbx
    ret
.globl _g_ret_2b8e
_g_ret_2b8e:
    ret
"""


def attendu_plancher(mode, equipe, typ, v):
    """What the game must do: original bounds except player team with mode 1..3."""
    pl = {0: (48, 72), 1: (48, 72), 2: (61, 91), 3: (144, 144)}
    m = mode if equipe == 0 and 0 <= mode <= 3 else 0
    leger, lourd = pl[m]
    x1 = min(max(v, leger), 144)
    if typ == 10:
        x0 = min(max(v, lourd), 144)
        return x0, x0, x1
    return x1, v, x1


def main():
    programme = open(G.ORIGINE, "rb").read()
    verifier("original executable rebuilt", __import__("hashlib").md5(programme).hexdigest() == G.MD5_ORIGINE)

    spec = importlib.util.spec_from_file_location("m", os.path.join(ATELIER, "outil", "modules", "vitesse_escadrille.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with tempfile.TemporaryDirectory(prefix="test_vitesse_") as dossier:
        # is the written module up to date with the source?
        retouches, md5, points, relocs, taille = V.generer(programme, dossier)
        verifier("module up to date with vitesse_escadrille.c",
                 [(r[1], r[2], r[3]) for r in module.RETOUCHES] == [(va, av, ap) for va, av, ap, _ in retouches])

        copie = bytearray(programme)
        for _, va, avant, apres in module.RETOUCHES:
            o = va - G.BASE_FICHIER
            verifier("original bytes at %#x" % va, copie[o:o + len(avant) // 2].hex() == avant)
            copie[o:o + len(apres) // 2] = bytes.fromhex(apres)
        prog = os.path.join(dossier, "build_mac")
        open(prog, "wb").write(copie)

        # 1. read-back with objdump
        b = instructions(prog, 0x1001c2b4b, 0x1001c2b95)
        verifier("branch: jmp to the patch code", b and b[0].startswith("jmp 0x10005d000"), b[:1])
        verifier("branch: the rest = int3 up to 0x1001c2b8e", all(i == "int3" for i in b[1:-1]) and len(b) == 64, len(b))
        verifier("rest of the game intact", b[-1].startswith("movl 0x318(%r13), %esi"), b[-1:])
        z = instructions(prog, points["_vit_plancher"], points["_vit_lua"])
        verifier("patch code: replays movss (%rbx), %xmm0", z[0] == "movss (%rbx), %xmm0", z[:1])
        verifier("patch code: team 0x260, is_ai 0x19, number 0x14",
                 "movq 0x260(%r13), %rax" in z and "cmpb $0x0, 0x19(%rax)" in z and "movl 0x14(%rax), %eax" in z)
        verifier("patch code: writes 0x2c8 and tests type 10",
                 sum(i.startswith("movss") and i.endswith("0x2c8(%r13)") for i in z) == 2 and "cmpl $0xa, 0x90(%r13)" in z)
        sauts = [i for i in z if i.startswith("jmp 0x")]
        verifier("patch code: returns to 0x1001c2b8e", any(i.startswith("jmp 0x1001c2b8e") for i in sauts), sauts)
        nom, fonction = struct.unpack_from("<QQ", copie, V.BASE_FUNCS_DOFILE - G.BASE_FICHIER)
        o = nom - G.BASE_FICHIER
        verifier('base_funcs: name "cc2_vitesse"', copie[o:o + 12] == b"cc2_vitesse\0", copie[o:o + 12])
        verifier("base_funcs: function = vit_lua", fonction == points["_vit_lua"], hex(fonction))
        f = instructions(prog, points["_vit_lua"], points["_vit_lua"] + 16)
        verifier("vit_lua starts with a real prologue", f[:2] == ["pushq %rbp", "movq %rsp, %rbp"], f[:2])
        appels = [i for i in instructions(prog, points["_vit_lua"], points["_vit_nom_lua"]) if i.startswith("callq")]
        cibles = {int(re.match(r"callq 0x([0-9a-f]+)", i).group(1), 16) for i in appels}
        verifier("vit_lua only calls Lua/libc functions of the game",
                 cibles <= {V.JEU[k] for k in ("_g_lua_gettop", "_g_lua_tointegerx", "_g_lua_pushinteger",
                                               "_g_fopen", "_g_fgetc", "_g_fputs", "_g_fclose")}, sorted(map(hex, cibles)))
        verifier("floors in the executable",
                 struct.unpack_from("<8f", copie, points["_vit_planchers"] - G.BASE_FICHIER) == (48, 72, 48, 72, 61, 91, 144, 144))

        # 2. real execution of the same source
        fichier_mode = os.path.join(dossier, "vitesse escadrille.txt")
        c = os.path.join(dossier, "harnais.c")
        s = os.path.join(dossier, "harnais.s")
        open(c, "w").write(HARNAIS_C)
        open(s, "w").write(HARNAIS_S)
        exe = os.path.join(dossier, "essai")
        r = subprocess.run(["clang", "-arch", "x86_64", "-O1", "-mno-red-zone", '-DCHEMIN="%s"' % fichier_mode,
                            "-o", exe, c, s, V.SOURCE], capture_output=True, text=True)
        verifier("test program compiled", r.returncode == 0, r.stderr.strip()[:400])
        if r.returncode:
            return
        r = subprocess.run(["arch", "-x86_64", exe, fichier_mode], capture_output=True, text=True, timeout=30)
        verifier("test program runs (x86_64 via Rosetta)", r.returncode == 0, r.stderr.strip())
        lignes = r.stdout.splitlines()
        lua = {l.split()[1]: l.split()[2] for l in lignes if l.startswith(("L ", "F "))}
        attendus = {"read_empty": "0", "set3": "3", "read": "3", "other_team": "3", "bad_mode": "3",
                    "zero_mode": "3", "team_16": "0", "team_neg": "0", "set1": "1", "contents": "1",
                    "restart": "1", "restart_other": "1"}
        for k, v in attendus.items():
            verifier("Lua: %s = %s" % (k, v), lua.get(k) == v, lua.get(k))
        plancher = [l.split()[1:] for l in lignes if l.startswith("P ")]
        verifier("floor: %d cases run" % len(plancher), len(plancher) == 5 * 3 * 2 * 4, len(plancher))
        faux = []
        for m, e, typ, v, c2c8, x0, x1, rax, rcx in plancher:
            m, e, typ, v = int(m), int(e), int(typ), float(v)
            att = attendu_plancher(m, e, typ, v)
            obtenu = (float(c2c8), float(x0), float(x1))
            if obtenu != att or rax != "1111111111111111" or rcx != "2222222222222222":
                faux.append((m, e, typ, v, obtenu, att, rax, rcx))
        verifier("floor: target speed, xmm0, xmm1, rax and rcx correct in all cases", not faux, faux[:3])
        exemples = {(int(p[0]), int(p[1]), int(p[2]), float(p[3])): float(p[4]) for p in plancher}
        print("     examples (target speed, tracked object at 0 m/s): Albatros ECO %g / NORMAL %g / FLANK %g;"
              " Manta ECO %g / NORMAL %g / FLANK %g; enemy at FLANK %g"
              % (exemples[(1, 0, 8, 0.0)], exemples[(2, 0, 8, 0.0)], exemples[(3, 0, 8, 0.0)],
                 exemples[(1, 0, 10, 0.0)], exemples[(2, 0, 10, 0.0)], exemples[(3, 0, 10, 0.0)],
                 exemples[(3, 1, 8, 0.0)]))


main()
print("\nRESULT: " + ("ALL PASSED" if ok else "THERE ARE FAILURES"))
sys.exit(0 if ok else 1)
