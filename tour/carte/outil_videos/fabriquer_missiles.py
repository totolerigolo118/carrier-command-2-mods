"""Missiles pour les videos de carte : suivi des missiles d'apres les lignes CC2MAP|M du journal, et dessin (trainee courte et vive + petite pointe, couleur
d'equipe : equipe 1 bleu clair, equipe 0 rouge, equipe 2 jaune) ; quand un missile n'est plus dans les donnees, une breve marque d'impact (cercle qui s'estompe
sur ~1 s de video). Utilise par fabriquer_videos_partie_v2.py (option --sans-missiles pour les desactiver).

Donnees : une ligne M = un instantane des missiles en vol, « id,def,equipe,x,z », toutes les ~0,2 a 0,5 s tant qu'il y en a ; une ligne M vide (1/1|) marque la fin
des missiles en vol. ATTENTION : cet « id » n'est PAS un identifiant de missile : l'enregistreur (cc2map_enregistreur*.lua) ecrit l'INDEX du missile dans la liste
du jeu (la methode get_id n'existe pas sur cet objet), et cet index change des qu'un autre missile disparait. Les missiles sont donc suivis par position : un
echantillon est rattache au missile de meme (def, equipe) dont la position attendue (derniere position + vitesse) est la plus proche, a moins de 250 m.

Rien n'est invente : la trainee relie de vrais echantillons ; la pointe est a la position interpolee entre deux echantillons ; avant le premier et apres le dernier
echantillon d'un missile, on ne dessine plus le missile. Quand un missile n'est plus revu pendant plus de 2 s, ou qu'une ligne M vide arrive, on dessine la marque
d'impact a sa derniere position : c'est une INFERENCE (« disparu des donnees »), pas la preuve qu'il a touche quelque chose (il a pu etre intercepte, tomber a l'eau,
arriver en fin de vie, ou sortir de ce que le jeu liste). Au tout dernier instantane du journal, aucune marque (on ne sait pas s'il a disparu).
"""
import bisect
import math

from PIL import Image, ImageDraw

import fabriquer_cartes_couleurs as C
import fabriquer_videos_couleurs as VC

TRAINEE_S = 2.0              # duree de la trainee (secondes d'horloge du journal)
TRAINEE_MAX_S = 6.0          # on remonte plus loin si la trainee reste plus courte que `mini` (vue large, missile lent)
TROU_MAX_S = 2.0             # un missile non revu pendant plus de 2 s a disparu des donnees (le journal a des trous de 1,1 s entre deux rafales d'echantillons)
PORTEE_M = 250.0             # ecart maximal (m) entre la position attendue et l'echantillon suivant du meme missile
IMPACT_VIDEO_S = 1.0         # duree de la marque d'impact (secondes de VIDEO : = IMPACT_VIDEO_S x facteur d'acceleration en secondes de journal)
CELLULE_PX = 14.0            # salve dense : une seule marque d'impact par case de 14 px (et par equipe), la plus recente
TAILLES = {                  # px a l'ecran : pointe (longueur, largeur), trait de la trainee en tete, longueur minimale de la trainee, rayon de la marque (debut, fin)
    'zoom': dict(tete=11.0, large=6.4, trait=2.2, mini=26.0, r0=6.0, r1=16.0),
    'archipel': dict(tete=8.0, large=4.6, trait=1.7, mini=16.0, r0=4.0, r1=10.0),
}


