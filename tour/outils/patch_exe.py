#!/usr/bin/env python3
"""Atelier de patch DIRECT de carrier_command.exe (methode du Mac : on change des octets du
programme sur le disque ; pas de DLL, pas de SDK, aucun code d'un tiers dans le jeu).

DEUX PROFILS (choisis par l'horodatage de compilation de l'en-tete PE du fichier donne ; aucun autre fichier n'est accepte) :
  ancien build 1.5.18 (horodatage 0x6a36c177, original 1C9A01C3...)         modules dans modules_exe/
  BUILD DE STEAM du 28/10/2026 (horodatage 0x6ae228f3, original 461E1262...) modules dans modules_exe_461E1262/
Les deux profils ont les MEMES noms de modules ; les octets sont ceux de chaque build (retrouves par le contexte, voir
tour/etude_port_nouvel_exe/). Sur le build de Steam, l'outil n'ecrit JAMAIS dans un chemin « steamapps » (meme avec
--cest-le-vrai-jeu) : on patche une COPIE, lancee a part ; Steam reecrirait l'original.

Modules (un fichier JSON par module) :
  ascenseur_x2  ascenseur, grue et roulage sur le pont x2 (32 changements de 4 octets)
  temps_x2      simulation 2x plus vite, MODE TEST (1 changement de 4 octets)
  atterrissage_creneau  la piste peut etre donnee pendant tout le virage arriere (3 changements de 4 octets)
  atterrissage_cercle   le circuit d'attente des avions devient un cercle au lieu d'un ovale (3 changements de 4 octets)
  pont_retour_x2        roulage de retour sur le pont x2 (1 changement de 4 octets ; peu vu en jeu)
  helicos_approche_x2   approche des helicos x2 (1 changement de 4 octets ; jamais vu en jeu)

Commandes (le chemin du fichier est TOUJOURS donne avec --exe : aucun chemin par defaut) :

  python patch_exe.py etat    --exe FICHIER
  python patch_exe.py activer --exe FICHIER --sauvegarde COPIE_ORIGINALE [--module NOM] [--a-blanc]
  python patch_exe.py retirer --exe FICHIER [--module NOM] [--a-blanc]
  python patch_exe.py retirer --exe FICHIER --sauvegarde COPIE_ORIGINALE --restaurer-tout-l-exe [--a-blanc]
                                (etat MELANGE de nos modules SEULEMENT : remplace TOUT le fichier par la copie)

--module vaut ascenseur_x2 par defaut.

Securites :
  - un fichier INCONNU (ni l'original ni un melange de NOS modules DU MEME PROFIL : autre build du jeu, ou octets abimes)
    est TOUJOURS refuse, pour `activer` comme pour `retirer`, MEME avec --sauvegarde, --restaurer-tout-l-exe et
    --cest-le-vrai-jeu : rien n'est ecrit, on demande au moddeur ;
  - un fichier dont l'horodatage de compilation (en-tete PE) n'est pas celui d'un des deux profils (0x6a36c177 ou
    0x6ae228f3) est refuse de la meme facon ; un fichier au horodatage d'un profil mais aux octets d'un autre build aussi ;
  - la somme de chaque original est EPINGLEE dans l'outil (pas seulement lue dans les JSON) ;
  - remettre TOUT le fichier depuis la copie de sauvegarde n'est possible que pour l'etat MELANGE de nos modules, avec
    --sauvegarde ET --restaurer-tout-l-exe (jamais d'office) ;
  - verification GLOBALE : si l'on remet a l'etat d'origine tous les endroits de TOUS les modules connus, le fichier
    doit redevenir exactement l'original (sha256). Sinon (autre version du jeu, autre octet modifie) : refus ;
  - `activer` exige une copie de sauvegarde dont le sha256 est celui de l'original ;
  - sur un chemin qui contient « steamapps » (le vrai jeu), il faut ajouter --cest-le-vrai-jeu, et le
    jeu doit etre FERME (carrier_command.exe ne tourne pas) ;
  - ecriture dans un fichier temporaire, relecture, verification du sha256, puis remplacement ;
  - rien d'autre que les octets listes dans modules_exe/*.json n'est jamais touche.
"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER_MODULES = os.path.join(ICI, 'modules_exe')

# Horodatage de compilation (en-tete PE) de l'ancien build 1.5.18, celui pour lequel les modules sont ecrits.
HORODATAGE_PE_ATTENDU = 0x6a36c177
# Build de Steam du 28/10/2026 (build Steam 26277078) : un AUTRE programme, sans aucun de nos patchs. Ne jamais y ecrire.
HORODATAGE_PE_BUILD_STEAM_28_10 = 0x6ae228f3
SHA256_BUILDS_ETRANGERS = set()   # sommes de builds a refuser MEME avec un horodatage connu (vide : le build Steam a maintenant son profil)
SHA256_ORIGINE_ANCIEN = '1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026'
SHA256_ORIGINE_STEAM_28_10 = '461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A'
PROFILS = [
    dict(nom='ancien build 1.5.18 (1C9A01C3...)', horodatage=HORODATAGE_PE_ATTENDU, sha256_origine=SHA256_ORIGINE_ANCIEN,
         dossier=os.path.join(ICI, 'modules_exe'), ecriture_dans_steamapps=True),
    dict(nom='BUILD DE STEAM du 28/10/2026 (461E1262...)', horodatage=HORODATAGE_PE_BUILD_STEAM_28_10,
         sha256_origine=SHA256_ORIGINE_STEAM_28_10, dossier=os.path.join(ICI, 'modules_exe_461E1262'),
         ecriture_dans_steamapps=False),
]
A_FAIRE = 'Rien n\'est ecrit. A FAIRE : ne rien ecrire et demander au moddeur (voir tour/etude_mise_a_jour/ETUDE.md).'


def sha256_octets(b):
    return hashlib.sha256(b).hexdigest().upper()


def lire(path):
    with open(path, 'rb') as f:
        return f.read()


def charger_tous(profil=None):
    """Modules du profil (par defaut : l'ancien build) ; la somme d'origine doit etre celle EPINGLEE dans l'outil."""
    profil = profil or PROFILS[0]
    mods = {}
    for p in sorted(glob.glob(os.path.join(profil['dossier'], '*.json'))):
        with open(p, 'r', encoding='utf-8') as f:
            m = json.load(f)
        mods[m['nom']] = m
    if not mods:
        sys.exit('REFUS : aucun module dans %s' % profil['dossier'])
    origines = {m['sha256_origine'] for m in mods.values()}
    if len(origines) != 1:
        sys.exit('REFUS : les modules ne partagent pas le meme sha256 d\'origine.')
    origine = origines.pop()
    if origine != profil['sha256_origine']:
        sys.exit('REFUS : les modules de %s ne portent pas la somme d\'origine epinglee dans l\'outil (%s).' % (
            profil['nom'], profil['sha256_origine'][:8]))
    for m in mods.values():
        h = int(m['build']['horodatage_pe'], 16)
        if h != profil['horodatage']:
            sys.exit('REFUS : le module %s annonce l\'horodatage 0x%08x, le profil attend 0x%08x.' % (m['nom'], h, profil['horodatage']))
    return mods, origine


def diagnostic(data, mod):
    """Pour chaque changement du module : d'origine, patche, ou autre."""
    n_orig = n_patch = 0
    autres = []
    for c in mod['changements']:
        reel = data[c['offset']:c['offset'] + 4].hex() if len(data) >= c['offset'] + 4 else ''
        if reel == c['avant']:
            n_orig += 1
        elif reel == c['apres']:
            n_patch += 1
        else:
            autres.append((c, reel))
    return n_orig, n_patch, autres


def tout_remettre_d_origine(data, mods):
    """Remet a l'etat d'origine les endroits de tous les modules ; renvoie (octets, liste des endroits inconnus)."""
    b = bytearray(data)
    inconnus = []
    for m in mods.values():
        for c in m['changements']:
            reel = bytes(b[c['offset']:c['offset'] + 4]).hex()
            if reel == c['avant'] or reel == c['apres']:
                b[c['offset']:c['offset'] + 4] = bytes.fromhex(c['avant'])
            else:
                inconnus.append((m['nom'], c, reel))
    return bytes(b), inconnus


PROFIL_COURANT = [None]     # profil choisi par main() ; sert seulement aux messages


def _etiquette_profil():
    return ' [profil : %s]' % PROFIL_COURANT[0]['nom'] if PROFIL_COURANT[0] else ''


def coherence_globale(data, mods, sha_origine):
    """-> (ok, message) : le fichier ne differe de l'original que par les modules connus."""
    remis, inconnus = tout_remettre_d_origine(data, mods)
    if inconnus:
        nom, c, reel = inconnus[0]
        return False, '%d endroit(s) ne contiennent ni l\'original ni le patch (ex. module %s, 0x%08x : %s) : autre version du jeu ?%s' % (
            len(inconnus), nom, c['va'], reel or 'hors fichier', _etiquette_profil())
    if sha256_octets(remis) != sha_origine:
        return False, 'le fichier differe de l\'original ailleurs que sur les modules connus (autre version du jeu, autre octet modifie ?)%s' % _etiquette_profil()
    return True, 'coherent : seul(s) des endroits de modules connus different de l\'original'


def etat_module(data, mod, mods, sha_origine):
    """-> ('original'|'patche'|'melange'|'inconnu', detail)"""
    ok, msg = coherence_globale(data, mods, sha_origine)
    if not ok:
        return 'inconnu', msg
    n_orig, n_patch, _ = diagnostic(data, mod)
    n = len(mod['changements'])
    if n_orig == n:
        return 'original', 'les %d endroits sont d\'origine' % n
    if n_patch == n:
        return 'patche', 'les %d endroits sont patches' % n
    return 'melange', '%d endroit(s) d\'origine et %d patche(s) : etat melange' % (n_orig, n_patch)


def horodatage_pe(data):
    """Horodatage de compilation de l'en-tete PE, ou None si ce n'est pas un PE lisible."""
    if len(data) < 0x40:
        return None
    pe = int.from_bytes(data[0x3c:0x40], 'little')
    if pe + 12 > len(data) or data[pe:pe + 4] != b'PE\0\0':
        return None
    return int.from_bytes(data[pe + 8:pe + 12], 'little')


def profil_de(data):
    """Le profil dont l'horodatage de compilation est celui du fichier, ou None."""
    h = horodatage_pe(data)
    for p in PROFILS:
        if p['horodatage'] == h:
            return p
    return None


def build_refuse(data):
    """None si le fichier est d'un des builds connus ; sinon la raison (texte) pour laquelle on refuse d'y ecrire."""
    if sha256_octets(data) in SHA256_BUILDS_ETRANGERS:
        return 'c\'est un BUILD ETRANGER connu (somme sha256 dans la liste des builds refuses)'
    if profil_de(data) is None:
        h = horodatage_pe(data)
        return ('horodatage de compilation %s : ce n\'est ni l\'ancien build 1.5.18 (0x%08x) ni le build de Steam du 28/10/2026 (0x%08x)' % (
            '0x%08x' % h if h is not None else 'illisible', HORODATAGE_PE_ATTENDU, HORODATAGE_PE_BUILD_STEAM_28_10))
    return None


def jeu_ouvert():
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq carrier_command.exe', '/NH'],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return None
    return 'carrier_command.exe' in out.lower()


def verifier_chemin(args):
    vrai = 'steamapps' in os.path.abspath(args.exe).lower()
    profil = getattr(args, 'profil', None)
    if vrai and profil is not None and not profil['ecriture_dans_steamapps']:
        # le build de Steam : on ne patche JAMAIS le fichier du jeu (Steam le reecrit) ; on patche une copie, lancee a part
        print('REFUS : %s : on n\'ecrit JAMAIS dans un chemin « steamapps » (meme avec --cest-le-vrai-jeu) : Steam reecrit ce fichier. '
              'Patche une COPIE hors du dossier de Steam. Rien n\'est ecrit. A FAIRE : demander au moddeur (voir tour/etude_port_nouvel_exe/).' % profil['nom'])
        sys.exit(3)
    if vrai and not args.cest_le_vrai_jeu:
        sys.exit("REFUS : ce chemin ressemble au VRAI jeu (steamapps). Ajouter --cest-le-vrai-jeu pour confirmer que c'est voulu.")
    return vrai


def ecrire_sur(path, octets, sha_attendu):
    tmp = path + '.cc2_tmp'
    try:
        with open(tmp, 'wb') as f:
            f.write(octets)
            f.flush()
            os.fsync(f.fileno())
        if sha256_octets(lire(tmp)) != sha_attendu:
            raise RuntimeError('relecture du fichier temporaire : sha256 different, rien n\'est remplace')
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    if sha256_octets(lire(path)) != sha_attendu:
        raise RuntimeError('ATTENTION : le fichier final n\'a pas le sha256 attendu')


def appliquer(data, mod, vers):
    """vers = 'apres' ou 'avant' : renvoie les octets avec les 4 octets de chaque changement du module."""
    nouveau = bytearray(data)
    for c in mod['changements']:
        nouveau[c['offset']:c['offset'] + 4] = bytes.fromhex(c[vers])
    return bytes(nouveau)


def cmd_etat(args, mods, sha_origine):
    data = lire(args.exe)
    ok, msg = coherence_globale(data, mods, sha_origine)
    print('Fichier   : %s' % os.path.abspath(args.exe))
    print('sha256    : %s' % sha256_octets(data))
    if getattr(args, 'profil', None):
        print('Profil    : %s' % args.profil['nom'])
    code = 0
    if not ok:
        print('Etat      : INCONNU (%s)' % msg)
        return 3
    for nom, m in mods.items():
        etat, detail = etat_module(data, m, mods, sha_origine)
        n_orig, n_patch, autres = diagnostic(data, m)
        print('Module %-13s : %-8s (%d d\'origine, %d patche(s) sur %d)' % (nom, etat.upper(), n_orig, n_patch, len(m['changements'])))
        if etat in ('melange', 'inconnu'):
            code = 3
    if all(etat_module(data, m, mods, sha_origine)[0] == 'original' for m in mods.values()):
        print('Etat      : ORIGINAL (sha256 exact de l\'original)')
    elif all(etat_module(data, m, mods, sha_origine)[0] in ('original', 'patche') for m in mods.values()):
        actifs = [n for n, m in mods.items() if etat_module(data, m, mods, sha_origine)[0] == 'patche']
        print('Etat      : PATCHE (%s ; coherent avec l\'original)' % ', '.join(actifs))
    return code


def charger_module(args, mods):
    if args.module not in mods:
        sys.exit('REFUS : module inconnu %r (modules : %s)' % (args.module, ', '.join(mods)))
    return mods[args.module]


def cmd_activer(args, mods, sha_origine):
    mod = charger_module(args, mods)
    vrai = verifier_chemin(args)
    data = lire(args.exe)
    raison = build_refuse(data)
    if raison:
        print('REFUS : %s. %s' % (raison, A_FAIRE))
        return 3
    etat, detail = etat_module(data, mod, mods, sha_origine)
    if etat == 'patche':
        print('Deja actif : rien a faire (%s).' % detail)
        return 0
    if etat != 'original':
        print('REFUS : etat %s (%s). %s' % (etat.upper(), detail, A_FAIRE if etat == 'inconnu' else 'Rien n\'est ecrit.'))
        return 3
    if not args.sauvegarde or not os.path.isfile(args.sauvegarde):
        print('REFUS : il faut --sauvegarde FICHIER (copie de l\'original, pour pouvoir revenir en arriere).')
        return 3
    if sha256_octets(lire(args.sauvegarde)) != sha_origine:
        print('REFUS : la sauvegarde n\'a pas le sha256 de l\'original. Rien n\'est ecrit.')
        return 3
    if os.path.abspath(args.sauvegarde) == os.path.abspath(args.exe):
        print('REFUS : la sauvegarde et le fichier a patcher sont le meme fichier.')
        return 3
    if vrai and not args.a_blanc:
        ouvert = jeu_ouvert()
        if ouvert is None or ouvert:
            print('REFUS : le jeu tourne (ou je ne peux pas le verifier). Ferme-le puis recommence. Rien n\'est ecrit.')
            return 3
    nouveau = appliquer(data, mod, 'apres')
    ok, msg = coherence_globale(nouveau, mods, sha_origine)
    n_orig, n_patch, _ = diagnostic(nouveau, mod)
    if not ok or n_patch != len(mod['changements']):
        print('ERREUR INTERNE : le resultat n\'est pas coherent (%s). Rien n\'est ecrit.' % msg)
        return 4
    sha_apres = sha256_octets(nouveau)
    print('%s %d changement(s) de 4 octets, module %s (sha256 attendu apres : %s...)' % (
        '[A BLANC] Je changerais' if args.a_blanc else 'Je change', len(mod['changements']), mod['nom'], sha_apres[:16]))
    if args.a_blanc:
        return 0
    ecrire_sur(args.exe, nouveau, sha_apres)
    print('FAIT : module %s ACTIF. sha256 verifie.' % mod['nom'])
    return 0


def cmd_retirer(args, mods, sha_origine):
    mod = charger_module(args, mods)
    vrai = verifier_chemin(args)
    data = lire(args.exe)
    raison = build_refuse(data)
    if raison:
        print('REFUS : %s. %s' % (raison, A_FAIRE))
        return 3
    etat, detail = etat_module(data, mod, mods, sha_origine)
    if etat == 'original':
        print('Deja d\'origine : rien a faire (%s).' % detail)
        return 0
    if etat == 'inconnu':
        # jamais de remplacement du fichier entier sur un etat inconnu : meme avec --sauvegarde et --cest-le-vrai-jeu
        print('REFUS : etat INCONNU (%s). Ce fichier n\'est ni l\'original ni un melange de nos modules : on n\'y ecrit rien, '
              'MEME avec --sauvegarde, --restaurer-tout-l-exe et --cest-le-vrai-jeu. %s' % (detail, A_FAIRE))
        return 3
    if vrai and not args.a_blanc:
        ouvert = jeu_ouvert()
        if ouvert is None or ouvert:
            print('REFUS : le jeu tourne (ou je ne peux pas le verifier). Ferme-le puis recommence. Rien n\'est ecrit.')
            return 3
    if etat == 'patche':
        nouveau = appliquer(data, mod, 'avant')
        ok, msg = coherence_globale(nouveau, mods, sha_origine)
        n_orig, _, _ = diagnostic(nouveau, mod)
        if not ok or n_orig != len(mod['changements']):
            print('ERREUR INTERNE : le retour n\'est pas coherent (%s). Rien n\'est ecrit.' % msg)
            return 4
        print('%s : retour aux octets d\'origine du module %s.' % ('[A BLANC]' if args.a_blanc else 'Je retire', mod['nom']))
        if not args.a_blanc:
            ecrire_sur(args.exe, nouveau, sha256_octets(nouveau))
            tout_original = sha256_octets(nouveau) == sha_origine
            print('FAIT : module %s retire%s (sha256 verifie).' % (mod['nom'], ' : fichier EXACTEMENT d\'origine' if tout_original else ' (d\'autres modules restent actifs)'))
        return 0
    # etat melange de NOS modules (coherent avec l'original) : la copie de sauvegarde peut le rattraper, mais seulement
    # avec le drapeau explicite --restaurer-tout-l-exe
    if not args.restaurer_tout:
        print('REFUS : etat MELANGE (%s). Rien n\'est ecrit. Pour tout remettre a l\'original avec la copie : ajouter '
              '--sauvegarde COPIE_ORIGINALE --restaurer-tout-l-exe (REMPLACE tout le fichier ; jamais sur l\'exe de Steam '
              'sans l\'accord du moddeur).' % detail)
        return 3
    if not (args.sauvegarde and os.path.isfile(args.sauvegarde)) or sha256_octets(lire(args.sauvegarde)) != sha_origine:
        print('REFUS : --restaurer-tout-l-exe demande --sauvegarde avec la copie de l\'original (sha256 exact). Rien n\'est ecrit.')
        return 3
    if os.path.abspath(args.sauvegarde) == os.path.abspath(args.exe):
        print('REFUS : la sauvegarde et le fichier a restaurer sont le meme fichier.')
        return 3
    print('%s : etat MELANGE, je remets la COPIE DE SAUVEGARDE entiere (tous les modules sont retires).' % (
        '[A BLANC]' if args.a_blanc else 'Je restaure'))
    if not args.a_blanc:
        ecrire_sur(args.exe, lire(args.sauvegarde), sha_origine)
        print('FAIT : fichier remplace par la sauvegarde (sha256 verifie).')
    return 0


def main():
    ap = argparse.ArgumentParser(description='Patch direct de carrier_command.exe', allow_abbrev=False)
    ap.add_argument('commande', choices=['etat', 'activer', 'retirer'])
    ap.add_argument('--exe', required=True, help='le fichier a lire / patcher (toujours explicite)')
    ap.add_argument('--module', default='ascenseur_x2', help='module a activer / retirer (defaut : ascenseur_x2)')
    ap.add_argument('--sauvegarde', help="copie de l'original (obligatoire pour activer)")
    ap.add_argument('--a-blanc', action='store_true', dest='a_blanc', help='montre ce qui serait fait, sans rien ecrire')
    ap.add_argument('--cest-le-vrai-jeu', action='store_true', dest='cest_le_vrai_jeu',
                    help='confirmation obligatoire si le chemin contient steamapps')
    ap.add_argument('--restaurer-tout-l-exe', action='store_true', dest='restaurer_tout',
                    help="retirer, etat MELANGE seulement : remplace TOUT le fichier par --sauvegarde (jamais sur un etat INCONNU)")
    args = ap.parse_args()
    if args.restaurer_tout and args.commande != 'retirer':
        sys.exit('REFUS : --restaurer-tout-l-exe ne s\'utilise qu\'avec la commande retirer.')
    if not os.path.isfile(args.exe):
        sys.exit('REFUS : fichier introuvable : %s' % args.exe)
    data = lire(args.exe)
    profil = profil_de(data)
    if profil is None:
        # horodatage inconnu / fichier illisible : rien n'est ecrit, quelle que soit la commande
        raison = build_refuse(data)
        if args.commande == 'etat':
            print('Fichier   : %s' % os.path.abspath(args.exe))
            print('sha256    : %s' % sha256_octets(data))
            print('Etat      : INCONNU (%s)' % raison)
            return 3
        print('REFUS : %s. %s' % (raison, A_FAIRE))
        return 3
    args.profil = profil
    PROFIL_COURANT[0] = profil
    mods, sha_origine = charger_tous(profil)
    return {'etat': cmd_etat, 'activer': cmd_activer, 'retirer': cmd_retirer}[args.commande](args, mods, sha_origine)


if __name__ == '__main__':
    sys.exit(main())
