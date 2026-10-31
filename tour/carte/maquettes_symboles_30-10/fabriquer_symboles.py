"""Images fixes (PNG 1280x720) « zoom » avec de petits SYMBOLES dessines ici a la place des points : M3 « ocean » et M5 « encre ».
Meme donnee et memes couleurs d'equipe que les images et videos « zoom » deja livrees (essai A du 29/10 : equipe 1 bleu clair, equipe 0 rouge,
equipe 2 jaune). Les symboles sont des polygones dessines a la main avec Pillow, volontairement simplifies et differents de ceux du jeu : AUCUNE image,
police ni fichier du jeu n'est lu ni decoupe. Orientation = colonne « cap » des lignes V du journal. Liseré de lisibilite autour de chaque symbole.

Symboles : porte-avions (coque effilee, ilot et piste), avion (fleche en V), unite terrestre (char : chenilles, tourelle ronde, canon),
navire / barge (coque a etrave pointue et cabine), cale seche (bassin en U). Taille 14 a 22 px.

Instant montre : 14:30:55 (l'avion 9 est en vol : tous les symboles se distinguent), traces dessinees jusque-la. Les memes images a la toute derniere
image (14:37:31) sont dans le sous-dossier derniere_image/ : l'avion 9 a alors disparu des donnees (il n'y a plus de symbole d'avion).

Usage : python -I fabriquer_symboles.py <journal essai A copie> <dossier de sortie NEUF>
"""
import bisect
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc2map
import fabriquer_cartes_couleurs as C
import fabriquer_videos_couleurs as VC
from PIL import Image, ImageChops, ImageDraw, ImageFilter

S = C.S
SS = 8                                   # sur-echantillonnage du dessin d'un symbole
AIR = (8, 10, 12, 14)
NAVIRES = (16, 57, 77, 79)
CALE = 64
TAILLE = {'porte-avions': 22, 'avion': 18, 'char': 15, 'navire': 16, 'cale': 18}        # px, dimension la plus grande
LISERE = {'M3': (240, 248, 255), 'M5': (20, 20, 20)}                                      # contour de lisibilite
DETAIL = {'M3': (10, 36, 66), 'M5': (20, 20, 20)}                                         # traits fins a l'interieur du symbole
T_IMAGE = '14:30:55'


def genre(defn):
    if defn == 0:
        return 'porte-avions'
    if defn in AIR:
        return 'avion'
    if defn in NAVIRES:
        return 'navire'
    if defn == CALE:
        return 'cale'
    return 'char'


def formes(kind):
    """(corps, creux, details) en coordonnees d'unite [-1, 1], proue vers le haut. Un detail est un polygone ou ('anneau', cx, cy, rayon, epaisseur)."""
    if kind == 'porte-avions':           # coque effilee, ilot a tribord, piste centrale
        corps = [[(0, -1.0), (0.30, -0.62), (0.36, -0.2), (0.36, 0.80), (0.26, 1.0), (-0.26, 1.0), (-0.36, 0.80), (-0.36, -0.2), (-0.30, -0.62)]]
        det = [[(0.12, -0.10), (0.36, -0.10), (0.36, 0.38), (0.12, 0.38)], [(-0.16, -0.55), (-0.09, -0.55), (-0.09, 0.85), (-0.16, 0.85)]]
        return corps, [], det
    if kind == 'avion':                  # fleche en V
        corps = [[(0, -1.0), (0.95, 0.85), (0, 0.38), (-0.95, 0.85)]]
        return corps, [], [[(-0.05, -0.55), (0.05, -0.55), (0.05, 0.25), (-0.05, 0.25)]]
    if kind == 'char':                   # coque, chenilles (traits), tourelle ronde (anneau), long canon
        corps = [[(-0.52, -0.45), (0.52, -0.45), (0.52, 0.90), (-0.52, 0.90)], [(-0.11, -1.0), (0.11, -1.0), (0.11, 0.0), (-0.11, 0.0)]]
        det = [[(-0.40, -0.40), (-0.33, -0.40), (-0.33, 0.85), (-0.40, 0.85)], [(0.33, -0.40), (0.40, -0.40), (0.40, 0.85), (0.33, 0.85)], ('anneau', 0, 0.22, 0.30, 0.10)]
        return corps, [], det
    if kind == 'navire':                 # coque a etrave pointue, cabine a l'arriere
        corps = [[(0, -1.0), (0.42, -0.45), (0.44, 0.74), (0.32, 1.0), (-0.32, 1.0), (-0.44, 0.74), (-0.42, -0.45)]]
        return corps, [], [[(-0.24, 0.22), (0.24, 0.22), (0.24, 0.72), (-0.24, 0.72)]]
    if kind == 'cale':                   # bassin en U, ouvert vers l'avant
        corps = [[(-0.85, -0.80), (0.85, -0.80), (0.85, 0.80), (-0.85, 0.80)]]
        creux = [[(-0.42, -0.84), (0.42, -0.84), (0.42, 0.34), (-0.42, 0.34)]]
        return corps, creux, []
    raise ValueError(kind)


_cache = {}


