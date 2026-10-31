#!/usr/bin/env python3
# Planches « temps réel vs temps du jeu » : lit les journaux cc2x copiés (lecture seule), écrit 2 PNG dans le dossier de sortie.
# Usage : python -I planches_temps.py <sortie> <journal1> [<journal2> ...]
import re, sys, os, statistics
from PIL import Image, ImageDraw, ImageFont

RX = re.compile(r'^(\d\d):(\d\d):(\d\d\.\d+) \[(?:frein|modes)\] info: id \d+ t=(\d+\.\d+)')
FONT = r'C:\Windows\Fonts\arial.ttf'
FONTB = r'C:\Windows\Fonts\arialbd.ttf'


def police(taille, gras=False):
    try:
        return ImageFont.truetype(FONTB if gras else FONT, taille)
    except Exception:
        return ImageFont.load_default()


def lire(chemin):
    pts = []
    with open(chemin, 'r', encoding='utf-8', errors='replace') as f:
        for ligne in f:
            m = RX.match(ligne)
            if not m:
                continue
            h, mi, s, t = int(m.group(1)), int(m.group(2)), float(m.group(3)), float(m.group(4))
            if t < 5.0:                      # premiers relevés d'une partie : pas fiables
                continue
            pts.append((h * 3600 + mi * 60 + s, t))
    pts.sort()
    segs, cur = [], []
    for w, t in pts:
        if cur and t < cur[-1][1] - 5.0:     # le temps du jeu a reculé : nouvelle partie
            segs.append(cur); cur = []
        cur.append((w, t))
    if cur:
        segs.append(cur)
    return [s for s in segs if len(s) > 20 and s[-1][0] - s[0][0] > 60]


def pente(seg):
    xs = [p[0] for p in seg]; ys = [p[1] for p in seg]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den


def rapports_fenetres(seg, pas=30.0):
    res, i, n = [], 0, len(seg)
    debut = seg[0][0]
    while debut + pas <= seg[-1][0]:
        a = [p for p in seg if debut <= p[0] < debut + pas]
        if len(a) >= 2 and a[-1][0] - a[0][0] > pas * 0.5:
            res.append((debut + pas / 2, (a[-1][1] - a[0][1]) / (a[-1][0] - a[0][0])))
        debut += pas
    return res


