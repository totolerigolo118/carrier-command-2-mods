#!/usr/bin/env python3
"""Verifie, en LECTURE SEULE, la copie du nouvel exe a 4 reglages (ascenseur + temps + pont + helicos_approche_x2).

  python -I -B verifier_copie_helicos.py

Controles :
  1. la copie a 4 reglages ne differe de la copie a 3 reglages (5AF41B4D..., deja lancee le 31/10) qu'aux 4 octets du module
     helicos_approche_x2, et remettre ces 4 octets redonne exactement 5AF41B4D... ;
  2. au desassembleur : l'instruction du site lit 50,0 dans la copie a 3 reglages et 100,0 dans la nouvelle (constante en .rdata,
     en lecture seule), meme instruction, meme taille ;
  3. distance des 4 octets changes a chaque site de crochet des plugins sur le nouvel exe (frein v12/v13, Hold v2.1, modes) : aucun
     chevauchement.
Python standard + capstone (deja installe). Aucun fichier ecrit.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

import capstone

ICI = Path(__file__).resolve().parent
TRAVAIL = Path(r'C:\Users\UTILISATEUR\Documents\cc2-port-travail')
TROIS = TRAVAIL / 'carrier_command_nouveau_patche_ascenseur_temps_pont.exe'
QUATRE = TRAVAIL / 'carrier_command_nouveau_patche_ascenseur_temps_pont_helicos.exe'
SHA_TROIS = '5AF41B4D78CF18EB25C2F227397EAAA2F0E6443E65D2E9A142CC5043F45CC345'
SHA_QUATRE = '2C9F8E47FD494BD3EF04038910C6E2A086742BCDA6AF71CACE2E1B69EA766F06'
MODULE = ICI.parents[1] / 'outils' / 'modules_exe_461E1262' / 'helicos_approche_x2.json'
# sites des plugins sur le nouvel exe (VA, octets deplaces) : frein v12 (VERIF_sites_v12.txt), Hold v2.1 (cc2x_hold.c), modes (lecture) ;
# 31/10 : + H6 du frein v13 (VERIF_sites_v13.txt, worktree gifted-moore), pose seulement si heli_recall=1 au demarrage
SITES = [('frein H6 (v13, si heli_recall=1)', 0x6fdded, 8),('frein H1', 0x7019de, 6), ('frein H2', 0x701b4d, 6), ('frein H3', 0x6ff20b, 6), ('frein sonde A/B', 0x6fecea, 8),
         ('frein sonde C/D', 0x6fecf7, 8), ('frein sonde E', 0x6fecd0, 8), ('frein sonde C passee', 0x6fe898, 6),
         ('frein H5', 0x6fe580, 7), ('frein sonde prise en charge', 0x6ff489, 9), ('Hold 1', 0x6fce72, 6), ('Hold 2', 0x6fda4c, 6),
         ('Hold synchronisation', 0x7061f0, 6), ('modes (lecture)', 0x71dcbf, 8)]
ok = True


def sha(b):
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
    return base, res


def va_vers_offset(secs, va):
    for nom, debut, vsize, raw, rsize, car in secs:
        if debut <= va < debut + max(vsize, rsize):
            return raw + (va - debut), nom, car
    raise ValueError(hex(va))


def main():
    t, q = TROIS.read_bytes(), QUATRE.read_bytes()
    verdict(sha(t) == SHA_TROIS, f'copie a 3 reglages = {SHA_TROIS[:8]}...')
    verdict(sha(q) == SHA_QUATRE, f'copie a 4 reglages = {SHA_QUATRE[:8]}...')
    m = json.loads(MODULE.read_text(encoding='utf-8'))
    ch = m['changements'][0]
    off, va = ch['offset'], ch['va']
    diff = [i for i in range(len(t)) if t[i] != q[i]] if len(t) == len(q) else None
    verdict(diff is not None and diff and min(diff) >= off and max(diff) < off + 4,
            f'seuls les octets {off:#x}..{off + 3:#x} different ({len(diff or [])} octet(s))')
    verdict(t[off:off + 4].hex() == ch['avant'] and q[off:off + 4].hex() == ch['apres'], f"avant {ch['avant']} / apres {ch['apres']}")
    r = bytearray(q); r[off:off + 4] = bytes.fromhex(ch['avant'])
    verdict(sha(bytes(r)) == SHA_TROIS, 'remettre ces 4 octets redonne exactement la copie a 3 reglages')

    base, secs = sections(q)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    # l'operande change est un deplacement : on cherche l'instruction qui le contient (debut <= va)
    for nom_fichier, b in (('3 reglages', t), ('4 reglages', q)):
        trouve = None
        for debut in range(va - 8, va + 1):
            o, _, _ = va_vers_offset(secs, debut)
            ins = next(md.disasm(b[o:o + 16], debut), None)
            if ins and debut <= va < debut + ins.size and va + 4 <= debut + ins.size:
                trouve = ins
                break
        cst = struct.unpack_from('<I', b, off)[0]
        oc, sec, car = va_vers_offset(secs, cst)
        valeur = struct.unpack_from('<f', b, oc)[0]
        ecrit = bool(car & 0x80000000)
        print(f'       {nom_fichier} : {trouve.address:#x} {trouve.mnemonic} {trouve.op_str} ({trouve.size} o) ; [{cst:#x}] = {valeur} dans {sec}'
              f'{" (ECRIVABLE)" if ecrit else " (lecture seule)"}')
        attendu = 50.0 if nom_fichier == '3 reglages' else 100.0
        verdict(trouve.mnemonic == 'addss' and 'xmm2' in trouve.op_str and valeur == attendu and not ecrit,
                f'{nom_fichier} : addss xmm2 lit {attendu}')

    print('       distance aux sites des plugins (nouvel exe) :')
    for nom, s, n in SITES:
        d = (s - (va + 4)) if s >= va else (va - (s + n))
        print(f'         {nom:30s} {s:#x} ({n} o) : {d:+d} octets')
        verdict(d > 0, f'pas de chevauchement avec {nom}')
    print('\nBILAN :', 'TOUT EST BON' if ok else 'ECHEC')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
