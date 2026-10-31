#!/usr/bin/env python3
"""Essai de mod_modes.py sur une FAUSSE racine (dossier temporaire, APPDATA detourne). Ne touche ni au vrai dossier du jeu, ni a
%APPDATA%\\Carrier Command 2, ni a un processus : la verification « le jeu tourne » est remplacee par une reponse imposee.

    python -I test_mod_modes.py

Controle surtout la revue du 29/10 (I2) : `installer`, `mettre-a-jour`, `retirer` et les commandes de plugin REFUSENT quand un
carrier_command* tourne (l'ancien exe de la voie A compris) ou quand on ne peut pas le savoir, et --jeu-ouvert-ok n'est pas accepte.
Les DLL de reference (dossiers de travail hors depot) sont lues, jamais modifiees ; si elles manquent, les essais de plugin sont sautes.
"""
import contextlib
import importlib.util
import io
import os
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('mod_modes_sous_test', os.path.join(ICI, 'mod_modes.py'))
MM = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MM)

pass_, fail_ = 0, 0


def check(cond, msg):
    global pass_, fail_
    if cond:
        pass_ += 1
    else:
        fail_ += 1
        print('  ECHEC :', msg)


def lancer(args, jeu):
    """Appelle mod_modes.main() en memoire avec _jeu_ouvert() qui repond `jeu` (True / False / None). -> (code, texte)."""
    MM._jeu_ouvert = lambda: jeu
    sys.argv = ['mod_modes.py'] + args
    sortie = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(sortie):
        try:
            code = MM.main()
        except SystemExit as e:
            code = e.code
    texte = sortie.getvalue() + (code if isinstance(code, str) else '')
    return code, texte


def refuse(code, texte):
    return (isinstance(code, str) and code.startswith('REFUS')) or (code not in (0, None) and 'REFUS' in texte)


def sha_fichier(p):
    return MM._sha(p) if os.path.isfile(p) else None


MODS_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n<data>\n\t<active_mod_folders>\n'
            '\t\t<path value="C:\\x\\autre_mod"/>\n\t</active_mod_folders>\n</data>\n')

