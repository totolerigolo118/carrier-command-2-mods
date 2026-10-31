"""Quatre videos de LA PARTIE du 30/10 (08:44:31 -> 08:55:29), version 2 : meme rendu que fabriquer_videos_partie.py (importe ici, inchange), mais
cadrage mieux centre. Les videos v1 n'etaient pas centrees :
 - ARCHIPEL : le cadre etait la boite des iles + positions de l'equipe 1 avec 1 % de marge (et un rayon d'ile approximatif) : le porte-avions touchait presque
   le bord bas, l'avion 10 le bord haut. v2 : cadre FIXE, centre sur la boite englobante de TOUT ce qui est dessine (contour exact des iles, toutes les positions
   de toutes les unites : route du porte-avions, trace de l'avion 10 jusqu'au bout), avec 6 % de marge de chaque cote ; echelle constante.
 - ZOOM : le cadre de 20 km etait fixe, centre sur la route du porte-avions, alors que le porte-avions bouge (~3 km) et que la trace de l'avion 10 monte hors
   du cadre. v2 : le cadre de 20 km SUIT le porte-avions : centre sur sa position lissee (moyenne glissante de +/- 20 s d'horloge du journal) a chaque image ;
   le fond (quadrillage, iles) defile en consequence, l'echelle reste fixe.
Reste inchange : pictos du jeu teintes par equipe, iles colorees par proprietaire, avions 9 et 10 par-dessus le porte-avions, echelle, horloge, x11, 1 s de
pause finale, H.264 yuv420p 1280x720 30 i/s sans son. Aucun fichier du dossier du jeu n'est lu (pictos : carte_timelapse/icones, Mac).

Usage : python -I fabriquer_videos_partie_v2.py <extrait CC2MAP de la partie> <dossier icones> <dossier de sortie NEUF>
        python -I fabriquer_videos_partie_v2.py <extrait> <dossier icones> --png M3|M5 zoom|archipel HH:MM:SS fichier.png
        python -I fabriquer_videos_partie_v2.py <extrait> <dossier icones> --controle      (marges de l'archipel, ecart porte-avions / centre, sortie de l'avion 10)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc2map
import fabriquer_cartes_couleurs as C
import fabriquer_maquettes as M
import fabriquer_videos_couleurs as VC
import fabriquer_videos_partie as P1

MARGE = 0.06                    # part du cadre laissee libre de chaque cote (archipel)
LISSAGE_S = 20                  # demi-fenetre de la moyenne glissante de la camera (s d'horloge du journal)
FACTEUR = P1.FACTEUR


def etendue_dessinee(d):
    """Boite englobante (x0, x1, z0, z1) de tout ce qui est dessine : contour exact des iles (avec la cote de M3, la plus large) et toutes les positions."""
    xs, zs = [], []
    for iid, ix, iz in d['iles']:
        prof = M.profil(iid)
        for n in range(96):
            a = n / 96 * 6.2832
            xs.append(ix + math.cos(a) * M.ILE_R * 1.13 * prof[n])
            zs.append(iz + math.sin(a) * M.ILE_R * 1.13 * prof[n])
    for w, t, it in d['V']:
        for v in it.values():
            xs.append(v[2])
            zs.append(v[3])
    return min(xs), max(xs), min(zs), max(zs)


def cadre_v2(d, nom):
    """Remplace fabriquer_cartes_couleurs.cadre. Zoom : 20 km de haut centres sur d['camera'] (mis a jour a chaque image). Archipel : cadre fixe centre sur la
    boite de tout ce qui est dessine, 6 % de marge de chaque cote, echelle constante."""
    if nom == 'zoom':
        cx, cz = d['camera']
        vh = M.VIEW_H
    else:
        x0, x1, z0, z1 = etendue_dessinee(d)
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        vh = max(z1 - z0, (x1 - x0) * M.H / M.W) / (1 - 2 * MARGE)
    s = M.H * M.S / vh

    def P(x, z):
        return (M.W * M.S / 2 + (x - cx) * s, M.H * M.S / 2 - (z - cz) * s)
    return cx, cz, vh, s, P


C.cadre = cadre_v2


class FilmV2(P1.FilmPartie):
    def __init__(self, d, style, vue, dossier_icones):
        d['camera'] = tuple(d['route'][0][1:])                         # depart ; mis a jour a chaque image en vue zoom
        super().__init__(d, style, vue, dossier_icones)

    def camera(self, t):
        """Centre du cadre zoom : position du porte-avions, moyenne glissante de +/- LISSAGE_S secondes."""
        pts = [self.suivi[self.car].pos(t + k) for k in range(-LISSAGE_S, LISSAGE_S + 1)]
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    def image(self, t):
        if self.vue == 'zoom':                                         # le fond (quadrillage, iles) est redessine autour de la camera
            self.d['camera'] = self.camera(t)
            img, dr, self.P, _, st, _ = C.fond(self.d, self.style, self.vue)
            C.echelle_horloge(dr, st, C.VUES[self.vue], self.s, None, True)
            self.bg = img
        return super().image(t)


def controle(d):
    x0, x1, z0, z1 = etendue_dessinee(d)
    cx, cz, vh, s, P = cadre_v2(d, 'archipel')
    px = lambda x, z: tuple(v / M.S for v in P(x, z))
    gauche, haut = px(x0, z1)
    droite, bas = px(x1, z0)
    print('archipel : boite x %.0f..%.0f z %.0f..%.0f ; cadre %.0f x %.0f m ; marges en px : gauche %.0f droite %.0f haut %.0f bas %.0f (image 1280 x 720)' % (
        x0, x1, z0, z1, vh * M.W / M.H, vh, gauche, M.W - droite, haut, M.H - bas))
    film = FilmV2(d, 'M3', 'zoom', '../mac/carte_timelapse/icones')
    ecart, dedans = 0.0, None
    cx0, cz0, vh0, s0, _ = cadre_v2(d, 'zoom')
    for k in range(int((d['t_fin'] - d['t_debut']) * 2) + 1):
        t = d['t_debut'] + k / 2
        cam = film.camera(t)
        c = film.suivi[film.car].pos(t)
        ecart = max(ecart, math.hypot(c[0] - cam[0], c[1] - cam[1]) * s0 / M.S)
    print('zoom : ecart max entre le porte-avions et le centre du cadre : %.1f px' % ecart)
    for w, tk, it in d['V']:
        cam = film.camera(w)
        if 10 in it:
            ok = abs(it[10][2] - cam[0]) <= vh0 * M.W / M.H / 2 and abs(it[10][3] - cam[1]) <= vh0 / 2
            if ok != dedans:
                print('   %s : avion 10 %s le cadre zoom' % (cc2map.hms(w), 'ENTRE dans' if ok else 'SORT de'))
                dedans = ok


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    d = C.preparer(sys.argv[1])
    icones = sys.argv[2]
    if sys.argv[3] == '--controle':
        controle(d)
        return
    if sys.argv[3] == '--png':
        film = FilmV2(d, sys.argv[4], sys.argv[5], icones)
        film.image(sum(int(v) * m for v, m in zip(sys.argv[6].split(':'), (3600, 60, 1)))).save(sys.argv[7])
        print('ecrit :', sys.argv[7])
        return
    sortie = sys.argv[3]
    if os.path.exists(sortie) and os.listdir(sortie):
        raise SystemExit("REFUS : %s existe deja et n'est pas vide" % sortie)
    os.makedirs(sortie, exist_ok=True)
    VC.FACTEUR = FACTEUR
    for style, vue in P1.VUES:
        VC.encoder(FilmV2(d, style, vue, icones), os.path.join(sortie, 'carte_partie_30-10_%s_%s_v2.mp4' % (style, vue)))


if __name__ == '__main__':
    main()
