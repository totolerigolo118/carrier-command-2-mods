#!/usr/bin/env python3
"""Tests de essai_auto.py SANS lancer le jeu, sur un faux dossier de donnees (temporaire, supprime a la fin).
Usage : python -I test_essai_auto.py
Verifie : essai a blanc complet (installation du mod de test, mods.xml, remise en etat) ; remise en etat des
sauvegardes quand le 'jeu' modifie / ajoute / supprime des fichiers ; refus si le mod existe deja ; capture de fenetre
sur un Bloc-notes lance puis ferme par ce test (aucun fichier du jeu n'est touche)."""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time

ICI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('essai_auto', os.path.join(ICI, 'essai_auto.py'))
ea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ea)

MODS_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n<data>\n\t<active_mod_folders>\n'
            '\t\t<path value="C:\\ailleurs\\mod_x"/>\n\t</active_mod_folders>\n</data>\n\n')
ok_total, ko = 0, 0


def verifie(cond, msg):
    global ok_total, ko
    if cond:
        ok_total += 1
    else:
        ko += 1
        print('ECHEC :', msg)


def lire_octets(p):
    with open(p, 'rb') as f:
        return f.read()


def faux_dossier(racine):
    os.makedirs(os.path.join(racine, 'saved_games', 'slot_18'))
    os.makedirs(os.path.join(racine, 'saved_games', 'slot_19'))
    os.makedirs(os.path.join(racine, 'mods'))
    for p, c in (('saved_games/slot_18/save.xml', b'<save>18</save>'), ('saved_games/slot_19/save.xml', b'<save>auto</save>'),
                 ('persistent_data.xml', b'<data/>'), ('settings.xml', b'<s/>')):
        with open(os.path.join(racine, p), 'wb') as f:
            f.write(c)
    with open(os.path.join(racine, 'mods.xml'), 'wb') as f:
        f.write(MODS_XML.encode('utf-8'))


