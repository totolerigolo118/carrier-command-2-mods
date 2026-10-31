#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste le module « ecriture_releve » (print() de Lua -> fichier) sans lancer le jeu.

1. Applique le module sur une COPIE du programme d'origine et relit chaque instruction ajoutee avec objdump.
2. Fait TOURNER la greffe (meme source assembleur, x86_64 via Rosetta) dans un petit programme d'essai qui
   imite luaB_print : pile alignee comme dans le jeu, case vide au depart, GOT de __stdoutp. Verifie que le
   fichier est ouvert une seule fois, que les deux points d'entree rendent l'adresse de la case, que le texte
   arrive dans le fichier, et que si le dossier n'existe pas tout part sur la sortie standard (comme avant).
"""
import hashlib, os, re, shutil, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
OUTIL = os.path.join(os.path.dirname(ICI), "outil")
sys.path.insert(0, OUTIL)
sys.path.insert(0, os.path.join(OUTIL, "generateurs"))
import patchs_cc2 as P
import generer_ecriture_releve as G

ok = True
def verifier(nom, condition, detail=""):
    global ok
    ok = ok and condition
    print("  %-62s %s %s" % (nom, "OK" if condition else "ECHEC", detail))


def instructions(chemin, debut, fin):
    sortie = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "--start-address=%#x" % debut,
                             "--stop-address=%#x" % fin, chemin], capture_output=True, text=True).stdout
    lignes = []
    for l in sortie.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+(.*)", l)
        if m:
            lignes.append((int(m.group(1), 16), re.sub(r"\s*<[^>]*>", "", m.group(2)).strip()))
    return lignes


HARNAIS = r"""
#include <stdio.h>
#include <string.h>
FILE *g_case;                          /* la case du jeu (0 au depart, comme en __bss) */
FILE **g_got_stdoutp = &__stdoutp;     /* l'entree de la GOT : contient &__stdoutp */
int nb_fopen;
FILE *g_fopen(const char *c, const char *m) { nb_fopen++; return fopen(c, m); }

