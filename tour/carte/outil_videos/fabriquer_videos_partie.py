"""Quatre videos (styles M3 « ocean » et M5 « encre », vues « zoom » et « archipel ») de LA PARTIE du 30/10 (08:44:31 -> 08:55:29), comme les videos
de pictos de l'essai A (fabriquer_videos_pictos.py, importe ici) : pictos du jeu teintes par equipe (equipe 1 bleu clair, equipe 0 rouge, equipe 2 jaune),
iles colorees par proprietaire, traces qui se dessinent, echelle et petite horloge du journal. Rien d'autre ; aucun nom ni identifiant.

Differences avec l'essai A :
 - le journal contient plusieurs parties : on part d'un extrait CC2MAP de la derniere partie (extraire_partie.py), pour ne pas melanger les instantanes ;
 - les avions de l'equipe 1 qui quittent le pont sont suivis (les avions 9 et 10 le matin du 30/10 ; tous ceux qui ont une trace dans d['vols']) : trace + picto,
   dessines PAR-DESSUS le porte-avions pour rester visibles quand ils sont poses sur le pont (picto un peu reduit sur le pont, pour laisser voir le porte-avions) ;
 - ZOOM : 20 km de haut centres sur la route du porte-avions (cadrage valide) ; l'avion 10 en sort quand il s'eloigne (voir --sortie) ;
 - ARCHIPEL : cadre elargi pour contenir les iles ET toutes les positions de l'equipe 1 (donc tout le vol de l'avion 10), avec sa trace ;
 - vitesse : 1 s de video = 11 s d'horloge du journal (la partie dure ~658 s) -> ~61 s avec 1 s de pause finale.

Pictos : ceux de carte_timelapse/icones (Mac). AUCUN fichier du dossier du jeu n'est lu. Ces videos contiennent des pictos du jeu : le partage depend de
l'autorisation du developpeur (voir NE_PAS_PARTAGER.txt). Fait maison : Pillow pour les images, ffmpeg (local) pour le H.264.

Usage : python -I fabriquer_videos_partie.py <extrait CC2MAP de la partie> <dossier icones> <dossier de sortie NEUF>
        python -I fabriquer_videos_partie.py <extrait> <dossier icones> --png M3|M5 zoom|archipel HH:MM:SS fichier.png      (une seule image)
        python -I fabriquer_videos_partie.py <extrait> <dossier icones> --sortie                                           (quand l'avion 10 quitte le cadre zoom)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc2map
import fabriquer_cartes_couleurs as C
import fabriquer_maquettes as M
import fabriquer_videos_couleurs as VC
import fabriquer_videos_pictos as FP
from PIL import Image, ImageDraw

FACTEUR = 11                    # 1 s de video = 11 s d'horloge du journal
PONT_M = M.HORS_PONT_M           # moins de 100 m du porte-avions : pose sur le pont
PONT_ECHELLE = 0.8               # picto un peu reduit sur le pont
MARGE_M = 2000                   # marge autour des positions de l'equipe 1 pour le cadre « archipel »
VUES = (('M3', 'zoom'), ('M5', 'zoom'), ('M3', 'archipel'), ('M5', 'archipel'))


def cadre_partie(d, nom):
    """Remplace fabriquer_cartes_couleurs.cadre : meme calcul, mais le zoom est centre sur la route du porte-avions seule (l'avion 10 s'en va tres loin)
    et le cadre « archipel » contient aussi toutes les positions de l'equipe 1 sur la partie."""
    if nom == 'zoom':
        xs = [p[1] for p in d['route']]
        zs = [p[2] for p in d['route']]
        cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
        vh = M.VIEW_H
    else:
        R = M.ILE_R * 1.35
        xs = [x - R for _, x, z in d['iles']] + [x + R for _, x, z in d['iles']]
        zs = [z - R for _, x, z in d['iles']] + [z + R for _, x, z in d['iles']]
        for w, t, it in d['V']:
            for i, v in it.items():
                if v[1] == 1:
                    xs += [v[2] - MARGE_M, v[2] + MARGE_M]
                    zs += [v[3] - MARGE_M, v[3] + MARGE_M]
        x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        vh = max(z1 - z0, (x1 - x0) * M.H / M.W) * 1.02
    s = M.H * M.S / vh

    def P(x, z):
        return (M.W * M.S / 2 + (x - cx) * s, M.H * M.S / 2 - (z - cz) * s)
    return cx, cz, vh, s, P


C.cadre = cadre_partie          # fond() cherche `cadre` dans ce module a chaque appel : les autres scripts restent inchanges