tmp = tempfile.mkdtemp(prefix='cc2_test_essai_')
try:
    # 1. essai a blanc complet
    racine = os.path.join(tmp, 'racine')
    faux_dossier(racine)
    avant = ea.manifeste(racine)
    os.environ['LOCALAPPDATA'] = os.path.join(tmp, 'local')
    os.makedirs(os.environ['LOCALAPPDATA'])
    sys.argv = ['essai_auto.py', 'lancer', 'test_a_blanc', '--racine', racine, '--sans-lancer']
    try:
        ea.main()
    except SystemExit as e:
        verifie(e.code == 0, 'essai a blanc : code de sortie %r' % (e.code,))
    verifie(ea.manifeste(racine) == avant, 'essai a blanc : le dossier de donnees n\'est pas identique apres')
    verifie(not os.path.exists(os.path.join(racine, 'mods', 'cc2_auto')), 'essai a blanc : le mod de test est reste')

    # 2. second essai avec la meme etiquette le meme jour : refuse, rien n'est ecrit
    sys.argv = ['essai_auto.py', 'lancer', 'test_a_blanc', '--racine', racine, '--sans-lancer']
    refus = False
    try:
        ea.main()
    except SystemExit as e:
        refus = isinstance(e.code, str) and 'existe deja' in e.code
    verifie(refus, 'meme etiquette : devait etre refusee')
    verifie(ea.manifeste(racine) == avant, 'meme etiquette : dossier de donnees modifie')

    # 2b. mode "dossier du jeu" (--rom0) sur un FAUX dossier de jeu : refus sans accord, refus si le fichier n'est pas vide,
    #     et sinon : script pose puis remis VIDE, mods.xml et mods intacts
    jeu = os.path.join(tmp, 'jeu')
    os.makedirs(os.path.join(jeu, 'rom_0', 'scripts'))
    rom5 = os.path.join(jeu, 'rom_0', 'scripts', 'library_custom_5.lua')
    open(rom5, 'wb').close()
    avant = ea.manifeste(racine)
    base_args = ['essai_auto.py', 'lancer']

    def lance(etiquette, *plus):
        sys.argv = base_args + [etiquette, '--racine', racine, '--dossier-jeu', jeu, '--sans-lancer'] + list(plus)
        try:
            ea.main()
        except SystemExit as e:
            return e.code
        return None

    code = lance('rom_sans_accord', '--rom0', '5')
    verifie(isinstance(code, str) and 'accord' in code, 'rom0 sans accord : devait etre refuse (%r)' % (code,))
    verifie(os.path.getsize(rom5) == 0, 'rom0 sans accord : le fichier du jeu a ete touche')
    with open(rom5, 'wb') as f:
        f.write(b'-- fichier de quelqu un d autre')
    code = lance('rom_non_vide', '--rom0', '5', '--accord-dossier-jeu')
    verifie(isinstance(code, str) and 'VIDE' in code, 'rom0 fichier non vide : devait etre refuse (%r)' % (code,))
    verifie(lire_octets(rom5) == b'-- fichier de quelqu un d autre', 'rom0 fichier non vide : contenu modifie')
    open(rom5, 'wb').close()
    code = lance('rom_ok', '--rom0', '5', '--accord-dossier-jeu')
    verifie(code == 0, 'rom0 avec accord : code de sortie %r' % (code,))
    verifie(os.path.getsize(rom5) == 0, 'rom0 : le fichier du jeu n\'est pas revenu VIDE')
    verifie(ea.manifeste(racine) == avant, 'rom0 : le dossier de donnees a change')
    verifie(not os.path.exists(os.path.join(racine, 'mods', 'cc2_auto')), 'rom0 : un mod a ete cree')
    rapport = lire_octets(os.path.join(os.environ['LOCALAPPDATA'], 'cc2_essais_auto', '%s_rom_ok' % __import__('datetime').date.today().isoformat(), 'rapport.txt')).decode('utf-8')
    verifie('remis VIDE' in rapport and 'tout est remis en etat' in rapport, 'rom0 : rapport incomplet')

    # 2c. touche_jeu.ps1 : sans le jeu, rien n'est envoye
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ea.TOUCHE_PS1], capture_output=True, text=True, timeout=60)
    verifie(r.stdout.strip() == 'PAS_DE_FENETRE', 'touche_jeu.ps1 sans jeu : %r' % r.stdout)

    # 3. remise en etat apres modifications par le "jeu"
    sauv = os.path.join(tmp, 'sauv')
    shutil.copytree(os.path.join(racine, 'saved_games'), os.path.join(sauv, 'saved_games'))
    for n in ('persistent_data.xml', 'settings.xml', 'mods.xml'):
        shutil.copyfile(os.path.join(racine, n), os.path.join(sauv, n))
    reference = ea.manifeste(racine)
    with open(os.path.join(racine, 'saved_games', 'slot_19', 'save.xml'), 'wb') as f:
        f.write(b'<save>modifie par le jeu</save>')           # modifie
    with open(os.path.join(racine, 'saved_games', 'slot_20.xml'), 'wb') as f:
        f.write(b'nouveau')                                     # cree
    os.remove(os.path.join(racine, 'saved_games', 'slot_18', 'save.xml'))   # supprime
    with open(os.path.join(racine, 'persistent_data.xml'), 'wb') as f:
        f.write(b'<data changed="1"/>')
    with open(os.path.join(racine, 'mods.xml'), 'wb') as f:
        f.write(b'<data/>')
    quarantaine = os.path.join(tmp, 'quarantaine')
    lignes = []
    pb = ea.restaurer_fichiers(racine, sauv, quarantaine, lambda *a: lignes.append(' '.join(str(x) for x in a)))
    verifie(pb == 0, 'restauration : %d probleme(s) : %s' % (pb, lignes))
    verifie(ea.manifeste(racine) == reference, 'restauration : dossier de donnees different de la reference')
    verifie(os.path.isfile(os.path.join(quarantaine, 'slot_20.xml')), 'restauration : fichier cree par le jeu non mis de cote')

    # 4. capture de fenetre sur une petite fenetre de test creee (et fermee) par ce test : jamais une fenetre de l'utilisateur
    code = ("import tkinter as t\nr = t.Tk()\nr.title('cc2_test_capture')\nr.geometry('420x300+150+150')\n"
            "t.Label(r, text='fenetre de test de capture', font=('Arial', 20)).pack(expand=True)\nr.after(12000, r.destroy)\nr.mainloop()\n")
    fen = subprocess.Popen([sys.executable, '-c', code])
    try:
        png = os.path.join(tmp, 'capture.png')
        res = ''
        for _ in range(10):
            time.sleep(1)
            r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ea.CAPTURE_PS1,
                                '-Sortie', png, '-Processus', os.path.splitext(os.path.basename(sys.executable))[0]],
                               capture_output=True, text=True, timeout=60)
            res = r.stdout.strip()
            if res.startswith('OK'):
                break
        verifie(res.startswith('OK') and os.path.getsize(png) > 1000, 'capture de fenetre : %r' % res)
        if os.path.isfile(png):
            with open(png, 'rb') as f:
                verifie(f.read(8) == b'\x89PNG\r\n\x1a\n', 'capture : pas un PNG')
        print('capture de test :', res, '(fichier temporaire, supprime a la fin)')
    finally:
        fen.terminate()

    # 5. lecture des rapports de plantage : ne doit pas planter
    sortie = ea.evenements_plantage(__import__('datetime').datetime.now() - __import__('datetime').timedelta(minutes=1))
    verifie(isinstance(sortie, str), 'evenements_plantage')

    # 5 bis. entrees : absolues, relatives ("mN" = N s apres le premier message du script) et touche maintenue
    ab = ea.analyser_entrees('1:clic;m5:touche:w:300;7:touche:d:1500')
    re_ = ea.analyser_entrees('1:clic;m5:touche:w:300;7:touche:d:1500', True)
    verifie([t for t, _, _ in ab] == [1, 7] and [t for t, _, _ in re_] == [5], 'analyser_entrees : absolues et relatives separees')
    verifie(re_[0][2] == ['-Type', 'touche', '-Touche', 'w', '-Duree', '300'], 'analyser_entrees : touche maintenue')

    # 6. recherche des boutons : courrier sans avions (la partie n'est pas encore installee) -> on attend, on ne plante pas ;
    #    puis tous les avions en baie (etat 4) -> aucun appui ne les fait sortir : fin du balayage sans erreur
    racine6 = os.path.join(tmp, 'racine6')
    os.makedirs(racine6)
    pd = os.path.join(racine6, 'persistent_data.xml')
    with open(pd, 'w', encoding='utf-8') as f:
        f.write('<d host_password="CA;attente;t=300;cmd=-;noeuds=?;foc=false;"/>')
    verifie(ea.lire_etats_avions(racine6) == [], 'lire_etats_avions : courrier sans avions = liste vide')
    with open(pd, 'w', encoding='utf-8') as f:
        f.write('<d host_password="CA;etat;t=1953;a1=-/-/-/-/-/st4/f1.00/m1.00/w1;a2=-/-/-/-/-/st4/f1.00/m1.00/w1;"/>')
    verifie(ea.lire_etats_avions(racine6) == [4, 4], 'lire_etats_avions : deux avions en baie')
    appels = []
    vrai_envoi, vrai_sommeil, vraie_capture = ea.envoyer_entree, ea.time.sleep, ea.capturer
    ea.envoyer_entree = lambda args: appels.append(args) or 'OK'
    ea.time.sleep = lambda s: None
    ea.capturer = lambda *a, **k: 'OK'
    try:
        res = ea.chercher_boutons(racine6, tmp, lambda *t: None)
    finally:
        ea.envoyer_entree, ea.time.sleep, ea.capturer = vrai_envoi, vrai_sommeil, vraie_capture
    verifie(res.startswith('FIN du balayage') and appels, 'chercher_boutons : balayage sans erreur (%r, %d appels)' % (res, len(appels)))
    verifie(any('clic' in a for a in appels) and any('e' in a for a in appels), 'chercher_boutons : essaie E et le clic gauche')
    # joueur attache a un ecran (foc=true) : on ne clique jamais, on s'arrete
    with open(pd, 'w', encoding='utf-8') as f:
        f.write('<d host_password="CA;etat;t=1;foc=true;a1=-/-/-/-/-/st4/f1.00;"/>')
    appels.clear()
    ea.envoyer_entree, ea.time.sleep, ea.capturer = (lambda args: appels.append(args) or 'OK'), (lambda s: None), (lambda *a, **k: 'OK')
    try:
        res = ea.chercher_boutons(racine6, tmp, lambda *t: None)
    finally:
        ea.envoyer_entree, ea.time.sleep, ea.capturer = vrai_envoi, vrai_sommeil, vraie_capture
    verifie(res.startswith('ARRET') and not any('clic' in a for a in appels), 'chercher_boutons : attache a un ecran -> aucun clic (%r)' % res)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('%d verifications reussies, %d echec(s)' % (ok_total, ko))
sys.exit(1 if ko else 0)
