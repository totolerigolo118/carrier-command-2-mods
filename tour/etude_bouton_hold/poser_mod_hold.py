#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pose (ou retire) le mod `cc2_hold_copies` : copie son dossier dans %APPDATA%\\Carrier Command 2\\mods\\ et ajoute UNE ligne
dans mods.xml (sauvegarde d'abord, jamais d'ecrasement). N'ecrit JAMAIS dans le dossier du jeu, ni exe, ni DLL.

  python -I -B poser_mod_hold.py etat    --mod DOSSIER_DU_MOD --jeu DOSSIER_DU_JEU
  python -I -B poser_mod_hold.py poser   --mod DOSSIER_DU_MOD --jeu DOSSIER_DU_JEU [--a-blanc]
  python -I -B poser_mod_hold.py retirer --mod DOSSIER_DU_MOD --jeu DOSSIER_DU_JEU [--a-blanc]
  python -I -B poser_mod_hold.py autotest

Refus (rien n'est ecrit) : un processus carrier_command* tourne ; le dossier du mod n'a pas exactement les 3 fichiers attendus ;
le fichier XML du mod ne differe plus du fichier du jeu QUE par l'ajout de blocs « copie du bouton Hold » (mise a jour du jeu :
refaire le mod avec fabriquer_mod_hold.py) ; le mod est deja pose ; un autre mod actif remplace deja le meme fichier du jeu ;
la sauvegarde datee existe deja. `retirer` ne supprime le dossier du mod que s'il est identique a celui qu'on a pose.
Un seul sous-processus : PowerShell, pour compter les processus carrier_command*. Aucun reseau.
"""
import argparse
import datetime
import difflib
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

NOM_MOD = "cc2_hold_copies"
XML_RELATIF = os.path.join("content", "game_objects", "vehicle_chassis_carrier.xml")
FICHIERS_ATTENDUS = {"mod.xml", "thumbnail.png", XML_RELATIF}
XML_JEU = os.path.join("rom_0", "game_objects", "vehicle_chassis_carrier.xml")
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


def lire_mod(mod):
    fichiers = {}
    for dossier, _, noms in os.walk(mod):
        for n in noms:
            p = os.path.join(dossier, n)
            with open(p, "rb") as f:
                fichiers[os.path.relpath(p, mod)] = f.read()
    if set(fichiers) != FICHIERS_ATTENDUS:
        raise Refus("le dossier du mod doit contenir exactement %s ; trouve %s" % (sorted(FICHIERS_ATTENDUS), sorted(fichiers)))
    return fichiers


def controler_mod_contre_jeu(fichiers, jeu):
    """Le XML du mod = celui du jeu + 1 ou 2 blocs « copie du bouton Hold », et RIEN d'autre. Renvoie les noms des copies."""
    mod_xml = fichiers[XML_RELATIF].decode("utf-8")
    with open(os.path.join(jeu, XML_JEU), "rb") as f:
        src = f.read().decode("utf-8")
    a, b = src.splitlines(keepends=True), mod_xml.splitlines(keepends=True)
    ops = [o for o in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if o[0] != "equal"]
    if not ops or any(o[0] != "insert" for o in ops):
        raise Refus("le fichier du mod ne correspond plus au fichier du jeu (mise a jour du jeu ?) : refaire le mod")
    ajoute = "".join("".join(b[o[3]:o[4]]) for o in ops)
    blocs = re.findall(r'[ \t]*<button name="(' + re.escape(PREFIXE) + r'[a-z_]+)" [^>\r\n]*type="18"[^>\r\n]*>\r\n'
                       r'[ \t]*<transform [^>\r\n]*/>\r\n[ \t]*</button>\r\n', ajoute)
    if not blocs or len(blocs) > 2 or ajoute.count("\n") != 3 * len(blocs):
        raise Refus("les lignes ajoutees ne sont pas uniquement des copies du bouton Hold")
    ET.fromstring(mod_xml.encode("utf-8"))
    return blocs


def chemins_actifs(texte):
    return [p.get("value") for p in ET.fromstring(texte.encode("utf-8")).iter("path")]


def meme_chemin(x, y):
    return os.path.normcase(os.path.normpath(x)) == os.path.normcase(os.path.normpath(y))


