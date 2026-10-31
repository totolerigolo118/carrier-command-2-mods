#!/usr/bin/env python3
"""Tests de lua_syntaxe.py : cas qui doivent passer, cas qui doivent echouer (avec la bonne ligne).

    python -I test_lua_syntaxe.py          (aucun programme tiers, rien n'est execute)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lua_syntaxe import verifier_texte  # noqa: E402

BONS = {
    'vide': '',
    'commentaires': '-- seul\n--[[ long\n ]] --[==[ x ]==] local a = 1',
    'nombres': 'x = 3 + 3.0 + .5 + 3e-2 + 0xFF + 0x.8p1 + 0xA.8p0 + 1e10',
    'chaines': 'x = "a\\n\\"b\\x41\\065\\u{48}\\z\n   c" .. \'q\\\'\' .. [[long\n]] .. [==[a]]b]==]',
    'affectations': 'a, b.c, d[1] = 1, 2, 3',
    'appels': 'f() f{1} f"s" f[[s]] a.b:c(1)(2){3} obj:m"x"',
    'fonctions': 'local function f(a, b, ...) return a, ... end\nfunction t.a.b:c(x) end\nlocal g = function() end',
    'boucles': 'for i = 1, 10, 2 do end for k, v in pairs(t) do break end while true do break end repeat local x = 1 until x',
    'if': 'if a then elseif b then else end',
    'goto': 'do goto fin ::fin:: end',
    'priorites': 'x = not a == b or -c ^ 2 .. d // e % f << 1 | 2 ~ 3 & 4 >> 5 <= 6',
    'unaires': 'x = - - 1 + #t + ~5 + (not nil == true)',
    'table': 't = {1, 2; 3, [4] = 5, k = 6, ["m"] = 7, f(), {}, function() end,}',
    'retour': 'return 1, 2',
    'retour_pv': 'return;',
    'retour_dans_bloc': 'do return end',
    'fonction_dans_boucle': 'while true do local f = function() return 1 end break end',
    'shebang': '#!/usr/bin/lua\nx = 1',
    'point_virgule': ';;; x = 1;',
    'appel_ligne_suivante': 'f\n(g)',
    'concat_nombre': 'x = 1 .. 2',
    'varargs': 'local function f(...) local a, b = ... return select("#", ...) end',
}

# (texte, ligne attendue de l'erreur)
MAUVAIS = {
    'end_en_trop': ('x = 1\nend', 2),
    'then_manquant': ('if a\n x = 1 end', 2),
    'end_manquant': ('if a then\n x = 1\n', 3),
    'do_manquant': ('while x\n y = 1 end', 2),
    'parenthese_non_fermee': ('x = (1 + 2\ny = 3', 2),
    'chaine_non_terminee': ('x = "abc\ny = 1', 1),
    'echappement_invalide': ('x = "\\q"', 1),
    'nombre_mal_forme': ('x = 3abc', 1),
    'nombre_deux_points': ('x = 1..2', 1),
    'hex_vide': ('x = 0x', 1),
    'break_hors_boucle': ('x = 1\nbreak', 2),
    'break_dans_fonction_dans_boucle': ('while true do\n local f = function() break end\nend', 2),
    'return_pas_dernier': ('return 1\nx = 2', 2),
    'affectation_sur_appel': ('f() = 1', 1),
    'affectation_sur_parenthese': ('(a) = 1', 1),
    'expression_inattendue': ('x = + 1', 1),
    'instruction_inattendue': ('1 + 2', 1),
    'nom_attendu': ('local = 1', 1),
    'for_incomplet': ('for i do end', 1),
    'table_non_fermee': ('t = {1, 2\nx = 1', 2),
    'attribut_const': ('local x <const> = 1', 1),
    'commentaire_long_non_ferme': ('x = 1 --[[ jamais ferme', 1),
    'caractere_inconnu': ('x = 1 @ 2', 1),
    'function_sans_nom': ('function () end', 1),
    'virgule_en_trop_param': ('function f(a,) end', 1),
    'else_isole': ('else', 1),
    'elseif_apres_else': ('if a then else elseif b then end', 1),
    'repeat_sans_until': ('repeat x = 1', 1),
    'egal_au_lieu_de_deux': ('if a = 1 then end', 1),
}


def main():
    ok = ko = 0
    for nom, texte in BONS.items():
        r = verifier_texte(texte)
        if r is None:
            ok += 1
        else:
            ko += 1
            print('ECHEC (devait passer) %-28s -> %s' % (nom, r))
    for nom, (texte, ligne) in MAUVAIS.items():
        r = verifier_texte(texte)
        if r is None:
            ko += 1
            print('ECHEC (devait echouer) %-27s -> accepte' % nom)
        elif int(r.split(':')[0]) != ligne:
            ko += 1
            print('ECHEC (mauvaise ligne) %-27s -> %s (attendu ligne %d)' % (nom, r, ligne))
        else:
            ok += 1
    print('%d reussis, %d echecs' % (ok, ko))
    return 1 if ko else 0


if __name__ == '__main__':
    sys.exit(main())