/* comme dans luaB_print : rsp aligne sur 16 au moment du call */
static void *par_r12(void) {
    void *r;
    __asm__ volatile("movq %%rsp, %%r13\n\tandq $-16, %%rsp\n\tcall _rv_r12\n\tmovq %%r13, %%rsp\n\tmovq %%r12, %0"
                     : "=r"(r) : : "rax", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11", "r12", "r13", "memory", "cc");
    return r;
}
static void *par_rbx(void) {
    void *r;
    __asm__ volatile("movq %%rsp, %%r13\n\tandq $-16, %%rsp\n\tcall _rv_rbx\n\tmovq %%r13, %%rsp\n\tmovq %%rbx, %0"
                     : "=r"(r) : : "rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11", "r13", "memory", "cc");
    return r;
}
int main(void) {
    void *a = par_r12();
    FILE *f = *(FILE **)a;
    fwrite("CC2R1 E e=1 t=2", 1, 15, f);
    void *b = par_rbx();
    fwrite("\n", 1, 1, *(FILE **)b);
    fflush(*(FILE **)b);
    void *c = par_r12();
    fwrite("deuxieme\n", 1, 9, *(FILE **)c);
    fflush(*(FILE **)c);
    fprintf(stderr, "case=%d r12=%d rbx=%d encore=%d fopen=%d stdout=%d\n", g_case != 0, a == (void *)&g_case,
            b == (void *)&g_case, c == (void *)&g_case, nb_fopen, g_case == __stdoutp);
    return 0;
}
"""


def construire(dossier, chemin_releve, nom):
    asm = os.path.join(dossier, nom + ".s")
    open(asm, "w").write(open(G.SOURCE).read().replace("__CHEMIN__", chemin_releve))
    c = os.path.join(dossier, "harnais.c")
    open(c, "w").write(HARNAIS)
    exe = os.path.join(dossier, nom)
    r = subprocess.run(["clang", "-arch", "x86_64", "-O1", "-mno-red-zone", "-o", exe, c, asm], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("compilation du harnais : " + r.stderr)
    return exe


def lancer(exe):
    r = subprocess.run(["arch", "-x86_64", exe], capture_output=True, text=True, timeout=30)
    vals = dict(x.split("=") for x in r.stderr.split()) if r.returncode == 0 else {}
    return r, vals


print("\nTest du module ecriture_releve")
tmp = tempfile.mkdtemp(prefix="test_releve_cc2_")
try:
    # 1. sur une copie du programme
    import importlib.util
    spec = importlib.util.spec_from_file_location("m", os.path.join(OUTIL, "modules", "ecriture_releve.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    prog = os.path.join(tmp, "build_mac")
    shutil.copyfile(os.path.join(os.path.dirname(OUTIL), "sauvegarde", "build_mac_origine"), prog)
    d = bytearray(open(prog, "rb").read())
    verifier("copie = programme d'origine", hashlib.md5(d).hexdigest() == G.MD5_ORIGINE)
    for _, va, avant, apres in m.RETOUCHES:
        o = va - P.BASE
        assert d[o:o + len(avant) // 2].hex() == avant
        d[o:o + len(apres) // 2] = bytes.fromhex(apres)
    open(prog, "wb").write(d)
    zone = instructions(prog, 0x100061a00, 0x100061a50)
    texte = [i for _, i in zone]
    # chaque instruction : morceaux attendus (la cible des acces relatifs est lue dans le commentaire « ## »)
    attendu = [
        ("callq\t0x100061a1a",), ("leaq", "%r12", "## 0x102a2a828"), ("retq",),
        ("callq\t0x100061a1a",), ("leaq", "%rbx", "## 0x102a2a828"), ("retq",),
        ("movq", "%rax", "## 0x102a2a828"), ("testq\t%rax, %rax",), ("jne\t0x100061a4f",),
        ("leaq", "%rdi", "## 0x100061a50"), ("leaq", "%rsi", "## 0x100061aa3"), ("callq\t0x102867e78",),
        ("testq\t%rax, %rax",), ("jne\t0x100061a48",), ("movq", "%rax", "## 0x10299dff0"), ("movq\t(%rax), %rax",),
        ("movq\t%rax,", "## 0x102a2a828"), ("retq",),
    ]
    verifier("greffe : les 18 instructions, une par une", len(texte) == len(attendu)
             and all(all(x in i for x in a) for i, a in zip(texte, attendu)), str(texte))
    verifier("greffe : chemin a 0x100061a50, mode « a » a 0x100061aa3",
             bytes(d[0x100061a50 - P.BASE:0x100061aa5 - P.BASE]) == G.CHEMIN_RELEVE.encode() + b"\0a\0")
    brut = subprocess.run(["objdump", "-d", "--start-address=0x100061a00", "--stop-address=0x100061a53", prog],
                          capture_output=True, text=True).stdout
    for cible, quoi in ((0x102a2a828, "la case (guard variable de la demo ImGui)"), (0x10299dff0, "la GOT de __stdoutp"),
                        (0x102867e78, "fopen")):
        verifier("greffe : vise %s" % quoi, ("%x" % cible) in brut)
    o = 0x100061a00 - P.BASE
    verifier("greffe : chemin du fichier + mode « a »", (G.CHEMIN_RELEVE.encode() + b"\0a\0") in bytes(d[o:o + 0x180]))
    verifier("greffe : tient avant helicos_pres_ascenseur (0x100061b80)", 0x100061a00 + len(bytes.fromhex(m.RETOUCHES[0][3])) <= 0x100061b80)
    for va, appel in ((0x10283aed0, "callq\t0x100061a00"), (0x10283af78, "callq\t0x100061a0d")):
        site = instructions(prog, va, va + 16)
        verifier("luaB_print %#x : %s puis nop" % (va, appel.replace("\t", " ")),
                 site[0][1] == appel and site[1][1].startswith("nop") and site[2][0] == va + 7, str(site[:3]))

    # 2. la greffe qui tourne
    fichier = os.path.join(tmp, "releve_cc2.txt")
    open(fichier, "w").write("ligne d'avant\n")
    r, v = lancer(construire(tmp, fichier, "essai"))
    verifier("le programme d'essai tourne (x86_64 via Rosetta)", r.returncode == 0, r.stderr.strip())
    verifier("la case recoit un fichier ouvert (pas stdout)", v.get("case") == "1" and v.get("stdout") == "0", str(v))
    verifier("_rv_r12 et _rv_rbx rendent l'adresse de la case", v.get("r12") == "1" and v.get("rbx") == "1" and v.get("encore") == "1")
    verifier("fichier ouvert une seule fois pour 3 print()", v.get("fopen") == "1")
    verifier("texte ajoute a la fin du fichier (mode « a »)",
             open(fichier).read() == "ligne d'avant\nCC2R1 E e=1 t=2\ndeuxieme\n", repr(open(fichier).read()))
    r, v = lancer(construire(tmp, os.path.join(tmp, "dossier_absent", "releve.txt"), "secours"))
    verifier("dossier absent : retour a la sortie standard, comme avant",
             r.returncode == 0 and v.get("stdout") == "1" and "CC2R1 E e=1 t=2" in r.stdout, str(v))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\nRESULTAT : " + ("TOUT EST BON" if ok else "IL Y A DES ECHECS"))
sys.exit(0 if ok else 1)