class Piste:
    """Un missile suivi : suite d'echantillons (heure du journal, x, z), de meme (def, equipe)."""

    def __init__(self, df, equipe, w, x, z, idx):
        self.df, self.equipe = df, equipe
        self.pts = [(w, x, z)]
        self.walls = [w]
        self.idx = {idx}                    # index(s) de liste vus pour ce missile (pas un identifiant : voir l'en-tete)
        self.v = (0.0, 0.0)                 # vitesse (m/s d'horloge) entre les deux derniers echantillons
        self.fin = False                    # vrai si l'on a constate qu'il n'est plus dans les donnees

    def ajouter(self, w, x, z, idx):
        w0, x0, z0 = self.pts[-1]
        if w - w0 >= 0.05:
            self.v = ((x - x0) / (w - w0), (z - z0) / (w - w0))
        self.pts.append((w, x, z))
        self.walls.append(w)
        self.idx.add(idx)

    def attendu(self, w):
        w0, x0, z0 = self.pts[-1]
        return x0 + self.v[0] * (w - w0), z0 + self.v[1] * (w - w0)

    def pos(self, t):
        """Position interpolee a l'heure t ; None avant le premier echantillon ou apres le dernier."""
        if t < self.walls[0] or t > self.walls[-1]:
            return None
        i = min(max(0, bisect.bisect_right(self.walls, t) - 1), len(self.pts) - 1)
        w0, x0, z0 = self.pts[i]
        if i + 1 >= len(self.pts):
            return (x0, z0)
        w1, x1, z1 = self.pts[i + 1]
        k = 0.0 if w1 <= w0 else (t - w0) / (w1 - w0)
        return (x0 + (x1 - x0) * k, z0 + (z1 - z0) * k)


def pister(snaps):
    """Instantanes M [(heure, tick, {index: (def, equipe, x, z)})] -> liste de Piste. Un instantane vide ferme tous les missiles suivis."""
    pistes, actives = [], []
    for w, tick, items in snaps:
        for p in list(actives):
            if not items or w - p.walls[-1] > TROU_MAX_S:
                p.fin = True
                actives.remove(p)
        lst = list(items.items())
        cands = []
        for ii, (idx, (df, equipe, x, z)) in enumerate(lst):
            for pi, p in enumerate(actives):
                if (p.df, p.equipe) == (df, equipe):
                    ex, ez = p.attendu(w)
                    d = math.hypot(x - ex, z - ez)
                    if d <= PORTEE_M:
                        cands.append((d, 0 if idx in p.idx else 1, ii, pi))
        cands.sort()
        pris_i, pris_p = set(), set()
        for d, _, ii, pi in cands:
            if ii in pris_i or pi in pris_p:
                continue
            pris_i.add(ii)
            pris_p.add(pi)
            idx, (df, equipe, x, z) = lst[ii]
            actives[pi].ajouter(w, x, z, idx)
        for ii, (idx, (df, equipe, x, z)) in enumerate(lst):
            if ii not in pris_i:
                p = Piste(df, equipe, w, x, z, idx)
                pistes.append(p)
                actives.append(p)
    return pistes


def marque(img, c, rayon, epaisseur, couleur, alpha, plein=False):
    """Cercle (ou disque) de couleur `couleur`, transparence `alpha`, centre c, rayon et epaisseur en pixels du canevas sur-echantillonne."""
    R = int(math.ceil(rayon + epaisseur)) + 2
    x0, y0 = int(round(c[0])) - R, int(round(c[1])) - R
    m = Image.new('L', (2 * R + 1, 2 * R + 1), 0)
    ImageDraw.Draw(m).ellipse((R - rayon, R - rayon, R + rayon, R + rayon), fill=int(255 * alpha) if plein else None, outline=int(255 * alpha), width=max(1, int(round(epaisseur))))
    img.paste(couleur, (x0, y0, x0 + 2 * R + 1, y0 + 2 * R + 1), m)


