#!/usr/bin/env python3
"""Modele IDEALISE de la machine a etats du circuit d'attente des avions (Windows 1.5.18), lue au desassemblage
de la fonction 0x6fc730-0x701fa8 (jump table 0x701fd0, 6 etats). Calcul pur : ne lit ni n'ecrit aucun fichier.

Hypothese du modele : l'avion suit EXACTEMENT la trajectoire theorique (pas d'inertie, pas de vent), a 80 m/s,
tick de 1/30 s. Ce n'est PAS une preuve en jeu : ca verifie seulement que les 6 etats s'enchainent bien dans
l'ordre 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 0 avec les seuils d'origine puis avec les seuils modifies, la duree d'un
tour, et la taille de la fenetre ou la piste peut etre donnee.

Usage : python -I modele_circuit.py
Repere du bateau : x vers tribord, z vers la proue (metres). Les transitions sont celles du code :
  etat 0 : ligne x = -2200 vers l'arriere      -> etat 1 quand z < -1800                       (0x7018e1)
  etat 1 : 1re moitie du virage arriere        -> etat 2 quand x > -1000  (= la « porte »)    (0x7019f3)
  etat 2 : 2e moitie du virage arriere         -> etat 3 quand z > -1800                       (0x701d2c)
  etat 3 : ligne x = 200 vers l'avant          -> etat 4 quand z > SEUIL_3  (600 d'origine)    (0x701d5b)
  etat 4 : 1er quart du virage avant           -> etat 5 quand x < -1000                       (0x701e58)
  etat 5 : 2e quart du virage avant            -> etat 0 quand z < SEUIL_5  (600 d'origine)    (0x701f4e)
Virage arriere : centre (-1000, -1800). Virage avant : centre (-1000, CENTRE_AVANT_Z), rayon 1200.
Piste donnee si mode == 1, piste libre et distance a la porte (-1000, -3000) < 1000 m (0x701a79).
"""
import math

V, DT, R = 80.0, 1 / 30.0, 1200.0
PORTE = (-1000.0, -3000.0)


def tour(centre_avant_z, seuil_3, seuil_5):
    """Fait faire un tour a l'avion ideal ; rend (duree en s, longueur en m, [(etat, ticks)], etats dans l'ordre,
    arc de fenetre etat 1 + etat 2 (m) ou la distance a la porte est < 1000)."""
    # position de depart : milieu de la ligne arriere (etat 0), si elle existe ; sinon sur le cercle a gauche
    x, z, etat = -2200.0, max(centre_avant_z, -1800.0), 0
    # chemin ideal : suite de morceaux (type, parametres)
    ticks = {i: 0 for i in range(6)}
    ordre, fenetre = [0], {1: 0.0, 2: 0.0}
    cap = (0.0, -1.0)           # cap initial : vers l'arriere (-z)
    s, t = 0.0, 0.0
    ZA = -1800.0                # centre du virage arriere (z)
    # on avance sur le chemin theorique par pas de V*DT ; la position est recalculee a partir de l'abscisse curviligne
    # morceaux (dans l'ordre de parcours) : (etat, longueur, fonction position(u))
    def ligne(x0, z0, x1, z1):
        L = math.hypot(x1 - x0, z1 - z0)
        return L, (lambda u: (x0 + (x1 - x0) * u / L, z0 + (z1 - z0) * u / L)) if L > 0 else (lambda u: (x0, z0))

    def arc(cx, cz, a0, a1):
        L = R * abs(a1 - a0)
        return L, (lambda u: (cx + R * math.cos(a0 + (a1 - a0) * u / L), cz + R * math.sin(a0 + (a1 - a0) * u / L))) if L > 0 else (lambda u: (cx + R * math.cos(a0), cz + R * math.sin(a0)))

    # angles : 0 = cote tribord (x + R), pi/2 = vers la proue (+z), pi = babord, 3pi/2 = vers l'arriere
    morceaux = []
    morceaux.append(ligne(-2200.0, centre_avant_z, -2200.0, ZA))                                   # ligne arriere (peut etre nulle)
    morceaux.append(arc(-1000.0, ZA, math.pi, 3 * math.pi / 2))                                    # virage arriere, 1re moitie
    morceaux.append(arc(-1000.0, ZA, 3 * math.pi / 2, 2 * math.pi))                                # virage arriere, 2e moitie
    morceaux.append(ligne(200.0, ZA, 200.0, centre_avant_z))                                       # ligne avant (peut etre nulle)
    morceaux.append(arc(-1000.0, centre_avant_z, 0.0, math.pi / 2))                                # virage avant, 1er quart
    morceaux.append(arc(-1000.0, centre_avant_z, math.pi / 2, math.pi))                            # virage avant, 2e quart
    longueur = sum(m[0] for m in morceaux)
    pos = lambda d: _pos(morceaux, d)
    d, etat, n = 0.0, 0, 0
    z_prec = None
    while n < 100000:
        x, z = pos(d)
        # la machine a etats du code, lue dans l'ordre des etats (un changement par tick)
        suivant = etat
        if etat == 0 and z < -1800.0:
            suivant = 1
        elif etat == 1 and x > -1000.0:
            suivant = 2
        elif etat == 2 and z > -1800.0:
            suivant = 3
        elif etat == 3 and z > seuil_3:
            suivant = 4
        elif etat == 4 and x < -1000.0:
            suivant = 5
        elif etat == 5 and z < seuil_5:
            suivant = 0
        ticks[etat] += 1
        if etat in (1, 2) and math.hypot(x - PORTE[0], z - PORTE[1]) < 1000.0:
            fenetre[etat] += V * DT
        if suivant != etat:
            ordre.append(suivant)
            if suivant == 0 and len(ordre) > 1:          # un tour complet : retour a l'etat 0
                break
            etat = suivant
        d += V * DT
        n += 1
    return n * DT, longueur, ticks, ordre, fenetre