def inserer_ligne(brut, chemin):
    texte = brut.decode("utf-8")
    m = re.search(r'(?P<indent>[ \t]*)<path value="[^"]*"/>(?P<nl>\r?\n)(?=[ \t]*</active_mod_folders>)', texte)
    if not m:
        raise Refus("mods.xml : structure inattendue (pas de </active_mod_folders> apres une ligne <path>)")
    ligne = '%s<path value="%s"/>%s' % (m.group("indent"), chemin, m.group("nl"))
    nouveau = texte[:m.end()] + ligne + texte[m.end():]
    if chemins_actifs(nouveau) != chemins_actifs(texte) + [chemin]:
        raise Refus("mods.xml : verification apres insertion ratee")
    return nouveau.encode("utf-8")


def retirer_ligne(brut, chemin):
    texte = brut.decode("utf-8")
    motif = re.compile(r'[ \t]*<path value="' + re.escape(chemin) + r'"/>\r?\n')
    if len(motif.findall(texte)) != 1:
        return None
    nouveau = motif.sub("", texte, count=1)
    attendu = [p for p in chemins_actifs(texte) if p != chemin]
    if chemins_actifs(nouveau) != attendu:
        raise Refus("mods.xml : verification apres retrait ratee")
    return nouveau.encode("utf-8")


def ecrire_verifie(chemin, octets):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    tmp = chemin + ".tmp_hold"
    with open(tmp, "wb") as f:
        f.write(octets)
    with open(tmp, "rb") as f:
        if f.read() != octets:
            os.remove(tmp)
            raise Refus("relecture differente de ce qui a ete ecrit : %s" % chemin)
    os.replace(tmp, chemin)


def contexte(a):
    appdata = a.appdata or os.path.join(os.environ["APPDATA"], "Carrier Command 2")
    return appdata, os.path.join(appdata, "mods.xml"), os.path.join(appdata, "mods", NOM_MOD)


def verifier_pose_possible(a, appdata, mods_xml, cible):
    if jeu_ouvert():
        raise Refus("un processus carrier_command* tourne : le fermer d'abord")
    fichiers = lire_mod(a.mod)
    blocs = controler_mod_contre_jeu(fichiers, a.jeu)
    with open(mods_xml, "rb") as f:
        brut = f.read()
    actifs = chemins_actifs(brut.decode("utf-8"))
    if os.path.exists(cible) or any(meme_chemin(p, cible) for p in actifs):
        raise Refus("le mod est deja pose (dossier ou ligne de mods.xml present)")
    for p in actifs:
        if os.path.isfile(os.path.join(p, XML_RELATIF)):
            raise Refus("le mod actif %s remplace deja ce fichier du jeu : un seul mod peut le faire" % p)
    return fichiers, blocs, brut, actifs


def sauvegarde_de(mods_xml, suffixe):
    return "%s.bak_%s_%s" % (mods_xml, datetime.date.today().isoformat(), suffixe)


def cmd_etat(a):
    appdata, mods_xml, cible = contexte(a)
    print("jeu lance               :", jeu_ouvert())
    fichiers = lire_mod(a.mod)
    print("mod (dossier source)    : 3 fichiers, copies du bouton :", controler_mod_contre_jeu(fichiers, a.jeu))
    with open(mods_xml, "rb") as f:
        brut = f.read()
    actifs = chemins_actifs(brut.decode("utf-8"))
    print("mods.xml                : %s, %d mods actifs, sha256 %s" % (mods_xml, len(actifs), sha(brut)[:8]))
    print("mod pose (dossier)      :", os.path.isdir(cible))
    print("mod actif (ligne)       :", any(meme_chemin(p, cible) for p in actifs))
    print("autre mod sur ce fichier:", [p for p in actifs if not meme_chemin(p, cible) and os.path.isfile(os.path.join(p, XML_RELATIF))] or "aucun")


def cmd_poser(a):
    appdata, mods_xml, cible = contexte(a)
    fichiers, blocs, brut, actifs = verifier_pose_possible(a, appdata, mods_xml, cible)
    nouveau = inserer_ligne(brut, cible)
    sauv = sauvegarde_de(mods_xml, "hold")
    if os.path.exists(sauv):
        raise Refus("la sauvegarde %s existe deja : on n'ecrase jamais" % sauv)
    print("Plan : copier le mod (%d copies du bouton : %s) dans %s ; sauvegarder mods.xml -> %s ; ajouter UNE ligne a mods.xml."
          % (len(blocs), ", ".join(blocs), cible, os.path.basename(sauv)))
    if a.a_blanc:
        print("A BLANC : rien ecrit.")
        return
    try:
        for rel, contenu in fichiers.items():
            ecrire_verifie(os.path.join(cible, rel), contenu)
    except Exception:
        shutil.rmtree(cible, ignore_errors=True)
        raise
    ecrire_verifie(sauv, brut)
    ecrire_verifie(mods_xml, nouveau)
    with open(mods_xml, "rb") as f:
        assert f.read() == nouveau
    print("POSE TERMINEE. mods.xml : %s -> %s ; sauvegarde %s (%s)." % (sha(brut)[:8], sha(nouveau)[:8], os.path.basename(sauv), sha(brut)[:8]))
    print("Retrait : python -I -B poser_mod_hold.py retirer --mod ... --jeu ...  (ou restaurer la sauvegarde, jeu ferme).")


