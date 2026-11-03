#!/usr/bin/env python3
"""Verifie, en LECTURE SEULE, les deux copies « multijoueur » du nouvel exe (SANS temps_x2) fabriquees le 31/10 hors du jeu.

  python -I -B verifier_copies_multi.py

  copie a 5 reglages : ascenseur_x2 + pont_retour_x2 + helicos_approche_x2 + atterrissage_cercle + atterrissage_creneau
  copie a 3 reglages : ascenseur_x2 + pont_retour_x2 + helicos_approche_x2 (la prudente : sans cercle ni creneau)

Controles, pour chaque copie :
  1. elle ne differe du build de Steam (461E1262...) qu'aux endroits de SES modules (octets « apres » du JSON), temps_x2 et les
     autres modules sont d'origine, et remettre ces endroits redonne exactement 461E1262... ;
  2. recoupement par un autre chemin : la copie a 3 = la copie hélicos deja verifiee (2C9F8E47...) sans temps_x2, et aussi la copie
     lancee a 13:52 (5AF41B4D...) sans temps_x2 avec helicos_approche_x2 ; la copie a 5 = la copie a 3 + cercle + creneau ;
  3. au desassembleur, a chaque endroit change : meme instruction (adresse, taille, nom) avant et apres ; seul l'operande change ;
     une constante lue (type abs) est dans une section en lecture seule ;
  4. distance de chaque endroit change aux crochets des plugins sur le nouvel exe (frein v13 dont H6, Hold v2.1, modes) : aucun
     chevauchement.
Python standard + capstone (deja installe). Aucun fichier ecrit.
"""
import collections
import json
import struct
import sys
from pathlib import Path

import capstone

ICI = Path(__file__).resolve().parent
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-port-travail')
MODULES = ICI.parents[1] / 'outils' / 'modules_exe_461E1262'
STEAM = (TRAVAIL / 'carrier_command_nouveau_steam_461E1262.exe', '461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A')
TROIS_TEMPS = (TRAVAIL / 'carrier_command_nouveau_patche_ascenseur_temps_pont.exe', '5AF41B4D78CF18EB25C2F227397EAAA2F0E6443E65D2E9A142CC5043F45CC345')
HELICOS = (TRAVAIL / 'carrier_command_nouveau_patche_ascenseur_temps_pont_helicos.exe', '2C9F8E47FD494BD3EF04038910C6E2A086742BCDA6AF71CACE2E1B69EA766F06')
COPIES = {
    'multi a 5 reglages': (TRAVAIL / 'carrier_command_nouveau_multi_ascenseur_pont_helicos_cercle_creneau.exe',
                           'FCB3CDE18346DACE6D86D217733F1E617AE1DD88BBE033A4AC8F6FDBE3313CFC',
                           {'ascenseur_x2', 'pont_retour_x2', 'helicos_approche_x2', 'atterrissage_cercle', 'atterrissage_creneau'}),
    'multi a 3 reglages': (TRAVAIL / 'carrier_command_nouveau_multi_ascenseur_pont_helicos.exe',
                           '795CD61DE271F8DA4B97F499491DD3CBCCED1A1433EBEBFCB63A182AF4AA1A0E',
                           {'ascenseur_x2', 'pont_retour_x2', 'helicos_approche_x2'}),
}
# memes sites que verifier_copie_helicos.py (frein v12 + H6 de la v13, Hold v2.1, modes), nouvel exe
SITES = [('frein H6 (v13, si heli_recall=1)', 0x6fdded, 8), ('frein H1', 0x7019de, 6), ('frein H2', 0x701b4d, 6),
         ('frein H3', 0x6ff20b, 6), ('frein sonde A/B', 0x6fecea, 8), ('frein sonde C/D', 0x6fecf7, 8), ('frein sonde E', 0x6fecd0, 8),
         ('frein sonde C passee', 0x6fe898, 6), ('frein H5', 0x6fe580, 7), ('frein sonde prise en charge', 0x6ff489, 9),
         ('Hold 1', 0x6fce72, 6), ('Hold 2', 0x6fda4c, 6), ('Hold synchronisation', 0x7061f0, 6), ('modes (lecture)', 0x71dcbf, 8)]
ok = True


def sha(b):
    import hashlib
    return hashlib.sha256(b).hexdigest().upper()


def verdict(cond, texte):
    global ok
    ok = ok and cond
    print(('OK     ' if cond else 'ECHEC  ') + texte)


def sections(b):
    nt = struct.unpack_from('<I', b, 0x3c)[0]
    n = struct.unpack_from('<H', b, nt + 6)[0]
    opt = struct.unpack_from('<H', b, nt + 20)[0]
    base = struct.unpack_from('<I', b, nt + 24 + 28)[0]
    res = []
    for i in range(n):
        o = nt + 24 + opt + 40 * i
        nom = b[o:o + 8].rstrip(b'\0').decode()
        vsize, va, rsize, raw = struct.unpack_from('<IIII', b, o + 8)
        car = struct.unpack_from('<I', b, o + 36)[0]
        res.append((nom, base + va, vsize, raw, rsize, car))
    return res


def va_vers_offset(secs, va):
    for nom, debut, vsize, raw, rsize, car in secs:
        if debut <= va < debut + max(vsize, rsize):
            return raw + (va - debut), nom, car
    return None, None, None


def remettre(b, mods, vers):
    r = bytearray(b)
    for m in mods:
        for c in m['changements']:
            r[c['offset']:c['offset'] + 4] = bytes.fromhex(c[vers])
    return bytes(r)


