#!/usr/bin/env python3
"""portage_appliquer.py : applique / retire les modules PORTES (modules_exe_nouvel_exe/*.json) sur une COPIE du nouvel exe.
Inspire de tour/outils/patch_exe.py (non modifie, non appele). Ne travaille que sur des copies :
  - REFUS si le chemin de sortie ou d'entree contient 'steamapps' ou 'Carrier Command 2' (le vrai jeu) ;
  - REFUS si la sortie est le meme fichier que l'entree ;
  - le fichier d'entree n'est JAMAIS modifie ; on ecrit un NOUVEAU fichier (temporaire, relu, sha256 verifie, puis renomme) ;
  - l'entree doit avoir exactement le sha256_origine des JSON (461E1262...), sinon refus.

Commandes (tous les chemins sont explicites) :
  python -I portage_appliquer.py etat     --exe FICHIER
  python -I portage_appliquer.py fabriquer --exe NOUVEL_EXE_ORIGINAL --sortie COPIE --module nom[,nom...] | --tous
  python -I portage_appliquer.py retirer  --exe COPIE_PATCHEE --sortie NOUVELLE_COPIE [--module nom[,nom...]]  (sans --module : tout retirer)
"""
import argparse, glob, hashlib, json, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, 'modules_exe_nouvel_exe')

def sha(b):
    return hashlib.sha256(b).hexdigest().upper()

def lire(p):
    with open(p, 'rb') as f:
        return f.read()

def charger():
    mods = {}
    for p in sorted(glob.glob(os.path.join(DOSSIER, '*.json'))):
        m = json.load(open(p, encoding='utf-8'))
        mods[m['nom']] = m
    if not mods:
        sys.exit('REFUS : aucun module dans ' + DOSSIER)
    orig = set(m['sha256_origine'] for m in mods.values())
    if len(orig) != 1:
        sys.exit("REFUS : les modules n'ont pas le meme sha256_origine")
    # aucun octet ne doit etre touche par deux modules differents
    vus = {}
    for m in mods.values():
        for c in m['changements']:
            for k in range(c['offset'], c['offset'] + 4):
                if k in vus and vus[k] != m['nom']:
                    sys.exit('REFUS : octet 0x%x touche par %s et %s' % (k, vus[k], m['nom']))
                vus[k] = m['nom']
    return mods, orig.pop()

def interdit(chemin):
    c = os.path.abspath(chemin).lower().replace('/', chr(92))
    return 'steamapps' in c or 'carrier command 2' in c

def remettre_origine(data, mods):
    b = bytearray(data)
    inconnus = []
    for m in mods.values():
        for c in m['changements']:
            reel = bytes(b[c['offset']:c['offset'] + 4]).hex()
            if reel in (c['avant'], c['apres']):
                b[c['offset']:c['offset'] + 4] = bytes.fromhex(c['avant'])
            else:
                inconnus.append((m['nom'], c['offset'], reel))
    return bytes(b), inconnus

def etat_modules(data, mods):
    res = {}
    for n, m in mods.items():
        a = sum(bytes(data[c['offset']:c['offset'] + 4]).hex() == c['avant'] for c in m['changements'])
        p = sum(bytes(data[c['offset']:c['offset'] + 4]).hex() == c['apres'] for c in m['changements'])
        t = len(m['changements'])
        res[n] = 'original' if a == t else ('patche' if p == t else 'melange')
    return res

def ecrire(chemin, octets):
    tmp = chemin + '.tmp_portage'
    with open(tmp, 'wb') as f:
        f.write(octets)
        f.flush()
        os.fsync(f.fileno())
    if sha(lire(tmp)) != sha(octets):
        os.remove(tmp)
        raise RuntimeError('relecture : sha256 different, rien ecrit')
    os.replace(tmp, chemin)
    if sha(lire(chemin)) != sha(octets):
        raise RuntimeError('fichier final : sha256 inattendu')

def noms(args, mods, defaut_tous):
    if getattr(args, 'tous', False) or (not args.module and defaut_tous):
        return list(mods)
    if not args.module:
        sys.exit('REFUS : donner --module ou --tous')
    n = [x.strip() for x in args.module.split(',') if x.strip()]
    for x in n:
        if x not in mods:
            sys.exit('REFUS : module inconnu %r (connus : %s)' % (x, ', '.join(mods)))
    return n

def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument('commande', choices=['etat', 'fabriquer', 'retirer'])
    ap.add_argument('--exe', required=True)
    ap.add_argument('--sortie')
    ap.add_argument('--module')
    ap.add_argument('--tous', action='store_true')
    args = ap.parse_args()
    mods, sha_orig = charger()
    if interdit(args.exe) or (args.sortie and interdit(args.sortie)):
        sys.exit('REFUS : ce chemin ressemble au VRAI jeu. Cet outil ne travaille que sur des copies hors du jeu.')
    if not os.path.isfile(args.exe):
        sys.exit('REFUS : fichier introuvable')
    data = lire(args.exe)
    remis, inconnus = remettre_origine(data, mods)
    coherent = (not inconnus) and sha(remis) == sha_orig
    if args.commande == 'etat':
        print('sha256 :', sha(data))
        print('coherent avec le nouvel exe + modules portes :', coherent)
        if coherent:
            for n, e in etat_modules(data, mods).items():
                print('  %-22s %s' % (n, e))
        return 0 if coherent else 3
    if not args.sortie:
        sys.exit('REFUS : --sortie obligatoire')
    if os.path.abspath(args.sortie) == os.path.abspath(args.exe):
        sys.exit("REFUS : la sortie est le fichier d'entree")
    if not coherent:
        sys.exit("REFUS : l'entree n'est pas (nouvel exe 461E1262 + modules portes). Rien ecrit.")
    etats = etat_modules(data, mods)
    if args.commande == 'fabriquer':
        if sha(data) != sha_orig:
            sys.exit("REFUS : pour fabriquer, l'entree doit etre le nouvel exe ORIGINAL (sha256 %s)" % sha_orig)
        sel = noms(args, mods, False)
        b = bytearray(data)
        for n in sel:
            for c in mods[n]['changements']:
                b[c['offset']:c['offset'] + 4] = bytes.fromhex(c['apres'])
        res = bytes(b)
        print('fabrique', ', '.join(sel), '-> sha256', sha(res))
    else:
        sel = noms(args, mods, True)
        b = bytearray(data)
        for n in sel:
            for c in mods[n]['changements']:
                b[c['offset']:c['offset'] + 4] = bytes.fromhex(c['avant'])
        res = bytes(b)
        print('retire', ', '.join(sel), '-> sha256', sha(res), '(= original)' if sha(res) == sha_orig else '')
    ecrire(args.sortie, res)
    print('ecrit', os.path.abspath(args.sortie))
    return 0

if __name__ == '__main__':
    sys.exit(main())