def cmd_retirer(a):
    appdata, mods_xml, cible = contexte(a)
    if jeu_ouvert():
        raise Refus("un processus carrier_command* tourne : le fermer d'abord")
    fichiers = lire_mod(a.mod)
    with open(mods_xml, "rb") as f:
        brut = f.read()
    nouveau = retirer_ligne(brut, cible)
    dossier_ok = os.path.isdir(cible)
    identique = dossier_ok and all(os.path.isfile(os.path.join(cible, r)) and open(os.path.join(cible, r), "rb").read() == c
                                   for r, c in fichiers.items())
    print("Plan : %s ; %s." % ("retirer la ligne de mods.xml" if nouveau else "pas de ligne a retirer dans mods.xml",
                                "supprimer le dossier du mod (identique a la source)" if identique else
                                ("dossier du mod DIFFERENT de la source : il ne sera pas supprime" if dossier_ok else "pas de dossier a supprimer")))
    if a.a_blanc:
        print("A BLANC : rien ecrit.")
        return
    if nouveau is not None:
        sauv = sauvegarde_de(mods_xml, "hold_avant_retrait")
        if not os.path.exists(sauv):
            ecrire_verifie(sauv, brut)
        ecrire_verifie(mods_xml, nouveau)
    if identique:
        shutil.rmtree(cible)
    print("RETRAIT TERMINE.")


# ------------------------------------------------------------------ autotest
def _xml(blocs=""):
    hold = ('\t\t<button name="vehicle_control_air_hold" display_name_loc="1527" button_panel_index="0" type="18" help_tag="x">\r\n'
            '\t\t\t<transform m00="1" tx="0" ty="0" tz="0"/>\r\n\t\t</button>\r\n')
    return '<?xml version="1.0" encoding="UTF-8"?>\r\n<vehicle>\r\n\t<buttons>\r\n' + hold + blocs + '\t</buttons>\r\n</vehicle>\r\n'


def _copie(nom, panneau):
    return ('\t\t<button name="%s%s" display_name_loc="1527" button_panel_index="%d" type="18" help_tag="x">\r\n'
            '\t\t\t<transform m00="1" tx="1" ty="1" tz="1"/>\r\n\t\t</button>\r\n' % (PREFIXE, nom, panneau))


def _monde(racine, nl="\r\n"):
    jeu = os.path.join(racine, "jeu")
    appdata = os.path.join(racine, "appdata")
    mod = os.path.join(racine, "mod")
    os.makedirs(os.path.join(jeu, "rom_0", "game_objects"))
    os.makedirs(os.path.join(mod, "content", "game_objects"))
    os.makedirs(os.path.join(appdata, "mods", "autre"))
    with open(os.path.join(jeu, XML_JEU), "wb") as f:
        f.write(_xml().encode())
    with open(os.path.join(mod, XML_RELATIF), "wb") as f:
        f.write(_xml(_copie("moteur", 8) + _copie("feux", 7)).encode())
    for n in ("mod.xml", "thumbnail.png"):
        with open(os.path.join(mod, n), "wb") as f:
            f.write(b"x")
    texte = ('<?xml version="1.0" encoding="UTF-8"?>%s<data>%s\t<active_mod_folders>%s\t\t<path value="C:\\w\\1"/>%s\t\t<path value="%s"/>%s'
             '\t</active_mod_folders>%s</data>' % (nl, nl, nl, nl, os.path.join(appdata, "mods", "autre"), nl, nl))
    with open(os.path.join(appdata, "mods.xml"), "wb") as f:
        f.write(texte.encode())
    return jeu, appdata, mod


