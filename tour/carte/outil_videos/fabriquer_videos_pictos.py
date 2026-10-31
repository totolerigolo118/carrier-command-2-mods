"""Quatre videos (styles M3 « ocean » et M5 « encre », vues « zoom » et « archipel ») de l'essai A du 29/10, comme les videos en couleurs d'equipe mais avec
les PICTOS DU JEU a la place des points : porte-avions, avions (albatros, manta, razorbill, petrel), unites terrestres (seal, walrus, bear, mule),
barge / canot, cale seche, tourelle ; choisis d'apres le type `def` de chaque unite, teintes de la couleur de leur equipe, orientes selon le cap du journal.
Equipe 1 = bleu clair, equipe 0 (IA) = rouge, equipe 2 = jaune. Memes iles, traces, echelle (5 km / 10 km) et petite horloge que les videos en couleurs.

Pictos : ceux deja utilises dans les premieres videos A et B, lus dans le dossier icones/ de carte_timelapse (Mac, branche mac-carte-enregistreur).
AUCUN fichier du dossier du jeu n'est lu. Ces videos contiennent des pictos du jeu : le partage dependra de l'autorisation du developpeur (voir NE_PAS_PARTAGER.txt).
Aucun nom ni identifiant de joueur. Fait maison : Pillow pour les images, ffmpeg (deja installe, local) pour le H.264.

Usage : python -I fabriquer_videos_pictos.py <journal essai A copie> <dossier icones> <dossier de sortie NEUF>
        python -I fabriquer_videos_pictos.py <journal> <dossier icones> --png M3|M5 zoom|archipel HH:MM:SS fichier.png      (une seule image, pour regarder)
"""
import bisect
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fabriquer_cartes_couleurs as C
import fabriquer_videos_couleurs as VC
from PIL import Image, ImageDraw, ImageFilter

S = C.S
ICON = {0: 'carrier', 8: 'albatros', 10: 'manta', 12: 'razorbill', 14: 'petrel', 2: 'seal', 4: 'walrus', 6: 'bear', 88: 'mule', 77: 'needlefish', 79: 'needlefish',
        16: 'lifeboat16', 57: 'lifeboat16', 59: 'turret', 64: 'carrier16'}
TAILLE = {   # px, dimension la plus grande ; en archipel un peu plus petits, le porte-avions reste le plus gros
    'zoom': {'carrier': 24, 'albatros': 20, 'manta': 22, 'razorbill': 18, 'petrel': 22, 'seal': 14, 'walrus': 15, 'bear': 16, 'mule': 14, 'needlefish': 18,
             'lifeboat16': 14, 'carrier16': 18, 'turret': 14},
    'archipel': {'carrier': 18, 'albatros': 12, 'manta': 13, 'razorbill': 11, 'petrel': 13, 'seal': 9, 'walrus': 9, 'bear': 10, 'mule': 9, 'needlefish': 11,
                 'lifeboat16': 9, 'carrier16': 11, 'turret': 9},
}
LISERE = {'M3': (240, 248, 255), 'M5': (20, 20, 20)}      # contour de lisibilite
DEFAUT = 'seal'                                           # unite terrestre inconnue


