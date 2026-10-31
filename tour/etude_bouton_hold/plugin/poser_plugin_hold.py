#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pose (ou retire) le plugin cc2x_hold.dll DANS le mod deja pose cc2_hold_copies : un seul fichier ajoute,
%APPDATA%\\Carrier Command 2\\mods\\cc2_hold_copies\\content\\cc2x\\cc2x_hold.dll (le SDK y charge les plugins des mods actifs).
mods.xml n'est QUE lu. Rien n'est ecrit dans le dossier du jeu.

  python -I -B poser_plugin_hold.py etat      [--dll DLL] [--ancienne DLL] [--jeu DOSSIER_DU_JEU]
  python -I -B poser_plugin_hold.py poser     [--dll DLL] [--jeu DOSSIER_DU_JEU] [--a-blanc]
  python -I -B poser_plugin_hold.py remplacer [--dll DLL] [--ancienne DLL] [--jeu DOSSIER_DU_JEU] [--a-blanc]
  python -I -B poser_plugin_hold.py retirer   [--dll DLL] [--jeu DOSSIER_DU_JEU] [--a-blanc]
  python -I -B poser_plugin_hold.py autotest

--dll : par defaut la v2 (plugin_v2\\dist) ; --ancienne : par defaut la v1 (plugin_v1\\dist). `remplacer` met --dll a la place
de --ancienne, seulement si la DLL posee est exactement --ancienne ; retour a la v1 : `remplacer --dll <v1> --ancienne <v2>`.
Refus (rien n'est ecrit) : un processus carrier_command* tourne ; une DLL n'a pas l'empreinte de son SHA256.txt (a cote d'elle) ou
n'est pas une DLL 32 bits ; le mod cc2_hold_copies n'est pas pose et actif dans mods.xml, ou son dossier n'a pas exactement ses 3
fichiers (4 avec le plugin, pour remplacer) avec des copies du bouton Hold ; pour poser : un cc2x_hold.dll est deja pose (dans le mod
ou dans le dossier du jeu). `retirer` ne supprime la DLL que si elle est identique a --dll. Avant de retirer le mod lui-meme
(poser_mod_hold.py retirer), retirer ce plugin. Un seul sous-processus : PowerShell, pour compter les processus carrier_command*.
Aucun reseau.
"""
import argparse
import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

NOM_MOD = "cc2_hold_copies"
NOM_DLL = "cc2x_hold.dll"
DLL_RELATIF = os.path.join("content", "cc2x", NOM_DLL)
XML_RELATIF = os.path.join("content", "game_objects", "vehicle_chassis_carrier.xml")
FICHIERS_MOD = {"mod.xml", "thumbnail.png", XML_RELATIF}
DLL_DEFAUT = r"C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v2\dist\cc2x_hold.dll"
ANCIENNE_DEFAUT = r"C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v1\dist\cc2x_hold.dll"
JEU_DEFAUT = r"C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2"
PREFIXE = "vehicle_control_air_hold_copie_"
JEU_OUVERT_FORCE = None          # reserve aux tests


class Refus(Exception):
    pass


def sha(octets):
    return hashlib.sha256(octets).hexdigest().upper()


def jeu_ouvert():
    if JEU_OUVERT_FORCE is not None:
        return JEU_OUVERT_FORCE
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                            "(Get-Process -Name 'carrier_command*' -ErrorAction SilentlyContinue | Measure-Object).Count"],
                           capture_output=True, text=True, timeout=30)
        return int(r.stdout.strip() or "0") > 0
    except Exception:
        raise Refus("impossible de savoir si le jeu tourne : par prudence, rien n'est fait")


def lire_dll(chemin):
    """La DLL et son empreinte attendue (SHA256.txt a cote, ecrit par construire_hold.py)."""
    with open(chemin, "rb") as f:
        d = f.read()
    ref = os.path.join(os.path.dirname(chemin), "SHA256.txt")
    if not os.path.isfile(ref):
        raise Refus("pas de SHA256.txt a cote de la DLL : la recompiler avec construire_hold.py")
    with open(ref, encoding="ascii") as f:
        attendu = f.read().split()[0].upper()
    if sha(d) != attendu:
        raise Refus("la DLL n'a pas l'empreinte de SHA256.txt (%s au lieu de %s)" % (sha(d)[:8], attendu[:8]))
    if d[:2] != b"MZ" or len(d) < 0x200:
        raise Refus("ce n'est pas une DLL")
    nt = struct.unpack_from("<I", d, 0x3c)[0]
    if d[nt:nt + 4] != b"PE\0\0" or struct.unpack_from("<H", d, nt + 4)[0] != 0x14c or not struct.unpack_from("<H", d, nt + 22)[0] & 0x2000:
        raise Refus("ce n'est pas une DLL 32 bits")
    if b"cc2x_plugin_load" not in d:
        raise Refus("la DLL n'exporte pas cc2x_plugin_load")
    return d


def contexte(a):
    appdata = a.appdata or os.path.join(os.environ["APPDATA"], "Carrier Command 2")
    mod = os.path.join(appdata, "mods", NOM_MOD)
    return appdata, mod, os.path.join(mod, DLL_RELATIF)


def meme_chemin(x, y):
    return os.path.normcase(os.path.normpath(x)) == os.path.normcase(os.path.normpath(y))


def verifier_mod(appdata, mod):
    with open(os.path.join(appdata, "mods.xml"), "rb") as f:
        actifs = [p.get("value") for p in ET.fromstring(f.read()).iter("path")]
    if not any(meme_chemin(p, mod) for p in actifs):
        raise Refus("le mod %s n'est pas actif dans mods.xml : le poser d'abord (poser_mod_hold.py)" % NOM_MOD)
    if not os.path.isdir(mod):
        raise Refus("le dossier du mod %s n'existe pas" % mod)
    fichiers = set()
    for dossier, _, noms in os.walk(mod):
        for n in noms:
            fichiers.add(os.path.relpath(os.path.join(dossier, n), mod))
    return fichiers, actifs


def copies_du_mod(mod):
    with open(os.path.join(mod, XML_RELATIF), "rb") as f:
        texte = f.read().decode("utf-8")
    return re.findall(r'<button name="(' + re.escape(PREFIXE) + r'[a-z_]+)"[^>]*type="18"', texte)


def ecrire_verifie(chemin, octets):
    tmp = chemin + ".tmp_hold"
    with open(tmp, "wb") as f:
        f.write(octets)
    with open(tmp, "rb") as f:
        if f.read() != octets:
            os.remove(tmp)
            raise Refus("relecture differente de ce qui a ete ecrit : %s" % chemin)
    os.replace(tmp, chemin)


def cmd_etat(a):
    appdata, mod, cible = contexte(a)
    print("jeu lance                :", jeu_ouvert())
    d = lire_dll(a.dll)
    print("DLL source               : %s (%d octets, %s)" % (a.dll, len(d), sha(d)[:16]))
    fichiers, _ = verifier_mod(appdata, mod)
    print("mod pose et actif        :", mod, "(%d fichiers)" % len(fichiers))
    print("copies dans le mod       :", copies_du_mod(mod))
    pose = open(cible, "rb").read() if os.path.isfile(cible) else None
    ancienne = open(a.ancienne, "rb").read() if a.ancienne and os.path.isfile(a.ancienne) else None
    print("plugin pose dans le mod  :", pose is not None, ("" if pose is None else "identique a --dll" if pose == d else
                                                            "identique a --ancienne" if pose == ancienne else "AUTRE (%s)" % sha(pose)[:16]))
    print("plugin dans le jeu       :", os.path.isfile(os.path.join(a.jeu, NOM_DLL)))
    return 0


def cmd_poser(a):
    appdata, mod, cible = contexte(a)
    if jeu_ouvert():
        raise Refus("un processus carrier_command* tourne : le fermer d'abord")
    d = lire_dll(a.dll)
    fichiers, _ = verifier_mod(appdata, mod)
    if DLL_RELATIF in fichiers or os.path.exists(cible):
        raise Refus("un %s est deja pose dans le mod" % NOM_DLL)
    if fichiers != FICHIERS_MOD:
        raise Refus("le dossier du mod doit contenir exactement %s ; trouve %s" % (sorted(FICHIERS_MOD), sorted(fichiers)))
    copies = copies_du_mod(mod)
    if not copies:
        raise Refus("le mod pose ne contient aucune copie du bouton Hold : le plugin n'aurait rien a faire")
    if os.path.exists(os.path.join(a.jeu, NOM_DLL)):
        raise Refus("un %s existe deja dans le dossier du jeu" % NOM_DLL)
    print("pose : %s (%s) -> %s ; copies du mod : %s" % (a.dll, sha(d)[:16], cible, copies))
    if a.a_blanc:
        print("A BLANC : rien n'est ecrit")
        return 0
    os.makedirs(os.path.dirname(cible), exist_ok=True)
    ecrire_verifie(cible, d)
    with open(cible, "rb") as f:
        if sha(f.read()) != sha(d):
            raise Refus("empreinte de la DLL posee differente")
    print("POSE : %s (%s). Retrait : poser_plugin_hold.py retirer" % (cible, sha(d)[:16]))
    return 0


def cmd_remplacer(a):
    appdata, mod, cible = contexte(a)
    if jeu_ouvert():
        raise Refus("un processus carrier_command* tourne : le fermer d'abord")
    d = lire_dll(a.dll)
    vieille = lire_dll(a.ancienne)
    if d == vieille:
        raise Refus("--dll et --ancienne sont la meme DLL : rien a remplacer")
    fichiers, _ = verifier_mod(appdata, mod)
    if not os.path.isfile(cible):
        raise Refus("aucun %s pose dans le mod : utiliser poser" % NOM_DLL)
    with open(cible, "rb") as f:
        pose = f.read()
    if pose != vieille:
        raise Refus("le %s pose n'est pas --ancienne (%s au lieu de %s) : rien n'est remplace" % (NOM_DLL, sha(pose)[:8], sha(vieille)[:8]))
    if fichiers != FICHIERS_MOD | {DLL_RELATIF}:
        raise Refus("le dossier du mod doit contenir exactement %s ; trouve %s" % (sorted(FICHIERS_MOD | {DLL_RELATIF}), sorted(fichiers)))
    copies = copies_du_mod(mod)
    if not copies:
        raise Refus("le mod pose ne contient aucune copie du bouton Hold : le plugin n'aurait rien a faire")
    if os.path.exists(os.path.join(a.jeu, NOM_DLL)):
        raise Refus("un %s existe aussi dans le dossier du jeu" % NOM_DLL)
    print("remplacement : %s (%s) -> %s (%s) dans %s ; copies du mod : %s" % (a.ancienne, sha(vieille)[:16], a.dll, sha(d)[:16], cible, copies))
    if a.a_blanc:
        print("A BLANC : rien n'est ecrit")
        return 0
    ecrire_verifie(cible, d)
    with open(cible, "rb") as f:
        if sha(f.read()) != sha(d):
            raise Refus("empreinte de la DLL posee differente")
    print("REMPLACE : %s (%s). Retour : poser_plugin_hold.py remplacer --dll %s --ancienne %s" % (cible, sha(d)[:16], a.ancienne, a.dll))
    return 0


def cmd_retirer(a):
    appdata, mod, cible = contexte(a)
    if jeu_ouvert():
        raise Refus("un processus carrier_command* tourne : le fermer d'abord")
    d = lire_dll(a.dll)
    if not os.path.isfile(cible):
        raise Refus("aucun %s pose dans le mod" % NOM_DLL)
    with open(cible, "rb") as f:
        if f.read() != d:
            raise Refus("le %s pose n'est pas celui-ci : rien n'est supprime" % NOM_DLL)
    print("retrait :", cible)
    if a.a_blanc:
        print("A BLANC : rien n'est supprime")
        return 0
    os.remove(cible)
    dossier = os.path.dirname(cible)
    if not os.listdir(dossier):
        os.rmdir(dossier)
    print("RETIRE. Le mod cc2_hold_copies reste pose (copies visibles, sans effet).")
    return 0


# ------------------------------------------------------------------------------------------------ autotest (faux dossiers)
def _monde(racine):
    appdata = os.path.join(racine, "appdata")
    mod = os.path.join(appdata, "mods", NOM_MOD)
    jeu = os.path.join(racine, "jeu")
    build = os.path.join(racine, "build")
    for p in (os.path.join(mod, "content", "game_objects"), jeu, build):
        os.makedirs(p, exist_ok=True)
    with open(os.path.join(appdata, "mods.xml"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<data>\n\t<active_mod_folders>\n\t\t<path value="C:\\autre"/>\n'
                '\t\t<path value="%s"/>\n\t</active_mod_folders>\n</data>\n' % mod)
    for n, t in (("mod.xml", b"<mod/>"), ("thumbnail.png", b"\x89PNG")):
        with open(os.path.join(mod, n), "wb") as f:
            f.write(t)
    with open(os.path.join(mod, XML_RELATIF), "wb") as f:
        f.write(b'<buttons>\n<button name="vehicle_control_air_hold" type="18">\n'
                b'<button name="vehicle_control_air_hold_copie_moteur" display_name_loc="1527" type="18" help_tag="x">\n</buttons>\n')
    dll = bytearray(0x400)
    dll[:2] = b"MZ"
    struct.pack_into("<I", dll, 0x3c, 0x80)
    dll[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HH", dll, 0x84, 0x14c, 1)
    struct.pack_into("<H", dll, 0x80 + 22, 0x2102)
    dll[0x200:0x210] = b"cc2x_plugin_load"
    with open(os.path.join(build, NOM_DLL), "wb") as f:
        f.write(bytes(dll))
    with open(os.path.join(build, "SHA256.txt"), "w", encoding="ascii") as f:
        f.write("%s  %s\n" % (sha(bytes(dll)), NOM_DLL))
    return appdata, mod, jeu, os.path.join(build, NOM_DLL)


def autotest():
    global JEU_OUVERT_FORCE
    ok = ko = 0

    def check(cond, texte):
        nonlocal ok, ko
        print(("OK     " if cond else "ECHEC  ") + texte)
        ok, ko = ok + bool(cond), ko + (not cond)

    def lancer(cmd, appdata, jeu, dll, a_blanc=False, ancienne=None):
        a = argparse.Namespace(commande=cmd, dll=dll, jeu=jeu, appdata=appdata, a_blanc=a_blanc, ancienne=ancienne)
        try:
            return {"poser": cmd_poser, "retirer": cmd_retirer, "etat": cmd_etat, "remplacer": cmd_remplacer}[cmd](a), ""
        except Refus as e:
            return None, str(e)

    def autre_dll(dll, dossier, octet):
        """une deuxieme fausse DLL (un octet change), avec son SHA256.txt, dans son propre dossier"""
        d = bytearray(open(dll, "rb").read())
        d[0x300] = octet
        os.makedirs(dossier, exist_ok=True)
        chemin = os.path.join(dossier, NOM_DLL)
        with open(chemin, "wb") as f:
            f.write(bytes(d))
        with open(os.path.join(dossier, "SHA256.txt"), "w", encoding="ascii") as f:
            f.write("%s  %s\n" % (sha(bytes(d)), NOM_DLL))
        return chemin

    def instantane(racine):
        r = {}
        for dossier, _, noms in os.walk(racine):
            for n in noms:
                p = os.path.join(dossier, n)
                r[os.path.relpath(p, racine)] = open(p, "rb").read()
        return r

    racine = tempfile.mkdtemp(prefix="test_poser_plugin_hold_")
    try:
        JEU_OUVERT_FORCE = False
        appdata, mod, jeu, dll = _monde(os.path.join(racine, "m1"))
        cible = os.path.join(mod, DLL_RELATIF)
        avant = instantane(os.path.join(racine, "m1"))
        r, e = lancer("poser", appdata, jeu, dll, a_blanc=True)
        check(r == 0 and instantane(os.path.join(racine, "m1")) == avant, "a blanc : rien n'est ecrit")
        JEU_OUVERT_FORCE = True
        r, e = lancer("poser", appdata, jeu, dll)
        check(r is None and "tourne" in e and not os.path.exists(cible), "jeu ouvert : refus")
        JEU_OUVERT_FORCE = False
        mx = open(os.path.join(appdata, "mods.xml"), "rb").read()
        r, e = lancer("poser", appdata, jeu, dll)
        check(r == 0 and open(cible, "rb").read() == open(dll, "rb").read(), "pose : DLL copiee a l'identique")
        check(open(os.path.join(appdata, "mods.xml"), "rb").read() == mx, "pose : mods.xml inchange")
        apres = instantane(os.path.join(racine, "m1"))
        check(set(apres) - set(avant) == {os.path.join("appdata", "mods", NOM_MOD, DLL_RELATIF)} and
              all(apres[k] == avant[k] for k in avant), "pose : un seul fichier ajoute, rien d'autre change")
        r, e = lancer("poser", appdata, jeu, dll)
        check(r is None and "deja pose" in e, "deuxieme pose : refus")
        r, e = lancer("etat", appdata, jeu, dll)
        check(r == 0, "etat apres pose")
        with open(cible, "ab") as f:
            f.write(b"x")
        r, e = lancer("retirer", appdata, jeu, dll)
        check(r is None and "pas celui-ci" in e and os.path.exists(cible), "retrait d'une DLL modifiee : refus, rien supprime")
        with open(cible, "wb") as f:
            f.write(open(dll, "rb").read())
        r, e = lancer("retirer", appdata, jeu, dll, a_blanc=True)
        check(r == 0 and os.path.exists(cible), "retrait a blanc : rien supprime")
        JEU_OUVERT_FORCE = True
        r, e = lancer("retirer", appdata, jeu, dll)
        check(r is None and os.path.exists(cible), "retrait jeu ouvert : refus")
        JEU_OUVERT_FORCE = False
        r, e = lancer("retirer", appdata, jeu, dll)
        check(r == 0 and not os.path.exists(cible) and not os.path.exists(os.path.dirname(cible)), "retrait : DLL et dossier cc2x vide supprimes")
        check(instantane(os.path.join(racine, "m1")) == avant, "apres retrait : tout est comme avant la pose")
        r, e = lancer("retirer", appdata, jeu, dll)
        check(r is None and "aucun" in e, "retrait sans DLL posee : refus")

        appdata, mod, jeu, dll = _monde(os.path.join(racine, "m2"))
        with open(os.path.join(os.path.dirname(dll), "SHA256.txt"), "w", encoding="ascii") as f:
            f.write("0" * 64 + "  x\n")
        r, e = lancer("poser", appdata, jeu, dll)
        check(r is None and "empreinte" in e, "DLL d'empreinte inattendue : refus")

        appdata, mod, jeu, dll = _monde(os.path.join(racine, "m3"))
        with open(os.path.join(appdata, "mods.xml"), "w", encoding="utf-8") as f:
            f.write('<data><active_mod_folders><path value="C:\\autre"/></active_mod_folders></data>')
        r, e = lancer("poser", appdata, jeu, dll)
        check(r is None and "pas actif" in e, "mod non actif dans mods.xml : refus")

        appdata, mod, jeu, dll = _monde(os.path.join(racine, "m4"))
        with open(os.path.join(mod, "en_trop.txt"), "wb") as f:
            f.write(b"x")
        r, e = lancer("poser", appdata, jeu, dll)
        check(r is None and "exactement" in e, "fichier en trop dans le mod : refus")

        appdata, mod, jeu, dll = _monde(os.path.join(racine, "m5"))
        with open(os.path.join(mod, XML_RELATIF), "wb") as f:
            f.write(b'<button name="vehicle_control_air_hold" type="18">')
        r, e = lancer("poser", appdata, jeu, dll)
        check(r is None and "aucune copie" in e, "mod sans copie : refus")

        appdata, mod, jeu, dll = _monde(os.path.join(racine, "m6"))
        with open(os.path.join(jeu, NOM_DLL), "wb") as f:
            f.write(b"x")
        r, e = lancer("poser", appdata, jeu, dll)
        check(r is None and "dossier du jeu" in e, "plugin deja dans le dossier du jeu : refus")

        appdata, mod, jeu, dll = _monde(os.path.join(racine, "m7"))
        d = bytearray(open(dll, "rb").read())
        d[0x84] = 0x64
        with open(dll, "wb") as f:
            f.write(bytes(d))
        with open(os.path.join(os.path.dirname(dll), "SHA256.txt"), "w", encoding="ascii") as f:
            f.write("%s  x\n" % sha(bytes(d)))
        r, e = lancer("poser", appdata, jeu, dll)
        check(r is None and "32 bits" in e, "DLL 64 bits : refus")

        shutil.rmtree(os.path.join(racine, "m1"))
        appdata, mod, jeu, dll = _monde(os.path.join(racine, "m1"))
        shutil.rmtree(mod)
        r, e = lancer("poser", appdata, jeu, dll)
        check(r is None and "n'existe pas" in e, "dossier du mod absent : refus")

        # remplacer : v1 posee -> v2, puis retour a la v1
        appdata, mod, jeu, v1 = _monde(os.path.join(racine, "m8"))
        v2 = autre_dll(v1, os.path.join(racine, "m8", "build_v2"), 0x42)
        cible = os.path.join(mod, DLL_RELATIF)
        r, e = lancer("remplacer", appdata, jeu, v2, ancienne=v1)
        check(r is None and "aucun" in e and not os.path.exists(cible), "remplacer sans plugin pose : refus")
        r, e = lancer("poser", appdata, jeu, v1)
        check(r == 0 and open(cible, "rb").read() == open(v1, "rb").read(), "v1 posee (preparation)")
        avant = instantane(os.path.join(racine, "m8", "appdata"))
        r, e = lancer("remplacer", appdata, jeu, v2, a_blanc=True, ancienne=v1)
        check(r == 0 and instantane(os.path.join(racine, "m8", "appdata")) == avant, "remplacer a blanc : rien n'est ecrit")
        JEU_OUVERT_FORCE = True
        r, e = lancer("remplacer", appdata, jeu, v2, ancienne=v1)
        check(r is None and "tourne" in e and open(cible, "rb").read() == open(v1, "rb").read(), "remplacer jeu ouvert : refus, v1 intacte")
        JEU_OUVERT_FORCE = False
        r, e = lancer("remplacer", appdata, jeu, v1, ancienne=v1)
        check(r is None and "meme DLL" in e, "remplacer par la meme DLL : refus")
        r, e = lancer("remplacer", appdata, jeu, v2, ancienne=v1)
        apres = instantane(os.path.join(racine, "m8", "appdata"))
        check(r == 0 and open(cible, "rb").read() == open(v2, "rb").read(), "remplacer : la v2 est posee a l'identique")
        check(set(apres) == set(avant) and all(apres[k] == avant[k] for k in avant if not k.endswith(NOM_DLL)),
              "remplacer : seul cc2x_hold.dll a change (mods.xml et le mod intacts)")
        check(not any(n.endswith(".tmp_hold") for n in os.listdir(os.path.dirname(cible))), "remplacer : aucun fichier temporaire laisse")
        r, e = lancer("remplacer", appdata, jeu, v2, ancienne=v1)
        check(r is None and "n'est pas --ancienne" in e, "remplacer deux fois : refus (la posee n'est plus la v1)")
        r, e = lancer("etat", appdata, jeu, v2, ancienne=v1)
        check(r == 0, "etat apres remplacement")
        r, e = lancer("remplacer", appdata, jeu, v1, ancienne=v2)
        check(r == 0 and open(cible, "rb").read() == open(v1, "rb").read() and instantane(os.path.join(racine, "m8", "appdata")) == avant,
              "retour a la v1 : tout est comme avant le remplacement")
        with open(os.path.join(mod, "en_trop.txt"), "wb") as f:
            f.write(b"x")
        r, e = lancer("remplacer", appdata, jeu, v2, ancienne=v1)
        check(r is None and "exactement" in e and open(cible, "rb").read() == open(v1, "rb").read(), "remplacer avec un fichier en trop : refus")
        os.remove(os.path.join(mod, "en_trop.txt"))
        with open(os.path.join(jeu, NOM_DLL), "wb") as f:
            f.write(b"x")
        r, e = lancer("remplacer", appdata, jeu, v2, ancienne=v1)
        check(r is None and "dossier du jeu" in e, "remplacer avec un plugin aussi dans le dossier du jeu : refus")
        os.remove(os.path.join(jeu, NOM_DLL))
        with open(os.path.join(os.path.dirname(v2), "SHA256.txt"), "w", encoding="ascii") as f:
            f.write("0" * 64 + "  x\n")
        r, e = lancer("remplacer", appdata, jeu, v2, ancienne=v1)
        check(r is None and "empreinte" in e and open(cible, "rb").read() == open(v1, "rb").read(), "remplacer par une DLL d'empreinte inattendue : refus")
    finally:
        JEU_OUVERT_FORCE = None
        shutil.rmtree(racine, ignore_errors=True)
    print("\n%d controles, %d echec(s)" % (ok + ko, ko))
    return 1 if ko else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], allow_abbrev=False)
    p.add_argument("commande", choices=("etat", "poser", "remplacer", "retirer", "autotest"))
    p.add_argument("--dll", default=DLL_DEFAUT)
    p.add_argument("--ancienne", default=ANCIENNE_DEFAUT)
    p.add_argument("--jeu", default=JEU_DEFAUT)
    p.add_argument("--appdata", help="reserve aux essais : par defaut %%APPDATA%%\\Carrier Command 2")
    p.add_argument("--a-blanc", action="store_true")
    a = p.parse_args()
    if a.commande == "autotest":
        return autotest()
    try:
        return {"etat": cmd_etat, "poser": cmd_poser, "remplacer": cmd_remplacer, "retirer": cmd_retirer}[a.commande](a)
    except Refus as e:
        print("REFUS :", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