def autotest():
    global JEU_OUVERT_FORCE
    echecs = []

    def verif(nom, cond):
        print(("OK     " if cond else "ECHEC  ") + nom)
        if not cond:
            echecs.append(nom)

    def refuse(f, *args):
        try:
            f(*args)
        except Refus:
            return True
        return False

    class A:
        a_blanc = False

        def __init__(self, jeu, appdata, mod):
            self.jeu, self.appdata, self.mod = jeu, appdata, mod

    JEU_OUVERT_FORCE = False
    for nl in ("\r\n", "\n"):
        with tempfile.TemporaryDirectory() as t:
            jeu, appdata, mod = _monde(t, nl)
            a = A(jeu, appdata, mod)
            mx = os.path.join(appdata, "mods.xml")
            avant = open(mx, "rb").read()
            cible = os.path.join(appdata, "mods", NOM_MOD)
            a.a_blanc = True
            cmd_poser(a)
            verif("[%r] a blanc : rien ecrit" % nl, open(mx, "rb").read() == avant and not os.path.exists(cible))
            a.a_blanc = False
            cmd_poser(a)
            apres = open(mx, "rb").read()
            verif("[%r] pose : dossier copie, 3 fichiers" % nl, os.path.isfile(os.path.join(cible, XML_RELATIF)))
            verif("[%r] pose : une seule ligne ajoutee en fin de liste" % nl, chemins_actifs(apres.decode()) == chemins_actifs(avant.decode()) + [cible])
            verif("[%r] pose : fins de ligne conservees" % nl, (b"\r\n" in apres) == (b"\r\n" in avant) and apres.count(b"\n") == avant.count(b"\n") + 1)
            verif("[%r] pose : sauvegarde identique a l'original" % nl, open(sauvegarde_de(mx, "hold"), "rb").read() == avant)
            verif("[%r] double pose refusee" % nl, refuse(cmd_poser, a))
            cmd_retirer(a)
            verif("[%r] retrait : mods.xml identique a l'original octet pour octet" % nl, open(mx, "rb").read() == avant)
            verif("[%r] retrait : dossier supprime" % nl, not os.path.exists(cible))
    with tempfile.TemporaryDirectory() as t:
        jeu, appdata, mod = _monde(t)
        a = A(jeu, appdata, mod)
        JEU_OUVERT_FORCE = True
        verif("jeu ouvert : pose refusee", refuse(cmd_poser, a))
        JEU_OUVERT_FORCE = False
        with open(os.path.join(jeu, XML_JEU), "ab") as f:
            f.write(b"<!-- mise a jour -->\r\n")
        verif("jeu change depuis la fabrication du mod : pose refusee", refuse(cmd_poser, a))
    with tempfile.TemporaryDirectory() as t:
        jeu, appdata, mod = _monde(t)
        a = A(jeu, appdata, mod)
        os.makedirs(os.path.join(appdata, "mods", "autre", "content", "game_objects"))
        open(os.path.join(appdata, "mods", "autre", XML_RELATIF), "wb").write(b"<x/>")
        verif("autre mod actif sur le meme fichier : pose refusee", refuse(cmd_poser, a))
    with tempfile.TemporaryDirectory() as t:
        jeu, appdata, mod = _monde(t)
        a = A(jeu, appdata, mod)
        open(sauvegarde_de(os.path.join(appdata, "mods.xml"), "hold"), "wb").write(b"deja")
        verif("sauvegarde datee deja presente : pose refusee", refuse(cmd_poser, a))
    with tempfile.TemporaryDirectory() as t:
        jeu, appdata, mod = _monde(t)
        a = A(jeu, appdata, mod)
        open(os.path.join(mod, "intrus.txt"), "wb").write(b"x")
        verif("fichier en trop dans le mod : pose refusee", refuse(cmd_poser, a))
    with tempfile.TemporaryDirectory() as t:
        jeu, appdata, mod = _monde(t)
        a = A(jeu, appdata, mod)
        with open(os.path.join(mod, XML_RELATIF), "wb") as f:
            f.write(_xml(_copie("moteur", 8)).replace("<buttons>", "<buttons><x/>").encode())
        verif("mod qui change autre chose qu'une copie du bouton : pose refusee", refuse(cmd_poser, a))
    JEU_OUVERT_FORCE = None
    print("%d echec(s)" % len(echecs))
    return 0 if not echecs else 1


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], allow_abbrev=False)
    p.add_argument("commande", choices=("etat", "poser", "retirer", "autotest"))
    p.add_argument("--mod")
    p.add_argument("--jeu")
    p.add_argument("--appdata", help="reserve aux essais : par defaut %%APPDATA%%\\Carrier Command 2")
    p.add_argument("--a-blanc", action="store_true")
    a = p.parse_args()
    if a.commande == "autotest":
        return autotest()
    if not a.mod or not a.jeu:
        p.error("--mod et --jeu sont obligatoires")
    try:
        {"etat": cmd_etat, "poser": cmd_poser, "retirer": cmd_retirer}[a.commande](a)
    except (Refus, OSError) as e:
        print("REFUSE : %s" % e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
