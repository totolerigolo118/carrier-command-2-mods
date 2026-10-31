#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste l'atelier de patchs sur des COPIES (le jeu n'est jamais touche).

Copie le programme du jeu et un faux rom_0 dans un dossier temporaire, puis verifie :
activation/retrait de chaque module, md5 attendus, retour a l'origine a l'octet pres,
et les refus (module abime, programme inconnu, chevauchement, fichier etranger).
A lancer apres chaque ajout de module :  python3 tests/test_patchs.py
"""
import hashlib, os, re, shutil, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(ICI), "outil"))
import patchs_cc2 as P

MD5_ASCENSEUR = "828ce81e69e5f8facd354d4074fe9c21"   # programme avec ascenseur_x2, valide en jeu le 23/10
MD5_ATTERRISSAGE = "073338c450fa11fce9c2dc5ff14835e6"   # programme avec atterrissage seul (reglage B), relu par objdump
MD5_ASCENSEUR_ATTERRISSAGE = "139a62c29069abc1f6fabd108bb4bf0d"   # les deux, active dans le jeu le 23/10
MD5_ECRITURE_RELEVE = "8655d7175105c0fe4e488f4e36b0075f"   # programme avec ecriture_releve seul (24/10)
MD5_PONT_RETOUR = "96d568f1039c7154f1d30316471dbdd7"   # programme avec pont_retour_x2 seul (calcule a part le 25/10)
MD5_JEU_25_10 = "afc9e2d87a7f3c0c617162da6957c1a4"   # programme du jeu le 25/10 (9 modules, sans pont_retour_x2)
MD5_JEU_PONT_RETOUR = "33716ba894fb5943540ada9f3b0ca44f"   # le meme + pont_retour_x2 (calcule a part le 25/10)
MD5_GRUE_ANNULATION = "773c3319c984cb13567377935a9902e5"   # programme avec grue_annulation seul (25/10)
MD5_JEU_GRUE_ANNULATION = "6fcfd65efc5431ad0372eefce4ab68a4"   # jeu du 25/10 (9 modules) + grue_annulation
MD5_CCTV_NET = "18e12e1858eb7106550f0e489ddad661"   # programme avec cctv_net seul (25/10)
MD5_JEU_CCTV_NET = "2791122bfa60a5c71287c1dd7490790c"   # jeu du 25/10 (9 modules) + cctv_net (calcule a part)
MD5_VITESSE_ESCADRILLE = "f03c977f864734496de2c29304bfc0ab"   # programme avec vitesse_escadrille seul (25/10)
MODULES_JEU_25_10 = ("ascenseur_x2", "atterrissage", "ecriture_releve", "effet_tele", "helicos_approche_x2",
                     "helicos_pres_ascenseur", "horloge", "journal", "releve")

# reglage B : ce que chaque instruction retouchee doit devenir, relu par objdump sur la copie
DECODAGE_B = [
    (0x1001af900, "jbe\t0x1001af914"), (0x1001af85b, "jbe\t0x1001af914"), (0x1001af867, "jmp\t0x1001af914"),
    (0x1001af785, "## 0x10286b920"), (0x1001af7d4, "## 0x10286b930"),
    (0x1001afa98, "## 0x10286b920"), (0x1001afae7, "## 0x10286b930"),
    (0x1001af870, "## 0x102869adc"), (0x1001afaf2, "## 0x102869adc"),
    (0x1001af87b, "subss\t%xmm1, %xmm0"),
]

ok = True
def verifier(nom, condition, detail=""):
    global ok
    ok = ok and condition
    print("  %-60s %s %s" % (nom, "OK" if condition else "ECHEC", detail))


def md5(chemin):
    return hashlib.md5(open(chemin, "rb").read()).hexdigest()


def decoder(chemin, va):
    """Premiere instruction a l'adresse va, telle que objdump la lit dans le fichier."""
    sortie = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "--start-address=%#x" % va,
                             "--stop-address=%#x" % (va + 16), chemin], capture_output=True, text=True).stdout
    for ligne in sortie.splitlines():
        if ligne.strip().startswith("%x:" % va):
            return re.sub(r" <[^>]*>", "", ligne.split(":", 1)[1].strip())
    return ""


