#!/usr/bin/env python3
"""Tests de demarrage_auto.py et lancer_cc2.py SANS lancer le jeu, sur un FAUX dossier du jeu et de donnees (temporaires, supprimes a la fin).
Aucun fichier reel (jeu, %APPDATA%\\Carrier Command 2, Steam) n'est lu ni ecrit ; aucun processus n'est lance.
Usage : python -I test_demarrage_auto.py"""
import contextlib
import datetime
import importlib.util
import io
import os
import shutil
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))


def charger(nom, fichier):
    spec = importlib.util.spec_from_file_location(nom, os.path.join(ICI, fichier))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


da = charger('demarrage_auto', 'demarrage_auto.py')
lc = charger('lancer_cc2', 'lancer_cc2.py')
ls = charger('lua_sonde', os.path.join('..', 'outils', 'lua_sonde.py'))
MODS_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n<data>\n\t<active_mod_folders>\n'
            '\t\t<path value="C:\\ailleurs\\mod_x"/>\n\t</active_mod_folders>\n</data>\n')
ok_total, ko = 0, 0


def verifie(cond, msg):
    global ok_total, ko
    if cond:
        ok_total += 1
    else:
        ko += 1
        print('ECHEC :', msg)


def lire(p):
    with open(p, 'rb') as f:
        return f.read()


def ecrire(p, octets):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(octets)


def faux_monde(tmp):
    jeu = os.path.join(tmp, 'steamapps', 'common', 'Carrier Command 2')
    racine = os.path.join(tmp, 'donnees')
    for n in range(10):
        ecrire(os.path.join(jeu, 'rom_0', 'scripts', 'library_custom_%d.lua' % n), b'')
    ecrire(os.path.join(racine, 'mods.xml'), MODS_XML.encode('utf-8'))
    ecrire(os.path.join(racine, 'mods', 'cc2_modes', 'content', 'scripts', 'library_custom_5.lua'), b'-- un autre mod\n')
    ecrire(os.path.join(tmp, 'steamapps', 'workshop', 'content', '1489630', '3398249587', 'content', 'scripts', 'library_custom_2.lua'), b'-- workshop\n')
    return jeu, racine


def commande(jeu, racine, *args):
    """Lance demarrage_auto.main() comme en ligne de commande ; renvoie (code, sortie)."""
    sys.argv = ['demarrage_auto.py'] + list(args) + ['--racine', racine, '--dossier-jeu', jeu]
    tampon = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(tampon):
        try:
            code = da.main() or 0
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else (1 if e.code else 0)
            if isinstance(e.code, str):
                print(e.code)
    return code, tampon.getvalue()


def etat_dossiers(jeu, racine):
    res = {}
    for base in (jeu, racine):
        for rep, _, fichiers in os.walk(base):
            for f in fichiers:
                p = os.path.join(rep, f)
                res[p] = da.sha(lire(p))
    return res


