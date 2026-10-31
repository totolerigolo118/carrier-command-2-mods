"""Essai du rendu des missiles sur d'anciens journaux (hors jeu, rien n'est ecrit ailleurs que dans le dossier de sortie, qui doit etre vide ou neuf).
 - journal du 27/10 (partie 2, 11 min : missiles des equipes 1 et 0) : images de controle avec et sans missiles + un extrait de 30 s (x2) avec et sans ;
 - journal du 30/10, partie 0 (08:39 -> 08:41 : 2 missiles de l'equipe 1 a 08:40:31) : images avec et sans.
Les images utilisent le facteur de production (x11) pour la duree des marques d'impact ; l'extrait video est a x2.

Usage : python -I essai_missiles.py <journal 27/10> <extrait CC2MAP partie 0 du 30/10> <dossier icones> <dossier de sortie>
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'outil_videos'))
import fabriquer_videos_couleurs as VC
import fabriquer_videos_partie_v2 as V2


def sec(h):
    a, b, c = h.split(':')
    return int(a) * 3600 + int(b) * 60 + int(c)


def images(d, prefixe, sortie, icones, liste):
    VC.FACTEUR = 11
    for style, vue, h, missiles in liste:
        nom = '%s_%s_%s_%s_%s.png' % (prefixe, 'avec' if missiles else 'sans', style, vue, h.replace(':', '-'))
        V2.FilmV2(d, style, vue, icones, missiles).image(sec(h)).save(os.path.join(sortie, nom))
        print('ecrit :', nom)


def main():
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    j27, p30, icones, sortie = sys.argv[1:]
    os.makedirs(sortie, exist_ok=True)
    d = V2.preparer(j27)
    images(d, '27-10', sortie, icones, [
        ('M3', 'zoom', '14:56:37', True), ('M3', 'zoom', '14:57:25', True), ('M3', 'zoom', '14:57:45', True), ('M3', 'zoom', '14:57:52', True),
        ('M3', 'zoom', '14:57:25', False), ('M3', 'zoom', '14:57:45', False), ('M5', 'zoom', '14:57:25', True), ('M3', 'archipel', '14:57:45', True)])
    d['t_debut'], d['t_fin'] = sec('14:57:36'), sec('14:58:06')           # extrait de 30 s autour des tirs de l'equipe 0
    VC.FACTEUR = 2
    for missiles in (True, False):
        VC.encoder(V2.FilmV2(d, 'M3', 'zoom', icones, missiles), os.path.join(sortie, '27-10_extrait_x2_%s_missiles.mp4' % ('avec' if missiles else 'sans')))
    d = V2.preparer(p30)
    images(d, '30-10', sortie, icones, [('M3', 'zoom', '08:40:32', True), ('M3', 'zoom', '08:40:32', False), ('M3', 'zoom', '08:40:37', True), ('M5', 'zoom', '08:40:33', True)])


if __name__ == '__main__':
    main()
