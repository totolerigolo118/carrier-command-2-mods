#!/usr/bin/env python3
"""Essai automatique en jeu, SANS personne devant l'ecran (tour Windows) -- equivalent du banc du Mac.

  python -I essai_auto.py lancer ETIQUETTE [--racine DOSSIER] [--duree-max SEC] [--intervalle SEC] [--sans-lancer]

Ce que ca fait, dans l'ordre (tout est annule a la fin, meme en cas d'erreur) :
  1. refuse si le jeu tourne deja ou si l'executable n'est pas dans l'etat attendu ;
  2. sauvegarde saved_games, persistent_data.xml, settings.xml et mods.xml dans <sortie>\\sauvegardes (empreintes sha256) ;
  3. installe le mod de test cc2_auto (tour\\auto\\library_custom_5.lua) et ajoute UNE ligne a mods.xml ;
  4. lance le jeu par Steam ; le script de test charge la sauvegarde 18, sort et rappelle 4 avions, affiche le bilan
     sur l'ecran, puis quitte le jeu tout seul ;
  5. pendant ce temps, capture la FENETRE du jeu (pas tout l'ecran) toutes les N secondes dans <sortie>\\captures ;
  6. s'il faut, ferme le jeu poliment (puis de force apres 30 s) a la fin du delai ;
  7. remet mods.xml, retire le mod, remet les sauvegardes a l'identique (les fichiers crees par le jeu sont deplaces
     dans <sortie>\\ajoutes_pendant_essai, jamais supprimes), verifie par sha256 et ecrit rapport.txt.
Aucun fichier du jeu n'est ecrit (ni exe, ni rom_0). Pas de reseau. <sortie> = %LOCALAPPDATA%\\cc2_essais_auto\\<date>_<etiquette>.
"""
import argparse
import re
import datetime
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
SRC_SCRIPT = os.path.normpath(os.path.join(ICI, '..', 'auto', 'library_custom_5.lua'))
CAPTURE_PS1 = os.path.join(ICI, 'capture_fenetre.ps1')
TOUCHE_PS1 = os.path.join(ICI, 'touche_jeu.ps1')
ENTREE_PS1 = os.path.join(ICI, 'entree_jeu.ps1')
ENTREES_DEFAUT = '8:touche:shift;16:touche:shift;24:touche:shift'
NOM_MOD = 'cc2_auto'
APPID = '1489630'
EXE_JEU = r'C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2\carrier_command.exe'
EXE_ATTENDU = '8E7FCBB6CE27BD3D8FEB02BF7F3DBBA646CCE6D4944360570F082972E8DFE8BE'   # ascenseur_x2 + temps_x2
MOD_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<data name="Essai auto CC2" author="Yolo" description="A activer SEULEMENT pour un essai sans personne devant '
           'l ecran (outil essai_auto.py, qui l ajoute et le retire tout seul). Charge la sauvegarde 18, sort et rappelle 4 '
           'avions, affiche le bilan en haut a gauche, puis quitte le jeu. Ne modifie aucun fichier.">\n</data>\n')


def charger_mod_mesures():
    """Reutilise png_uni / valider_xml du programme d'installation du mod de mesures."""
    spec = importlib.util.spec_from_file_location('mod_mesures', os.path.join(ICI, 'mod_mesures.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sha(octets):
    return hashlib.sha256(octets).hexdigest().upper()


def lire(p):
    with open(p, 'rb') as f:
        return f.read()


def ecrire_atomique(p, octets):
    tmp = p + '.cc2_tmp'
    try:
        with open(tmp, 'wb') as f:
            f.write(octets)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def manifeste(dossier):
    """{chemin relatif : sha256} de tous les fichiers d'un dossier (vide si le dossier n'existe pas)."""
    res = {}
    if os.path.isdir(dossier):
        for rac, _, fichiers in os.walk(dossier):
            for n in fichiers:
                p = os.path.join(rac, n)
                res[os.path.relpath(p, dossier)] = sha(lire(p))
    return res


def processus_jeu():
    """PID du jeu (liste), ou None si je ne peux pas le verifier."""
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq carrier_command.exe', '/NH', '/FO', 'CSV'],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return None
    pids = []
    for ligne in out.splitlines():
        if 'carrier_command.exe' in ligne.lower():
            champs = [c.strip('"') for c in ligne.split('","')]
            if len(champs) > 1:
                pids.append(champs[1].strip('"'))
    return pids


class Rapport:
    def __init__(self, chemin):
        self.chemin = chemin
        self.t0 = time.time()

    def __call__(self, *a):
        ligne = '%s  %s' % (datetime.datetime.now().strftime('%H:%M:%S'), ' '.join(str(x) for x in a))
        print(ligne, flush=True)
        with open(self.chemin, 'a', encoding='utf-8') as f:
            f.write(ligne + '\n')


def capturer(sortie_png, log, rouvrir=False, surlignage=False):
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', CAPTURE_PS1, '-Sortie', sortie_png]
                       + (['-Rouvrir'] if rouvrir else []) + (['-Surlignage'] if surlignage else []),
                       capture_output=True, text=True, timeout=60)
    return r.stdout.strip() or r.stderr.strip()[:200]


def envoyer_touche():
    """Une touche (Maj) a la fenetre du jeu, seulement si elle est au premier plan (voir touche_jeu.ps1)."""
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', TOUCHE_PS1],
                       capture_output=True, text=True, timeout=60)
    return r.stdout.strip() or r.stderr.strip()[:200]


