#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste le module grue_annulation (annuler la sortie d'un avion deja pris par la grue) sur des COPIES.

1. logique : essai_grue_annulation.c (le vrai code de la greffe sur un faux gestionnaire d'avions),
   compile en x86_64 et execute via Rosetta : cas acceptes, cas refuses, fin du retour, deroule complet ;
2. programme : chargement avec tous les modules de l'atelier (aucun chevauchement), activation seule (md5
   annonce), relecture par objdump des 2 branchements et de TOUT le code ajoute (chaque appel ou saut va
   dans la greffe ou vers une adresse du jeu prevue, chaque constante lue est dans la greffe, les
   instructions remplacees sont rejouees), puis avec les modules du jeu et retour a l'origine a l'octet pres.
Le jeu n'est jamais touche. A lancer apres chaque generation :  python3 tests/test_grue_annulation.py
"""
import hashlib, importlib.util, os, re, shutil, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, os.path.join(RACINE, "outil"))
sys.path.insert(0, os.path.join(RACINE, "outil", "generateurs"))
import patchs_cc2 as P
import generer_grue_annulation as GA

ok = True
def verifier(nom, condition, detail=""):
    global ok
    ok = ok and condition
    print("  %-70s %s %s" % (nom, "OK" if condition else "ECHEC", detail))


def md5(chemin):
    return hashlib.md5(open(chemin, "rb").read()).hexdigest()


def desassembler(chemin, debut, fin):
    sortie = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "--start-address=%#x" % debut,
                             "--stop-address=%#x" % fin, chemin], capture_output=True, text=True).stdout
    lignes = []
    for l in sortie.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+(.*)", l)
        if m:
            lignes.append((int(m.group(1), 16), re.sub(r"\s*<[^>]*>", "", m.group(2).strip())))
    return lignes


def charger(chemin):
    spec = importlib.util.spec_from_file_location("m", chemin)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


DEBUT_A = ["cmpl\t$0x7, 0x220(%r14)", "jne", "movl\t%ebx, 0x28(%rdi)", "jmp\t0x1001a8c0e",
           "movq\t%r14, %rsi", "movq\t%rcx, %rdx", "callq", "jmp\t0x1001a8c0e"]
FIN_B = ["popq\t%rax", "cmpl\t$0x0, 0x18(%r14)", "jmp\t0x1001ad9b2"]
# modules « programme » actifs dans le jeu le 25/10 (les modules « fichier » ne changent pas le programme)
MODULES_JEU = ("ascenseur_x2", "atterrissage", "ecriture_releve", "helicos_approche_x2", "helicos_pres_ascenseur")
MD5_JEU_25_10 = "afc9e2d87a7f3c0c617162da6957c1a4"

tmp = tempfile.mkdtemp(prefix="test_grue_cc2_")
try:
    print("Logique de la greffe (faux gestionnaire, x86_64 via Rosetta)")
    essai = os.path.join(tmp, "essai")
    r = subprocess.run(["clang", "-arch", "x86_64", "-O1", "-Wall", "-Wextra", "-Werror", "-o", essai,
                        os.path.join(ICI, "essai_grue_annulation.c")], capture_output=True, text=True)
    verifier("compilation de l'essai", r.returncode == 0, r.stderr.strip()[:200])
    if r.returncode == 0:
        r = subprocess.run([essai], capture_output=True, text=True)
        for l in r.stdout.splitlines():
            print("    " + l)
        verifier("essai de la logique : tout est bon", r.returncode == 0 and "RESULTAT LOGIQUE : tout est bon" in r.stdout)

    print("\nProgramme (copie)")
    origine = os.path.join(RACINE, "sauvegarde", "build_mac_origine")
    verifier("programme d'origine reconstruit", md5(origine) == P.MD5_ORIGINE)
    rom = os.path.join(tmp, "rom_0")
    os.makedirs(os.path.join(rom, "scripts"))
    dossier = os.path.join(tmp, "modules")
    shutil.copytree(P.MODULES, dossier, ignore=shutil.ignore_patterns("__pycache__"))
    module = charger(os.path.join(dossier, "grue_annulation.py"))
    md5_annonce = re.search(r"md5 du programme avec ce module seul : ([0-9a-f]+)",
                            open(os.path.join(dossier, "grue_annulation.py")).read()).group(1)
    prog = os.path.join(tmp, "build_mac")
    shutil.copyfile(origine, prog)
    sauv, sauv_rom = os.path.join(tmp, "sauv", "build_mac_origine"), os.path.join(tmp, "sauv", "rom_0")
    try:
        a = P.Atelier(prog, rom, dossier, sauv, sauv_rom)
        verifier("charge avec tous les modules de l'atelier (aucun chevauchement)", True, "%d modules" % len(a.modules))
    except P.Refus as e:
        verifier("charge avec tous les modules de l'atelier (aucun chevauchement)", False, str(e))
        raise SystemExit
    a.appliquer({"grue_annulation": True})
    verifier("active seul : md5 annonce", md5(prog) == md5_annonce, md5(prog))
    avant, apres = open(origine, "rb").read(), open(prog, "rb").read()
    ecarts = [i for i, (x, y) in enumerate(zip(avant, apres)) if x != y]
    zones = [(va - P.BASE, len(av) // 2) for _, va, av, _ in module.RETOUCHES]
    verifier("octets changes uniquement dans la greffe et les 2 branchements",
             len(avant) == len(apres) and all(any(o <= i < o + n for o, n in zones) for i in ecarts),
             "%d octets" % len(ecarts))

    greffe = module.RETOUCHES[0]
    debut, taille = greffe[1], len(greffe[3]) // 2
    verifier("greffe dans ImGui::ShowDemoWindow, a sa place", debut == GA.ZONE and taille <= GA.ZONE_TAILLE
             and 0x10005af39 <= debut and debut + taille <= 0x100061c00, "%#x + %d octets" % (debut, taille))
    autres = [(m, r_[1], len(r_[3]) // 2) for m in os.listdir(os.path.join(RACINE, "outil", "modules_en_reserve"))
              if m.endswith(".py") for r_ in charger(os.path.join(RACINE, "outil", "modules_en_reserve", m)).RETOUCHES
              if r_[0] == "imm"]
    croise = [m for m, va, n in autres if va < debut + taille and debut < va + n]
    verifier("aucun module en reserve sur les memes octets", not croise, ", ".join(croise))

    points = {}
    for va, attendu, point, _ in GA.BRANCHEMENTS:
        n = len(attendu) // 2
        l = desassembler(prog, va, va + n)
        m = re.match(r"jmp\s+0x([0-9a-f]+)", l[0][1]) if l else None
        points[point] = int(m.group(1), 16) if m else None
        verifier("branchement %#x -> %s" % (va, point), m is not None and debut <= points[point] < debut + taille
                 and all(t == "nop" for _, t in l[1:]) and l[-1][0] < va + n, l[0][1] if l else "")
    # le code proprement dit (__text) ; apres lui, les constantes de la greffe (a ne pas lire comme du code)
    with tempfile.TemporaryDirectory(prefix="objet_grue_") as d_:
        objet = os.path.join(d_, "g.o")
        subprocess.run(["clang"] + GA.G.DRAPEAUX + ["-o", objet, GA.SOURCE], check=True)
        texte_taille = next(s["size"] for s in GA.G.lire_objet(open(objet, "rb").read())[0] if s["nom"] == "__text")
    code = desassembler(prog, debut, debut + texte_taille)
    verifier("le code se termine par un retour ou un saut", code and code[-1][1].split("\t")[0] in ("retq", "jmp"),
             code[-1][1] if code else "")
    def suite(adresse, n):
        idx = [i for i, (a_, _) in enumerate(code) if a_ == adresse]
        return [t for _, t in code[idx[0]:idx[0] + n]] if idx else []
    sa = suite(points["_ag_a"], 8)
    verifier("A rejoue l'original (attente au lancement) puis appelle ag_annuler",
             len(sa) == 8 and all(t.startswith(p) for t, p in zip(sa, DEBUT_A)), " | ".join(sa))
    ib = [i for i, (a_, _) in enumerate(code) if a_ == points["_ag_b"]][0]
    sb = [t for _, t in code[ib:ib + 60]]
    kb = next((j for j in range(len(sb)) if sb[j] == "cmpl\t$0x0, 0x18(%r14)"), None)
    verifier("B sauvegarde/restaure tout, rejoue cmpl $0,0x18(%r14), revient a 0x1001ad9b2",
             kb is not None and sb[kb - 1:kb + 2] == FIN_B and sb.count("pushq\t%rax") == 1
             and sum(1 for t in sb[:kb] if t.startswith("movdqu\t%xmm")) == 16
             and sum(1 for t in sb[:kb] if t.startswith("movdqu\t") and t.endswith(tuple("%%xmm%d" % k for k in range(16)))) == 16
             and "movq\t-0x38(%rbp), %rsi" in sb[:kb] and "movq\t%r14, %rdi" in sb[:kb])

    prevues = set(GA.JEU.values())
    dehors, appels = [], {}
    for adr, texte in code:
        m = re.match(r"(callq|jmp|j[a-z]+)\s+0x([0-9a-f]+)", texte)
        if m:
            cible = int(m.group(2), 16)
            if not debut <= cible < debut + taille:
                if cible not in prevues:
                    dehors.append("%#x -> %#x" % (adr, cible))
                appels[cible] = appels.get(cible, 0) + 1
        m = re.search(r"## 0x([0-9a-f]+)", texte)
        if m and not debut <= int(m.group(1), 16) < debut + taille:
            dehors.append("%#x lit %#x" % (adr, int(m.group(1), 16)))
        if texte.startswith(("callq\t*", "jmpq\t*")) and not re.match(r"(callq|jmpq)\s+\*\(%r[a-z0-9]+\)$", texte):
            dehors.append("%#x appel indirect inattendu : %s" % (adr, texte))
    verifier("chaque appel/saut/constante va la ou prevu", not dehors, "; ".join(dehors[:5]))
    indirects = [t for _, t in code if t.startswith(("callq\t*", "jmpq\t*"))]
    verifier("un seul appel indirect (la carte, fonction virtuelle n° 0)", len(indirects) == 1, " | ".join(indirects))
    noms = {0x10019a450: "push_back du geste", 0x10009060c: "efface la route", 0x10010cea4: "reset_waypoint_path",
            0x1001a8c0e: "retour A", 0x1001ad9b2: "retour B"}
    for cible in sorted(appels):
        print("      va vers %#x %s (x%d)" % (cible, noms.get(cible, "?"), appels[cible]))

    a.appliquer({n: True for n in MODULES_JEU})
    e = a.etats()
    verifier("avec les 5 modules programme du jeu : les 6 actifs", all(e[n] == "actif" for n in MODULES_JEU + ("grue_annulation",)), str(e))
    if "pont_retour_x2" in e:
        a.appliquer({"pont_retour_x2": True})
        verifier("  + pont_retour_x2 : les 7 actifs", set(a.etats()[n] for n in MODULES_JEU + ("grue_annulation", "pont_retour_x2")) == {"actif"})
        print("      md5 avec les 7 : %s" % md5(prog))
        a.appliquer({"pont_retour_x2": False})
    print("      md5 jeu du 25/10 + grue_annulation : %s" % md5(prog))
    a.appliquer({"grue_annulation": False})
    verifier("retirer grue_annulation : exactement le programme du jeu du 25/10", md5(prog) == MD5_JEU_25_10, md5(prog))
    a.appliquer({n: False for n, v in a.etats().items() if v == "actif"})
    verifier("tout retire : programme d'origine a l'octet pres", md5(prog) == P.MD5_ORIGINE)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\nRESULTAT : %s" % ("tout est bon" if ok else "IL Y A DES ECHECS"))
sys.exit(0 if ok else 1)
