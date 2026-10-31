"""Compare, en lecture seule, les sources modifiées du SDK au clone d'origine (7ab05c7).

Usage : python -I -B comparer_sources.py <clone> <sources_ref> <sources_nouveau> <empreintes.txt>
"""
import difflib
import hashlib
import os
import sys

clone, ref, nouv, emp = sys.argv[1:5]


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# 1. empreintes épinglées vs clone
attendu = {}
for ligne in open(emp, encoding="utf-8"):
    h, nom = ligne.split(None, 1)
    attendu[nom.strip()] = h
ok = 0
for nom, h in attendu.items():
    reel = sha(os.path.join(clone, nom))
    if reel == h:
        ok += 1
    else:
        print("ECART empreinte clone :", nom, reel)
print(f"clone vs empreintes epinglees : {ok}/{len(attendu)} identiques")


def lister(racine):
    out = []
    for d, _, fs in os.walk(racine):
        for f in fs:
            out.append(os.path.relpath(os.path.join(d, f), racine).replace("\\", "/"))
    return sorted(out)


for nom_copie, copie in (("sources_ref", ref), ("sources_nouveau", nouv)):
    print(f"\n===== {nom_copie} =====")
    fichiers = lister(copie)
    print("fichiers :", fichiers)
    for rel in fichiers:
        orig = os.path.join(clone, rel)
        if not os.path.exists(orig):
            print("  ABSENT du clone :", rel)
            continue
        a = open(orig, "rb").read()
        b = open(os.path.join(copie, rel), "rb").read()
        same = a == b
        print(f"  {rel}: {len(a)} -> {len(b)} octets, sha copie {sha(os.path.join(copie, rel))[:16]}, "
              f"identique={same}, CR dans copie={b.count(b'\r')}, octets>0x7e dans copie={sum(1 for x in b if x > 0x7e)}")
        if not same:
            la = a.decode("utf-8").splitlines(keepends=True)
            lb = b.decode("utf-8").splitlines(keepends=True)
            for l in difflib.unified_diff(la, lb, "a/" + rel, "b/" + rel, n=0):
                sys.stdout.write(l if l.endswith("\n") else l + "\n")