def analyser_entrees(texte, relatives=False):
    """'45:souris:0:90;48:touche:e;55:clic' -> [(45, ['-Type','souris','-Dx','0','-Dy','90']), ...] trie par instant.
    relatives=False : seulement les instants absolus (secondes depuis le lancement) ; True : seulement ceux en "mN" (secondes apres le premier message du script)."""
    res = []
    for morceau in [m.strip() for m in texte.split(';') if m.strip()]:
        champs = morceau.split(':')
        if champs[0].startswith('m') != relatives:       # "m150:..." = 150 s apres le premier message du script (partie demarree)
            continue
        t, genre = int(champs[0].lstrip('m')), champs[1]
        if genre == 'touche':           # touche:nom[:duree_ms] ; avec une duree, la touche est MAINTENUE (marcher : d, a, w, s)
            args = ['-Type', 'touche', '-Touche', champs[2]] + (['-Duree', champs[3]] if len(champs) > 3 else [])
        elif genre == 'souris':
            args = ['-Type', 'souris', '-Dx', champs[2], '-Dy', champs[3]]
        elif genre == 'curseur':
            args = ['-Type', 'curseur', '-X', champs[2], '-Y', champs[3]]
        elif genre == 'boutons':        # recherche fine des boutons de baie autour de la vue courante, avec retour d'etat des avions
            args = ['BOUTONS', champs[2] if len(champs) > 2 else '']
        elif genre == 'balayer':        # balayage du pont : cherche l'ecran qui prend le focus du joueur (foc=true dans la boite aux lettres)
            args = ['BALAYER', champs[2] if len(champs) > 2 else '']
        elif genre == 'viser':          # boucle fermee : amene la ligne surlignee du menu sur y = champs[2] (colonne x = champs[3] ou 585)
            args = ['VISER', champs[2], champs[3] if len(champs) > 3 else '585']
        elif genre == 'clic':
            args = ['-Type', 'clic']
        else:
            raise ValueError('entree inconnue : %s' % morceau)
        res.append((t, morceau, args))
    return sorted(res, key=lambda x: x[0])


def envoyer_entree(args):
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ENTREE_PS1] + args,
                       capture_output=True, text=True, timeout=60)
    return r.stdout.strip() or r.stderr.strip()[:200]


def viser_ligne(y_cible, x, sortie, log, essais=8):
    """Boucle fermee sur le menu : place le curseur, lit sur une capture quelle ligne est surlignee, corrige jusqu'a tomber sur y_cible."""
    y_curseur = y_cible
    envoyer_entree(['-Type', 'curseur', '-X', str(x), '-Y', str(y_curseur)])
    for k in range(1, essais + 1):
        time.sleep(1.2)
        png = os.path.join(sortie, 'captures', 'viser_%d_%d.png' % (y_cible, k))
        res = capturer(png, log, False, True)
        surligne = None
        for ligne in res.splitlines():
            if ligne.startswith('SURLIGNE ') and ligne.split()[1].lstrip('-').isdigit():
                surligne = int(ligne.split()[1])
        log('  viser %d, essai %d : curseur y=%d -> ligne surlignee y=%s' % (y_cible, k, y_curseur, surligne))
        if surligne is not None and abs(surligne - y_cible) <= 14:
            return 'OK (ligne surlignee y=%d, curseur y=%d)' % (surligne, y_curseur)
        if surligne is None:
            y_curseur += 6 if k % 2 else -12          # rien de surligne : on secoue un peu
        else:
            y_curseur += int(0.8 * (y_cible - surligne))
        y_curseur = min(max(y_curseur, y_cible - 90), y_cible + 90)      # jamais loin de la cible : pas de derive
        envoyer_entree(['-Type', 'curseur', '-X', str(x), '-Y', str(y_curseur)])
    return 'ECHEC : la ligne voulue n a pas ete atteinte'


