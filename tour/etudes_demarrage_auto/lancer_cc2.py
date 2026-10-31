#!/usr/bin/env python3
"""Lanceur de Carrier Command 2 avec RELANCE AUTOMATIQUE si le jeu plante au demarrage (voir ETUDE.md, option B).

  python -I lancer_cc2.py [--exe CHEMIN] [--essais 3] [--surveillance 180] [--lancement-max 180] [--a-blanc]

Ce que ca fait : lance le jeu (par Steam ; ou, avec --exe, un exe d'essai du dossier du jeu, directement) puis le surveille pendant
--surveillance secondes. Si le jeu s'arrete dans ce delai ET que Windows a ecrit un rapport de plantage (journal « Application Error »),
il note le code et l'adresse du plantage (0x1EF518 / 0x1EF525 : celle de l'etude) et RELANCE (3 essais au plus). Si le jeu tient jusqu'au
bout du delai, il se retire en laissant le jeu tourner. Si le jeu s'arrete SANS rapport de plantage (tu l'as ferme, ou le jeu s'est
quitte), il ne relance pas.
Il n'ecrit RIEN dans le jeu ni dans ses donnees ; seul fichier ecrit : %LOCALAPPDATA%\\cc2_demarrage_auto\\lancements.log (une ligne par
evenement). Refuse de demarrer si un exe du jeu tourne deja. --a-blanc : verifie tout (etat du demarrage auto compris), ne lance rien.
Codes de sortie : 0 jeu en route, 1 tous les essais ont plante, 2 refus ou lancement impossible, 3 arret sans plantage (pas de relance)."""
import argparse
import datetime
import importlib.util
import os
import re
import subprocess
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
APPID = '1489630'
JEU_DEFAUT = r'C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2'


