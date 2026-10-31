#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch workshop for Carrier Command 2 (Mac build): one tool for all the changes.

Each change is a MODULE (a file in outil/modules/) of one of these two types:
  - "programme" : byte patches in the game executable (MacOS/build_mac);
  - "fichier"   : replacement of a file in rom_0 (Lua script, graphics effect...).
Modules can be enabled and removed independently; the tool checks that they never touch
the same bytes or the same file.

Usage:
  patchs_cc2.py                       -> status of each module
  patchs_cc2.py --activer NAME [NAME..] -> enables these modules
  patchs_cc2.py --retirer NAME [NAME..] -> removes them
  patchs_cc2.py --origine             -> removes everything (original executable and files)
  patchs_cc2.py --menu                -> menu (this is what the double-click launcher runs)
For tests: --programme PATH, --rom FOLDER, --modules FOLDER, --sauvegarde PATH
(they work on copies; the "game closed" check is then skipped).

Safeguards:
  - refuses to run while the game is running;
  - refuses to touch the executable unless it is exactly the one that was analysed (once all
    modules are reverted to original, its md5 must be MD5_ORIGINE): after a Steam update, the
    analysis has to be redone;
  - a module whose bytes are neither all original nor all modified is "damaged": refused;
  - keeps a copy of the original executable (rebuilt, hence always the true one) and of the
    original files that were replaced; writes through a temporary file; reads back and checks.
