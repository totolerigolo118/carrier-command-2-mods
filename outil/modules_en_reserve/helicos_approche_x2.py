# -*- coding: utf-8 -*-
"""Approche des helicos vers la PISTE deux fois plus rapide (~5 m/s -> ~10 m/s).

FICHIER GENERE par outil/generateurs/generer_helicos_ascenseur.py. Demande du moddeur le 24/10/2026.
Dans le jeu d'origine, un helico qui se pose sur la piste vise un point 50 m devant lui (au plus z = 52) ;
le pilote automatique corrige l'ecart a 0,1 par metre, d'ou ~5 m/s et ~1:00 d'approche (mesure du 23/10).
Ici le point vise est 100 m devant lui (constante 100.0 deja presente, lue a la place de 50.0) : ~10 m/s
sur la longue ligne droite, meme fin d'approche (le point vise reste borne a z = 52). Instruction propre
aux helicos (apres le test get_is_rotor a 0x1001ad3e1) : les avions ne sont pas concernes. Ne touche pas
les helicos de la voie ascenseur (module helicos_ascenseur), qui ont leur propre pilotage.
"""
NOM = "helicos_approche_x2"
TITRE = "Helicos : approche de la piste 2x plus rapide"
TYPE = "programme"

RETOUCHES = [
    # movss 50.0 -> 100.0 : distance du point vise devant l'helico (approche de la piste)
    ("rip", 0x1001ad3ef, "f30f1005b5c46b02", 0x1028698ac, 0x1028697ac, 2.0),
]