def refuse(fn):
    try:
        fn()
    except P.Refus as e:
        return str(e)
    return None


tmp = tempfile.mkdtemp(prefix="test_patchs_cc2_")
try:
    prog = os.path.join(tmp, "build_mac")
    shutil.copyfile(P.PROGRAMME, prog)
    rom = os.path.join(tmp, "rom_0")
    os.makedirs(os.path.join(rom, "scripts"))
    open(os.path.join(rom, "scripts", "library_custom_1.lua"), "wb").close()
    open(os.path.join(rom, "scripts", "library_custom_4.lua"), "wb").close()
    open(os.path.join(rom, "scripts", "library_custom_5.lua"), "wb").close()
    open(os.path.join(rom, "scripts", "library_custom_6.lua"), "wb").close()
    os.makedirs(os.path.join(rom, "shaders"))
    shader_jeu = os.path.join(P.ROM, "shaders", "screen_crt_hud.glsl")
    sauv_shader = os.path.join(P.SAUVEGARDE_ROM, "shaders", "screen_crt_hud.glsl")
    # le jeu peut avoir l'effet deja installe : on repart de l'original (copie de secours si besoin)
    import hashlib as _h
    origine_shader = open(shader_jeu, "rb").read()
    if _h.sha256(origine_shader).hexdigest() != "ceadab0a21459350b0e75a3467fafd98ab7efb8eade5aaa1eec1458db83775f8":
        origine_shader = open(sauv_shader, "rb").read()
    open(os.path.join(rom, "shaders", "screen_crt_hud.glsl"), "wb").write(origine_shader)
    sauv, sauv_rom = os.path.join(tmp, "sauv", "build_mac_origine"), os.path.join(tmp, "sauv", "rom_0")

    def atelier(modules=P.MODULES):
        return P.Atelier(prog, rom, modules, sauv, sauv_rom)

    # le programme du jeu peut etre actuellement patche : on repart toujours de l'original reconstruit
    a = atelier()
    verifier("programme reconnu (version analysee)", a.programme_reconnu())
    open(prog, "wb").write(a.original_reconstruit())
    verifier("copie remise d'origine", md5(prog) == P.MD5_ORIGINE)

    print("\nModules :", ", ".join(atelier().modules))
    e = atelier().etats()
    verifier("au depart : tout est retire", all(v == "retire" for v in e.values()), str(e))

    faits = atelier().appliquer({"ascenseur_x2": True})
    verifier("activer ascenseur_x2", faits == ["ascenseur_x2"])
    verifier("  md5 = celui valide en jeu", md5(prog) == MD5_ASCENSEUR, md5(prog))
    verifier("  copie de secours = original", md5(sauv) == P.MD5_ORIGINE)
    verifier("  reactiver : rien a faire", atelier().appliquer({"ascenseur_x2": True}) == [])

    atelier().appliquer({"horloge": True, "journal": True})
    journal = open(os.path.join(rom, "scripts", "library_custom_4.lua"), "rb").read()
    verifier("activer journal : fichier = notre source", journal == open(os.path.join(P.FICHIERS, "journal", "library_custom_4.lua"), "rb").read())
    lua = open(os.path.join(rom, "scripts", "library_custom_1.lua"), "rb").read()
    verifier("activer horloge : fichier = notre source", lua == open(os.path.join(P.FICHIERS, "horloge", "library_custom_1.lua"), "rb").read())
    e2 = atelier().etats()
    verifier("  les deux actifs ensemble", e2["ascenseur_x2"] == "actif" and e2["horloge"] == "actif")

    atelier().appliquer({"effet_tele": True})
    shader = open(os.path.join(rom, "shaders", "screen_crt_hud.glsl"), "rb").read()
    verifier("activer effet_tele : effet remplace par notre version",
             shader == open(os.path.join(P.FICHIERS, "effet_tele", "screen_crt_hud.glsl"), "rb").read())
    e3 = atelier().etats()
    verifier("  trois modules actifs ensemble", all(e3[n] == "actif" for n in ("ascenseur_x2", "horloge", "effet_tele")), str(e3))

    atelier().appliquer({"ascenseur_x2": False})
    verifier("retirer ascenseur_x2 : original a l'octet pres", md5(prog) == P.MD5_ORIGINE)
    verifier("  l'horloge reste active", atelier().etats()["horloge"] == "actif")
    atelier().appliquer({"effet_tele": False})
    verifier("retirer effet_tele : effet d'origine a l'octet pres",
             open(os.path.join(rom, "shaders", "screen_crt_hud.glsl"), "rb").read() == origine_shader)
    atelier().appliquer({"effet_tele": True})

    atelier().appliquer({"ascenseur_x2": True})
    atelier().appliquer({n: False for n in atelier().modules})
    verifier("--origine : programme d'origine", md5(prog) == P.MD5_ORIGINE)
    verifier("--origine : fichier vide d'origine", os.path.getsize(os.path.join(rom, "scripts", "library_custom_1.lua")) == 0)
    verifier("--origine : journal retire (fichier vide)", os.path.getsize(os.path.join(rom, "scripts", "library_custom_4.lua")) == 0)
    verifier("--origine : effet d'origine", open(os.path.join(rom, "shaders", "screen_crt_hud.glsl"), "rb").read() == origine_shader)

    print("\nModule atterrissage (reglage B : creneau elargi + circuit en cercle) :")
    verifier("depart : programme d'origine", md5(prog) == P.MD5_ORIGINE)
    atelier().appliquer({"atterrissage": True})
    verifier("activer atterrissage", atelier().etats()["atterrissage"] == "actif")
    verifier("  md5 attendu", md5(prog) == MD5_ATTERRISSAGE, md5(prog))
    a_b = atelier()
    origine_b, patche_b = bytes(a_b.original_reconstruit()), open(prog, "rb").read()
    ecarts = [i for i, (a, b) in enumerate(zip(origine_b, patche_b)) if a != b] \
        if len(origine_b) == len(patche_b) else None
    verifier("  taille identique, octets changes dans les 10 instructions seulement",
             ecarts is not None and all(any(o <= i < o + len(a) for o, a, _ in atelier().tables["atterrissage"]) for i in ecarts),
             "%s octets changes" % (len(ecarts) if ecarts is not None else "?"))
    for va, attendu in DECODAGE_B:
        lu = decoder(prog, va)
        verifier("  %#x se lit « %s »" % (va, attendu), attendu in lu, lu)
    d_b = open(prog, "rb").read()
    verifier("  constantes lues : (1000, 1800), (-1000, -1800), -1800",
             struct.unpack_from("<2f", d_b, 0x10286b920 - P.BASE) == (1000.0, 1800.0)
             and struct.unpack_from("<2f", d_b, 0x10286b930 - P.BASE) == (-1000.0, -1800.0)
             and struct.unpack_from("<f", d_b, 0x102869adc - P.BASE)[0] == -1800.0)
    atelier().appliquer({"ascenseur_x2": True})
    e4 = atelier().etats()
    verifier("  avec ascenseur_x2 : les deux actifs", e4["ascenseur_x2"] == "actif" and e4["atterrissage"] == "actif", str(e4))
    verifier("  md5 = celui active dans le jeu le 23/10", md5(prog) == MD5_ASCENSEUR_ATTERRISSAGE, md5(prog))
    atelier().appliquer({"atterrissage": False})
    verifier("  retirer atterrissage : reste exactement ascenseur_x2", md5(prog) == MD5_ASCENSEUR)
    atelier().appliquer({"ascenseur_x2": False})
    verifier("  tout retire : original a l'octet pres", md5(prog) == P.MD5_ORIGINE)

    print("\nModule pont_retour_x2 (roulage x2 sur le pont au retour) :")
    verifier("depart : programme d'origine", md5(prog) == P.MD5_ORIGINE)
    atelier().appliquer({"pont_retour_x2": True})
    verifier("activer pont_retour_x2", atelier().etats()["pont_retour_x2"] == "actif")
    verifier("  md5 = celui calcule a part", md5(prog) == MD5_PONT_RETOUR, md5(prog))
    patche_p = open(prog, "rb").read()
    ecarts_p = [i for i, (a, b) in enumerate(zip(origine_b, patche_p)) if a != b] \
        if len(origine_b) == len(patche_p) else None
    verifier("  taille identique, octets changes dans les 3 instructions seulement",
             ecarts_p is not None and 0 < len(ecarts_p) <= 12
             and all(any(o <= i < o + len(a) for o, a, _ in atelier().tables["pont_retour_x2"]) for i in ecarts_p),
             "%s octets changes" % (len(ecarts_p) if ecarts_p is not None else "?"))
    for va in (0x1001b0824, 0x1001ae07c, 0x1001b0831):
        lu = decoder(prog, va)
        verifier("  %#x se lit « mulss … %%xmm1 ## 0x1028699cc »" % va,
                 lu.startswith("mulss") and "%xmm1" in lu and "## 0x1028699cc" in lu, lu)
    verifier("  constantes : 15.0 lue, 30.0 d'origine intacte",
             struct.unpack_from("<f", patche_p, 0x1028699cc - P.BASE)[0] == 15.0
             and struct.unpack_from("<f", patche_p, 0x102869898 - P.BASE)[0] == 30.0)
    atelier().appliquer({n: True for n in MODULES_JEU_25_10})
    e_p = atelier().etats()
    verifier("  avec les 9 modules du jeu : les 10 actifs",
             all(e_p[n] == "actif" for n in MODULES_JEU_25_10 + ("pont_retour_x2",)), str(e_p))
    verifier("  md5 = jeu du 25/10 + pont_retour_x2 (calcule a part)", md5(prog) == MD5_JEU_PONT_RETOUR, md5(prog))
    atelier().appliquer({"pont_retour_x2": False})
    verifier("  retirer pont_retour_x2 : exactement le programme du jeu du 25/10", md5(prog) == MD5_JEU_25_10, md5(prog))
    atelier().appliquer({n: False for n in MODULES_JEU_25_10})
    verifier("  tout retire : original a l'octet pres", md5(prog) == P.MD5_ORIGINE)
    verifier("  tout retire : fichiers du faux rom_0 d'origine",
             open(os.path.join(rom, "shaders", "screen_crt_hud.glsl"), "rb").read() == origine_shader
             and all(os.path.getsize(os.path.join(rom, "scripts", "library_custom_%d.lua" % k)) == 0 for k in (1, 4, 5)))

    print("\nModule grue_annulation (annuler la sortie d'un avion deja pris par la grue) :")
    atelier().appliquer({"grue_annulation": True})
    verifier("activer grue_annulation", atelier().etats()["grue_annulation"] == "actif")
    verifier("  md5 = celui annonce par le module", md5(prog) == MD5_GRUE_ANNULATION, md5(prog))
    for va, cible in ((0x1001a8c01, "jmp\t0x100061200"), (0x1001ad9ad, "jmp\t0x100061230")):
        lu = decoder(prog, va)
        verifier("  %#x se lit « %s »" % (va, cible.replace("\t", " ")), lu.startswith(cible), lu)
    atelier().appliquer({n: True for n in MODULES_JEU_25_10})
    e_g = atelier().etats()
    verifier("  avec les 9 modules du jeu : les 10 actifs",
             all(e_g[n] == "actif" for n in MODULES_JEU_25_10 + ("grue_annulation",)), str(e_g))
    verifier("  md5 = jeu du 25/10 + grue_annulation", md5(prog) == MD5_JEU_GRUE_ANNULATION, md5(prog))
    atelier().appliquer({"grue_annulation": False})
    verifier("  retirer grue_annulation : exactement le programme du jeu du 25/10", md5(prog) == MD5_JEU_25_10, md5(prog))
    atelier().appliquer({n: False for n in MODULES_JEU_25_10})
    verifier("  tout retire : original a l'octet pres", md5(prog) == P.MD5_ORIGINE)
    print("  (logique de la greffe et relecture complete : tests/test_grue_annulation.py)")

    print("\nModule cctv_net (ecran des cameras CCTV en 512 x 512) :")
    atelier().appliquer({"cctv_net": True})
    verifier("activer cctv_net", atelier().etats()["cctv_net"] == "actif")
    verifier("  md5 = celui annonce par le module", md5(prog) == MD5_CCTV_NET, md5(prog))
    for va, cible in ((0x1000ad74f, "jmp\t0x100061800"), (0x10021ce70, "jmp\t0x10006187b"),
                      (0x10015e662, "jmp\t0x1000618d0"), (0x10021cf13, "jmp\t0x10006198c")):
        lu = decoder(prog, va)
        verifier("  %#x se lit « %s »" % (va, cible.replace("\t", " ")), lu.startswith(cible), lu)
    atelier().appliquer({n: True for n in MODULES_JEU_25_10 + ("grue_annulation",)})
    e_c = atelier().etats()
    verifier("  avec les 9 modules du jeu et grue_annulation : les 11 actifs",
             all(e_c[n] == "actif" for n in MODULES_JEU_25_10 + ("grue_annulation", "cctv_net")), str(e_c))
    atelier().appliquer({"grue_annulation": False})
    verifier("  md5 = jeu du 25/10 + cctv_net", md5(prog) == MD5_JEU_CCTV_NET, md5(prog))
    atelier().appliquer({"cctv_net": False})
    verifier("  retirer cctv_net : exactement le programme du jeu du 25/10", md5(prog) == MD5_JEU_25_10, md5(prog))
    atelier().appliquer({n: False for n in MODULES_JEU_25_10})
    verifier("  tout retire : original a l'octet pres", md5(prog) == P.MD5_ORIGINE)
    print("  (greffes executees et relecture complete : tests/test_cctv_net.py)")

    print("\nModules vitesse_escadrille + vitesse_boutons (vitesse des avions ECO / NORMAL / FLANK) :")
    atelier().appliquer({"vitesse_escadrille": True})
    verifier("activer vitesse_escadrille", atelier().etats()["vitesse_escadrille"] == "actif")
    verifier("  md5 = celui annonce par le module", md5(prog) == MD5_VITESSE_ESCADRILLE, md5(prog))
    lu = decoder(prog, 0x1001c2b4b)
    verifier("  0x1001c2b4b se lit « jmp 0x10005d000 »", lu.startswith("jmp\t0x10005d000"), lu)
    import struct as _s
    entree = _s.unpack_from("<QQ", open(prog, "rb").read(), 0x1029dd310 - 0x100000000)
    verifier("  base_funcs : { cc2_vitesse, vit_lua }", entree == (0x10005d200, 0x10005d080), [hex(x) for x in entree])
    atelier().appliquer({"vitesse_escadrille": False})
    verifier("  retirer : original a l'octet pres", md5(prog) == P.MD5_ORIGINE)
    autres = [n for n in atelier().modules if n not in ("vitesse_escadrille", "vitesse_boutons")]
    atelier().appliquer({n: True for n in autres})
    md5_autres = md5(prog)
    atelier().appliquer({"vitesse_escadrille": True, "vitesse_boutons": True})
    e_v = atelier().etats()
    verifier("  avec tous les autres modules (%d) : tous actifs" % len(autres), all(v == "actif" for v in e_v.values()), str(e_v))
    verifier("  library_custom_6.lua = notre source", open(os.path.join(rom, "scripts", "library_custom_6.lua"), "rb").read()
             == open(os.path.join(P.FICHIERS, "vitesse_boutons", "library_custom_6.lua"), "rb").read())
    atelier().appliquer({"vitesse_escadrille": False, "vitesse_boutons": False})
    verifier("  retirer les deux : programme identique a celui des autres modules", md5(prog) == md5_autres, md5(prog))
    verifier("  library_custom_6.lua de nouveau vide", os.path.getsize(os.path.join(rom, "scripts", "library_custom_6.lua")) == 0)
    atelier().appliquer({n: False for n in autres})
    verifier("  tout retire : original a l'octet pres", md5(prog) == P.MD5_ORIGINE)
    print("  (greffe executee et relecture complete : tests/test_vitesse_escadrille.py ; barre : tests/test_vitesse_boutons.py)")

    print("\nModule en reserve atterrissage_creneau (reglage A) :")
    res = os.path.join(tmp, "modules_reglage_a")
    shutil.copytree(P.MODULES, res)
    os.remove(os.path.join(res, "atterrissage.py"))
    shutil.copy(os.path.join(os.path.dirname(P.MODULES), "modules_en_reserve", "atterrissage_creneau.py"), res)
    atelier(res).appliquer({"atterrissage_creneau": True})
    verifier("activer : les 3 sauts vont au test de la piste",
             all("0x1001af914" in decoder(prog, va) for va in (0x1001af900, 0x1001af85b, 0x1001af867)))
    atelier(res).appliquer({"atterrissage_creneau": False})
    verifier("retirer : original a l'octet pres", md5(prog) == P.MD5_ORIGINE)
    deux = os.path.join(tmp, "modules_a_et_b")
    shutil.copytree(P.MODULES, deux)
    shutil.copy(os.path.join(os.path.dirname(P.MODULES), "modules_en_reserve", "atterrissage_creneau.py"), deux)
    r = refuse(lambda: atelier(deux))
    verifier("A et B ensemble dans modules/ : refus (memes octets)", r is not None and "memes octets" in r, r or "")

    print("\nModules du releve (releve + ecriture_releve) :")
    verifier("depart : programme d'origine", md5(prog) == P.MD5_ORIGINE)
    atelier().appliquer({"releve": True, "ecriture_releve": True})
    e5 = atelier().etats()
    verifier("activer les deux", e5["releve"] == "actif" and e5["ecriture_releve"] == "actif")
    verifier("  library_custom_5.lua = notre source", open(os.path.join(rom, "scripts", "library_custom_5.lua"), "rb").read()
             == open(os.path.join(P.FICHIERS, "releve", "library_custom_5.lua"), "rb").read())
    verifier("  md5 attendu (ecriture_releve seul)", md5(prog) == MD5_ECRITURE_RELEVE, md5(prog))
    verifier("  0x10283aed0 : call vers la greffe (_rv_r12)", "callq\t0x100061a00" in decoder(prog, 0x10283aed0), decoder(prog, 0x10283aed0))
    verifier("  0x10283af78 : call vers la greffe (_rv_rbx)", "callq\t0x100061a0d" in decoder(prog, 0x10283af78), decoder(prog, 0x10283af78))
    verifier("  instructions suivantes intactes", decoder(prog, 0x10283aed7) == "movq\t%r15, %rdi"
             and decoder(prog, 0x10283af7f) == "movq\t(%rbx), %rcx", decoder(prog, 0x10283aed7) + " / " + decoder(prog, 0x10283af7f))
    atelier().appliquer({"helicos_pres_ascenseur": True, "helicos_approche_x2": True})
    e6 = atelier().etats()
    verifier("  avec les modules helicos (meme zone de code mort) : tous actifs",
             all(e6[n] == "actif" for n in ("releve", "ecriture_releve", "helicos_pres_ascenseur", "helicos_approche_x2")), str(e6))
    atelier().appliquer({"helicos_pres_ascenseur": False, "helicos_approche_x2": False})
    verifier("  retirer les helicos : reste exactement ecriture_releve", md5(prog) == MD5_ECRITURE_RELEVE)
    atelier().appliquer({"releve": False, "ecriture_releve": False})
    verifier("  tout retirer : programme d'origine a l'octet pres", md5(prog) == P.MD5_ORIGINE)
    verifier("  tout retirer : library_custom_5.lua de nouveau vide",
             os.path.getsize(os.path.join(rom, "scripts", "library_custom_5.lua")) == 0)

    print("\nRefus attendus :")
    d = bytearray(open(prog, "rb").read())
    o = 0x10019455a - P.BASE + 5
    d[o] ^= 0xFF
    open(prog, "wb").write(d)
    r = refuse(lambda: atelier().appliquer({"ascenseur_x2": True}))
    verifier("module abime (1 octet change sur un site)", r is not None and "abime" in r, r or "")
    d[o] ^= 0xFF
    d[0x200000] ^= 0x01                                   # octet hors des sites : autre version du jeu
    open(prog, "wb").write(d)
    r = refuse(lambda: atelier().appliquer({"ascenseur_x2": True}))
    verifier("programme d'une autre version (mise a jour Steam)", r is not None and "analyse" in r, r or "")
    d[0x200000] ^= 0x01
    open(prog, "wb").write(d)
    verifier("  et rien n'a ete ecrit", md5(prog) == P.MD5_ORIGINE)

    faux = os.path.join(tmp, "modules_faux")
    shutil.copytree(P.MODULES, faux)
    with open(os.path.join(faux, "zz_faux.py"), "w") as f:
        f.write('NOM = "faux"\nTITRE = "test"\nTYPE = "programme"\n'
                'RETOUCHES = [("imm", 0x10019f0ad, "41c78718010000cdcccc3e", "41c78718010000cdcccc3f")]\n')
    r = refuse(lambda: atelier(faux))
    verifier("deux modules sur les memes octets", r is not None and "memes octets" in r, r or "")

    open(os.path.join(rom, "scripts", "library_custom_1.lua"), "w").write("-- un autre mod\n")
    r = refuse(lambda: atelier().appliquer({"horloge": True}))
    verifier("fichier occupe par un autre mod", r is not None and "autre chose" in r, r or "")

    print("\nModule fichier avec un original non vide (cas d'un effet graphique) :")
    os.makedirs(os.path.join(rom, "shaders"), exist_ok=True)
    original = b"// effet d'origine\nvoid main() {}\n"
    open(os.path.join(rom, "shaders", "essai.glsl"), "wb").write(original)
    os.makedirs(os.path.join(P.FICHIERS, "_test"), exist_ok=True)
    open(os.path.join(P.FICHIERS, "_test", "essai.glsl"), "wb").write(b"// version modifiee\n")
    mods2 = os.path.join(tmp, "modules_shader")
    shutil.copytree(P.MODULES, mods2)
    with open(os.path.join(mods2, "zz_essai.py"), "w") as f:
        f.write('NOM = "essai"\nTITRE = "test"\nTYPE = "fichier"\nCIBLE = "shaders/essai.glsl"\n'
                'SOURCE = "_test/essai.glsl"\nORIGINE_SHA256 = "%s"\n' % hashlib.sha256(original).hexdigest())
    open(os.path.join(rom, "scripts", "library_custom_1.lua"), "wb").close()
    P.Atelier(prog, rom, mods2, sauv, sauv_rom).appliquer({"essai": True})
    verifier("activer : fichier remplace", open(os.path.join(rom, "shaders", "essai.glsl"), "rb").read() == b"// version modifiee\n")
    P.Atelier(prog, rom, mods2, sauv, sauv_rom).appliquer({"essai": False})
    verifier("retirer : original remis a l'octet pres", open(os.path.join(rom, "shaders", "essai.glsl"), "rb").read() == original)

    print("\nLecture stricte des arguments (l'accident du 23/10 ne doit plus etre possible) :")
    colle = "--programme %s --rom %s" % (prog, rom)        # options collees en un seul mot (zsh)
    r = refuse(lambda: P.lire_arguments([colle, "--activer", "ascenseur_x2"]))
    verifier("options collees en un seul mot : refus", r is not None and "non reconnu" in r, r or "")
    verifier("mot inconnu : refus", refuse(lambda: P.lire_arguments(["--activr", "x"])) is not None)
    verifier("chemin manquant : refus", refuse(lambda: P.lire_arguments(["--programme"])) is not None)

    import subprocess
    outil = os.path.join(os.path.dirname(ICI), "outil", "patchs_cc2.py")
    copie = ["--programme", prog, "--rom", rom, "--sauvegarde", sauv, "--sauvegarde-rom", sauv_rom]
    subprocess.run([sys.executable, "-I", outil] + copie + ["--activer", "ascenseur_x2"], capture_output=True)
    verifier("commande --activer sur la copie", md5(prog) == MD5_ASCENSEUR)
    sortie = subprocess.run([sys.executable, "-I", outil] + copie + ["--menu"], input="1\nq\n",
                            capture_output=True, text=True).stdout
    verifier("menu : choix 1 = retirer ascenseur x2", md5(prog) == P.MD5_ORIGINE and "Retirer  Ascenseur" in sortie)
    sortie = subprocess.run([sys.executable, "-I", outil, colle, "--origine"], capture_output=True, text=True).stdout
    verifier("commande avec options collees : ARRET, rien touche", "ARRET" in sortie, sortie.strip().splitlines()[-1])
finally:
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(os.path.join(P.FICHIERS, "_test"), ignore_errors=True)

print("\nRESULTAT : " + ("TOUT EST BON" if ok else "IL Y A DES ECHECS"))
sys.exit(0 if ok else 1)
