"""Quatre videos (styles M3 « ocean » et M5 « encre », vues « zoom » et « archipel ») de l'essai A du 29/10, en couleurs d'equipe :
equipe 1 = bleu clair, equipe 0 (IA qui controle les iles) = rouge, equipe 2 = jaune ; iles colorees par proprietaire.
Les unites se deplacent (points), les traces se dessinent au fur et a mesure (porte-avions, avion 9, unites des autres equipes qui se deplacent de plus
de 500 m). Rien d'autre que l'echelle et la petite horloge du journal. Positions du journal toutes les ~5 s, interpolees. Aucun picto, police ni image du
jeu ; aucun nom ni identifiant. Fait maison : Pillow pour les images, ffmpeg (deja installe, local) pour le H.264.
Les fonctions de dessin viennent de fabriquer_cartes_couleurs.py (les memes que pour les 4 images fixes).

Usage : python -I fabriquer_videos_couleurs.py <journal essai A copie> <dossier de sortie NEUF>
        python -I fabriquer_videos_couleurs.py <journal> --png M3|M5 zoom|archipel HH:MM:SS fichier.png      (une seule image, pour regarder)
"""
import bisect
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc2map
import fabriquer_cartes_couleurs as C
from PIL import ImageDraw

FPS, FACTEUR, PAUSE_S = 30, 10, 1      # 1 s de video = 10 s du journal ; 1 s de pause sur la derniere image
FFMPEG = r'C:\Users\UTILISATEUR\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe'
AVION = 9
# tailles pour les videos : en vue archipel, points un peu plus gros (3 a 4 px) et porte-avions nettement plus gros que sur l'image fixe
VUES_VIDEO = {
    'zoom': dict(C.VUES['zoom']),
    'archipel': dict(C.VUES['archipel'], car_w=2.6, vol_w=2.2, rte_w=1.2, r_car=8.0, r_pt=3.6, r_vol=4.2),
}
SORTIES = (('carte_couleurs_M3_zoom_essai_A.mp4', 'M3', 'zoom'), ('carte_couleurs_M5_zoom_essai_A.mp4', 'M5', 'zoom'),
           ('carte_couleurs_M3_archipel_essai_A.mp4', 'M3', 'archipel'), ('carte_couleurs_M5_archipel_essai_A.mp4', 'M5', 'archipel'))


class Suivi:
    """Position d'une unite a l'heure t du journal, interpolee entre deux positions voisines."""

    def __init__(self, V, uid):
        self.walls = [w for w, t, it in V]
        self.pts = [(it[uid][2], it[uid][3]) if uid in it else None for w, t, it in V]

    def pos(self, t):
        i = max(0, bisect.bisect_right(self.walls, t) - 1)
        a = self.pts[i]
        if a is None:
            return None                                     # absente des donnees
        if i + 1 < len(self.pts) and self.pts[i + 1] is not None:
            w0, w1 = self.walls[i], self.walls[i + 1]
            k = 0.0 if w1 <= w0 else min(1.0, max(0.0, (t - w0) / (w1 - w0)))
            b = self.pts[i + 1]
            return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
        return a                                            # tenue jusqu'a la position suivante, ou jusqu'a la fin


