"""Deux videos time-lapse basiques des essais du 29/10 (atterrissage de l'avion 9 sur le porte-avions, plugin frein v6 puis v7).
Chaque video : vue d'ensemble (route du porte-avions et de l'avion 9), gros plan sur le pont, horloge du JOURNAL, facteur d'acceleration,
evenements du plugin. Fait maison : Python + Pillow pour les images, ffmpeg (deja installe, local) pour l'encodage H.264. Aucun reseau.
Lit seulement les lignes CC2MAP et quelques lignes « id 9 » du plugin frein ; ne touche ni au jeu, ni aux journaux d'origine.

Usage : python -I fabriquer_videos.py <dossier icones du jeu> <dossier des journaux copies> <dossier de sortie NEUF>
        python -I fabriquer_videos.py <icones> <journaux> --png A|B HH:MM:SS fichier.png      (une seule image, pour regarder)
Les videos contiennent les pictos du jeu : usage personnel, ne pas les partager (voir tour/carte/LISEZ-MOI_rendu_marine.md).
"""
import bisect
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc2map
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SPEED = 1280, 720, 30, 5
FFMPEG = r'C:\Users\UTILISATEUR\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe'
FONTS = 'C:/Windows/Fonts/'
BG, CYAN, PALE, STRONG, WEAK, AMBER = (5, 9, 11), (61, 242, 255), (159, 232, 240), (216, 251, 255), (95, 163, 173), (255, 210, 74)
LINE = (30, 70, 78)
MAIN = (20, 20, 660, 700)      # vue d'ensemble
INS = (680, 258, 1260, 528)    # gros plan sur le pont
DECK_PX = (95, 190)            # porte-avions du gros plan : taille indicative
INS_S = 1.3                    # pixels par metre dans le gros plan
ZONE_M = 150                   # zone du pont du plugin frein

ESSAIS = {
    'A': dict(log='cc2x_2026-10-29_142607_frein_v6_ancien_exe.log', titre='Essai A · plugin frein v6', sortie='essai_A_v6_14h27.mp4',
              debut='14:30:00', fin='14:34:00'),
    'B': dict(log='cc2x_2026-10-29_154658_frein_v7_diag.log', titre='Essai B · plugin frein v7', sortie='essai_B_v7_15h49.mp4',
              debut='15:51:00', fin='15:56:18'),
}
_fc = {}


def font(nom, px):
    k = (nom, px)
    if k not in _fc:
        try:
            _fc[k] = ImageFont.truetype(FONTS + nom, px)
        except OSError:
            _fc[k] = ImageFont.load_default()
    return _fc[k]


def secs(hms):
    h, m, s = hms.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def seeded(n):
    st = [n * 9301 + 49297]

    def rnd():
        st[0] = (st[0] * 9301 + 49297) % 233280
        return st[0] / 233280
    return rnd


def profil(seed):                # meme forme d'ile indicative que la page de rejeu
    rnd = seeded(seed * 7 + 11)
    hh = [(rnd() * 6.283, (0.20 / (h ** 0.9)) * (0.6 + rnd() * 0.8)) for h in range(1, 8)]
    arr = []
    for i in range(96):
        a = i / 96 * 6.2832
        k = 1 + sum(am * math.sin((j + 1) * a + ph) for j, (ph, am) in enumerate(hh))
        k = max(0.55, k) * (1 + 0.035 * math.sin(23 * i / 96 * 6.2832 + seed) + 0.02 * math.sin(41 * i / 96 * 6.2832 + seed * 2))
        arr.append(k)
    return arr


