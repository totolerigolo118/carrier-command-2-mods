"""Extrait d'un journal cc2x.log (copie) les seules lignes CC2MAP comprises entre deux heures, pour isoler UNE partie parmi plusieurs
(le temps du jeu repart de zero a chaque nouvelle partie, ce qui melangerait les instantanes). Aucune autre ligne du journal n'est gardee.

Usage : python -I extraire_partie.py <journal copie> HH:MM:SS HH:MM:SS <fichier de sortie NEUF>
"""
import os
import re
import sys

RX = re.compile(r'^(\d\d):(\d\d):(\d\d\.\d+) .*?CC2MAP\|')


def sec(h):
    a, b, c = h.split(':')
    return int(a) * 3600 + int(b) * 60 + int(c)


def main():
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    t0, t1, sortie = sec(sys.argv[2]), sec(sys.argv[3]), sys.argv[4]
    if os.path.exists(sortie):
        raise SystemExit('REFUS : %s existe deja' % sortie)
    n = 0
    with open(sys.argv[1], encoding='latin-1') as f, open(sortie, 'w', encoding='latin-1', newline='\n') as o:
        for ln in f:
            m = RX.match(ln)
            if m and t0 <= int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) <= t1:
                o.write(ln.rstrip('\r\n') + '\n')
                n += 1
    print('lignes CC2MAP gardees :', n, '->', sortie)


if __name__ == '__main__':
    main()
