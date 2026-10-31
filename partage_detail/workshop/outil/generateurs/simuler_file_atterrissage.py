#!/usr/bin/env python3
"""Simulation of the CC2 aircraft landing queue (logic read in docking_manager_air::update).

Model: waiting planes follow the pattern at 80 m/s (abscissa s along the lap, 0 = the "gate" at the
bottom of the rear turn). A plane is given the runway if the runway is free AND it is inside the
assignment window. The runway stays occupied O seconds (approach + touchdown + taxiing to the elevator).
Original game: window = the instant the plane passes the gate (one tick per lap).
"""
import random

V = 80.0              # m/s, holding speed (override_target_velocity = 80)
TICK = 1 / 30.0
QUART = 1200 * 3.14159265 / 2          # quarter of a turn, radius 1200 m
AVANT = 1031.0        # part of state 1 within 1000 m of the gate
APRES = 1684.0        # part of state 2 where the distance test passes (z < -2000)

CIRCUITS = {
    "origine": 2 * 2400 + 2 * 1200 * 3.14159265,    # oval: 2 straight lines of 2400 m + 2 half-circles
    "cercle": 2 * 1200 * 3.14159265,                # both turns on the same circle
}


def simuler(tour, fenetre, O, departs, horizon=3000):
    """departs: starting abscissae of the planes (m, counted BEFORE the gate). Returns the instants
    of runway assignment and the final release time."""
    s = [(-d) % tour for d in departs]          # position along the lap
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
                    dedans = a < tour <= b or (b >= tour)            # passing the gate during this tick
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
    print("  landing duration O :        90 s    110 s    130 s    150 s    170 s")
    for titre, tour, fen in (("original game          ", CIRCUITS["origine"], False),
                             ("A widened window       ", CIRCUITS["origine"], True),
                             ("B A + circular pattern ", CIRCUITS["cercle"], True)):
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
    print("Lap of the pattern: original %.0f m (%.0f s), circle %.0f m (%.0f s)"
          % (CIRCUITS["origine"], CIRCUITS["origine"] / V, CIRCUITS["cercle"], CIRCUITS["cercle"] / V))
    # 4 planes coming back together, in a line 300 m apart, the first one 2 km from the gate
    scenario("4 grouped planes (time between arrival near the gate and the 4th on the elevator)",
             lambda tour: [2000 + 300 * k for k in range(4)], 1)
    # 4 planes arriving at different times: random positions on the pattern
    scenario("4 planes scattered at random on the pattern (average of 400 trials)",
             lambda tour: [random.uniform(0, tour) for _ in range(4)], 400)