def lire_foc(racine):
    """foc=true/false/? lu dans la boite aux lettres (mot de passe d'hebergement de persistent_data.xml)."""
    try:
        txt = lire(os.path.join(racine, 'persistent_data.xml')).decode('utf-8', 'replace')
    except Exception:
        return None
    m = re.search(r'host_password="[^"]*foc=(true|false|\?)', txt)
    return m.group(1) if m else None


def lire_etats_avions(racine):
    """Etats d'accostage (st<n>) des avions suivis, lus dans la boite aux lettres ; None si illisible."""
    try:
        txt = lire(os.path.join(racine, 'persistent_data.xml')).decode('utf-8', 'replace')
    except Exception:
        return None
    m = re.search(r'host_password="([^"]*)"', txt)
    if not m:
        return None
    return [int(x) for x in re.findall(r'/st(\d+)/', m.group(1))]


def chercher_boutons(racine, sortie, log):
    """Cherche les boutons de baie : balaie finement autour de la vue courante (pas de souris relatifs). A chaque point : capture de ce que
    vise la mire, puis appui sur E, puis clic gauche, en suivant le nombre d'avions sortis de l'etat 4 (range). Un bouton est un
    BASCULEUR : si le nombre baisse, on rappuie avec la meme methode. Si E attache le joueur a un ecran (foc=true), on ressort avec Echap
    avant de continuer (jamais de clic ni de mouvement de souris pendant qu'on est attache)."""
    souris = lambda dx, dy: envoyer_entree(['-Type', 'souris', '-Dx', str(dx), '-Dy', str(dy)])
    touche = lambda nom: envoyer_entree(['-Type', 'touche', '-Touche', nom])
    methodes = (('E', lambda: touche('e')), ('clic', lambda: envoyer_entree(['-Type', 'clic'])))
    refus = [0]
    def controle(res, quoi):
        """Une entree refusee (jeu pas au premier plan, fenetre perdue...) ne doit pas passer inapercue : on le note, et on s'arrete a 3 de suite."""
        if str(res).startswith('OK'):
            refus[0] = 0
            return True
        refus[0] += 1
        log('  boutons : %s REFUSE (%s)' % (quoi, str(res)[:80]))
        return False
    def sortis():
        e = lire_etats_avions(racine)
        return None if not e else (sum(1 for x in e if x != 4), len(e))
    cx, cy = 0, 0
    deb = sortis()
    t_attente = time.time()
    while deb is None and time.time() - t_attente < 120:     # le script ne liste les avions qu'une fois la partie installee (attente ~30 s)
        time.sleep(3)
        deb = sortis()
    if deb is None:
        return 'ECHEC : courrier illisible (aucun avion liste en 2 minutes)'
    log('  boutons : depart, avions sortis du hangar = %s' % (deb,))
    sens = 1
    for cible_y in range(-40, 14, 8):
        colonnes = list(range(-10, 64, 8))
        if sens < 0:
            colonnes.reverse()
        for cible_x in colonnes:
            dx, dy = cible_x - cx, cible_y - cy
            if dx or dy:
                controle(souris(dx, dy), 'souris')
                cx, cy = cible_x, cible_y
            time.sleep(0.8)
            res_c = capturer(os.path.join(sortie, 'captures', 'bouton_x%+d_y%+d.png' % (cx, cy)), log, False, False)    # ce que vise la mire
            if not str(res_c).startswith('OK'):
                log('  boutons : capture en (%+d, %+d) : %s' % (cx, cy, res_c))
                refus[0] += 1
            if refus[0] >= 3:
                return 'ARRET : 3 refus de suite (fenetre perdue ou plus au premier plan) en (%+d, %+d)' % (cx, cy)
            for nom_m, appuyer in methodes:
                if lire_foc(racine) == 'true':
                    return 'ARRET : joueur attache a un ecran avant %s en (%+d, %+d), je ne clique pas' % (nom_m, cx, cy)
                avant = sortis()
                controle(appuyer(), nom_m)
                time.sleep(2.4)
                if lire_foc(racine) == 'true':
                    capturer(os.path.join(sortie, 'captures', 'attache_%s_x%+d_y%+d.png' % (nom_m, cx, cy)), log, False, False)
                    touche('escape')
                    time.sleep(3)
                    log('  boutons : %s en (%+d, %+d) -> joueur ATTACHE a un ecran (foc=true), sorti avec Echap' % (nom_m, cx, cy))
                    break
                apres = sortis()
                if avant and apres and apres[0] != avant[0]:
                    log('  boutons : %s en (%+d, %+d) -> avions sortis %d -> %d / %d' % (nom_m, cx, cy, avant[0], apres[0], apres[1]))
                    capturer(os.path.join(sortie, 'captures', 'effet_%s_x%+d_y%+d.png' % (nom_m, cx, cy)), log, False, False)
                    if apres[0] < avant[0]:
                        appuyer()                       # basculeur : on a annule, on relance
                        time.sleep(3.2)
                        log('  boutons : relance -> %s' % (sortis(),))
                    fin = sortis()
                    if fin and fin[0] >= apres[1]:
                        return 'OK : les %d avions sont partis (%s, dernier appui en (%+d, %+d))' % (apres[1], nom_m, cx, cy)
        sens = -sens
    fin = sortis()
    return 'FIN du balayage : avions sortis = %s' % (fin,)