def instruction(md, secs, b, va):
    """L'instruction qui contient les 4 octets en va : balayage lineaire depuis 32 debuts differents, vote (le x86 se resynchronise)."""
    votes = collections.Counter()
    for debut in range(va - 64, va - 32):
        o, _, _ = va_vers_offset(secs, debut)
        for ins in md.disasm(b[o:o + (va - debut) + 16], debut):
            if ins.address + ins.size > va:
                if ins.address <= va and va + 4 <= ins.address + ins.size:
                    votes[ins.address] += 1
                break
    if not votes:
        return None, 0
    adr, n = votes.most_common(1)[0]
    o, _, _ = va_vers_offset(secs, adr)
    return next(md.disasm(b[o:o + 16], adr)), n


def main():
    mods = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in sorted(MODULES.glob('*.json'))}
    fichiers = {}
    for nom, (chemin, attendu) in (('build de Steam', STEAM), ('copie lancee a 13:52', TROIS_TEMPS), ('copie helicos', HELICOS)):
        fichiers[nom] = chemin.read_bytes()
        verdict(sha(fichiers[nom]) == attendu, f'{nom} = {attendu[:8]}...')
    steam = fichiers['build de Steam']
    secs = sections(steam)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

    for nom, (chemin, attendu, actifs) in COPIES.items():
        print(f'\n=== {nom} : {chemin.name}')
        b = chemin.read_bytes()
        verdict(sha(b) == attendu, f'sha256 = {attendu[:8]}...')
        fichiers[nom] = b
        les_miens = [mods[n] for n in sorted(actifs)]
        fenetres = {c['offset'] + i for m in les_miens for c in m['changements'] for i in range(4)}
        diff = [i for i in range(len(steam)) if steam[i] != b[i]] if len(steam) == len(b) else None
        verdict(diff is not None and set(diff) <= fenetres, f'{len(diff or [])} octet(s) differents, tous dans les endroits de ses modules')
        verdict(all(b[c['offset']:c['offset'] + 4].hex() == c['apres'] for m in les_miens for c in m['changements']),
                f"modules actifs : {', '.join(sorted(actifs))} (octets « apres » partout)")
        autres = [n for n in mods if n not in actifs]
        verdict(all(b[c['offset']:c['offset'] + 4].hex() == c['avant'] for n in autres for c in mods[n]['changements']),
                f"modules d'origine : {', '.join(sorted(autres))}")
        verdict('temps_x2' in autres, 'temps_x2 absent (SIM x1, comme le jeu de l ami)')
        verdict(sha(remettre(b, les_miens, 'avant')) == STEAM[1], 'remettre ses endroits redonne exactement 461E1262...')

        print('       au desassembleur (sauf ascenseur_x2 : memes octets que la copie lancee a 13:52, voir les recoupements) :')
        for m in les_miens:
            for c in m['changements']:
                if m['nom'] == 'ascenseur_x2':
                    continue
                avant, n1 = instruction(md, secs, steam, c['va'])
                apres, n2 = instruction(md, secs, b, c['va'])
                meme = avant and apres and (avant.address, avant.size, avant.mnemonic) == (apres.address, apres.size, apres.mnemonic)
                extra = ''
                if c.get('type') == 'abs':
                    vals = []
                    for x in (steam, b):
                        cst = struct.unpack_from('<I', x, c['offset'])[0]
                        oc, sec, car = va_vers_offset(secs, cst)
                        vals.append((struct.unpack_from('<f', x, oc)[0], sec, bool(car & 0x80000000)))
                    extra = f" ; constante {vals[0][0]:g} -> {vals[1][0]:g} ({vals[1][1]}{', ECRIVABLE' if vals[1][2] else ', lecture seule'})"
                    meme = meme and not vals[1][2]
                elif c.get('type') == 'imm':
                    extra = f" ; valeur {struct.unpack_from('<f', steam, c['offset'])[0]:g} -> {struct.unpack_from('<f', b, c['offset'])[0]:g}"
                if avant and apres:
                    print(f"         {m['nom']:20s} {avant.address:#x} ({avant.size} o, vote {n1}/32) : {avant.mnemonic} {avant.op_str}  ->  "
                          f"{apres.mnemonic} {apres.op_str}{extra}")
                verdict(bool(meme), f"{m['nom']} {c['va']:#x} : meme instruction, seul l'operande change")
        fenetres_va = [(m['nom'], c['va']) for m in les_miens for c in m['changements']]
        print('       distance aux sites des plugins (le plus proche endroit change) :')
        for site, s, n in SITES:
            d, qui = min(((s - (va + 4)) if s >= va else (va - (s + n)), mn) for mn, va in fenetres_va)
            print(f'         {site:34s} {s:#x} ({n} o) : {d:+d} octets ({qui})')
            verdict(d > 0, f'pas de chevauchement avec {site}')

    print('\n=== recoupements')
    t = mods['temps_x2']
    verdict(remettre(fichiers['copie helicos'], [t], 'avant') == fichiers['multi a 3 reglages'],
            'copie helicos (2C9F8E47...) sans temps_x2 = copie multi a 3 reglages')
    verdict(remettre(remettre(fichiers['copie lancee a 13:52'], [t], 'avant'), [mods['helicos_approche_x2']], 'apres') == fichiers['multi a 3 reglages'],
            'copie de 13:52 (5AF41B4D...) sans temps_x2, + helicos = copie multi a 3 reglages')
    verdict(remettre(fichiers['multi a 3 reglages'], [mods['atterrissage_cercle'], mods['atterrissage_creneau']], 'apres') == fichiers['multi a 5 reglages'],
            'copie multi a 3 reglages + cercle + creneau = copie multi a 5 reglages')
    print('\nBILAN :', 'TOUT EST BON' if ok else 'ECHEC')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