class Film:
    def __init__(self, d, style, vue):
        self.d = d
        img, dr, self.P, self.s, self.st, _ = C.fond(d, style, vue)
        C.echelle_horloge(dr, self.st, C.VUES[vue], self.s, None, True)         # l'echelle fait partie du fond ; l'horloge est dessinee a chaque image
        self.bg = img
        self.vp = VUES_VIDEO[vue]
        V = d['V']
        self.V = V
        info = {}
        for w, t, it in V:
            for i, v in it.items():
                info.setdefault(i, (v[0], v[1]))
        self.team = {i: v[1] for i, v in info.items()}
        self.suivi = {i: Suivi(V, i) for i in info}
        self.car = d['car']
        self.mobiles = []                                   # unites des autres equipes qui se deplacent de plus de 500 m (deplacement net)
        for i, tm in self.team.items():
            pts = [p for p in self.suivi[i].pts if p]
            if tm != 1 and len(pts) > 1 and math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]) > C.ROUTE_MIN_M:
                self.mobiles.append(i)
        self.vols = [run for uid, run in d['vols'] if uid == AVION]

    def image(self, t):
        st, vp, P = self.st, self.vp, self.P
        img = self.bg.copy()
        dr = ImageDraw.Draw(img)
        pos = {i: sv.pos(t) for i, sv in self.suivi.items()}
        c = pos[self.car]
        # traces des unites des autres equipes qui bougent, puis route du porte-avions, puis vol de l'avion 9
        for i in self.mobiles:
            pts = [P(x, z) for (w, x, z) in ((self.V[k][0],) + self.suivi[i].pts[k] for k in range(len(self.V)) if self.suivi[i].pts[k] and self.V[k][0] <= t)]
            if pos[i]:
                pts.append(P(*pos[i]))
            C.ligne(dr, pts, st['rte_col'][self.team[i]], None, vp['rte_w'])
        route = [P(x, z) for w, x, z in self.d['route'] if w <= t] + ([P(*c)] if c else [])
        C.ligne(dr, route, C.EQUIPE[1], st['casing'], vp['car_w'])
        a = pos.get(AVION)
        for run in self.vols:
            if run[0][0] > t:
                continue
            pts = [P(p[1], p[2]) for p in run if p[0] <= t]
            if a and t <= run[-1][0]:
                pts.append(P(*a))                          # le bout de la trace suit le point
            C.ligne(dr, pts, C.EQUIPE[1], st['casing'], vp['vol_w'])
        # points : unites (petits), porte-avions (gros), puis avion 9 par-dessus
        for i, p in pos.items():
            if p is None or i in (self.car, AVION):
                continue
            if self.team[i] == 1 and c and math.hypot(p[0] - c[0], p[1] - c[1]) < C.A_BORD_M:
                continue                                    # sur le pont : le gros point suffit
            C.dot(dr, P(*p), vp['r_pt'], C.EQUIPE[self.team[i]], st['outline'])
        if c:
            C.dot(dr, P(*c), vp['r_car'], C.EQUIPE[1], st['outline'], 2)
        if a:
            C.dot(dr, P(*a), vp['r_vol'], C.EQUIPE[1], st['outline'])
        C.echelle_horloge(dr, st, vp, self.s, t, False)
        return img.reduce(C.S)


def encoder(film, sortie):
    t0, t1 = film.d['t_debut'], film.d['t_fin']
    n = int((t1 - t0) / FACTEUR * FPS) + 1
    cmd = [FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (C.W, C.H), '-r', str(FPS), '-i', '-',
           '-an', '-c:v', 'libx264', '-profile:v', 'high', '-level', '4.1', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', sortie]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        data = film.image(min(t1, t0 + f * FACTEUR / FPS)).tobytes()
        p.stdin.write(data)
        if f % 400 == 0:
            print('  %s : image %d / %d' % (os.path.basename(sortie), f, n), flush=True)
    for _ in range(PAUSE_S * FPS):                          # pause sur la derniere image, avec toutes les traces
        p.stdin.write(data)
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit('ffmpeg a echoue pour ' + sortie)
    print('ecrit :', sortie, os.path.getsize(sortie), 'octets,', n + PAUSE_S * FPS, 'images,', (n + PAUSE_S * FPS) / FPS, 's')


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    d = C.preparer(sys.argv[1])
    if sys.argv[2] == '--png':
        film = Film(d, sys.argv[3], sys.argv[4])
        film.image(sum(int(v) * m for v, m in zip(sys.argv[5].split(':'), (3600, 60, 1)))).save(sys.argv[6])
        print('ecrit :', sys.argv[6])
        return
    sortie = sys.argv[2]
    if os.path.exists(sortie) and os.listdir(sortie):
        raise SystemExit("REFUS : %s existe deja et n'est pas vide" % sortie)
    os.makedirs(sortie, exist_ok=True)
    for nom, style, vue in SORTIES:
        encoder(Film(d, style, vue), os.path.join(sortie, nom))


if __name__ == '__main__':
    main()
