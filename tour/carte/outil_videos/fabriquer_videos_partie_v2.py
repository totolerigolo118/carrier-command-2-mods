"""Quatre videos de LA PARTIE du 30/10 (08:44:31 -> 08:55:29), version 2 : meme rendu que fabriquer_videos_partie.py (importe ici, inchange), mais
cadrage mieux centre. Les videos v1 n'etaient pas centrees :
 - ARCHIPEL : le cadre etait la boite des iles + positions de l'equipe 1 avec 1 % de marge (et un rayon d'ile approximatif) : le porte-avions touchait presque
   le bord bas, l'avion 10 le bord haut. v2 : cadre FIXE, centre sur la boite englobante de TOUT ce qui est dessine (contour exact des iles, toutes les positions
   de toutes les unites : route du porte-avions, trace de l'avion 10 jusqu'au bout), avec 6 % de marge de chaque cote ; echelle constante.
 - ZOOM : le cadre de 20 km etait fixe, centre sur la route du porte-avions, alors que le porte-avions bouge (~3 km) et que la trace de l'avion 10 monte hors
   du cadre. v2 : le cadre de 20 km SUIT le porte-avions : centre sur sa position lissee (moyenne glissante de +/- 20 s d'horloge du journal) a chaque image ;
   le fond (quadrillage, iles) defile en consequence, l'echelle reste fixe.
Reste inchange : pictos du jeu teintes par equipe, iles colorees par proprietaire, avions 9 et 10 par-dessus le porte-avions, echelle, horloge, 1 s de
pause finale, H.264 yuv420p 1280x720 30 i/s sans son. Aucun fichier du dossier du jeu n'est lu (pictos : carte_timelapse/icones, Mac).

MISSILES (ajoutes pour les parties futures ; fabriquer_missiles.py) : les lignes CC2MAP|M du journal sont dessinees (trainee courte + pointe, couleur d'equipe, marque
d'impact breve quand un missile disparait des donnees). Actif par defaut ; --sans-missiles redonne exactement le rendu d'avant (meme octets).
Vitesse : par defaut 1 s de video = (duree de la partie / 60) s de journal, arrondi, pour ~60 s de video ; --facteur N pour la forcer (la partie du 30/10 donne 11).

SUIVI LARGE (option --suivi-large : 2 videos de plus, M3 et M5, vue « large ») : quand des avions s'eloignent a 50-70 km, le zoom de 20 km se vide. Le suivi large garde
un cadre centre sur la boite du porte-avions et des unites de l'equipe 1 qui s'en eloignent, avec 12 % de marge, au moins 20 km de haut, boite et echelle lissees
(+/- 30 s) : on voit les details au debut, puis le cadre s'elargit en douceur quand les avions partent ; le pas du quadrillage et l'echelle s'adaptent.

Usage : python -I fabriquer_videos_partie_v2.py <extrait CC2MAP de la partie> <dossier icones> <dossier de sortie NEUF> [--nom PREFIXE] [--facteur N] [--sans-missiles] [--suivi-large]
        python -I fabriquer_videos_partie_v2.py <extrait> <dossier icones> --png M3|M5 zoom|archipel|large HH:MM:SS fichier.png [--facteur N] [--sans-missiles]
        python -I fabriquer_videos_partie_v2.py <extrait> <dossier icones> --controle      (marges de l'archipel, ecart porte-avions / centre, sortie de l'avion 10)
        python -I fabriquer_videos_partie_v2.py <extrait> <dossier icones> --missiles      (liste des missiles suivis, sans rien dessiner)
(<extrait CC2MAP> : fichier fait par extraire_partie.py, ou journal ne contenant qu'une seule partie.)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc2map
import fabriquer_cartes_couleurs as C
import fabriquer_maquettes as M
import fabriquer_missiles as MI
import fabriquer_videos_couleurs as VC
import fabriquer_videos_partie as P1
import fabriquer_videos_pictos as FP

MARGE = 0.06                    # part du cadre laissee libre de chaque cote (archipel)
LISSAGE_S = 20                  # demi-fenetre de la moyenne glissante de la camera (s d'horloge du journal)
DUREE_VIDEO_S = 60              # duree visee des videos (s) pour le facteur par defaut
GRAND_MARGE = 0.12              # suivi large : part du cadre laissee libre de chaque cote
GRAND_LISSAGE_S = 30            # suivi large : demi-fenetre du lissage de la boite (s d'horloge du journal)
PAS_GRILLE_M = (2000, 5000, 10000, 20000, 50000)

# Vue « large » (option --suivi-large) : cadre centre sur la boite du porte-avions et des unites de l'equipe 1 qui s'en eloignent, echelle ADAPTATIVE lissee (au moins
# 20 km de haut, comme le zoom) ; le pas du quadrillage et la longueur de l'echelle sont recalcules a chaque image. Tailles de pictos et de missiles entre zoom et archipel.
C.VUES['large'] = dict(car_w=2.4, vol_w=2.0, rte_w=1.0, r_car=6.0, r_pt=2.2, r_vol=3.4, grille=5000, echelle=5000)
VC.VUES_VIDEO['large'] = dict(C.VUES['large'], car_w=2.6, vol_w=2.2, rte_w=1.2, r_car=7.5, r_pt=3.2, r_vol=4.0)
FP.TAILLE['large'] = {'carrier': 22, 'albatros': 15, 'manta': 16, 'razorbill': 14, 'petrel': 16, 'seal': 11, 'walrus': 11, 'bear': 12, 'mule': 11, 'needlefish': 14,
                      'lifeboat16': 11, 'carrier16': 14, 'turret': 11}
MI.TAILLES['large'] = dict(tete=9.0, large=5.2, trait=1.9, mini=20.0, r0=5.0, r1=12.0)


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
    if nom in ('zoom', 'large'):                                       # vue « large » : hauteur d['vue_h'] (adaptative), sinon 20 km
        cx, cz = d['camera']
        vh = d['vue_h'] if nom == 'large' else M.VIEW_H
    else:
        x0, x1, z0, z1 = etendue_dessinee(d)
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        vh = max(z1 - z0, (x1 - x0) * M.H / M.W) / (1 - 2 * MARGE)
    s = M.H * M.S / vh

    def P(x, z):
        return (M.W * M.S / 2 + (x - cx) * s, M.H * M.S / 2 - (z - cz) * s)
    return cx, cz, vh, s, P


C.cadre = cadre_v2


def preparer(chemin):
    d = C.preparer(chemin)
    d['M'] = cc2map.parse(chemin)['M']                                 # instantanes des missiles (lignes CC2MAP|M)
    return d


def facteur_auto(d):
    return max(1, int(round((d['t_fin'] - d['t_debut']) / DUREE_VIDEO_S)))


class FilmV2(P1.FilmPartie):
    def __init__(self, d, style, vue, dossier_icones, missiles=True):
        d['camera'] = tuple(d['route'][0][1:])                         # depart ; mis a jour a chaque image en vue zoom ou large
        d['vue_h'] = M.VIEW_H
        super().__init__(d, style, vue, dossier_icones)
        self.missiles = MI.Missiles(d['M']) if missiles else None
        self.grand = self.boites_large() if vue == 'large' else None

    def dessus(self, img, dr, P, t):
        if self.missiles:
            self.missiles.dessiner(self, img, dr, P, t)

    def camera(self, t):
        """Centre du cadre zoom : position du porte-avions, moyenne glissante de +/- LISSAGE_S secondes."""
        pts = [self.suivi[self.car].pos(t + k) for k in range(-LISSAGE_S, LISSAGE_S + 1)]
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    def boites_large(self):
        """Suivi large : boite (x0, x1, z0, z1) du porte-avions et des unites de l'equipe 1 a plus de 80 m de lui, a chaque seconde d'horloge du journal, lissee
        par une moyenne glissante de +/- GRAND_LISSAGE_S s (la camera et l'echelle varient doucement, meme quand un avion se pose ou disparait)."""
        t0 = self.d['t_debut']
        n = int(self.d['t_fin'] - t0) + 2
        equipe1 = [i for i, tm in self.team.items() if tm == 1 and i != self.car]
        brut = []
        for k in range(n):
            c = self.suivi[self.car].pos(t0 + k)
            pts = [c] + [p for p in (self.suivi[i].pos(t0 + k) for i in equipe1) if p and math.hypot(p[0] - c[0], p[1] - c[1]) >= C.A_BORD_M]
            xs, zs = [p[0] for p in pts], [p[1] for p in pts]
            brut.append((min(xs), max(xs), min(zs), max(zs)))
        lisse = []
        for k in range(n):
            seg = brut[max(0, k - GRAND_LISSAGE_S):k + GRAND_LISSAGE_S + 1]
            lisse.append(tuple(sum(b[j] for b in seg) / len(seg) for j in range(4)))
        return lisse

    def camera_large(self, t):
        """(centre, hauteur du cadre en m) du suivi large a l'heure t : boite lissee + 12 % de marge de chaque cote, jamais moins de 20 km de haut."""
        k = min(max(t - self.d['t_debut'], 0.0), len(self.grand) - 1.001)
        i, f = int(k), k - int(k)
        x0, x1, z0, z1 = (self.grand[i][j] + (self.grand[i + 1][j] - self.grand[i][j]) * f for j in range(4))
        vh = max(M.VIEW_H, max(z1 - z0, (x1 - x0) * M.H / M.W) / (1 - 2 * GRAND_MARGE))
        return ((x0 + x1) / 2, (z0 + z1) / 2), vh

    def image(self, t):
        if self.vue in ('zoom', 'large'):                              # le fond (quadrillage, iles) est redessine autour de la camera
            if self.vue == 'zoom':
                self.d['camera'] = self.camera(t)
            else:
                self.d['camera'], self.d['vue_h'] = self.camera_large(t)
                C.VUES['large']['grille'] = C.VUES['large']['echelle'] = next((p for p in PAS_GRILLE_M if p >= self.d['vue_h'] / 7), PAS_GRILLE_M[-1])
            img, dr, self.P, s, st, _ = C.fond(self.d, self.style, self.vue)
            C.echelle_horloge(dr, st, C.VUES[self.vue], s, None, True)
            self.bg = img
        return super().image(t)


def controle(d, icones):
    x0, x1, z0, z1 = etendue_dessinee(d)
    cx, cz, vh, s, P = cadre_v2(d, 'archipel')
    px = lambda x, z: tuple(v / M.S for v in P(x, z))
    gauche, haut = px(x0, z1)
    droite, bas = px(x1, z0)
    print('archipel : boite x %.0f..%.0f z %.0f..%.0f ; cadre %.0f x %.0f m ; marges en px : gauche %.0f droite %.0f haut %.0f bas %.0f (image 1280 x 720)' % (
        x0, x1, z0, z1, vh * M.W / M.H, vh, gauche, M.W - droite, haut, M.H - bas))
    film = FilmV2(d, 'M3', 'zoom', icones, missiles=False)
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


def options(argv):
    """Separe les options facultatives (--sans-missiles, --nom X, --facteur N) des arguments."""
    opt, args, k = dict(missiles=True, nom='carte_partie', facteur=None, large=False), [], 0
    while k < len(argv):
        if argv[k] == '--sans-missiles':
            opt['missiles'] = False
        elif argv[k] == '--suivi-large':
            opt['large'] = True
        elif argv[k] in ('--nom', '--facteur') and k + 1 < len(argv):
            opt[argv[k][2:]] = int(argv[k + 1]) if argv[k] == '--facteur' else argv[k + 1]
            k += 1
        else:
            args.append(argv[k])
        k += 1
    return opt, args


def main():
    opt, args = options(sys.argv[1:])
    if len(args) < 3:
        raise SystemExit(__doc__)
    d = preparer(args[0])
    icones = args[1]
    VC.FACTEUR = opt['facteur'] or facteur_auto(d)                    # encoder() et la duree des marques d'impact lisent ce reglage
    if args[2] == '--controle':
        controle(d, icones)
        return
    if args[2] == '--missiles':
        for eq, df, w0, w1, n, idx, fin in MI.Missiles(d['M']).resume():
            print('equipe %d def %d : %s -> %s (%.1f s, %d echantillons) index de liste %s ; %s' % (
                eq, df, cc2map.hms(w0), cc2map.hms(w1), w1 - w0, n, idx, 'disparu des donnees' if fin else 'encore present au dernier instantane'))
        return
    if args[2] == '--png':
        film = FilmV2(d, args[3], args[4], icones, opt['missiles'])
        film.image(sum(int(v) * m for v, m in zip(args[5].split(':'), (3600, 60, 1)))).save(args[6])
        print('ecrit :', args[6])
        return
    sortie = args[2]
    if os.path.exists(sortie) and os.listdir(sortie):
        raise SystemExit("REFUS : %s existe deja et n'est pas vide" % sortie)
    os.makedirs(sortie, exist_ok=True)
    print('facteur', VC.FACTEUR, '; missiles', 'actives' if opt['missiles'] else 'desactives', '; suivi large', 'oui' if opt['large'] else 'non')
    for style, vue in list(P1.VUES) + ([('M3', 'large'), ('M5', 'large')] if opt['large'] else []):
        VC.encoder(FilmV2(d, style, vue, icones, opt['missiles']), os.path.join(sortie, '%s_%s_%s.mp4' % (opt['nom'], style, vue)))


if __name__ == '__main__':
    main()