def _pos(morceaux, d):
    d_mod = d % sum(m[0] for m in morceaux)
    for L, f in morceaux:
        if d_mod <= L:
            return f(d_mod)
        d_mod -= L
    return morceaux[-1][1](morceaux[-1][0])


def main():
    print("Modele idealise du circuit d'attente (avion ideal a 80 m/s)\n")
    for nom, c, s3, s5 in (("ORIGINE (ovale)", 600.0, 600.0, 600.0), ("MODIFIE (cercle)", -1800.0, -1800.0, -1800.0)):
        duree, longueur, ticks, ordre, fen = tour(c, s3, s5)
        print("%s : centre avant z = %g, seuil etat 3 = %g, seuil etat 5 = %g" % (nom, c, s3, s5))
        print("  longueur theorique du tour : %.0f m  -> %.0f s ; tour simule : %.1f s" % (longueur, longueur / V, duree))
        print("  etats visites dans l'ordre : %s" % ' -> '.join(map(str, ordre)))
        print("  ticks passes dans chaque etat : %s" % ', '.join('etat %d: %d' % (e, t) for e, t in ticks.items()))
        print("  fenetre de piste (distance a la porte < 1000 m) : etat 1 = %.0f m, etat 2 = %.0f m, total %.0f m = %.1f s de vol" % (
            fen[1], fen[2], fen[1] + fen[2], (fen[1] + fen[2]) / V))
        print("  (au jeu d'origine seul le tick du passage 1 -> 2 compte : fenetre = 1 tick = %.1f m)\n" % (V * DT))
    # controle : l'enchainement doit etre 0,1,2,3,4,5,0 dans les deux cas
    for c, s3, s5 in ((600.0, 600.0, 600.0), (-1800.0, -1800.0, -1800.0)):
        ordre = tour(c, s3, s5)[3]
        assert ordre == [0, 1, 2, 3, 4, 5, 0], ordre
    print("Controle : l'ordre 0,1,2,3,4,5,0 est respecte dans les deux cas.")


if __name__ == '__main__':
    main()