def fmt_min(sec):
    return '%d:%02d' % (int(sec // 60), int(sec % 60))


def planche1(chemin, parties):
    W, H = 1600, 900
    img = Image.new('RGB', (W, H), (250, 250, 247))
    d = ImageDraw.Draw(img)
    d.text((60, 30), 'Temps réel et temps du jeu : une seconde réelle = environ 2 secondes du journal du jeu', font=police(34, True), fill=(30, 30, 30))
    d.text((60, 78), 'Chaque courbe est une partie (journaux cc2x.log). Plus la courbe monte vite, plus le jeu va vite par rapport à la montre.', font=police(22), fill=(80, 80, 80))
    gx0, gy0, gx1, gy1 = 130, 150, 1540, 800
    d.rectangle((gx0, gy0, gx1, gy1), outline=(120, 120, 120), width=2)
    xmax = max((s[-1][0] - s[0][0]) for _, segs in parties for s in segs) / 60.0
    ymax = max((s[-1][1] - s[0][1]) for _, segs in parties for s in segs) / 60.0
    xmax = int(xmax) + 1; ymax = int(ymax) + 2
    for k in range(0, xmax + 1, 2):
        x = gx0 + (gx1 - gx0) * k / xmax
        d.line((x, gy0, x, gy1), fill=(225, 225, 220))
        d.text((x - 12, gy1 + 8), '%d' % k, font=police(20), fill=(60, 60, 60))
    for k in range(0, ymax + 1, 2):
        y = gy1 - (gy1 - gy0) * k / ymax
        d.line((gx0, y, gx1, y), fill=(225, 225, 220))
        d.text((gx0 - 48, y - 12), '%d' % k, font=police(20), fill=(60, 60, 60))
    d.text((gx0 + 520, gy1 + 40), 'temps réel écoulé (minutes de montre)', font=police(24), fill=(40, 40, 40))
    d.text((12, gy0 - 36), 'temps du journal du jeu (minutes)', font=police(24), fill=(40, 40, 40))
    # droite de référence : 1 seconde réelle = 1 seconde de jeu
    d.line((gx0, gy1, gx0 + (gx1 - gx0) * min(xmax, ymax) / xmax, gy1 - (gy1 - gy0) * min(xmax, ymax) / ymax), fill=(170, 170, 170), width=2)
    d.text((gx0 + 300, gy1 - 120), 'pointillé gris : si le jeu allait à la vitesse de la montre', font=police(20), fill=(130, 130, 130))
    couleurs = [(31, 119, 180), (214, 39, 40), (44, 160, 44), (255, 127, 14), (148, 103, 189), (140, 86, 75)]
    ly = gy0 + 14
    n = 0
    for nom, segs in parties:
        for s in segs:
            c = couleurs[n % len(couleurs)]
            x0, t0 = s[0]
            pts = [(gx0 + (gx1 - gx0) * ((w - x0) / 60.0) / xmax, gy1 - (gy1 - gy0) * ((t - t0) / 60.0) / ymax) for w, t in s]
            d.line(pts, fill=c, width=4)
            p = pente(s)
            d.rectangle((gx0 + 24, ly, gx0 + 54, ly + 22), fill=c)
            d.text((gx0 + 66, ly - 2), '%s : ×%.2f' % (nom, p), font=police(22), fill=(30, 30, 30))
            ly += 32
            n += 1
    img.save(chemin)


def planche2(chemin, parties, ratios_fen):
    W, H = 1600, 980
    img = Image.new('RGB', (W, H), (250, 250, 247))
    d = ImageDraw.Draw(img)
    d.text((60, 30), 'Les trois horloges du jeu, pour convertir un temps en un autre', font=police(34, True), fill=(30, 30, 30))
    d.text((60, 78), 'Mesuré dans les journaux : la montre (temps réel) et le journal du jeu (cc2x.log). Le temps affiché à l\'écran vient du compteur SIM ×1,33.', font=police(22), fill=(80, 80, 80))
    moy = statistics.mean(ratios_fen)
    med = statistics.median(ratios_fen)
    mini, maxi = min(ratios_fen), max(ratios_fen)
    # histogramme des rapports par fenêtre de 30 s
    gx0, gy0, gx1, gy1 = 110, 190, 880, 560
    d.text((gx0, gy0 - 44), 'Vitesse du journal du jeu, par tranche de 30 s réelles', font=police(24, True), fill=(40, 40, 40))
    d.rectangle((gx0, gy0, gx1, gy1), outline=(120, 120, 120), width=2)
    lo, hi = 1.5, 2.6
    nb = 22
    cases = [0] * nb
    for r in ratios_fen:
        k = int((min(max(r, lo), hi - 1e-9) - lo) / (hi - lo) * nb)
        cases[k] += 1
    cmax = max(cases) or 1
    lw = (gx1 - gx0) / nb
    for k, c in enumerate(cases):
        x = gx0 + k * lw
        h = (gy1 - gy0 - 30) * c / cmax
        d.rectangle((x + 2, gy1 - h, x + lw - 2, gy1), fill=(31, 119, 180))
    for v in (1.5, 1.8, 2.0, 2.2, 2.4, 2.6):
        x = gx0 + (gx1 - gx0) * (v - lo) / (hi - lo)
        d.line((x, gy1, x, gy1 + 8), fill=(60, 60, 60), width=2)
        d.text((x - 16, gy1 + 12), '×%.1f' % v, font=police(20), fill=(60, 60, 60))
    xm = gx0 + (gx1 - gx0) * (med - lo) / (hi - lo)
    d.line((xm, gy0, xm, gy1), fill=(214, 39, 40), width=3)
    d.text((xm + 8, gy0 + 8), 'médiane ×%.2f' % med, font=police(22, True), fill=(214, 39, 40))
    d.text((gx0, gy1 + 44), '%d tranches mesurées : de ×%.2f à ×%.2f (moyenne ×%.2f)' % (len(ratios_fen), mini, maxi, moy), font=police(22), fill=(60, 60, 60))
    # tableau de conversion
    tx0, ty0 = 940, 190
    d.text((tx0, ty0 - 44), 'Tableau de conversion', font=police(24, True), fill=(40, 40, 40))
    k_sdk = med
    k_aff = 1.33
    lignes = [('Montre (réel)', 'Journal du jeu', 'Affiché à l\'écran')]
    for sec in (60, 300, 600, 1800):
        lignes.append((fmt_min(sec), fmt_min(sec * k_sdk), fmt_min(sec * k_aff)))
    cw = [200, 200, 220]
    y = ty0
    for i, lg in enumerate(lignes):
        x = tx0
        fond = (225, 232, 240) if i == 0 else (255, 255, 255)
        d.rectangle((tx0, y, tx0 + sum(cw), y + 44), fill=fond, outline=(150, 150, 150))
        for j, txt in enumerate(lg):
            d.text((x + 10, y + 9), txt, font=police(22, i == 0), fill=(30, 30, 30))
            x += cw[j]
        y += 44
    d.text((tx0, y + 18), '(minutes:secondes)', font=police(20), fill=(100, 100, 100))
    notes = [
        '1 min de montre = %.1f min du journal du jeu' % k_sdk,
        '1 min de montre = %.1f min de « temps de jeu » affiché (SIM ×1,33, vu sur la capture du 29/10)' % k_aff,
        '1 min affichée = %.2f min du journal : c\'est le « 1,56 » qui restait inexpliqué (2,08 ÷ 1,33)' % (k_sdk / k_aff),
    ]
    yy = 700
    d.rectangle((60, yy - 16, 1540, yy + 190), fill=(255, 250, 235), outline=(210, 190, 120))
    d.text((80, yy), 'À retenir', font=police(26, True), fill=(40, 40, 40))
    for i, n in enumerate(notes):
        d.text((80, yy + 46 + 44 * i), '•  ' + n, font=police(24), fill=(40, 40, 40))
    d.text((60, 930), 'Source : journaux cc2x des 29 et 30/10/2026 (lignes « id N t=… » des plugins). Le 2,08 est mesuré ; le ×1,33 vient de l\'écran du jeu (une capture) : à reconfirmer.', font=police(18), fill=(110, 110, 110))
    img.save(chemin)


def main():
    sortie = sys.argv[1]
    os.makedirs(sortie, exist_ok=True)
    parties, ratios = [], []
    for chemin in sys.argv[2:]:
        segs = lire(chemin)
        if not segs:
            print('aucun segment exploitable :', chemin); continue
        base = os.path.basename(chemin).replace('cc2x_', '').split('_frein')[0]
        etiquettes = {'2026-10-29_142607': 'Essai A, 29/10 14:26', '2026-10-29_154658': 'Essai B, 29/10 15:49',
                      '2026-10-30_080001': 'Partie v8, 30/10 08:00', '2026-10-30_082200': 'Partie v9, 30/10 08:22'}
        nom = etiquettes.get(base, base)
        if len(segs) > 1:                      # plusieurs parties dans le même journal : on les numérote
            for k, s in enumerate(segs, 1):
                parties.append(('%s (partie %d)' % (nom, k), [s]))
        else:
            parties.append((nom, segs))
        for s in segs:
            ratios += [r for _, r in rapports_fenetres(s)]
            print('%s : %d points, %.0f s réelles, pente %.3f' % (nom, len(s), s[-1][0] - s[0][0], pente(s)))
    if not parties:
        sys.exit('rien à tracer')
    planche1(os.path.join(sortie, 'planche_1_temps_reel_vs_journal.png'), parties)
    planche2(os.path.join(sortie, 'planche_2_conversion_des_horloges.png'), parties, ratios)
    print('médiane des tranches de 30 s : %.3f ; moyenne %.3f ; min %.3f ; max %.3f (n=%d)' % (statistics.median(ratios), statistics.mean(ratios), min(ratios), max(ratios), len(ratios)))


if __name__ == '__main__':
    main()
