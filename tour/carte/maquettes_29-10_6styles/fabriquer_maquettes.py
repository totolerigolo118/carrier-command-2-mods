"""Six maquettes (PNG 1280x720) tres simples de la meme image : les iles, les trajectoires des avions de l'equipe 1, la route du porte-avions.
Meme donnee pour les trois (derniere image de l'essai A du 29/10 : tout le journal) ; seul l'aspect change (6 styles).
Tout est dessine ici avec des formes simples : AUCUN picto, aucune police et aucune image du jeu, aucun nom ni identifiant sur l'image.
Lit seulement les lignes CC2MAP d'un journal (copie) ; n'ecrit que les 3 PNG, dans un dossier neuf.

Usage : python -I fabriquer_maquettes.py <journal essai A copie> <dossier de sortie NEUF>
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc2map
from PIL import Image, ImageChops, ImageDraw, ImageFont

W, H, S = 1280, 720, 2          # S = sur-echantillonnage (anti-crenelage)
VIEW_H = 20000.0                # metres visibles en hauteur
ILE_R = 2040.0                  # rayon indicatif des iles (les journaux n'en donnent pas la taille)
HORS_PONT_M = 100               # un avion a moins de 100 m du porte-avions est « a bord » : pas de trajectoire
AIR = (8, 10, 12, 14)
FONT = 'C:/Windows/Fonts/arial.ttf'

PALETTES = {
    'M1_radar_noir': dict(bg=(5, 9, 11), grid=(16, 38, 42), isl=(12, 40, 42), isl_line=(44, 118, 114), rim=None,
                          car=(61, 242, 255), plane=(255, 194, 74), car_w=3.2, plane_w=2.6, dot_out=None, txt=(112, 170, 178)),
    'M2_carte_claire': dict(bg=(243, 235, 215), grid=(226, 212, 180), isl=(229, 209, 152), isl_line=(160, 128, 76), rim=None,
                            car=(31, 58, 107), plane=(31, 58, 107), car_w=4.2, plane_w=2.4, dot_out=(243, 235, 215), txt=(100, 82, 54)),
    'M3_ocean': dict(bg=(30, 100, 150), grid=(40, 114, 162), isl=(98, 172, 92), isl_line=None, rim=(238, 222, 168),
                     car=(255, 255, 255), plane=(255, 224, 72), car_w=4.4, plane_w=3.2, dot_out=(24, 80, 124), txt=(222, 236, 246)),
    'M4_bleu_nuit': dict(bg=(11, 22, 52), grid=(22, 40, 80), isl=(156, 204, 236), isl_line=(214, 238, 252), rim=None,
                         car=(255, 176, 80), plane=(255, 122, 24), car_w=4.2, plane_w=2.8, dot_out=(11, 22, 52), txt=(150, 182, 222)),
    'M5_encre': dict(bg=(255, 255, 255), grid=None, isl=(255, 255, 255), isl_line=(20, 20, 20), rim=None,
                     car=(38, 92, 200), plane=(214, 52, 52), car_w=2.6, plane_w=1.8, dot_out=(255, 255, 255), txt=(90, 90, 90)),
    'M6_vieille_carte': dict(bg=(233, 217, 178), grid=(216, 198, 152), isl=(241, 229, 197), isl_line=(112, 76, 42), rim=None, hatch=(150, 108, 64),
                             car=(162, 44, 34), plane=(162, 44, 34), car_w=3.8, plane_w=2.2, dot_out=(233, 217, 178), txt=(92, 64, 36)),
}


def seeded(n):
    st = [n * 9301 + 49297]

    def rnd():
        st[0] = (st[0] * 9301 + 49297) % 233280
        return st[0] / 233280
    return rnd


def profil(seed):                # forme d'ile indicative (meme generateur que la page de rejeu)
    rnd = seeded(seed * 7 + 11)
    hh = [(rnd() * 6.283, (0.20 / (h ** 0.9)) * (0.6 + rnd() * 0.8)) for h in range(1, 8)]
    arr = []
    for i in range(96):
        a = i / 96 * 6.2832
        k = 1 + sum(am * math.sin((j + 1) * a + ph) for j, (ph, am) in enumerate(hh))
        arr.append(max(0.55, k) * (1 + 0.035 * math.sin(23 * i / 96 * 6.2832 + seed) + 0.02 * math.sin(41 * i / 96 * 6.2832 + seed * 2)))
    return arr


def donnees(chemin):
    D = cc2map.parse(chemin)
    V = D['V']
    car = [i for i, v in V[0][2].items() if v[0] == 0 and v[1] == 1][0]
    route = [(w, it[car][2], it[car][3]) for w, t, it in V if car in it]
    vols = []                                              # une polyligne par vol, tous les avions de l'equipe 1 qui quittent le pont
    for uid in sorted({i for w, t, it in V for i, v in it.items() if v[1] == 1 and v[0] in AIR}):
        pts = [(w, it[uid][2], it[uid][3], math.hypot(it[uid][2] - it[car][2], it[uid][3] - it[car][3])) for w, t, it in V if uid in it and car in it]
        run = []
        for k, p in enumerate(pts):
            if p[3] > HORS_PONT_M:
                if not run and k > 0:
                    run.append(pts[k - 1])                 # le point juste avant, pour relier au porte-avions
                run.append(p)
            elif run:
                run.append(p)                              # le point juste apres (retour sur le pont)
                vols.append((uid, run))
                run = []
        if run:
            vols.append((uid, run))
    iles = [(i, x, z) for i, (team, x, z) in D['T'][0][2].items()]
    return dict(route=route, vols=vols, iles=iles, t_fin=V[-1][0], t_debut=V[0][0], uid_n=len({u for u, _ in vols}))


def dessiner(d, pal, nom, sortie):
    xs = [p[1] for p in d['route']] + [p[1] for _, run in d['vols'] for p in run]
    zs = [p[2] for p in d['route']] + [p[2] for _, run in d['vols'] for p in run]
    cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
    s = H * S / VIEW_H

    def P(x, z):
        return (W * S / 2 + (x - cx) * s, H * S / 2 - (z - cz) * s)

    img = Image.new('RGB', (W * S, H * S), pal['bg'])
    dr = ImageDraw.Draw(img)
    # quadrillage tres discret tous les 5 km
    x0, x1 = cx - W / 2 * VIEW_H / H, cx + W / 2 * VIEW_H / H
    g = math.ceil(x0 / 5000) * 5000
    while pal['grid'] and g < x1:
        dr.line([P(g, cz - VIEW_H), P(g, cz + VIEW_H)], fill=pal['grid'], width=S)
        g += 5000
    g = math.ceil((cz - VIEW_H / 2) / 5000) * 5000
    while pal['grid'] and g < cz + VIEW_H / 2:
        dr.line([P(x0, g), P(x1, g)], fill=pal['grid'], width=S)
        g += 5000
    # iles (position reelle, forme et taille indicatives)
    for iid, ix, iz in d['iles']:
        if abs(ix - cx) > W / 2 * VIEW_H / H + ILE_R * 1.5 or abs(iz - cz) > VIEW_H / 2 + ILE_R * 1.5:
            continue
        prof = profil(iid)
        if pal['rim']:
            dr.polygon([P(ix + math.cos(n / 96 * 6.2832) * ILE_R * 1.13 * prof[n], iz + math.sin(n / 96 * 6.2832) * ILE_R * 1.13 * prof[n]) for n in range(96)], fill=pal['rim'])
        pts = [P(ix + math.cos(n / 96 * 6.2832) * ILE_R * prof[n], iz + math.sin(n / 96 * 6.2832) * ILE_R * prof[n]) for n in range(96)]
        dr.polygon(pts, fill=pal['isl'])
        if pal.get('hatch'):                                   # hachures diagonales, decoupees a la forme de l'ile
            bx0, by0 = int(min(p[0] for p in pts)) - 1, int(min(p[1] for p in pts)) - 1
            bx1, by1 = int(max(p[0] for p in pts)) + 2, int(max(p[1] for p in pts)) + 2
            bw, bh = bx1 - bx0, by1 - by0
            msk = Image.new('L', (bw, bh), 0)
            ImageDraw.Draw(msk).polygon([(x - bx0, y - by0) for x, y in pts], fill=255)
            hl = Image.new('L', (bw, bh), 0)
            hd = ImageDraw.Draw(hl)
            for k in range(-bh, bw + bh, 8 * S):
                hd.line([(k, bh), (k + bh, 0)], fill=255, width=int(round(1.1 * S)))
            img.paste(Image.new('RGB', (bw, bh), pal['hatch']), (bx0, by0), ImageChops.multiply(msk, hl))
        if pal['isl_line']:
            dr.line(pts + [pts[0]], fill=pal['isl_line'], width=int(round(1.6 * S)), joint='curve')
    # route du porte-avions, puis trajectoires des avions
    rp = [P(x, z) for _, x, z in d['route']]
    dr.line(rp, fill=pal['car'], width=int(round(pal['car_w'] * S)), joint='curve')
    for _, run in d['vols']:
        vp = [P(p[1], p[2]) for p in run]
        dr.line(vp, fill=pal['plane'], width=int(round(pal['plane_w'] * S)), joint='curve')
        e = vp[-1]
        r = 4.8 * S
        dr.ellipse((e[0] - r, e[1] - r, e[0] + r, e[1] + r), fill=pal['plane'], outline=pal['dot_out'], width=S if pal['dot_out'] else 0)
    c = rp[-1]
    r = 8.5 * S
    dr.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=pal['car'], outline=pal['dot_out'], width=2 * S if pal['dot_out'] else 0)
    # echelle (5 km) et petite horloge du journal
    f = ImageFont.truetype(FONT, 15 * S)
    bx, by, bl = 26 * S, (H - 30) * S, 5000 * s
    dr.line([(bx, by), (bx + bl, by)], fill=pal['txt'], width=2 * S)
    dr.line([(bx, by - 5 * S), (bx, by + 5 * S)], fill=pal['txt'], width=2 * S)
    dr.line([(bx + bl, by - 5 * S), (bx + bl, by + 5 * S)], fill=pal['txt'], width=2 * S)
    dr.text((bx, by - 10 * S), '5 km', font=f, fill=pal['txt'], anchor='ls')
    dr.text(((W - 24) * S, (H - 20) * S), cc2map.hms(d['t_fin']), font=f, fill=pal['txt'], anchor='rs')
    img.resize((W, H), Image.LANCZOS).save(os.path.join(sortie, nom + '.png'))


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    sortie = sys.argv[2]
    if os.path.exists(sortie) and os.listdir(sortie):
        raise SystemExit("REFUS : %s existe deja et n'est pas vide" % sortie)
    os.makedirs(sortie, exist_ok=True)
    d = donnees(sys.argv[1])
    print('route : %d points ; vols : %d (avions concernes : %d) ; iles lues : %d' % (len(d['route']), len(d['vols']), d['uid_n'], len(d['iles'])))
    for nom, pal in PALETTES.items():
        dessiner(d, pal, nom, sortie)
        print('ecrit :', os.path.join(sortie, nom + '.png'))


main()