class Missiles:
    def __init__(self, snaps):
        self.pistes = pister(snaps)

    def resume(self):
        """[(equipe, def, debut, fin, nb d'echantillons, index de liste vus, disparu des donnees)] pour les comptes rendus."""
        return [(p.equipe, p.df, p.walls[0], p.walls[-1], len(p.pts), sorted(p.idx), p.fin) for p in self.pistes]

    def dessiner(self, film, img, dr, P, t):
        """Dessine, a l'heure t, les missiles en vol (trainee + pointe) et les marques d'impact en cours, sur le canevas sur-echantillonne `img`."""
        st, S = film.st, C.S
        tl = TAILLES[film.vue]
        duree = IMPACT_VIDEO_S * VC.FACTEUR
        marques = {}
        for p in self.pistes:                                              # marques d'impact (en dessous des missiles)
            fin = p.walls[-1]
            if p.fin and fin < t <= fin + duree:
                k = (t - fin) / duree
                c = P(p.pts[-1][1], p.pts[-1][2])
                cle = (int(c[0] // (CELLULE_PX * S)), int(c[1] // (CELLULE_PX * S)), p.equipe)
                if cle not in marques or k < marques[cle][0]:              # salve dense : une seule marque (la plus recente) par case de 14 px et par equipe
                    marques[cle] = (k, c, p.equipe)
        for k, c, equipe in sorted(marques.values(), key=lambda m: -m[0]):
            r = (tl['r0'] + (tl['r1'] - tl['r0']) * k) * S
            a = (1.0 - k) ** 0.8
            marque(img, c, r, 1.8 * S, st['outline'], a)                   # anneau clair (M3) ou noir (M5), qui grandit et s'estompe
            marque(img, c, 2.6 * S, 0, C.EQUIPE[equipe], a, plein=True)    # coeur a la couleur de l'equipe
        for p in self.pistes:
            if p.walls[0] <= t <= p.walls[-1]:
                self.vol(p, st, tl, dr, P, t)

    def trainee(self, p, t, P, mini):
        """Points (pixels) de la trainee : de t - 2 s (plus loin si trop courte) a la position de la pointe, par de vrais echantillons."""
        T = TRAINEE_S
        while True:
            t0 = max(p.walls[0], t - T)
            pts = [P(*p.pos(t0))] + [P(x, z) for w, x, z in p.pts if t0 < w < t] + [P(*p.pos(t))]
            longueur = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
            if longueur >= mini * C.S or t0 <= p.walls[0] or T >= TRAINEE_MAX_S:
                return pts
            T += 0.5

    @staticmethod
    def direction(p, t, P):
        """Vecteur unitaire (pixels) du deplacement au moment t, d'apres le segment d'echantillons qui contient t ; None si le missile n'a qu'un echantillon."""
        i = min(max(0, bisect.bisect_right(p.walls, t) - 1), len(p.pts) - 1)
        a, b = (i, i + 1) if i + 1 < len(p.pts) else (i - 1, i)
        if a < 0:
            return None
        pa, pb = P(p.pts[a][1], p.pts[a][2]), P(p.pts[b][1], p.pts[b][2])
        n = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
        return None if n < 1e-6 else ((pb[0] - pa[0]) / n, (pb[1] - pa[1]) / n)

    def vol(self, p, st, tl, dr, P, t):
        S = C.S
        pts = self.trainee(p, t, P, tl['mini'])
        n = len(pts) - 1
        for pas in (0, 1):                                                 # d'abord le contour sombre de tous les segments, puis la couleur
            for k in range(n):
                w = tl['trait'] * (0.35 + 0.65 * (k + 1) / n) * S
                if pas == 0:
                    w += 1.0 * S
                    col = st['casing']
                else:
                    col = st['rte_col'][p.equipe]
                dr.line([pts[k], pts[k + 1]], fill=col, width=max(1, int(round(w))))
                dr.ellipse((pts[k + 1][0] - w / 2, pts[k + 1][1] - w / 2, pts[k + 1][0] + w / 2, pts[k + 1][1] + w / 2), fill=col)
        hp = pts[-1]
        u = self.direction(p, t, P)
        if u is None:                                                      # un seul echantillon : simple point
            r = tl['large'] / 2 * S
            dr.ellipse((hp[0] - r - S, hp[1] - r - S, hp[0] + r + S, hp[1] + r + S), fill=st['outline'])
            dr.ellipse((hp[0] - r, hp[1] - r, hp[0] + r, hp[1] + r), fill=C.EQUIPE[p.equipe])
            return
        nx, ny = -u[1], u[0]

        def tri(L, W):
            return [(hp[0] + u[0] * L * 0.6, hp[1] + u[1] * L * 0.6), (hp[0] - u[0] * L * 0.4 + nx * W / 2, hp[1] - u[1] * L * 0.4 + ny * W / 2),
                    (hp[0] - u[0] * L * 0.4 - nx * W / 2, hp[1] - u[1] * L * 0.4 - ny * W / 2)]
        dr.polygon(tri((tl['tete'] + 1.8) * S, (tl['large'] + 1.8) * S), fill=st['outline'])
        dr.polygon(tri(tl['tete'] * S, tl['large'] * S), fill=C.EQUIPE[p.equipe])