tmp = tempfile.mkdtemp(prefix='cc2_test_demarrage_')
os.environ['LOCALAPPDATA'] = os.path.join(tmp, 'local')
try:
    print('--- 1. etat, installation, refus de reinstaller')
    jeu, racine = faux_monde(os.path.join(tmp, 'a'))
    avant = etat_dossiers(jeu, racine)
    code, out = commande(jeu, racine, 'etat')
    verifie(code == 0 and 'absent' in out and 'decoche' in out, 'etat sur un monde vierge')
    verifie(etat_dossiers(jeu, racine) == avant, 'etat ne modifie rien')
    code, out = commande(jeu, racine, 'installer', '--date', '2026-10-28')
    rom = os.path.join(jeu, 'rom_0', 'scripts', 'library_custom_0.lua')
    verifie(code == 0, 'installation reussie : %s' % out[-200:])
    script = lire(rom)
    verifie(script.startswith(da.MARQUE.encode()), 'le fichier de rom_0 commence par la marque de l\'outil')
    verifie(b'g_da_mode = "nouvelle"' in script and b'g_da_attente = 30' in script and b'g_da_attendre_menu = false' in script, 'lignes de reglage ecrites')
    verifie(script.endswith(lire(da.SRC_LUA)), 'le script du jeu = la source demarrage_auto.lua, apres l\'entete')
    dm = os.path.join(racine, 'mods', 'cc2_demarrage_auto')
    verifie(os.path.isfile(os.path.join(dm, 'mod.xml')) and os.path.isfile(os.path.join(dm, 'thumbnail.png'))
            and os.path.isfile(os.path.join(dm, 'content', 'scripts', 'library_custom_0.lua')), 'dossier du mod complet')
    verifie(b'name="Demarrage auto"' in lire(os.path.join(dm, 'mod.xml')), 'le mod s\'appelle bien « Demarrage auto » (nom lu par le script)')
    verifie(lire(os.path.join(racine, 'mods.xml')) == MODS_XML.encode('utf-8'), 'mods.xml NON touche par « installer »')
    for n in range(1, 10):
        verifie(os.path.getsize(os.path.join(jeu, 'rom_0', 'scripts', 'library_custom_%d.lua' % n)) == 0, 'les autres fichiers de rom_0 sont intacts (%d)' % n)
    # le fichier pose est du Lua valide (vraie verification de syntaxe)
    vm = ls.VM()
    b = script
    r = vm.L.luaL_loadbuffer(vm.s, b, len(b), b'=library_custom_0')
    vm.close()
    verifie(r == 0, 'le fichier pose passe la verification de syntaxe Lua')
    apres_install = etat_dossiers(jeu, racine)
    code, out = commande(jeu, racine, 'installer')
    verifie(code != 0 and 'REFUS' in out, 'reinstaller est refuse')
    verifie(etat_dossiers(jeu, racine) == apres_install, 'le refus ne modifie rien')
    code, out = commande(jeu, racine, 'etat')
    verifie('notre script' in out and 'mode=nouvelle' in out and 'present' in out and 'decoche' in out, 'etat apres installation')

    print('--- 2. armer / desarmer (mods.xml)')
    code, out = commande(jeu, racine, 'armer', '--date', '2026-10-28')
    verifie(code == 0, 'armer reussi : %s' % out[-200:])
    txt = lire(os.path.join(racine, 'mods.xml')).decode('utf-8')
    verifie(txt.count('cc2_demarrage_auto') == 1 and '\t\t<path value="%s"/>\n\t</active_mod_folders>' % dm in txt, 'une ligne ajoutee en fin de liste')
    baks = sorted(f for f in os.listdir(racine) if f.startswith('mods.xml.bak_'))
    verifie(len(baks) == 1 and lire(os.path.join(racine, baks[0])) == MODS_XML.encode('utf-8'), 'sauvegarde de mods.xml identique a l\'original')
    code, out = commande(jeu, racine, 'armer')
    verifie(code == 0 and 'Deja arme' in out and lire(os.path.join(racine, 'mods.xml')).decode('utf-8').count('cc2_demarrage_auto') == 1, 'armer deux fois : rien de plus')
    code, out = commande(jeu, racine, 'etat')
    verifie('COCHE' in out, 'etat : interrupteur coche')
    code, out = commande(jeu, racine, 'desarmer', '--date', '2026-10-28')
    verifie(code == 0 and lire(os.path.join(racine, 'mods.xml')) == MODS_XML.encode('utf-8'), 'desarmer : mods.xml revient octet pour octet a l\'original')
    baks = sorted(f for f in os.listdir(racine) if f.startswith('mods.xml.bak_'))
    verifie(len(baks) == 2, 'les sauvegardes ne s\'ecrasent jamais (2 apres armer + desarmer)')
    code, out = commande(jeu, racine, 'desarmer')
    verifie(code == 0 and 'Deja desarme' in out, 'desarmer deux fois : rien')

    print('--- 3. desinstaller remet tout')
    commande(jeu, racine, 'armer')
    code, out = commande(jeu, racine, 'desinstaller')
    verifie(code == 0, 'desinstaller reussi : %s' % out[-300:])
    verifie(os.path.getsize(rom) == 0 and da.sha(lire(rom)) == da.VIDE, 'fichier de rom_0 revenu a 0 octet (sha256 vide)')
    verifie(not os.path.exists(dm), 'dossier du mod supprime')
    verifie(lire(os.path.join(racine, 'mods.xml')) == MODS_XML.encode('utf-8'), 'mods.xml identique a l\'original')
    code, out = commande(jeu, racine, 'desinstaller')
    verifie(code == 0, 'desinstaller est repetable')
    verifie(not any(f.endswith('.cc2_tmp') for _, _, fs in os.walk(tmp) for f in fs), 'aucun fichier temporaire oublie')

    print('--- 4. garde-fous')
    jeu, racine = faux_monde(os.path.join(tmp, 'b'))
    ecrire(os.path.join(jeu, 'rom_0', 'scripts', 'library_custom_0.lua'), b'-- le script de quelqu\'un d\'autre\n')
    avant = etat_dossiers(jeu, racine)
    code, out = commande(jeu, racine, 'installer')
    verifie(code != 0 and 'pas le fichier VIDE' in out and etat_dossiers(jeu, racine) == avant, 'refus si le fichier de rom_0 n\'est pas vide, rien d\'ecrit')
    code, out = commande(jeu, racine, 'desinstaller')
    verifie(os.path.getsize(os.path.join(jeu, 'rom_0', 'scripts', 'library_custom_0.lua')) > 0, 'desinstaller ne vide JAMAIS un fichier qui n\'est pas le notre')
    jeu, racine = faux_monde(os.path.join(tmp, 'c'))
    avant = etat_dossiers(jeu, racine)
    for n, qui in ((5, 'cc2_modes'), (2, '3398249587')):
        code, out = commande(jeu, racine, 'installer', '--rom', str(n))
        verifie(code != 0 and qui in out and etat_dossiers(jeu, racine) == avant, 'refus si un mod (%s) fournit deja library_custom_%d.lua' % (qui, n))
    ecrire(os.path.join(racine, 'mods', 'cc2_demarrage_auto', 'x.txt'), b'deja la')
    avant = etat_dossiers(jeu, racine)
    code, out = commande(jeu, racine, 'installer')
    verifie(code != 0 and 'existe deja' in out and etat_dossiers(jeu, racine) == avant, 'refus si le dossier du mod existe deja')
    shutil.rmtree(os.path.join(racine, 'mods', 'cc2_demarrage_auto'))
    code, out = commande(jeu, racine, 'installer', '--rom', '3', '--mode', 'charger', '--partie', '7', '--attente', '12', '--attendre-touche')
    s3 = lire(os.path.join(jeu, 'rom_0', 'scripts', 'library_custom_3.lua'))
    verifie(code == 0 and b'g_da_mode = "charger"' in s3 and b'g_da_slot = 7' in s3 and b'g_da_attente = 12' in s3 and b'g_da_attendre_menu = true' in s3,
            'options --rom/--mode/--partie/--attente/--attendre-touche prises en compte')
    code, out = commande(jeu, racine, 'etat')
    verifie('library_custom_3.lua : notre script' in out and 'mode=charger' in out, 'etat relit les reglages poses')
    code, out = commande(jeu, racine, 'desinstaller')
    verifie(code == 0 and os.path.getsize(os.path.join(jeu, 'rom_0', 'scripts', 'library_custom_3.lua')) == 0, 'desinstaller retrouve le fichier ecrit sur un autre numero')
    code, out = commande(jeu, racine, 'installer', '--attente', '1')
    verifie(code != 0 and 'entre 3 et 600' in out, 'attente hors limites refusee')

    print('--- 5. mods.xml de forme inattendue, mod etranger dans notre dossier, jeu en cours')
    jeu, racine = faux_monde(os.path.join(tmp, 'd'))
    commande(jeu, racine, 'installer')
    ecrire(os.path.join(racine, 'mods.xml'), MODS_XML.replace('\n', '\r\n').encode('utf-8'))
    avant = lire(os.path.join(racine, 'mods.xml'))
    code, out = commande(jeu, racine, 'armer')
    verifie(code != 0 and 'forme attendue' in out and lire(os.path.join(racine, 'mods.xml')) == avant, 'armer refuse un mods.xml en fins de ligne Windows, sans rien ecrire')
    ecrire(os.path.join(racine, 'mods.xml'), MODS_XML.encode('utf-8'))
    ecrire(os.path.join(racine, 'mods', 'cc2_demarrage_auto', 'perso.txt'), b'a moi')
    code, out = commande(jeu, racine, 'desinstaller')
    verifie(code != 0 and os.path.isfile(os.path.join(racine, 'mods', 'cc2_demarrage_auto', 'perso.txt')), 'un fichier etranger dans le dossier du mod : dossier GARDE')
    verifie(os.path.getsize(os.path.join(jeu, 'rom_0', 'scripts', 'library_custom_0.lua')) == 0, '... mais le fichier de rom_0 est quand meme remis a 0 octet')
    shutil.rmtree(os.path.join(racine, 'mods', 'cc2_demarrage_auto'), ignore_errors=True)
    jeu, racine = faux_monde(os.path.join(tmp, 'e'))
    vrai_avant, pj_avant = da.est_vrai, da.processus_jeu
    try:
        da.est_vrai = lambda a: True
        for faux_pids, attendu in ((['1234'], 'REFUS'), (None, 'REFUS'), ([], None)):
            da.processus_jeu = lambda p=faux_pids: p
            avant = etat_dossiers(jeu, racine)
            code, out = commande(jeu, racine, 'installer')
            if attendu:
                verifie(code != 0 and 'le jeu tourne' in out and etat_dossiers(jeu, racine) == avant, 'jeu en cours (%r) : installer refuse, rien ecrit' % (faux_pids,))
            else:
                verifie(code == 0, 'jeu ferme et verifiable : installer passe')
    finally:
        da.est_vrai, da.processus_jeu = vrai_avant, pj_avant

    print('--- 6. lanceur : lecture des rapports de plantage Windows')
    en = ('Faulting application name: carrier_command.exe, version: 1.5.18.0, time stamp: 0x6a36c177 / Faulting module name: carrier_command.exe, '
          'version: 1.5.18.0, time stamp: 0x6a36c177 / Exception code: 0xc0000005 / Fault offset: 0x001ef518 / Faulting process id: 0x1f4c')
    fr = ('Nom de l\'application defaillante : carrier_command.exe, version : 1.5.18.0, horodatage : 0x6a36c177 / Nom du module defaillant : '
          'carrier_command.exe, version : 1.5.18.0, horodatage : 0x6a36c177 / Code d\'exception : 0xc0000005 / Decalage d\'erreur : 0x001ef525 / ID du processus : 0x1f4c')
    verifie(lc.analyser_plantage(en) == ('0xc0000005', '0x001ef518'), 'rapport anglais : code et decalage')
    verifie(lc.analyser_plantage(fr) == ('0xc0000005', '0x001ef525'), 'rapport francais : code et decalage')
    verifie(lc.analyser_plantage('rien') == (None, None), 'message sans code : (None, None)')

    print('--- 7. lanceur : relance automatique (faux jeu, fausse horloge)')

    class Horloge:
        def __init__(self):
            self.t = 1000.0

        def time(self):
            return self.t

        def sleep(self, s):
            self.t += s

    def scenario(vies, evenements, essais=3, surveillance=60):
        """vies : duree (en secondes d'horloge) de chaque lancement successif ; evenements : liste d'evenements Windows vus apres chaque arret."""
        h = Horloge()
        lance = []
        etat = {'debut': None, 'k': -1}
        vieux = (lc.time, lc.demarrer_jeu, lc.processus_jeu, lc.evenements_plantage, lc.journal)
        lc.time = h
        journaux = []

        def demarrer(exe):
            etat['k'] += 1
            etat['debut'] = h.t
            lance.append(exe)

        def pj():
            if etat['debut'] is None:
                return []
            return ['4242'] if h.t - etat['debut'] < vies[min(etat['k'], len(vies) - 1)] else []

        lc.demarrer_jeu = demarrer
        lc.processus_jeu = pj
        lc.evenements_plantage = lambda depuis: evenements[min(etat['k'], len(evenements) - 1)]
        lc.journal = journaux.append
        try:
            sys.argv = ['lancer_cc2.py', '--essais', str(essais), '--surveillance', str(surveillance), '--dossier-jeu', os.path.join(tmp, 'vide'),
                        '--racine', os.path.join(tmp, 'vide')]
            tampon = io.StringIO()
            with contextlib.redirect_stdout(tampon):
                code = lc.main()
        finally:
            lc.time, lc.demarrer_jeu, lc.processus_jeu, lc.evenements_plantage, lc.journal = vieux
        return code, len(lance), journaux

    crash = [('08:15:01', en)]
    code, n, jr = scenario(vies=[20, 9999], evenements=[crash, []])
    verifie(code == 0 and n == 2, 'plantage a 20 s puis jeu qui tient : relance une fois, code 0 (lancements : %d, code %s)' % (n, code))
    verifie(any('0x001ef518' in l and 'adresse connue' in l for l in jr), 'l\'adresse du plantage est notee, reconnue comme celle de l\'etude')
    code, n, jr = scenario(vies=[20, 30, 40], evenements=[crash])
    verifie(code == 1 and n == 3, 'trois plantages de suite : 3 lancements, code 1')
    code, n, jr = scenario(vies=[25], evenements=[[]])
    verifie(code == 3 and n == 1, 'arret sans rapport de plantage : pas de relance, code 3')
    code, n, jr = scenario(vies=[9999], evenements=[[]])
    verifie(code == 0 and n == 1, 'jeu qui tient toute la surveillance : un seul lancement, code 0')
    code, n, jr = scenario(vies=[20, 9999], evenements=[crash, []], essais=1)
    verifie(code == 1 and n == 1, '--essais 1 : pas de relance')

    print('--- 8. lanceur : refus si le jeu tourne deja ; a blanc')
    vieux = (lc.processus_jeu, lc.demarrer_jeu, lc.journal)
    appels = []
    try:
        lc.processus_jeu = lambda: ['999']
        lc.demarrer_jeu = lambda exe: appels.append(exe)
        lc.journal = lambda t: None
        sys.argv = ['lancer_cc2.py', '--dossier-jeu', os.path.join(tmp, 'vide'), '--racine', os.path.join(tmp, 'vide')]
        verifie(lc.main() == 2 and not appels, 'un exe du jeu tourne deja : refus (code 2), rien lance')
        lc.processus_jeu = lambda: []
        sys.argv = ['lancer_cc2.py', '--a-blanc', '--dossier-jeu', os.path.join(tmp, 'vide'), '--racine', os.path.join(tmp, 'vide')]
        verifie(lc.main() == 0 and not appels, '--a-blanc : rien n\'est lance')
        lc.processus_jeu = lambda: None
        sys.argv = ['lancer_cc2.py', '--dossier-jeu', os.path.join(tmp, 'vide'), '--racine', os.path.join(tmp, 'vide')]
        verifie(lc.main() == 2 and not appels, 'impossible de verifier les processus : refus')
    finally:
        lc.processus_jeu, lc.demarrer_jeu, lc.journal = vieux
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('\n%d verifications reussies, %d echec(s)' % (ok_total, ko))
sys.exit(1 if ko else 0)
