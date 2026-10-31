"""Quatre images fixes (PNG 1280x720) en couleurs d'equipe : M3 « ocean » et M5 « encre », chacune en vue « archipel » (les 24 iles) et « zoom » (20 km
autour du porte-avions). Donnee : derniere image de l'essai A du 29/10 (tout le journal, toutes les traces).
Couleurs d'equipe : equipe 1 = bleu clair, equipe 0 (IA qui controle les iles) = rouge, equipe 2 = jaune. Appliquees aux iles (couleur du proprietaire),
aux unites (points) et aux traces. Le porte-avions est le gros point ; les unites de l'equipe 1 restees sur le pont (< 80 m) ne sont pas dessinees a part.
Une route n'est tracee que pour les unites des autres equipes qui se deplacent de plus de 500 m (deplacement net, premiere -> derniere position).
AUCUN picto, police ni image du jeu ; aucun nom ni identifiant. Lit seulement les lignes CC2MAP d'une copie du journal.

Usage : python -I fabriquer_cartes_couleurs.py <journal essai A copie> <dossier de sortie NEUF>
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc2map
import fabriquer_maquettes as M
from PIL import Image, ImageDraw, ImageFont

W, H, S = M.W, M.H, M.S
EQUIPE = {1: (110, 200, 255), 0: (240, 70, 60), 2: (255, 214, 50)}          # bleu clair, rouge, jaune
A_BORD_M = 80                                                                 # unite de l'equipe 1 a moins de 80 m du porte-avions : a bord
ROUTE_MIN_M = 500                                                             # deplacement net minimal pour tracer une route

STYLES = {
    # M3 : mer plus sombre ; ile = remplissage sombre de l'equipe + cote (liseré) dans la couleur vive de l'equipe ; points a liseré clair
    'M3': dict(bg=(16, 58, 100), grid=(27, 78, 124), rim=True, isl_fill={1: (34, 96, 148), 0: (122, 38, 34), 2: (134, 112, 26)}, isl_line=None,
               outline=(240, 248, 255), txt=(222, 236, 246), casing=(8, 30, 56), rte_col=dict(EQUIPE)),
    # M5 : fond blanc ; ile = teinte claire de l'equipe + contour noir ; points et traces a liseré noir ; routes d'unites en rouge/jaune plus fonces
    'M5': dict(bg=(255, 255, 255), grid=None, rim=False, isl_fill={1: (186, 222, 248), 0: (246, 186, 180), 2: (252, 228, 110)}, isl_line=(20, 20, 20),
               outline=(20, 20, 20), txt=(90, 90, 90), casing=(20, 20, 20), rte_col={1: EQUIPE[1], 0: (196, 28, 28), 2: (200, 150, 0)}),
}
VUES = {   # largeurs de trait (px), rayons de points (px), pas du quadrillage et longueur de l'echelle (m)
    'zoom': dict(car_w=3.2, vol_w=2.6, rte_w=1.2, r_car=8.5, r_pt=3.0, r_vol=4.8, grille=5000, echelle=5000),
    'archipel': dict(car_w=2.2, vol_w=2.0, rte_w=1.0, r_car=5.0, r_pt=1.8, r_vol=3.0, grille=10000, echelle=10000),
}


def preparer(chemin):
    d = M.donnees(chemin)
    D = cc2map.parse(chemin)
    T0, T1 = D['T'][0][2], D['T'][-1][2]
    V = d['V']
    car = d['car']
    d['iles_eq'] = {i: T1[i][0] for i in T0}
    dern = V[-1][2]
    c = dern[car]
    d['points'] = []                                         # (id, equipe, x, z) a la derniere image, sauf equipe 1 a bord et porte-avions
    for i, v in dern.items():
        if i == car:
            continue
        if v[1] == 1 and math.hypot(v[2] - c[2], v[3] - c[3]) < A_BORD_M:
            continue
        d['points'].append((i, v[1], v[2], v[3]))
    d['routes'] = []                                         # routes des unites des autres equipes qui se deplacent
    for i, v in dern.items():
        if v[1] == 1:
            continue
        pts = [(it[i][2], it[i][3]) for w, t, it in V if i in it]
        if len(pts) > 1 and math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]) > ROUTE_MIN_M:
            d['routes'].append((v[1], pts))
    d['compte'] = {}
    for i, v in V[-1][2].items():
        d['compte'][v[1]] = d['compte'].get(v[1], 0) + 1
    return d


def cadre(d, nom):
    if nom == 'zoom':
        cx, cz, _, _ = M.vue(d)
        vh = M.VIEW_H
    else:
        R = M.ILE_R * 1.35
        xs = [x for _, x, z in d['iles']]
        zs = [z for _, x, z in d['iles']]
        x0, x1, z0, z1 = min(xs) - R, max(xs) + R, min(zs) - R, max(zs) + R
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        vh = max(z1 - z0, (x1 - x0) * H / W) * 1.02
    s = H * S / vh

    def P(x, z):
        return (W * S / 2 + (x - cx) * s, H * S / 2 - (z - cz) * s)
    return cx, cz, vh, s, P


def ligne(dr, pts, couleur, casing, largeur):
    """Trait colore avec liseré sombre dessous, pour rester lisible sur la mer comme sur le blanc."""
    if len(pts) < 2:
        return
    if casing:
        dr.line(pts, fill=casing, width=int(round((largeur + 1.2) * S)), joint='curve')
    dr.line(pts, fill=couleur, width=int(round(largeur * S)), joint='curve')


def dot(dr, c, r, couleur, bord, epaisseur=1):
    r *= S
    dr.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=couleur, outline=bord, width=int(epaisseur * S))


def fond(d, style, vue):
    """Fond commun aux images et aux videos : mer, quadrillage, iles colorees par proprietaire. Renvoie (image, dessin, P, s, style, vue)."""
    st, vp = STYLES[style], VUES[vue]
    cx, cz, vh, s, P = cadre(d, vue)
    img = Image.new('RGB', (W * S, H * S), st['bg'])
    dr = ImageDraw.Draw(img)
    x0, x1 = cx - W / 2 * vh / H, cx + W / 2 * vh / H
    if st['grid']:
        g = math.ceil(x0 / vp['grille']) * vp['grille']
        while g < x1:
            dr.line([P(g, cz - vh), P(g, cz + vh)], fill=st['grid'], width=S)
            g += vp['grille']
        g = math.ceil((cz - vh / 2) / vp['grille']) * vp['grille']
        while g < cz + vh / 2:
            dr.line([P(x0, g), P(x1, g)], fill=st['grid'], width=S)
            g += vp['grille']
    # iles : couleur de l'equipe qui les controle
    for iid, ix, iz in d['iles']:
        if abs(ix - cx) > W / 2 * vh / H + M.ILE_R * 1.5 or abs(iz - cz) > vh / 2 + M.ILE_R * 1.5:
            continue
        eq = d['iles_eq'][iid]
        prof = M.profil(iid)
        if st['rim']:                                        # cote : couleur vive de l'equipe qui controle l'ile
            dr.polygon([P(ix + math.cos(n / 96 * 6.2832) * M.ILE_R * 1.13 * prof[n], iz + math.sin(n / 96 * 6.2832) * M.ILE_R * 1.13 * prof[n]) for n in range(96)], fill=EQUIPE[eq])
        pts = [P(ix + math.cos(n / 96 * 6.2832) * M.ILE_R * prof[n], iz + math.sin(n / 96 * 6.2832) * M.ILE_R * prof[n]) for n in range(96)]
        dr.polygon(pts, fill=st['isl_fill'][eq])
        if st['isl_line']:
            dr.line(pts + [pts[0]], fill=st['isl_line'], width=int(round(1.6 * S)), joint='curve')
    return img, dr, P, s, st, vp


def echelle_horloge(dr, st, vp, s, t, avec_echelle):
    """Seuls textes : echelle (dessinee dans le fond des videos) et petite horloge du journal."""
    f = ImageFont.truetype(M.FONT, 15 * S)
    if avec_echelle:
        bx, by, bl = 26 * S, (H - 30) * S, vp['echelle'] * s
        for a, b in (((bx, by), (bx + bl, by)), ((bx, by - 5 * S), (bx, by + 5 * S)), ((bx + bl, by - 5 * S), (bx + bl, by + 5 * S))):
            dr.line([a, b], fill=st['txt'], width=2 * S)
        dr.text((bx, by - 10 * S), '%d km' % (vp['echelle'] // 1000), font=f, fill=st['txt'], anchor='ls')
    if t is not None:
        dr.text(((W - 24) * S, (H - 20) * S), cc2map.hms(t), font=f, fill=st['txt'], anchor='rs')


def rendre(d, style, vue, sortie):
    img, dr, P, s, st, vp = fond(d, style, vue)
    # routes des unites des autres equipes qui bougent
    for eq, pts in d['routes']:
        ligne(dr, [P(x, z) for x, z in pts], st['rte_col'][eq], None, vp['rte_w'])
    # route du porte-avions et trace de l'avion 9 (equipe 1)
    ligne(dr, [P(x, z) for _, x, z in d['route']], EQUIPE[1], st['casing'], vp['car_w'])
    for _, run in d['vols']:
        vpts = [P(p[1], p[2]) for p in run]
        ligne(dr, vpts, EQUIPE[1], st['casing'], vp['vol_w'])
        dot(dr, vpts[-1], vp['r_vol'], EQUIPE[1], st['outline'])
    # unites (petits points), puis porte-avions (gros point)
    for _, eq, x, z in d['points']:
        dot(dr, P(x, z), vp['r_pt'], EQUIPE[eq], st['outline'])
    dot(dr, P(d['route'][-1][1], d['route'][-1][2]), vp['r_car'], EQUIPE[1], st['outline'], 2)
    echelle_horloge(dr, st, vp, s, d['t_fin'], True)
    nom = '%s_%s.png' % (style, vue)
    img.resize((W, H), Image.LANCZOS).save(os.path.join(sortie, nom))
    return nom


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    sortie = sys.argv[2]
    if os.path.exists(sortie) and os.listdir(sortie):
        raise SystemExit("REFUS : %s existe deja et n'est pas vide" % sortie)
    os.makedirs(sortie, exist_ok=True)
    d = preparer(sys.argv[1])
    print('dernier instantane : unites par equipe', d['compte'], '| points dessines a part :', len(d['points']), '| routes d\'unites :', len(d['routes']))
    print('iles par equipe :', {e: sum(1 for v in d['iles_eq'].values() if v == e) for e in (1, 0, 2)})
    for style in ('M3', 'M5'):
        for vue in ('archipel', 'zoom'):
            print('ecrit :', os.path.join(sortie, rendre(d, style, vue, sortie)))


if __name__ == '__main__':
    main()
