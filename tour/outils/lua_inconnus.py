#!/usr/bin/env python3
"""Cherche les NOMS inconnus d'un script Lua (fautes de frappe dans les fonctions et variables du jeu). Rien n'est execute.

    python -I lua_inconnus.py script.lua [script2.lua ...]  [--jeu DOSSIER_DES_SCRIPTS_DU_JEU]

Principe : un nom (hors champs `a.b`, `a:b` et cles de tables `{ nom = ... }`) qui n'est ni un mot reserve, ni de la bibliotheque
standard de Lua, ni declare dans le script lui-meme (local, parametre, variable de boucle, fonction), ni present dans les scripts
du jeu (qui sont, eux, corrects), est SUSPECT : soit une faute de frappe, soit un nom qui vient d'ailleurs (le SDK : `cc2x`).
C'est une aide a la relecture, pas une preuve : il peut manquer une faute qui retombe sur un autre nom existant.
Reutilise le lexeur de lua_syntaxe.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lua_syntaxe import lex, KEYWORDS  # noqa: E402

JEU = r'C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2\rom_0\scripts'
STD = set('''_G _VERSION assert collectgarbage dofile error getmetatable ipairs load loadfile next pairs pcall print rawequal rawget
rawlen rawset require select setmetatable tonumber tostring type xpcall unpack
coroutine debug io math os package string table utf8 self arg'''.split())


def noms(chemin):
    """(noms utilises comme globaux possibles avec leur ligne, noms declares dans le fichier)"""
    texte = open(chemin, 'rb').read().decode('utf-8', errors='replace')
    toks = lex(texte)
    utilises, declares = [], set()
    n = len(toks)
    for i, t in enumerate(toks):
        if t.t != 'name':
            continue
        prec = toks[i - 1] if i else None
        suiv = toks[i + 1] if i + 1 < n else None
        if prec and prec.t == 'op' and prec.v in ('.', ':'):
            continue                                              # champ : a.b, a:b
        # declarations : local a, b / function f / function t.f(a, b) / for a, b in / parametres
        j = i
        while j > 0 and toks[j - 1].t == 'name' or (j > 1 and toks[j - 1].t == 'op' and toks[j - 1].v == ',' and toks[j - 2].t == 'name'):
            j -= 1
        debut = toks[j - 1] if j else None
        if debut and debut.t == 'kw' and debut.v in ('local', 'for'):
            declares.add(t.v)
        if prec and prec.t == 'kw' and prec.v == 'function':
            declares.add(t.v)                                     # function nom(...) : declare aussi un global du script
        if suiv and suiv.t == 'op' and suiv.v == '=' and prec and prec.t == 'op' and prec.v in ('{', ',', ';'):
            continue                                              # cle de table : { nom = ... }
        utilises.append((t.v, t.line))
    # parametres de fonctions : function ( a, b, ... )
    for i, t in enumerate(toks):
        if t.t == 'kw' and t.v == 'function':
            k = i + 1
            while k < n and not (toks[k].t == 'op' and toks[k].v == '('):
                k += 1
            k += 1
            while k < n and not (toks[k].t == 'op' and toks[k].v == ')'):
                if toks[k].t == 'name':
                    declares.add(toks[k].v)
                k += 1
    return utilises, declares


def connus_du_jeu(dossier):
    tous = set()
    for rep, _, fichiers in os.walk(dossier):
        for f in fichiers:
            if f.lower().endswith('.lua'):
                u, d = noms(os.path.join(rep, f))
                tous |= {x for x, _ in u} | d
    return tous


def main(argv):
    jeu = JEU
    if '--jeu' in argv:
        k = argv.index('--jeu')
        jeu = argv[k + 1]
        argv = argv[:k] + argv[k + 2:]
    fichiers = [a for a in argv if not a.startswith('-')]
    if not fichiers:
        print(__doc__)
        return 2
    sys.setrecursionlimit(20000)
    connus = connus_du_jeu(jeu) | STD | KEYWORDS
    print('%d noms connus (scripts du jeu : %s)' % (len(connus), jeu))
    mauvais = 0
    for f in fichiers:
        u, d = noms(f)
        vus = {}
        for nom, ligne in u:
            if nom not in connus and nom not in d:
                vus.setdefault(nom, []).append(ligne)
        print('\n%s : %s' % (f, 'aucun nom inconnu' if not vus else '%d nom(s) inconnu(s)' % len(vus)))
        for nom, lignes in sorted(vus.items()):
            print('   %-28s lignes %s' % (nom, ', '.join(map(str, lignes[:8]))))
        mauvais += len(vus)
    return 1 if mauvais else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
