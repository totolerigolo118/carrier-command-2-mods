#!/usr/bin/env python3
"""Lanceur du BANC LUA de Carrier Command 2 : fait tourner les scripts Lua de mod du depot HORS DU JEU contre une FAUSSE API.

    python tests/banc_lua/lancer.py                 contrôles statiques + tous les scénarios
    python tests/banc_lua/lancer.py --filtre SIM    seulement les scénarios dont le nom contient « SIM »
    python tests/banc_lua/lancer.py --lua CHEMIN    interpréteur Lua 5.3 à utiliser (sinon : variable LUA53, puis le PATH)
    python tests/banc_lua/lancer.py --sans-statique ne lance pas les contrôles statiques
    python tests/banc_lua/lancer.py --mutations     vérifie que le banc DÉTECTE des défauts introduits exprès (copies jetables)
    python tests/banc_lua/lancer.py --inventaire    réécrit INVENTAIRE_API.md (liste des fonctions de la fausse API et leur statut)

Dépendances : Python 3.8+ (bibliothèque standard seulement) et un interpréteur Lua 5.3 (le jeu embarque Lua 5.3.5). Aucun paquet Python,
aucun accès réseau, rien n'est écrit dans le dépôt (sauf INVENTAIRE_API.md avec --inventaire). Voir LISEZ-MOI.md.
Code de sortie : 0 si tout passe, 1 sinon, 2 si l'interpréteur Lua est introuvable ou n'est pas en version 5.3.
"""
import sys

sys.dont_write_bytecode = True      # ne pas créer de __pycache__ dans tour/outils/ en important les outils du dépôt

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:                                   # console Windows : ne jamais planter sur un caractère inconnu
    sys.stdout.reconfigure(errors='replace')
    sys.stderr.reconfigure(errors='replace')
except Exception:
    pass

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.abspath(os.path.join(ICI, '..', '..'))
OUTILS = os.path.join(RACINE, 'tour', 'outils')

SCRIPTS = [
    'tour/lua/library_custom_7.lua',
    'tour/lua/library_custom_9.lua',
    'tour/auto/library_custom_5.lua',
    'tour/etudes_demarrage_auto/demarrage_auto.lua',
    'tour/etudes_modes_carburant/lua/library_custom_3.lua',
    'tour/etudes_modes_carburant/lua/library_custom_5.lua',
    'tour/etudes_modes_carburant/lua/v2/library_custom_5.lua',
]

# Variables de réglage posées EN TÊTE de fichier par les outils d'installation (demarrage_auto.py, essai_auto.py) : lues, jamais définies
# par le script lui-même ; ce ne sont pas des fautes de frappe.
REGLAGES_FACULTATIFS = {
    'g_da_mode', 'g_da_slot', 'g_da_attente', 'g_da_attendre_menu',
    'g_ca_slot_voulu', 'g_ca_mode', 'g_ca_hud', 'g_ca_attente_menu', 'g_ca_slots',
}
# Ce qu'un script de mod ne doit jamais appeler (fichiers, processus, réseau, chargement de code) : le jeu n'a ni io ni os.
INTERDITS = {'io', 'os', 'package', 'require', 'dofile', 'loadfile', 'load', 'loadstring', 'socket', 'debug'}

DELAI_MUTANT = 120        # secondes par mutant (un mutant peut boucler à l'infini)
NOMS_LUA = ['lua5.3', 'lua53', 'lua5.3.exe', 'lua53.exe', 'lua', 'lua.exe']


