#!/usr/bin/env python3
"""Verifie HORS JEU demarrage_auto.lua dans un vrai Lua 5.1 (lua51.dll d'OBS, via tour/outils/lua_sonde.py) avec de FAUX appels
du jeu. Ne lance pas le jeu, n'ecrit aucun fichier.   python -I test_lua_demarrage_auto.py
Prouve la LOGIQUE d'accrochage, pas le comportement reel du jeu (les appels du jeu sont des doublures)."""
import importlib.util
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('lua_sonde', os.path.join(ICI, '..', 'outils', 'lua_sonde.py'))
ls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ls)
SRC = open(os.path.join(ICI, 'demarrage_auto.lua'), encoding='utf-8').read()
bad = 0


def verif(c, m):
    global bad
    print(('  OK  ' if c else '  ECHEC ') + m)
    if not c:
        bad += 1


def scenario(entete, armed, menu=True, actif=True, frames=((0,), (10,), (29,), (31,), (40,))):
    """entete : lignes g_da_* ajoutees en tete (comme le fait demarrage_auto.py). actif : valeur de g_is_menu_active."""
    vm = ls.VM()
    ok, t = vm.run(ls.PRELUDE, 'prelude')
    assert ok, t
    ok, t = vm.run('''
        function update_get_mod_details()
            return { { id = 1, is_enabled = true, manifest = { name = "cc2_modes" } },
                     { id = 2, is_enabled = %s, manifest = { name = "Demarrage auto" } } }
        end
        SCREEN = "screen_menu_main"
    ''' % ('true' if armed else 'false'), 'fakes')
    assert ok, t
    ok, t = vm.run(entete + SRC, 'demarrage_auto')
    assert ok, 'chargement : ' + t
    ok, t = vm.run(('g_is_menu_active = %s\n' % ('true' if actif else 'false') if menu else '')
                   + 'function update(w, h, ticks) calls.updates = (calls.updates or 0) + 1 end\nbegin_load()', 'begin')
    assert ok, t
    res = []
    for (now,) in frames:
        ok, t = vm.run('NOW = %d; update(1600, 900, 1); return table.concat(calls.events, ",")' % now, 'frame')
        assert ok, t
        res.append((now, t))
    ok, txt = vm.run('return tostring(calls.last_text)', 'txt')
    # verrou : un autre "contexte" tente de demarrer apres coup
    ok, t2 = vm.run('g_da_fini = false; g_da_envoye = false; g_da_e0 = 0; NOW = 100; update(1600, 900, 1); return table.concat(calls.events, ",")', 'second')
    vm.close()
    return res, txt, t2


print('--- 1. menu, mod coche : rien avant 30 s, une seule demande apres')
res, txt, t2 = scenario('', True)
print('   ', res)
verif(all(ev == '' for now, ev in res if now < 30), 'aucune commande avant 30 s')
verif(res[-1][1] == 'new_game_custom', 'une commande new_game_custom apres 30 s (et une seule)')
verif('commande envoyee' in txt, 'apres la commande, un message reste affiche (diagnostic : s\'il reste, la commande a ete ignoree)')
verif(t2 == 'new_game_custom', 'un 2e contexte qui tente ensuite est bloque par le verrou (toujours une seule commande)')
res, txt, t2 = scenario('', True, frames=((0,), (10,)))
verif('DEMARRAGE AUTO dans' in txt, 'le compte a rebours s\'affiche pendant l\'attente')
print('--- 2. menu, mod PAS coche : jamais rien')
res, txt, t2 = scenario('', False)
verif(all(ev == '' for now, ev in res) and t2 == '', 'aucune commande, aucun affichage')
print('--- 3. contexte de partie (pas de g_is_menu_active) : rien du tout')
res, txt, t2 = scenario('', True, menu=False)
verif(all(ev == '' for now, ev in res) and t2 == '', 'aucune accroche, aucune commande')
print('--- 4. parametres de l\'outil (lignes g_da_* en tete)')
res, txt, t2 = scenario('g_da_mode = "charger"\ng_da_slot = 19\n', True)
verif(res[-1][1] == 'load_game:19', 'MODE charger : load_game 19 demande apres 30 s')
res, txt, t2 = scenario('g_da_mode = "charger"\ng_da_slot = 7\n', True)
verif(res[-1][1] == '', 'sauvegarde absente (slot 7 inconnu du faux jeu) : aucune commande')
res, txt, t2 = scenario('g_da_attente = 8\n', True, frames=((0,), (7,), (9,)))
verif([ev for now, ev in res] == ['', '', 'new_game_custom'], 'attente reglee a 8 s : commande entre 7 s et 9 s')
print('--- 5. attendre l\'ecran-titre (g_da_attendre_menu)')
res, txt, t2 = scenario('g_da_attendre_menu = true\n', True, actif=False, frames=((0,), (50,), (100,)))
verif(all(ev == '' for now, ev in res), 'ecran-titre encore la (g_is_menu_active faux) : le compte a rebours ne part pas')
vm = ls.VM()
ok, t = vm.run(ls.PRELUDE, 'prelude'); assert ok, t
ok, t = vm.run('function update_get_mod_details() return { { id = 2, is_enabled = true, manifest = { name = "Demarrage auto" } } } end', 'f'); assert ok, t
ok, t = vm.run('g_da_attendre_menu = true\n' + SRC, 'src'); assert ok, t
ok, t = vm.run('g_is_menu_active = false\nfunction update(w, h, t) end\nbegin_load()', 'b'); assert ok, t
suite = []
for now, actif in ((0, 'false'), (100, 'true'), (120, 'true'), (131, 'true')):
    ok, t = vm.run('NOW = %d; g_is_menu_active = %s; update(1600, 900, 1); return table.concat(calls.events, ",")' % (now, actif), 'frame')
    suite.append(t)
vm.close()
verif(suite == ['', '', '', 'new_game_custom'], 'une touche passe l\'ecran-titre a 100 s : la commande part 30 s plus tard (131 s), pas avant')
print('TOUT EST OK' if bad == 0 else '%d ECHEC(S)' % bad)
sys.exit(1 if bad else 0)
