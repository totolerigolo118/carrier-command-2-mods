#!/usr/bin/env python3
"""Controle STRUCTUREL d'un script Lua (il n'y a pas d'interpreteur Lua sur la tour) :
retire commentaires et chaines, puis verifie que chaque function / if / for / while / do / repeat est ferme
(end / until) et que parentheses, accolades et crochets sont equilibres.
Ce n'est PAS un vrai analyseur : il attrape les `end` oublies ou en trop, pas toutes les fautes de syntaxe.

Usage : python -I verifier_blocs_lua.py fichier.lua [fichier2.lua ...]
"""
import re
import sys


def nettoyer(src):
    res, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith('--[[', i):
            j = src.find(']]', i)
            i = j + 2 if j != -1 else n
            continue
        if src.startswith('--', i):
            j = src.find('\n', i)
            i = j if j != -1 else n
            continue
        if c in ('"', "'"):
            q = c
            i += 1
            while i < n and src[i] != q:
                if src[i] == '\\':
                    i += 1
                i += 1
            i += 1
            res.append('""')
            continue
        res.append(c)
        i += 1
    return ''.join(res)


def verifier(chemin):
    code = nettoyer(open(chemin, encoding='utf-8').read())
    toks = re.findall(r'[A-Za-z_][A-Za-z_0-9]*|\S', code)
    pile, erreurs = [], []
    for t in toks:
        if t in ('function', 'if'):
            pile.append(t)
        elif t in ('for', 'while'):
            pile.append('boucle')
        elif t == 'do':
            if pile and pile[-1] == 'boucle':
                pile[-1] = 'boucle+do'
            else:
                pile.append('do')
        elif t == 'repeat':
            pile.append('repeat')
        elif t == 'until':
            if pile and pile[-1] == 'repeat':
                pile.pop()
            else:
                erreurs.append('until sans repeat')
        elif t == 'end':
            if not pile:
                erreurs.append('end EN TROP')
                break
            pile.pop()
    if pile:
        erreurs.append('blocs NON fermes : %s' % pile)
    for a, b in ('()', '{}', '[]'):
        if code.count(a) != code.count(b):
            erreurs.append('%s%s desequilibres : %d ouvertes, %d fermees' % (a, b, code.count(a), code.count(b)))
    print('%-28s %s' % (chemin.replace('\\', '/').split('/')[-1], 'OK (blocs et parentheses equilibres)' if not erreurs else 'PROBLEME : ' + '; '.join(erreurs)))
    return not erreurs


if __name__ == '__main__':
    ok = all([verifier(p) for p in sys.argv[1:]])
    sys.exit(0 if ok else 1)