class FilmPartie(FP.FilmPictos):
    def __init__(self, d, style, vue, dossier_icones):
        super().__init__(d, style, vue, dossier_icones)
        self.suivis = tuple(sorted({uid for uid, run in d['vols']}))   # avions de l'equipe 1 qui ont quitte le pont : trace + picto par-dessus le porte-avions
        self.runs = {u: [run for uid, run in d['vols'] if uid == u] for u in self.suivis}

    def sprite_pont(self, defn, equipe, angle):
        sp = self.sprite(defn, equipe, angle)
        cle = ('pont', defn, equipe, int(round(angle / 2.0)) * 2)
        if cle not in self._cache:
            self._cache[cle] = sp.resize((max(1, int(round(sp.width * PONT_ECHELLE))), max(1, int(round(sp.height * PONT_ECHELLE)))), Image.LANCZOS)
        return self._cache[cle]

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
        for u in self.suivis:                                          # traces des vols des avions suivis
            a = pos.get(u)
            for run in self.runs[u]:
                if run[0][0] > t:
                    continue
                pts = [P(p[1], p[2]) for p in run if p[0] <= t]
                if a and t <= run[-1][0]:
                    pts.append(P(*a))
                C.ligne(dr, pts, C.EQUIPE[1], st['casing'], vp['vol_w'])
        for i, p in pos.items():                                       # pictos : unites, puis porte-avions, puis les deux avions suivis par-dessus
            if p is None or i == self.car or i in self.suivis:
                continue
            if self.team[i] == 1 and c and math.hypot(p[0] - c[0], p[1] - c[1]) < C.A_BORD_M:
                continue                                               # sur le pont : le porte-avions suffit
            self.poser(img, self.sprite(self.defn[i], self.team[i], self.cap(i, t)), P(*p))
        if c:
            self.poser(img, self.sprite(0, 1, self.cap(self.car, t)), P(*c))
        for u in self.suivis:
            p = pos.get(u)
            if not p:
                continue
            sur_pont = c and math.hypot(p[0] - c[0], p[1] - c[1]) < PONT_M
            f = self.sprite_pont if sur_pont else self.sprite
            self.poser(img, f(self.defn[u], 1, self.cap(u, t)), P(*p))
        self.dessus(img, dr, P, t)
        C.echelle_horloge(dr, st, vp, self.s, t, False)
        return img.reduce(C.S)

    def dessus(self, img, dr, P, t):
        """Point d'accroche : dessin par-dessus les pictos, avant l'horloge (rien ici ; fabriquer_videos_partie_v2.py y dessine les missiles)."""


def sortie_zoom(d):
    """Instants ou l'avion 10 est hors du cadre zoom (20 km de haut)."""
    cx, cz, vh, s, P = cadre_partie(d, 'zoom')
    demi_l, demi_h = vh * M.W / M.H / 2, vh / 2
    dedans = None
    for w, t, it in d['V']:
        if 10 in it:
            ok = abs(it[10][2] - cx) <= demi_l and abs(it[10][3] - cz) <= demi_h
            if ok != dedans:
                print('   %s : avion 10 %s le cadre zoom (position %.0f, %.0f ; cadre x %.0f..%.0f z %.0f..%.0f)' % (
                    cc2map.hms(w), 'ENTRE dans' if ok else 'SORT de', it[10][2], it[10][3], cx - demi_l, cx + demi_l, cz - demi_h, cz + demi_h))
                dedans = ok


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    d = C.preparer(sys.argv[1])
    icones = sys.argv[2]
    if sys.argv[3] == '--sortie':
        sortie_zoom(d)
        return
    if sys.argv[3] == '--png':
        film = FilmPartie(d, sys.argv[4], sys.argv[5], icones)
        film.image(sum(int(v) * m for v, m in zip(sys.argv[6].split(':'), (3600, 60, 1)))).save(sys.argv[7])
        print('ecrit :', sys.argv[7])
        return
    sortie = sys.argv[3]
    if os.path.exists(sortie) and os.listdir(sortie):
        raise SystemExit("REFUS : %s existe deja et n'est pas vide" % sortie)
    os.makedirs(sortie, exist_ok=True)
    VC.FACTEUR = FACTEUR                                              # encoder() lit ce reglage a chaque appel
    for style, vue in VUES:
        VC.encoder(FilmPartie(d, style, vue, icones), os.path.join(sortie, 'carte_partie_30-10_%s_%s.mp4' % (style, vue)))


if __name__ == '__main__':
    main()