def balayer_pupitre(racine, sortie, log):
    """Balaye le pont (rotations de la vue par pas de souris relatifs), appuie sur E a chaque point et s'arrete des que le joueur
    est ATTACHE a un ecran (foc=true). Ressort ensuite avec Echap. Sans rien casser : ne clique jamais ; E seulement si la fenetre
    du jeu est au premier plan (entree_jeu.ps1)."""
    souris = lambda dx, dy: envoyer_entree(['-Type', 'souris', '-Dx', str(dx), '-Dy', str(dy)])
    touche = lambda nom: envoyer_entree(['-Type', 'touche', '-Touche', nom])
    cx, cy = 0, 0
    sens = 1
    for ligne, cible_y in enumerate([40, 80, 120, 160]):
        colonnes = [-120, -80, -40, 0, 40, 80, 120]
        if sens < 0:
            colonnes.reverse()
        for cible_x in colonnes:
            dx, dy = cible_x - cx, cible_y - cy
            if dx or dy:
                souris(dx, dy)
                cx, cy = cible_x, cible_y
            time.sleep(1.2)
            capturer(os.path.join(sortie, 'captures', 'balayage_x%d_y%d_avant.png' % (cx, cy)), log, False, False)    # voir l'invite "interact"
            touche('e')
            for _ in range(6):                      # le courrier est mis a jour toutes les ~2 s
                time.sleep(1.0)
                if lire_foc(racine) == 'true':
                    break
            etat = lire_foc(racine)
            log('  balayage (x=%d, y=%d) : foc=%s' % (cx, cy, etat))
            if etat == 'true':
                png = os.path.join(sortie, 'captures', 'attache_x%d_y%d.png' % (cx, cy))
                capturer(png, log, False, False)
                touche('escape')
                time.sleep(3)
                return 'ATTACHE en (x=%d, y=%d)' % (cx, cy)
        sens = -sens
    return 'ECHEC : aucun point du balayage ne donne le focus'


