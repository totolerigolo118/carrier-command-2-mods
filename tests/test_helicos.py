#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste les modules « helicos sur l'ascenseur » (temoin et normal) sur des COPIES du programme.

Pour chaque version : chargement avec les autres modules programme (aucun chevauchement), activation
seule (md5 annonce par le module), relecture par objdump des 3 branchements et de TOUT le code ajoute
(chaque appel ou saut doit aller dans la greffe ou vers une fonction du jeu prevue, chaque constante lue
doit etre dans la greffe ou une donnee du jeu prevue), puis aller-retour avec ascenseur_x2 + atterrissage
et retour a l'origine a l'octet pres. Le jeu n'est jamais touche.
A lancer apres chaque generation :  python3 tests/test_helicos.py
"""
import hashlib, importlib.util, os, re, shutil, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, os.path.join(RACINE, "outil"))
sys.path.insert(0, os.path.join(RACINE, "outil", "generateurs"))
import patchs_cc2 as P
import generer_helicos_ascenseur as G

ok = True
def verifier(nom, condition, detail=""):
    global ok
    ok = ok and condition
    print("  %-66s %s %s" % (nom, "OK" if condition else "ECHEC", detail))


def md5(chemin):
    return hashlib.md5(open(chemin, "rb").read()).hexdigest()


def desassembler(chemin, debut, fin):
    sortie = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "--start-address=%#x" % debut,
                             "--stop-address=%#x" % fin, chemin], capture_output=True, text=True).stdout
    lignes = []
    for l in sortie.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+(.*)", l)
        if m:
            lignes.append((int(m.group(1), 16), m.group(2).strip()))
    return lignes


def charger(chemin):
    spec = importlib.util.spec_from_file_location("m", chemin)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ATTENDU_H1 = ["movq\t%r13, -0x70(%rbp)", "pushq\t%rax"]
FIN_H1 = ["cmpl\t$-0x1, 0x80(%r14)", "movq\t%r14, %rax", "jne\t0x1001ace50", "jmp\t0x1001acda9"]
ATTENDU_H2 = ["cmpl\t$-0x1, 0x84(%r14)", "jne\t0x1001ae787", "jmp\t0x1001ae780"]
ATTENDU_H3 = ["cmpl\t$-0x1, 0x7c(%r14)", "jne\t0x1001ae07c", "cmpl\t$-0x1, 0x84(%r14)", "je\t0x1001b151b",
              "cmpb\t$-0x5b, 0x9f(%r14)", "jne\t0x1001b151b", "testb\t$-0x80, 0x9e(%r14)", "jne\t0x1001ae07c",
              "jmp\t0x1001b151b"]

tmp = tempfile.mkdtemp(prefix="test_helicos_cc2_")
try:
    origine = os.path.join(RACINE, "sauvegarde", "build_mac_origine")
    verifier("programme d'origine reconstruit", md5(origine) == P.MD5_ORIGINE)
    rom = os.path.join(tmp, "rom_0")
    os.makedirs(rom)
    autres = ["ascenseur_x2.py", "atterrissage.py"]
    md5_autres = None
    for nom in ("helicos_temoin", "helicos_ascenseur"):
        print("\n%s" % nom)
        dossier = os.path.join(tmp, "modules_" + nom)
        os.makedirs(dossier)
        for f in autres:
            shutil.copyfile(os.path.join(RACINE, "outil", "modules", f), os.path.join(dossier, f))
        shutil.copyfile(os.path.join(RACINE, "outil", "modules_en_reserve", nom + ".py"), os.path.join(dossier, nom + ".py"))
        module = charger(os.path.join(dossier, nom + ".py"))
        md5_annonce = re.search(r"md5 du programme avec ce module seul : ([0-9a-f]+)",
                                open(os.path.join(dossier, nom + ".py")).read()).group(1)
        prog = os.path.join(tmp, "build_mac_" + nom)
        shutil.copyfile(origine, prog)
        sauv, sauv_rom = os.path.join(tmp, "sauv_" + nom, "build_mac_origine"), os.path.join(tmp, "sauv_" + nom, "rom_0")
        try:
            a = P.Atelier(prog, rom, dossier, sauv, sauv_rom)
            verifier("charge avec ascenseur_x2 + atterrissage (aucun chevauchement)", True)
        except P.Refus as e:
            verifier("charge avec ascenseur_x2 + atterrissage (aucun chevauchement)", False, str(e))
            continue
        a.appliquer({nom: True})
        verifier("active seul : md5 annonce", md5(prog) == md5_annonce, md5(prog))

        greffe = module.RETOUCHES[0]
        debut, taille = greffe[1], len(greffe[3]) // 2
        verifier("greffe dans ImGui::ShowDemoWindow", G.ZONE_DEBUT <= debut and debut + taille <= G.ZONE_FIN,
                 "%#x + %d octets" % (debut, taille))

        points = {}
        for va, attendu, point, _ in G.BRANCHEMENTS:
            l = desassembler(prog, va, va + 5)
            m = re.match(r"jmp\s+0x([0-9a-f]+)", l[0][1]) if l else None
            points[point] = int(m.group(1), 16) if m else None
            verifier("branchement %#x -> %s" % (va, point), m is not None and debut <= points[point] < debut + taille,
                     l[0][1] if l else "")

        code = desassembler(prog, debut, debut + taille)
        par_adresse = dict(code)
        def suite(adresse, n):
            idx = [i for i, (a_, _) in enumerate(code) if a_ == adresse]
            return [re.sub(r"\s*<[^>]*>", "", t) for _, t in code[idx[0]:idx[0] + n]] if idx else []
        verifier("H1 commence par les instructions du jeu remplacees", suite(points["_hl_h1"], 2) == ATTENDU_H1)
        i1 = [i for i, (a_, _) in enumerate(code) if a_ == points["_hl_h1"]][0]
        fin1 = [re.sub(r"\s*<[^>]*>", "", t) for _, t in code[i1:i1 + 120]]
        k = next((j for j in range(len(fin1)) if fin1[j] == FIN_H1[0]), None)
        verifier("H1 rend la main au jeu comme a l'origine", k is not None and fin1[k:k + 4] == FIN_H1)
        verifier("H1 sauvegarde puis restaure les registres",
                 fin1.count("pushq\t%rax") == 1 and fin1.count("popq\t%rax") == 1 and
                 sum(1 for t in fin1 if t.startswith("movdqu\t%xmm")) == 16 and
                 sum(1 for t in fin1 if t.startswith("movdqu\t") and t.endswith(("%xmm0", "%xmm15"))) == 2)
        verifier("H2 identique au plan", suite(points["_hl_h2"], 3) == ATTENDU_H2)
        verifier("H3 identique au plan", suite(points["_hl_h3"], 9) == ATTENDU_H3)

        # tous les appels et sauts : dans la greffe ou vers les adresses du jeu prevues
        prevues = set(G.JEU.values())
        dehors, noms = [], {}
        for adr, texte in code:
            m = re.match(r"(callq|jmp|j[a-z]+)\s+0x([0-9a-f]+)(?:\s+<(.*)>)?", texte)
            if m:
                cible = int(m.group(2), 16)
                if not (debut <= cible < debut + taille):
                    if cible not in prevues:
                        dehors.append("%#x -> %#x" % (adr, cible))
                    noms[cible] = (m.group(3) or "").split("(")[0]
            m = re.search(r"## 0x([0-9a-f]+)", texte)
            if m:
                cible = int(m.group(1), 16)
                if not (debut <= cible < debut + taille) and cible not in prevues:
                    dehors.append("%#x lit %#x" % (adr, cible))
            if texte.startswith("callq\t*") or texte.startswith("jmpq\t*"):
                if not re.match(r"(callq|jmpq)\s+\*0x[0-9a-f]+\(%r[a-z0-9]+\)$", texte):
                    dehors.append("%#x appel indirect inattendu : %s" % (adr, texte))
        verifier("chaque appel/saut/constante va la ou prevu", not dehors, "; ".join(dehors[:5]))
        if nom == "helicos_ascenseur":
            for cible in sorted(noms):
                print("      appelle %#x %s" % (cible, noms[cible]))

        # aller-retour avec les autres modules
        a.appliquer({"ascenseur_x2": True, "atterrissage": True})
        verifier("les trois actifs", a.etats() == {"ascenseur_x2": "actif", "atterrissage": "actif", nom: "actif"})
        a.appliquer({nom: False})
        m_autres = md5(prog)
        verifier("retire : reste ascenseur_x2 + atterrissage (md5 139a62c2...)", m_autres.startswith("139a62c2"), m_autres)
        a.appliquer({"ascenseur_x2": False, "atterrissage": False})
        verifier("tout retire : programme d'origine a l'octet pres", md5(prog) == P.MD5_ORIGINE)

    # approche x2 : avec tous les autres modules programme, dont la voie ascenseur
    print("\nhelicos_approche_x2")
    dossier = os.path.join(tmp, "modules_approche")
    os.makedirs(dossier)
    for f in autres:
        shutil.copyfile(os.path.join(RACINE, "outil", "modules", f), os.path.join(dossier, f))
    for f in ("helicos_ascenseur.py", "helicos_approche_x2.py"):
        shutil.copyfile(os.path.join(RACINE, "outil", "modules_en_reserve", f), os.path.join(dossier, f))
    prog = os.path.join(tmp, "build_mac_approche")
    shutil.copyfile(origine, prog)
    try:
        a = P.Atelier(prog, rom, dossier, os.path.join(tmp, "sauv_a", "b"), os.path.join(tmp, "sauv_a", "r"))
        verifier("charge avec les 3 autres modules programme (aucun chevauchement)", True)
        a.appliquer({"helicos_approche_x2": True})
        l = desassembler(prog, 0x1001ad3ef, 0x1001ad3f7)
        verifier("0x1001ad3ef lit 100.0 (0x1028697ac) au lieu de 50.0", l and "## 0x1028697ac" in l[0][1], l[0][1] if l else "")
        a.appliquer({"helicos_ascenseur": True, "ascenseur_x2": True, "atterrissage": True})
        verifier("les quatre actifs ensemble", set(a.etats().values()) == {"actif"})
        a.appliquer({n: False for n in a.etats()})
        verifier("tout retire : programme d'origine a l'octet pres", md5(prog) == P.MD5_ORIGINE)
    except P.Refus as e:
        verifier("approche x2 avec les autres modules", False, str(e))

    # toucher pres de l'ascenseur : avec ascenseur_x2, atterrissage et approche x2 (la combinaison a tester)
    print("\nhelicos_pres_ascenseur")
    dossier = os.path.join(tmp, "modules_pres")
    os.makedirs(dossier)
    for f in autres:
        shutil.copyfile(os.path.join(RACINE, "outil", "modules", f), os.path.join(dossier, f))
    for f in ("helicos_approche_x2.py", "helicos_pres_ascenseur.py"):
        shutil.copyfile(os.path.join(RACINE, "outil", "modules_en_reserve", f), os.path.join(dossier, f))
    prog = os.path.join(tmp, "build_mac_pres")
    shutil.copyfile(origine, prog)
    try:
        a = P.Atelier(prog, rom, dossier, os.path.join(tmp, "sauv_p", "b"), os.path.join(tmp, "sauv_p", "r"))
        verifier("charge avec ascenseur_x2, atterrissage, approche x2", True)
        a.appliquer({"helicos_pres_ascenseur": True})
        def lu(va):
            l = desassembler(prog, va, va + 8)
            return re.sub(r"\s*<[^>]*>", "", l[0][1]) if l else ""
        verifier("0x1001ad3fc lit 48.0 (point vise z = -20)", "## 0x102869af0" in lu(0x1001ad3fc), lu(0x1001ad3fc))
        verifier("0x1001b1066 lit 70.0 (train a z > -63)", "## 0x1028698a0" in lu(0x1001b1066), lu(0x1001b1066))
        saut = lu(0x1001ad57a)
        verifier("0x1001ad57a saute vers la greffe", saut.startswith("jmp\t0x100061b8"), saut)
        cible = int(saut.split("0x")[1], 16)
        g = [re.sub(r"\s*<[^>]*>", "", t) for _, t in desassembler(prog, cible, cible + 24)][:3]
        verifier("greffe : subss, maxss -2.0, retour 0x1001ad582",
                 len(g) == 3 and g[0].startswith("subss\t") and "## 0x102869850" in g[1] and g[2] == "jmp\t0x1001ad582", " | ".join(g))
        donnees = open(prog, "rb").read()
        disp = int.from_bytes(donnees[cible - 0x100000000 + 4:cible - 0x100000000 + 8], "little", signed=True)
        valeur = struct.unpack("<f", donnees[cible + 8 + disp - 0x100000000:cible + 12 + disp - 0x100000000])[0]
        verifier("decalage lu par subss = 23.5 m (toucher a z = -40)", valeur == 23.5, repr(valeur))
        a.appliquer({"helicos_approche_x2": True, "ascenseur_x2": True, "atterrissage": True})
        verifier("les quatre actifs ensemble", set(a.etats().values()) == {"actif"})
        print("      md5 avec les quatre : %s" % md5(prog))
        a.appliquer({n: False for n in a.etats()})
        verifier("tout retire : programme d'origine a l'octet pres", md5(prog) == P.MD5_ORIGINE)
    except P.Refus as e:
        verifier("toucher pres de l'ascenseur avec les autres modules", False, str(e))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\nRESULTAT : %s" % ("tout est bon" if ok else "IL Y A DES ECHECS"))
sys.exit(0 if ok else 1)
