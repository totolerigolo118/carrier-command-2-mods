#!/usr/bin/env python3
"""Alignement de TOUT le code (.text) de l'ancien exe et du nouvel exe de Steam, instruction par instruction. LECTURE SEULE.

Deux instructions sont « egales » si leurs octets sont les memes, les champs qui changent forcement d'un build a l'autre
(adresses absolues avec relocation, deplacements des call/jmp/jcc rel32) etant mis a zero. Marche en parallele sur les deux
exe ; a la premiere difference, on cherche le plus petit saut (insertion / suppression / remplacement) apres lequel 8
instructions de suite redeviennent egales.

Utilisation comme module : Alignement(ancien, nouveau).va_nouveau(va_ancien) -> (va_nouveau, distance_a_la_difference_la_plus_proche)
Utilisation en script : python -I -B alignement.py <ancien> <nouveau> <sortie.txt>
"""
import bisect
import os
import sys
from array import array

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_lecture import Exe  # noqa: E402
from localiser_sites import Balayage  # noqa: E402

K = 8            # instructions de suite qui doivent redevenir egales pour reprendre l'alignement
FENETRE = 800    # saut maximal (en instructions) cherche de chaque cote


def cles(bal):
    """hash de (taille, octets avec jokers a zero) pour chaque instruction."""
    exe = bal.exe
    relocs = exe.relocs
    base = exe.base
    texte, va0 = bal.texte, bal.va_texte
    out = array('q')
    for a, sz in zip(bal.addr, bal.size):
        o = a - va0
        raw = bytearray(texte[o:o + sz])
        rva = a - base
        if sz >= 4:
            for p in range(0, sz - 3):
                if (rva + p) in relocs:
                    raw[p:p + 4] = b'\0\0\0\0'
            if sz == 5 and raw[0] in (0xE8, 0xE9):
                raw[1:5] = b'\0\0\0\0'
            elif sz == 6 and raw[0] == 0x0F and 0x80 <= raw[1] <= 0x8F:
                raw[2:6] = b'\0\0\0\0'
        out.append(hash(bytes(raw)))
    return out


def fenetres(k):
    """hash des K cles suivantes, pour chaque position."""
    n = len(k)
    out = array('q', [0]) * n
    for i in range(n - K + 1):
        out[i] = hash(tuple(k[i:i + K]))
    return out


class Alignement:
    def __init__(self, ancien, nouveau):
        self.A, self.N = ancien, nouveau
        self.BA, self.BN = Balayage(ancien), Balayage(nouveau)
        ka, kn = cles(self.BA), cles(self.BN)
        wa, wn = fenetres(ka), fenetres(kn)
        na, nn = len(ka), len(kn)
        self.egaux = []        # (i_ancien, j_nouveau, longueur) : suites d'instructions egales
        self.diffs = []        # (i0, i1, j0, j1) : instructions i0..i1-1 de l'ancien <-> j0..j1-1 du nouveau
        i = j = 0
        debut_i = debut_j = 0
        while i < na and j < nn:
            if ka[i] == kn[j]:
                i += 1
                j += 1
                continue
            if i > debut_i:
                self.egaux.append((debut_i, debut_j, i - debut_i))
            # cherche la reprise : plus petit di + dj avec les memes K instructions
            vus = {}
            for dj in range(min(FENETRE, nn - K - j) + 1):
                vus.setdefault(wn[j + dj], dj)
            meilleur = None
            for di in range(min(FENETRE, na - K - i) + 1):
                dj = vus.get(wa[i + di])
                if dj is not None and (meilleur is None or di + dj < meilleur[0]):
                    meilleur = (di + dj, di, dj)
                if meilleur is not None and di >= meilleur[0]:
                    break
            if meilleur is None:
                self.diffs.append((i, na, j, nn))      # plus de reprise : le reste est different
                i, j = na, nn
                debut_i, debut_j = i, j
                break
            _, di, dj = meilleur
            self.diffs.append((i, i + di, j, j + dj))
            i, j = i + di, j + dj
            debut_i, debut_j = i, j
        if i > debut_i:
            self.egaux.append((debut_i, debut_j, i - debut_i))
        self._starts = [e[0] for e in self.egaux]

    # --- correspondance d'une adresse
    def index_ancien(self, va):
        i = bisect.bisect_right(self.BA.addr, va) - 1
        return i if i >= 0 and self.BA.addr[i] <= va < self.BA.addr[i] + self.BA.size[i] else None

    def va_nouveau(self, va):
        """-> (adresse nouvelle ou None, statut, instructions egales autour) pour une adresse de l'ancien exe.
        statut : 'egal' (dans une suite d'instructions egales), 'difference' (dans un bloc qui differe), 'hors code'."""
        i = self.index_ancien(va)
        if i is None:
            return None, 'hors code', 0
        k = bisect.bisect_right(self._starts, i) - 1
        if k >= 0:
            i0, j0, n = self.egaux[k]
            if i0 <= i < i0 + n:
                j = j0 + (i - i0)
                dec = va - self.BA.addr[i]
                return self.BN.addr[j] + dec, 'egal', min(i - i0, i0 + n - 1 - i)
        return None, 'difference', 0

    def blocs_proches(self, va, rayon=40):
        """blocs de difference a moins de `rayon` instructions de l'adresse (ancien exe)."""
        i = self.index_ancien(va)
        if i is None:
            return []
        return [d for d in self.diffs if d[0] - rayon <= i < d[1] + rayon]

    def texte_ancien(self, i0, i1, n=6):
        return ['%08x %s %s' % (self.BA.addr[i], self.BA.mn[i], self.BA.op[i]) for i in range(i0, min(i1, i0 + n))]

    def texte_nouveau(self, j0, j1, n=6):
        return ['%08x %s %s' % (self.BN.addr[j], self.BN.mn[j], self.BN.op[j]) for j in range(j0, min(j1, j0 + n))]


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    A, N = Exe(sys.argv[1]), Exe(sys.argv[2])
    al = Alignement(A, N)
    L = ['Alignement du code (.text) ancien 1C9A01C3... / nouveau 461E1262... (jokers : adresses absolues et deplacements relatifs)',
         'instructions : ancien %d, nouveau %d' % (len(al.BA.addr), len(al.BN.addr)),
         'suites egales : %d, couvrant %d instructions de l\'ancien' % (len(al.egaux), sum(e[2] for e in al.egaux)),
         'blocs qui different : %d (%d instructions de l\'ancien, %d du nouveau)' % (
             len(al.diffs), sum(d[1] - d[0] for d in al.diffs), sum(d[3] - d[2] for d in al.diffs)), '']
    L.append('--- chaque bloc : ancien i0-i1 (adresse) | nouveau j0-j1 (adresse) | type | decalage des adresses avant/apres')
    for (i0, i1, j0, j1) in al.diffs:
        a0 = al.BA.addr[i0] if i0 < len(al.BA.addr) else 0
        b0 = al.BN.addr[j0] if j0 < len(al.BN.addr) else 0
        typ = 'insertion' if i1 == i0 else ('suppression' if j1 == j0 else 'remplacement')
        L.append('0x%08x (+%d instr.) | 0x%08x (+%d instr.) | %s | decalage %+#x' % (a0, i1 - i0, b0, j1 - j0, typ, b0 - a0))
        for t in al.texte_ancien(i0, i1, 4):
            L.append('      - ' + t)
        for t in al.texte_nouveau(j0, j1, 4):
            L.append('      + ' + t)
    with open(sys.argv[3], 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L[:4]))


if __name__ == '__main__':
    main()
