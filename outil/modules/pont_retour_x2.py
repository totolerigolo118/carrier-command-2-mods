# -*- coding: utf-8 -*-
"""Roulage x2 sur le pont au retour : apres le toucher, les avions (et les helicos) roulent 2x plus vite
de l'avant de la piste jusqu'a l'ascenseur.

FICHIER GENERE par outil/generateurs/generer_pont_retour.py (ne pas modifier a la main).
Fonction : c_vehicle_server_carrier::docking_manager_air::update, etats de piste 5, 6 et 7. Chaque tick,
l'avancement d'un troncon augmente de v / (L x 30) ; ici v / (L x 15) pour ces trois troncons seulement
(constante 30.0 -> 15.0, deja presente). La piste reste reservee jusqu'a l'ascenseur, comme a l'origine :
aucun nouveau risque de collision. Avec ascenseur_x2 (autres octets : acceleration et plafond) : temps sur
le pont ~42 s -> ~22 s. Choisi par le moddeur le 25/10/2026. Etude : etudes/piste_et_pont.md
"""
NOM = "pont_retour_x2"
TITRE = "Roulage x2 sur le pont au retour (avions, helicos)"
TYPE = "programme"

RETOUCHES = [
    ("rip", 0x1001b0824, "f30f590d6c906b02", 0x102869898, 0x1028699cc, 0.5),  # mulss 30.0 -> 15.0 : etat 5 : recul de l'avant de la piste jusqu'a taxi_a (~125 m)
    ("rip", 0x1001ae07c, "f30f590d14b86b02", 0x102869898, 0x1028699cc, 0.5),  # mulss 30.0 -> 15.0 : etat 6 : taxi_a -> lift_upper_wait (~17 m)
    ("rip", 0x1001b0831, "f30f590d5f906b02", 0x102869898, 0x1028699cc, 0.5),  # mulss 30.0 -> 15.0 : etat 7 : lift_upper_wait -> plateforme de l'ascenseur (15,5 m)
]
