#!/usr/bin/env python3
"""Forme reelle du circuit d'attente des avions, lue dans le journal du SDK (cc2x.log) : LECTURE SEULE, sur une COPIE du journal.

Le mod cc2_carte ecrit toutes les ~10 s de jeu des lignes `CC2MAP|V|<tick>|<p>/<n>|id,def,team,x,z,cap;...`. On y suit le bateau
(id 2) et les avions, on passe leurs positions dans le repere du bateau (x vers tribord, z vers la proue) et on regarde la partie
« attente » (entre le premier passage a l'arriere et le toucher) : etendue en z, cercle ajuste (moindres carres), temps par tour.
Un OVALE d'origine monterait a z = +1800 au virage avant (centre 600) ; un CERCLE reste derriere le bateau (centre z = -1800).

Usage : python -I trajets_circuit.py <copie_de_cc2x.log> [--navire 2] [--avions 9,10,17,18]
"""
import collections
import math
import re
import sys


def lire(chemin):
    snaps = collections.defaultdict(dict)
    for ligne in open(chemin, encoding='utf-8', errors='replace'):
        m = re.search(r'CC2MAP\|V\|(\d+)\|(\d+)/(\d+)\|(.*)$', ligne)
        if not m:
            continue
        t = int(m.group(1))
        for u in m.group(4).strip().split(';'):
            f = u.split(',')
            if len(f) == 6:
                snaps[t][int(f[0])] = (int(f[1]), int(f[2]), float(f[3]), float(f[4]), float(f[5]))
    return snaps


def serie(snaps, navire, i):
    """[(secondes de jeu, tribord, avant, cap)] une mesure par instantane, repere du bateau."""
    res, vus = [], set()
    for t in sorted(snaps):
        if i in snaps[t] and navire in snaps[t] and t // 15 not in vus:
            vus.add(t // 15)
            _, _, x, z, c = snaps[t][i]
            _, _, sx, sz, sc = snaps[t][navire]
            a = math.radians(sc)
            dx, dz = x - sx, z - sz
            res.append((t / 30.0, dx * math.cos(a) - dz * math.sin(a), dx * math.sin(a) + dz * math.cos(a), c))
    return res


def cercle(pts):
    """Cercle ajuste (Kasa) : (cx, cz, rayon, ecart_moyen)."""
    n = len(pts)
    sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
    sxx = sum(p[0] ** 2 for p in pts); syy = sum(p[1] ** 2 for p in pts); sxy = sum(p[0] * p[1] for p in pts)
    sxxx = sum(p[0] ** 3 for p in pts); syyy = sum(p[1] ** 3 for p in pts)
    sxyy = sum(p[0] * p[1] ** 2 for p in pts); sxxy = sum(p[0] ** 2 * p[1] for p in pts)
    C = n * sxx - sx * sx; D = n * sxy - sx * sy; E = n * (sxxx + sxyy) - (sxx + syy) * sx
    G = n * syy - sy * sy; H = n * (sxxy + syyy) - (sxx + syy) * sy
    den = 2 * (C * G - D * D)
    a = (G * E - D * H) / den
    b = (C * H - D * E) / den
    ray = [math.hypot(p[0] - a, p[1] - b) for p in pts]
    r = sum(ray) / n
    return a, b, r, sum(abs(x - r) for x in ray) / n


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    navire = int(sys.argv[sys.argv.index('--navire') + 1]) if '--navire' in sys.argv else 2
    ids = [int(x) for x in (sys.argv[sys.argv.index('--avions') + 1] if '--avions' in sys.argv else '9,10,17,18').split(',')]
    snaps = lire(sys.argv[1])
    print('journal : %d instantanes, de %.0f a %.0f s de jeu ; navire = id %d' % (len(snaps), min(snaps) / 30, max(snaps) / 30, navire))
    for i in ids:
        s = serie(snaps, navire, i)
        # attente : du premier point loin derriere le bateau (z < -2000) jusqu'au toucher (au plus pres du bateau, z > 0)
        debut = next((k for k, p in enumerate(s) if p[2] < -2000), None)
        if debut is None:
            print('avion %d : jamais loin derriere le bateau' % i)
            continue
        fin = next((k for k in range(debut, len(s)) if abs(s[k][1]) < 60 and -20 < s[k][2] < 200), len(s) - 1)
        attente = s[debut:fin]
        boucle = [p for p in attente if math.hypot(p[1] + 1000, p[2] + 1800) < 1500 and p[2] < -700]
        print('\navion %d : toucher vers %.0f s de jeu ; attente de %.0f s a %.0f s (%d points)' % (i, s[fin][0], attente[0][0], attente[-1][0], len(attente)))
        print('  z (avant) pendant l\'attente : de %.0f a %.0f m ; x (tribord) : de %.0f a %.0f m   (ovale d\'origine : z monterait vers +1800)' % (
            min(p[2] for p in attente), max(p[2] for p in attente), min(p[1] for p in attente), max(p[1] for p in attente)))
        if len(boucle) >= 8:
            cx, cz, r, ec = cercle([(p[1], p[2]) for p in boucle])
            # nombre de tours : angle cumule autour du centre ajuste
            ang, prec, tot = None, None, 0.0
            for p in boucle:
                a = math.atan2(p[2] - cz, p[1] - cx)
                if prec is not None:
                    d = a - prec
                    while d > math.pi:
                        d -= 2 * math.pi
                    while d < -math.pi:
                        d += 2 * math.pi
                    tot += d
                prec = a
            duree = boucle[-1][0] - boucle[0][0]
            tours = abs(tot) / (2 * math.pi)
            print('  cercle ajuste sur %d points : centre (%.0f, %.0f) m, rayon %.0f m (ecart moyen %.0f m) ; %.1f tours en %.0f s -> %.0f s par tour' % (
                len(boucle), cx, cz, r, ec, tours, duree, duree / tours if tours else 0))
        else:
            print('  peu de points en boucle (%d) : l\'avion a eu la piste presque tout de suite' % len(boucle))


if __name__ == '__main__':
    main()