class FilmPictos(VC.Film):
    def __init__(self, d, style, vue, dossier_icones):
        super().__init__(d, style, vue)
        self.style, self.vue = style, vue
        self.icones = {n: Image.open(os.path.join(dossier_icones, n + '.png')).convert('RGBA') for n in set(ICON.values())}
        self.walls = [w for w, t, it in self.V]
        self.defn = {}
        self.caps = {}
        for k, (w, t, it) in enumerate(self.V):
            for i, v in it.items():
                self.defn.setdefault(i, v[0])
        for i in self.defn:
            self.caps[i] = [it[i][4] if i in it else None for w, t, it in self.V]
        self._cache = {}

    def cap(self, uid, t):
        """Cap interpole entre les deux positions voisines du journal (chemin le plus court)."""
        i = max(0, bisect.bisect_right(self.walls, t) - 1)
        a = self.caps[uid][i]
        if a is None:
            return 0.0
        if i + 1 < len(self.walls) and self.caps[uid][i + 1] is not None:
            b = self.caps[uid][i + 1]
            w0, w1 = self.walls[i], self.walls[i + 1]
            k = 0.0 if w1 <= w0 else min(1.0, max(0.0, (t - w0) / (w1 - w0)))
            return (a + ((b - a + 180) % 360 - 180) * k) % 360
        return a

    def sprite(self, defn, equipe, angle):
        nom = ICON.get(defn, DEFAUT)
        cle = (nom, equipe, int(round(angle / 2.0)) * 2)
        if cle in self._cache:
            return self._cache[cle]
        base = self.icones[nom].rotate(180)                   # les pictos du jeu pointent vers le bas
        long_px = TAILLE[self.vue][nom] * S
        w, h = base.size
        f = long_px / max(w, h)
        taille = (max(1, int(round(w * f))), max(1, int(round(h * f))))
        alpha = base.getchannel('A').resize(taille, Image.BICUBIC)
        k = 1                                                 # liseré fin (~0,5 px) pour ne pas noyer la couleur des petits pictos
        bord = alpha.point(lambda v: 255 if v > 40 else 0).filter(ImageFilter.MaxFilter(2 * k + 1))
        marge = 2 * k + 2
        cadre = (taille[0] + 2 * marge, taille[1] + 2 * marge)
        im = Image.new('RGBA', cadre, (0, 0, 0, 0))
        im.paste(Image.new('RGBA', taille, LISERE[self.style] + (255,)), (marge, marge), bord)
        teinte = Image.new('RGBA', taille, C.EQUIPE[equipe] + (255,))
        im.paste(teinte, (marge, marge), alpha)
        im = im.rotate(-cle[2], resample=Image.BICUBIC, expand=True)
        self._cache[cle] = im
        return im

    @staticmethod
    def poser(img, sp, c):
        img.paste(sp, (int(round(c[0] - sp.width / 2)), int(round(c[1] - sp.height / 2))), sp)

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
        for i, p in pos.items():                                       # pictos : unites, puis avion 9, puis porte-avions par-dessus
            if p is None or i in (self.car, VC.AVION):
                continue
            if self.team[i] == 1 and c and math.hypot(p[0] - c[0], p[1] - c[1]) < C.A_BORD_M:
                continue                                               # sur le pont : le porte-avions suffit
            self.poser(img, self.sprite(self.defn[i], self.team[i], self.cap(i, t)), P(*p))
        if a:
            self.poser(img, self.sprite(self.defn[VC.AVION], 1, self.cap(VC.AVION, t)), P(*a))
        if c:
            self.poser(img, self.sprite(0, 1, self.cap(self.car, t)), P(*c))
        C.echelle_horloge(dr, st, vp, self.s, t, False)
        return img.reduce(S)


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    d = C.preparer(sys.argv[1])
    icones = sys.argv[2]
    if sys.argv[3] == '--png':
        film = FilmPictos(d, sys.argv[4], sys.argv[5], icones)
        film.image(sum(int(v) * m for v, m in zip(sys.argv[6].split(':'), (3600, 60, 1)))).save(sys.argv[7])
        print('ecrit :', sys.argv[7])
        return
    sortie = sys.argv[3]
    if os.path.exists(sortie) and os.listdir(sortie):
        raise SystemExit("REFUS : %s existe deja et n'est pas vide" % sortie)
    os.makedirs(sortie, exist_ok=True)
    for style, vue in (('M3', 'zoom'), ('M5', 'zoom'), ('M3', 'archipel'), ('M5', 'archipel')):
        VC.encoder(FilmPictos(d, style, vue, icones), os.path.join(sortie, 'carte_symboles_%s_%s_essai_A.mp4' % (style, vue)))


if __name__ == '__main__':
    main()
