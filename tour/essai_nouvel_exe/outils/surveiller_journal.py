#!/usr/bin/env python3
"""Surveille cc2x.log pendant une partie (LECTURE SEULE dans le dossier du jeu).

  python -I -B surveiller_journal.py copier  --jeu DOSSIER_DU_JEU --sortie FICHIER.log [--processus NOM.exe]
  python -I -B surveiller_journal.py alertes --jeu DOSSIER_DU_JEU [--depuis-fin]

`copier` : copie cc2x.log vers FICHIER (hors du jeu) toutes les 20 s tant que le processus du jeu tourne, puis une derniere fois
apres sa fermeture (le journal est recree a chaque lancement). N'ecrit que FICHIER ; refuse un FICHIER dans le dossier du jeu.
`alertes` : affiche, une par ligne, les lignes utiles du journal (demarrage, rappel, prise en charge, hangar, Hold, avertissements,
erreurs) et les ALERTES « REMONTE » de PROCEDURE_partie_v12.md (avant la prise en charge, avion en dock 5 ou 1) :
  (a) rel > 1,5 m/s sur deux releves qui montent ; (b) puissance lue 1,00 sur plus de 2 releves de suite ; (c) roues < 3/3 avec
  rel > 1 ; (d) HOOK H2 ... try k avec k >= 3 ; (e) UNEXPECTED ... runway state is 4. Apres TAKEN OVER, rel jusqu'a ~2,5 est normal.
Python standard seulement, aucun reseau.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

UTILES = ('ready for', 'plugin ', 'crochets poses', 'synchronisation posee', 'synchronisation NON', 'synchronisation arretee',
          'synchronisation n.', 'repond', 'loaded (frein', 'installed', 'could NOT', 'not loaded', 'unexpected', 'stays inactive',
          'session started', 'session ended', 'session commencee', 'session finie', 'RECALL start', 'RECALL ended', 'FORCE start',
          'HOOK H1', 'HOOK H2', 'HOOK H3', 'HOOK H5', 'PROBE take-over', 'VERDICT', 'TAKEN OVER', 'HANGAR', 'REFUEL',
          'UNEXPECTED', 'FOLLOW stopped', 'TOUCH TEST', 'AFTER THE TAKE-OVER', 'did not act', 'SILENT', '] warn:', '] error:')
RE_ID = re.compile(r'\[frein\] info: id (\d+)')
RE_CHAMP = {k: re.compile(k + r'=([-0-9.]+)') for k in ('rel', 'dock', 'power_read', 'power', 'brk')}
RE_ROUES = re.compile(r'wheels=(\d)/(\d)')
RE_TRY = re.compile(r'HOOK H2 .*try (\d+)')


def processus_vivant(nom):
    try:
        out = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {nom}', '/FO', 'CSV', '/NH'], capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return True                                         # dans le doute : on continue a copier
    return f'"{nom.lower()}"' in out.lower()               # CSV : nom complet (le tableau le coupe a 25 caracteres, 31/10)


def copier(args):
    jeu, sortie = Path(args.jeu), Path(args.sortie)
    if os.path.normcase(os.path.abspath(sortie)).startswith(os.path.normcase(os.path.abspath(jeu))):
        sys.exit('REFUS : la copie doit etre hors du dossier du jeu')
    log = jeu / 'cc2x.log'
    debut = time.time()
    while not (log.exists() and log.stat().st_mtime >= debut - 5):        # attendre le journal du nouveau lancement
        if time.time() - debut > 600:
            print('COPIE : aucun nouveau journal en 10 minutes, arret', flush=True)
            return
        time.sleep(5)
    vu = False
    while True:
        vivant = processus_vivant(args.processus)
        vu = vu or vivant
        try:
            shutil.copyfile(log, sortie)
        except OSError:
            pass
        if vu and not vivant:
            time.sleep(5)
            shutil.copyfile(log, sortie)
            print(f'COPIE FINIE : le jeu est ferme, journal copie vers {sortie} ({sortie.stat().st_size} octets)', flush=True)
            return
        time.sleep(20)


def alertes(args):
    log = Path(args.jeu) / 'cc2x.log'
    pos = log.stat().st_size if (args.depuis_fin and log.exists()) else 0
    reste = ''
    etat = {}                                               # id -> {'rels': [...], 'p1': n, 'pris': bool}
    dernier = {}                                            # (id, cle) -> heure de la derniere alerte
    debut = time.time()

    def alerte(i, cle, texte, ligne):
        if time.time() - dernier.get((i, cle), 0) < 10:
            return
        dernier[(i, cle)] = time.time()
        print(f'ALERTE REMONTE ({cle}) avion {i} : {texte} | {ligne[:220]}', flush=True)

    while True:
        if not log.exists():
            time.sleep(1)
            continue
        taille = log.stat().st_size
        if taille < pos:                                    # journal recree (nouveau lancement)
            pos, reste, etat = 0, '', {}
            print('JOURNAL RECREE (nouveau lancement)', flush=True)
        if taille > pos:
            with open(log, 'rb') as f:
                f.seek(pos)
                bloc = f.read(taille - pos)
            pos = taille
            texte = reste + bloc.decode('utf-8', errors='replace')
            lignes = texte.split('\n')
            reste = lignes.pop()
            for l in (x.rstrip('\r') for x in lignes):
                if any(k in l for k in UTILES) and 'FOLLOW +' not in l:
                    print(l[:300], flush=True)
                m = RE_ID.search(l)
                if not m:
                    continue
                i = m.group(1)
                e = etat.setdefault(i, {'rels': [], 'p1': 0, 'pris': False})
                if 'TAKEN OVER' in l:
                    e['pris'] = True
                if 'UNEXPECTED' in l and 'runway state is 4' in l:
                    alerte(i, 'e', 'etat de piste 4 inattendu', l)
                t = RE_TRY.search(l)
                if t and int(t.group(1)) >= 3:
                    alerte(i, 'd', f'HOOK H2 essai {t.group(1)}', l)
                d = RE_CHAMP['dock'].search(l)
                r = RE_CHAMP['rel'].search(l)
                if e['pris'] or not d or not r or d.group(1) not in ('5', '1'):
                    continue
                rel = float(r.group(1))
                e['rels'] = (e['rels'] + [rel])[-3:]
                if len(e['rels']) >= 3 and e['rels'][-1] > 1.5 and e['rels'][-3] < e['rels'][-2] < e['rels'][-1]:
                    alerte(i, 'a', f'rel monte {e["rels"]}', l)
                pw = RE_CHAMP['power_read'].search(l) or RE_CHAMP['power'].search(l)
                if pw and float(pw.group(1)) >= 0.995:
                    e['p1'] += 1
                    if e['p1'] > 2:
                        alerte(i, 'b', f'puissance 1,00 sur {e["p1"]} releves de suite', l)
                elif pw:
                    e['p1'] = 0
                w = RE_ROUES.search(l)
                if w and int(w.group(1)) < int(w.group(2)) and rel > 1:
                    alerte(i, 'c', f'roues {w.group(1)}/{w.group(2)} avec rel {rel}', l)
        time.sleep(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], allow_abbrev=False)
    ap.add_argument('commande', choices=('copier', 'alertes'))
    ap.add_argument('--jeu', required=True)
    ap.add_argument('--sortie')
    ap.add_argument('--processus', default='carrier_command_nouveau_5AF41B4D.exe')
    ap.add_argument('--depuis-fin', action='store_true')
    args = ap.parse_args()
    if args.commande == 'copier':
        if not args.sortie:
            ap.error('--sortie est obligatoire pour copier')
        copier(args)
    else:
        alertes(args)


if __name__ == '__main__':
    main()
