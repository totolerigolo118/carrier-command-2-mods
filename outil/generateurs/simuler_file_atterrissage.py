#!/usr/bin/env python3
"""Simulation de la file d'atterrissage des avions de CC2 (logique lue dans docking_manager_air::update).

Modele : les avions en attente suivent le circuit a 80 m/s (abscisse s le long du tour, 0 = la « porte »
au bas du virage arriere). Un avion recoit la piste si la piste est libre ET s'il est dans la fenetre
d'attribution. La piste reste occupee O secondes (approche + toucher + roulage jusqu'a l'ascenseur).
Jeu d'origine : fenetre = l'instant ou l'avion passe la porte (un tick par tour).
"""
import random

V = 80.0              # m/s, vitesse d'attente (override_target_velocity = 80)
TICK = 1 / 30.0
QUART = 1200 * 3.14159265 / 2          # quart de virage, rayon 1200 m
AVANT = 1031.0        # partie de l'etat 1 a moins de 1000 m de la porte
APRES = 1684.0        # partie de l'etat 2 ou le test de distance passe (z < -2000)

CIRCUITS = {
    "origine": 2 * 2400 + 2 * 1200 * 3.14159265,    # ovale : 2 lignes droites de 2400 m + 2 demi-cercles
    "cercle": 2 * 1200 * 3.14159265,                # les deux virages sur le meme cercle
}


def simuler(tour, fenetre, O, departs, horizon=3000):
    """departs : abscisses de depart des avions (m, comptees AVANT la porte). Rend les instants
    d'attribution de la piste et l'heure de liberation finale."""
    s = [(-d) % tour for d in departs]          # position le long du tour
    attente = list(range(len(s)))
    libre_a = 0.0
    attrib = []
    t = 0.0
    while attente and t < horizon:
        if t >= libre_a:
            for i in attente:
                a, b = s[i], (s[i] + V * TICK)
                if fenetre:
                    dedans = s[i] >= tour - AVANT or s[i] <= APRES
                else:
                    dedans = a < tour <= b or (b >= tour)            # passage de la porte pendant ce tick
                if dedans:
                    attrib.append(t)
                    attente.remove(i)
                    libre_a = t + O
                    break
        for i in attente:
            s[i] = (s[i] + V * TICK) % tour
        t += TICK
    return attrib, (attrib[-1] + O if len(attrib) == len(departs) else None)


def scenario(nom, departs_fn, essais):
    print("\n" + nom)
    print("  duree d'un atterrissage O :      90 s    110 s    130 s    150 s    170 s")
    for titre, tour, fen in (("jeu d'origine          ", CIRCUITS["origine"], False),
                             ("A creneau elargi       ", CIRCUITS["origine"], True),
                             ("B A + circuit en cercle", CIRCUITS["cercle"], True)):
        ligne = []
        for O in (90, 110, 130, 150, 170):
            tot = []
            for k in range(essais):
                random.seed(k)
                _, fin = simuler(tour, fen, O, departs_fn(tour))
                tot.append(fin)
            ligne.append(sum(tot) / len(tot))
        print("  %s  %s" % (titre, "  ".join("%5.0f s" % x for x in ligne)))


if __name__ == "__main__":
    print("Tour du circuit : origine %.0f m (%.0f s), cercle %.0f m (%.0f s)"
          % (CIRCUITS["origine"], CIRCUITS["origine"] / V, CIRCUITS["cercle"], CIRCUITS["cercle"] / V))
    # 4 avions qui rentrent ensemble, en file a 300 m les uns des autres, le premier a 2 km de la porte
    scenario("4 avions groupes (temps entre l'arrivee pres de la porte et le 4e sur l'ascenseur)",
             lambda tour: [2000 + 300 * k for k in range(4)], 1)
    # 4 avions arrives a des moments differents : positions au hasard sur le circuit
    scenario("4 avions disperses au hasard sur le circuit (moyenne de 400 essais)",
             lambda tour: [random.uniform(0, tour) for _ in range(4)], 400)
