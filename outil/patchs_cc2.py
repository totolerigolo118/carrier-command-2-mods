#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atelier de patchs de Carrier Command 2 (version Mac) : un seul outil pour tous les changements.

Chaque changement est un MODULE (un fichier dans outil/modules/) de l'un de ces deux types :
  - "programme" : retouches d'octets dans le programme du jeu (MacOS/build_mac) ;
  - "fichier"   : remplacement d'un fichier de rom_0 (script Lua, effet graphique...).
Les modules s'activent et se retirent independamment ; l'outil verifie qu'ils ne touchent
jamais les memes octets ni le meme fichier.

Usage :
  patchs_cc2.py                       -> etat de chaque module
  patchs_cc2.py --activer NOM [NOM..] -> active ces modules
  patchs_cc2.py --retirer NOM [NOM..] -> les retire
  patchs_cc2.py --origine             -> retire tout (programme et fichiers d'origine)
  patchs_cc2.py --menu                -> menu (c'est ce que lance le bouton a double-cliquer)
Pour les tests : --programme CHEMIN, --rom DOSSIER, --modules DOSSIER, --sauvegarde CHEMIN
(travaillent sur des copies ; la verification « jeu ferme » est alors sautee).

Securites :
  - refuse si le jeu tourne ;
  - refuse de toucher au programme s'il n'est pas exactement celui analyse (une fois tous les
    modules remis d'origine, son md5 doit etre MD5_ORIGINE) : apres une mise à jour Steam, il
    faudra refaire l'analyse ;
  - un module dont les octets ne sont ni tous d'origine ni tous modifies est « abime » : refus ;
  - garde une copie du programme d'origine (reconstruite, donc toujours la vraie) et des
    fichiers d'origine remplaces ; ecrit via un fichier temporaire ; relit et controle.
"""
import hashlib, importlib.util, os, shutil, struct, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.dirname(ICI)
APP = "/Users/UTILISATEUR/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents"
PROGRAMME = os.path.join(APP, "MacOS", "build_mac")
ROM = os.path.join(APP, "Resources", "rom_0")
MODULES = os.path.join(ICI, "modules")
FICHIERS = os.path.join(DOSSIER, "fichiers")
SAUVEGARDE = os.path.join(DOSSIER, "sauvegarde", "build_mac_origine")
SAUVEGARDE_ROM = os.path.join(DOSSIER, "sauvegarde", "rom_0")

MD5_ORIGINE = "b0107170ddaf0245cbfee8a2d876aeb6"   # build_mac du 05/01/2026 (Steam)
BASE = 0x100000000                                   # binaire x86_64 seul : offset = adresse - BASE


class Refus(Exception):
    pass


# ---------------------------------------------------------------- outils communs

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
            raise Refus("module %s : type inconnu %r" % (nom, m.TYPE))
        modules.append(m)
    noms = [m.NOM for m in modules]
    if len(set(noms)) != len(noms):
        raise Refus("deux modules portent le meme nom")
    return modules


def retouches(module, donnees):
    """Liste de (offset, octets d'origine, octets modifies) d'un module « programme », verifiee.

    Le module fournit RETOUCHES : des tuples
      ("imm", adresse, octets_origine_hex, octets_modifies_hex)
      ("rip", adresse, octets_origine_hex, ancienne_constante, nouvelle_constante, facteur)
    « rip » = instruction qui lit une constante par adresse relative (disp32 en fin d'instruction) :
    on la redirige vers une autre constante deja presente dans le jeu ; si facteur n'est pas None,
    on verifie que nouvelle valeur == facteur x ancienne (float exact).
    """
    liste = []
    for r in module.RETOUCHES:
        if r[0] == "imm":
            _, va, avant, apres = r
            avant, apres = bytes.fromhex(avant), bytes.fromhex(apres)
            if len(avant) != len(apres):
                raise Refus("%s : retouche %#x de longueur variable" % (module.NOM, va))
        elif r[0] == "rip":
            _, va, avant, vieux, neuf, facteur = r
            avant = bytes.fromhex(avant)
            fin = va + len(avant)
            if int.from_bytes(avant[-4:], "little", signed=True) != vieux - fin:
                raise Refus("%s : l'instruction %#x ne lit pas %#x" % (module.NOM, va, vieux))
            if facteur is not None and lire_f32(donnees, neuf) != facteur * lire_f32(donnees, vieux):
                raise Refus("%s : %#x ne vaut pas %s x %#x" % (module.NOM, neuf, facteur, vieux))
            apres = avant[:-4] + (neuf - fin).to_bytes(4, "little", signed=True)
        else:
            raise Refus("%s : retouche de type inconnu %r" % (module.NOM, r[0]))
        liste.append((va - BASE, avant, apres))
    return liste


def verifier_chevauchements(tables):
    occupe = {}
    for nom, table in tables.items():
        for o, a, _ in table:
            for i in range(o, o + len(a)):
                if i in occupe and occupe[i] != nom:
                    raise Refus("les modules %s et %s touchent les memes octets (%#x)"
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


# ---------------------------------------------------------------- le travail

class Atelier:
    def __init__(self, programme, rom, dossier_modules, sauvegarde, sauvegarde_rom):
        self.programme, self.rom = programme, rom
        self.sauvegarde, self.sauvegarde_rom = sauvegarde, sauvegarde_rom
        self.modules = {m.NOM: m for m in charger_modules(dossier_modules)}
        cibles = [m.CIBLE for m in self.modules.values() if m.TYPE == "fichier"]
        if len(set(cibles)) != len(cibles):
            raise Refus("deux modules remplacent le meme fichier")
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
        """voulus : {nom: True (actif) / False (retire)}. Ne fait rien si tout est deja dans l'etat voulu."""
        etats = self.etats()
        for n in voulus:
            if n not in self.modules:
                raise Refus("module inconnu : %s (connus : %s)" % (n, ", ".join(self.modules)))
        a_faire = {n: v for n, v in voulus.items() if etats[n] != ("actif" if v else "retire")}
        if not a_faire:
            return []
        prog = [n for n in a_faire if self.modules[n].TYPE == "programme"]
        if prog:
            if not self.programme_reconnu():
                raise Refus("le programme du jeu n'est pas celui que j'ai analyse (mise a jour Steam ?). Rien n'est touche.")
            for n in prog:
                if etats[n] == "abime":
                    raise Refus("le module %s est abime (ni tout d'origine, ni tout modifie). Rien n'est touche." % n)
        for n in a_faire:
            m = self.modules[n]
            if m.TYPE == "fichier" and etats[n] not in ("actif", "retire"):
                raise Refus("%s : le fichier %s contient autre chose que l'original ou notre version. Rien n'est touche."
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
                    raise Refus("%s : pas de copie de l'original de %s pour le remettre." % (n, m.CIBLE))

        apres = self.etats()
        rates = [n for n, v in a_faire.items() if apres[n] != ("actif" if v else "retire")]
        if rates:
            raise Refus("la relecture ne donne pas l'etat attendu pour : " + ", ".join(rates))
        return sorted(a_faire)


# ---------------------------------------------------------------- affichage

LIBELLES = {"actif": "ACTIF", "retire": "retire (jeu d'origine)", "abime": "ABIME",
            "inconnu": "fichier INCONNU", "absent": "fichier ABSENT"}


def afficher(atelier):
    print("\n  Etat des patchs :")
    for n, e in atelier.etats().items():
        m = atelier.modules[n]
        print("    %-14s %-24s %s" % (n, LIBELLES[e], m.TITRE))
    if any(m.TYPE == "programme" for m in atelier.modules.values()) and not atelier.programme_reconnu():
        print("\n  ATTENTION : le programme du jeu n'est pas celui que j'ai analyse (mise a jour Steam ?).")


AVEC_VALEUR = ("--programme", "--rom", "--modules", "--sauvegarde", "--sauvegarde-rom")


def lire_arguments(argv):
    """Analyse stricte : tout mot non compris est refuse (jamais ignore, pour ne pas retomber
    sur le vrai jeu par erreur quand on voulait travailler sur une copie)."""
    opts = {"activer": [], "retirer": [], "origine": False, "menu": False}
    i, liste = 0, None
    while i < len(argv):
        a = argv[i]
        if a in AVEC_VALEUR:
            if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                raise Refus("il manque le chemin apres %s" % a)
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
            raise Refus("argument non reconnu : %r" % a)
        i += 1
    return opts


def ouvrir(opts):
    programme, rom = opts.get("--programme", PROGRAMME), opts.get("--rom", ROM)
    if programme == PROGRAMME and rom == ROM and \
            subprocess.run(["pgrep", "-x", "build_mac"], capture_output=True).returncode == 0:
        raise Refus("ferme d'abord Carrier Command 2.")
    return Atelier(programme, rom, opts.get("--modules", MODULES),
                   opts.get("--sauvegarde", SAUVEGARDE), opts.get("--sauvegarde-rom", SAUVEGARDE_ROM))


def faire(atelier, voulus):
    faits = atelier.appliquer(voulus)
    if faits:
        print("\n  OK : " + ", ".join(("%s %s" % (n, "active" if voulus[n] else "retire")) for n in faits)
              + ". Relance le jeu pour en profiter.")
    else:
        print("\n  Rien a faire : deja dans cet etat.")


def menu(opts):
    """Menu pour le bouton a double-cliquer : propose d'activer ou de retirer chaque module."""
    while True:
        atelier = ouvrir(opts)
        afficher(atelier)
        etats = atelier.etats()
        choix = []
        for n, e in etats.items():
            if e == "actif":
                choix.append(("Retirer  " + atelier.modules[n].TITRE, {n: False}))
            elif e == "retire":
                choix.append(("Activer  " + atelier.modules[n].TITRE, {n: True}))
        choix.append(("Tout remettre d'origine", {n: False for n in atelier.modules}))
        print("\n  Que veux-tu faire ?")
        for k, (texte, _) in enumerate(choix, 1):
            print("    %d. %s" % (k, texte))
        print("    q. Quitter")
        try:
            rep = input("\n  Ton choix : ").strip().lower()
        except EOFError:
            return 0
        if rep in ("q", ""):
            return 0
        if not rep.isdigit() or not 1 <= int(rep) <= len(choix):
            print("\n  Choix inconnu.")
            continue
        faire(atelier, choix[int(rep) - 1][1])


def main(argv):
    print("\n  ATELIER DE PATCHS - Carrier Command 2")
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
        print("\n  ARRET : %s\n" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
