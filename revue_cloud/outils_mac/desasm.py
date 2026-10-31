#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Petit outil de lecture du programme d'origine, pour la feuille revue_cloud/FEUILLE_MAC_desassemblage.md.

LECTURE SEULE : il ne fait que lancer `objdump -d` (et `nm -n`) sur le fichier qu'on lui donne.
Toujours lui donner sauvegarde/build_mac_origine (md5 b0107170ddaf0245cbfee8a2d876aeb6), jamais le jeu installe.

  lire   FICHIER DEBUT FIN [--reg rdx ...] [--drapeaux]
         instructions de [DEBUT, FIN[ ; `>>` marque les lignes qui citent un des registres (toute la famille :
         rdx, edx, dx, dl, dh) ; --drapeaux ajoute [F-ecrit] / [F-lit] (HEURISTIQUE : motifs exacts de
         mnemoniques usuels, a confirmer a l'oeil).
  sauts  FICHIER DEBUT:FIN [DEBUT:FIN ...] [--scan-debut A --scan-fin B]
         en UNE passe sur tout le programme (par defaut 0x100001000..0x102858000, comme tests/test_cctv_net.py),
         liste les sauts/appels DIRECTS dont la cible tombe STRICTEMENT dans ]DEBUT, FIN[ de chaque plage (une
         entree au milieu d'un bloc qu'on remplace). Signale aussi les sauts INDIRECTS proches (tables de sauts
         possibles), que l'outil ne sait pas suivre.
  appels FICHIER CIBLE [--scan-debut A --scan-fin B]
         liste tous les sauts/appels DIRECTS qui visent exactement CIBLE (ex. le stub de glViewport).

Les adresses s'ecrivent en hexadecimal (0x1001c2b4c). Compatible objdump LLVM (Mac) et GNU (Linux).
Le nom de la fonction contenante vient de `nm -n` quand il donne quelque chose (sinon rien n'est ajoute).
"""
import argparse, bisect, re, subprocess, sys

SCAN_DEBUT, SCAN_FIN = 0x100001000, 0x102858000

# mnemoniques qui ecrivent / lisent les drapeaux : HEURISTIQUE (motifs exacts, suffixe de taille AT&T b/w/l/q permis ;
# les instructions SSE addss, xorps, andps... n'y touchent pas et ne sont donc pas reconnues)
RE_ECRIT_F = re.compile(r"(?:cmp|test|add|sub|and|or|xor|inc|dec|neg|shl|shr|sar|sal|rol|ror|adc|sbb|bt|btc|btr|bts|"
                        r"mul|imul|div|idiv)[bwlq]?|u?comis[sd]|popf[qw]?")
RE_LIT_F = re.compile(r"(?:adc|sbb)[bwlq]?|cmov\w+|set\w+|pushf[qw]?|j(?!mp)\w+")
RE_DIRECT = re.compile(r"(j[a-z]+|callq?|loop[a-z]*)\s+(?:0x)?([0-9a-f]+)\s*(?:#.*)?$")
RE_INDIRECT = re.compile(r"(j[a-z]+|callq?)\s+\*")


def famille(reg):
    reg = reg.lstrip("%").lower()
    m = re.fullmatch(r"r([abcd])x", reg)
    if m:
        c = m.group(1)
        return {"r%sx" % c, "e%sx" % c, "%sx" % c, "%sl" % c, "%sh" % c}
    m = re.fullmatch(r"r(si|di|bp|sp)", reg)
    if m:
        c = m.group(1)
        return {"r" + c, "e" + c, c, c + "l"}
    m = re.fullmatch(r"r(\d+)", reg)
    if m:
        n = m.group(1)
        return {"r" + n, "r%sd" % n, "r%sw" % n, "r%sb" % n}
    return {reg}


_OPTIONS = {}


def options_objdump(chemin):
    """--print-imm-hex existe dans l'objdump LLVM (Mac), pas dans le GNU (qui affiche deja en hexa)."""
    if chemin not in _OPTIONS:
        sonde = subprocess.run(["objdump", "--print-imm-hex", "-d", "--start-address=0", "--stop-address=1", chemin],
                               capture_output=True, text=True)
        _OPTIONS[chemin] = ["--print-imm-hex"] if sonde.returncode == 0 else []
    return _OPTIONS[chemin]


def flux_instructions(chemin, debut, fin):
    """Lit objdump LIGNE PAR LIGNE (le programme entier fait des millions d'instructions : pas de liste en memoire)."""
    cmd = ["objdump", "-d", "--no-show-raw-insn"] + options_objdump(chemin) + [
        "--start-address=%#x" % debut, "--stop-address=%#x" % fin, chemin]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for l in proc.stdout:
        m = re.match(r"\s*([0-9a-f]+):\s+(.*)", l)
        if m:
            yield int(m.group(1), 16), re.sub(r"\s*<[^>]*>", "", m.group(2).strip())
    erreur = proc.stderr.read()
    if proc.wait() != 0:
        sys.exit("objdump a echoue : " + erreur.strip()[:300])


def desassembler(chemin, debut, fin):
    return list(flux_instructions(chemin, debut, fin))


class Symboles:
    """Nom de la fonction contenante, d'apres `nm -n` (facultatif : vide si nm ne donne rien)."""

    def __init__(self, chemin):
        self.adr, self.nom = [], []
        try:
            r = subprocess.run(["nm", "-n", chemin], capture_output=True, text=True)
        except OSError:
            return
        for l in r.stdout.splitlines():
            m = re.match(r"([0-9a-f]{8,16})\s+[A-Za-z]\s+(\S+)$", l)
            if m:
                self.adr.append(int(m.group(1), 16))
                self.nom.append(m.group(2))

    def de(self, adresse):
        i = bisect.bisect_right(self.adr, adresse) - 1
        if i < 0 or adresse - self.adr[i] > 0x20000:
            return ""
        return "  [%s+%#x]" % (self.nom[i], adresse - self.adr[i])


def mnemonique(texte):
    return texte.split()[0] if texte.split() else ""


def drapeaux(texte):
    mn = mnemonique(texte)
    etiquettes = []
    if RE_LIT_F.fullmatch(mn):
        etiquettes.append("[F-lit]")
    if RE_ECRIT_F.fullmatch(mn):
        etiquettes.append("[F-ecrit]")
    return " ".join(etiquettes)


def commande_lire(a):
    regs = set()
    for r in a.reg or []:
        regs |= famille(r)
    for adresse, texte in desassembler(a.fichier, a.debut, a.fin):
        cites = set(re.findall(r"%([a-z0-9]+)", texte))
        marque = ">>" if regs & cites else "  "
        extra = ("  " + drapeaux(texte)) if a.drapeaux and drapeaux(texte) else ""
        print("%s %#x  %s%s" % (marque, adresse, texte, extra))


class Parcours:
    """Parcourt tout le programme en flux et compte les instructions lues."""

    def __init__(self, a):
        self.a, self.n = a, 0

    def __iter__(self):
        for x in flux_instructions(self.a.fichier, self.a.scan_debut, self.a.scan_fin):
            self.n += 1
            yield x

    def bilan(self):
        print("%d instructions lues entre %#x et %#x" % (self.n, self.a.scan_debut, self.a.scan_fin))
        if not self.n:
            sys.exit("ATTENTION : aucune instruction lue (mauvais fichier ou mauvaise plage ?)")


def commande_sauts(a):
    plages = []
    for p in a.plages:
        d, f = p.split(":")
        d, f = adresse(d), adresse(f)
        if d >= f:
            sys.exit("plage %s : DEBUT doit etre plus petit que FIN" % p)
        plages.append((d, f))
    sym = Symboles(a.fichier)
    trouves = {p: [] for p in plages}
    indirects = {p: [] for p in plages}
    parcours = Parcours(a)
    for adr, texte in parcours:
        m = RE_DIRECT.match(texte)
        if m:
            cible = int(m.group(2), 16)
            for d, f in plages:
                if d < cible < f:
                    trouves[(d, f)].append((adr, cible, texte))
        elif RE_INDIRECT.match(texte):
            for d, f in plages:
                if d - 0x4000 <= adr <= f + 0x4000:
                    indirects[(d, f)].append((adr, texte))
    parcours.bilan()
    for d, f in plages:
        print("\n== plage ]%#x, %#x[ : %d saut(s)/appel(s) direct(s) vers l'INTERIEUR" % (d, f, len(trouves[(d, f)])))
        for src, cible, texte in trouves[(d, f)]:
            print("   %#x  %-28s -> %#x (+%#x)%s" % (src, texte, cible, cible - d, sym.de(src)))
        print("   indirects a moins de 0x4000 octets (a regarder a la main : table de sauts ?) : %d"
              % len(indirects[(d, f)]))
        for src, texte in indirects[(d, f)]:
            print("   %#x  %s%s" % (src, texte, sym.de(src)))
    print("\n(Une entree au debut exact d'une plage n'est pas comptee : c'est l'entree normale.)")


def commande_appels(a):
    sym = Symboles(a.fichier)
    n = 0
    parcours = Parcours(a)
    for adr, texte in parcours:
        m = RE_DIRECT.match(texte)
        if m and int(m.group(2), 16) == a.cible:
            n += 1
            print("   %#x  %s%s" % (adr, texte, sym.de(adr)))
    parcours.bilan()
    print("%d appel(s)/saut(s) direct(s) vers %#x" % (n, a.cible))


def adresse(s):
    return int(s, 0)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    l = sp.add_parser("lire")
    l.add_argument("fichier"); l.add_argument("debut", type=adresse); l.add_argument("fin", type=adresse)
    l.add_argument("--reg", action="append"); l.add_argument("--drapeaux", action="store_true")
    s = sp.add_parser("sauts")
    s.add_argument("fichier"); s.add_argument("plages", nargs="+", metavar="DEBUT:FIN")
    c = sp.add_parser("appels")
    c.add_argument("fichier"); c.add_argument("cible", type=adresse)
    for x in (s, c):
        x.add_argument("--scan-debut", type=adresse, default=SCAN_DEBUT)
        x.add_argument("--scan-fin", type=adresse, default=SCAN_FIN)
    a = p.parse_args()
    {"lire": commande_lire, "sauts": commande_sauts, "appels": commande_appels}[a.cmd](a)


if __name__ == "__main__":
    main()