# ---------------------------------------------------------------- interpréteur
def version_lua(chemin):
    try:
        r = subprocess.run([chemin, '-e', 'io.write(_VERSION)'], capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode('utf-8', 'replace').strip()


def trouver_lua(demande):
    candidats = []
    if demande:
        candidats.append(demande)
    elif os.environ.get('LUA53'):
        candidats.append(os.environ['LUA53'])
    else:
        for nom in NOMS_LUA:
            c = shutil.which(nom)
            if c:
                candidats.append(c)
    vus = []
    for c in candidats:
        v = version_lua(c)
        vus.append((c, v))
        if v == 'Lua 5.3':
            return c
    print('ERREUR : aucun interpréteur Lua 5.3 trouvé.')
    if vus:
        for c, v in vus:
            print('   essayé : %s -> %s' % (c, v or 'ne répond pas'))
    print('Ce banc vise Lua 5.3, la version embarquée dans le jeu (Lua 5.3.5) : avant 5.3 les entiers et string.format("%d") se comportent\n'
          'autrement et le banc donnerait de faux résultats. Voir LISEZ-MOI.md (« Côté PC du moddeur »).\n'
          'Indiquez l\'interpréteur avec --lua CHEMIN ou la variable d\'environnement LUA53.')
    sys.exit(2)


def lancer_lua(lua, args, racine=RACINE, capture=False, delai=None):
    cmd = [lua, os.path.join(ICI, 'banc.lua'), racine] + args
    try:
        if capture:
            r = subprocess.run(cmd, capture_output=True, timeout=delai)
            return r.returncode, r.stdout.decode('utf-8', 'replace'), r.stderr.decode('utf-8', 'replace')
        return subprocess.run(cmd, timeout=delai).returncode, '', ''
    except subprocess.TimeoutExpired:
        return 124, '', 'delai depasse (%s s)' % delai


# ---------------------------------------------------------------- contrôles statiques (outils maison du dépôt, réutilisés)
def outils_lua():
    sys.path.insert(0, OUTILS)
    import lua_syntaxe      # noqa: E402  (tour/outils/lua_syntaxe.py : vérificateur de syntaxe Lua 5.3 fait maison)
    import lua_inconnus     # noqa: E402  (tour/outils/lua_inconnus.py : noms inconnus = fautes de frappe possibles)
    sys.setrecursionlimit(20000)
    return lua_syntaxe, lua_inconnus


def controles_statiques(lua):
    """Renvoie le nombre d'échecs."""
    echecs = 0

    def verif(ok, msg):
        nonlocal echecs
        print('  %s %s' % ('OK    ' if ok else 'ECHEC ', msg))
        if not ok:
            echecs += 1

    lua_syntaxe, lua_inconnus = outils_lua()
    print('\n== Contrôles statiques (outils maison tour/outils/lua_syntaxe.py et lua_inconnus.py + vrai compilateur Lua 5.3)')

    # 0. les tests de l'outil de syntaxe lui-même
    r = subprocess.run([sys.executable, '-I', '-B', os.path.join(OUTILS, 'test_lua_syntaxe.py')], capture_output=True)
    verif(r.returncode == 0, 'tour/outils/test_lua_syntaxe.py : ' + (r.stdout.decode('utf-8', 'replace').strip().splitlines() or ['?'])[-1])

    # 1. syntaxe : l'outil maison ET le vrai compilateur doivent être d'accord, et accepter les 7 scripts
    for s in SCRIPTS:
        chemin = os.path.join(RACINE, s)
        maison = lua_syntaxe.verifier_fichier(chemin)
        reel = subprocess.run([lua, os.path.join(ICI, 'compiler.lua'), chemin], capture_output=True)      # loadfile : compile sans exécuter
        verif(maison is None and reel.returncode == 0,
              'syntaxe de %s : outil maison %s, Lua 5.3 %s' % (s, 'OK' if maison is None else maison, 'OK' if reel.returncode == 0 else reel.stdout.decode('utf-8', 'replace')))

    # 2. aucun accès fichier / processus / réseau / chargement de code (le jeu n'a ni io ni os)
    for s in SCRIPTS:
        texte = open(os.path.join(RACINE, s), 'rb').read().decode('utf-8', 'replace')
        jetons = lua_syntaxe.lex(texte)
        trouves = []
        for i, j in enumerate(jetons):
            if j.t == 'name' and j.v in INTERDITS:
                precedent = jetons[i - 1] if i else None
                if precedent is not None and precedent.t == 'op' and precedent.v in ('.', ':'):
                    continue                      # un champ (t.load) n'est pas la fonction globale
                trouves.append('%s ligne %d' % (j.v, j.line))
        verif(not trouves, '%s : aucun appel à io/os/package/require/dofile/load/debug (%s)' % (s, ', '.join(trouves) or 'rien trouvé'))

    # 3. noms inconnus : tout nom utilisé doit être fourni par la fausse API, défini par le script, ou être un réglage facultatif posé en tête
    code, sortie, err = lancer_lua(lua, ['--noms'], capture=True)
    verif(code == 0 and sortie.strip() != '', 'liste des noms fournis par la fausse API (%d noms)' % len(sortie.split()))
    connus = set(sortie.split()) | lua_inconnus.STD | lua_syntaxe.KEYWORDS | REGLAGES_FACULTATIFS
    for s in SCRIPTS:
        chemin = os.path.join(RACINE, s)
        texte = open(chemin, 'rb').read().decode('utf-8', 'replace')
        utilises, declares = lua_inconnus.noms(chemin)
        inconnus = {}
        for nom, ligne in utilises:
            if nom in connus or nom in declares:
                continue
            if re.search(r'(?<![\w.:])%s\s*=(?!=)' % re.escape(nom), texte):
                continue                          # variable globale posée par le script lui-même
            inconnus.setdefault(nom, []).append(ligne)
        verif(not inconnus, '%s : aucun nom inconnu de la fausse API (%s)' % (s, ', '.join('%s l.%s' % (n, l[0]) for n, l in sorted(inconnus.items())) or 'rien trouvé'))
    return echecs


# ---------------------------------------------------------------- validation du banc par mutations
# (script, texte à remplacer, remplaçant, fichiers de scénarios qui doivent le voir, tout remplacer ?)
MUTATIONS = [
    ('tour/lua/library_custom_7.lua', 'if d >= 10 then', 'if d >= 5 then', 'sim_lib7', False),
    ('tour/lua/library_custom_7.lua', '((tick - v.tick0) / 30) / d', '((tick - v.tick0) / 60) / d', 'sim_lib7', False),
    ('tour/lua/library_custom_7.lua', 'pcall(vsim_observer)', 'vsim_observer()', 'sim_lib7', False),
    ('tour/lua/library_custom_7.lua', 'if x + w > screen_w - 4 then return end', 'if x + w > screen_w + 400 then return end', 'sim_lib7', False),
    ('tour/lua/library_custom_7.lua', '(nom == "screen_veh_l" or nom == "screen_veh_m" or nom == "screen_veh_r")', 'true', 'sim_lib7', False),
    ('tour/lua/library_custom_9.lua', 'HANGAR, VOL = 2, 3, 7, 4, 0', 'HANGAR, VOL = 2, 3, 7, 4, 5', 'sorties_lib9', False),
    ('tour/lua/library_custom_9.lua', 'elseif etat == HANGAR then', 'elseif false then', 'sorties_lib9', False),
    ('tour/lua/library_custom_9.lua', 'if (ok1 and rattache == id_bateau) or (ok2 and accoste == id_bateau) then', 'if (ok1 and rattache == id_bateau) then', 'sorties_lib9', False),
    ('tour/lua/library_custom_9.lua', 'AFFICHAGE_APRES_FIN = 3600', 'AFFICHAGE_APRES_FIN = 36000', 'sorties_lib9', False),
    ('tour/lua/library_custom_9.lua', 'pcall(sorties_observer)', 'sorties_observer()', 'sorties_lib9', False),
    ('tour/auto/library_custom_5.lua', 'local ATTENTE_JEU = 1800', 'local ATTENTE_JEU = 100', 'essai_auto_lib5', False),
    ('tour/auto/library_custom_5.lua', 'g_ca_attente_menu or 28', 'g_ca_attente_menu or 2', 'essai_auto_lib5', False),
    ('tour/auto/library_custom_5.lua', 'if okp and mdp ~= VERROU then', 'if okp then', 'essai_auto_lib5', False),
    ('tour/auto/library_custom_5.lua', 'local DEVANT = 4000', 'local DEVANT = 400', 'essai_auto_lib5', False),
    ('tour/auto/library_custom_5.lua', 'pcall(update_ui_event, "quit_game")', 'pcall(function() end)', 'essai_auto_lib5', True),
    ('tour/auto/library_custom_5.lua', 'if refus == #s.rec then', 'if false then', 'essai_auto_lib5', False),
    ('tour/auto/library_custom_5.lua', 'v:set_target_vehicle(wp, s.porte)', 'v:set_target_vehicle(wp, 0)', 'essai_auto_lib5', False),
    ('tour/auto/library_custom_5.lua', 'if not ok then s.err = "erreur : " .. tostring(err) end', '', 'essai_auto_lib5', True),
    ('tour/etudes_demarrage_auto/demarrage_auto.lua', 'g_da_attente or 30', 'g_da_attente or 3', 'demarrage_auto', False),
    ('tour/etudes_demarrage_auto/demarrage_auto.lua', 'if okp and mdp == VERROU then return end', '', 'demarrage_auto', False),
    ('tour/etudes_demarrage_auto/demarrage_auto.lua', 'update_ui_event("new_game_custom")\n\t\tg_da_envoye = true', 'update_ui_event("new_game_custom"); update_ui_event("new_game_custom")\n\t\tg_da_envoye = true', 'demarrage_auto', False),
    ('tour/etudes_demarrage_auto/demarrage_auto.lua', 'if not g_da_arme then g_da_fini = true; return end', '', 'demarrage_auto', False),
    ('tour/etudes_demarrage_auto/demarrage_auto.lua', 'if rawget(_G, "g_is_menu_active") == nil then return end', '', 'demarrage_auto', False),
    ('tour/etudes_modes_carburant/lua/library_custom_3.lua', 'local PAR_LIGNE = 6', 'local PAR_LIGNE = 12', 'carburant_mesure_lib3', False),
    ('tour/etudes_modes_carburant/lua/library_custom_3.lua', 'cc2x.api >= 4', 'cc2x.api >= 3', 'carburant_mesure_lib3', False),
    ('tour/etudes_modes_carburant/lua/library_custom_3.lua', 'v.flight_state == 2', 'v.flight_state ~= nil', 'carburant_mesure_lib3', False),
    ('tour/etudes_modes_carburant/lua/library_custom_3.lua', 'local PAS = 150', 'local PAS = 15', 'carburant_mesure_lib3', False),
    ('tour/etudes_modes_carburant/lua/library_custom_3.lua', '"%a:[\\\\/][^%s]*"', '"zzz"', 'carburant_mesure_lib3', False),
    ('tour/etudes_modes_carburant/lua/library_custom_5.lua', 'local FEN_Y = 99', 'local FEN_Y = 50', 'carburant_onglet_v1', False),
    ('tour/etudes_modes_carburant/lua/library_custom_5.lua', 'g_cm.casse = true', 'g_cm.casse = false', 'carburant_onglet_v1', False),
    ('tour/etudes_modes_carburant/lua/library_custom_5.lua', 'local MODE_DEFAUT = 2', 'local MODE_DEFAUT = 1', 'carburant_onglet_v1', False),
    ('tour/etudes_modes_carburant/lua/library_custom_5.lua', 'ui.region_stack[#ui.region_stack] = nil', 'break', 'carburant_onglet_v1', False),
    ('tour/etudes_modes_carburant/lua/v2/library_custom_5.lua', 'local MODE_PLUGIN = { 1, 0, 2 }', 'local MODE_PLUGIN = { 0, 1, 2 }', 'carburant_onglet_v2', False),
    ('tour/etudes_modes_carburant/lua/v2/library_custom_5.lua', 'if type(id) == "number" and id > 0 then cc2x.modes.hold(id) end', 'if type(id) == "number" then cc2x.modes.hold(id) end', 'carburant_onglet_v2', False),
    ('tour/etudes_modes_carburant/lua/v2/library_custom_5.lua', 'local REAFFICHER_STATUT = 60', 'local REAFFICHER_STATUT = 1', 'carburant_onglet_v2', False),
    ('tour/etudes_modes_carburant/lua/v2/library_custom_5.lua', '[8] = 800, [10] = 1200', '[8] = 80, [10] = 1200', 'carburant_onglet_v2', False),
    ('tour/etudes_modes_carburant/lua/v2/library_custom_5.lua', 'pcall(cc2x.modes.set, id, MODE_PLUGIN[i])', 'pcall(cc2x.modes.set, id, MODE_PLUGIN[i] + 1)', 'carburant_onglet_v2', False),
    ('tour/etudes_modes_carburant/lua/v2/library_custom_5.lua', 'local BOUTON_DE_MODE = { [0] = 2, [1] = 1, [2] = 3 }', 'local BOUTON_DE_MODE = { [0] = 2, [1] = 3, [2] = 1 }', 'carburant_onglet_v2', False),
    ('tour/etudes_modes_carburant/lua/v2/library_custom_5.lua', 'local FEN_Y = 99', 'local FEN_Y = 60', 'carburant_onglet_v2', False),
]


def mutations(lua):
    print('\n== Validation du banc par mutations : chaque défaut introduit exprès dans une COPIE JETABLE doit faire échouer le banc')
    survivants = []
    erreurs_prep = 0
    for k, (script, avant, apres, scenarios, tout) in enumerate(MUTATIONS, 1):
        with tempfile.TemporaryDirectory(prefix='banc_lua_mutant_') as tmp:
            for s in SCRIPTS:
                dest = os.path.join(tmp, s)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copyfile(os.path.join(RACINE, s), dest)
            chemin = os.path.join(tmp, script)
            texte = open(chemin, 'rb').read().decode('utf-8')
            if avant not in texte:
                print('  ERREUR mutation %d : motif introuvable dans %s : %r (le script a changé ? mettre à jour MUTATIONS)' % (k, script, avant))
                erreurs_prep += 1
                continue
            nouveau = texte.replace(avant, apres) if tout else texte.replace(avant, apres, 1)
            open(chemin, 'wb').write(nouveau.encode('utf-8'))
            code, sortie, err = lancer_lua(lua, ['--seulement', scenarios], racine=tmp, capture=True, delai=DELAI_MUTANT)
            tue = code != 0                                    # 124 = délai dépassé (boucle infinie du mutant) : compte comme « tuée »
            echecs = [l.strip() for l in sortie.splitlines() if l.strip().startswith('ECHEC')]
            print('  %s mutation %2d %-60s %s' % ('tuée    ' if tue else 'SURVIT  ', k, '%s : %s' % (os.path.basename(os.path.dirname(script)) + '/' + os.path.basename(script), avant[:40].replace('\n', ' ')),
                                             (('-> %d scénario(s) en échec' % len(echecs)) if code != 124 else '-> délai dépassé (boucle infinie)') if tue else ''))
            if not tue:
                survivants.append((k, script, avant))
    print('%d mutations, %d tuées, %d survivante(s), %d erreur(s) de préparation' % (len(MUTATIONS), len(MUTATIONS) - len(survivants) - erreurs_prep, len(survivants), erreurs_prep))
    return len(survivants) + erreurs_prep


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description='Banc Lua de Carrier Command 2 (hors du jeu, fausse API)')
    ap.add_argument('--lua', help='chemin de l\'interpréteur Lua 5.3 (sinon variable LUA53, sinon le PATH)')
    ap.add_argument('--filtre', help='ne lance que les scénarios dont "groupe nom" contient ce texte')
    ap.add_argument('--seulement', help='ne charge que ces fichiers de scénarios (ex. sim_lib7,sorties_lib9)')
    ap.add_argument('--verbeux', action='store_true')
    ap.add_argument('--sans-statique', action='store_true', help='saute les contrôles statiques')
    ap.add_argument('--mutations', action='store_true', help='valide le banc par mutations (plus long) et ne fait que cela')
    ap.add_argument('--inventaire', action='store_true', help='réécrit INVENTAIRE_API.md et s\'arrête')
    a = ap.parse_args()

    lua = trouver_lua(a.lua)
    print('Interpréteur : %s (%s)' % (lua, version_lua(lua)))

    if a.inventaire:
        code, sortie, err = lancer_lua(lua, ['--inventaire'], capture=True)
        if code != 0:
            print(err)
            return 1
        with open(os.path.join(ICI, 'INVENTAIRE_API.md'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(sortie)
        print('INVENTAIRE_API.md réécrit.')
        return 0
    if a.mutations:
        return 1 if mutations(lua) else 0

    total = 0
    if not a.sans_statique:
        total += controles_statiques(lua)
    print('\n== Scénarios (fausse API, Lua 5.3)')
    args = []
    if a.filtre:
        args += ['--filtre', a.filtre]
    if a.seulement:
        args += ['--seulement', a.seulement]
    if a.verbeux:
        args += ['--verbeux']
    code, _, _ = lancer_lua(lua, args)
    if code != 0:
        total += 1
    print('\n%s' % ('TOUT EST OK' if total == 0 else 'IL Y A DES ECHECS'))
    return 0 if total == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
