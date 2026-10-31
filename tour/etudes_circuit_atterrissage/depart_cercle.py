"""Usage : python -I depart_cercle.py <copie_de_cc2x.log>   (avions 10, 17, 9, 18 ; navire id 2)
Ou chaque avion quitte le cercle d'attente (lecture seule d'une COPIE du journal). Repere du bateau ; centre du cercle (-1000,-1800).
Etat 1 = 1re moitie du virage arriere : angle 180 -> 270 deg (portillon d'origine a 270 = (-1000,-3000))."""
import importlib.util, math, os, sys
spec = importlib.util.spec_from_file_location('tc', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trajets_circuit.py'))
tc = importlib.util.module_from_spec(spec); spec.loader.exec_module(tc)
snaps = tc.lire(sys.argv[1])
CX, CZ = -1000.0, -1800.0
for i in (10, 17, 9, 18):
    s = tc.serie(snaps, 2, i)
    debut = next(k for k, p in enumerate(s) if p[2] < -2000)
    fin = next((k for k in range(debut, len(s)) if abs(s[k][1]) < 60 and -20 < s[k][2] < 200), len(s) - 1)
    print('\navion %d : toucher vers %.0f s (journal du SDK)' % (i, s[fin][0]))
    print('   t(s)    x(m)    z(m)   angle/centre  dist/centre')
    for p in s[max(debut, fin - 9):fin + 1]:
        a = math.degrees(math.atan2(p[2] - CZ, p[1] - CX)) % 360
        print('  %5.0f  %6.0f  %6.0f   %6.0f deg    %6.0f' % (p[0], p[1], p[2], a, math.hypot(p[1] - CX, p[2] - CZ)))