def symbole(kind, equipe_rgb, style, cap_deg):
    """Symbole RGBA (liseré compris), pivote de cap_deg degres dans le sens horaire, a l'echelle du canevas sur-echantillonne (S)."""
    cle = (kind, equipe_rgb, style, int(round(cap_deg / 3.0)) * 3)
    if cle in _cache:
        return _cache[cle]
    taille = TAILLE[kind]
    n = int(taille * SS * 1.7) | 1
    c, s = n / 2.0, taille * SS / 2.0

    def pts(poly):
        return [(c + x * s, c + y * s) for x, y in poly]

    corps, creux, det = formes(kind)
    body, detail = Image.new('L', (n, n), 0), Image.new('L', (n, n), 0)
    bd, dd = ImageDraw.Draw(body), ImageDraw.Draw(detail)
    for poly in corps:
        bd.polygon(pts(poly), fill=255)
    for poly in creux:
        bd.polygon(pts(poly), fill=0)
    for it in det:
        if it[0] == 'anneau':
            _, cx, cy, r, e = it
            dd.ellipse((c + (cx - r) * s, c + (cy - r) * s, c + (cx + r) * s, c + (cy + r) * s), outline=255, width=max(1, int(e * s)))
        else:
            dd.polygon(pts(it), fill=255)
    detail = ImageChops.multiply(detail, body)
    k = int(round(1.3 * SS))
    bord = body.filter(ImageFilter.MaxFilter(2 * k + 1))
    im = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    im.paste(Image.new('RGBA', (n, n), LISERE[style] + (255,)), (0, 0), bord)
    im.paste(Image.new('RGBA', (n, n), equipe_rgb + (255,)), (0, 0), body)
    im.paste(Image.new('RGBA', (n, n), DETAIL[style] + (255,)), (0, 0), detail)
    im = im.rotate(-cle[3], resample=Image.BICUBIC, expand=True)
    _cache[cle] = im.resize((max(1, int(round(im.width * S / SS))), max(1, int(round(im.height * S / SS)))), Image.LANCZOS)
    return _cache[cle]


def poser(img, sp, c):
    img.paste(sp, (int(round(c[0] - sp.width / 2)), int(round(c[1] - sp.height / 2))), sp)


class FilmSymboles(VC.Film):
    """Meme etat que les videos (positions interpolees, traces progressives), mais avec des symboles orientes au lieu de points."""

    def cap(self, uid, t):
        i = max(0, bisect.bisect_right(self.suivi[self.car].walls, t) - 1)
        v = self.V[i][2].get(uid)
        return v[4] if v else 0.0

    def defn(self, uid):
        for w, tk, it in self.V:
            if uid in it:
                return it[uid][0]

    def image(self, t):
        st, vp, P = self.st, self.vp, self.P
        img = self.bg.copy()
        dr = ImageDraw.Draw(img)
        pos = {i: sv.pos(t) for i, sv in self.suivi.items()}
        c = pos[self.car]
        for i in self.mobiles:                                         # traces des unites des autres equipes qui bougent
            pts = [P(x, z) for (w, x, z) in ((self.V[k][0],) + self.suivi[i].pts[k] for k in range(len(self.V)) if self.suivi[i].pts[k] and self.V[k][0] <= t)]
            if pos[i]:
                pts.append(P(*pos[i]))
            C.ligne(dr, pts, st['rte_col'][self.team[i]], None, vp['rte_w'])
        C.ligne(dr, [P(x, z) for w, x, z in self.d['route'] if w <= t] + ([P(*c)] if c else []), C.EQUIPE[1], st['casing'], vp['car_w'])
        a = pos.get(VC.AVION)
        for run in self.vols:
            if run[0][0] > t:
                continue
            pts = [P(p[1], p[2]) for p in run if p[0] <= t]
            if a and t <= run[-1][0]:
                pts.append(P(*a))
            C.ligne(dr, pts, C.EQUIPE[1], st['casing'], vp['vol_w'])
        style = 'M3' if st['bg'] != (255, 255, 255) else 'M5'
        for i, p in pos.items():                                       # symboles : unites, puis avion 9, puis porte-avions par-dessus
            if p is None or i in (self.car, VC.AVION):
                continue
            if self.team[i] == 1 and c and math.hypot(p[0] - c[0], p[1] - c[1]) < C.A_BORD_M:
                continue                                               # sur le pont : le porte-avions suffit
            poser(img, symbole(genre(self.defn(i)), C.EQUIPE[self.team[i]], style, self.cap(i, t)), P(*p))
        if a:
            poser(img, symbole('avion', C.EQUIPE[1], style, self.cap(VC.AVION, t)), P(*a))
        if c:
            poser(img, symbole('porte-avions', C.EQUIPE[1], style, self.cap(self.car, t)), P(*c))
        C.echelle_horloge(dr, st, vp, self.s, t, False)
        return img.resize((C.W, C.H), Image.LANCZOS)


def hms_s(h):
    a, b, c = h.split(':')
    return int(a) * 3600 + int(b) * 60 + int(c)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    sortie = sys.argv[2]
    if os.path.exists(sortie) and os.listdir(sortie):
        raise SystemExit("REFUS : %s existe deja et n'est pas vide" % sortie)
    os.makedirs(os.path.join(sortie, 'derniere_image'), exist_ok=True)
    d = C.preparer(sys.argv[1])
    for style in ('M3', 'M5'):
        film = FilmSymboles(d, style, 'zoom')
        film.image(hms_s(T_IMAGE)).save(os.path.join(sortie, '%s_zoom_symboles.png' % style))
        film.image(d['t_fin']).save(os.path.join(sortie, 'derniere_image', '%s_zoom_symboles_fin.png' % style))
        print('ecrit :', style, '(', T_IMAGE, 'et', cc2map.hms(d['t_fin']), ')')


if __name__ == '__main__':
    main()