def restaurer_fichiers(racine, sauv, quarantaine, log):
    """Remet a l'identique saved_games / persistent_data / settings / mods.xml depuis la sauvegarde. Rien n'est supprime."""
    pb = 0
    # fichiers isoles
    for nom in ('persistent_data.xml', 'settings.xml', 'mods.xml'):
        src, dst = os.path.join(sauv, nom), os.path.join(racine, nom)
        if os.path.isfile(src) and (not os.path.isfile(dst) or lire(src) != lire(dst)):
            ecrire_atomique(dst, lire(src))
            log('remis a l identique :', nom)
    # saved_games : meme principe, fichier par fichier
    sg_s, sg_d = os.path.join(sauv, 'saved_games'), os.path.join(racine, 'saved_games')
    avant = manifeste(sg_s)
    apres = manifeste(sg_d)
    for rel in sorted(set(apres) - set(avant)):                    # crees par le jeu : mis de cote, pas supprimes
        dst = os.path.join(quarantaine, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(os.path.join(sg_d, rel), dst)
        log('cree pendant l essai, mis de cote :', rel)
    for rel, h in sorted(avant.items()):
        p = os.path.join(sg_d, rel)
        if apres.get(rel) != h:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            shutil.copyfile(os.path.join(sg_s, rel), p)
            log('sauvegarde remise a l identique :', rel)
    # verification finale
    if manifeste(sg_d) != avant:
        log('ALERTE : saved_games differe encore de la sauvegarde'); pb += 1
    for nom in ('persistent_data.xml', 'settings.xml', 'mods.xml'):
        src, dst = os.path.join(sauv, nom), os.path.join(racine, nom)
        if os.path.isfile(src) and (not os.path.isfile(dst) or lire(src) != lire(dst)):
            log('ALERTE :', nom, 'differe encore de la sauvegarde'); pb += 1
    return pb


def evenements_plantage(depuis):
    cmd = ("Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Application Error'; StartTime=[datetime]'%s'} "
           "-ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'carrier_command' } | "
           "Select-Object -First 3 | ForEach-Object { $_.TimeCreated.ToString('HH:mm:ss') + ' ' + ($_.Message -split '\\r?\\n')[0] }"
           % depuis.strftime('%Y-%m-%dT%H:%M:%S'))
    try:
        return subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:
        return 'lecture impossible : %s' % e


def cmd_lancer(a):
    mm = charger_mod_mesures()
    racine = os.path.abspath(a.racine)
    vrai = os.path.normcase(racine) == os.path.normcase(os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2'))
    base = os.environ.get('LOCALAPPDATA') or ICI
    sortie = os.path.join(base, 'cc2_essais_auto', '%s_%s' % (datetime.date.today().isoformat(), a.etiquette))
    if os.path.exists(sortie):
        sys.exit('REFUS : %s existe deja (je n\'ecrase rien). Donne une autre etiquette.' % sortie)
    os.makedirs(os.path.join(sortie, 'captures'))
    os.makedirs(os.path.join(sortie, 'sauvegardes'))
    log = Rapport(os.path.join(sortie, 'rapport.txt'))
    log('essai auto', a.etiquette, '| racine', racine, '| sortie', sortie)

    # 1. garde-fous
    pids = processus_jeu()
    if pids is None or pids:
        sys.exit('REFUS : le jeu tourne deja (ou je ne peux pas le verifier). Rien n\'est ecrit.')
    if not a.sans_lancer and vrai:
        h = sha(lire(EXE_JEU))
        log('executable sha256', h)
        if h != EXE_ATTENDU and not a.exe_quelconque:
            sys.exit('REFUS : l\'executable n\'est pas dans l\'etat attendu (ascenseur_x2 + temps_x2). Rien n\'est ecrit.')
    mods_xml = os.path.join(racine, 'mods.xml')
    dossier_mod = os.path.join(racine, 'mods', NOM_MOD)
    mode_mod = a.rom0 is None and not a.rien
    rom_fichier = None
    if not mode_mod and not a.rien:
        # mode "dossier du jeu" (methode du Mac) : le script est pose DANS un fichier library_custom_N.lua d'origine, VIDE, de rom_0,
        # seul endroit charge aussi dans le menu ; il est remis VIDE a la fin. Exige l'accord explicite du moddeur.
        if not a.accord_dossier_jeu:
            sys.exit('REFUS : --rom0 ecrit dans le dossier du jeu ; il faut --accord-dossier-jeu (accord explicite du moddeur). Rien n\'est ecrit.')
        rom_fichier = os.path.join(a.dossier_jeu, 'rom_0', 'scripts', 'library_custom_%d.lua' % a.rom0)
        if not os.path.isfile(rom_fichier) or os.path.getsize(rom_fichier) != 0:
            sys.exit('REFUS : %s n\'est pas le fichier VIDE d\'origine : je n\'y touche pas. Rien n\'est ecrit.' % rom_fichier)
    elif mode_mod and os.path.exists(dossier_mod):
        sys.exit('REFUS : %s existe deja (je ne remplace jamais un dossier).' % dossier_mod)
    avant_mods = lire(mods_xml)
    txt = avant_mods.decode('utf-8')
    ligne = '\t\t<path value="%s"/>\n' % dossier_mod
    marque = '\t</active_mod_folders>'
    if mode_mod and ('\r\n' in txt or txt.count(marque) != 1 or ligne in txt):
        sys.exit('REFUS : mods.xml n\'a pas la forme attendue. Rien n\'est ecrit.')
    mm.valider_xml(avant_mods)
    source = lire(SRC_SCRIPT)

    # 2. sauvegardes
    sauv = os.path.join(sortie, 'sauvegardes')
    if os.path.isdir(os.path.join(racine, 'saved_games')):
        shutil.copytree(os.path.join(racine, 'saved_games'), os.path.join(sauv, 'saved_games'))
    for nom in ('persistent_data.xml', 'settings.xml', 'mods.xml'):
        if os.path.isfile(os.path.join(racine, nom)):
            shutil.copyfile(os.path.join(racine, nom), os.path.join(sauv, nom))
    if manifeste(os.path.join(sauv, 'saved_games')) != manifeste(os.path.join(racine, 'saved_games')) or lire(os.path.join(sauv, 'mods.xml')) != avant_mods:
        sys.exit('ERREUR : la sauvegarde n\'est pas identique a l\'original. Rien d\'autre n\'est ecrit.')
    log('sauvegardes faites :', len(manifeste(os.path.join(sauv, 'saved_games'))), 'fichiers de parties + mods.xml (sha256', sha(avant_mods)[:12] + ')')

    t_debut = datetime.datetime.now()
    pb = 0
    mod_installe = False
    try:
        if mode_mod:
            # 3a. mod de test (applique seulement quand une partie tourne : verifie en jeu, pas dans le menu)
            scripts = os.path.join(dossier_mod, 'content', 'scripts')
            os.makedirs(scripts)
            mod_installe = True
            # le meme script dans chaque slot demande ; chaque copie note son numero dans g_ca_slots
            for n in a.slots:
                octets = ('g_ca_slot_voulu = %d\ng_ca_slots = (g_ca_slots or "") .. "%d"\n' % (a.partie, n)).encode('ascii') + source
                chemin = os.path.join(scripts, 'library_custom_%d.lua' % n)
                with open(chemin, 'wb') as f:
                    f.write(octets)
                if lire(chemin) != octets:
                    raise RuntimeError('copie du script de test differente de la source (slot %d)' % n)
            with open(os.path.join(dossier_mod, 'mod.xml'), 'wb') as f:
                f.write(MOD_XML.encode('utf-8'))
            with open(os.path.join(dossier_mod, 'thumbnail.png'), 'wb') as f:
                f.write(mm.png_uni(128, (90, 50, 40)))
            nouveau = txt.replace(marque, ligne + marque)
            mm.valider_xml(nouveau.encode('utf-8'))
            ecrire_atomique(mods_xml, nouveau.encode('utf-8'))
            log('mod cc2_auto installe et ajoute a mods.xml (script sha256', sha(source)[:12] + ')')
        elif a.rien:
            log('--rien : AUCUN script (ni mod, ni dossier du jeu) : seules les entrees clavier/souris et les captures')
        else:
            # 3b. dossier du jeu : le fichier vide library_custom_N.lua recoit le script (remis vide dans le "finally")
            octets = ('g_ca_slot_voulu = %d\ng_ca_mode = "%s"\ng_ca_attente_menu = %d\ng_ca_slots = (g_ca_slots or "") .. "rom%d"\n'
                      % (a.partie, a.mode, a.attente_menu, a.rom0)).encode('ascii') + source
            with open(rom_fichier, 'wb') as f:
                f.write(octets)
            if lire(rom_fichier) != octets:
                raise RuntimeError('copie du script dans le dossier du jeu differente de la source')
            log('script pose dans', rom_fichier, '(sha256', sha(octets)[:12] + ') ; sera remis VIDE a la fin')

        if a.sans_lancer:
            log('--sans-lancer : le jeu n\'est PAS lance (essai a blanc)')
        else:
            # empeche la mise en veille / l'extinction de l'ecran pendant l'essai
            try:
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000003)
            except Exception:
                pass
            os.startfile('steam://rungameid/%s' % APPID)
            log('jeu demande a Steam')
            t0 = time.time()
            pid = None
            while time.time() - t0 < 180:
                p = processus_jeu()
                if p:
                    pid = p[0]
                    break
                time.sleep(3)
            if pid is None:
                raise RuntimeError('le jeu ne s\'est pas lance en 3 minutes')
            log('jeu lance, pid', pid, 'apres', int(time.time() - t0), 's')
            t_jeu = time.time()
            n = 0
            ferme = False
            entrees = analyser_entrees(a.entrees)      # ecran-titre "PRESS ANY KEY" puis navigation du menu (vrais clics)
            entrees_rel = analyser_entrees(a.entrees, True)     # armees au premier message du script (partie vraiment demarree)
            t_courrier = None
            derniere_capture = 0.0
            fin_guidage = None
            derniere_boite = [None]
            fichier_pd = os.path.join(racine, 'persistent_data.xml')
            while True:
                time.sleep(1)       # les entrees sont servies a la seconde (le rythme des captures est a part)
                if not processus_jeu():
                    log('le jeu s\'est ferme (apres %d s)' % int(time.time() - t_jeu))
                    break
                while entrees and time.time() - t_jeu >= entrees[0][0]:
                    _, texte_entree, args_entree = entrees.pop(0)
                    if args_entree and args_entree[0] == 'BOUTONS':
                        log('entree', texte_entree, ':', chercher_boutons(racine, sortie, log))
                    elif args_entree and args_entree[0] == 'BALAYER':
                        log('entree', texte_entree, ':', balayer_pupitre(racine, sortie, log))
                    elif args_entree and args_entree[0] == 'VISER':
                        log('entree', texte_entree, ':', viser_ligne(int(args_entree[1]), int(args_entree[2]), sortie, log))
                    else:
                        log('entree', texte_entree, ':', envoyer_entree(args_entree))
                    if not entrees:
                        fin_guidage = time.time() + 40      # captures rapprochees pendant et 40 s apres les entrees
                # boite aux lettres : le script ecrit ses mesures dans le mot de passe d'hebergement, que le jeu enregistre dans persistent_data.xml
                try:
                    import re as _re
                    m = _re.search(r'host_password="([^"]*)"', lire(fichier_pd).decode('utf-8', 'replace'))
                    if m and m.group(1).startswith('CA;') and t_courrier is None:
                        t_courrier = time.time() - t_jeu
                        log('partie demarree (premier message du script a %d s)' % int(t_courrier))
                        entrees = sorted(entrees + [(t_courrier + dt, txt, ar) for dt, txt, ar in entrees_rel], key=lambda x: x[0])
                        entrees_rel = []
                    if m and m.group(1) != derniere_boite[0]:
                        derniere_boite[0] = m.group(1)
                        if m.group(1):
                            log('boite aux lettres :', m.group(1))
                except Exception:
                    pass
                guide = bool(entrees) or bool(entrees_rel) or (fin_guidage is not None and time.time() < fin_guidage)
                if a.exiger_courrier and t_courrier is None and not ferme and time.time() - t_jeu > a.exiger_courrier:
                    log('ERREUR : aucun message du script apres %d s : la partie ne demarre pas (menu bloque ?) ; fermeture du jeu' % a.exiger_courrier)
                    pb += 1
                    ferme = True
                    subprocess.run(['taskkill', '/PID', pid], capture_output=True)
                    t_ferme = time.time()
                rythme = min(a.intervalle, 4) if guide else a.intervalle
                if time.time() - derniere_capture >= rythme:
                    derniere_capture = time.time()
                    n += 1
                    png = os.path.join(sortie, 'captures', '%03d_t%04ds.png' % (n, int(time.time() - t_jeu)))
                    res = capturer(png, log, a.rouvrir)
                    if not res.startswith('OK'):
                        log('capture %d : %s' % (n, res))
                        if os.path.exists(png):
                            os.remove(png)
                if time.time() - t_jeu > a.duree_max and not ferme:
                    ferme = True
                    log('delai maximum atteint (%d s) : fermeture polie du jeu' % a.duree_max)
                    subprocess.run(['taskkill', '/PID', pid], capture_output=True)
                    t_ferme = time.time()
                if ferme and time.time() - t_ferme > 30:
                    log('le jeu ne s\'est pas ferme : arret force')
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                    time.sleep(5)
                    if not processus_jeu():
                        break
            time.sleep(3)
            plantages = evenements_plantage(t_debut)
            log('rapports de plantage Windows pendant l\'essai :', plantages if plantages else 'aucun')
    except BaseException as e:      # y compris Ctrl+C : on remet tout en etat avant de repartir
        log('ERREUR :', repr(e))
        pb += 1
    finally:
        if rom_fichier is not None and os.path.isfile(rom_fichier) and os.path.getsize(rom_fichier) != 0:
            with open(rom_fichier, 'wb'):
                pass                                     # remis VIDE, comme a l'origine
            if os.path.getsize(rom_fichier) == 0:
                log('fichier du jeu remis VIDE :', rom_fichier)
            else:
                log('ALERTE : le fichier du jeu n\'est pas revenu vide :', rom_fichier)
                pb += 1
        if processus_jeu():
            # erreur de l'outil en cours d'essai : le jeu lance par CET essai est ferme (poliment, puis de force) avant de tout remettre
            log('ERREUR en cours d\'essai : fermeture du jeu avant de remettre les fichiers')
            for p_jeu in processus_jeu() or []:
                subprocess.run(['taskkill', '/PID', str(p_jeu)], capture_output=True)
            t_f = time.time()
            while processus_jeu() and time.time() - t_f < 30:
                time.sleep(1)
            for p_jeu in processus_jeu() or []:
                subprocess.run(['taskkill', '/F', '/PID', str(p_jeu)], capture_output=True)
            time.sleep(3)
        if processus_jeu():
            log('ALERTE : le jeu tourne encore, je ne remets pas les fichiers en place')
            pb += 1
        else:
            pb += restaurer_fichiers(racine, sauv, os.path.join(sortie, 'ajoutes_pendant_essai'), log)
            if mod_installe and os.path.isdir(dossier_mod):
                attendus = {os.path.join('content', 'scripts', 'library_custom_%d.lua' % n) for n in a.slots} | {'mod.xml', 'thumbnail.png'}
                presents = set(manifeste(dossier_mod))
                if presents <= attendus:
                    shutil.rmtree(dossier_mod)
                    log('mod cc2_auto retire')
                else:
                    log('ALERTE : le dossier du mod contient autre chose que ce que j\'y ai mis, je le laisse :', sorted(presents - attendus))
                    pb += 1
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        except Exception:
            pass
    log('FIN :', 'tout est remis en etat' if pb == 0 else '%d PROBLEME(S), voir ALERTE / ERREUR ci-dessus' % pb)
    print('Rapport :', os.path.join(sortie, 'rapport.txt'))
    print('Captures :', os.path.join(sortie, 'captures'))
    return 0 if pb == 0 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('lancer')
    p.add_argument('etiquette')
    p.add_argument('--racine', default=os.path.join(os.environ.get('APPDATA', ''), 'Carrier Command 2'))
    p.add_argument('--duree-max', type=int, default=1800, help='secondes avant fermeture du jeu (defaut 1800)')
    p.add_argument('--intervalle', type=int, default=15, help='secondes entre deux captures (defaut 15)')
    p.add_argument('--slots', default='5', help='numeros de library_custom ou installer le script, ex. 0,2,3,5,6,8 (defaut 5) ; '
                   'jamais 1, 4, 7, 9 (utilises par cc2_mesures)')
    p.add_argument('--rom0', type=int, default=None, help='au lieu du mod : pose le script dans rom_0\\scripts\\library_custom_N.lua '
                   '(fichier VIDE d\'origine, remis vide a la fin) ; seul moyen d\'agir dans le menu ; exige --accord-dossier-jeu')
    p.add_argument('--accord-dossier-jeu', action='store_true', help='a ne mettre qu\'avec l\'accord explicite du moddeur pour ecrire dans le dossier du jeu')
    p.add_argument('--dossier-jeu', default=os.path.dirname(EXE_JEU), help='dossier d\'installation du jeu (defaut : Steam)')
    p.add_argument('--partie', type=int, default=19, help='numero de la sauvegarde a charger (defaut 19 = partie de test de la tour ; '
                   '18 = ancienne partie du Mac : le chargement plante sur la tour)')
    p.add_argument('--mode', choices=('complet', 'menu_seul'), default='complet',
                   help='menu_seul : le script ne fait que charger la partie depuis le menu (isole un plantage du chargement)')
    p.add_argument('--rien', action='store_true', help='aucun script du tout : seulement les entrees clavier/souris (--entrees) et les captures (reference sans script)')
    p.add_argument('--attente-menu', type=int, default=28,
                   help='secondes de menu avant la demande de chargement (100000 = ne jamais charger : isole un plantage)')
    p.add_argument('--entrees', default=ENTREES_DEFAUT, help='entrees envoyees a la fenetre du jeu (seulement si elle est au premier plan) : '
                   '"instant:touche:nom;instant:souris:dx:dy;instant:clic" ; defaut : Maj a 8, 16 et 24 s (ecran-titre)')
    p.add_argument('--exiger-courrier', type=int, default=0, help='N secondes : si le script de test n a rien ecrit apres N s (partie non demarree), '
                   'le jeu est ferme et la passe est comptee en echec (le pilote de reessais recommence) ; 0 = pas de controle')
    p.add_argument('--rouvrir', action='store_true', help='essais SANS personne : rouvre la fenetre du jeu si elle est reduite (sinon la fenetre n est pas touchee)')
    p.add_argument('--sans-lancer', action='store_true', help='essai a blanc : tout sauf le lancement du jeu')
    p.add_argument('--exe-quelconque', action='store_true', help='ne verifie pas l\'etat de l\'executable')
    a = ap.parse_args()
    try:
        a.slots = sorted({int(x) for x in a.slots.split(',')})
    except ValueError:
        sys.exit('REFUS : --slots doit etre une liste de nombres, ex. 0,2,3,5,6,8')
    if not a.slots or any(n < 0 or n > 9 or n in (1, 4, 7, 9) for n in a.slots):
        sys.exit('REFUS : --slots : entre 0 et 9, sans 1, 4, 7, 9 (pris par cc2_mesures)')
    if a.rom0 is not None and not 0 <= a.rom0 <= 9:
        sys.exit('REFUS : --rom0 : un numero entre 0 et 9')
    sys.exit(cmd_lancer(a))


if __name__ == '__main__':
    main()
