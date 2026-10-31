#!/usr/bin/env python3
"""PARTIE 2 : retrouve dans le NOUVEL exe de Steam chaque adresse du profil du SDK CC2X (cc2x.c + world.c, commit 7ab05c7).
LECTURE SEULE sur les deux exe. Ecrit un JSON de valeurs et un rapport texte.

Pour chaque valeur on donne : l'adresse ancienne, la nouvelle, la methode, les octets controles et, pour une fonction, le
nombre d'instructions du corps qui restent IDENTIQUES a l'ancien exe (jokers : adresses absolues, deplacements relatifs).
Un cas non trivial est signale, jamais devine.

Usage : python -I -B profil_sdk.py <ancien_original> <nouveau> <sortie.json> <sortie.txt>
"""
import bisect
import json
import os
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_lecture import Exe  # noqa: E402
from alignement import Alignement  # noqa: E402

# ---- valeurs de l'ancien profil (cc2x.c 0.5.0 lignes 29-35, world.c lignes 45-69), recopiees A LA MAIN ici
FONCTIONS_CC2X = [   # (nom, adresse ancienne, octets de signature du source ou None)
    ('server_init', 0x00772fd0, None), ('server_tick', 0x0077ee10, None), ('server_end', 0x0077eea0, None),
    ('f_index2addr', 0x008cda70, bytes([0x8b, 0x41, 0x14, 0x85, 0xd2, 0x7e, 0x0d, 0xc1])),
    ('f_auxsetstr', 0x008ce200, bytes([0x55, 0x8b, 0xec, 0x83, 0xec, 0x08, 0x53, 0x56])),
    ('f_finishset', 0x008ff6b0, bytes([0x55, 0x8b, 0xec, 0x83, 0xe4, 0xf8, 0x83, 0xec])),
    ('f_luaS_new', 0x00908220, bytes([0x55, 0x8b, 0xec, 0x83, 0xec, 0x08, 0x53, 0x8b])),
    ('f_luaH_new', 0x00904a50, bytes([0x56, 0x8b, 0x71, 0x10, 0x33, 0xd2, 0x6a, 0x20])),
    ('f_luaC_step', 0x00904050, bytes([0x53, 0x8b, 0xd9, 0x56, 0x57, 0x8b, 0x7b, 0x10])),
]
SITES_CC2X = [('lua_site', 0x004465ec, bytes([0x6a, 0x20, 0x89, 0x85, 0x64, 0xff, 0xff, 0xff]))]
FONCTIONS_WORLD = [
    ('f_vehicle_by_id', 0x005ee6a0), ('f_tile_by_id', 0x00631240), ('f_tile_at', 0x00631040), ('f_request_landing', 0x0062b4a0),
    ('f_waypoints_clear', 0x00854870), ('f_deque_grow', 0x00860c90), ('f_spawn', 0x0062ca30), ('f_af_tick', 0x00628600),
]
SITES_WORLD = [
    ('h_waypoints', 0x007781d4, bytes([0xff, 0xb0, 0x50, 0x01, 0x00, 0x00])),
    ('h_hangar', 0x0062ae8d, bytes([0x8b, 0x57, 0x6c, 0x33, 0xc0])),
    ('h_hangar_found', 0x0062aefc, None), ('h_hangar_none', 0x0062aead, None),
    ('h_controller[0]', 0x0063014f, bytes([0x8b, 0x01, 0x8b, 0x40, 0x10, 0xff, 0xd0])),
    ('h_controller[1]', 0x00634981, bytes([0x8b, 0x07, 0x8b, 0x40, 0x10, 0xff, 0xd0])),
    ('h_spawn', 0x00634f3d, None), ('h_af_tick', 0x0062b8f3, None),
]
DONNEES = [('nilobject', 0x00d03518), ('vt_rigid_dynamic', 0x00cdd478)]
VTABLE_SERVEUR = 0x00d34bc4


def masque(exe, va, n):
    """octets de [va, va+n) avec les champs relocalises mis a zero (meme ceux qui depassent la fin de la fenetre)."""
    b = bytearray(exe.octets(va, n))
    for p in range(n):
        if exe.est_reloc(va + p):
            for q in range(p, min(n, p + 4)):
                b[q] = 0
    for p in range(-3, 0):
        if exe.est_reloc(va + p):
            for q in range(0, p + 4):
                b[q] = 0
    return bytes(b)