def charger_installateur():
    spec = importlib.util.spec_from_file_location('demarrage_auto', os.path.join(ICI, 'demarrage_auto.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


da = charger_installateur()
processus_jeu = da.processus_jeu


def journal(texte):
    ligne = '%s  %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), texte)
    print(ligne, flush=True)
    base = os.environ.get('LOCALAPPDATA')
    if base:
        try:
            dossier = os.path.join(base, 'cc2_demarrage_auto')
            os.makedirs(dossier, exist_ok=True)
            with open(os.path.join(dossier, 'lancements.log'), 'a', encoding='utf-8') as f:
                f.write(ligne + '\n')
        except OSError:
            pass


def evenements_plantage(depuis):
    """Rapports de plantage Windows concernant carrier_command* depuis `depuis` : liste de (heure, message sur une ligne)."""
    cmd = ("Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Application Error'; StartTime=[datetime]'%s'} "
           "-ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'carrier_command' } | "
           "ForEach-Object { $_.TimeCreated.ToString('HH:mm:ss') + '|' + ($_.Message -replace '\\r?\\n', ' / ') }"
           % depuis.strftime('%Y-%m-%dT%H:%M:%S'))
    try:
        sortie = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=90).stdout
    except Exception:
        return []
    res = []
    for ligne in sortie.splitlines():
        if '|' in ligne:
            h, m = ligne.split('|', 1)
            res.append((h.strip(), m.strip()))
    return res


def analyser_plantage(message):
    """(code d'exception, decalage) lus dans un rapport « Application Error » (anglais ou francais : on prend les nombres hexadecimaux dans l'ordre).
    Le rapport donne le code (0xc0000005) puis, juste apres, le decalage dans le module (0x001ef518) : meme ordre dans toutes les langues."""
    jetons = re.findall(r'0x[0-9a-fA-F]+', message)
    for i, j in enumerate(jetons):
        if re.fullmatch(r'0x[cC][0-9a-fA-F]{7}', j) and i + 1 < len(jetons):
            return j.lower(), jetons[i + 1].lower()
    return None, None


def demarrer_jeu(exe):
    if exe:
        subprocess.Popen([exe], cwd=os.path.dirname(os.path.abspath(exe)))     # exe d'essai : lance directement (le dossier du jeu doit etre le dossier courant)
    else:
        os.startfile('steam://rungameid/%s' % APPID)


def attendre_processus(delai):
    t0 = time.time()
    while time.time() - t0 < delai:
        p = processus_jeu()
        if p:
            return p[0]
        time.sleep(3)
    return None


def attendre_rapport(depuis, delai=15):
    """Windows met quelques secondes a ecrire le rapport de plantage : on guette jusqu'a `delai` secondes."""
    t0 = time.time()
    while True:
        evs = evenements_plantage(depuis)
        if evs or time.time() - t0 >= delai:
            return evs
        time.sleep(3)


def un_essai(a, numero):
    """'ok' (le jeu tient), 'plante', 'arret' (arret sans plantage), 'pas_lance'."""
    depuis = datetime.datetime.now() - datetime.timedelta(seconds=2)
    journal('essai %d/%d : lancement (%s)' % (numero, a.essais, a.exe or 'Steam'))
    demarrer_jeu(a.exe)
    pid = attendre_processus(a.lancement_max)
    if pid is None:
        journal('le jeu ne s\'est pas lance en %d s' % a.lancement_max)
        return 'pas_lance'
    t0 = time.time()
    journal('jeu lance (pid %s), surveillance %d s' % (pid, a.surveillance))
    while time.time() - t0 < a.surveillance:
        time.sleep(2)
        p = processus_jeu()
        if p is not None and not p:
            duree = int(time.time() - t0)
            journal('le jeu s\'est arrete apres %d s' % duree)
            evs = attendre_rapport(depuis)
            if not evs:
                journal('aucun rapport de plantage Windows : arret volontaire ou sortie normale, je ne relance pas')
                return 'arret'
            for h, m in evs:
                code, decalage = analyser_plantage(m)
                journal('PLANTAGE a %s : code %s, decalage %s%s | %s' % (h, code, decalage,
                        ' (= l\'adresse connue 0x1EF518/0x1EF525 de l\'etude)' if decalage in ('0x001ef518', '0x001ef525', '0x1ef518', '0x1ef525') else '',
                        m[:160]))
            return 'plante'
    journal('le jeu tourne toujours apres %d s : je me retire, il continue' % a.surveillance)
    return 'ok'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument('--exe', default=None, help='exe d\'essai a lancer directement (au lieu de Steam)')
    ap.add_argument('--essais', type=int, default=3)
    ap.add_argument('--surveillance', type=int, default=180, help='secondes de surveillance apres le lancement (defaut 180)')
    ap.add_argument('--lancement-max', type=int, default=180, help='secondes pour que le processus apparaisse (defaut 180)')
    ap.add_argument('--a-blanc', action='store_true', help='ne lance rien : verifie seulement')
    ap.add_argument('--dossier-jeu', default=JEU_DEFAUT)
    ap.add_argument('--racine', default=None)
    a = ap.parse_args()
    if not 1 <= a.essais <= 10:
        sys.exit('REFUS : --essais : entre 1 et 10')
    if a.exe and not os.path.isfile(a.exe):
        sys.exit('REFUS : --exe introuvable : %s' % a.exe)
    p = processus_jeu()
    if p is None:
        journal('REFUS : je ne peux pas verifier si le jeu tourne')
        return 2
    if p:
        journal('REFUS : un exe du jeu tourne deja (pid %s). Rien n\'est lance.' % ', '.join(p))
        return 2
    # information (lecture seule) : le demarrage automatique est-il arme ?
    b = argparse.Namespace(racine=a.racine or da.racine_defaut(), dossier_jeu=a.dossier_jeu, rom=0, mode='nouvelle', partie=19, attente=30,
                           attendre_touche=False, date=None)
    c = da.chemins(b)
    roms = [n for n in range(10) if da.etat_rom(os.path.join(c['scripts_rom'], 'library_custom_%d.lua' % n))[0] == 'notre script']
    arme = os.path.isfile(c['mods_xml']) and da.ligne_mods_xml(c) in da.lire(c['mods_xml']).decode('utf-8', 'replace').replace('\r\n', '\n')
    journal('demarrage automatique : script %s, interrupteur %s' % (('pose (library_custom_%s)' % ', '.join(map(str, roms))) if roms else 'ABSENT',
                                                                   'COCHE' if arme else 'decoche'))
    if a.a_blanc:
        journal('--a-blanc : rien n\'est lance.')
        return 0
    resultat = None
    for n in range(1, a.essais + 1):
        resultat = un_essai(a, n)
        if resultat in ('ok', 'arret', 'pas_lance'):
            break
        if n < a.essais:
            t0 = time.time()
            while processus_jeu() and time.time() - t0 < 30:       # le processus plante peut mettre un moment a disparaitre
                time.sleep(2)
            journal('on relance')
    code = {'ok': 0, 'plante': 1, 'pas_lance': 2, 'arret': 3}[resultat]
    if resultat == 'plante':
        journal('%d essai(s), tous termines par un plantage' % a.essais)
    return code


if __name__ == '__main__':
    sys.exit(main())