"""
import hashlib, importlib.util, os, shutil, struct, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.dirname(ICI)
APP = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents")
PROGRAMME = os.path.join(APP, "MacOS", "build_mac")
ROM = os.path.join(APP, "Resources", "rom_0")
MODULES = os.path.join(ICI, "modules")
FICHIERS = os.path.join(DOSSIER, "fichiers")
SAUVEGARDE = os.path.join(DOSSIER, "sauvegarde", "build_mac_origine")
SAUVEGARDE_ROM = os.path.join(DOSSIER, "sauvegarde", "rom_0")

MD5_ORIGINE = "b0107170ddaf0245cbfee8a2d876aeb6"   # build_mac of 2026-01-05 (Steam)
BASE = 0x100000000                                   # x86_64-only binary: offset = address - BASE


class Refus(Exception):
    pass


# ---------------------------------------------------------------- common helpers

def md5(donnees):
    return hashlib.md5(donnees).hexdigest()


def sha256(donnees):
    return hashlib.sha256(donnees).hexdigest()


def lire(chemin):
    with open(chemin, "rb") as f:
        return f.read()


def ecrire(chemin, donnees):
    tmp = chemin + ".tmp_patchs_cc2"
    with open(tmp, "wb") as f:
        f.write(donnees)
    if os.path.exists(chemin):
        shutil.copymode(chemin, tmp)
    os.replace(tmp, chemin)


def lire_f32(donnees, va):
    return struct.unpack_from("<f", donnees, va - BASE)[0]


# ---------------------------------------------------------------- modules

def charger_modules(dossier):
    modules = []
    for nom in sorted(os.listdir(dossier)):
        if not nom.endswith(".py") or nom.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location("module_cc2_" + nom[:-3], os.path.join(dossier, nom))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        if m.TYPE not in ("programme", "fichier"):
            raise Refus("module %s: unknown type %r" % (nom, m.TYPE))
        modules.append(m)
    noms = [m.NOM for m in modules]
    if len(set(noms)) != len(noms):
        raise Refus("two modules have the same name")
    return modules


def retouches(module, donnees):
    """List of (offset, original bytes, modified bytes) of a "programme" module, checked.

    The module provides RETOUCHES: tuples
      ("imm", address, original_bytes_hex, modified_bytes_hex)
      ("rip", address, original_bytes_hex, old_constant, new_constant, factor)
    "rip" = instruction that reads a constant by RIP-relative address (disp32 at the end of the
    instruction): we redirect it to another constant already present in the game; if factor is
    not None, we check that new value == factor x old value (exact float).
    """
    liste = []
    for r in module.RETOUCHES:
        if r[0] == "imm":
            _, va, avant, apres = r
            avant, apres = bytes.fromhex(avant), bytes.fromhex(apres)
            if len(avant) != len(apres):
                raise Refus("%s: patch %#x changes the length" % (module.NOM, va))
        elif r[0] == "rip":
            _, va, avant, vieux, neuf, facteur = r
            avant = bytes.fromhex(avant)
            fin = va + len(avant)
            if int.from_bytes(avant[-4:], "little", signed=True) != vieux - fin:
                raise Refus("%s: the instruction at %#x does not read %#x" % (module.NOM, va, vieux))
            if facteur is not None and lire_f32(donnees, neuf) != facteur * lire_f32(donnees, vieux):
                raise Refus("%s: %#x is not %s x %#x" % (module.NOM, neuf, facteur, vieux))
            apres = avant[:-4] + (neuf - fin).to_bytes(4, "little", signed=True)
        else:
            raise Refus("%s: unknown patch type %r" % (module.NOM, r[0]))
        liste.append((va - BASE, avant, apres))
    return liste


def verifier_chevauchements(tables):
    occupe = {}
    for nom, table in tables.items():
        for o, a, _ in table:
            for i in range(o, o + len(a)):
                if i in occupe and occupe[i] != nom:
                    raise Refus("modules %s and %s touch the same bytes (%#x)"
                                % (occupe[i], nom, i + BASE))
                occupe[i] = nom


def etat_programme(donnees, table):
    if all(donnees[o:o + len(a)] == a for o, a, _ in table):
        return "retire"
    if all(donnees[o:o + len(b)] == b for o, _, b in table):
        return "actif"
    return "abime"


def etat_fichier(module, rom):
    cible = os.path.join(rom, module.CIBLE)
    if not os.path.isfile(cible):
        return "absent"
    h = sha256(lire(cible))
    if h == sha256(lire(os.path.join(FICHIERS, module.SOURCE))):
        return "actif"
    if h == module.ORIGINE_SHA256:
        return "retire"
    return "inconnu"


# ---------------------------------------------------------------- the work

class Atelier:
    def __init__(self, programme, rom, dossier_modules, sauvegarde, sauvegarde_rom):
        self.programme, self.rom = programme, rom
        self.sauvegarde, self.sauvegarde_rom = sauvegarde, sauvegarde_rom
        self.modules = {m.NOM: m for m in charger_modules(dossier_modules)}
        cibles = [m.CIBLE for m in self.modules.values() if m.TYPE == "fichier"]
        if len(set(cibles)) != len(cibles):
            raise Refus("two modules replace the same file")
        self.donnees = bytearray(lire(programme))
        self.tables = {n: retouches(m, self.donnees) for n, m in self.modules.items() if m.TYPE == "programme"}
        verifier_chevauchements(self.tables)

    def original_reconstruit(self):
        d = bytearray(self.donnees)
        for table in self.tables.values():
            for o, a, _ in table:
                d[o:o + len(a)] = a
        return d

    def programme_reconnu(self):
        return md5(self.original_reconstruit()) == MD5_ORIGINE

    def etats(self):
        res = {}
        for n, m in self.modules.items():
            res[n] = etat_programme(self.donnees, self.tables[n]) if m.TYPE == "programme" else etat_fichier(m, self.rom)
        return res

    def appliquer(self, voulus):
        """voulus: {name: True (active) / False (removed)}. Does nothing if everything is already in the wanted state."""
        etats = self.etats()
        for n in voulus:
            if n not in self.modules:
                raise Refus("unknown module: %s (known: %s)" % (n, ", ".join(self.modules)))
        a_faire = {n: v for n, v in voulus.items() if etats[n] != ("actif" if v else "retire")}
        if not a_faire:
            return []
        prog = [n for n in a_faire if self.modules[n].TYPE == "programme"]
        if prog:
            if not self.programme_reconnu():
                raise Refus("the game executable is not the one that was analysed (Steam update?). Nothing was touched.")
            for n in prog:
                if etats[n] == "abime":
                    raise Refus("module %s is damaged (neither all original nor all modified). Nothing was touched." % n)
        for n in a_faire:
            m = self.modules[n]
            if m.TYPE == "fichier" and etats[n] not in ("actif", "retire"):
                raise Refus("%s: file %s contains something other than the original or our version. Nothing was touched."
                            % (n, m.CIBLE))

        if prog:
            if not os.path.isfile(self.sauvegarde):
                os.makedirs(os.path.dirname(self.sauvegarde), exist_ok=True)
                ecrire(self.sauvegarde, bytes(self.original_reconstruit()))
            for n in prog:
                for o, a, b in self.tables[n]:
                    self.donnees[o:o + len(a)] = b if a_faire[n] else a
            ecrire(self.programme, bytes(self.donnees))
            self.donnees = bytearray(lire(self.programme))

        for n in a_faire:
            m = self.modules[n]
            if m.TYPE != "fichier":
                continue
            cible = os.path.join(self.rom, m.CIBLE)
            copie = os.path.join(self.sauvegarde_rom, m.CIBLE)
            if a_faire[n]:
                if not os.path.isfile(copie):
                    os.makedirs(os.path.dirname(copie), exist_ok=True)
                    shutil.copy2(cible, copie)
                ecrire(cible, lire(os.path.join(FICHIERS, m.SOURCE)))
            else:
                if os.path.isfile(copie) and sha256(lire(copie)) == m.ORIGINE_SHA256:
                    ecrire(cible, lire(copie))
                elif m.ORIGINE_SHA256 == sha256(b""):
                    ecrire(cible, b"")
                else:
                    raise Refus("%s: no copy of the original %s to restore." % (n, m.CIBLE))

        apres = self.etats()
        rates = [n for n, v in a_faire.items() if apres[n] != ("actif" if v else "retire")]
        if rates:
            raise Refus("read-back does not give the expected state for: " + ", ".join(rates))
        return sorted(a_faire)


# ---------------------------------------------------------------- display

LIBELLES = {"actif": "ACTIVE", "retire": "removed (original game)", "abime": "DAMAGED",
            "inconnu": "UNKNOWN file", "absent": "MISSING file"}


def afficher(atelier):
    print("\n  Patch status:")
    for n, e in atelier.etats().items():
        m = atelier.modules[n]
        print("    %-14s %-24s %s" % (n, LIBELLES[e], m.TITRE))
    if any(m.TYPE == "programme" for m in atelier.modules.values()) and not atelier.programme_reconnu():
        print("\n  WARNING: the game executable is not the one that was analysed (Steam update?).")


AVEC_VALEUR = ("--programme", "--rom", "--modules", "--sauvegarde", "--sauvegarde-rom")


def lire_arguments(argv):
    """Strict parsing: any word that is not understood is refused (never ignored, so that we do
    not silently fall back on the real game when we meant to work on a copy)."""
    opts = {"activer": [], "retirer": [], "origine": False, "menu": False}
    i, liste = 0, None
    while i < len(argv):
        a = argv[i]
        if a in AVEC_VALEUR:
            if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                raise Refus("missing path after %s" % a)
            opts[a] = argv[i + 1]
            i, liste = i + 2, None
            continue
        if a in ("--activer", "--retirer"):
            liste = opts[a[2:]]
        elif a in ("--origine", "--menu"):
            opts[a[2:]], liste = True, None
        elif liste is not None and not a.startswith("-"):
            liste.append(a)
        else:
            raise Refus("unrecognised argument: %r" % a)
        i += 1
    return opts


def ouvrir(opts):
    programme, rom = opts.get("--programme", PROGRAMME), opts.get("--rom", ROM)
    if programme == PROGRAMME and rom == ROM and \
            subprocess.run(["pgrep", "-x", "build_mac"], capture_output=True).returncode == 0:
        raise Refus("close Carrier Command 2 first.")
    return Atelier(programme, rom, opts.get("--modules", MODULES),
                   opts.get("--sauvegarde", SAUVEGARDE), opts.get("--sauvegarde-rom", SAUVEGARDE_ROM))


def faire(atelier, voulus):
    faits = atelier.appliquer(voulus)
    if faits:
        print("\n  OK: " + ", ".join(("%s %s" % (n, "enabled" if voulus[n] else "removed")) for n in faits)
              + ". Restart the game to see the effect.")
    else:
        print("\n  Nothing to do: already in that state.")


def menu(opts):
    """Menu for the double-click launcher: offers to enable or remove each module."""
    while True:
        atelier = ouvrir(opts)
        afficher(atelier)
        etats = atelier.etats()
        choix = []
        for n, e in etats.items():
            if e == "actif":
                choix.append(("Remove   " + atelier.modules[n].TITRE, {n: False}))
            elif e == "retire":
                choix.append(("Enable   " + atelier.modules[n].TITRE, {n: True}))
        choix.append(("Restore everything to original", {n: False for n in atelier.modules}))
        print("\n  What do you want to do?")
        for k, (texte, _) in enumerate(choix, 1):
            print("    %d. %s" % (k, texte))
        print("    q. Quit")
        try:
            rep = input("\n  Your choice: ").strip().lower()
        except EOFError:
            return 0
        if rep in ("q", ""):
            return 0
        if not rep.isdigit() or not 1 <= int(rep) <= len(choix):
            print("\n  Unknown choice.")
            continue
        faire(atelier, choix[int(rep) - 1][1])


def main(argv):
    print("\n  PATCH WORKSHOP - Carrier Command 2")
    print("  " + "-" * 38)
    try:
        opts = lire_arguments(argv)
        if opts["menu"]:
            return menu(opts)
        atelier = ouvrir(opts)
        voulus = {n: False for n in atelier.modules} if opts["origine"] else {}
        voulus.update({n: True for n in opts["activer"]})
        voulus.update({n: False for n in opts["retirer"]})
        if voulus:
            faire(atelier, voulus)
        afficher(atelier)
        print()
        return 0
    except Refus as e:
        print("\n  ABORTED: %s\n" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
