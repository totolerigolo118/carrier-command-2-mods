"""Deux videos toutes simples (styles M3 « ocean » et M5 « encre ») de l'essai A du 29/10 : les iles, le porte-avions (gros point) et l'avion 9
(petit point) qui se deplacent, leur trace qui se dessine. Rien d'autre qu'une echelle de 5 km et la petite horloge du journal.
Meme cadrage et memes couleurs que les maquettes (fabriquer_maquettes.py, importe ici). Positions du journal toutes les ~5 s, interpolees.
AUCUN picto, police ni image du jeu ; aucun nom ni identifiant. Fait maison : Pillow pour les images, ffmpeg (deja installe, local) pour le H.264.

Usage : python -I fabriquer_videos_cartes.py <journal essai A copie> <dossier de sortie NEUF>
        python -I fabriquer_videos_cartes.py <journal> --png M3_ocean|M5_encre HH:MM:SS fichier.png      (une seule image, pour regarder)
"""
import bisect
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc2map
import fabriquer_maquettes as M
from PIL import ImageDraw

FPS, FACTEUR, PAUSE_S = 30, 10, 1      # 1 s de video = 10 s du journal ; 1 s de pause sur la derniere image
FFMPEG = r'C:\Users\UTILISATEUR\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe'
SORTIES = (('carte_M3_ocean_essai_A.mp4', 'M3_ocean'), ('carte_M5_encre_essai_A.mp4', 'M5_encre'))
AVION = 9


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
    def __init__(self, d, pal):
        self.d, self.pal = d, pal
        self.bg, _, self.P, self.s = M.fond(d, pal)
        M.echelle(ImageDraw.Draw(self.bg), pal, self.s)
        self.car = Suivi(d['V'], d['car'])
        self.avion = Suivi(d['V'], AVION)
        self.vols = [run for uid, run in d['vols'] if uid == AVION]

    def image(self, t):
        pal, P = self.pal, self.P
        img = self.bg.copy()
        dr = ImageDraw.Draw(img)
        c = self.car.pos(t)
        route = [P(x, z) for w, x, z in self.d['route'] if w <= t] + ([P(*c)] if c else [])
        if len(route) > 1:
            dr.line(route, fill=pal['car'], width=int(round(pal['car_w'] * M.S)), joint='curve')
        a = self.avion.pos(t)
        for run in self.vols:
            if run[0][0] > t:
                continue
            pts = [P(p[1], p[2]) for p in run if p[0] <= t]
            if a and t <= run[-1][0]:
                pts.append(P(*a))                          # le bout de la trace suit le point
            if len(pts) > 1:
                dr.line(pts, fill=pal['plane'], width=int(round(pal['plane_w'] * M.S)), joint='curve')
        if c:
            M.point(dr, pal, P(*c), 8.5, pal['car'], 2)
        if a:
            M.point(dr, pal, P(*a), 4.8, pal['plane'], 1)
        M.horloge(dr, pal, t)
        return img.reduce(M.S)


def encoder(film, sortie):
    t0, t1 = film.d['t_debut'], film.d['t_fin']
    n = int((t1 - t0) / FACTEUR * FPS) + 1
    cmd = [FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (M.W, M.H), '-r', str(FPS), '-i', '-',
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
    d = M.donnees(sys.argv[1])
    if sys.argv[2] == '--png':
        film = Film(d, M.PALETTES[sys.argv[3]])
        film.image(sum(int(v) * m for v, m in zip(sys.argv[4].split(':'), (3600, 60, 1)))).save(sys.argv[5])
        print('ecrit :', sys.argv[5])
        return
    sortie = sys.argv[2]
    if os.path.exists(sortie) and os.listdir(sortie):
        raise SystemExit("REFUS : %s existe deja et n'est pas vide" % sortie)
    os.makedirs(sortie, exist_ok=True)
    for nom, style in SORTIES:
        encoder(Film(d, M.PALETTES[style]), os.path.join(sortie, nom))


main()