class Essai:
    def __init__(self, cle, dossier_logs, dossier_icones):
        c = ESSAIS[cle]
        self.cle, self.titre, self.sortie = cle, c['titre'], c['sortie']
        D = cc2map.parse(os.path.join(dossier_logs, c['log']))
        self.t0, self.t1 = secs(c['debut']), secs(c['fin'])
        self.V = D['V']
        self.walls = [s[0] for s in self.V]
        self.T = D['T']
        cars = [i for i, v in self.V[0][2].items() if v[0] == 0 and v[1] == 1]
        self.car = cars[0]
        self.icons = {n: Image.open(os.path.join(dossier_icones, n + '.png')).convert('RGBA') for n in ('carrier', 'albatros')}
        self.events = self._events(D['events'])
        # etendue de la vue d'ensemble : porte-avions + avion 9 dans la fenetre
        xs, zs = [], []
        for w, t, it in self.V:
            if self.t0 - 10 <= w <= self.t1 + 10:
                for u in (self.car, 9):
                    if u in it:
                        xs.append(it[u][2])
                        zs.append(it[u][3])
        pad = 350
        self.minx, self.maxx, self.minz, self.maxz = min(xs) - pad, max(xs) + pad, min(zs) - pad, max(zs) + pad
        mw, mh = MAIN[2] - MAIN[0], MAIN[3] - MAIN[1]
        self.s = min(mw / (self.maxx - self.minx), mh / (self.maxz - self.minz))
        self.ox = MAIN[0] + (mw - (self.maxx - self.minx) * self.s) / 2
        self.oz = MAIN[1] + (mh - (self.maxz - self.minz) * self.s) / 2
        self.bg = self._fond()

    # ---------------------------------------------------------------- evenements a annoter
    def _events(self, brut):
        ev = []
        for w, uid, mot, rest in brut:
            if uid != 9 or not (self.t0 <= w <= self.t1 + 1):
                continue
            if mot == 'left the zone':
                ev.append((w, "Avion 9 quitte le pont"))
            elif mot == 'BRAKE start':
                ev.append((w, "Atterrissage : début du freinage"))
            elif mot == 'STOPPED':
                m = re.search(r'after ([\d.]+) s', rest)
                ev.append((w, "Avion 9 arrêté sur le pont" + (" (%s s)" % m.group(1).replace('.', ',') if m else "")))
            elif mot == 'BRAKE released':
                ev.append((w, "Ordre de retour : frein relâché"))
            elif mot == 'RECALL start':
                ev.append((w, "Ordre de retour : frein maintenu"))
            elif mot == 'IDLE ended' and 'session ended' in rest:
                ev.append((w, "Fin de la session du plugin"))
        vu = False
        for w, t, it in self.V:                      # disparition de l'avion 9 des donnees
            if 9 in it:
                vu = True
            elif vu and self.t0 <= w <= self.t1:
                ev.append((w, "Avion 9 n'est plus dans les données"))
                break
        ev.sort()
        return ev

    # ---------------------------------------------------------------- etat interpole a l'heure t du journal
    def etat(self, t):
        i = max(0, min(len(self.V) - 1, bisect.bisect_right(self.walls, t) - 1))
        j = min(i + 1, len(self.V) - 1)
        A, B = self.V[i], self.V[j]
        k = 0.0 if B[0] <= A[0] else max(0.0, min(1.0, (t - A[0]) / (B[0] - A[0])))
        out = {}
        for uid, a in A[2].items():
            b = B[2].get(uid)
            if b is None:
                out[uid] = (a[0], a[1], a[2], a[3], a[4])
                continue
            dy = (b[4] - a[4] + 180) % 360 - 180
            out[uid] = (a[0], a[1], a[2] + (b[2] - a[2]) * k, a[3] + (b[3] - a[3]) * k, (a[4] + dy * k) % 360)
        return out

    def trace(self, t, uid):
        pts = [(w, it[uid][2], it[uid][3]) for w, tk, it in self.V if self.t0 - 1 <= w <= t and uid in it]
        e = self.etat(t).get(uid)
        pts = [(x, z) for _, x, z in pts]
        if e:
            pts.append((e[2], e[3]))
        return pts

    # ---------------------------------------------------------------- coordonnees
    def P(self, x, z):
        return (self.ox + (x - self.minx) * self.s - MAIN[0], self.oz + (self.maxz - z) * self.s - MAIN[1])

    def _fond(self):
        img = Image.new('RGB', (W, H), BG)
        d = ImageDraw.Draw(img, 'RGBA')
        # panneau principal
        d.rectangle(MAIN, outline=CYAN + (200,), width=1)
        crop = img.crop(MAIN)
        cd = ImageDraw.Draw(crop, 'RGBA')
        mw, mh = MAIN[2] - MAIN[0], MAIN[3] - MAIN[1]
        pas = 500 if (self.maxx - self.minx) > 2500 else 250
        x = math.ceil(self.minx / pas) * pas
        while x < self.maxx:
            px = self.P(x, 0)[0]
            cd.line([(px, 0), (px, mh)], fill=(61, 242, 200, 28))
            cd.text((px + 3, mh - 16), '%.2f' % (x / 1000), font=font('georgiai.ttf', 12), fill=PALE + (190,))
            x += pas
        z = math.ceil(self.minz / pas) * pas
        while z < self.maxz:
            py = self.P(0, z)[1]
            cd.line([(0, py), (mw, py)], fill=(61, 242, 200, 28))
            cd.text((4, py - 15), '%.2f' % (z / 1000), font=font('georgiai.ttf', 12), fill=PALE + (190,))
            z += pas
        # iles (forme et taille indicatives), couleur selon le proprietaire au debut de la fenetre
        tiles = [s for s in self.T if s[0] <= self.t0] or self.T[:1]
        owners = tiles[-1][2] if tiles else {}
        for iid, (team, ix, iz) in (self.T[0][2].items() if self.T else []):
            team = owners.get(iid, (team,))[0]
            r = 2400 * 0.85
            if ix + r < self.minx or ix - r > self.maxx or iz + r < self.minz or iz - r > self.maxz:
                continue
            col = {1: CYAN, 2: (255, 90, 77)}.get(team, (255, 194, 74))
            prof = profil(iid)
            pts = []
            for n in range(96):
                a = n / 96 * 6.2832
                pts.append(self.P(ix + math.cos(a) * r * prof[n], iz + math.sin(a) * r * prof[n]))
            layer = Image.new('RGBA', crop.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            ld.polygon(pts, fill=(8, 34, 36, 190))
            msk = Image.new('L', crop.size, 0)
            ImageDraw.Draw(msk).polygon(pts, fill=255)
            hach = Image.new('RGBA', crop.size, (0, 0, 0, 0))
            hd = ImageDraw.Draw(hach)
            for k in range(-mh, mw + mh, 8):
                hd.line([(k, mh), (k + mh, 0)], fill=(95, 225, 210, 90))
            layer.paste(hach, (0, 0), msk)
            crop.paste(layer, (0, 0), layer)
            cd = ImageDraw.Draw(crop, 'RGBA')
            cd.line(pts + [pts[0]], fill=col + (230,), width=2)
            c = self.P(ix, iz)
            cd.text((c[0], c[1] + r * self.s * 1.05 + 4), 'Île %d' % iid, font=font('georgiaz.ttf', 14), fill=col + (255,), anchor='mt')
        # barre d'echelle
        bar = 500 * self.s
        cd.rectangle((14, mh - 40, 14 + bar, mh - 36), fill=CYAN + (220,))
        cd.text((14, mh - 58), '500 m', font=font('georgiai.ttf', 13), fill=PALE + (230,))
        cd.text((mw - 14, 12), 'Nord en haut', font=font('georgiai.ttf', 13), fill=PALE + (230,), anchor='ra')
        cd.text((mw - 14, 32), "îles : forme et taille indicatives", font=font('georgiai.ttf', 12), fill=WEAK + (255,), anchor='ra')
        img.paste(crop, MAIN[:2])
        d = ImageDraw.Draw(img, 'RGBA')
        # cadre du gros plan avec quadrillage de 50 m (porte-avions vers la droite)
        d.rectangle(INS, outline=CYAN + (200,), width=1)
        ic = img.crop(INS)
        idr = ImageDraw.Draw(ic, 'RGBA')
        iw, ih = ic.size
        cx, cy = iw / 2, ih / 2
        for m in range(-int(iw / 2 / INS_S / 50) * 50 - 50, int(iw / 2 / INS_S / 50) * 50 + 51, 50):
            idr.line([(cx + m * INS_S, 0), (cx + m * INS_S, ih)], fill=(61, 242, 200, 26))
        for m in range(-int(ih / 2 / INS_S / 50) * 50 - 50, int(ih / 2 / INS_S / 50) * 50 + 51, 50):
            idr.line([(0, cy + m * INS_S), (iw, cy + m * INS_S)], fill=(61, 242, 200, 26))
        idr.line([(iw - 14 - 50 * INS_S, ih - 14), (iw - 14, ih - 14)], fill=CYAN + (230,), width=3)
        idr.text((iw - 14, ih - 32), '50 m', font=font('georgiai.ttf', 13), fill=PALE + (230,), anchor='ra')
        idr.text((8, 6), "GROS PLAN SUR LE PONT (porte-avions : taille indicative)", font=font('consola.ttf', 12), fill=WEAK + (255,))
        img.paste(ic, INS[:2])
        # textes fixes
        d.text((680, 18), self.titre, font=font('georgiaz.ttf', 32), fill=STRONG)
        d.text((680, 62), "29/10 · avion 9 et porte-avions de l'équipe 1", font=font('consola.ttf', 15), fill=WEAK)
        d.text((680, 92), "HEURE DU JOURNAL", font=font('consola.ttf', 14), fill=WEAK)
        d.text((1262, 112), "×%d" % SPEED, font=font('consolab.ttf', 64), fill=CYAN, anchor='ra')
        d.text((1262, 186), "1 s de vidéo = %d s du journal" % SPEED, font=font('consola.ttf', 14), fill=WEAK, anchor='ra')
        d.text((680, 538), "ÉVÉNEMENTS (plugin frein)", font=font('consola.ttf', 14), fill=WEAK)
        # legende de la vue d'ensemble
        d.ellipse((34, 36, 44, 46), fill=CYAN)
        d.text((52, 32), "porte-avions", font=font('consola.ttf', 14), fill=PALE)
        d.ellipse((34, 58, 44, 68), fill=AMBER)
        d.text((52, 54), "avion 9", font=font('consola.ttf', 14), fill=PALE)
        return img

    # ---------------------------------------------------------------- sprites
    _sp = {}

    def sprite(self, nom, taille, couleur, angle):
        k = (nom, taille, couleur, int(round(angle / 2.0)) * 2)
        if k not in Essai._sp:
            base = self.icons[nom].rotate(180)                    # les pictos du jeu pointent vers le bas
            tint = Image.new('RGBA', base.size, couleur + (255,))
            tint.putalpha(base.getchannel('A'))
            tint = tint.resize(taille, Image.BICUBIC)
            Essai._sp[k] = tint.rotate(-k[3], resample=Image.BICUBIC, expand=True)    # sens horaire
        return Essai._sp[k]

    @staticmethod
    def coller(img, sp, x, y):
        img.paste(sp, (int(round(x - sp.width / 2)), int(round(y - sp.height / 2))), sp)

    # ---------------------------------------------------------------- une image
    def image(self, t):
        img = self.bg.copy()
        et = self.etat(t)
        car, pl = et[self.car], et.get(9)
        mw, mh = MAIN[2] - MAIN[0], MAIN[3] - MAIN[1]
        # ----- vue d'ensemble
        m = img.crop(MAIN)
        md = ImageDraw.Draw(m, 'RGBA')
        for uid, tr_col, wd in ((self.car, CYAN, 2), (9, AMBER, 2)):
            pts = [self.P(x, z) for x, z in self.trace(t, uid)]
            if len(pts) > 1:
                md.line(pts, fill=tr_col + ((120,) if uid == self.car else (230,)), width=(4 if uid == self.car else wd))
        for uid, v in et.items():                                     # autres unites de l'equipe 1, seulement si loin du pont
            if v[1] == 1 and uid not in (self.car, 9) and math.hypot(v[2] - car[2], v[3] - car[3]) > ZONE_M:
                p = self.P(v[2], v[3])
                md.ellipse((p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2), fill=WEAK + (255,))
        pc = self.P(car[2], car[3])
        self.coller(m, self.sprite('carrier', (18, 36), CYAN, car[4]), *pc)
        if pl:
            pp = self.P(pl[2], pl[3])
            md.ellipse((pp[0] - 15, pp[1] - 15, pp[0] + 15, pp[1] + 15), outline=AMBER + (255,), width=2)
            self.coller(m, self.sprite('albatros', (22, 22), AMBER, pl[4]), *pp)
        img.paste(m, MAIN[:2])
        # ----- gros plan : porte-avions vers la droite, tribord vers le bas
        ic = img.crop(INS)
        idr = ImageDraw.Draw(ic, 'RGBA')
        iw, ih = ic.size
        cx, cy = iw / 2, ih / 2
        b = math.radians(car[4])
        fx, fz, rx, rz = math.sin(b), math.cos(b), math.cos(b), -math.sin(b)

        def rel(x, z):
            dx, dz = x - car[2], z - car[3]
            return cx + (dx * fx + dz * fz) * INS_S, cy + (dx * rx + dz * rz) * INS_S

        self.coller(ic, self.sprite('carrier', DECK_PX, CYAN, 90), cx, cy)
        dist = None
        if pl:
            dist = math.hypot(pl[2] - car[2], pl[3] - car[3])
            hist = []
            for s in range(30, -1, -1):                               # trace des 30 dernieres secondes, vue depuis le porte-avions
                e2 = self.etat(max(self.t0, t - s))
                if 9 in e2:
                    c2 = e2[self.car]
                    hist.append(rel(car[2] + e2[9][2] - c2[2], car[3] + e2[9][3] - c2[3]))
            if len(hist) > 1:
                idr.line(hist, fill=AMBER + (200,), width=2)
            px, py = rel(pl[2], pl[3])
            if 0 <= px < iw and 0 <= py < ih:
                self.coller(ic, self.sprite('albatros', (40, 40), AMBER, pl[4] - car[4] + 90), px, py)
                idr.ellipse((px - 26, py - 26, px + 26, py + 26), outline=AMBER + (255,), width=2)
            else:
                idr.text((iw - 10, 8), "avion 9 hors cadre", font=font('consola.ttf', 13), fill=AMBER + (255,), anchor='ra')
        img.paste(ic, INS[:2])
        d = ImageDraw.Draw(img, 'RGBA')
        # ----- horloge, statut, evenements, avancement
        d.text((680, 106), cc2map.hms(t), font=font('consolab.ttf', 80), fill=STRONG)
        if pl is None:
            etat = "Avion 9 : absent des données"
            col = (255, 150, 120)
        elif dist <= ZONE_M:
            etat, col = "Avion 9 : sur le pont, à %d m du centre" % dist, AMBER
        else:
            etat, col = "Avion 9 : en vol, à %s m du porte-avions" % format(int(round(dist)), ',').replace(',', ' '), AMBER
        d.text((680, 222), etat, font=font('consolab.ttf', 21), fill=col)
        passes = [e for e in self.events if e[0] <= t][-4:]
        for n, (w, txt) in enumerate(passes):
            neuf = (n == len(passes) - 1)
            d.text((680, 562 + n * 30), "%s  %s" % (cc2map.hms(w), txt), font=font('consolab.ttf' if neuf else 'consola.ttf', 17), fill=STRONG if neuf else PALE)
        if not passes:
            d.text((680, 562), "(aucun pour l'instant)", font=font('consola.ttf', 17), fill=WEAK)
        d.rectangle((20, 710, 1260, 714), fill=LINE)
        d.rectangle((20, 710, 20 + (1240) * (t - self.t0) / (self.t1 - self.t0), 714), fill=CYAN)
        return img


def encoder(essai, sortie):
    n = int((essai.t1 - essai.t0) / SPEED * FPS)
    cmd = [FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
           '-an', '-c:v', 'libx264', '-profile:v', 'high', '-level', '4.1', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', sortie]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(essai.image(essai.t0 + f / FPS * SPEED).tobytes())
        if f % 300 == 0:
            print('  %s : image %d / %d' % (essai.cle, f, n), flush=True)
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit('ffmpeg a echoue pour ' + sortie)
    print('ecrit :', sortie, os.path.getsize(sortie), 'octets,', n, 'images,', n / FPS, 's')


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    icones, logs = sys.argv[1], sys.argv[2]
    if sys.argv[3] == '--png':
        e = Essai(sys.argv[4], logs, icones)
        e.image(secs(sys.argv[5])).save(sys.argv[6])
        print('ecrit :', sys.argv[6])
        return
    sortie = sys.argv[3]
    if os.path.exists(sortie) and os.listdir(sortie):
        raise SystemExit('REFUS : %s existe deja et n\'est pas vide' % sortie)
    os.makedirs(sortie, exist_ok=True)
    for cle in ('A', 'B'):
        encoder(Essai(cle, logs, icones), os.path.join(sortie, ESSAIS[cle]['sortie']))


main()