with tempfile.TemporaryDirectory(prefix='essai_mod_modes_') as tmp:
    ancien_appdata = os.environ.get('APPDATA')
    os.environ['APPDATA'] = tmp                                   # la « vraie » racine de cet essai = tmp\Carrier Command 2
    racine = os.path.join(tmp, 'Carrier Command 2')
    os.makedirs(racine)
    xml = os.path.join(racine, 'mods.xml')
    open(xml, 'w', encoding='utf-8', newline='').write(MODS_XML)
    ui5 = os.path.join(racine, 'mods', 'cc2_modes', 'content', 'scripts', 'library_custom_5.lua')
    dll = MM.plugin_chemin(racine)
    base = ['--racine', racine]

    print('empreintes des sources et des DLL de reference')
    for nom, (dossier, attendu) in (MM.MESURE, MM.UI_V1, MM.UI_V2, MM.UI_V2_1):
        check(sha_fichier(os.path.join(dossier, nom)) == attendu, '%s dans %s : sha256 different de celui de mod_modes.py' % (nom, dossier))
    dll_ok = {}
    for v, (src, sha) in MM.PLUGINS.items():
        dll_ok[v] = src.is_file() and MM._sha(src) == sha
        print('  plugin v%s : %s' % (v, 'DLL de reference conforme' if dll_ok[v] else 'DLL de reference ABSENTE ou differente (essais sautes)'))
    check(MM.PLUGIN_SHA == MM.PLUGINS[MM.PLUGIN_COURANT][1] and MM.PLUGIN_COURANT == '3.1', 'la version courante est la 3.1')
    check(len(set(MM.PLUGIN_CONNUS)) == len(MM.PLUGIN_CONNUS) == 4, 'quatre versions de plugin connues (v1, v2, v3, v3.1)')

    print('I2 : le « charger_outil » remplace la verification etroite de l\'outil de base')
    MM._jeu_ouvert = lambda: False
    mm_base = MM.charger_outil()
    check(mm_base.jeu_ouvert is MM._jeu_ouvert, 'mod_mesures.jeu_ouvert doit etre la verification large de mod_modes')

    print('I2 : installer / mettre-a-jour / retirer refusent si un carrier_command* tourne, ou si on ne sait pas')
    for jeu in (True, None):
        etiquette = 'jeu ouvert' if jeu else 'jeu inconnu'
        avant = sha_fichier(xml)
        code, t = lancer(['installer', '--etape', 'tout2_1', '--date', '2026-10-30'] + base, jeu)
        check(refuse(code, t), 'installer doit refuser (%s) : %r %s' % (etiquette, code, t))
        check(sha_fichier(xml) == avant and not os.path.exists(os.path.join(racine, 'mods')), 'installer (%s) n\'a rien ecrit' % etiquette)
    code, t = lancer(['installer', '--etape', 'tout2_1', '--date', '2026-10-30'] + base, False)
    check(code == 0, 'installer tout2_1 avec le jeu ferme : %r %s' % (code, t))
    check(sha_fichier(ui5) == MM.UI_V2_1[1][1], 'l\'onglet v2.1 est pose dans la fausse racine')
    apres_installer = sha_fichier(xml)
    check('autre_mod' in open(xml, encoding='utf-8').read() and 'cc2_modes' in open(xml, encoding='utf-8').read(), 'mods.xml : l\'autre mod est garde, cc2_modes ajoute')
    for jeu in (True, None):
        etiquette = 'jeu ouvert' if jeu else 'jeu inconnu'
        for etape in ('interface2', 'interface2_1', 'tout2'):
            avant = sha_fichier(ui5)
            code, t = lancer(['mettre-a-jour', '--etape', etape] + base, jeu)
            check(refuse(code, t), 'mettre-a-jour --etape %s doit refuser (%s) : %r' % (etape, etiquette, code))
            check(sha_fichier(ui5) == avant, 'mettre-a-jour (%s) n\'a rien ecrit' % etiquette)
        code, t = lancer(['retirer'] + base, jeu)
        check(refuse(code, t), 'retirer doit refuser (%s) : %r' % (etiquette, code))
        check(os.path.isdir(os.path.dirname(os.path.dirname(os.path.dirname(ui5)))) and sha_fichier(xml) == apres_installer, 'retirer (%s) n\'a rien supprime' % etiquette)
    code, t = lancer(['mettre-a-jour', '--etape', 'interface2_1', '--jeu-ouvert-ok'] + base, True)
    check(refuse(code, t) and '--jeu-ouvert-ok' in t, '--jeu-ouvert-ok n\'est pas accepte : %r' % code)
    code, t = lancer(['mettre-a-jour', '--etape', 'interface2_1', '--jeu-ouvert-ok'] + base, False)
    check(refuse(code, t), '--jeu-ouvert-ok n\'est pas accepte meme avec le jeu ferme')

    print('mises a jour de l\'onglet (jeu ferme) : v2.1 -> v2 -> v1 -> v2.1, mods.xml intact')
    for etape, attendu in (('interface2', MM.UI_V2[1][1]), ('interface', MM.UI_V1[1][1]), ('interface2_1', MM.UI_V2_1[1][1])):
        code, t = lancer(['mettre-a-jour', '--etape', etape] + base, False)
        check(code == 0 and sha_fichier(ui5) == attendu, 'mettre-a-jour --etape %s : %r' % (etape, code))
        check(sha_fichier(xml) == apres_installer, 'mods.xml inchange apres %s' % etape)
        code, t = lancer(['etat'] + base, False)
        check(code == 0 and {'interface2': 'onglet v2 (', 'interface': 'onglet v1 (', 'interface2_1': 'onglet v2.1 ('}[etape] in t, 'etat apres %s : %s' % (etape, t))
    code, t = lancer(['mettre-a-jour', '--etape', 'interface2_1'] + base, False)
    check(code == 0 and 'deja a jour' in t, 'rejouer la meme mise a jour = « deja a jour »')

    print('plugin : poser, mettre a jour v3 <-> v3.1, retirer ; refus si le jeu tourne')
    if dll_ok['3.1'] and dll_ok['3']:
        for jeu in (True, None):
            code, t = lancer(['poser-plugin'] + base, jeu)
            check(refuse(code, t) and not os.path.exists(dll), 'poser-plugin doit refuser (jeu %s)' % ('ouvert' if jeu else 'inconnu'))
        code, t = lancer(['poser-plugin'] + base, False)
        check(code == 0 and sha_fichier(dll) == MM.PLUGINS['3.1'][1], 'poser-plugin pose la v3.1 par defaut : %r %s' % (code, t))
        code, t = lancer(['etat'] + base, False)
        check('v3.1 conforme' in t, 'etat : v3.1 conforme\n' + t)
        code, t = lancer(['mettre-a-jour-plugin'] + base, False)
        check(code == 0 and 'deja a jour (v3.1)' in t, 'mettre-a-jour-plugin sur la v3.1 : deja a jour')
        for jeu in (True, None):
            avant = sha_fichier(dll)
            code, t = lancer(['mettre-a-jour-plugin', '--version', '3'] + base, jeu)
            check(refuse(code, t) and sha_fichier(dll) == avant, 'mettre-a-jour-plugin doit refuser (jeu %s)' % ('ouvert' if jeu else 'inconnu'))
        code, t = lancer(['mettre-a-jour-plugin', '--version', '3'] + base, False)
        check(code == 0 and sha_fichier(dll) == MM.PLUGINS['3'][1] and 'remplace par la v3 ' in t, 'retour arriere --version 3 : %r %s' % (code, t))
        check('--version 3.1' in t, 'le message donne la commande pour revenir a la v3.1')
        code, t = lancer(['etat'] + base, False)
        check('v3 (sha256 331581C6...)' in t and 'remplacera par la v3.1' in t, 'etat : v3, mise a jour proposee vers la 3.1\n' + t)
        code, t = lancer(['mettre-a-jour-plugin'] + base, False)
        check(code == 0 and sha_fichier(dll) == MM.PLUGINS['3.1'][1], 'mettre-a-jour-plugin (defaut) : de la v3 vers la v3.1')
        code, t = lancer(['mettre-a-jour-plugin', '--version', '9'] + base, False)
        check(refuse(code, t) and sha_fichier(dll) == MM.PLUGINS['3.1'][1], 'version inconnue refusee, rien ecrit')
        open(dll, 'wb').write(b'pas une DLL connue')
        code, t = lancer(['mettre-a-jour-plugin'] + base, False)
        check(refuse(code, t) and open(dll, 'rb').read() == b'pas une DLL connue', 'un plugin inconnu n\'est jamais remplace')
        code, t = lancer(['retirer-plugin'] + base, False)
        check(code == 1 and os.path.exists(dll), 'un plugin inconnu n\'est jamais retire non plus')
        open(dll, 'wb').write(open(MM.PLUGINS['3'][0], 'rb').read())
        code, t = lancer(['retirer-plugin'] + base, True)
        check(refuse(code, t) and os.path.exists(dll), 'retirer-plugin doit refuser (jeu ouvert)')
        code, t = lancer(['retirer-plugin'] + base, False)
        check(code == 0 and not os.path.exists(dll), 'retirer-plugin retire la v3 (version connue)')
    else:
        print('  (DLL de reference absentes : essais de plugin sautes)')

    print('une racine d\'essai (pas la vraie) n\'est pas bloquee par la verification, comme avant')
    autre = os.path.join(tmp, 'autre_racine')
    os.makedirs(autre)
    open(os.path.join(autre, 'mods.xml'), 'w', encoding='utf-8', newline='').write(MODS_XML)
    code, t = lancer(['installer', '--etape', 'tout2_1', '--date', '2026-10-30', '--racine', autre], True)
    check(code == 0, 'installer sur une racine d\'essai avec « jeu ouvert » : %r %s' % (code, t))

    print('retirer (jeu ferme) remet mods.xml comme avant')
    code, t = lancer(['retirer'] + base, False)
    check(code == 0 and not os.path.exists(os.path.join(racine, 'mods', 'cc2_modes')) and open(xml, encoding='utf-8').read() == MODS_XML, 'retirer : mods.xml identique a l\'original : %r %s' % (code, t))
    if ancien_appdata is None:
        os.environ.pop('APPDATA', None)
    else:
        os.environ['APPDATA'] = ancien_appdata

print('\n%d reussis, %d echoues' % (pass_, fail_))
sys.exit(1 if fail_ else 0)