def corps_identique(al, va_ancien, va_nouveau, max_ins=4000):
    """Nombre d'instructions IDENTIQUES (octets, jokers compris) depuis l'entree, dans l'ordre, avant la 1re difference,
    et si la fonction se termine (ret) dans cette suite. Decodage direct depuis l'entree des deux cotes."""
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    A, N = al.A, al.N
    ia = md.disasm(A.octets(va_ancien, 0x4000), va_ancien)
    ib = md.disasm(N.octets(va_nouveau, 0x4000), va_nouveau)
    n, premier_ret = 0, None
    for a, b in zip(ia, ib):
        if a.size != b.size or a.mnemonic != b.mnemonic:
            break
        ma, mb = masque(A, a.address, a.size), masque(N, b.address, b.size)
        if a.size == 5 and a.bytes[0] in (0xE8, 0xE9):
            ma, mb = ma[:1] + bytes(4), mb[:1] + bytes(4)
        elif a.size == 6 and a.bytes[0] == 0x0F and 0x80 <= a.bytes[1] <= 0x8F:
            ma, mb = ma[:2] + bytes(4), mb[:2] + bytes(4)
        if ma != mb:
            break
        n += 1
        if a.mnemonic in ('ret', 'retn') and premier_ret is None:
            premier_ret = n
        if n >= max_ins:
            break
    return n, premier_ret


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    A, N = Exe(sys.argv[1]), Exe(sys.argv[2])
    al = Alignement(A, N)
    L, res, problemes = [], {}, []

    def log(s=''):
        L.append(s)

    log('Profil du SDK pour le nouvel exe (PE 0x%08x, taille d\'image 0x%08x ; ancien : PE 0x%08x, taille 0x%08x)' % (
        N.horodatage, N.taille_image, A.horodatage, A.taille_image))
    log('')
    log('%-18s %-10s %-10s %-9s %-10s %s' % ('nom', 'ancien', 'nouveau', 'alignem.', 'corps ident.', 'octets controles (ancien | nouveau, jokers a 0)'))

    def traiter(nom, va, sig, fonction):
        nv, st, _ = al.va_nouveau(va)
        remarque = ''
        if nv is None or A.octets(va, 1) != N.octets(nv, 1):
            nv2 = None
        # cas particulier : l'entree tombe dans des donnees du .text (table de sauts) -> l'alignement ne la voit pas
        if nv is None:
            # cherche la signature dans le nouveau .text, a +-0x400 du decalage des suites egales voisines
            i = al.index_ancien(va)
            k = bisect.bisect_right(al._starts, i) - 1
            i0, j0, n = al.egaux[k]
            apres = al.egaux[k + 1] if k + 1 < len(al.egaux) else None
            ref = al.BN.addr[apres[1]] - al.BA.addr[apres[0]] if apres else al.BN.addr[j0] - al.BA.addr[i0]
            cible = A.octets(va, 8)
            t = N.sec_nom('.text')
            blob = N.data[t['rawptr']:t['rawptr'] + t['rawsz']]
            cand = []
            lo = va + ref - 0x400
            while True:
                j = blob.find(cible, max(0, lo - t['va']))
                if j == -1 or t['va'] + j > va + ref + 0x400:
                    break
                cand.append(t['va'] + j)
                lo = t['va'] + j + 1
            if len(cand) == 1:
                nv, st = cand[0], 'signature+voisin'
                remarque = 'entree dans une table de sauts du .text : trouvee par ses 8 octets (une seule occurrence a +-0x400 de la suite egale voisine, decalage ' + hex(ref) + ')'
            else:
                problemes.append((nom, va, 'entree non trouvee (%d candidats)' % len(cand)))
                log('%-18s 0x%08x %-10s %s' % (nom, va, 'INTROUVABLE', ''))
                res[nom] = dict(ancien=va, nouveau=None)
                return
        n_octets = len(sig) if sig else 8
        ma, mb = masque(A, va, n_octets), masque(N, nv, n_octets)
        sig_ok = (sig is None or (A.octets(va, n_octets) == sig and N.octets(nv, n_octets) == sig))
        egal_oct = ma == mb
        corps = ''
        if fonction:
            n, premier_ret = corps_identique(al, va, nv)
            corps = '%d instr. identiques%s' % (n, ', 1er ret a l\'instr. %d' % premier_ret if premier_ret else ', AUCUN ret dans la suite')
        ok = egal_oct and sig_ok
        if not ok:
            problemes.append((nom, va, 'octets differents: ancien %s nouveau %s' % (A.octets(va, n_octets).hex(), N.octets(nv, n_octets).hex())))
        log('%-18s 0x%08x 0x%08x %-9s %-12s %s | %s %s%s%s' % (
            nom, va, nv, st if st != 'egal' else 'egal', corps, A.octets(va, n_octets).hex(), N.octets(nv, n_octets).hex(),
            '' if ok else ' << DIFFERENT', ' [signature du source OK]' if sig and sig_ok else '', ' ' + remarque if remarque else ''))
        res[nom] = dict(ancien=va, nouveau=nv, alignement=st, corps=corps, octets_ancien=A.octets(va, n_octets).hex(),
                        octets_nouveau=N.octets(nv, n_octets).hex(), remarque=remarque)

    log('--- cc2x.c : fonctions du jeu')
    for nom, va, sig in FONCTIONS_CC2X:
        traiter(nom, va, sig, True)
    log('--- cc2x.c : site du crochet Lua (8 octets controles)')
    for nom, va, sig in SITES_CC2X:
        traiter(nom, va, sig, False)

    # --- table virtuelle du serveur
    log('--- cc2x.c : table virtuelle du serveur (3 pointeurs init, tick, end)')
    cible = struct.pack('<III', res['server_init']['nouveau'], res['server_tick']['nouveau'], res['server_end']['nouveau'])
    rd = N.sec_nom('.rdata')
    blob = N.data[rd['rawptr']:rd['rawptr'] + rd['rawsz']]
    trouves, j = [], blob.find(cible)
    while j != -1:
        trouves.append(rd['va'] + j)
        j = blob.find(cible, j + 1)
    ancien_ok = struct.pack('<III', *[res[k]['ancien'] for k in ('server_init', 'server_tick', 'server_end')]) == A.octets(VTABLE_SERVEUR, 12)
    reloc_ok = all(N.est_reloc(trouves[0] + 4 * k) for k in range(3)) if len(trouves) == 1 else False
    log('ancien : 0x%08x contient (init, tick, end) = %s ; nouveau : triplet trouve en %s (relocations: %s)' % (
        VTABLE_SERVEUR, 'OUI' if ancien_ok else 'NON', [hex(x) for x in trouves], reloc_ok))
    if len(trouves) != 1 or not ancien_ok or not reloc_ok:
        problemes.append(('server_vtable', VTABLE_SERVEUR, 'triplet non unique / non relocalise'))
    res['server_vtable'] = dict(ancien=VTABLE_SERVEUR, nouveau=trouves[0] if len(trouves) == 1 else None)
    # voisins de la table : le pointeur juste avant (info de type) correspond ?
    log('   pointeur juste avant : ancien 0x%08x, nouveau 0x%08x' % (A.u32(VTABLE_SERVEUR - 4), N.u32(trouves[0] - 4) if trouves else 0))

    # --- donnees
    log('--- donnees lues par le code (retrouvees par TOUTES leurs references dans le code)')
    t = A.sec_nom('.text')
    for nom, val in DONNEES:
        refs = [A.base + rva for rva in sorted(A.relocs) if t['va'] <= A.base + rva < t['va'] + t['vsize'] and A.u32(A.base + rva) == val]
        cand, diffs = {}, 0
        for r in refs:
            nv, st, _ = al.va_nouveau(r)
            if nv is None:
                diffs += 1
                continue
            cand.setdefault(N.u32(nv), []).append(r)
        un = len(cand) == 1
        nouvelle = next(iter(cand)) if un else None
        # le contenu pointe est-il pareil ?
        meme_contenu = None
        if nouvelle:
            meme_contenu = A.octets(val, 16) == N.octets(nouvelle, 16) or A.nom_section(val) == N.nom_section(nouvelle)
        log('%-18s ancien 0x%08x -> nouveau %s : %d references dans l\'ancien code, %d dans des blocs qui different (ignorees), valeurs vues dans le nouveau : %s ; section %s -> %s ; 16 octets identiques : %s' % (
            nom, val, hex(nouvelle) if nouvelle else '?', len(refs), diffs, {hex(k): len(v) for k, v in cand.items()},
            A.nom_section(val), N.nom_section(nouvelle) if nouvelle else '?', A.octets(val, 16) == N.octets(nouvelle, 16) if nouvelle else None))
        if not un:
            problemes.append((nom, val, 'plusieurs valeurs candidates'))
        res[nom] = dict(ancien=val, nouveau=nouvelle, references=len(refs), valeurs_vues={hex(k): len(v) for k, v in cand.items()})

    log('--- world.c : fonctions du jeu')
    for nom, va in FONCTIONS_WORLD:
        traiter(nom, va, None, True)
    log('--- world.c : sites de crochets (octets controles comme dans le source)')
    for nom, va, sig in SITES_WORLD:
        traiter(nom, va, sig, False)

    log('')
    if problemes:
        log('PROBLEMES (on s\'arrete, rien n\'est devine) :')
        for p in problemes:
            log('   %s 0x%08x : %s' % p)
    else:
        log('Aucun probleme : toutes les valeurs sont retrouvees.')
    with open(sys.argv[3], 'w', encoding='utf-8') as f:
        json.dump(dict(valeurs=res, problemes=problemes), f, indent=1)
    with open(sys.argv[4], 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))
    return 1 if problemes else 0


if __name__ == '__main__':
    sys.exit(main())
